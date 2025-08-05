import os
import json
from fastapi import FastAPI
from typing import List, Dict, Any
from pydantic import BaseModel, Field
from typing_extensions import TypedDict

# --- LangChain Core Imports ---
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableLambda
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory

# --- LangChain Community & Integrations ---
from langchain_community.document_loaders import JSONLoader
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_openai import ChatOpenAI
from langserve import add_routes
from langchain.memory import ConversationBufferWindowMemory
from langchain_core.runnables.history import RunnableWithMessageHistory

# --- 1. Environment and Model Configuration ---
# Set environment variables to ensure the model is loaded correctly
os.environ["CUDA_VISIBLE_DEVICES"] = "0,2"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"

# LLM Configuration
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
        
        # clean_data = {
        #     "Neuron_ID": get_val(record, "Neuron_ID"),
        #     "A": get_val(record, "A"),
        #     "B": get_val(record, "B"),
        #     "C": get_val(record, "C"),
        #     "Target_Organ": get_val(record, "Target_Organ"),
        #     "C_Type": get_val(record, "C_Type"),
        # }
        
        # # Create meaningful text content for semantic search
        # page_content = (
        #     f"Neuron Connection Info: Neuron ID is {clean_data['Neuron_ID']}. "
        #     f"It connects from {clean_data['A']} to {clean_data['B']} via {clean_data['C']}. "
        #     f"The target organ is {clean_data['Target_Organ']}. "
        #     f"The connection type C_Type is {clean_data['C_Type']}."
        # )


        clean_data = {
            "Neuron_ID": get_val(record, "Neuron_ID"),
            "A_L1_ID": get_val(record, "A_L1_ID"),
            "A_L1": get_val(record, "A_L1"),
            "A_L2_ID": get_val(record, "A_L2_ID"),
            "A_L2": get_val(record, "A_L2"),
            "A_L3_ID": get_val(record, "A_L3_ID"),
            "A_L3": get_val(record, "A_L3"),
            "A_ID": get_val(record, "A_ID"),
            "A": get_val(record, "A"),
            "C_ID": get_val(record, "C_ID"),
            "C": get_val(record, "C"),
            "C_Type": get_val(record, "C_Type"),
            "B_ID": get_val(record, "B_ID"),
            "B": get_val(record, "B"),
            "Target_Organ_IRI": get_val(record, "Target_Organ_IRI"),
            "Target_Organ": get_val(record, "Target_Organ"),
        }
        
        # Create meaningful text content for semantic search
        page_content = (
            f"Neuron Connection Info: Neuron ID is {clean_data['Neuron_ID']}. "
            f"It connects from {clean_data['A']} (A_ID: {clean_data['A_ID']}) "
            f"to {clean_data['B']} (B_ID: {clean_data['B_ID']}) "
            f"via {clean_data['C']} (C_ID: {clean_data['C_ID']}). "
            f"The target organ is {clean_data['Target_Organ']} (IRI: {clean_data['Target_Organ_IRI']}). "
            f"The connection type C_Type is {clean_data['C_Type']}. "
            f"Hierarchical structure: A_L1: {clean_data['A_L1']} (ID: {clean_data['A_L1_ID']}), "
            f"A_L2: {clean_data['A_L2']} (ID: {clean_data['A_L2_ID']}), "
            f"A_L3: {clean_data['A_L3']} (ID: {clean_data['A_L3_ID']})."
        )

        # Store both the text and the structured data
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
    # Use a sentence-transformer model for creating embeddings. It runs locally.
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    print("Creating Chroma vector store in memory...")
    # Chroma is used as the vector store. It's fast and efficient for this use case.
    vector_store = Chroma.from_documents(
        documents=documents,
        embedding=embeddings
    )
    print("Vector store created successfully!")
    return vector_store

# --- Global Vector Store and Retriever (Initialized once) ---
processed_docs = load_and_process_documents()
vector_store = create_vector_store(processed_docs)
retriever = vector_store.as_retriever(search_kwargs={"k": 20}) # Retrieve top 20 most similar documents

# --- 3. Conversation History Management ---
# This dictionary will store conversation histories for different sessions.
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

