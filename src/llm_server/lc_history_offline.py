#!/usr/bin/env python
import os

from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import SimpleChatModel
from langserve import add_routes
from langchain_core.messages import  HumanMessage, AIMessage
from langchain_core.chat_history import  BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import  RunnableWithMessageHistory
from langchain_litellm import ChatLiteLLM
from langchain_community.llms.vllm import VLLM,VLLMOpenAI
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


os.environ["CUDA_VISIBLE_DEVICES"] = "2"
os.environ["NO_PROXY"] = "localhost,127.0.0.1"
base_url ="http://localhost:8000/v1"
api_key ="EMPTY"
model_id ="/hpc/fxu244/Documents/Code/LLMs/Qwen3-32B"

# 2. Create model
model =ChatOpenAI(base_url=base_url, api_key=api_key, model=model_id)  

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are a helpful assistant. Answer all questions to me.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | model

with_message_history = RunnableWithMessageHistory(
    chain,
    get_session_history,
    input_messages_key="messages",
)

config = {"configurable": {"session_id": "abc11"}}

response = with_message_history.invoke(
    {"messages": [HumanMessage(content="hi! I'm todd")], "language": "Spanish"},
    config=config,
)

print(response.content)
config = {"configurable": {"session_id": "abc11"}}

response = with_message_history.invoke(
    {"messages": [HumanMessage(content="whats my name?")], "language": "Spanish"},
    config=config,
)

print(response.content)