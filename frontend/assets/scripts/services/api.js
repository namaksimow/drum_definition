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

export async function fetchCourses(query = "", options = {}) {
  const limit = Number.isFinite(options.limit) ? Number(options.limit) : 50;
  const offset = Number.isFinite(options.offset) ? Number(options.offset) : 0;
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (query.trim()) {
    params.set("q", query.trim());
  }
  const response = await fetch(`/api/courses?${params.toString()}`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPublicCourseLessons(courseId) {
  const response = await fetch(`/api/community/courses/${encodeURIComponent(courseId)}/lessons`);
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function createCourse(
  token,
  { title, description = "", visibility = "public", tags = [], coverImagePath = "" }
) {
  const response = await fetch("/api/courses", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({
      title,
      description,
      visibility,
      tags,
      cover_image_path: coverImagePath,
    }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function uploadCourseCover(token, file) {
  const formData = new FormData();
  formData.append("file", file);
  const response = await fetch("/api/courses/cover", {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });
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

export async function fetchPersonalAuthorRoleRequest(token) {
  const response = await fetch("/api/personal/author-role-request", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function createPersonalAuthorRoleRequest(token, message) {
  const response = await fetch("/api/personal/author-role-request", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ message }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminTablatures(token, query = "", options = {}) {
  const limit = Number.isFinite(options.limit) ? Number(options.limit) : 200;
  const offset = Number.isFinite(options.offset) ? Number(options.offset) : 0;
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (query.trim()) {
    params.set("q", query.trim());
  }
  const response = await fetch(`/api/admin/tablatures?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminCourses(token, query = "", options = {}) {
  const limit = Number.isFinite(options.limit) ? Number(options.limit) : 200;
  const offset = Number.isFinite(options.offset) ? Number(options.offset) : 0;
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (query.trim()) {
    params.set("q", query.trim());
  }
  const response = await fetch(`/api/admin/courses?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminTablatureById(token, tablatureId) {
  const response = await fetch(`/api/admin/tablatures/${encodeURIComponent(tablatureId)}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updateAdminTablatureVisibility(token, tablatureId, visibility) {
  const response = await fetch(`/api/admin/tablatures/${encodeURIComponent(tablatureId)}/visibility`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ visibility }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function deleteAdminTablature(token, tablatureId) {
  const response = await fetch(`/api/admin/tablatures/${encodeURIComponent(tablatureId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminTablatureComments(token, tablatureId, { limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  const response = await fetch(
    `/api/admin/tablatures/${encodeURIComponent(tablatureId)}/comments?${params.toString()}`,
    {
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function deleteAdminTablatureComment(token, tablatureId, commentId) {
  const response = await fetch(
    `/api/admin/tablatures/${encodeURIComponent(tablatureId)}/comments/${encodeURIComponent(commentId)}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminCourseById(token, courseId) {
  const response = await fetch(`/api/admin/courses/${encodeURIComponent(courseId)}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updateAdminCourseVisibility(token, courseId, visibility) {
  const response = await fetch(`/api/admin/courses/${encodeURIComponent(courseId)}/visibility`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify({ visibility }),
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function deleteAdminCourse(token, courseId) {
  const response = await fetch(`/api/admin/courses/${encodeURIComponent(courseId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminCourseLessons(token, courseId) {
  const response = await fetch(`/api/admin/courses/${encodeURIComponent(courseId)}/lessons`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminUsers(token, { role = "all", query = "", limit = 200, offset = 0 } = {}) {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (role && String(role).trim()) {
    params.set("role", String(role).trim());
  }
  if (query && String(query).trim()) {
    params.set("q", String(query).trim());
  }
  const response = await fetch(`/api/admin/users?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updateAdminUserAccount(
  token,
  userId,
  { email = undefined, nickname = undefined, role = undefined } = {}
) {
  const body = {};
  if (typeof email !== "undefined") {
    body.email = email;
  }
  if (typeof nickname !== "undefined") {
    body.nickname = nickname;
  }
  if (typeof role !== "undefined") {
    body.role = role;
  }

  const response = await fetch(`/api/admin/users/${encodeURIComponent(userId)}`, {
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

export async function deleteAdminUser(token, userId) {
  const response = await fetch(`/api/admin/users/${encodeURIComponent(userId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchAdminAuthorRoleRequests(token, { status = "pending", limit = 100, offset = 0 } = {}) {
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (status && status.trim()) {
    params.set("status", status.trim());
  }
  const response = await fetch(`/api/admin/author-role-requests?${params.toString()}`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updateAdminAuthorRoleRequest(token, requestId, status, adminMessage = "") {
  const body = { status };
  if (typeof adminMessage === "string" && adminMessage.trim()) {
    body.admin_message = adminMessage.trim();
  }
  const response = await fetch(`/api/admin/author-role-requests/${encodeURIComponent(requestId)}`, {
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

export async function fetchPersonalCourses(token, query = "", options = {}) {
  const limit = Number.isFinite(options.limit) ? Number(options.limit) : 50;
  const offset = Number.isFinite(options.offset) ? Number(options.offset) : 0;
  const params = new URLSearchParams();
  params.set("limit", String(limit));
  params.set("offset", String(offset));
  if (query.trim()) {
    params.set("q", query.trim());
  }
  const response = await fetch(`/api/personal/courses?${params.toString()}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function updatePersonalCourse(
  token,
  courseId,
  { title = undefined, description = undefined, visibility = undefined, tags = undefined, coverImagePath = undefined } = {}
) {
  const body = {};
  if (typeof title !== "undefined") {
    body.title = title;
  }
  if (typeof description !== "undefined") {
    body.description = description;
  }
  if (typeof visibility !== "undefined") {
    body.visibility = visibility;
  }
  if (typeof tags !== "undefined") {
    body.tags = tags;
  }
  if (typeof coverImagePath !== "undefined") {
    body.cover_image_path = coverImagePath;
  }
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}`, {
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

export async function deletePersonalCourse(token, courseId) {
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPersonalCourseLessons(token, courseId) {
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}/lessons`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPersonalCourseLessonProgress(token, courseId) {
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}/lessons/progress`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function setPersonalCourseLessonProgress(token, courseId, lessonId, completed) {
  const response = await fetch(
    `/api/personal/courses/${encodeURIComponent(courseId)}/lessons/${encodeURIComponent(lessonId)}/progress`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify({ completed: Boolean(completed) }),
    }
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function trackPersonalCourseVisit(token, courseId) {
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}/visit`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function fetchPersonalCourseStats(token, courseId) {
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}/stats`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function createPersonalCourseLesson(
  token,
  courseId,
  { title, content = "", position = undefined } = {}
) {
  const body = { title, content };
  if (typeof position !== "undefined") {
    body.position = position;
  }
  const response = await fetch(`/api/personal/courses/${encodeURIComponent(courseId)}/lessons`, {
    method: "POST",
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

export async function updatePersonalCourseLesson(
  token,
  courseId,
  lessonId,
  { title = undefined, content = undefined, position = undefined } = {}
) {
  const body = {};
  if (typeof title !== "undefined") {
    body.title = title;
  }
  if (typeof content !== "undefined") {
    body.content = content;
  }
  if (typeof position !== "undefined") {
    body.position = position;
  }
  const response = await fetch(
    `/api/personal/courses/${encodeURIComponent(courseId)}/lessons/${encodeURIComponent(lessonId)}`,
    {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(body),
    }
  );
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(typeof payload === "object" ? JSON.stringify(payload) : String(payload));
  }
  return payload;
}

export async function deletePersonalCourseLesson(token, courseId, lessonId) {
  const response = await fetch(
    `/api/personal/courses/${encodeURIComponent(courseId)}/lessons/${encodeURIComponent(lessonId)}`,
    {
      method: "DELETE",
      headers: {
        Authorization: `Bearer ${token}`,
      },
    }
  );
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
