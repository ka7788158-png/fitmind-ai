from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma 
from langchain_huggingface import HuggingFaceEmbeddings
import os

DATA_DIR = "./data"
CHROMA_DIR = "./chroma_db"

def ingest():
    documents = []

    for file in os.listdir(DATA_DIR):
        if file.endswith(".pdf"):
            print(f"Loading {file}...")
            loader = PyPDFLoader(os.path.join(DATA_DIR, file))
            documents.extend(loader.load())

    print(f"Total pages loaded: {len(documents)}")

    splitter = RecursiveCharacterTextSplitter(
        chunk_size = 1000, 
        chunk_overlap = 200
    )

    chunks = splitter.split_documents(documents)
    print(f"Total chunks created: {len(chunks)}")

    print("Embedding and storing in ChromaDB ...")
    embedding = HuggingFaceEmbeddings(model = "all-MiniLM-L6-v2")

    vectorstore = Chroma.from_documents(
        documents = chunks, 
        embedding = embedding, 
        persist_directory = CHROMA_DIR
    )

    print("Done! Knowledge base ready.")

if __name__ == "__main__":
    ingest()