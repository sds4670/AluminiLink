import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import CountdownTimer from "../../components/ui/CountdownTimer";
import api from "../../api/axios";

export default function ActiveWindow() {
  const [windows, setWindows] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/windows/")
      .then((res) => {
        const now = new Date();
        const active = res.data.filter(
          (w) => new Date(w.opens_at) <= now && new Date(w.closes_at) > now
        );
        setWindows(active);
      })
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-3xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Active Connection Windows</h2>
        <p className="text-gray-500 text-sm mb-6">Alumni are currently accepting requests during these windows.</p>

        {loading && <p className="text-gray-500">Loading...</p>}
        {!loading && windows.length === 0 && (
          <p className="text-gray-400">No active windows right now. Check back later.</p>
        )}

        <div className="space-y-4">
          {windows.map((w) => (
            <div key={w.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
              <div className="flex items-center justify-between">
                <h3 className="font-semibold text-gray-900">{w.title}</h3>
                <CountdownTimer targetDate={w.closes_at} />
              </div>
              <p className="text-xs text-gray-400 mt-1">Max {w.max_requests} requests</p>
              <Link
                to="/student/browse"
                className="mt-3 inline-block px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-medium hover:bg-primary-700 transition-colors"
              >
                Browse Alumni
              </Link>
            </div>
          ))}
        </div>
      </div>
    </Layout>
  );
}
