import { useEffect, useState } from "react";
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";

export default function Reports() {
  const [snapshots, setSnapshots] = useState([]);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/admin/analytics/snapshots"),
      api.get("/api/v1/admin/analytics/summary"),
    ]).then(([snapRes, summaryRes]) => {
      setSnapshots(snapRes.data);
      setSummary(summaryRes.data);
    }).finally(() => setLoading(false));
  }, []);

  const chartData = snapshots.map((s) => ({
    date: format(new Date(s.snapshot_date), "MMM d"),
    "Acceptance Rate %": Math.round((s.metrics.acceptance_rate || 0) * 100),
    "Completion Rate %": Math.round((s.metrics.completion_rate || 0) * 100),
    "Avg Match Score %": s.metrics.avg_match_score_pct || 0,
  }));

  const metrics = summary ? [
    { label: "Total Requests", value: summary.total_requests },
    { label: "Acceptance Rate", value: `${Math.round(summary.acceptance_rate * 100)}%` },
    { label: "Completion Rate", value: `${Math.round(summary.completion_rate * 100)}%` },
    { label: "Avg Rating", value: summary.avg_rating },
    { label: "Avg Screening Score", value: summary.avg_screening_score },
    { label: "Total Posts", value: summary.total_posts },
  ] : [];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Platform Reports</h2>
        {loading && <p className="text-gray-500">Loading...</p>}

        <div className="grid grid-cols-3 gap-4 mb-6">
          {metrics.map((m) => (
            <div key={m.label} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
              <p className="text-3xl font-bold text-gray-900">{m.value}</p>
              <p className="text-sm text-gray-500 mt-1">{m.label}</p>
            </div>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Trend (last 30 days)</h3>
          {chartData.length === 0 && !loading && (
            <p className="text-gray-400 text-sm">
              Not enough history yet — snapshots accumulate once a day (or whenever the analytics summary is viewed).
            </p>
          )}
          {chartData.length > 0 && (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={chartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="Acceptance Rate %" stroke="#4f46e5" strokeWidth={2} />
                <Line type="monotone" dataKey="Completion Rate %" stroke="#059669" strokeWidth={2} />
                <Line type="monotone" dataKey="Avg Match Score %" stroke="#db2777" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </Layout>
  );
}
