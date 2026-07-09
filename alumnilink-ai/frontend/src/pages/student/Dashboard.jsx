import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function StudentDashboard() {
  const [stats, setStats] = useState({ requests: 0, sessions: 0 });

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/requests/my").catch(() => ({ data: [] })),
      api.get("/api/v1/sessions/my").catch(() => ({ data: [] })),
    ]).then(([reqRes, sesRes]) => {
      setStats({ requests: reqRes.data.length, sessions: sesRes.data.length });
    });
  }, []);

  const cards = [
    { label: "My Requests", value: stats.requests, to: "/student/requests", color: "bg-blue-50 text-blue-700" },
    { label: "My Sessions", value: stats.sessions, to: "/student/sessions", color: "bg-green-50 text-green-700" },
  ];

  return (
    <Layout>
      <div className="max-w-4xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Student Dashboard</h2>

        <div className="grid grid-cols-2 gap-4 mb-8">
          {cards.map((c) => (
            <Link key={c.to} to={c.to} className={`rounded-xl p-6 ${c.color} hover:opacity-90 transition-opacity`}>
              <p className="text-4xl font-bold">{c.value}</p>
              <p className="mt-1 text-sm font-medium">{c.label}</p>
            </Link>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm">
          <h3 className="font-semibold text-gray-900 mb-4">Quick actions</h3>
          <div className="flex flex-wrap gap-3">
            <Link to="/student/browse" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
              Browse Alumni
            </Link>
            <Link to="/student/feed" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">
              View Feed
            </Link>
          </div>
        </div>
      </div>
    </Layout>
  );
}
