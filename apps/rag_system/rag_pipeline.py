import os
import re

from datetime import datetime
from typing import Literal

from bs4 import BeautifulSoup
import unicodedata
import numpy as np
import pandas as pd 

from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import RecursiveUrlLoader
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_mistralai import ChatMistralAI
from langgraph.graph import END, StateGraph, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver

from .deposit_parser import parse_deposits

FAISS_DB = "C:/Users/Kika-/Desktop/itmo_slivs/llm_project/FinanceInsight/data/index"

EMBEDDING_MODEL_NAME = 'intfloat/multilingual-e5-small'

embedding_model = HuggingFaceEmbeddings(
    model_name = EMBEDDING_MODEL_NAME,
    multi_process = True,
    encode_kwargs = {"normalize_embeddings": True}
)

vector_store = FAISS.load_local(
    FAISS_DB, 
    embedding_model, 
    allow_dangerous_deserialization = True
)



def bs4_extractor(html: str) -> str:            
    """Extracts text from HTML using BeautifulSoup

    Args:
        html (str): HTML content

    Returns:
        str: Extracted text
    """
    soup = BeautifulSoup(html, "lxml")
    # Работает
    text = ' '.join(
        BeautifulSoup(
                    html, "html.parser"
                ).stripped_strings
            )
    text = unicodedata.normalize("NFKD", soup.text).strip()
    text = re.sub(r"[\n\t ]+", " ", text)
    return text 


@tool
def get_news(source: str) -> str:
    """
    Получение последних новостей из различных источников, таких как "rambler", "rbc", "journal.tinkoff"

    Args:
        source: Источник новостей.
    """
    
    date = datetime.now()

    year = date.year
    month = date.month
    day = f"0{date.day}" if date.day < 10 else str(date.day)

    if source == "rambler":
        url = "https://finance.rambler.ru/economics/"

    elif source == "rbc":
        url = f"https://www.rbc.ru/business/{day}/{month}/{year}/"
        # url = f"https://www.rbc.ru/economics/{day}/{month}/{year}/"

    elif source == "journal.tinkoff":
        url = f"https://journal.tinkoff.ru/news"

    # По умолчанию 
    else:
        url = "https://finance.rambler.ru/economics/"


    loader = RecursiveUrlLoader(
        url, 
        extractor=bs4_extractor,
        max_depth = 2,
        encoding = "utf-8"
    )

    data = loader.load()
    
    answers = f"""Последние новости из {source}:\n| Ссылка | Описание |\n|--------|--------|"""

    for article in data[1:]:
        answers += "\n"
        
        source = article.metadata['source']
        description = article.metadata['description'].replace('\n', '')

        row = f"| [Ссылка]({source}) | {description} |"
        answers+=row

    answers = re.sub(r"[\n\t ]{1, }", " ", answers)
    return answers


# @tool("search", return_direct=True) #(response_format="content_and_artifact")
@tool(parse_docstring=True)
def retrieve(query: str):
    """
    Получение ответа на вопросы об экономике, финансах, законах.
    Данные получены из статей, сайтов, 

    Args:
        query: вопрос пользователя.
    """
    
    retrieved_docs = vector_store.similarity_search(query = query, k=2)
    
    found_docs = " ".join([f"Текст:\n{doc.page_content}\nИсточник:\n{doc.metadata}\n\n" for doc in retrieved_docs])

    return found_docs

@tool(parse_docstring=True)
def deposits() -> str:
    
    """
    Получение информации об актуальных вкладах и накопительных счетах: 
        название банка, ставка, период, сумма

    Данные получены на сегодняшний день через https://www.banki.ru/ 
    Используется, когда пользователь спрашивает о вкладах или накопительных счетах

    """
    
    today = datetime.now().strftime("%Y-%m-%d")
    path = f"./deposits_{today}.csv"

    if not os.path.exists(path):
        deposists = parse_deposits()
        deposists.to_csv(path, index=False)
    else: 
        deposists = pd.read_csv(path)

    return "Источник: https://www.banki.ru/products/deposits/?type=14&special[]=14&sort=efficient_rate&order=desc  \n" + deposists.to_string(index=False)

