const statusStyles = {
  pending: "bg-yellow-100 text-yellow-800",
  accepted: "bg-green-100 text-green-800",
  rejected: "bg-red-100 text-red-800",
  withdrawn: "bg-gray-100 text-gray-600",
  expired: "bg-orange-100 text-orange-700",
  scheduled: "bg-blue-100 text-blue-800",
  completed: "bg-green-100 text-green-800",
  cancelled: "bg-red-100 text-red-800",
  no_show: "bg-orange-100 text-orange-700",
  approved: "bg-green-100 text-green-800",
  verified: "bg-green-100 text-green-800",
  active: "bg-green-100 text-green-800",
  inactive: "bg-gray-100 text-gray-600",
  banned: "bg-red-100 text-red-800",
  pending_review: "bg-yellow-100 text-yellow-800",
};

export default function StatusBadge({ status }) {
  const style = statusStyles[status] || "bg-gray-100 text-gray-600";
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium capitalize ${style}`}>
      {status?.replace(/_/g, " ")}
    </span>
  );
}
