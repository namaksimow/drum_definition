export async function uploadAudio(file) {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch("/api/upload", {
    method: "POST",
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

