import StatusBadge from "../ui/StatusBadge";
import { format } from "date-fns";

export default function RequestCard({ request, onAccept, onReject }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-3">
        <div>
          <p className="text-sm text-gray-500">Request #{request.id}</p>
          <p className="text-xs text-gray-400 mt-0.5">
            {format(new Date(request.created_at), "MMM d, yyyy")}
          </p>
        </div>
        <StatusBadge status={request.status} />
      </div>

      {request.message && (
        <p className="text-sm text-gray-700 bg-gray-50 rounded-lg p-3 mb-3 italic">
          "{request.message}"
        </p>
      )}

      {request.status === "pending" && (onAccept || onReject) && (
        <div className="flex gap-2">
          {onAccept && (
            <button
              onClick={() => onAccept(request.id)}
              className="flex-1 px-3 py-2 text-sm bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Accept
            </button>
          )}
          {onReject && (
            <button
              onClick={() => onReject(request.id)}
              className="flex-1 px-3 py-2 text-sm border border-red-300 text-red-600 rounded-lg hover:bg-red-50 transition-colors"
            >
              Decline
            </button>
          )}
        </div>
      )}
    </div>
  );
}
