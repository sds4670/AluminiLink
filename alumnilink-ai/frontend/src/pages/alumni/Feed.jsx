import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import PostCard from "../../components/cards/PostCard";
import api from "../../api/axios";

const POST_TYPE_OPTIONS = ["job", "internship", "resource", "announcement"];

const FILTER_TABS = [
  { key: "all", label: "All" },
  { key: "job", label: "Jobs" },
  { key: "internship", label: "Internships" },
  { key: "event", label: "Events" },
  { key: "resource", label: "Resources" },
  { key: "query", label: "Queries" },
];

function PostForm({ onCreated }) {
  const [content, setContent] = useState("");
  const [postType, setPostType] = useState(POST_TYPE_OPTIONS[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = await api.post("/api/v1/feed/posts", { content, post_type: postType });
      if (res.data.post.moderation_status === "pending_review") {
        setError("Your post was flagged for admin review and will appear once approved.");
      }
      setContent("");
      onCreated();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(detail?.reason || "Failed to create post.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 mb-6">
      {error && (
        <div className="mb-3 p-2.5 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">{error}</div>
      )}
      <textarea
        value={content}
        onChange={(e) => setContent(e.target.value)}
        required
        rows={3}
        placeholder="Share a job, internship, resource, or announcement with the community..."
        className="w-full px-3 py-2 border border-gray-200 rounded-lg text-sm resize-none focus:outline-none focus:ring-2 focus:ring-primary-500"
      />
      <div className="flex items-center justify-between mt-3">
        <select
          value={postType}
          onChange={(e) => setPostType(e.target.value)}
          className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 capitalize"
        >
          {POST_TYPE_OPTIONS.map((t) => <option key={t} value={t}>{t}</option>)}
        </select>
        <button
          type="submit"
          disabled={loading || !content.trim()}
          className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          {loading ? "Posting..." : "Post"}
        </button>
      </div>
    </form>
  );
}

export default function Feed() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  const loadPosts = () => {
    setLoading(true);
    const params = filter === "all" ? {} : { post_type: filter };
    api.get("/api/v1/feed/posts", { params }).then((res) => setPosts(res.data)).finally(() => setLoading(false));
  };

  useEffect(loadPosts, [filter]);

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Community Feed</h2>
        <PostForm onCreated={loadPosts} />

        <div className="flex gap-1 mb-6 border-b border-gray-200 overflow-x-auto">
          {FILTER_TABS.map((t) => (
            <button
              key={t.key}
              onClick={() => setFilter(t.key)}
              className={`px-3 py-2 text-sm font-medium whitespace-nowrap border-b-2 transition-colors ${
                filter === t.key ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && posts.length === 0 && <p className="text-gray-400">No posts yet.</p>}
        <div className="space-y-4">
          {posts.map((post) => <PostCard key={post.id} post={post} />)}
        </div>
      </div>
    </Layout>
  );
}
