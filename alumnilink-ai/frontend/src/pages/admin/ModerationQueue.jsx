import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";
import { getErrorMessage } from "../../utils";

export default function ModerationQueue() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [confirming, setConfirming] = useState(null); // { id, action: "approve" | "reject" }

  const load = () => {
    api.get("/api/v1/admin/moderation/queue").then((res) => setPosts(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const approve = async (id) => {
    setError("");
    try {
      await api.patch(`/api/v1/admin/moderation/${id}/approve`);
      setConfirming(null);
      load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to approve post."));
    }
  };

  const reject = async (id) => {
    setError("");
    try {
      await api.patch(`/api/v1/admin/moderation/${id}/reject`);
      setConfirming(null);
      load();
    } catch (err) {
      setError(getErrorMessage(err, "Failed to reject post."));
    }
  };

  return (
    <Layout>
      <div className="max-w-4xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Moderation Queue</h2>
        {error && <p className="text-red-600 text-sm mb-4">{error}</p>}
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && posts.length === 0 && <p className="text-gray-400">Queue is clear.</p>}

        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          {posts.map((post) => (
            <div key={post.id} className="p-5 border-b border-gray-100 last:border-0">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <p className="text-sm font-semibold text-gray-900">{post.author_name}</p>
                    <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600 capitalize">{post.post_type}</span>
                    {post.toxicity_score != null && (
                      <span className="text-xs px-2 py-0.5 rounded-full bg-amber-100 text-amber-700">
                        Toxicity: {post.toxicity_score.toFixed(2)}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-700 mt-2">{post.content}</p>
                  <p className="text-xs text-gray-400 mt-2">{format(new Date(post.created_at), "PPp")}</p>
                </div>
                {confirming?.id === post.id ? (
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <span className="text-xs text-gray-500">{confirming.action === "approve" ? "Approve" : "Reject"} this post?</span>
                    <button
                      onClick={() => (confirming.action === "approve" ? approve(post.id) : reject(post.id))}
                      className={`px-3 py-1.5 text-xs text-white rounded-lg ${confirming.action === "approve" ? "bg-green-600 hover:bg-green-700" : "bg-red-500 hover:bg-red-600"}`}
                    >
                      Confirm
                    </button>
                    <button onClick={() => setConfirming(null)} className="px-3 py-1.5 text-xs border border-gray-200 text-gray-600 rounded-lg hover:bg-gray-50">
                      Cancel
                    </button>
                  </div>
                ) : (
                  <div className="flex gap-2 flex-shrink-0">
                    <button onClick={() => setConfirming({ id: post.id, action: "approve" })} className="px-3 py-1.5 text-xs bg-green-600 text-white rounded-lg hover:bg-green-700">Approve</button>
                    <button onClick={() => setConfirming({ id: post.id, action: "reject" })} className="px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600">Reject</button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
