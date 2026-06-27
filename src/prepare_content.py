"""
Pull in more than 5 search results & then consulidate the overlapping results so that we have 5 unique context windows.
"""

from embedding_db import get_psql_session, TextEmbedding
from retrieve_db_content import search_embeddings, get_surrounding_sentences
from ollama import Client
from nltk.tokenize import sent_tokenize
import os

# Check If context window of current match overlaps with context window of existing matches.
def _is_unique_match(existing_matches, current_match, group_window_size=5):
    for existing in existing_matches:
        if existing.file_name != current_match.file_name:
            continue
        if existing.sentence_number > current_match.sentence_number + group_window_size or existing.sentence_number < current_match.sentence_number - group_window_size:
            continue
        else:
            return False
    return True


def get_filtered_matches(search_results, group_window_size=5):
    unique_count = 0
    matches = []
    for result in search_results:
        if unique_count >= 5:
            break
        if _is_unique_match(matches, result, group_window_size=group_window_size):
            unique_count += 1
            matches.append(result)
    return matches


def search_by_query(query, num_matches=5, group_window_size=5):
    session = get_psql_session()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    client = Client(host=host)

    sentences = sent_tokenize(query)
    embeddings = client.embed(model="nomic-embed-text", input=sentences)["embeddings"]

    # Pull in more than 5 search results to ensure after consulidating the overlapping results, we have 5 unique context windows.
    search_result = search_embeddings(query_embedding=embeddings[0], session=session, limit=num_matches * (2 * group_window_size + 1))
    filtered_matches = get_filtered_matches(search_result, group_window_size=group_window_size)

    entry_ids = [match.id for match in filtered_matches]
    file_names = [match.file_name for match in filtered_matches]

    return get_surrounding_sentences(entry_ids, file_names, session, group_window_size=group_window_size)

if __name__ == "__main__":

    query = "Tell me about children's rights in Iran."
    print(f"\n TEST: Searching for query: {query}")
    context = search_by_query(query)
    for i in context:
        print(i, "\n")