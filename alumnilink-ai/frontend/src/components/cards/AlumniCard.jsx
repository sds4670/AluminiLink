import { Link } from "react-router-dom";
import MatchBadge from "../ui/MatchBadge";

export default function AlumniCard({ alumni, requestStatus = null }) {
  const topSkills = (alumni.skills || []).slice(0, 3);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-5 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 rounded-full bg-accent-500 text-white flex items-center justify-center text-lg font-bold flex-shrink-0">
            {alumni.name?.[0] || "A"}
          </div>
          <div>
            <h3 className="font-semibold text-gray-900">{alumni.name}</h3>
            <p className="text-sm text-gray-500">
              {alumni.designation}{alumni.company ? ` @ ${alumni.company}` : ""}
            </p>
          </div>
        </div>
        {alumni.match_score != null && <MatchBadge score={alumni.match_score} />}
      </div>

      {topSkills.length > 0 && (
        <div className="mt-3 flex flex-wrap gap-1">
          {topSkills.map((tag) => (
            <span key={tag} className="px-2 py-0.5 bg-primary-50 text-primary-700 rounded text-xs">
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="mt-4 flex gap-2">
        <Link
          to={`/student/alumni/${alumni.user_id}`}
          className="flex-1 text-center px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
        >
          View Profile
        </Link>
        {requestStatus === "pending" && (
          <span
            title="You already have a pending request with this alumnus"
            className="flex-1 text-center px-3 py-2 text-sm bg-gray-100 text-gray-400 rounded-lg cursor-not-allowed"
          >
            Request Pending
          </span>
        )}
        {requestStatus === "accepted" && (
          <Link
            to="/student/requests"
            title="You're already connected — continue in chat"
            className="flex-1 text-center px-3 py-2 text-sm bg-green-50 text-green-700 border border-green-200 rounded-lg hover:bg-green-100 transition-colors"
          >
            Connected — Chat
          </Link>
        )}
        {!requestStatus && (
          <Link
            to={`/student/request/${alumni.user_id}`}
            className="flex-1 text-center px-3 py-2 text-sm bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors"
          >
            Connect
          </Link>
        )}
      </div>
    </div>
  );
}
