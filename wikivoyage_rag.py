import requests
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

HEADERS = {
    "User-Agent": "trip-planner-capstone/1.0"
}


def get_wikivoyage_content(destination):
    try:
        url = "https://en.wikivoyage.org/w/api.php"

        params = {
            "action": "query",
            "prop": "extracts",
            "titles": destination,
            "explaintext": False,
            "format": "json"
        }

        response = requests.get(
            url,
            params=params,
            headers=HEADERS,
            timeout=20
        )

        data = response.json()

        pages = data["query"]["pages"]

        for page in pages.values():
            return page.get("extract", "")

    except Exception as e:
        print("Wikivoyage error:", e)
        return ""


def clean_html(text):
    text = re.sub(r"<.*?>", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def chunk_text(text, chunk_size=900):
    chunks = []

    for i in range(0, len(text), chunk_size):
        chunks.append(text[i:i + chunk_size])

    return chunks


def build_rag(chunks):
    vectorizer = TfidfVectorizer(stop_words="english")

    embeddings = vectorizer.fit_transform(chunks)

    return vectorizer, embeddings


def semantic_search(query,
                    chunks,
                    vectorizer,
                    embeddings,
                    top_k=3):

    query_vector = vectorizer.transform([query])

    scores = cosine_similarity(
        query_vector,
        embeddings
    )[0]

    ranked = scores.argsort()[::-1]

    results = []

    for idx in ranked[:top_k]:
        results.append(chunks[idx])

    return results


def get_travel_context(destination, question):

    raw_text = get_wikivoyage_content(destination)

    if not raw_text:
        return []

    cleaned = clean_html(raw_text)

    chunks = chunk_text(cleaned)

    vectorizer, embeddings = build_rag(chunks)

    return semantic_search(
        question,
        chunks,
        vectorizer,
        embeddings
    )