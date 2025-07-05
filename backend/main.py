from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import os
from langchain_ollama import OllamaEmbeddings, OllamaLLM
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
import shutil
from pydantic import BaseModel

app = FastAPI()

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Config ---
DB_PATH = "documents.db"
FILES_DIR = "files"
VECTORSTORE_DIR = "vectorstore"

os.makedirs(FILES_DIR, exist_ok=True)
os.makedirs(VECTORSTORE_DIR, exist_ok=True)

# --- Init SQLite ---
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- LangChain Models ---
try:
    embeddings = OllamaEmbeddings(model="mistral")
    llm = OllamaLLM(model="mistral")
except Exception as e:
    raise RuntimeError(f"Failed to load Ollama models: {str(e)}")

# --- Request Model ---
class AskRequest(BaseModel):
    doc_id: int
    question: str
    language: str = "english"

# --- Helper: DB Connection ---
def get_db_connection():
    try:
        return sqlite3.connect(DB_PATH)
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=f"DB error: {str(e)}")

# --- Helper: Load Vectorstore ---
def load_vectorstore(doc_id):
    vector_path = os.path.join(VECTORSTORE_DIR, str(doc_id))
    if not os.path.exists(os.path.join(vector_path, "index.faiss")):
        raise HTTPException(status_code=404, detail=f"Vectorstore index not found for doc_id {doc_id}")
    return FAISS.load_local(vector_path, embeddings, allow_dangerous_deserialization=True)

# --- Upload Endpoint ---
@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")

    file_path = os.path.join(FILES_DIR, file.filename)
    with open(file_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Save to DB
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO documents (filename, filepath) VALUES (?, ?)", (file.filename, file_path))
    doc_id = cursor.lastrowid
    conn.commit()
    conn.close()

    # Load & Index
    try:
        from langchain_community.document_loaders import PyPDFLoader
        loader = PyPDFLoader(file_path)
        documents = loader.load()

        vectorstore = FAISS.from_documents(documents, embeddings)
        os.makedirs(os.path.join(VECTORSTORE_DIR, str(doc_id)), exist_ok=True)
        vectorstore.save_local(os.path.join(VECTORSTORE_DIR, str(doc_id)))

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to index document: {str(e)}")

    return {"message": "Upload and index complete", "doc_id": doc_id, "filename": file.filename}

# --- Ask Endpoint ---
@app.post("/ask")
def ask_question(request: AskRequest):
    if not request.question.strip():
        raise HTTPException(status_code=422, detail="Question cannot be empty")

    vectorstore = load_vectorstore(request.doc_id)
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=vectorstore.as_retriever()
    )

    prompt_map = {
        "english": f"Answer in English: {request.question}",
        "hindi": f"प्रश्न का उत्तर हिंदी में दें: {request.question}",
        "telugu": f"తెలుగులో సమాధానం ఇవ్వండి: {request.question}"
    }

    prompt = prompt_map.get(request.language.lower(), prompt_map["english"])
    try:
        response = qa_chain({"query": prompt})
        return {"answer": response["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answering failed: {str(e)}")

# --- List Documents ---
@app.get("/documents")
def list_documents():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, filename FROM documents")
    docs = [{"id": row[0], "filename": row[1]} for row in cursor.fetchall()]
    conn.close()
    return docs

# --- Summarize ---
@app.get("/summarize/{doc_id}")
def summarize_document(doc_id: int, language: str = "english"):
    vectorstore = load_vectorstore(doc_id)
    docs = vectorstore.similarity_search("summarize the document", k=5)
    text = " ".join([doc.page_content for doc in docs])

    prompt_map = {
        "english": f"Summarize in English: {text}",
        "hindi": f"इस दस्तावेज़ का सार हिंदी में दें: {text}",
        "telugu": f"ఈ డాక్యుమెంట్‌ను తెలుగులో సంక్షిప్తీకరించండి: {text}",
    }
    prompt = prompt_map.get(language.lower(), prompt_map["english"])

    try:
        qa_chain = RetrievalQA.from_chain_type(llm=llm, chain_type="stuff", retriever=vectorstore.as_retriever())
        response = qa_chain({"query": prompt})
        return {"summary": response["result"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Summarization failed: {str(e)}")

# --- Delete Endpoint ---
@app.delete("/document/{doc_id}")
def delete_document(doc_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT filepath FROM documents WHERE id = ?", (doc_id,))
    result = cursor.fetchone()
    if not result:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        os.remove(result[0])
        vector_path = os.path.join(VECTORSTORE_DIR, str(doc_id))
        if os.path.exists(vector_path):
            shutil.rmtree(vector_path)
        cursor.execute("DELETE FROM documents WHERE id = ?", (doc_id,))
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")
    finally:
        conn.close()

    return {"message": f"Document {doc_id} deleted"}
