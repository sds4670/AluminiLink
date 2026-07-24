import { NavLink } from "react-router-dom";
import useAuthStore from "../../store/authStore";

const studentLinks = [
  { to: "/student", label: "Dashboard" },
  { to: "/student/profile", label: "My Profile" },
  { to: "/student/browse", label: "Browse Alumni" },
  { to: "/student/requests", label: "My Requests" },
  { to: "/student/sessions", label: "Sessions" },
  { to: "/student/feed", label: "Feed" },
];

const alumniLinks = [
  { to: "/alumni", label: "Dashboard" },
  { to: "/alumni/profile", label: "My Profile" },
  { to: "/alumni/availability", label: "Availability" },
  { to: "/alumni/requests", label: "Requests" },
  { to: "/alumni/students", label: "My Students" },
  { to: "/alumni/sessions", label: "Sessions" },
  { to: "/alumni/feed", label: "Feed" },
];

const adminLinks = [
  { to: "/admin", label: "Dashboard" },
  { to: "/admin/approvals", label: "Alumni Approvals" },
  { to: "/admin/users", label: "Users" },
  { to: "/admin/moderation", label: "Moderation" },
  { to: "/admin/audit", label: "Audit Logs" },
  { to: "/admin/reports", label: "Reports" },
];

const linkMap = { student: studentLinks, alumni: alumniLinks, admin: adminLinks };

export default function Sidebar() {
  const { role, logout } = useAuthStore();
  const links = linkMap[role] || [];

  return (
    <aside className="w-64 h-full bg-primary-900 text-white flex flex-col">
      <div className="p-6 border-b border-primary-700">
        <h1 className="text-xl font-bold tracking-tight">AlumniLink AI</h1>
        <p className="text-primary-300 text-xs mt-1 capitalize">{role} portal</p>
      </div>
      <nav className="flex-1 p-4 space-y-1">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            end={link.to.split("/").length === 2}
            className={({ isActive }) =>
              `block px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                isActive
                  ? "bg-primary-600 text-white"
                  : "text-primary-200 hover:bg-primary-800 hover:text-white"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
      <div className="p-4 border-t border-primary-700">
        <button
          onClick={logout}
          className="w-full px-4 py-2 text-sm text-primary-200 hover:text-white hover:bg-primary-800 rounded-lg transition-colors text-left"
        >
          Sign out
        </button>
      </div>
    </aside>
  );
}
