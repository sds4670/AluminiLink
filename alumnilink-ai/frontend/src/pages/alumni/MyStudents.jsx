import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function MyStudents() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/requests/mine")
      .then((res) => setRequests(res.data.filter((r) => r.status === "accepted")))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Students</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && requests.length === 0 && <p className="text-gray-400">No accepted mentees yet.</p>}
        <div className="space-y-3">
          {requests.map((r) => (
            <div key={r.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p className="text-sm font-medium text-gray-900">Student #{r.student_id}</p>
              <p className="text-xs text-gray-400 mt-0.5">Request #{r.id} · Accepted</p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
