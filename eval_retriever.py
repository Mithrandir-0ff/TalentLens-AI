import json
import pandas as pd
from knowledge_base import get_vector_store

def load_test_dataset(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def evaluate_retriever(dataset_path, k=3):
    dataset = load_test_dataset(dataset_path)
    
    store = get_vector_store()
    results = []
    
    for item in dataset:
        query = item["query"]
        expected = set(item["expected_ids"])
        
        docs = store.similarity_search(query, k=k)
        
        retrieved = [doc.metadata.get("id") for doc in docs]
        retrieved_set = set(retrieved)
        
        relevant_retrieved = retrieved_set.intersection(expected)
        
        precision = len(relevant_retrieved) / k
        recall = len(relevant_retrieved) / len(expected)
        
        results.append({
            "query": query,
            "precision": precision,
            "recall": recall,
            "found_ids": retrieved,
            "expected_ids": item["expected_ids"]
        })
    
    return pd.DataFrame(results)

if __name__ == "__main__":
    DATASET_PATH = "retriever_test_data.json"
    
    df_results = evaluate_retriever(DATASET_PATH, k=3)

    print("Отчет по качеству ретривера")

    print(f"Mean Precision@: {df_results['precision'].mean():.2f}")
    print(f"Mean Recall@:    {df_results['recall'].mean():.2f}")

    print(df_results[['query', 'precision', 'recall']])
    
    df_results.to_csv("retriever_evaluation_results.csv", index=False)