// Thin client over the FastAPI backend.
const base = "/api";

async function http(path, options = {}) {
  const res = await fetch(base + path, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}));
    throw new Error(detail.detail || `Request failed (${res.status})`);
  }
  return res.json();
}

export const api = {
  config: () => http("/config"),
  listRequests: () => http("/requests"),
  getRequest: (id) => http(`/requests/${id}`),
  createRequest: (body) =>
    http("/requests", { method: "POST", body: JSON.stringify(body) }),
  refine: (id, content) =>
    http(`/requests/${id}/refine`, {
      method: "POST",
      body: JSON.stringify({ content }),
    }),
  setStatus: (id, status) =>
    http(`/requests/${id}/status`, {
      method: "POST",
      body: JSON.stringify({ status }),
    }),
  addComment: (id, body) =>
    http(`/requests/${id}/comments`, {
      method: "POST",
      body: JSON.stringify(body),
    }),
};
