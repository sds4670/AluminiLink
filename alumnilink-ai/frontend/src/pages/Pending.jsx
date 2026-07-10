import { Link } from "react-router-dom";
import useAuthStore from "../store/authStore";

export default function Pending() {
  const { logout } = useAuthStore();

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
        <div className="w-14 h-14 mx-auto mb-4 rounded-full bg-amber-50 text-amber-600 flex items-center justify-center text-2xl">
          ⏳
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">Verification Pending</h1>
        <p className="text-sm text-gray-500 mb-6">
          Your alumni account is awaiting admin verification. You can view your dashboard and
          complete your profile in the meantime, but mentoring features (availability, requests,
          sessions) unlock once an admin verifies your account.
        </p>
        <div className="flex flex-col gap-2">
          <Link to="/alumni" className="px-4 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700">
            Back to Dashboard
          </Link>
          <button onClick={logout} className="px-4 py-2.5 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">
            Sign out
          </button>
        </div>
      </div>
    </div>
  );
}
