from embedding_db import get_psql_session, TextEmbedding
from ollama import Client
from nltk.tokenize import sent_tokenize
from sqlalchemy import text
import os

query = "What is the human rights situation in Slovakia?"

host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
client = Client(host=host)

sentences = sent_tokenize(query)
embeddings = client.embed(model="nomic-embed-text", input=sentences)["embeddings"]
#print(embeddings[0])

def group_entries(entry_ids, file_names, index_of_interest, group_window_size):
    entry_id_of_interest = entry_ids[index_of_interest]
    file_name_of_interest = file_names[index_of_interest]

    group_idxs = [index_of_interest]

    for idx, (entry_id, file_name) in enumerate(zip(entry_ids, file_names)):
        if idx == index_of_interest:
            continue
        if file_name != file_name_of_interest:
            continue
        if (entry_id >= entry_id_of_interest - group_window_size) and (entry_id <= entry_id_of_interest + group_window_size):
            group_idxs.append(idx)

    return group_idxs


def consolidate_groupings(grouped_entries):
    original_groups = [list(group) for group in grouped_entries]
    combined_groups = []

    while original_groups:
        current_grouping = list(original_groups.pop(0))
        merged_group = set(current_grouping)

        idx = 0
        while idx < len(original_groups):
            other_entry = set(original_groups[idx])
            if merged_group & other_entry:
                merged_group.update(other_entry)
                original_groups.pop(idx)
                idx = 0
                continue
            idx += 1

        combined_groups.append(sorted(merged_group))

    return combined_groups


def get_min_max_ids(entry_ids, file_names, combined_groups, group_window_size):
    min_ids = []
    max_ids = []

    for group in combined_groups:
        group_entry_ids = [entry_ids[idx] for idx in group]
        min_id = min(group_entry_ids) - group_window_size
        max_id = max(group_entry_ids) + group_window_size

        min_ids.append(min_id)
        max_ids.append(max_id)

    return min_ids, max_ids


# Find the most similar sentence in the database to our query using cosine distance
def search_embeddings(query_embedding, session, limit=5):
    
    # <=> operator for computing cosine distance between the query and the embeddings stored in the database
    # <=> expects both operands to be of type vector. So the query_embedding which is a python vector needs to be cast to vector type using CAST()
    sql_query = text("""
        SELECT id, sentence_number, content, file_name, 
                    embedding <=> CAST(:query_embedding AS vector) AS distance
        FROM text_embeddings
        ORDER BY distance
        LIMIT :limit
    """)

    result = session.execute(sql_query, {"query_embedding": query_embedding, "limit": limit})
    return result.fetchall()


def get_surrounding_sentences(entry_ids, file_names, session, group_window_size=3):
    if not entry_ids:
        return []

    grouped_entries = []
    for idx in range(len(entry_ids)):
        grouped_entries.append(group_entries(entry_ids, file_names, index_of_interest=idx, group_window_size=group_window_size))

    combined_groups = consolidate_groupings(grouped_entries)
    min_ids, max_ids = get_min_max_ids(entry_ids, file_names, combined_groups, group_window_size)

    surrounding_sentences = []
    for group, min_id, max_id in zip(combined_groups, min_ids, max_ids):
        file_name = file_names[group[0]]
        sql_query = text("""
            SELECT id, sentence_number, content, file_name
            FROM text_embeddings
            WHERE file_name = :file_name
              AND id >= :min_id AND id <= :max_id
        """)

        result = session.execute(sql_query, {
            "file_name": file_name,
            "min_id": min_id,
            "max_id": max_id,
        })

        surrounding_sentences.append(result.fetchall())

    return surrounding_sentences

if __name__ == "__main__":
    session = get_psql_session()
    query_result = search_embeddings(query_embedding=embeddings[0], session=session, limit=5)

    print("########## Query Result ##########")
    for row in query_result:
        print(f"ID: {row.id}, Sentence Number: {row.sentence_number}, File Name: {row.file_name}, Distance: {row.distance}")

    print("\n########## Surrounding Sentences for each Query Result ##########")
    entry_ids = []
    file_names = []
    for row in query_result:
        entry_ids.append(row.id)
        file_names.append(row.file_name)
    
    surrounding_sentences = get_surrounding_sentences(entry_ids=entry_ids, file_names=file_names, session=session, group_window_size=3)
    for entry_id, surrounding in zip(entry_ids, surrounding_sentences):
        print(f"Surrondings for {entry_id}:")
        for row in surrounding:
            print(f"ID: {row.id}, Sentence Number: {row.sentence_number}, Content: {row.content}, File Name: {row.file_name} \n")