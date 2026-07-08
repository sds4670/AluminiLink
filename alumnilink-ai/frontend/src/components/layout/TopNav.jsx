import useAuthStore from "../../store/authStore";

export default function TopNav() {
  const { user, role } = useAuthStore();

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between">
      <div />
      <div className="flex items-center gap-3">
        <span className="text-sm text-gray-500">{user?.email}</span>
        <div className="w-8 h-8 rounded-full bg-primary-600 text-white flex items-center justify-center text-sm font-semibold uppercase">
          {user?.email?.[0] || "?"}
        </div>
      </div>
    </header>
  );
}
