"""Text processing functions for the Splitflap integration."""
from dataclasses import dataclass, field
from typing import List

@dataclass
class Row:
    """Represents a single row of processed text for the display."""
    content: str
    is_continuation: bool = False
    splits_word: bool = False
    has_triple_spaces: bool = False
    complete_words: List[str] = field(default_factory=list)

    def can_be_centered(self) -> bool:
        """Determine if a row's content is suitable for centering."""
        if not self.content or not self.content.strip():
            return False
        if self.has_triple_spaces or self.splits_word or self.is_continuation:
            return False
        content_length = sum(len(word) for word in self.complete_words)
        return (content_length / len(self.content)) <= 0.6 if self.content else False

def process_escaped_chars(text: str) -> str:
    """Process escaped characters for lowercase and uppercase the rest."""
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            result.append(text[i + 1].lower())
            i += 2
        else:
            result.append(text[i].upper())
            i += 1
    return "".join(result)

def split_into_tokens(text: str) -> List[str]:
    """Split text into words and spaces as separate tokens, preserving spacing."""
    tokens = []
    current_word = ""
    i = 0
    while i < len(text):
        if text[i] == ' ':
            if current_word:
                tokens.append(current_word)
                current_word = ""
            space_start = i
            while i < len(text) and text[i] == ' ':
                i += 1
            tokens.append(text[space_start:i])
        else:
            current_word += text[i]
            i += 1
    if current_word:
        tokens.append(current_word)
    return tokens

def fit_to_rows(text: str, row_length: int, mode: str) -> List[Row]:
    """Master function to fit text to rows based on selected mode."""
    processed_text = process_escaped_chars(text)
    tokens = split_into_tokens(processed_text)

    if mode == "none":
        return _fit_to_rows_nooverflow(processed_text, row_length)
    if mode == "hyphen":
        return _fit_to_rows_hyphen(tokens, row_length)
    return _fit_to_rows_newline(tokens, row_length)

def _fit_to_rows_newline(tokens: List[str], row_length: int) -> List[Row]:
    """Fit text to rows, moving whole words to a new line if they don't fit."""
    rows = []
    current_row = ""
    current_words = []
    for token in tokens:
        if len(current_row) + len(token) <= row_length:
            current_row += token
            if not token.isspace():
                current_words.append(token)
        else:
            rows.append(Row(content=current_row, complete_words=current_words, has_triple_spaces="   " in current_row))
            if token.isspace():
                current_row = ""
                current_words = []
            else:
                if len(token) > row_length:
                    while len(token) > row_length:
                        rows.append(Row(content=token[:row_length], splits_word=True))
                        token = token[row_length:]
                    current_row = token
                    current_words = [token] if token else []
                else:
                    current_row = token
                    current_words = [token]

    if current_row:
        rows.append(Row(content=current_row, complete_words=current_words, has_triple_spaces="   " in current_row))
    return rows

def _fit_to_rows_hyphen(tokens: List[str], row_length: int) -> List[Row]:
    """Fit text to rows, breaking words with a hyphen if they don't fit."""
    rows = []
    current_row = ""
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.isspace():
            if len(current_row) + len(token) <= row_length:
                current_row += token
                i += 1
            else:
                rows.append(Row(content=current_row))
                current_row = ""
        elif len(current_row) + len(token) <= row_length:
            current_row += token
            i += 1
        else:
            if not current_row:
                split_point = row_length - 1
                rows.append(Row(content=token[:split_point] + "-", splits_word=True))
                tokens[i] = token[split_point:]
            else:
                rows.append(Row(content=current_row))
                current_row = ""
    if current_row:
        rows.append(Row(content=current_row))
    for i in range(1, len(rows)):
        if rows[i - 1].splits_word:
            rows[i].is_continuation = True
    return rows

def _fit_to_rows_nooverflow(text: str, row_length: int) -> List[Row]:
    """Fit text to rows by simply cutting at the row length."""
    rows = []
    for i in range(0, len(text), row_length):
        rows.append(Row(content=text[i:i + row_length], splits_word=True))
    for i in range(1, len(rows)):
        if rows[i-1].splits_word:
            rows[i].is_continuation = True
    return rows