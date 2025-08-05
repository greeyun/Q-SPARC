import os
import json
from fastapi import FastAPI
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# --- LangChain Core Imports ---
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory

# --- LangChain Community & Integrations ---
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
# from langserve import add_routes  # <-- 已移除
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables.history import RunnableWithMessageHistory

# --- 1. Environment and Model Configuration ---
# 设置环境变量，确保模型可以被正确加载
os.environ["CUDA_VISIBLE_DEVICES"] = "0,2"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# LLM 配置
BASE_URL = "http://localhost:8000/v1"
API_KEY = "EMPTY"
MODEL_ID = "/hpc/fxu244/Documents/Code/LLMs/Qwen3-32B"

# --- 2. Data Loading and Vector Store Creation (Executed on Server Startup) ---

def get_val(record: Dict[str, Any], key: str) -> str:
    """Safely extracts the 'value' from a record's key."""
    if key in record and isinstance(record.get(key), dict):
        return record[key].get('value', 'N/A')
    return 'N/A'

def load_and_process_documents() -> List[Document]:
    """
    Loads data from a JSON file, processes it into a structured format,
    and creates LangChain Document objects ready for embedding.
    """
    file_path = '/hpc/fxu244/Documents/Code/LLMs/a-b-via-c.json'
    jq_schema = '.results.bindings[]'
    
    print("Loading raw data from JSON...")
    loader = JSONLoader(
        file_path=file_path,
        jq_schema=jq_schema,
        text_content=False
    )
    raw_docs = loader.load()
    
    final_documents = []
    print(f"Processing {len(raw_docs)} records...")
    for doc in raw_docs:
        record = json.loads(doc.page_content)
        
        clean_data = {
            "Neuron_ID": get_val(record, "Neuron_ID"),
            "A": get_val(record, "A"),
            "B": get_val(record, "B"),
            "C": get_val(record, "C"),
            "Target_Organ": get_val(record, "Target_Organ"),
            "C_Type": get_val(record, "C_Type"),
        }
        
        page_content = (
            f"Neuron Connection Info: Neuron ID is {clean_data['Neuron_ID']}. "
            f"It connects from {clean_data['A']} to {clean_data['B']} via {clean_data['C']}. "
            f"The target organ is {clean_data['Target_Organ']}. "
            f"The connection type C_Type is {clean_data['C_Type']}."
        )
        
        final_documents.append(
            Document(page_content=page_content, metadata=clean_data)
        )
        
    print("Document processing complete.")
    return final_documents

def create_vector_store(documents: List[Document]) -> Chroma:
    """
    Initializes an embedding model and creates a Chroma vector store
    from the processed documents.
    """
    print("Initializing embedding model...")
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print("Creating Chroma vector store in memory...")
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings
    )
    print("Vector store created successfully!")
    return vector_store

# --- Global Vector Store and Retriever (Initialized once) ---
processed_docs = load_and_process_documents()
vector_store = create_vector_store(processed_docs)
retriever = vector_store.as_retriever(search_kwargs={"k": 20})

# --- 3. Conversation History Management ---
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """
    Retrieves the chat history for a given session ID. If the session
    doesn't exist, a new one is created.
    """
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

# --- 4. LangChain Runnable/Chain Construction ---
template = """You are an expert assistant specializing in neuroscience and neural pathways. 
Answer the user's question based on the following context and the chat history.
If the context does not contain the answer, state that you cannot find relevant information in the provided data.
Be concise and clear.

CONTEXT:
{context}

CHAT HISTORY:
"""
prompt = ChatPromptTemplate.from_messages([
    ("system", template),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

model = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL_ID)
parser = StrOutputParser()

def format_docs(docs: List[Document]) -> str:
    """Helper function to format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    RunnablePassthrough.assign(
        context=RunnableLambda(lambda x: x["input"]) | retriever | format_docs
    )
    | prompt
    | model
    | parser
)

class InputChat(TypedDict):
    """Input for the chat endpoint."""
    input: str

chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
).with_types(input_type=InputChat)

# --- 5. FastAPI Application Setup ---
app = FastAPI(
    title="Custom RAG API with History",
    version="1.0",
    description="An API server for querying neural connection data with conversational history.",
)

# --- 新增: 定义请求和响应模型 ---
class ChatRequest(BaseModel):
    """Chat endpoint 的请求模型"""
    input: str = Field(..., description="用户的问题或消息", examples=["Find connections from A to B"])
    session_id: str = Field(..., description="用于追踪对话的唯一会话ID", examples=["user123_session456"])

class ChatResponse(BaseModel):
    """Chat endpoint 的响应模型"""
    response: str

# --- 新增: 定义自定义API端点 ---
@app.get("/")
def read_root():
    """一个简单的 GET 端点，用于确认服务器正在运行。"""
    return {"status": "ok", "message": "RAG API is running"}

@app.post("/chat")
def chat_with_rag(request: ChatRequest):
    """
    通过调用带有历史记录的 RAG chain 来处理聊天请求。
    """
    # 使用用户的输入和会话ID调用 chain。
    # `config` 字典对于 `RunnableWithMessageHistory` 正确工作至关重要。
    answer = chain_with_history.invoke(
        {"input": request.input},
        config={"configurable": {"session_id": request.session_id}}
    )
    return {"response": answer}


# Add the runnable to the FastAPI app, making it available at the /chat endpoint
# add_routes(
#     app,
#     chain_with_history,
#     path="/chain",
# )

# --- 6. Run the Server ---
if __name__ == "__main__":
    import uvicorn
    # 服务器将在 localhost 的 7777 端口上运行
    uvicorn.run(app, host="localhost", port=7777)