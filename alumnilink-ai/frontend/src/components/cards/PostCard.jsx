import { useState } from "react";
import api from "../../api/axios";
import { format } from "date-fns";

const TYPE_STYLES = {
  internship: "bg-blue-50 text-blue-700",
  job: "bg-green-50 text-green-700",
  event: "bg-purple-50 text-purple-700",
  resource: "bg-amber-50 text-amber-700",
  query: "bg-gray-100 text-gray-700",
  announcement: "bg-pink-50 text-pink-700",
  general: "bg-gray-100 text-gray-700",
};

export default function PostCard({ post }) {
  const [likeCount, setLikeCount] = useState(post.like_count);
  const [liked, setLiked] = useState(post.liked_by_me);
  const [commentCount, setCommentCount] = useState(post.comment_count);
  const [showComments, setShowComments] = useState(false);
  const [comments, setComments] = useState(null);
  const [commentInput, setCommentInput] = useState("");
  const [commentError, setCommentError] = useState("");
  const [posting, setPosting] = useState(false);

  const toggleLike = async () => {
    try {
      const res = await api.post(`/api/v1/feed/posts/${post.id}/like`);
      setLiked(res.data.liked);
      setLikeCount(res.data.like_count);
    } catch {
      // ignore — not critical enough to surface an error banner for a like toggle
    }
  };

  const loadComments = async () => {
    setShowComments((prev) => !prev);
    if (comments === null) {
      const res = await api.get(`/api/v1/feed/posts/${post.id}/comments`);
      setComments(res.data);
    }
  };

  const submitComment = async (e) => {
    e.preventDefault();
    setCommentError("");
    setPosting(true);
    try {
      const res = await api.post(`/api/v1/feed/posts/${post.id}/comments`, { content: commentInput });
      setComments((prev) => [...(prev || []), res.data]);
      setCommentCount((c) => c + 1);
      setCommentInput("");
    } catch (err) {
      setCommentError(err.response?.data?.detail?.reason || err.response?.data?.detail || "Comment rejected.");
    } finally {
      setPosting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-full bg-accent-500 text-white flex items-center justify-center text-sm font-bold">
            {post.author_name?.[0] || "?"}
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">{post.author_name}</p>
            <p className="text-xs text-gray-400 capitalize">{post.author_role}</p>
          </div>
        </div>
        <span className={`text-xs font-medium px-2.5 py-1 rounded-full capitalize ${TYPE_STYLES[post.post_type] || "bg-gray-100 text-gray-700"}`}>
          {post.post_type}
        </span>
      </div>

      <p className="text-sm text-gray-700 whitespace-pre-wrap">{post.content}</p>
      <p className="text-xs text-gray-400 mt-3">{format(new Date(post.created_at), "PPp")}</p>

      <div className="flex items-center gap-4 mt-3 pt-3 border-t border-gray-100">
        <button
          onClick={toggleLike}
          className={`flex items-center gap-1.5 text-sm ${liked ? "text-primary-600 font-medium" : "text-gray-500"} hover:text-primary-600 transition-colors`}
        >
          <span>{liked ? "♥" : "♡"}</span> {likeCount}
        </button>
        <button
          onClick={loadComments}
          className="flex items-center gap-1.5 text-sm text-gray-500 hover:text-primary-600 transition-colors"
        >
          💬 {commentCount}
        </button>
      </div>

      {showComments && (
        <div className="mt-3 pt-3 border-t border-gray-100 space-y-3">
          {comments === null && <p className="text-xs text-gray-400">Loading comments...</p>}
          {comments?.map((c) => (
            <div key={c.id} className="bg-gray-50 rounded-lg p-2.5">
              <p className="text-xs font-semibold text-gray-800">{c.author_name} <span className="font-normal text-gray-400 capitalize">· {c.author_role}</span></p>
              <p className="text-sm text-gray-700 mt-0.5">{c.content}</p>
            </div>
          ))}
          {comments?.length === 0 && <p className="text-xs text-gray-400">No comments yet.</p>}

          {commentError && <p className="text-xs text-red-600">{commentError}</p>}
          <form onSubmit={submitComment} className="flex gap-2">
            <input
              value={commentInput}
              onChange={(e) => setCommentInput(e.target.value)}
              placeholder="Add a comment..."
              className="flex-1 px-3 py-1.5 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <button
              type="submit"
              disabled={posting || !commentInput.trim()}
              className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-medium hover:bg-primary-700 disabled:opacity-50"
            >
              Send
            </button>
          </form>
        </div>
      )}
    </div>
  );
}
