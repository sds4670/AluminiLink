import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";

export default function AlumniSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/v1/sessions/incoming").then((res) => setSessions(res.data)).finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Sessions</h2>
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
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
