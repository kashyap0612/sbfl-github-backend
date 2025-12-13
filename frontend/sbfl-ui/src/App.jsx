import { useState } from "react";
import { fetchRepoFiles, fetchFileContent } from "./api";

function App() {
  const [repoUrl, setRepoUrl] = useState("");
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState(null);
  const [content, setContent] = useState("");

  async function handleFetchFiles() {
    const data = await fetchRepoFiles(repoUrl);
    setFiles(data.files || []);
    setContent("");
    setSelectedFile(null);
  }

  async function handleFileClick(path) {
    setSelectedFile(path);
    const data = await fetchFileContent(repoUrl, path);
    setContent(data.content || "");
  }

  return (
    <div style={{ padding: "20px", fontFamily: "sans-serif" }}>
      <h2>SBFL GitHub Repo Explorer</h2>

      <input
        style={{ width: "400px" }}
        placeholder="Paste GitHub repo URL"
        value={repoUrl}
        onChange={(e) => setRepoUrl(e.target.value)}
      />

      <button onClick={handleFetchFiles} style={{ marginLeft: "10px" }}>
        Fetch Files
      </button>

      <div style={{ display: "flex", marginTop: "20px" }}>
        <ul style={{ width: "40%", maxHeight: "400px", overflowY: "auto" }}>
          {files.map((file) => (
            <li
              key={file}
              style={{ cursor: "pointer" }}
              onClick={() => handleFileClick(file)}
            >
              {file}
            </li>
          ))}
        </ul>

        <pre
          style={{
            width: "60%",
            padding: "10px",
            background: "#f5f5f5",
            maxHeight: "400px",
            overflowY: "auto"
          }}
        >
          {content}
        </pre>
      </div>
    </div>
  );
}

export default App;
