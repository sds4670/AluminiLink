import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    api.get("/api/admin/users").then((res) => setUsers(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, []);

  const ban = async (id) => {
    if (!window.confirm("Ban this user?")) return;
    await api.patch(`/api/admin/users/${id}/ban`);
    load();
  };

  return (
    <Layout>
      <div className="max-w-5xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">User Management</h2>
        {loading && <p className="text-gray-500">Loading...</p>}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-4 py-3 font-medium">ID</th>
                <th className="text-left px-4 py-3 font-medium">Email</th>
                <th className="text-left px-4 py-3 font-medium">Role</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Joined</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400">#{u.id}</td>
                  <td className="px-4 py-3 font-medium text-gray-900">{u.email}</td>
                  <td className="px-4 py-3 capitalize text-gray-600">{u.role}</td>
                  <td className="px-4 py-3"><StatusBadge status={u.status} /></td>
                  <td className="px-4 py-3 text-gray-400">{format(new Date(u.created_at), "MMM d, yyyy")}</td>
                  <td className="px-4 py-3">
                    {u.status !== "banned" && (
                      <button onClick={() => ban(u.id)} className="text-xs text-red-500 hover:text-red-700">Ban</button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
