import os
from getpass import getpass
from langchain_community.vectorstores import FAISS
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from openai import OpenAI


# ============================================
# 📂 Configuration
# ============================================
PDF_PATH = "C:/Users/LENOVO/Desktop/Final Year Project/rag.pdf"
INDEX_PATH = "./qa_index"
MODEL_NAME = "gpt-5-nano"

# ============================================
# 📥 Load PDF
# ============================================
print("Loading PDF...")
loader = PyPDFLoader(PDF_PATH)
documents = loader.load()

# ============================================
# ✂ Split into chunks
# ============================================
print("Splitting document...")
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200
)
chunks = splitter.split_documents(documents)

# ============================================
# 🔎 Create Embeddings
# ============================================
embedding = OpenAIEmbeddings(openai_api_key=api_key)

# ============================================
# 🧠 Create or Load FAISS Index
# ============================================
if os.path.exists(INDEX_PATH):
    print("Loading existing FAISS index...")
    vectorstore = FAISS.load_local(
        INDEX_PATH,
        embedding,
        allow_dangerous_deserialization=True
    )
else:
    print("Creating new FAISS index...")
    vectorstore = FAISS.from_documents(chunks, embedding)
    vectorstore.save_local(INDEX_PATH)
    print("QA Index created successfully!")

# ============================================
# 🎯 QA SYSTEM PROMPT
# ============================================
qa_prompt = """
You are a Senior Software Quality Assurance AI Agent.

Your job:
1. Analyze the given project document.
2. Identify structural issues.
3. Detect missing sections.
4. Suggest improvements.
5. Highlight risks.
6. Provide a professional QA Report.

Format your response as:

1. Overall Assessment
2. Strengths
3. Issues Found
4. Risk Analysis
5. Recommendations
6. Final QA Verdict

Be professional and detailed.
"""

print("\nQA AI Agent Ready!")
print("Type 'review' to analyze the whole document.")
print("Ask any question about the project.")
print("Type 'exit' to quit.\n")

# ============================================
# 🔁 CHAT LOOP
# ============================================
while True:
    try:
        query = input("You: ").strip()

        if not query:
            continue

        if query.lower() == "exit":
            print("Goodbye!")
            break

        # ------------------------------------
        # 📋 FULL DOCUMENT REVIEW
        # ------------------------------------
        if query.lower() == "review":
            print("Generating full QA report...")

            context = "\n".join([doc.page_content for doc in chunks])

            messages = [
                {"role": "system", "content": qa_prompt},
                {"role": "user", "content": f"Project Document:\n{context}"}
            ]

        # ------------------------------------
        # 🔎 RAG QUESTION ANSWERING
        # ------------------------------------
        else:
            docs = vectorstore.similarity_search(query, k=3)

            if not docs:
                print("No relevant information found in document.\n")
                continue

            context = "\n".join([doc.page_content for doc in docs])

            messages = [
    {
        "role": "system",
        "content": "You are a helpful QA assistant. Use the provided context to answer. If answer is not clearly in context, say what is available."
    },
    {
        "role": "user",
        "content": f"Context:\n{context}\n\nQuestion:\n{query}"
    }
]
        print("\nDEBUG: Retrieved documents:", len(docs))
        print("DEBUG: Context length:", len(context))
        # ------------------------------------
        # 🤖 OpenAI Call
        # ------------------------------------
        response = client.chat.completions.create(
            model="gpt-5-nano",
            messages=messages,
            max_completion_tokens=700,
        )

        answer = response.choices[0].message.content

        print("\nAI Response:\n")
        print(answer)
        print("\n" + "-"*60 + "\n")

    except Exception as e:
        print("Error occurred:", e)