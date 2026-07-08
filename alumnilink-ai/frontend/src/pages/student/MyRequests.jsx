import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import RequestCard from "../../components/cards/RequestCard";
import api from "../../api/axios";

export default function MyRequests() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/requests/mine")
      .then((res) => setRequests(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Requests</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && requests.length === 0 && (
          <p className="text-gray-400">No requests yet. Browse alumni to connect.</p>
        )}
        <div className="space-y-4">
          {requests.map((r) => <RequestCard key={r.id} request={r} />)}
        </div>
      </div>
    </Layout>
  );
}
