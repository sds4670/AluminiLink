import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import CountdownTimer from "../../components/ui/CountdownTimer";
import api from "../../api/axios";
import { format } from "date-fns";
import { getErrorMessage } from "../../utils";

export default function ActiveWindow() {
  const { windowId } = useParams();
  const navigate = useNavigate();
  const [window_, setWindow] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [bookingSlotId, setBookingSlotId] = useState(null);

  const load = () => {
    api.get(`/api/v1/windows/${windowId}`)
      .then((res) => setWindow(res.data))
      .catch((err) => setError(getErrorMessage(err, "Window not found.")))
      .finally(() => setLoading(false));
  };

  useEffect(load, [windowId]);

  const handleBook = async (slotId) => {
    setError("");
    setBookingSlotId(slotId);
    try {
      await api.post("/api/v1/sessions/book", { window_id: Number(windowId), slot_id: slotId });
      navigate("/student/sessions");
    } catch (err) {
      setError(getErrorMessage(err, "Failed to book slot."));
      setBookingSlotId(null);
      load();
    }
  };

  if (loading) return <Layout><p className="text-gray-500">Loading...</p></Layout>;
  if (!window_) return <Layout><p className="text-red-600">{error || "Window not found."}</p></Layout>;

  const expiresAt = new Date(window_.expires_at).getTime();
  const isExpired = expiresAt <= Date.now() || window_.status !== "active";

  return (
    <Layout>
      <div className="max-w-3xl mx-auto">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">{window_.alumni_name}</h2>
              <p className="text-sm text-gray-500">{window_.company}</p>
            </div>
            <CountdownTimer seconds={window_.time_remaining_seconds} label="Window closes in" />
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        {isExpired ? (
          <p className="text-gray-400">This booking window is no longer active.</p>
        ) : (
          <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-500 text-xs uppercase">
                <tr>
                  <th className="text-left px-4 py-3">Date</th>
                  <th className="text-left px-4 py-3">Start</th>
                  <th className="text-left px-4 py-3">End</th>
                  <th className="text-right px-4 py-3">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {window_.available_slots.map((slot) => (
                  <tr key={slot.id}>
                    <td className="px-4 py-3">{format(new Date(slot.slot_date), "MMM d, yyyy")}</td>
                    <td className="px-4 py-3">{slot.start_time}</td>
                    <td className="px-4 py-3">{slot.end_time}</td>
                    <td className="px-4 py-3 text-right">
                      <button
                        onClick={() => handleBook(slot.id)}
                        disabled={bookingSlotId === slot.id}
                        className="px-3 py-1.5 bg-primary-600 text-white rounded-lg text-xs font-semibold hover:bg-primary-700 disabled:opacity-50"
                      >
                        {bookingSlotId === slot.id ? "Booking..." : "Book"}
                      </button>
                    </td>
                  </tr>
                ))}
                {window_.available_slots.length === 0 && (
                  <tr>
                    <td colSpan={4} className="px-4 py-8 text-center text-gray-400">
                      No open slots right now. Check back soon.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
