import { useState } from "react";
import {
  fetchRepoFiles,
  fetchRepoInfo,
  fetchFileContent,
  chatWithFile,
  runSBFL,
} from "./api";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
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
  try {
    setSelectedFile(path);
    const data = await fetchFileContent(repoUrl, path);
    setContent(data.content || "");
    setQuestion("");
    setAnswer("");
  } catch (e) {
    setRepoError("Failed to load file content");
  }
}

  // ---------------- CHAT ----------------

  async function askQuestion() {
  if (!content || !question) return;
  try {
    const res = await chatWithFile(content, question);
    setAnswer(res.answer);
  } catch (e) {
    setAnswer("Failed to get response from backend");
  }
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

  // Find max suspiciousness in the current file
  const fileScores = Object.values(sbflLines);
  const maxScore = fileScores.length > 0 ? Math.max(...fileScores).toFixed(2) : null;

  // Generate heatmap styles based on string-coerced line number
  const getLineProps = (lineNumber) => {
    const score = sbflLines[String(lineNumber)];
    let style = { display: "block", cursor: "text" };
    if (score !== undefined) {
      if (score >= 0.8) style.backgroundColor = "rgba(255, 0, 0, 0.45)";
      else if (score >= 0.5) style.backgroundColor = "rgba(255, 128, 0, 0.3)";
      else if (score >= 0.2) style.backgroundColor = "rgba(255, 255, 0, 0.15)";
    }
    return { style };
  };

  // ---------------- UI ----------------

  return (
    <div className="app">
      {/* LEFT SIDEBAR */}
      <aside className="sidebar">
        <div className="banner info-banner">
          <strong>Note:</strong> Repository must contain standard discoverable Python test files (<code>test_*.py</code> or <code>*_test.py</code>).
          <div style={{ marginTop: "8px" }}>
            <strong>Demo Repositories (click to use):</strong>
            <ul style={{ paddingLeft: "16px", margin: "4px 0 0 0" }}>
              <li>
                <span 
                  style={{ cursor: "pointer", textDecoration: "underline" }}
                  onClick={() => setRepoUrl("https://github.com/kashyap0612/sbfl-target-repo_1")}
                  title="Click to auto-fill"
                >
                  https://github.com/kashyap0612/sbfl-target-repo_1
                </span>
              </li>
              <li style={{ marginTop: "4px" }}>
                <span 
                  style={{ cursor: "pointer", textDecoration: "underline" }}
                  onClick={() => setRepoUrl("https://github.com/kashyap0612/sbfl_target_repo_2")}
                  title="Click to auto-fill"
                >
                  https://github.com/kashyap0612/sbfl_target_repo_2
                </span>
              </li>
            </ul>
          </div>
        </div>

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
          className={sbflLoading ? "loading-btn" : ""}
        >
          {sbflLoading ? (
            <span className="spinner"></span>
          ) : (
            "Run SBFL"
          )}
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
            <>
              <div className="code-header">
                <span className="file-name">{selectedFile}</span>
                {maxScore !== null && (
                  <span className={`max-score ${maxScore >= 0.8 ? 'danger' : maxScore >= 0.5 ? 'warning' : ''}`}>
                    Max Suspiciousness: {maxScore}
                  </span>
                )}
              </div>
              <div className="editor-container">
                <SyntaxHighlighter
                  language="python"
                  style={vscDarkPlus}
                  showLineNumbers={true}
                  wrapLines={true}
                  lineProps={getLineProps}
                  customStyle={{
                    margin: 0,
                    padding: "16px",
                    background: "transparent",
                    fontSize: "13px"
                  }}
                >
                  {content}
                </SyntaxHighlighter>
              </div>
            </>
          ) : (
            <div className="empty-state">
              <p>Select a file to view its contents</p>
            </div>
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