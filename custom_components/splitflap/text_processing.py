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
            return True  # Empty rows can be "centered"
        if self.has_triple_spaces or self.splits_word or self.is_continuation:
            return False
        
        # Heuristic: If non-space characters are less than 60% of the content, it's likely not a full line.
        content_length = sum(len(word) for word in self.complete_words)
        return (content_length / len(self.content)) <= 0.6 if self.content else True


def process_escaped_chars(text: str) -> str:
    """Process escaped characters for lowercase and uppercase the rest."""
    result = []
    i = 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            result.append(text[i + 1].lower())  # Keep escaped char as is
            i += 2
        else:
            result.append(text[i].upper())
            i += 1
    return "".join(result)


def split_into_tokens(text: str) -> List[str]:
    """Split text into words and spaces as separate tokens."""
    return [token for token in text.split(" ") if token]


def fit_to_rows(text: str, row_length: int, mode: str) -> List[Row]:
    """Master function to fit text to rows based on selected mode."""
    processed_text = process_escaped_chars(text)
    words = processed_text.split()
    
    if mode == "none":
        return _fit_to_rows_nooverflow(processed_text, row_length)
    if mode == "hyphen":
        return _fit_to_rows_hyphen(words, row_length)
    # Default to "new line"
    return _fit_to_rows_newline(words, row_length)


def _fit_to_rows_newline(words: List[str], row_length: int) -> List[Row]:
    """Fit text to rows, moving whole words to a new line if they don't fit."""
    rows = []
    current_row_content = ""
    current_row_words = []
    
    for word in words:
        if len(word) > row_length:
            # Word is too long for a single row, must be split
            if current_row_content:
                rows.append(Row(content=current_row_content, complete_words=current_row_words))
                current_row_content = ""
                current_row_words = []

            for i in range(0, len(word), row_length):
                 rows.append(Row(content=word[i:i+row_length], splits_word=True))

        elif len(current_row_content) + len(word) + (1 if current_row_content else 0) <= row_length:
            if current_row_content:
                current_row_content += " "
            current_row_content += word
            current_row_words.append(word)
        else:
            rows.append(Row(content=current_row_content, complete_words=current_row_words))
            current_row_content = word
            current_row_words = [word]
    
    if current_row_content:
        rows.append(Row(content=current_row_content, complete_words=current_row_words))
        
    return rows


def _fit_to_rows_hyphen(words: List[str], row_length: int) -> List[Row]:
    """Fit text to rows, breaking words with a hyphen if they don't fit."""
    rows = []
    current_row_content = ""
    
    for word in words:
        while len(word) > row_length:
            if current_row_content: # Word won't fit, push current row
                rows.append(Row(content=current_row_content))
                current_row_content = ""
            
            split_point = row_length - 1
            rows.append(Row(content=word[:split_point] + "-", splits_word=True))
            word = word[split_point:]

        if len(current_row_content) + len(word) + (1 if current_row_content else 0) <= row_length:
            if current_row_content:
                current_row_content += " "
            current_row_content += word
        else:
            rows.append(Row(content=current_row_content))
            current_row_content = word

    if current_row_content:
        rows.append(Row(content=current_row_content))

    # Mark continuations
    for i in range(1, len(rows)):
        if rows[i-1].splits_word:
            rows[i].is_continuation = True

    return rows


def _fit_to_rows_nooverflow(text: str, row_length: int) -> List[Row]:
    """Fit text to rows by simply cutting at the row length."""
    rows = []
    for i in range(0, len(text), row_length):
        rows.append(Row(content=text[i:i+row_length]))
    return rows
