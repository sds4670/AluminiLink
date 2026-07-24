import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";
import { getErrorMessage } from "../../utils";

export default function AlumniSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [completingId, setCompletingId] = useState(null);
  const [editingLinkId, setEditingLinkId] = useState(null);
  const [linkInput, setLinkInput] = useState("");
  const [savingLink, setSavingLink] = useState(false);

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
      setError(getErrorMessage(err, "Failed to mark session complete."));
    } finally {
      setCompletingId(null);
    }
  };

  const startEditLink = (session) => {
    setEditingLinkId(session.id);
    setLinkInput(session.meeting_link || "");
    setError("");
  };

  const saveLink = async (id) => {
    setError("");
    setSavingLink(true);
    try {
      await api.patch(`/api/v1/sessions/${id}/meeting-link`, { meeting_link: linkInput });
      setEditingLinkId(null);
      load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to save meeting link."));
    } finally {
      setSavingLink(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
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

              {s.status === "scheduled" && editingLinkId === s.id && (
                <div className="mt-3 flex gap-2">
                  <input
                    type="url"
                    value={linkInput}
                    onChange={(e) => setLinkInput(e.target.value)}
                    placeholder="https://meet.google.com/..."
                    className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
                  />
                  <button
                    onClick={() => saveLink(s.id)}
                    disabled={savingLink || !linkInput.trim()}
                    className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-medium hover:bg-primary-700 disabled:opacity-50"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => setEditingLinkId(null)}
                    className="px-3 py-1.5 border border-gray-200 text-gray-700 rounded-lg text-xs font-medium hover:bg-gray-50"
                  >
                    Cancel
                  </button>
                </div>
              )}

              {s.status === "scheduled" && editingLinkId !== s.id && (
                <div className="mt-3 flex items-center gap-3 flex-wrap">
                  {s.meeting_link ? (
                    <a href={s.meeting_link} target="_blank" rel="noopener noreferrer" className="text-sm text-primary-600 hover:underline break-all">
                      🔗 {s.meeting_link}
                    </a>
                  ) : (
                    <span className="text-xs text-amber-600">No meeting link added yet — the student can't see how to join.</span>
                  )}
                  <button
                    onClick={() => startEditLink(s)}
                    className="text-xs text-primary-600 hover:underline"
                  >
                    {s.meeting_link ? "Edit link" : "Add meeting link"}
                  </button>
                </div>
              )}

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
