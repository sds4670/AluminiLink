import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import RequestCard from "../../components/cards/RequestCard";
import api from "../../api/axios";

export default function MentorshipRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get("/api/requests/mine").then((res) => setRequests(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const handleAccept = async (id) => {
    await api.patch(`/api/requests/${id}`, { status: "accepted" });
    load();
  };

  const handleReject = async (id) => {
    const reason = window.prompt("Reason for declining (optional):");
    await api.patch(`/api/requests/${id}`, { status: "rejected", rejection_reason: reason || null });
    load();
  };

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Mentorship Requests</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && requests.length === 0 && <p className="text-gray-400">No requests yet.</p>}
        <div className="space-y-4">
          {requests.map((r) => (
            <RequestCard key={r.id} request={r} onAccept={handleAccept} onReject={handleReject} />
          ))}
        </div>
      </div>
    </Layout>
  );
}
