import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function AlumniApprovalQueue() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get("/api/admin/alumni/pending").then((res) => setUsers(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const approve = async (id) => {
    await api.post(`/api/admin/alumni/${id}/approve`);
    load();
  };

  const reject = async (id) => {
    await api.post(`/api/admin/alumni/${id}/reject`);
    load();
  };

  return (
    <Layout>
      <div className="max-w-4xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Alumni Verification Queue</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && users.length === 0 && <p className="text-gray-400">No alumni awaiting verification.</p>}
        <div className="space-y-4">
          {users.map((u) => (
            <div key={u.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-semibold text-gray-900">{u.full_name || u.email}</h3>
                  <p className="text-sm text-gray-500">{u.email}</p>
                  <p className="text-xs text-gray-400 mt-0.5">Register No. {u.register_number}</p>
                </div>
                <div className="flex gap-2 flex-shrink-0">
                  <button onClick={() => approve(u.id)} className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700">Approve</button>
                  <button onClick={() => reject(u.id)} className="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600">Reject</button>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
