import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";

export default function ModerationQueue() {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get("/api/admin/posts/moderation").then((res) => setPosts(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const deletePost = async (id) => {
    await api.delete(`/api/feed/${id}`);
    setPosts((prev) => prev.filter((p) => p.id !== id));
  };

  return (
    <Layout>
      <div className="max-w-3xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Moderation Queue</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && posts.length === 0 && <p className="text-gray-400">Queue is clear.</p>}
        <div className="space-y-4">
          {posts.map((post) => (
            <div key={post.id} className="bg-white rounded-xl border border-amber-200 shadow-sm p-5">
              <div className="flex items-start justify-between gap-3">
                <div className="flex-1">
                  {post.title && <h3 className="font-semibold text-gray-900">{post.title}</h3>}
                  <p className="text-sm text-gray-700 mt-1">{post.content}</p>
                  <p className="text-xs text-gray-400 mt-2">{format(new Date(post.created_at), "PPp")}</p>
                </div>
                <button onClick={() => deletePost(post.id)} className="flex-shrink-0 px-3 py-1.5 text-xs bg-red-500 text-white rounded-lg hover:bg-red-600">
                  Remove
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
