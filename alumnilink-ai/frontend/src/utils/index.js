export function classNames(...classes) {
  return classes.filter(Boolean).join(" ");
}

// FastAPI error responses come in three different shapes depending on where
// they're raised: a plain string (HTTPException(detail="...")), an object
// with a .reason field (the moderation/screener pipelines), or an ARRAY of
// Pydantic validation-error objects (422s from a model_validator raising
// ValueError, e.g. "start_time must be at least 1 hour from now"). Rendering
// the array/object case directly as JSX ({error}) throws "Objects are not
// valid as a React child" with no error boundary anywhere in this app —
// which blanks the entire page instead of showing anything. Always route
// error display through this instead of reading err.response.data.detail directly.
// Should a connection request still block sending a new one to the same
// alumnus? Pending always blocks. Accepted only blocks while unresolved (no
// session booked yet, or a booked session that hasn't happened yet) — once
// that session is completed/cancelled/no-show, the relationship cycle is
// finished and a follow-up request is legitimate, matching the backend's
// guard in routers/requests.py's send_request.
export function isRequestStillBlocking(r) {
  if (r.status === "pending") return true;
  if (r.status === "accepted") return !r.session_status || r.session_status === "scheduled";
  return false;
}

export function getErrorMessage(err, fallback = "Something went wrong.") {
  const detail = err?.response?.data?.detail;
  if (!detail) return fallback;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail.map((d) => d?.msg || JSON.stringify(d)).join(" ");
  }
  if (typeof detail === "object") {
    return detail.reason || JSON.stringify(detail);
  }
  return fallback;
}

export function truncate(str, n = 100) {
  return str && str.length > n ? str.slice(0, n) + "..." : str;
}
