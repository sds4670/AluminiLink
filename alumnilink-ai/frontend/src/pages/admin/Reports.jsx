import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function Reports() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/admin/reports/summary").then((res) => setSummary(res.data)).finally(() => setLoading(false));
  }, []);

  const metrics = summary ? [
    { label: "Total Users", value: summary.total_users },
    { label: "Alumni Pending Approval", value: summary.alumni_pending_approval },
    { label: "Posts Pending Moderation", value: summary.posts_pending_moderation },
  ] : [];

  return (
    <Layout>
      <div className="max-w-3xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Reports</h2>
        {loading && <p className="text-gray-500">Loading...</p>}

        <div className="grid grid-cols-3 gap-4">
          {metrics.map((m) => (
            <div key={m.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
              <p className="text-4xl font-bold text-gray-900">{m.value}</p>
              <p className="text-sm text-gray-500 mt-1">{m.label}</p>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
