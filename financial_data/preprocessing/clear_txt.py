from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Dict, List, Optional, Pattern, Tuple, Union


@dataclass
class RegexPattern:
    pattern: Optional[str]

    def compile(self) -> Optional[Pattern]:
        if not isinstance(self.pattern, str):
            print(
                f"Invalid pattern type: {type(self.pattern)}. Expected a string."
            )
            return None
        try:
            return re.compile(self.pattern)
        except re.error:
            return re.compile(re.escape(self.pattern))


@dataclass
class TextProcessingPatterns:
    before_first_chapter: Optional[Pattern]
    after_last_chapter: Optional[Pattern]
    chapter_separator: Optional[Pattern]
    in_chapters: List[Dict[str, Optional[Pattern]]]
    inline_patterns: List[Optional[Pattern]]

    @classmethod
    def from_config(
        cls, config: Dict[str, Union[str, List[Dict[str, str]]]]
    ) -> "TextProcessingPatterns":
        remove_patterns = config.get("remove_patterns", {})
        return cls(
            before_first_chapter=RegexPattern(
                remove_patterns.get("before_first_chapter")
            ).compile(),
            after_last_chapter=RegexPattern(
                remove_patterns.get("after_last_chapter")
            ).compile(),
            chapter_separator=RegexPattern(
                remove_patterns.get("chapter_separator")
            ).compile(),
            in_chapters=[
                {
                    "from": RegexPattern(chapter.get("from")).compile(),
                    "to": RegexPattern(chapter.get("to")).compile(),
                }
                for chapter in remove_patterns.get("in_chapters", [])
            ],
            inline_patterns=[
                RegexPattern(pattern.get("pattern")).compile()
                for pattern in remove_patterns.get("inline_patterns", [])
            ],
        )


class TextLineProcessor:
    def __init__(self, patterns: TextProcessingPatterns):
        self.patterns = patterns
        self.before_first_chapter_passed = False
        self.ignore_text = False
        self.current_chapter = None

    def should_process_line(self, line: str) -> bool:
        if self.current_chapter:
            self.ignore_text = self._check_in_chapters_to(line)
            if self.ignore_text:
                return False

        self.ignore_text, self.current_chapter = self._check_in_chapters_from(
            line
        )

        if self.ignore_text:
            return False

        return not self._check_inline_patterns(line) and len(line.strip()) > 0

    def check_before_first_chapter(self, line: str) -> bool:
        return bool(
            self.patterns.before_first_chapter
            and self.patterns.before_first_chapter.search(line)
        )

    def check_after_last_chapter(self, line: str) -> bool:
        return bool(
            self.patterns.after_last_chapter
            and self.patterns.after_last_chapter.search(line)
        )

    def check_chapter_start(self, line: str) -> bool:
        return bool(
            self.patterns.chapter_separator
            and self.patterns.chapter_separator.search(line)
        )

    def _check_inline_patterns(self, line: str) -> bool:
        return any(
            pattern and pattern.search(line)
            for pattern in self.patterns.inline_patterns
        )

    def _check_in_chapters_from(
        self, line: str
    ) -> Tuple[bool, Optional[Dict[str, Pattern]]]:
        for pattern in self.patterns.in_chapters:
            if pattern["from"] and pattern["from"].search(line):
                return True, pattern
        return False, None

    def _check_in_chapters_to(self, line: str) -> bool:
        return not bool(
            self.current_chapter
            and self.current_chapter["to"]
            and self.current_chapter["to"].search(line)
        )


class TextFileProcessor:
    def __init__(self, patterns: TextProcessingPatterns):
        self.line_processor = TextLineProcessor(patterns)

    def process_file(self, input_path: Path, output_path: Path) -> None:
        print(f"Processing text data from {input_path}")

        processed_text = []
        total_length = 0

        with open(input_path, "r", encoding="utf-8") as f:
            for line in f:
                total_length += len(line)
                if self.line_processor.check_before_first_chapter(line):
                    self.line_processor.before_first_chapter_passed = True
                if not self.line_processor.before_first_chapter_passed:
                    continue
                if self.line_processor.check_after_last_chapter(line):
                    break
                if self.line_processor.check_chapter_start(line):
                    self.line_processor.current_chapter = None
                if self.line_processor.should_process_line(line):
                    processed_text.append(line)

        result = "".join(processed_text)
        result_len = len(result)

        print(
            f"Original file length: {total_length}, "
            f"processed file length: {result_len}"
        )

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(result)


def clear_txt() -> None:
    """
    Preprocess text data from raw txt files with cleaning configuration,
    which is specified in the meta.json file in each textbook directory.
    After processing, save the processed text to the processed directory.
    """
    txt_dir: Path = Path("./data/txt_data")
    output_dir: Path = Path("./data/to_split")
    os.makedirs(output_dir, exist_ok=True)

    for txt_data_dir in txt_dir.iterdir():
        meta_path = txt_data_dir / "meta.json"
        if not meta_path.exists():
            continue

        with open(meta_path, "r") as f:
            processing_config = json.load(f)

        patterns = TextProcessingPatterns.from_config(processing_config)
        output_subdir = output_dir / txt_data_dir.name
        os.makedirs(output_subdir, exist_ok=True)

        for txt_file in txt_data_dir.iterdir():
            if txt_file.is_file() and txt_file.suffix != ".json":
                processor = TextFileProcessor(patterns)
                processor.process_file(txt_file, output_subdir / txt_file.name)


if __name__ == "__main__":
    clear_txt()
