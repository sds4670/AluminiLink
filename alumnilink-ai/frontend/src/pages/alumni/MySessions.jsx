import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";

export default function AlumniSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [completingId, setCompletingId] = useState(null);

  const load = () => {
    api.get("/api/v1/sessions/incoming").then((res) => setSessions(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleComplete = async (id) => {
    setError("");
    setCompletingId(id);
    try {
      await api.patch(`/api/v1/sessions/${id}/complete`);
      load();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to mark session complete.");
    } finally {
      setCompletingId(null);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Sessions</h2>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && sessions.length === 0 && <p className="text-gray-400">No sessions yet.</p>}
        <div className="space-y-4">
          {sessions.map((s) => (
            <div key={s.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-medium text-gray-900">{s.student_name}</h3>
                <StatusBadge status={s.status} />
              </div>
              <p className="text-sm text-gray-600">{format(new Date(s.slot_date), "MMM d, yyyy")}</p>
              <p className="text-xs text-gray-400 mt-1">{s.start_time} – {s.end_time}</p>
              {s.status === "scheduled" && (
                <button
                  onClick={() => handleComplete(s.id)}
                  disabled={completingId === s.id}
                  className="mt-3 px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
                >
                  {completingId === s.id ? "Marking..." : "Mark Complete"}
                </button>
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
