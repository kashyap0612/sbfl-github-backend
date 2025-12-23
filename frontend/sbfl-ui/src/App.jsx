import { useState } from "react";
import { fetchRepoFiles, fetchFileContent, chatWithFile } from "./api";
import "./App.css";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [files, setFiles] = useState([]);
  const [selectedExt, setSelectedExt] = useState("ALL");
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState("");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  async function handleFetchFiles() {
    const data = await fetchRepoFiles(repoUrl);
    setFiles(data.files || []);
    setSelectedExt("ALL");
    setSelectedFile(null);
    setContent("");
    setQuestion("");
    setAnswer("");
  }

  async function handleFileClick(path) {
    setSelectedFile(path);
    const data = await fetchFileContent(repoUrl, path);
    setContent(data.content || "");
    setQuestion("");
    setAnswer("");
  }

  async function askQuestion() {
    if (!content || !question) return;
    const res = await chatWithFile(content, question);
    setAnswer(res.answer);
  }

  const extensions = ["ALL", ...new Set(files.map(f => f.extension))];

  const visibleFiles =
    selectedExt === "ALL"
      ? files
      : files.filter(f => f.extension === selectedExt);

  return (
    <div className="app">
      {/* LEFT SIDEBAR */}
      <aside className="sidebar">
        <h3>Repository</h3>

        <input
          className="repo-input"
          placeholder="GitHub repository URL"
          value={repoUrl}
          onChange={(e) => setRepoUrl(e.target.value)}
        />

        <button onClick={handleFetchFiles}>Fetch files</button>

        <div className="filter">
          <label>Extension</label>
          <select
            value={selectedExt}
            onChange={(e) => setSelectedExt(e.target.value)}
          >
            {extensions.map(ext => (
              <option key={ext} value={ext}>
                {ext}
              </option>
            ))}
          </select>
        </div>

        <ul className="file-list">
          {visibleFiles.map(file => (
            <li
              key={file.path}
              className={`file-item ${
                selectedFile === file.path ? "active" : ""
              }`}
              onClick={() => handleFileClick(file.path)}
              title={file.path}
            >
              {file.path}
            </li>
          ))}
        </ul>
      </aside>

      {/* RIGHT WORKSPACE */}
      <main className="workspace">
        {/* CODE VIEW */}
        <section className="code-pane">
          {content ? (
            <SyntaxHighlighter
              language={selectedFile?.split(".").pop()}
              style={vscDarkPlus}
              customStyle={{
                background: "transparent",
                margin: 0,
                fontSize: "13px",
              }}
            >
              {content}
            </SyntaxHighlighter>

          ) : (
            <p style={{ color: "#777" }}>Select a file to view its contents</p>
          )}
        </section>

        {/* CHAT */}
        <section className="chat-pane">
          <div className="chat-messages">
            {answer && <pre>{answer}</pre>}
          </div>

          {content && (
            <div className="chat-input">
              <textarea
                placeholder="Ask a question about this file…"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    askQuestion();
                  }
                }}
              />
              <button onClick={askQuestion}>➤</button>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;