# --- Few-Shot Examples from readme.md ---
# By providing these examples, we guide the LLM to respond in a similar format.
few_shot_examples = [
HumanMessage(content="Is there a connection from inferior mesenteric ganglion to the urinary bladder in rats? Summarize the pathways based on the nerves involved."),
AIMessage(content="""
Yes, there is a connection from the inferior mesenteric ganglion to the urinary bladder in rats. The pathways are summarized as follows:

1. Via bladder nerve:
   - From inferior mesenteric ganglion to Dome of the Bladder
   - From inferior mesenteric ganglion to neck of urinary bladder
2. Via hypogastric nerve:
   - From inferior mesenteric ganglion to Dome of the Bladder
   - From inferior mesenteric ganglion to neck of urinary bladder
3. Via pelvic ganglion:
   - From inferior mesenteric ganglion to Dome of the Bladder
   - From inferior mesenteric ganglion to neck of urinary bladder."""),

HumanMessage(content="To what organs does the pelvic ganglion project? Summarize the connections categorized by end organs. Only list the end organs."),
AIMessage(content="""
The pelvic ganglion projects to several organs, which can be categorized as follows:

1. Bladder:
   - Dome of the bladder
   - Neck of the urinary bladder
2. Uterus:
   - Uterine myometrium
   - Blood vessel of the uterus
   - Blood vessel of the cervix
   - Blood vessel of the isthmus of the Fallopian tube
3. Cervix:
   - Smooth muscle of the cervix
   - Epithelium of the cervix
4. Vagina:
   - Smooth muscle of the vagina
   - Blood vessel of the vagina
5. Clitoris:
   - Dorsal artery of the clitoris
   - Clitoral smooth muscle
6. Ovary:
   - Ovary
7. Prostate:
   - Prostate gland smooth muscle
   - Prostate epithelium
8. Seminal Vesicles:
   - Muscular coat of seminal vesicle
9. Fallopian Tube:
   - Smooth muscle of the isthmus of the Fallopian tube

These connections illustrate the diverse roles of the pelvic ganglion in innervating various reproductive and urinary structures.
"""),

HumanMessage(content="What connections originate the nucleus of brain? Categorize the pathways based on different brain nucleus."),
AIMessage(content="""
Based on the information provided, there are no results available from the SCKAN autonomous nervous system connectivity knowledge base regarding the connections that originate from the nucleus of the brain. Therefore, I am unable to categorize the pathways based on different brain nuclei.
"""),

HumanMessage(content="What connections terminate in the urinary bladder? Concisely summarize the pathways categorized as follows: What are the origins of those connections? What are the exact parts of the organ the connections terminate? What nerves are involved in those connections?"),
AIMessage(content="""
The connections that terminate in the urinary bladder can be summarized as follows:
          
Origins of Connections:
1. Pelvic Ganglion
2. First Sacral Dorsal Root Ganglion
3. Sixth Lumbar Dorsal Root Ganglion
4. First Lumbar Dorsal Root Ganglion
5. Second Lumbar Dorsal Root Ganglion
6. Third Lumbar Dorsal Root Ganglion
7. Fourth Lumbar Ganglion
8. Fifth Lumbar Sympathetic Ganglion
9. Sixth Lumbar Sympathetic Ganglion
10. Twelfth Thoracic Ganglion
11. Thirteenth Thoracic Ganglion
12. Inferior Mesenteric Ganglion
13. First Lumbar Ganglion

Parts of the Organ the Connections Terminate:

1. Dome of the Bladder
2. Neck of the Urinary Bladder
3. Arteriole in Connective Tissue of Bladder Neck

Nerves Involved in Those Connections:

1. Bladder Nerve
2. Pelvic Splanchnic Nerve
3. Lumbar Splanchnic Nerve
4. Hypogastric Nerve
5. Gray Communicating Ramus
6. Interganglionic Segments of the Sympathetic Chain** (e.g., L1 - L2, L2 - L3, etc.)

These connections illustrate the complex neural pathways that facilitate communication between various spinal and autonomic ganglia and the urinary bladder."""),


HumanMessage(content="What organs are innervated by vagus nerve? Summarize the pathways categorized by the origins and the end organ systems."),
AIMessage(content="""
The vagus nerve innervates several organs through various pathways originating from different nuclei and ganglia. Below is a summary of the pathways categorized by their origins and the corresponding end organ systems:

From Inferior Vagus X Ganglion:

1. Cardiovascular System:
   - Aorta
   - Epicardium
   - Heart (Left Ventricle)
   - Heart (Right Ventricle)
   - Left Cardiac Atrium
   - Pulmonary Artery
   - Right Cardiac Atrium
2. Gastrointestinal System:
   - Esophagus (smooth muscle circular layer)
   - Esophagus (smooth muscle longitudinal layer)
   - Lower Esophagus
   - Mucosa of Stomach
   - Myenteric Nerve Plexus of Stomach
   - Stomach (smooth muscle circular layer)
   - Stomach (smooth muscle outer longitudinal layer)
3. Other Systems:
   - Multicellular Organism
   - Thymus Gland

From Dorsal Motor Nucleus of Vagus Nerve:

1. Cardiovascular System:
   - Atrial Intrinsic Cardiac Ganglion
   - Ventricular Intrinsic Cardiac Ganglion
2. Gastrointestinal System:
   - Myenteric Nerve Plexus of Stomach
   - Intrapancreatic Ganglia
   - Celiac Ganglion - Superior Mesenteric Ganglion Complex
   - Juxta-Intestinal Mesenteric Lymph Node
   - Renal Nerve Plexus Ganglion (via renal plexus)
3. Reproductive System:
   - Ovarian Ganglion (via aortic plexus)

From Nucleus Ambiguus:

1. Cardiovascular System:
   - Atrial Intrinsic Cardiac Ganglion
   - Ventricular Intrinsic Cardiac Ganglion
2. Respiratory System:
   - Bronchiole Parasympathetic Ganglia
   - Bronchus Parasympathetic Ganglia
   - Terminal Bronchiole Parasympathetic Ganglia
   - Trachea Parasympathetic Ganglia
3. Reproductive System:
   - Ovarian Ganglion (via aortic plexus)

Sensory Pathways:

1. From Left Nodose Ganglion:
   - Sensory terminal in hilus of the liver, bile duct, or portal vein (via anterior abdominal vagal trunk to nucleus of solitary tract)
2. From Right Nodose Ganglion:
   - Sensory terminal in bile duct or portal vein (via periarterial plexus of the common hepatic artery to nucleus of solitary tract)

This summary highlights the diverse innervation provided by the vagus nerve to various organ systems, illustrating its critical role in autonomic regulation."""),

HumanMessage(content="What anatomical structures can be stimulated by inferior mesenteric ganglion? Only list unique origins, destinations, and via structures."),
AIMessage(content="""
The anatomical structures that can be stimulated by the inferior mesenteric ganglion, along with their unique origins, destinations, and via structures, are as follows:

1. From the first lumbar dorsal root ganglion:
   - Destination: L1 segment of lumbar spinal cord via inferior mesenteric ganglion
   - Destination: L2 segment of lumbar spinal cord via inferior mesenteric ganglion
2. From the second lumbar dorsal root ganglion:
   - Destination: L1 segment of lumbar spinal cord via inferior mesenteric ganglion
   - Destination: L2 segment of lumbar spinal cord via inferior mesenteric ganglion
3. From the L1 segment of lumbar spinal cord:
   - Destination: Pelvic ganglion via inferior mesenteric ganglion
   - Via: Gray communicating ramus of first lumbar nerve
   - Via: Gray communicating ramus of second lumbar nerve
   - Via: Lumbar splanchnic nerve
   - Via: Ventral root of the first lumbar spinal cord segment
   - Via: Ventral root of the second lumbar spinal cord segment
   - Via: White communicating ramus of first lumbar spinal nerve
   - Via: White communicating ramus of second lumbar spinal nerve
   - Via: White matter of spinal cord
4. From the L2 segment of lumbar spinal cord:
   - Destination: Pelvic ganglion via inferior mesenteric ganglion
   - Via: Gray communicating ramus of first lumbar nerve
   - Via: Gray communicating ramus of second lumbar nerve
   - Via: Lumbar splanchnic nerve
   - Via: Ventral root of the first lumbar spinal cord segment
   - Via: Ventral root of the second lumbar spinal cord segment
   - Via: White communicating ramus of first lumbar spinal nerve
   - Via: White communicating ramus of second lumbar spinal nerve
   - Via: White matter of spinal cord
5. From the L3 segment of lumbar spinal cord:
   - Destination: Inferior mesenteric ganglion via Fourth lumbar ganglion
   - Destination: Inferior mesenteric ganglion via Third lumbar ganglion
   - Via: White communicating ramus of fourth lumbar anterior ramus
   - Via: Gray communicating ramus of fourth lumbar nerve
   - Via: Gray communicating ramus of third lumbar nerve
   - Via: Lumbar splanchnic nerve
   - Via: Ventral root of the fourth lumbar spinal cord segment
   - Via: Ventral root of the third lumbar spinal cord segment
   - Via: White communicating ramus of third lumbar spinal nerve
   - Via: White matter of spinal cord
6. From the L4 segment of lumbar spinal cord:
   - Destination: Inferior mesenteric ganglion via Fourth lumbar ganglion
   - Destination: Inferior mesenteric ganglion via Third lumbar ganglion
   - Via: White communicating ramus of fourth lumbar anterior ramus
   - Via: Gray communicating ramus of fourth lumbar nerve
   - Via: Gray communicating ramus of third lumbar nerve
   - Via: Lumbar splanchnic nerve
   - Via: Ventral root of the fourth lumbar spinal cord segment
   - Via: Ventral root of the third lumbar spinal cord segment
   - Via: White communicating ramus of third lumbar spinal nerve
   - Via: White matter of spinal cord
7. From the inferior mesenteric ganglion:
   - Destination: Dome of the bladder via bladder nerve
   - Destination: Neck of urinary bladder via bladder nerve
   - Destination: Dome of the bladder via hypogastric nerve
   - Destination: Neck of urinary bladder via hypogastric nerve
   - Destination: Dome of the bladder via pelvic ganglion
   - Destination: Neck of urinary bladder via pelvic ganglion
   - Destination: Peyer's patch via Circular muscle layer of descending colon
   - Destination: Descending colon via Circular muscle layer of descending colon
   - Destination: Peyer's patch via Lamina propria mucosae of descending colon
   - Destination: Descending colon via Lamina propria mucosae of descending colon
   - Destination: Peyer's patch via Longitudinal muscle layer of descending colon
   - Destination: Descending colon via Longitudinal muscle layer of descending colon
   - Destination: Peyer's patch via Myenteric nerve plexus of descending colon
   - Destination: Descending colon via Myenteric nerve plexus of descending colon
   - Destination: Peyer's patch via Serosa of descending colon
   - Destination: Descending colon via Serosa of descending colon
   - Destination: Peyer's patch via Submucosal nerve plexus of descending colon
   - Destination: Descending colon via Submucosal nerve plexus of descending colon
   - Destination: Prostate gland smooth muscle via hypogastric nerve via postganglionic sympathetic fiber
8. From the Myenteric nerve plexus of descending colon:
   - Destination: Inferior mesenteric ganglion via Longitudinal muscle layer of descending colon
   - Destination: Inferior mesenteric ganglion via Serosa of descending colon
   - Destination: Inferior mesenteric ganglion via lumbar colonic nerve
9. From the L6-S3 spinal cord:
   - Destination: Inferior mesenteric ganglion via pelvic splanchnic nerve
10. From the intermediolateral cell column of L1-L2 spinal cord:
    - Destination: Major pelvic ganglion via inferior mesenteric ganglion via hypogastric nerve

This comprehensive list outlines the various anatomical structures that can be stimulated by the inferior mesenteric ganglion, highlighting their origins, destinations, and the pathways involved."""),


]


