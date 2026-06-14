import os
import re
import wikipedia

# Set a custom User-Agent to prevent the Wikipedia API from blocking the request
wikipedia.set_user_agent("MyCorpusGenerator/1.0 (test@example.com)")

def generate_corpus(search_term="politics", num_articles=1000, output_dir="data/all_articles"):
    # Generate a corpus of Wikipedia articles and save them as text files.

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    articles = []
    search_results = wikipedia.search(search_term, results=num_articles)
    
    for i, title in enumerate(search_results, 1):
        try:
            # Get the page content
            page = wikipedia.page(title, auto_suggest=False)
            articles.append((title, page.content))
            
            # Save to file
            sanitized = re.sub(r'[^a-zA-Z0-9]', '_', title)
            filename = f"{sanitized}.txt"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(page.content)

            print(f"Saved {i}/{len(search_results)}: '{title}'")
                
        except Exception as e:
            print(f"Error processing '{title}': {str(e)}")
            continue
    
    print(f"\nCompleted! Saved {len(articles)} articles!")

if __name__ == "__main__":
    generate_corpus()