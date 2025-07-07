# indexing.py

from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore

load_dotenv()

QDRANT_URL = "http://localhost:6333"
COLLECTION_NAME = "chaiaurdocs"
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

# Load URLs from text file (created by crawler.py)
with open("chaiaurdocs_links.txt") as f:
    urls = f.read().splitlines()

print(f"📄 Loading {len(urls)} URLs...")
loader = WebBaseLoader(urls)
docs = loader.load()

print("✂️ Chunking documents...")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

print("🧠 Indexing to Qdrant...")
vector_store = QdrantVectorStore.from_documents(
    documents=chunks,
    embedding=embedding_model,
    url=QDRANT_URL,
    collection_name=COLLECTION_NAME,
)

print("✅ Indexing complete!")