# Define the prompt template
# It includes placeholders for context (from retriever), history, and the user's input.
# The few-shot examples are now part of the template.


system_prompt = """You are an expert assistant specializing in neuroscience and neural pathways. 
Answer the user's question based on the following context and the chat history.Be concise and clear,do not output thinking stage and do not output repeat or redudant results.
After completing the text answer, you will also need to return the data in the original database that I used in the following format, if not exist show N/A, and delete the repeated data:

Start_JSON "head": [
      "Neuron_ID",
      "A_L1_ID",
      "A_L1",
      "A_L2_ID",
      "A_L2",
      "A_L3_ID",
      "A_L3",
      "A_ID",
      "A",
      "C_ID",
      "C",
      "C_Type",
      "B_ID",
      "B",
      "Target_Organ_IRI",
      "Target_Organ"
    ],
"rows":[...,...,...]
End_JSON

CONTEXT:
{context}
"""

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
    ]
    + few_shot_examples
    + [
        MessagesPlaceholder(variable_name="history"),
        ("human", "{input}"),
    ]
)

# Initialize the LLM
model = ChatOpenAI(base_url=BASE_URL, api_key=API_KEY, model=MODEL_ID)

# Standard output parser
parser = StrOutputParser()

def format_docs(docs: List[Document]) -> str:
    """Helper function to format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)

# Create the main RAG (Retrieval-Augmented Generation) chain
# This chain orchestrates the entire process.
rag_chain = (
    RunnablePassthrough.assign(
        context=RunnableLambda(lambda x: x["input"]) | retriever | format_docs
    )
    | prompt
    | model
    | parser
)

# Define the input type for the final chain, making it compatible with LangServe
class InputChat(TypedDict):
    """Input for the chat endpoint."""
    input: str

# Wrap the RAG chain with history management
chain_with_history = RunnableWithMessageHistory(
    rag_chain,
    get_session_history,
    input_messages_key="input",
    history_messages_key="history",
).with_types(input_type=InputChat)


# --- 5. FastAPI Application Setup ---
app = FastAPI(
    title="LangServe RAG with History",
    version="1.0",
    description="An API server for querying neural connection data with conversational history.",
)

# Add the runnable to the FastAPI app, making it available at the /chain endpoint
add_routes(
    app,
    chain_with_history,
    path="/chain",
)

# --- 6. Run the Server ---
if __name__ == "__main__":
    import uvicorn
    # The server will run on localhost at port 7777
    uvicorn.run(app, host="localhost", port=8889)