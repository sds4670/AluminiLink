import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.get("/api/admin/reports/summary").then((res) => setSummary(res.data)).catch(() => {});
  }, []);

  const cards = summary ? [
    { label: "Total Users", value: summary.total_users, to: "/admin/users", color: "bg-blue-50 text-blue-700" },
    { label: "Alumni Pending", value: summary.alumni_pending_approval, to: "/admin/approvals", color: "bg-amber-50 text-amber-700" },
    { label: "Posts to Review", value: summary.posts_pending_moderation, to: "/admin/moderation", color: "bg-red-50 text-red-700" },
  ] : [];

  return (
    <Layout>
      <div className="max-w-4xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h2>

        <div className="grid grid-cols-3 gap-4 mb-8">
          {cards.map((c) => (
            <Link key={c.to} to={c.to} className={`rounded-xl p-6 ${c.color} hover:opacity-90 transition-opacity`}>
              <p className="text-4xl font-bold">{c.value}</p>
              <p className="mt-1 text-sm font-medium">{c.label}</p>
            </Link>
          ))}
          {!summary && <p className="col-span-3 text-gray-400">Loading stats...</p>}
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Quick actions</h3>
          <div className="flex flex-wrap gap-3">
            <Link to="/admin/approvals" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">Alumni Approvals</Link>
            <Link to="/admin/moderation" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">Moderation Queue</Link>
            <Link to="/admin/audit" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">Audit Logs</Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}
