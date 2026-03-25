import os

import numpy as np
import pandas as pd
import torch
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from sklearn.metrics.pairwise import cosine_similarity


def load_docs(file_path, nrows=10000):
    """Load JSONL rows without chunking and apply the E5 passage prefix."""
    print(f"Loading data... (max {nrows} rows)")
    df = pd.read_json(file_path, lines=True, nrows=nrows)

    documents = []
    for _, row in df.iterrows():
        content = f"passage: {row['page_content']}"
        documents.append(
            Document(
                page_content=content,
                metadata={
                    "id": row["id"],
                    "update_date": row.get("update_date"),
                    "categories": row.get("categories"),
                },
            )
        )

    print(f"Loaded {len(documents)} documents.")
    return documents


def get_embedding_model(model_name="intfloat/multilingual-e5-base"):
    """Load the E5 embedding model."""
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"\nLoading embedding model [{model_name}] on {device}...")

    return HuggingFaceEmbeddings(
        model_name=model_name,
        model_kwargs={"device": device},
    )


def create_vector_store(model, documents):
    """Embed each full document as a single vector."""
    print("Creating document embeddings...")
    all_texts = [doc.page_content for doc in documents]
    all_vectors = model.embed_documents(all_texts)

    print(f"Created {len(all_vectors)} vectors (dim: {len(all_vectors[0])})")
    return np.array(all_vectors)


def prepare_vectordb_data(documents, all_vectors):
    """Build a DataFrame where one document maps to one vector."""
    print("\nPreparing vector DB DataFrame...")
    ready_data = []

    for i, doc in enumerate(documents):
        ready_data.append(
            {
                "id": str(doc.metadata.get("id")),
                "update_date": doc.metadata.get("update_date"),
                "categories": doc.metadata.get("categories"),
                "page_content": doc.page_content,
                "vector": all_vectors[i].tolist(),
            }
        )

    df_ready_for_db = pd.DataFrame(ready_data)
    print(f"Built DataFrame with {len(df_ready_for_db)} rows.")
    return df_ready_for_db


def prepare_embedding_artifacts(file_path, nrows=100000):
    """Create the common artifacts used by both search and DB storage."""
    docs = load_docs(file_path, nrows=nrows)
    model = get_embedding_model()
    vectors = create_vector_store(model, docs)
    df_vector_db = prepare_vectordb_data(docs, vectors)
    return docs, model, vectors, df_vector_db


def build_vector_db_dataframe(file_path, nrows=100000):
    """Build only the DataFrame needed for vector DB storage."""
    _, _, _, df_vector_db = prepare_embedding_artifacts(file_path, nrows=nrows)
    return df_vector_db


def search_documents(query, model, doc_vectors, df_vector_db, top_k=5):
    """Search the most similar documents using the E5 query prefix."""
    formatted_query = f"query: {query}"
    query_vector = model.embed_query(formatted_query)
    query_vector = np.array(query_vector).reshape(1, -1)

    similarities = cosine_similarity(query_vector, doc_vectors)[0]
    top_indices = np.argsort(similarities)[::-1][:top_k]

    results = []
    for idx in top_indices:
        matched_row = df_vector_db.iloc[idx]
        results.append(
            {
                "score": similarities[idx],
                "id": matched_row["id"],
                "content": matched_row["page_content"],
            }
        )
    return results


def display_results(results, query):
    print(f"\nSearch results for '{query}':")
    if not results:
        print("No results found.")
        return

    for i, res in enumerate(results, 1):
        print("=" * 70)
        print(f"[{i}] score: {res['score']:.4f} | document id: {res['id']}")
        print("-" * 70)
        print(res["content"].replace("passage: ", "", 1))
    print("=" * 70)


def run_total_pipeline(query, file_path, nrows=100000, verbose=True):
    docs, model, vectors, df_vector_db = prepare_embedding_artifacts(
        file_path,
        nrows=nrows,
    )
    results = search_documents(query, model, vectors, df_vector_db, top_k=5)

    if verbose:
        display_results(results, query)

    return df_vector_db, vectors, results


if __name__ == "__main__":
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, "backend", "vector_store", "arxiv_final.json")

    query = input("\nEnter your project topic: ")
    df_vector_db, vectors, results = run_total_pipeline(query, file_path, nrows=10000)

    print("\n[Reference] DataFrame preview:")
    print(df_vector_db.head(5))
