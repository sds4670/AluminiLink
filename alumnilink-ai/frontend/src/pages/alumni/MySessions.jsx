import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import SessionCard from "../../components/cards/SessionCard";
import api from "../../api/axios";

export default function AlumniSessions() {
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/sessions/mine").then((res) => setSessions(res.data)).finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Sessions</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && sessions.length === 0 && <p className="text-gray-400">No sessions yet.</p>}
        <div className="space-y-4">
          {sessions.map((s) => <SessionCard key={s.id} session={s} />)}
        </div>
      </div>
    </Layout>
  );
}
