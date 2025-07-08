import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from openai import OpenAI

# Load OpenAI API key
load_dotenv()

client = OpenAI()
embedding_model = OpenAIEmbeddings(model="text-embedding-3-large")
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
COLLECTION_NAME = "chaiaurdocs"

# Initialize session state
if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# UI setup
st.set_page_config(page_title="Chai aur Docs Chatbot")
st.title("🫖 Chai aur Docs Chatbot")

# 💾 Load existing vector store
if st.session_state.vector_store is None:
    st.session_state.vector_store = QdrantVectorStore.from_existing_collection(
        url=QDRANT_URL,
        collection_name=COLLECTION_NAME,
        embedding=embedding_model,
        api_key=QDRANT_API_KEY
    )
    st.success("✅ Vector store loaded")

# 💬 Chat interface
st.subheader("Ask your question")

# Show previous messages
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_query = st.chat_input("Ask about Chai aur Docs...")

if user_query:
    # Display user message
    st.chat_message("user").markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})

    with st.spinner("Thinking..."):
        # Get matching chunks from Qdrant
        results = st.session_state.vector_store.similarity_search(user_query, k=4)

        # Build context from matching documents
        context = "\n\n".join([
            f"📄 {doc.metadata.get('source')}\n\n{doc.page_content}"
            for doc in results
        ])

        # Prepare system prompt
        SYSTEM_PROMPT = f"""
        You are a helpful assistant. Use only the following PDF context to answer the user's question.
        If you can't find the answer, say so politely.

        Context:
        {context}
        """

        # Get response from OpenAI
        response = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_query},
            ]
        )

        answer = response.choices[0].message.content

        # Extract source links to show below the answer
        sources = list({doc.metadata.get("source", "").strip() for doc in results if doc.metadata.get("source")})
        source_links = "\n".join([f"- [🔗 Source]({url})" for url in sources if url])

        full_answer = f"{answer}\n\n---\n**📚 Sources:**\n{source_links}" if source_links else answer

    # Show assistant message
    st.chat_message("assistant").markdown(f"🧠 {full_answer}")
    st.session_state.chat_history.append({"role": "assistant", "content": full_answer})