class FinanceMultiAgentRAG:
    def __init__(self, api_key):
        # self.api_key = api_key
        self.llm_supervisor = ChatMistralAI(model="ministral-3b-latest", api_key = api_key, temperature = 0.5)
        self.llm_generator = ChatMistralAI(model="mistral-large-latest", api_key = api_key)

        self.llm_supervisor = self.llm_supervisor.bind_tools([get_news, retrieve, deposits], tool_choice = "any")

        self.news_tool = ToolNode([get_news], name="news_tool")
        self.retrieve_tool = ToolNode([retrieve], name="retrieve_tool")
        self.deposit_tool = ToolNode([deposits], name="deposit_tool")

        

        #Генерируем псевдо случайное значение для памяти модели и создаём конфиг
        self.config = {"configurable": {"thread_id": np.random.randint(1, 10000)}}

        self.graph = self.__create_graph()
        
        

    def __create_graph(self):

        graph_builder = StateGraph(MessagesState)

        graph_builder.add_node("Supervisor", self.query_or_respond)
        graph_builder.add_node("news_tool", self.news_tool)
        graph_builder.add_node("retrieve_tool", self.retrieve_tool)
        graph_builder.add_node("deposit_tool", self.deposit_tool)

        graph_builder.add_node("generate", self.generate)

        graph_builder.set_entry_point("Supervisor")

        graph_builder.add_conditional_edges(
            "Supervisor",
            self.route_by_state, 
            {END: END, "news_tool": "news_tool", "retrieve_tool": "retrieve_tool", "deposit_tool": "deposit_tool"},
        )

        graph_builder.add_edge("retrieve_tool", "generate")
        graph_builder.add_edge("deposit_tool", "generate")
        graph_builder.add_edge("generate", END)
        graph_builder.add_edge("news_tool", END)

        # memory = MemorySaver()
        graph = graph_builder.compile() # checkpointer=memory

        return graph

    def get_response(self, input_message: str) -> str:
        # try:

            
        #     # print(output)
        # except Exception as e:
        #     return f"Произошла ошибка: {e}"

        output = self.graph.invoke({
                "messages": [
                    HumanMessage(content = input_message)
                ]
            }
        )
        
        return output["messages"][-1].content


    def route_by_state(self, state: str) -> Literal["retrieve_tool", "deposit_tool", "news_tool", '__end__']:
        """Определение узла по состоянию"""


        # """
        # Определение узла по состоянию
        
        # Args:
        #     state (AIMessage): ответ агента

        # """

        try:
            if state["messages"][-1].tool_calls[-1]["name"] == "retrieve":
                return "retrieve_tool"
            
            elif state["messages"][-1].tool_calls[-1]["name"] == "deposits":
                return "deposit_tool"
            
            elif state["messages"][-1].tool_calls[-1]["name"] == "get_news":
                return "news_tool"
        except:
            return '__end__'
        
    
    def query_or_respond(self, state: MessagesState):
        """Вызов tool функций"""
        # """
        # Вызов tool функций

        # Args:
        #     state (MessagesState): состояние агента 
        
        # """

        response = self.llm_supervisor.invoke(state["messages"])
        return {"messages": [response]}



    def generate(self, state: MessagesState):
        """Ответь на вопрос по контексту"""

        # Get generated ToolMessages
        recent_tool_messages = []
        
        for message in reversed(state["messages"]):
            if message.type == "tool":
                recent_tool_messages.append(message)
            else:
                break
        
        tool_messages = recent_tool_messages[::-1]

        docs_content = "\n\n".join(doc.content for doc in tool_messages)


        system_message_content = f"""
        Ты являешь помощником для ответа на вопросы по финансовому анализу.
        Используй контекст ниже для ответа на вопрос, а также указывай источник информации из контекста.
        Если не знаешь ответ на вопрос, напиши "Я не знаю ответа на данный вопрос".
        
        Контекст:
        {docs_content}
        """
        
        conversation_messages = [message for message in state["messages"] if message.type in ("human", "system") or (message.type == "ai" and not message.tool_calls)]
        prompt = [SystemMessage(system_message_content)] + conversation_messages

        # Run
        response = self.llm_generator.invoke(prompt)
        return {"messages": [response]}

        


# # Image(pipeline.graph.get_graph().draw_mermaid_png(output_file_path="graph.png"))

# # input_message = "Привет, какие финансовые законы ты знаешь?"
# input_message = "Найди последние новости из источника Tinkoff Journal"

# for step in pipeline.graph.stream({"messages": [{"role": "user", "content": input_message}]},stream_mode="values",):
#     step["messages"][-1].pretty_print()