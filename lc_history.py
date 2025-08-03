# This is code that can be deployed on a server and accessed by mapping it to the corresponding SSH port.

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

from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.messages import HumanMessage

from pydantic import BaseModel, Field
from typing_extensions import TypedDict

os.environ["CUDA_VISIBLE_DEVICES"] = "0,2"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
base_url = "http://localhost:8000/v1"
api_key = "EMPTY"
model_id = "/hpc/fxu244/Documents/Code/LLMs/Qwen3-32B"
store = {}

# 1. Create prompt template
system_template = "You are a smart AI assistant, answer each question."

prompt = ChatPromptTemplate.from_messages([
    ("system", "You're an assistant, answer any questions."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}"),
])

# 2. Create the model
model = ChatOpenAI(base_url=base_url, api_key=api_key, model=model_id)

parser = StrOutputParser()

# Function to get session-specific chat history
# The current issue might be that data sent from the frontend API cannot be stored properly?
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
        # print('here')
        # print(store[session_id].messages)
    return store[session_id]

# 2. Create base chain (without history)
base_chain = prompt | model | parser

# class InputChat(BaseModel):
#     """Input for the chat endpoint."""
#     input: str = Field(
#         ...,
#         description="The human input to the chat system.",
#         extra={"widget": {"type": "chat", "input": "input"}},
#     )

class InputChat(TypedDict):
    """Input for the chat endpoint."""
    input: str
    """Human input"""

# 3. Wrap the base chain with message history
chain_with_history = RunnableWithMessageHistory(
    base_chain,
    get_session_history,
    input_messages_key="input",   # Specify the key name for input messages
    history_messages_key="history",  # Specify the key name for history messages
).with_types(input_type=InputChat)

# 4. App definition
app = FastAPI(
    title="LangChain Server",
    version="1.0",
    description="A simple API server using LangChain's Runnable interfaces",
)

# 5. Add the chain route to the app
add_routes(
    app,
    chain_with_history,
    path="/chain",
)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=7789)
