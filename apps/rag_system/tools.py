from langchain_community.document_loaders import RecursiveUrlLoader
import re
from bs4 import BeautifulSoup
import unicodedata
from langchain_core.tools import tool
from datetime import datetime


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
    
    # print(day)

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
        
        row = f"| [Ссылка]({article.metadata['source']}) | {article.metadata['description']} |"
        answers+=row

    answers = re.sub(r"[\n\t ]{1, }", " ", answers)
    return answers
