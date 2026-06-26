"""
Pull in more than 5 search results & then consulidate the overlapping results so that we have 5 unique context windows.
"""

from embedding_db import TextEmbedding

# Check If context window of current match overlaps with context window of existing matches.
def is_unique_match(existing_matches, current_match, group_window_size=5):
    for existing in existing_matches:
        if existing.file_name != current_match.file_name:
            continue
        if existing.sentence_number > current_match.sentence_number + group_window_size or existing.sentence_number < current_match.sentence_number - group_window_size:
            continue
        else:
            return False
    return True


if __name__ == "__main__":
    # test is_unique_match function
    existing_matches = [TextEmbedding(file_name="file1.txt", sentence_number=10), TextEmbedding(file_name="file1.txt", sentence_number=18)]
    current_match = TextEmbedding(file_name="file1.txt", sentence_number=14)
    print(is_unique_match(existing_matches, current_match))