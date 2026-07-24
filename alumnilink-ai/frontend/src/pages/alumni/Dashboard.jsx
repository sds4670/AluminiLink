import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import PostCard from "../../components/cards/PostCard";
import useAuthStore from "../../store/authStore";
import api from "../../api/axios";

const MENTOR_TIERS = [
  { min: 15, label: "Elite Mentor", color: "bg-purple-100 text-purple-800" },
  { min: 8, label: "Gold Mentor", color: "bg-yellow-100 text-yellow-800" },
  { min: 4, label: "Silver Mentor", color: "bg-gray-200 text-gray-700" },
  { min: 1, label: "Bronze Mentor", color: "bg-orange-100 text-orange-800" },
  { min: 0, label: "Rising Mentor", color: "bg-blue-100 text-blue-700" },
];

function mentorTier(completedSessions) {
  return MENTOR_TIERS.find((t) => completedSessions >= t.min);
}

export default function AlumniDashboard() {
  const user = useAuthStore((s) => s.user);
  const [stats, setStats] = useState({ requests: 0, upcoming: 0, completed: 0, slots: 0 });
  const [feedPreview, setFeedPreview] = useState([]);
  const [mentorScore, setMentorScore] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/requests/incoming").catch(() => ({ data: [] })),
      api.get("/api/v1/requests/incoming", { params: { status: "accepted" } }).catch(() => ({ data: [] })),
      api.get("/api/v1/requests/incoming", { params: { status: "rejected" } }).catch(() => ({ data: [] })),
      api.get("/api/v1/sessions/incoming").catch(() => ({ data: [] })),
      api.get("/api/v1/availability/my").catch(() => ({ data: [] })),
      api.get("/api/v1/feed/posts", { params: { limit: 3 } }).catch(() => ({ data: [] })),
      api.get("/api/v1/profiles/alumni/me").then(() => true).catch(() => false),
    ]).then(async ([pendingRes, acceptedRes, rejectedRes, sesRes, slotRes, feedRes, profileComplete]) => {
      const sessions = sesRes.data;
      const completed = sessions.filter((s) => s.status === "completed");
      const upcoming = sessions.filter((s) => s.status === "scheduled");

      setStats({
        requests: pendingRes.data.length,
        upcoming: upcoming.length,
        completed: completed.length,
        slots: slotRes.data.length,
      });
      setFeedPreview(feedRes.data);

      // Average rating across my completed sessions' feedback (N+1, but session
      // counts are small at this scale — no dedicated aggregate endpoint yet).
      const feedbacks = await Promise.all(
        completed.map((s) => api.get(`/api/v1/sessions/${s.id}/feedback`).then((r) => r.data).catch(() => []))
      );
      const ratings = feedbacks.flat().map((f) => f.rating);
      const avgRating = ratings.length ? ratings.reduce((a, b) => a + b, 0) / ratings.length : 0;

      const acceptedCount = acceptedRes.data.length;
      const rejectedCount = rejectedRes.data.length;
      const responseRate = acceptedCount + rejectedCount > 0 ? acceptedCount / (acceptedCount + rejectedCount) : 0;

      const score =
        (avgRating / 5) * 0.4 +
        Math.min(completed.length / 10, 1) * 0.3 +
        responseRate * 0.2 +
        (profileComplete ? 1 : 0) * 0.1;
      setMentorScore(Math.round(Math.min(score, 1) * 100));
    }).finally(() => setLoading(false));
  }, []);

  const tier = mentorTier(stats.completed);

  const cards = [
    { label: "Pending Requests", value: stats.requests, to: "/alumni/requests", color: "bg-amber-50 text-amber-700" },
    { label: "Upcoming Sessions", value: stats.upcoming, to: "/alumni/sessions", color: "bg-green-50 text-green-700" },
    { label: "Availability Slots", value: stats.slots, to: "/alumni/availability", color: "bg-blue-50 text-blue-700" },
  ];

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Alumni Dashboard</h2>
          <div className="flex items-center gap-3">
            <span className={`text-xs font-semibold px-3 py-1 rounded-full ${tier.color}`}>{tier.label}</span>
            {mentorScore != null && (
              <span className="text-xs font-semibold px-3 py-1 rounded-full bg-primary-50 text-primary-700">
                AI Mentor Score: {mentorScore}/100
              </span>
            )}
          </div>
        </div>

        {user?.verification_status === "pending" && (
          <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-xl text-amber-800 flex items-center justify-between gap-4 flex-wrap">
            <p className="text-sm">
              <span className="font-semibold">Verification pending.</span> Complete your mentor
              profile so an admin has something real to verify you against — you won't appear in
              student matches or unlock availability/requests until then.
            </p>
            <Link to="/alumni/profile" className="px-4 py-2 bg-amber-600 text-white rounded-lg text-sm font-semibold hover:bg-amber-700 whitespace-nowrap">
              Complete My Profile
            </Link>
          </div>
        )}

        <div className="grid grid-cols-3 gap-4 mb-8">
          {cards.map((c) => (
            <Link key={c.to} to={c.to} className={`rounded-xl p-6 ${c.color} hover:opacity-90 transition-opacity`}>
              <p className="text-4xl font-bold">{loading ? "…" : c.value}</p>
              <p className="mt-1 text-sm font-medium">{c.label}</p>
            </Link>
          ))}
        </div>

        <div className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm mb-6">
          <h3 className="font-semibold text-gray-900 mb-4">Quick actions</h3>
          <div className="flex flex-wrap gap-3">
            <Link to="/alumni/availability" className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors">
              Add Availability
            </Link>
            <Link to="/alumni/requests" className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50 transition-colors">
              Review Requests
            </Link>
          </div>
        </div>

        <div>
          <div className="flex items-center justify-between mb-3">
            <h3 className="font-semibold text-gray-900">Latest from the Feed</h3>
            <Link to="/alumni/feed" className="text-xs text-primary-600 hover:underline">View all</Link>
          </div>
          {!loading && feedPreview.length === 0 && <p className="text-gray-400 text-sm">No posts yet.</p>}
          <div className="space-y-3">
            {feedPreview.map((post) => <PostCard key={post.id} post={post} />)}
          </div>
        </div>
      </div>
    </Layout>
  );
}
