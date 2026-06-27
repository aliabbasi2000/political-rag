import os
from ollama import Client
from nltk.tokenize import sent_tokenize
try:
    from .embedding_db import get_psql_session, TextEmbedding
except ImportError:
    from embedding_db import get_psql_session, TextEmbedding
    
def populate_vector_database(folder_path="./data/all_articles"):

    session = get_psql_session()
    host = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
    client = Client(host=host)

    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        print(f"Trying: {file_path}")

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                file_content = f.read()

            sentences = sent_tokenize(file_content)
            embeddings = client.embed(model="nomic-embed-text", input=sentences)["embeddings"]
            
            for i, (embedding, sentence) in enumerate(zip(embeddings, sentences)):
                new_embedding = TextEmbedding(
                    embedding=embedding,
                    content=sentence,
                    file_name=filename,
                    sentence_number=i + 1,
                )
                session.add(new_embedding)
            session.commit()

            print(f"Successfully generated embeddings for: {file_path}")

        except IOError as e:
            print(f"Error reading {filename}: {str(e)}")
            continue
        
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
            continue

    return

if __name__ == "__main__":
    populate_vector_database()