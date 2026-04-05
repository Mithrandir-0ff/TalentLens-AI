
import os
from dotenv import load_dotenv
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.tools import tool

load_dotenv()

_vector_store = None

def get_vector_store():
    global _vector_store
    if _vector_store is None:
        loader = TextLoader("scout_knowledge.txt", encoding="utf-8")
        docs = loader.load()
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=100)
        all_splits = text_splitter.split_documents(docs)
        
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

        _vector_store = FAISS.from_documents(all_splits, embeddings)
    return _vector_store

@tool
def fetch_scouting(query: str):
    """
    ОБЯЗАТЕЛЬНЫЙ ИНСТРУМЕНТ для начала любого анализа. 
    Используй его ПЕРЕД вызовом статистических инструментов, чтобы получить 
    внутренние стандарты клуба, пороговые значения метрик (thresholds) 
    и специфические требования к тактическим ролям (например, Inverted Winger, False 9). 
    """
    store = get_vector_store() 
    retrieved_docs = store.similarity_search(query, k=2)
    return "\n\n".join([doc.page_content for doc in retrieved_docs])