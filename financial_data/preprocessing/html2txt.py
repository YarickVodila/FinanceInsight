import os
from pathlib import Path

import html2text


def html2txt() -> None:
    """
    Convert html files to txt with md format
    """
    html_data_dirs = Path("./data/courses")
    output_dir = Path("./data/txt_data")
    h = html2text.HTML2Text()
    h.ignore_links = True
    h.ignore_images = True
    for data_dir in html_data_dirs.iterdir():
        output_data_dir = output_dir / data_dir.name
        os.makedirs(output_data_dir, exist_ok=True)
        for file in data_dir.iterdir():
            if not (file.suffix == ".html" or file.suffix == ".txt"):
                continue
            with open(file, "r") as f:
                content = f.read()
            transformed = h.handle(content)
            output_path = output_data_dir / file.stem
            with open(f"{output_path}.txt", "w") as f:
                f.write(transformed)


if __name__ == "__main__":
    html2txt()
