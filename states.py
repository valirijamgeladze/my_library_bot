from enum import Enum, auto

class States(Enum):
    ADD_BOOK_TITLE = auto()
    ADD_BOOK_AUTHOR = auto()
    ADD_CATEGORY_NAME = auto()
    SEARCH_QUERY = auto()