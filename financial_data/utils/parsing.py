from bs4 import BeautifulSoup
from requests import Response


def load_content(response: Response) -> BeautifulSoup:
    response.encoding = "utf-8"
    course_content = response.content
    soup = BeautifulSoup(course_content, "html.parser")
    return soup
