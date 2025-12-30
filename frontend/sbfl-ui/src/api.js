const BASE_URL = import.meta.env.VITE_API_BASE_URL;

async function post(endpoint, payload) {
  const res = await fetch(`${BASE_URL}${endpoint}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${endpoint}`);
  }

  return res.json();
}

export function fetchRepoInfo(repoUrl) {
  return post("/repo-info", { repo_url: repoUrl });
}

export function fetchRepoFiles(repoUrl) {
  return post("/repo-files", { repo_url: repoUrl });
}

export function fetchFileContent(repoUrl, path) {
  return post("/repo-file-content", {
    repo_url: repoUrl,
    path,
  });
}

export function chatWithFile(fileContent, question) {
  return post("/chat-file", {
    file_content: fileContent,
    question,
  });
}

export function runSBFL(repoUrl) {
  return post("/run-sbfl", { repo_url: repoUrl });
}
