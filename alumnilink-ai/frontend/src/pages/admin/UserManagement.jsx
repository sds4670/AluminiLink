import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import StatusBadge from "../../components/ui/StatusBadge";
import api from "../../api/axios";
import { format } from "date-fns";

const ROLE_FILTERS = ["all", "student", "alumni", "admin"];

export default function UserManagement() {
  const [users, setUsers] = useState([]);
  const [role, setRole] = useState("all");
  const [loading, setLoading] = useState(true);
  const [confirmingBanId, setConfirmingBanId] = useState(null);

  const load = () => {
    setLoading(true);
    const params = role === "all" ? {} : { role };
    api.get("/api/v1/admin/users", { params }).then((res) => setUsers(res.data)).finally(() => setLoading(false));
  };

  useEffect(load, [role]);

  const ban = async (id) => {
    await api.patch(`/api/v1/admin/users/${id}/ban`);
    setConfirmingBanId(null);
    load();
  };

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">User Management</h2>

        <div className="flex gap-1 mb-4 border-b border-gray-200">
          {ROLE_FILTERS.map((r) => (
            <button
              key={r}
              onClick={() => setRole(r)}
              className={`px-4 py-2 text-sm font-medium capitalize border-b-2 transition-colors ${
                role === r ? "border-primary-600 text-primary-700" : "border-transparent text-gray-500 hover:text-gray-700"
              }`}
            >
              {r}
            </button>
          ))}
        </div>

        {loading && <p className="text-gray-500">Loading...</p>}
        <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-gray-50 text-gray-600">
              <tr>
                <th className="text-left px-4 py-3 font-medium">ID</th>
                <th className="text-left px-4 py-3 font-medium">Name / Email</th>
                <th className="text-left px-4 py-3 font-medium">Role</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Verification</th>
                <th className="text-left px-4 py-3 font-medium">Joined</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {users.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-gray-400">#{u.id}</td>
                  <td className="px-4 py-3">
                    <p className="font-medium text-gray-900">{u.full_name || "—"}</p>
                    <p className="text-xs text-gray-400">{u.email}</p>
                  </td>
                  <td className="px-4 py-3 capitalize text-gray-600">{u.role}</td>
                  <td className="px-4 py-3"><StatusBadge status={u.status} /></td>
                  <td className="px-4 py-3"><StatusBadge status={u.verification_status} /></td>
                  <td className="px-4 py-3 text-gray-400">{format(new Date(u.created_at), "MMM d, yyyy")}</td>
                  <td className="px-4 py-3">
                    {u.status !== "banned" && confirmingBanId === u.id && (
                      <div className="flex items-center gap-2">
                        <span className="text-xs text-gray-500">Ban {u.full_name || u.email}?</span>
                        <button onClick={() => ban(u.id)} className="text-xs font-medium text-red-600 hover:text-red-800">Confirm</button>
                        <button onClick={() => setConfirmingBanId(null)} className="text-xs text-gray-400 hover:text-gray-600">Cancel</button>
                      </div>
                    )}
                    {u.status !== "banned" && confirmingBanId !== u.id && (
                      <button onClick={() => setConfirmingBanId(u.id)} className="text-xs text-red-500 hover:text-red-700">Ban</button>
                    )}
                  </td>
                </tr>
              ))}
              {!loading && users.length === 0 && (
                <tr><td colSpan={7} className="px-4 py-8 text-center text-gray-400">No users found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </Layout>
  );
}
