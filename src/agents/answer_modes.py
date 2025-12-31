from enum import Enum


class AnswerMode(str, Enum):
    QA = "qa"
    LIST = "list"
    EXPAND = "expand"
    SUMMARY = "summary"
