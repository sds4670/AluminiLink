import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";

export default function AuditLogs() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get("/api/admin/audit-logs").then((res) => setLogs(res.data)).finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-5xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Audit Logs</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
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
                  <td className="px-4 py-3 text-gray-600">#{log.actor_id || "system"}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{log.action}</td>
                  <td className="px-4 py-3 text-gray-500">{log.resource_type} {log.resource_id && `#${log.resource_id}`}</td>
                  <td className="px-4 py-3 text-gray-400 text-xs">{log.details}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {!loading && logs.length === 0 && <p className="text-center py-8 text-gray-400">No audit logs yet.</p>}
        </div>
      </div>
    </Layout>
  );
}
