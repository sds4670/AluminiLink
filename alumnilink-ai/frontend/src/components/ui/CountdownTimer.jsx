import { useState, useEffect } from "react";

function formatTime(ms) {
  if (ms <= 0) return "00:00:00";
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  return [h, m, s].map((v) => String(v).padStart(2, "0")).join(":");
}

export default function CountdownTimer({ targetDate, label = "Closes in" }) {
  const [remaining, setRemaining] = useState(() => new Date(targetDate) - Date.now());

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining(new Date(targetDate) - Date.now());
    }, 1000);
    return () => clearInterval(id);
  }, [targetDate]);

  const expired = remaining <= 0;

  return (
    <div className="inline-flex items-center gap-2">
      <span className="text-sm text-gray-500">{label}:</span>
      <span className={`font-mono text-sm font-semibold ${expired ? "text-red-600" : "text-primary-700"}`}>
        {expired ? "Closed" : formatTime(remaining)}
      </span>
    </div>
  );
}
