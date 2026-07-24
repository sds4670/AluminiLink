import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import ChatThread from "../../components/chat/ChatThread";
import useAuthStore from "../../store/authStore";
import api from "../../api/axios";
import { format } from "date-fns";

const TABS = ["pending", "accepted", "rejected", "expired"];

export default function MyRequests() {
  const [requests, setRequests] = useState([]);
  const [tab, setTab] = useState("pending");
  const [loading, setLoading] = useState(true);
  const [openChatId, setOpenChatId] = useState(null);
  const currentUser = useAuthStore((s) => s.user);

  useEffect(() => {
    api.get("/api/v1/requests/my")
      .then((res) => setRequests(res.data))
      .finally(() => setLoading(false));
  }, []);

  const filtered = requests.filter((r) => r.status === tab);

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Requests</h2>

        <div className="flex gap-1 mb-6 border-b border-gray-200">
          {TABS.map((t) => (
            <button
              key={t}
              onClick={() => setTab(t)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
                tab === t ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {t} {requests.filter((r) => r.status === t).length > 0 && `(${requests.filter((r) => r.status === t).length})`}
            </button>
          ))}
        </div>

        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && filtered.length === 0 && (
          <p className="text-gray-400">No {tab} requests.</p>
        )}

        <div className="space-y-4">
          {filtered.map((r) => (
            <div key={r.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-start justify-between mb-2">
                <div>
                  <h3 className="font-semibold text-gray-900">{r.alumni_name}</h3>
                  <p className="text-xs text-gray-500">{r.designation} @ {r.company}</p>
                  <p className="text-xs text-gray-400 mt-0.5">{format(new Date(r.created_at), "MMM d, yyyy")}</p>
                </div>
                <div className="flex flex-col items-end gap-1.5">
                  <StatusBadge status={r.status} />
                  {r.screening_score != null && (
                    <span className="text-xs font-medium text-primary-600">
                      Screener: {r.screening_score.toFixed(2)}
                    </span>
                  )}
                </div>
              </div>
              {r.message && (
                <p className="text-sm text-gray-600 bg-gray-50 rounded-lg p-3 italic">"{r.message}"</p>
              )}
              {r.status === "rejected" && (
                <p className="text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg p-3 mt-2">
                  <span className="font-medium">Alumnus's note: </span>
                  {r.rejection_reason || "No reason given."}
                </p>
              )}
              {r.status === "accepted" && r.window_id && r.window_status === "active" && (
                <Link
                  to={`/student/window/${r.window_id}`}
                  className="mt-3 inline-block px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
                >
                  Book your session →
                </Link>
              )}
              {r.status === "accepted" && r.window_status === "booked" && (
                <span className="mt-3 inline-flex items-center gap-1 px-3 py-2 text-sm text-green-700 bg-green-50 border border-green-100 rounded-lg">
                  ✓ Session booked
                </span>
              )}
              {r.status === "accepted" && r.window_status === "expired" && (
                <span className="mt-3 inline-block px-3 py-2 text-sm text-gray-400 bg-gray-50 border border-gray-100 rounded-lg">
                  Booking window expired without a session being booked.
                </span>
              )}
              {r.status === "accepted" && (
                <>
                  <button
                    onClick={() => setOpenChatId(openChatId === r.id ? null : r.id)}
                    className="mt-3 ml-2 inline-block px-4 py-2 border border-primary-200 text-primary-700 rounded-lg text-sm font-medium hover:bg-primary-50 transition-colors"
                  >
                    {openChatId === r.id ? "Hide chat" : "Chat"}
                  </button>
                  {openChatId === r.id && currentUser && (
                    <ChatThread
                      requestId={r.id}
                      currentUserId={currentUser.id}
                      otherPartyName={r.alumni_name}
                    />
                  )}
                </>
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
