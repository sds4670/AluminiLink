import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";

export default function MentorshipRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [expandedId, setExpandedId] = useState(null);
  const [error, setError] = useState("");

  const load = () => {
    api.get("/api/v1/requests/incoming").then((res) => setRequests(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleAccept = async (id) => {
    setError("");
    try {
      await api.patch(`/api/v1/requests/${id}/accept`);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to accept request.");
    }
  };

  const handleReject = async (id) => {
    setError("");
    try {
      await api.patch(`/api/v1/requests/${id}/reject`);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to reject request.");
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Mentorship Requests</h2>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && requests.length === 0 && <p className="text-gray-400">No pending requests.</p>}

        <div className="space-y-4">
          {requests.map((r) => {
            const expanded = expandedId === r.id;
            return (
              <div key={r.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="font-semibold text-gray-900">{r.student_name}</h3>
                    <p className="text-xs text-gray-500">{r.department}</p>
                    <p className="text-xs text-gray-400 mt-0.5">{format(new Date(r.created_at), "MMM d, yyyy")}</p>
                  </div>
                  {r.screening_score != null && (
                    <span className="text-xs font-semibold px-2.5 py-1 rounded-full bg-primary-50 text-primary-700">
                      Score: {r.screening_score.toFixed(2)}
                    </span>
                  )}
                </div>

                <p className="text-xs text-gray-500 mt-2">
                  <span className="font-medium text-gray-700">Career goal:</span> {r.career_goal}
                </p>

                <button
                  onClick={() => setExpandedId(expanded ? null : r.id)}
                  className="text-xs text-primary-600 hover:underline mt-2"
                >
                  {expanded ? "Hide message" : "View full message"}
                </button>

                {expanded && r.message && (
                  <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 mt-2 italic">"{r.message}"</p>
                )}

                <div className="flex gap-2 mt-4">
                  <button
                    onClick={() => handleAccept(r.id)}
                    className="flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
                  >
                    Accept
                  </button>
                  <button
                    onClick={() => handleReject(r.id)}
                    className="flex-1 px-3 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
                  >
                    Reject
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </Layout>
  );
}
