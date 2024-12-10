from pathlib import Path
from typing import List

import requests

from ..utils.parsing import load_content


OUTPUT_DIR = Path("./data/courses/tinkoff")
BASE_URL = "https://journal.tinkoff.ru"
COURSES_URL = "https://journal.tinkoff.ru/pro/page/about/"
COURSES_TEXT = "Деньги"
COURSES_CLASS = "_heading_juhjt_1"
LESSON_CARD_CLASS = "_lessonCard_1u9fj_9"
COURSE_DATA_TAGS = ["h1", "div", "div"]
COURSE_DATA_CLASSES = [
    "_headerTitle_1cm63_125",
    "_subtitle_1cm63_146",
    "_articleView_12tln_1",
]


def get_courses_links() -> List[str]:
    response = requests.get(COURSES_URL)
    soup = load_content(response)
    h2_tag = soup.find("h2", {"class": COURSES_CLASS}, string=COURSES_TEXT)
    parent_div = h2_tag.find_parent("div")
    next_div = parent_div.find_next_sibling("div")
    links = next_div.find_all("a")
    return [link["href"] for link in links]


def get_course_parts_links(course_href: str) -> List[str]:
    response = requests.get(BASE_URL + course_href)
    soup = load_content(response)
    course_parts = soup.find_all("div", {"class": LESSON_CARD_CLASS})
    course_parts_links = [part.find("a")["href"] for part in course_parts]
    return course_parts_links


def parse_course_part(course_part_link: str) -> str:
    response = requests.get(BASE_URL + course_part_link)
    soup = load_content(response)
    course_content = ""
    for tag, item_class in zip(COURSE_DATA_TAGS, COURSE_DATA_CLASSES):
        element = soup.find(tag, {"class": item_class})
        if not element:
            return course_content
        course_content += element.prettify()
    return course_content


def parse_tinkoff_courses() -> None:
    courses_links = get_courses_links()
    courses_parts_links = [
        get_course_parts_links(course_link) for course_link in courses_links
    ]
    for i in range(len(courses_parts_links)):
        for j, course_part_link in enumerate(courses_parts_links[i]):
            course_content = parse_course_part(course_part_link)
            if course_content:
                with open(OUTPUT_DIR / f"{i}_{j}.html", "w") as f:
                    f.write(course_content)
    return None


if __name__ == "__main__":
    parse_tinkoff_courses()
