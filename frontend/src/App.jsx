import React, { useState, useEffect } from "react";
import axios from "axios";
import "./App.css";
import image from "./image.png";

function App() {
  const [pdfList, setPdfList] = useState([]);
  const [selectedDocId, setSelectedDocId] = useState("");
  const [messages, setMessages] = useState([]);
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [typing, setTyping] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [summarizing, setSummarizing] = useState(false);
  const [language, setLanguage] = useState("english");

  useEffect(() => {
    fetchDocuments();
  }, []);

  const fetchDocuments = async () => {
    try {
      const res = await axios.get("http://localhost:8000/documents");
      setPdfList(res.data);
      if (res.data.length > 0 && !selectedDocId) {
        setSelectedDocId(res.data[0].id);
      }
    } catch (err) {
      alert("Failed to fetch documents.");
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file || !file.name.endsWith(".pdf")) return alert("Only PDF files are allowed");

    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await axios.post("http://localhost:8000/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setMessages([{ sender: "bot", text: `✅ "${res.data.filename}" uploaded successfully.` }]);
      fetchDocuments();
    } catch (err) {
      alert("Upload failed");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm("Are you sure you want to delete this document?")) return;

    try {
      await axios.delete(`http://localhost:8000/document/${docId}`);
      setMessages([]);
      fetchDocuments();
      alert("Document deleted successfully.");
    } catch (err) {
      console.error("Delete failed", err);
      alert("Failed to delete document.");
    }
  };

  const handleSend = async () => {
    if (!message.trim() || !selectedDocId) return;
    const docId = parseInt(selectedDocId, 10);
    if (isNaN(docId)) return alert("Invalid document ID");

    setMessages((prev) => [...prev, { sender: "user", text: message }]);
    setLoading(true);
    setMessage("");
    setTyping(false);

    try {
      const res = await axios.post("http://localhost:8000/ask", {
        doc_id: docId,
        question: message,
        language,
      });
      setMessages((prev) => [...prev, { sender: "bot", text: res.data.answer }]);
    } catch (err) {
      console.error("Ask error:", err.response?.data || err.message);
      setMessages((prev) => [...prev, { sender: "bot", text: "❌ Error getting response from backend." }]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter" && !loading && message.trim() && selectedDocId) {
      handleSend();
    }
  };

  const handleInputChange = (e) => {
    setMessage(e.target.value);
    setTyping(e.target.value.length > 0);
  };

  const handleSummarize = async () => {
    if (!selectedDocId) return alert("Please select a document.");
    setSummarizing(true);
    setLoading(true);
    try {
      const res = await axios.get(`http://localhost:8000/summarize/${selectedDocId}?language=${language}`);
      setMessages((prev) => [...prev, { sender: "bot", text: `📝 Summary: ${res.data.summary}` }]);
    } catch (err) {
      console.error("Summarize error:", err.response?.data || err.message);
      setMessages((prev) => [...prev, { sender: "bot", text: "❌ Error generating summary." }]);
    } finally {
      setSummarizing(false);
      setLoading(false);
    }
  };

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="logo">
          <img src={image} alt="Logo" className="logo-image" />
        </div>
        <label className="upload-btn">
          <input type="file" hidden onChange={handleFileUpload} />
          {uploading ? "⏳ Uploading..." : "📄 Upload PDF"}
        </label>
      </header>

      <main className="chat-body">
        {messages.length === 0 ? (
          <div className="empty-state">Upload a PDF to start chatting.</div>
        ) : (
          <div className="chat-window">
            {messages.map((msg, i) => (
              <div key={i} className={`chat-message ${msg.sender}`}>
                {msg.text}
              </div>
            ))}
            {loading && !summarizing && <div className="chat-message bot loader">🤖 Thinking...</div>}
            {summarizing && <div className="chat-message bot loader">📝 Generating summary...</div>}
            {typing && !loading && !summarizing && <div className="chat-message bot typing">✍️ User is typing...</div>}
          </div>
        )}
      </main>

      <footer className="chat-footer">
        <div className="footer-input-container">
          <div className="pdf-group">
            <button
              className="delete-btn"
              onClick={() => handleDelete(Number(selectedDocId))}
              disabled={!selectedDocId}
              title="Delete selected PDF"
            >
              🗑️
            </button>
            <select
              className="pdf-selector"
              value={selectedDocId}
              onChange={(e) => setSelectedDocId(e.target.value)}
              disabled={pdfList.length === 0}
            >
              {pdfList.map((doc) => (
                <option key={doc.id} value={doc.id}>
                  {doc.filename}
                </option>
              ))}
            </select>
          </div>

          <input
            className="message-input"
            placeholder="Ask something about the PDF..."
            value={message}
            onChange={handleInputChange}
            onKeyPress={handleKeyPress}
            disabled={loading || pdfList.length === 0}
          />

          <button className="send-btn" onClick={handleSend} disabled={loading || !message.trim()}>
            ➤
          </button>

          <div className="lang-group">
            <select
              className="language-selector"
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              disabled={loading || !selectedDocId}
            >
              <option value="english">English</option>
              <option value="hindi">Hindi</option>
              <option value="telugu">Telugu</option>
            </select>

            <button className="summarize-btn" onClick={handleSummarize} disabled={loading || !selectedDocId}>
              Summarize
            </button>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
