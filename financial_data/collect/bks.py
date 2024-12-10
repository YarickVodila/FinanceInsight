import json
from pathlib import Path
import time
from typing import Dict, List, Optional, Tuple

import requests

from ..utils.parsing import load_content


BASE_URL = "https://bcs-express.ru"
OUTPUT_DIR = Path("./data/courses/bks")
REQUEST_PARAMS_PATH = Path("./configs/bks_params.json")
COURSES_DATA_URL = "https://api.bcs.ru/learning/v1/courses?limit=4"
COURSE_DATA_ID = "content"
COURSE_DATA_CLASS = "TjB6 KSLV Ncpb ZKPa"


def load_request_params() -> Tuple[Dict[str, str], Dict[str, str]]:
    with open(str(REQUEST_PARAMS_PATH), "r") as f:
        request_params = json.load(f)
    return request_params["cookies"], request_params["headers"]


def get_courses_links() -> List[str]:
    response = requests.get(COURSES_DATA_URL)
    data = response.json()["data"]
    return [item["url"] for item in data]


def get_course_parts_links(
    course_link: str, cookies: Dict[str, str], headers: Dict[str, str]
) -> List[str]:
    response = requests.get(course_link, cookies=cookies, headers=headers)
    soup = load_content(response)
    hrefs = [elem["href"] for elem in soup.find_all("a")]
    return list(filter(lambda x: BASE_URL in x, hrefs))


def parse_course_part(
    course_part_link: str, cookies: Dict[str, str], headers: Dict[str, str]
) -> Optional[str]:
    response = requests.get(course_part_link, cookies=cookies, headers=headers)
    soup = load_content(response)
    div_tag = soup.find(
        "div", {"data-id": COURSE_DATA_ID, "class": COURSE_DATA_CLASS}
    )
    content = None
    if div_tag:
        content = div_tag.prettify()
    return content


def parse_bks_courses() -> None:
    cookies, headers = load_request_params()
    timeout = 1.0
    courses_links = get_courses_links()
    course_part_links = []
    for course_link in courses_links:
        time.sleep(timeout)
        course_part_links.append(
            get_course_parts_links(course_link, cookies, headers)
        )
    for i in range(len(course_part_links)):
        for j, course_part_link in enumerate(course_part_links[i]):
            time.sleep(timeout)
            course_part_content = parse_course_part(
                course_part_link, cookies, headers
            )
            if course_part_content:
                with open(OUTPUT_DIR / f"{i}_{j}.html", "w") as f:
                    f.write(course_part_content)
    return None


if __name__ == "__main__":
    parse_bks_courses()
