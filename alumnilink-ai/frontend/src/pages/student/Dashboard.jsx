import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import AlumniCard from "../../components/cards/AlumniCard";
import PostCard from "../../components/cards/PostCard";
import api from "../../api/axios";
import { isRequestStillBlocking } from "../../utils";

export default function StudentDashboard() {
  const [topAlumni, setTopAlumni] = useState([]);
  const [requestStatusByAlumni, setRequestStatusByAlumni] = useState({});
  const [stats, setStats] = useState({ recommended: 0, pending: 0, upcoming: 0, completed: 0 });
  const [feedPreview, setFeedPreview] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/matching/alumni").catch(() => ({ data: [] })),
      api.get("/api/v1/requests/my").catch(() => ({ data: [] })),
      api.get("/api/v1/sessions/my").catch(() => ({ data: [] })),
      api.get("/api/v1/feed/posts", { params: { limit: 3 } }).catch(() => ({ data: [] })),
    ]).then(([alumniRes, reqRes, sesRes, feedRes]) => {
      setTopAlumni(alumniRes.data.slice(0, 3));
      const statusMap = {};
      reqRes.data.forEach((r) => {
        if (isRequestStillBlocking(r)) {
          statusMap[r.alumni_user_id] = r.status;
        }
      });
      setRequestStatusByAlumni(statusMap);
      setStats({
        recommended: alumniRes.data.length,
        pending: reqRes.data.filter((r) => r.status === "pending").length,
        upcoming: sesRes.data.filter((s) => s.status === "scheduled").length,
        completed: sesRes.data.filter((s) => s.status === "completed").length,
      });
      setFeedPreview(feedRes.data);
    }).finally(() => setLoading(false));
  }, []);

  const cards = [
    { label: "Recommended Alumni", value: stats.recommended, to: "/student/browse", color: "bg-purple-50 text-purple-700" },
    { label: "Pending Requests", value: stats.pending, to: "/student/requests", color: "bg-blue-50 text-blue-700" },
    { label: "Upcoming Sessions", value: stats.upcoming, to: "/student/sessions", color: "bg-green-50 text-green-700" },
    { label: "Completed Sessions", value: stats.completed, to: "/student/sessions", color: "bg-gray-50 text-gray-700" },
  ];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Student Dashboard</h2>

        <div className="grid grid-cols-4 gap-4 mb-8">
          {cards.map((c) => (
            <Link key={c.label} to={c.to} className={`rounded-xl p-6 ${c.color} hover:opacity-90 transition-opacity`}>
              <p className="text-4xl font-bold">{loading ? "…" : c.value}</p>
              <p className="mt-1 text-sm font-medium">{c.label}</p>
            </Link>
          ))}
        </div>

        <div className="grid grid-cols-2 gap-6">
          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Top Matches</h3>
              <Link to="/student/browse" className="text-xs text-primary-600 hover:underline">View all</Link>
            </div>
            {loading && <p className="text-gray-400 text-sm">Loading...</p>}
            {!loading && topAlumni.length === 0 && (
              <p className="text-gray-400 text-sm">Complete your profile to get matched with alumni.</p>
            )}
            <div className="space-y-3">
              {topAlumni.map((a) => (
                <AlumniCard key={a.user_id} alumni={a} requestStatus={requestStatusByAlumni[a.user_id] || null} />
              ))}
            </div>
          </div>

          <div>
            <div className="flex items-center justify-between mb-3">
              <h3 className="font-semibold text-gray-900">Latest from the Feed</h3>
              <Link to="/student/feed" className="text-xs text-primary-600 hover:underline">View all</Link>
            </div>
            {loading && <p className="text-gray-400 text-sm">Loading...</p>}
            {!loading && feedPreview.length === 0 && (
              <p className="text-gray-400 text-sm">No posts yet.</p>
            )}
            <div className="space-y-3">
              {feedPreview.map((post) => <PostCard key={post.id} post={post} />)}
            </div>
          </div>
        </div>
      </div>
    </Layout>
  );
}
