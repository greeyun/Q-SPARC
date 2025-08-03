#这是一个可以部署在服务器端上的代码，可以通过映射到ssh对应的端口上访问

#!/usr/bin/env python
import os

from fastapi import FastAPI
# from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langserve import add_routes
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_community.chat_message_histories import ChatMessageHistory
from langchain.memory import ConversationBufferWindowMemory

from langchain_core.runnables.history import  RunnableWithMessageHistory
from langchain_core.messages import  HumanMessage

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

os.environ["CUDA_VISIBLE_DEVICES"] = "0,2"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
base_url ="http://localhost:8000/v1"
api_key ="EMPTY"
model_id ="/hpc/fxu244/Documents/Code/LLMs/Qwen3-32B"
store = {}

# 1. Create prompt template
system_template = "You are a smart AI assitant, answer each question."

prompt = ChatPromptTemplate.from_messages([
    ("system", "You're an assistant, answer any questions."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])


# 2. Create model
model =ChatOpenAI(base_url=base_url, api_key=api_key, model=model_id)

parser = StrOutputParser()

def get_session_history(session_id: str) -> BaseChatMessageHistory:     #现在的问题应该就是 API前端传回来的没办法搞进去？
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
        # print('here')
        # print(store[session_id].messages)
    return store[session_id]


#还是传参数tmd 有问题 搞不回来 没法自动来搞 lang serve就是个傻逼

# 2. 创建基础链（不包含历史记录）
base_chain = prompt | model | parser


# class InputChat(BaseModel):
#     """Input for the chat endpoint."""

#     # The field extra defines a chat widget.
#     # As of 2024-02-05, this chat widget is not fully supported.
#     # It's included in documentation to show how it should be specified, but
#     # will not work until the widget is fully supported for history persistence
#     # on the backend.
#     input: str = Field(
#         ...,
#         description="The human input to the chat system.",
#         extra={"widget": {"type": "chat", "input": "input"}},
#     )

class InputChat(TypedDict):
    """Input for the chat endpoint."""

    input: str
    """Human input"""


# 3. 将基础链包装为带历史记录的链
chain_with_history = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="input",  # 指定输入消息的键名
    history_messages_key="history",  # 指定历史消息的键名
).with_types(input_type=InputChat)



# 4. App definition
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces",
)

# 5. Adding chain route
add_routes(
    app,
    chain_with_history,
    path="/chain",
)



if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=7789)




#需要做