import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { getErrorMessage, isRequestStillBlocking } from "../../utils";

const DIMENSION_LABELS = {
  intent: "Intent",
  professional_tone: "Professional Tone",
  personalisation: "Personalisation",
  message_quality: "Message Quality",
};

function ScoreBar({ label, value }) {
  const pct = Math.round((value / 0.25) * 100);
  const color = pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500";
  return (
    <div>
      <div className="flex justify-between text-xs text-gray-600 mb-1">
        <span>{label}</span>
        <span>{value.toFixed(2)} / 0.25</span>
      </div>
      <div className="w-full h-2 bg-gray-100 rounded-full overflow-hidden">
        <div className={`h-full ${color} transition-all`} style={{ width: `${Math.min(pct, 100)}%` }} />
      </div>
    </div>
  );
}

export default function SendRequest() {
  const { alumniId } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [alumni, setAlumni] = useState(null);
  const [screener, setScreener] = useState(null);
  const [checking, setChecking] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [blockedStatus, setBlockedStatus] = useState(null);

  useEffect(() => {
    Promise.all([
      api.get(`/api/v1/profiles/alumni/${alumniId}`),
      api.get("/api/v1/requests/my").catch(() => ({ data: [] })),
    ]).then(([profileRes, reqRes]) => {
      setAlumni(profileRes.data);
      const existing = reqRes.data.find(
        (r) => r.alumni_user_id === Number(alumniId) && isRequestStillBlocking(r)
      );
      setBlockedStatus(existing?.status || null);
    });
  }, [alumniId]);

  const wordCount = message.trim() ? message.trim().split(/\s+/).length : 0;

  const handlePreview = async () => {
    setError("");
    setChecking(true);
    try {
      const res = await api.post("/api/v1/screener/check", { message });
      setScreener(res.data);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to check message."));
    } finally {
      setChecking(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/api/v1/requests/", { alumni_id: Number(alumniId), message });
      navigate("/student/requests");
    } catch (err) {
      const detail = err.response?.data?.detail;
      if (detail && typeof detail === "object" && !Array.isArray(detail) && "breakdown" in detail) {
        setScreener(detail);
        setError("Message did not pass screening — see feedback below.");
      } else {
        setError(getErrorMessage(err, "Failed to send request."));
      }
    } finally {
      setSubmitting(false);
    }
  };

  const canSubmit = screener?.passed === true;

  return (
    <Layout>
      <div className="max-w-xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Send Connection Request</h2>

        {alumni && (
          <div className="bg-primary-50 border border-primary-100 rounded-xl p-4 mb-6">
            <p className="text-sm font-semibold text-primary-900">To: {alumni.full_name}</p>
            <p className="text-xs text-primary-600 mt-0.5">{alumni.designation}{alumni.company ? ` @ ${alumni.company}` : ""}</p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        {blockedStatus ? (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
            <p className="text-sm text-gray-700">
              {blockedStatus === "accepted"
                ? `You're already connected with ${alumni?.full_name || "this alumnus"}. Continue the conversation in chat instead of sending a new request.`
                : `You already have a pending request with ${alumni?.full_name || "this alumnus"}. Wait for them to accept or reject it before sending another.`}
            </p>
            <button
              type="button"
              onClick={() => navigate("/student/requests")}
              className="mt-4 px-4 py-2 text-sm border border-gray-200 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              {blockedStatus === "accepted" ? "Go to Chat" : "View My Requests"}
            </button>
          </div>
        ) : (
        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
          <div>
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-medium text-gray-700">Message</label>
              <span className={`text-xs ${wordCount < 30 ? "text-red-500" : "text-gray-400"}`}>
                {wordCount} words {wordCount < 30 ? "(min 30)" : ""}
              </span>
            </div>
            <textarea
              value={message}
              onChange={(e) => {
                setMessage(e.target.value);
                setScreener(null);
              }}
              rows={7}
              required
              placeholder="Introduce yourself, mention something specific about the alumnus, and explain what mentorship you're looking for..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          <button
            type="button"
            onClick={handlePreview}
            disabled={checking || wordCount === 0}
            className="w-full py-2.5 border border-primary-200 text-primary-700 rounded-lg text-sm font-semibold hover:bg-primary-50 disabled:opacity-50"
          >
            {checking ? "Checking..." : "Preview screening"}
          </button>

          {screener && (
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm font-semibold text-gray-900">
                  Score: {screener.score.toFixed(2)} / 1.00
                </span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${screener.passed ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"}`}>
                  {screener.passed ? "Passed" : "Needs work"}
                </span>
              </div>
              {Object.entries(screener.breakdown).map(([key, value]) => (
                <ScoreBar key={key} label={DIMENSION_LABELS[key] || key} value={value} />
              ))}
              {screener.suggestions.length > 0 && (
                <ul className="text-xs text-gray-600 list-disc list-inside space-y-1 pt-1">
                  {screener.suggestions.map((s) => <li key={s}>{s}</li>)}
                </ul>
              )}
            </div>
          )}

          <div className="flex gap-3">
            <button type="button" onClick={() => navigate(-1)} className="flex-1 py-2.5 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting || !canSubmit}
              title={!canSubmit ? "Preview and pass screening first (score ≥ 0.6)" : ""}
              className="flex-1 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 disabled:opacity-50"
            >
              {submitting ? "Sending..." : "Submit request"}
            </button>
          </div>
        </form>
        )}
      </div>
    </Layout>
  );
}
