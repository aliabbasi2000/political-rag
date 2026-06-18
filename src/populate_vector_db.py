import os
from ollama import embed
from nltk.tokenize import sent_tokenize
from sentence_transformers import SentenceTransformer
from embedding_db import get_psql_session, TextEmbedding

def populate_vector_database(folder_path="./data/all_articles"):

    session = get_psql_session()
    model = SentenceTransformer("models/Qwen3-Embedding-0.6B", device="cpu") #https://huggingface.co/Qwen/Qwen3-Embedding-0.6B

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        print(f"Trying: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            sentences = sent_tokenize(content)
            #embeddings = embed(model="custom_deepseek", input=sentences)["embeddings"]
            embeddings = model.encode(sentences)
            
            for i, (embedding, content) in enumerate(zip(embeddings, sentences)):
                new_embedding = TextEmbedding(
                    embedding=embedding,
                    content=content,
                    file_name=filename,
                    sentence_number=i + 1,
                )
                session.add(new_embedding)
            session.commit()

            print(f"Successfully generated embeddings for: {file_path}")


        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return

if __name__ == "__main__":
    populate_vector_database()