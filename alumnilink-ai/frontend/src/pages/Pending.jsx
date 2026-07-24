import { Link } from "react-router-dom";
import Layout from "../components/layout/Layout";
import useAuthStore from "../store/authStore";

export default function Pending() {
  const user = useAuthStore((s) => s.user);
  const isRejected = user?.verification_status === "rejected";

  return (
    <Layout>
      <div className="max-w-md mx-auto mt-12 bg-white rounded-2xl shadow-sm border border-gray-100 p-8 text-center">
        <div
          className={`w-14 h-14 mx-auto mb-4 rounded-full flex items-center justify-center text-2xl ${
            isRejected ? "bg-red-50 text-red-600" : "bg-amber-50 text-amber-600"
          }`}
        >
          {isRejected ? "✕" : "⏳"}
        </div>
        <h1 className="text-xl font-bold text-gray-900 mb-2">
          {isRejected ? "Verification Rejected" : "Verification Pending"}
        </h1>
        <p className="text-sm text-gray-500 mb-6">
          {isRejected
            ? "An admin reviewed your alumni account and did not approve it. Mentoring features remain locked. If you believe this is a mistake, please contact your university's alumni relations office."
            : "Your alumni account is awaiting admin verification. Fill in your mentor profile — that's what the admin reviews to verify you. Availability, requests, and the community feed unlock once you're verified."}
        </p>
        {!isRejected && (
          <Link to="/alumni/profile" className="inline-block px-4 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700">
            Complete My Profile
          </Link>
        )}
      </div>
    </Layout>
  );
}
