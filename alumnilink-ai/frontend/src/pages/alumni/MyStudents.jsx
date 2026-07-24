import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import ChatThread from "../../components/chat/ChatThread";
import useAuthStore from "../../store/authStore";
import api from "../../api/axios";

export default function MyStudents() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [openChatId, setOpenChatId] = useState(null);
  const currentUser = useAuthStore((s) => s.user);

  useEffect(() => {
    api.get("/api/v1/requests/incoming", { params: { status: "accepted" } })
      .then((res) => setRequests(res.data))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Students</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && requests.length === 0 && <p className="text-gray-400">No accepted mentees yet.</p>}
        <div className="space-y-3">
          {requests.map((r) => (
            <div key={r.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4">
              <p className="text-sm font-medium text-gray-900">{r.student_name}</p>
              <p className="text-xs text-gray-400 mt-0.5">{r.department} · Accepted</p>
              <button
                onClick={() => setOpenChatId(openChatId === r.id ? null : r.id)}
                className="mt-2 inline-block px-3 py-1.5 border border-primary-200 text-primary-700 rounded-lg text-xs font-medium hover:bg-primary-50 transition-colors"
              >
                {openChatId === r.id ? "Hide chat" : "Chat"}
              </button>
              {openChatId === r.id && currentUser && (
                <ChatThread
                  requestId={r.id}
                  currentUserId={currentUser.id}
                  otherPartyName={r.student_name}
                />
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
