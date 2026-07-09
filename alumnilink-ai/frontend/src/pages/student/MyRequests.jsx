import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";

const TABS = ["pending", "accepted", "rejected", "expired"];

export default function MyRequests() {
  const [requests, setRequests] = useState([]);
  const [tab, setTab] = useState("pending");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/v1/requests/my")
      .then((res) => setRequests(res.data))
      .finally(() => setLoading(false));
  }, []);

  const filtered = requests.filter((r) => r.status === tab);

  return (
    <Layout>
      <div className="max-w-2xl">
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
              {r.status === "accepted" && r.window_id && (
                <Link
                  to={`/student/window/${r.window_id}`}
                  className="mt-3 inline-block px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
                >
                  Book your session →
                </Link>
              )}
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
