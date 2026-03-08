export async function uploadAudio(file, token = "", tablatureName = "") {
  const formData = new FormData();
  formData.append("file", file);
  if (tablatureName && tablatureName.trim()) {
    formData.append("tablature_name", tablatureName.trim());
  }

  const headers = {};
  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch("/api/upload", {
    method: "POST",
    headers,
    body: formData,
  });

  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPdfByJobId(jobId) {
  const response = await fetch(`/api/pdf?job_id=${encodeURIComponent(jobId)}`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }
  return response.blob();
}

export async function fetchJobById(jobId) {
  const response = await fetch(`/api/jobs/${encodeURIComponent(jobId)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchTablatureByJobId(jobId) {
  const response = await fetch(`/api/tablature?job_id=${encodeURIComponent(jobId)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchCommunityTablatures(query = "") {
  const params = new URLSearchParams();
  if (query.trim()) {
    params.set("q", query.trim());
  }
  const response = await fetch(`/api/community/tablatures?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchCommunityTablatureById(tablatureId) {
  const response = await fetch(`/api/community/tablatures/${encodeURIComponent(tablatureId)}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchCommunityTablatureComments(tablatureId, { limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  const response = await fetch(`/api/community/tablatures/${encodeURIComponent(tablatureId)}/comments?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function createCommunityTablatureComment(token, tablatureId, content) {
  const response = await fetch(`/api/community/tablatures/${encodeURIComponent(tablatureId)}/comments`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ content }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchCommunityTablatureReactions(tablatureId, token = "") {
  const headers = token ? { Authorization: `Bearer ${token}` } : undefined;
  const response = await fetch(`/api/community/tablatures/${encodeURIComponent(tablatureId)}/reactions`, {
    headers,
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function setCommunityTablatureReaction(token, tablatureId, reactionType) {
  const response = await fetch(`/api/community/tablatures/${encodeURIComponent(tablatureId)}/reactions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ reaction_type: reactionType }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function downloadCommunityTablatureJson(tablatureId) {
  const response = await fetch(`/api/community/tablatures/${encodeURIComponent(tablatureId)}/download`);
  if (!response.ok) {
    const text = await response.text();
    throw new Error(text);
  }
  return response.blob();
}

export async function registerUser({ email, password, nickname }) {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, nickname }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function loginUser({ email, password }) {
  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAuthMe(token) {
  const response = await fetch("/api/auth/me", {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updateAuthMe(token, { nickname }) {
  const response = await fetch("/api/auth/me", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ nickname }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPersonalTablatures(token, query = "", options = {}) {
  const limit = Number.isFinite(options.limit) ? Number(options.limit) : 50;
  const offset = Number.isFinite(options.offset) ? Number(options.offset) : 0;
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (query.trim()) {
    params.set("q", query.trim());
  }
  const response = await fetch(`/api/personal/tablatures?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPersonalTablatureById(token, tablatureId) {
  const response = await fetch(`/api/personal/tablatures/${encodeURIComponent(tablatureId)}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updatePersonalTablature(
  token,
  tablatureId,
  { trackFileName = undefined, visibility = undefined, jsonFormat = undefined } = {}
) {
  const body = {};
  if (typeof trackFileName !== "undefined") {
    body.track_file_name = trackFileName;
  }
  if (typeof visibility !== "undefined") {
    body.visibility = visibility;
  }
  if (typeof jsonFormat !== "undefined") {
    body.json_format = jsonFormat;
  }
  const response = await fetch(`/api/personal/tablatures/${encodeURIComponent(tablatureId)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}
