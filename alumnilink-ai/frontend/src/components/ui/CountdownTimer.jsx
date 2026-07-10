import { useState, useEffect } from "react";

const SIX_HOURS_IN_SECONDS = 6 * 60 * 60;

function formatHHMMSS(totalSeconds) {
  const s = Math.max(0, totalSeconds);
  const h = Math.floor(s / 3600);
  const m = Math.floor((s % 3600) / 60);
  const sec = Math.floor(s % 60);
  return [h, m, sec].map((v) => String(v).padStart(2, "0")).join(":");
}

/** Counts down from `seconds`. Turns red once less than 6 hours remain. */
export default function CountdownTimer({ seconds, label = "Closes in" }) {
  const [remaining, setRemaining] = useState(seconds);

  useEffect(() => {
    setRemaining(seconds);
  }, [seconds]);

  useEffect(() => {
    const id = setInterval(() => {
      setRemaining((prev) => Math.max(0, prev - 1));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  const expired = remaining <= 0;
  const urgent = remaining < SIX_HOURS_IN_SECONDS;

  return (
    <div className="inline-flex items-center gap-2">
      <span className="text-sm text-gray-500">{label}:</span>
      <span className={`font-mono text-sm font-semibold ${expired ? "text-red-600" : urgent ? "text-red-600" : "text-primary-700"}`}>
        {expired ? "Closed" : formatHHMMSS(remaining)}
      </span>
    </div>
  );
}
