# База знаний финансового ассистента

## База

Скачать файловое хранилище эмбеддингов можно с гугл диска по ссылке: https://drive.google.com/file/d/1ZJpODxrIUufjtp1993AEv5vnhhjtVp_3/view?usp=sharing

## Состав
1. Учебники по экономике:
    - Financial Markets and Institutions 7th ed. Frederic S. Mishkin, Stanley G. Eakins
    - Principles of macroeconomics 3th ed. David Shapiro, Daniel MacDonald, Steven A. Greenlaw
    - Principles of microeconomics 3th ed. David Shapiro, Daniel MacDonald, Steven A. Greenlaw
    - Principles of economics 3th ed. David Shapiro, Daniel MacDonald, Steven A. Greenlaw
    - Principles of Finance. Julie Danhlquist, Rainford Knight
    - Capital Markets And Securities Laws.
    - Securities Trading: Principles and Procedures. Joel Hasbrouck
2. Курсов по финансовой грамотности от bks и tinkoff
3. Кодексов РФ

## Важные нюансы

### БКС
У bcs на данный момент нет хорошо поддерживаемого api, поэтому перед запуском парсинга необходимо зайти на сайт и скопировать свои куки и заголовки, чтобы не получить блокировку по ip.

### Кодексы
Кодексы получены с помощью парсинга сайта консультант плюс и в данном модуле исопльзуются как готовые json документы

### Учебники
На данный момент очистка учебников требует ручного конфигурирования

## Добавление источников

### Размещение учебников
Для этого в корень проекта необходимо добавить директорию `data/pdf_textbooks`, где в каждой поддиректории будут лежать учебники, которые необходимо предобработать.

### Перевод в txt формат
Далее запускается скрипт `pdf2txt.py`

```bash
python preprocessing/pdf2txt.py
```

### Очистка
В директории `data/txt_data` появляются учебники в txt файлах с md форматированием.
Вам необходимо изучить частые паттерны и заполнить конфиг `meta.json`, который выполняет предобработку,
если хотите работать с учебником напрямую, то пропустите данный шаг

Пример файла `meta.json`:
```json
{
    "remove_patterns": {
        "before_first_chapter": "# 1",
        "after_last_chapter": "#### APPENDIX A",
        "chapter_separator": "# \\d{1,2}",
        "in_chapters": [
            {
                "from": "**CHAPTER OBJECTIVES**",
                "to": "###### \\d{1,2}\\.1"
            },
            {
                "from": "###### BRING IT HOME",
                "to": "# \\d{1,2}"
            }
        ],
        "inline_patterns": [
            {
                "pattern": "\\*\\*FIGURE \\d+\\.\\d+"
            },
            {
                "pattern": "-+"
            },
            {
                "pattern": "http"
            }
        ]
    }
}
```
Здесь есть несоклько типов паттернов:
1. `before_first_chapter`, `after_first_chapter` обозначают строки, до и после которых текст игнорируется. Например, можно убрать оглавление и ссылки на литературу с благодарностями в конце
2. `chapter_separator` - паттерн смены глав в учебнике
3. `in_chapters` паттерны, которые отлавливаются внутри каждой главы. Например, это могут быть задания для самостоятельной подготовки в конце и т.д.
4. `inline_patterns` - просто паттерны, которые применяются к каждой строке. В примере это графики и ссылки

```bash
python preprocessing/clear_txt.py
```

По завершению работы в директории `data/to_split` появятся `N` текстовых файлов

### Сплит на чанки

Для сплита используется `split_cfg.json`, в нем описываются заголовки, по которым будет производиться сплит `MarkdownHeaderTextSplitter`'ом.

```json
{
    "headers_to_split_on": [
        [
            "####",
            "Part"
        ],
        [
            "#####",
            "Chapter"
        ]
    ]
}
```

```bash
python preprocessing/split.py
```

По выполнению в директории chunks появятся `jsonl` файлы с документами. Их уже можно индексировать с сохранением в FAISS
