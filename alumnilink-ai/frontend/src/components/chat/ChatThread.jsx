import { useEffect, useRef, useState } from "react";
import api from "../../api/axios";
import { format } from "date-fns";

const POLL_INTERVAL_MS = 7000;

/**
 * Chat thread tied to a connection_request (not a session), so it stays the
 * same thread across booking and session completion. Polls instead of using
 * websockets, matching this module's scope.
 */
export default function ChatThread({ requestId, currentUserId, otherPartyName }) {
  const [messages, setMessages] = useState([]);
  const [content, setContent] = useState("");
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [error, setError] = useState("");
  const bottomRef = useRef(null);

  const load = async () => {
    try {
      const res = await api.get(`/api/v1/requests/${requestId}/messages`);
      setMessages(res.data);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to load messages.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    const interval = setInterval(load, POLL_INTERVAL_MS);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: "nearest" });
  }, [messages.length]);

  const handleSend = async (e) => {
    e.preventDefault();
    if (!content.trim()) return;
    setSending(true);
    setError("");
    try {
      const res = await api.post(`/api/v1/requests/${requestId}/messages`, { content });
      setMessages((prev) => [...prev, res.data]);
      setContent("");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send message.");
    } finally {
      setSending(false);
    }
  };

  return (
    <div className="border border-gray-100 rounded-lg bg-gray-50 mt-3">
      <div className="max-h-64 overflow-y-auto p-3 space-y-2">
        {loading && <p className="text-xs text-gray-400">Loading messages...</p>}
        {!loading && messages.length === 0 && (
          <p className="text-xs text-gray-400">No messages yet. Say hello!</p>
        )}
        {messages.map((m) => {
          const isMine = m.sender_id === currentUserId;
          return (
            <div key={m.id} className={`flex ${isMine ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[75%] rounded-lg px-3 py-2 text-sm ${
                  isMine ? "bg-primary-600 text-white" : "bg-white border border-gray-200 text-gray-800"
                }`}
              >
                <p className="text-[11px] font-medium opacity-70 mb-0.5">
                  {isMine ? "You" : otherPartyName || "Them"}
                </p>
                <p className="whitespace-pre-wrap break-words">{m.content}</p>
                <p className={`text-[10px] mt-1 ${isMine ? "text-primary-100" : "text-gray-400"}`}>
                  {format(new Date(m.created_at), "MMM d, h:mm a")}
                </p>
              </div>
            </div>
          );
        })}
        <div ref={bottomRef} />
      </div>

      {error && <p className="text-xs text-red-600 px-3">{error}</p>}

      <form onSubmit={handleSend} className="flex gap-2 p-3 border-t border-gray-100">
        <input
          type="text"
          value={content}
          onChange={(e) => setContent(e.target.value)}
          placeholder="Type a message..."
          className="flex-1 px-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
        />
        <button
          type="submit"
          disabled={sending || !content.trim()}
          className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 disabled:opacity-50"
        >
          Send
        </button>
      </form>
    </div>
  );
}
