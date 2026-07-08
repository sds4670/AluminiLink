import StatusBadge from "../ui/StatusBadge";
import { format } from "date-fns";

export default function SessionCard({ session }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <div className="flex items-center justify-between mb-2">
        <h3 className="font-medium text-gray-900">Session #{session.id}</h3>
        <StatusBadge status={session.status} />
      </div>
      <p className="text-sm text-gray-600">
        {format(new Date(session.scheduled_at), "PPPp")}
      </p>
      <p className="text-xs text-gray-400 mt-1">{session.duration_minutes} minutes</p>
      {session.meeting_link && (
        <a
          href={session.meeting_link}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-3 inline-block text-sm text-primary-600 hover:underline"
        >
          Join meeting
        </a>
      )}
    </div>
  );
}
