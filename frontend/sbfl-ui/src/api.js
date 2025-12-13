const BASE_URL = "http://127.0.0.1:8000";

export async function fetchRepoFiles(repoUrl) {
  const res = await fetch(`${BASE_URL}/repo-files`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl })
  });
  return res.json();
}

export async function fetchFileContent(repoUrl, path) {
  const res = await fetch(`${BASE_URL}/repo-file-content`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ repo_url: repoUrl, path })
  });
  return res.json();
}
