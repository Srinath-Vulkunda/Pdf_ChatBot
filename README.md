
# 📄 PDF ChatBot

A full-stack AI-powered chatbot that can read and answer questions from uploaded PDF documents in multiple languages (English, Hindi, Telugu).

## ✨ Features

- 🔺 Upload PDF documents via an elegant frontend.
- 🤖 Ask questions and receive answers based on PDF content.
- 🧠 Supports multilingual queries: English, Hindi, Telugu.
- 📝 Generate concise summaries from PDF files.
- 🗑️ Delete uploaded PDFs easily from the interface.
- ⚡ Built with FastAPI, LangChain, React.js, and Ollama for local LLM support.

---

## 🛠️ Tech Stack

| Backend                | Frontend             |
|------------------------|----------------------|
| FastAPI + LangChain    | React.js             |
| Ollama (Mistral Model) | Axios (API requests) |
| FAISS (Vector DB)      | Responsive UI with CSS |

---

## 📂 Folder Structure

```

pdf\_chatBot/
├── backend/
│   ├── main.py
│   └── requirements.txt
└── frontend/
└── src/
├── App.jsx
└── App.css

````

---

## 🚀 Getting Started

### 📌 Prerequisites

- Python 3.9+
- Node.js & npm
- Ollama installed locally (for Mistral model)

### 🔧 Backend Setup

```bash
cd backend
python -m venv venv
source venv/Scripts/activate  # On Windows
pip install -r requirements.txt
uvicorn main:app --reload
````

Make sure Ollama is running and has the **mistral** model downloaded:

```bash
ollama run mistral
```

### 💻 Frontend Setup

```bash
cd frontend
npm install
npm start
```

The React app will start at `http://localhost:3000`.

---

## 🌐 Usage

1. Upload a `.pdf` file.
2. Select a language (English, Hindi, Telugu).
3. Ask questions or click "Summarize" to get the main idea of the PDF.
4. Switch between PDFs and delete them anytime.

---

## 🧠 Powered By

* [LangChain](https://www.langchain.com/)
* [Ollama](https://ollama.com/)
* [FastAPI](https://fastapi.tiangolo.com/)
* [React](https://reactjs.org/)

---



## 🙋‍♂️

**Vulkunda Srinath**
📧 Email: [srinathvulkunda@gmail.com](mailto:srinathvulkunda@gmail.com)
🌐 GitHub: [@Srinath-Vulkunda](https://github.com/Srinath-Vulkunda)

---

## 📃 License

This project is open-source and free to use. You can modify and extend it for educational or personal purposes.

---

## 💡 Future Improvements

* Login and authentication
* Support for multiple file types
* Persistent vector DB (e.g., Pinecone or Chroma)
* Improved translation accuracy

---

