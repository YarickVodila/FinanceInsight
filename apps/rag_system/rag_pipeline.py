import os
from langchain.schema import Document
from langchain_community.vectorstores import FAISS
from langchain_community.vectorstores.faiss import DistanceStrategy

from langchain_huggingface import HuggingFaceEmbeddings

from langchain_community.document_loaders import UnstructuredHTMLLoader, SeleniumURLLoader, NewsURLLoader, PlaywrightURLLoader
from langchain_community.document_loaders import BSHTMLLoader
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_community.document_loaders import WebBaseLoader

from langchain_text_splitters import RecursiveCharacterTextSplitter

import re
from bs4 import BeautifulSoup
import unicodedata

from IPython.display import display, Markdown, Latex
from langchain_core.tools import tool

from langchain_mistralai import ChatMistralAI

from langchain.agents import AgentExecutor

from langchain.agents.agent import BaseSingleActionAgent
from langchain_core.messages import HumanMessage


from langchain_core.runnables.graph import CurveStyle, MermaidDrawMethod, NodeStyles
from IPython.display import Image, display

from langgraph.graph import END, START, StateGraph, MessagesState, StateGraph
from langgraph.prebuilt import create_react_agent, ToolNode, tools_condition

from tools import get_news


class FinanceMultiToolAgent:

    def __init__(self, api_key: str):
        # self.api_key = api_key
        self.llm = ChatMistralAI(model="mistral-large-latest", api_key = api_key)
        self.graph = self.create_graph()
        

    def query_or_respond(self, state: MessagesState):
        """Generate tool call for retrieval or respond."""

        llm_with_tools = self.llm.bind_tools([get_news])

        response = llm_with_tools.invoke(state["messages"])
        # MessagesState appends messages to state instead of overwriting
        return {"messages": [response]}


    def create_graph(self):
        graph_builder = StateGraph(MessagesState)

        searcher_news_node = ToolNode([get_news])

        graph_builder.add_node("Supervisor", self.query_or_respond)
        graph_builder.add_node("searcher_news", searcher_news_node)

        graph_builder.set_entry_point("Supervisor")
        graph_builder.add_conditional_edges(
            "Supervisor",
            tools_condition,
            {END: END, "searcher_news": "searcher_news"},
        )
        graph_builder.add_edge("searcher_news", END)

        graph = graph_builder.compile()

        return graph



with open("D:/programming/ITMO/IntroLLM/FinanceInsight/api_keys/api_mistral.txt", "r") as f:
    os.environ["MISTRAL_API_KEY"] = f.readline()

api_key = os.environ["MISTRAL_API_KEY"]

display(Image(FinanceMultiToolAgent(api_key).graph.get_graph().draw_mermaid_png(output_file_path="graph.png")))