import { useState } from "react";
import {
  fetchRepoFiles,
  fetchRepoInfo,
  fetchFileContent,
  chatWithFile,
  runSBFL,
} from "./api";
import "./App.css";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [repoError, setRepoError] = useState("");

  const [files, setFiles] = useState([]);
  const [selectedExt, setSelectedExt] = useState("ALL");
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState("");

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");

  const [sbflResult, setSbflResult] = useState(null);
  const [sbflLoading, setSbflLoading] = useState(false);
  const [sbflError, setSbflError] = useState("");

  // ---------------- FETCH FILES (WITH VISIBILITY CHECK) ----------------

  async function handleFetchFiles() {
    if (!repoUrl) return;

    setRepoError("");
    setSbflError("");
    setFiles([]);

    try {
      // 1️⃣ Check repo visibility
      const info = await fetchRepoInfo(repoUrl);

      if (info.visibility === "private") {
        setRepoError("This repository is private. Make it public to continue.");
        return;
      }

      // 2️⃣ Fetch files only if public
      const data = await fetchRepoFiles(repoUrl);
      setFiles(data.files || []);

      setSelectedExt("ALL");
      setSelectedFile(null);
      setContent("");
      setQuestion("");
      setAnswer("");
      setSbflResult(null);

    } catch (err) {
      setRepoError("Invalid repository URL or repository not accessible.");
    }
  }

  // ---------------- FILE CLICK ----------------

  async function handleFileClick(path) {
    setSelectedFile(path);
    const data = await fetchFileContent(repoUrl, path);
    setContent(data.content || "");
    setQuestion("");
    setAnswer("");
  }

  // ---------------- CHAT ----------------

  async function askQuestion() {
    if (!content || !question) return;
    const res = await chatWithFile(content, question);
    setAnswer(res.answer);
  }

  // ---------------- RUN SBFL ----------------

  async function handleRunSBFL() {
    if (!repoUrl) return;

    setSbflLoading(true);
    setSbflError("");

    try {
      const result = await runSBFL(repoUrl);
      setSbflResult(result);
    } catch (e) {
      setSbflError("SBFL failed to run");
    } finally {
      setSbflLoading(false);
    }
  }

  const extensions = ["ALL", ...new Set(files.map((f) => f.extension))];

  const visibleFiles =
    selectedExt === "ALL"
      ? files
      : files.filter((f) => f.extension === selectedExt);

  const sbflLines =
    sbflResult && selectedFile ? sbflResult[selectedFile] || {} : {};

  // ---------------- UI ----------------

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

        {repoError && (
          <p style={{ color: "red", marginTop: "6px" }}>{repoError}</p>
        )}

        <button
          onClick={handleRunSBFL}
          disabled={sbflLoading}
          style={{ marginTop: "8px" }}
        >
          {sbflLoading ? "Running SBFL..." : "Run SBFL"}
        </button>

        <div className="filter">
          <label>Extension</label>
          <select
            value={selectedExt}
            onChange={(e) => setSelectedExt(e.target.value)}
          >
            {extensions.map((ext) => (
              <option key={ext} value={ext}>
                {ext}
              </option>
            ))}
          </select>
        </div>

        <ul className="file-list">
          {visibleFiles.map((file) => (
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
            <pre className="code-block">
              {content.split("\n").map((line, idx) => {
                const lineNumber = idx + 1;
                const score = sbflLines[lineNumber];

                let bg = "transparent";
                if (score >= 0.8) bg = "#4b0000";
                else if (score >= 0.5) bg = "#5c3a00";
                else if (score >= 0.2) bg = "#5c5c00";

                return (
                  <div
                    key={lineNumber}
                    style={{
                      backgroundColor: bg,
                      display: "flex",
                      padding: "0 8px",
                    }}
                  >
                    <span
                      style={{
                        width: 40,
                        color: "#666",
                        userSelect: "none",
                      }}
                    >
                      {lineNumber}
                    </span>
                    <code>{line}</code>
                  </div>
                );
              })}
            </pre>
          ) : (
            <p style={{ color: "#777" }}>
              Select a file to view its contents
            </p>
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

        {/* SBFL OUTPUT */}
        {sbflResult && (
          <section className="sbfl-pane">
            <h4>SBFL Result</h4>
            <pre>{JSON.stringify(sbflResult, null, 2)}</pre>
          </section>
        )}

        {sbflError && <p style={{ color: "red" }}>{sbflError}</p>}
      </main>
    </div>
  );
}

export default App;