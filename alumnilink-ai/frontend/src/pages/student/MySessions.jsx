import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";
import { getErrorMessage } from "../../utils";

const TABS = [
  { key: "upcoming", label: "Upcoming", statuses: ["scheduled"] },
  { key: "completed", label: "Completed", statuses: ["completed"] },
  { key: "cancelled", label: "Cancelled", statuses: ["cancelled", "no_show"] },
];

function FeedbackModal({ session, onClose, onSubmitted }) {
  const [rating, setRating] = useState(5);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const submit = async () => {
    setSubmitting(true);
    setError("");
    try {
      await api.post(`/api/v1/sessions/${session.id}/feedback`, { rating, comment });
      onSubmitted();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to submit feedback."));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 px-4">
      <div className="bg-white rounded-2xl shadow-xl p-6 w-full max-w-sm">
        <h3 className="font-semibold text-gray-900 mb-4">Rate your session with {session.alumni_name}</h3>
        {error && <p className="text-red-600 text-sm mb-3">{error}</p>}
        <div className="flex gap-1 justify-center mb-4">
          {[1, 2, 3, 4, 5].map((n) => (
            <button
              key={n}
              onClick={() => setRating(n)}
              className={`text-3xl ${n <= rating ? "text-yellow-400" : "text-gray-200"}`}
            >
              ★
            </button>
          ))}
        </div>
        <textarea
          value={comment}
          onChange={(e) => setComment(e.target.value)}
          rows={3}
          placeholder="Any comments about the session? (optional)"
          className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none mb-4"
        />
        <div className="flex gap-2">
          <button onClick={onClose} className="flex-1 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">
            Cancel
          </button>
          <button onClick={submit} disabled={submitting} className="flex-1 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 disabled:opacity-50">
            {submitting ? "Submitting..." : "Submit"}
          </button>
        </div>
      </div>
    </div>
  );
}

export default function MySessions() {
  const [sessions, setSessions] = useState([]);
  const [tab, setTab] = useState("upcoming");
  const [loading, setLoading] = useState(true);
  const [feedbackSession, setFeedbackSession] = useState(null);

  const load = () => {
    api.get("/api/v1/sessions/my").then((res) => setSessions(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const activeTab = TABS.find((t) => t.key === tab);
  const filtered = sessions.filter((s) => activeTab.statuses.includes(s.status));

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Sessions</h2>

        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setTab(t.key)}
              className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
                tab === t.key ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && filtered.length === 0 && <p className="text-gray-400">No {activeTab.label.toLowerCase()} sessions.</p>}

        <div className="space-y-4">
          {filtered.map((s) => (
            <div key={s.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900">{s.alumni_name}</h3>
                <StatusBadge status={s.status} />
              </div>
              <p className="text-sm text-gray-600">{format(new Date(s.slot_date), "MMM d, yyyy")}</p>
              <p className="text-xs text-gray-400 mt-1">{s.start_time} – {s.end_time}</p>
              {s.status === "scheduled" && (
                s.meeting_link ? (
                  <a
                    href={s.meeting_link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="mt-3 inline-block px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
                  >
                    Join Meeting →
                  </a>
                ) : (
                  <p className="mt-3 text-xs text-gray-400">
                    Your mentor hasn't added a meeting link yet — check the chat for details closer to the time.
                  </p>
                )
              )}
              {s.status === "completed" && !s.has_feedback && (
                <button
                  onClick={() => setFeedbackSession(s)}
                  className="mt-3 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
                >
                  Leave feedback
                </button>
              )}
              {s.status === "completed" && s.has_feedback && (
                <p className="mt-2 text-xs text-green-600">✓ Feedback submitted</p>
              )}
            </div>
          ))}
        </div>
      </div>

      {feedbackSession && (
        <FeedbackModal
          session={feedbackSession}
          onClose={() => setFeedbackSession(null)}
          onSubmitted={() => {
            setFeedbackSession(null);
            load();
          }}
        />
      )}
    </Layout>
  );
}
