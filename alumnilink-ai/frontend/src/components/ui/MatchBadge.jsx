export default function MatchBadge({ score }) {
  const s = score || 0;
  const pct = Math.round(s * 100);
  const color =
    s > 0.7 ? "bg-green-700 text-white" :
    s >= 0.5 ? "bg-amber-100 text-amber-800" :
    "bg-gray-100 text-gray-600";

  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${color}`}>
      {pct}% match
    </span>
  );
}
