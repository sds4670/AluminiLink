import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [action, setAction] = useState("");
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    const params = action ? { action } : {};
    api.get("/api/v1/admin/audit-logs", { params }).then((res) => setLogs(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, [action]);

  const knownActions = ["", "approve_alumni", "reject_alumni", "ban_user", "session_completed", "expire_window"];

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Audit Logs</h2>
          <select
            value={action}
            onChange={(e) => setAction(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          >
            {knownActions.map((a) => (
              <option key={a || "all"} value={a}>{a ? a.replace(/_/g, " ") : "All actions"}</option>
            ))}
          </select>
        </div>
        {loading && <p className="text-gray-500">Loading...</p>}

        {!loading && logs.length === 0 && (
          <div className="text-center py-16 text-gray-400 bg-white rounded-xl border border-gray-100 shadow-sm">
            <p className="text-lg">No audit logs{action ? ` for "${action.replace(/_/g, " ")}"` : ""}.</p>
            <p className="text-sm mt-1">{action ? "Try a different action filter." : "Admin and system actions will show up here."}</p>
          </div>
        )}

        {!loading && logs.length > 0 && (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600">
                <tr>
                  <th className="text-left px-4 py-3 font-medium">Time</th>
                  <th className="text-left px-4 py-3 font-medium">Actor</th>
                  <th className="text-left px-4 py-3 font-medium">Action</th>
                  <th className="text-left px-4 py-3 font-medium">Resource</th>
                  <th className="text-left px-4 py-3 font-medium">Details</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {logs.map((log) => (
                  <tr key={log.id} className="hover:bg-gray-50">
                    <td className="px-4 py-3 text-gray-400 whitespace-nowrap">{format(new Date(log.created_at), "MMM d, HH:mm")}</td>
                    <td className="px-4 py-3 text-gray-600">{log.actor_id ? `#${log.actor_id}` : "system"}</td>
                    <td className="px-4 py-3 font-medium text-gray-900 capitalize">{log.action.replace(/_/g, " ")}</td>
                    <td className="px-4 py-3 text-gray-500">{log.resource_type} {log.resource_id && `#${log.resource_id}`}</td>
                    <td className="px-4 py-3 text-gray-400 text-xs">{log.details}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
