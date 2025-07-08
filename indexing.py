import os
from dotenv import load_dotenv
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from tqdm import tqdm

# Load environment variables
load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "chaiaurdocs"
EMBEDDING_DIM = 3072  # for text-embedding-3-large

# Initialize embedding model
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")

# Check if URL file exists
url_file = "chaiaurdocs_links.txt"
if not os.path.exists(url_file):
    print(f"❌ File '{url_file}' not found.")
    exit(1)

# Load URLs
with open(url_file) as f:
    urls = f.read().splitlines()

if not urls:
    print("⚠️ No URLs found in the file.")
    exit(1)

print(f"📄 Loading {len(urls)} URLs...")
loader = WebBaseLoader(urls)

try:
    docs = loader.load()
except Exception as e:
    print(f"❌ Error loading documents: {e}")
    exit(1)

# Chunk the documents
print("✂️ Chunking documents...")
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(docs)

# Connect to Qdrant
print("🔌 Connecting to Qdrant...")
client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60
)

# Check and create collection if needed
collections = client.get_collections().collections
collection_names = [c.name for c in collections]

if COLLECTION_NAME not in collection_names:
    print(f"📦 Creating collection '{COLLECTION_NAME}'...")
    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(size=EMBEDDING_DIM, distance=Distance.COSINE)
    )
else:
    print(f"📁 Using existing collection '{COLLECTION_NAME}'")

# Initialize vector store
vector_store = QdrantVectorStore(
    client=client,
    collection_name=COLLECTION_NAME,
    embedding=embedding_model,
)

# Upload in batches with progress
print(f"🚀 Uploading {len(chunks)} chunks in batches...")
batch_size = 100

for i in tqdm(range(0, len(chunks), batch_size)):
    batch = chunks[i:i + batch_size]
    try:
        vector_store.add_documents(batch)
    except Exception as e:
        print(f"❌ Error uploading batch {i//batch_size + 1}: {e}")
        continue

print("🎉 Indexing complete!")
