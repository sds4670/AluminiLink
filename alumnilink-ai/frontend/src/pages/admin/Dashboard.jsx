import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function AdminDashboard() {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    api.get("/api/v1/admin/analytics/summary").then((res) => setSummary(res.data)).catch(() => {});
  }, []);

  const cards = summary ? [
    { label: "Total Students", value: summary.total_students, to: "/admin/users", color: "bg-blue-50 text-blue-700" },
    { label: "Verified Alumni", value: summary.verified_alumni, to: "/admin/users", color: "bg-green-50 text-green-700" },
    { label: "Pending Approvals", value: summary.pending_alumni, to: "/admin/approvals", color: "bg-amber-50 text-amber-700" },
    { label: "Active Mentorships", value: summary.accepted_requests, to: "/admin/reports", color: "bg-purple-50 text-purple-700" },
    { label: "Completed Sessions", value: summary.completed_sessions, to: "/admin/reports", color: "bg-teal-50 text-teal-700" },
    { label: "Avg Match Score", value: `${summary.avg_match_score_pct}%`, to: "/admin/reports", color: "bg-pink-50 text-pink-700" },
  ] : [];

  const chartData = summary ? [
    { name: "Requests", value: summary.total_requests },
    { name: "Accepted", value: summary.accepted_requests },
    { name: "Rejected", value: summary.rejected_requests },
    { name: "Sessions", value: summary.total_sessions },
    { name: "Completed", value: summary.completed_sessions },
  ] : [];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Admin Dashboard</h2>

        <div className="grid grid-cols-3 gap-4 mb-8">
          {cards.map((c) => (
            <Link key={c.label} to={c.to} className={`rounded-xl p-6 ${c.color} hover:opacity-90 transition-opacity`}>
              <p className="text-4xl font-bold">{c.value}</p>
              <p className="mt-1 text-sm font-medium">{c.label}</p>
            </Link>
          ))}
          {!summary && <p className="col-span-3 text-gray-400">Loading stats...</p>}
        </div>

        {summary && (
          <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mb-6">
            <h3 className="font-semibold text-gray-900 mb-4">Requests &amp; Sessions Funnel</h3>
            <ResponsiveContainer width="100%" height={260}>
              <BarChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                <Tooltip />
                <Bar dataKey="value" fill="#4f46e5" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}

        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Quick actions</h3>
          <div className="flex flex-wrap gap-3">
            <Link to="/admin/approvals" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700">Alumni Approvals</Link>
            <Link to="/admin/moderation" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">Moderation Queue</Link>
            <Link to="/admin/audit" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">Audit Logs</Link>
            <Link to="/admin/reports" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">Reports</Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}
