import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { format } from "date-fns";

export default function AvailabilitySlots() {
  const [slots, setSlots] = useState([]);
  const [form, setForm] = useState({ slot_date: "", start_time: "", end_time: "" });
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const loadSlots = () => {
    api.get("/api/v1/availability/my").then((res) => setSlots(res.data)).finally(() => setLoading(false));
  };

  useEffect(loadSlots, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await api.post("/api/v1/availability/", form);
      setForm({ slot_date: "", start_time: "", end_time: "" });
      loadSlots();
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to create slot.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDelete = async (id) => {
    try {
      await api.delete(`/api/v1/availability/${id}`);
      setSlots((prev) => prev.filter((s) => s.id !== id));
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to delete slot.");
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Availability Slots</h2>

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 mb-6 space-y-4">
          <h3 className="font-semibold text-gray-900">Add New Slot</h3>
          {error && <p className="text-red-600 text-sm">{error}</p>}
          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Date</label>
            <input type="date" value={form.slot_date} onChange={(e) => setForm((f) => ({ ...f, slot_date: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Start time</label>
              <input type="time" value={form.start_time} onChange={(e) => setForm((f) => ({ ...f, start_time: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">End time</label>
              <input type="time" value={form.end_time} onChange={(e) => setForm((f) => ({ ...f, end_time: e.target.value }))} required className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500" />
            </div>
          </div>
          <button type="submit" disabled={submitting} className="px-4 py-2 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 disabled:opacity-50">
            {submitting ? "Adding..." : "Add Slot"}
          </button>
        </form>

        {loading && <p className="text-gray-500">Loading...</p>}
        <div className="space-y-3">
          {slots.map((slot) => (
            <div key={slot.id} className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-900">{format(new Date(`${slot.slot_date}T${slot.start_time}`), "PPp")}</p>
                <p className="text-xs text-gray-400">until {slot.end_time}</p>
                <p className="text-xs text-gray-500 capitalize mt-0.5">{slot.status}</p>
              </div>
              {slot.status === "open" && (
                <button onClick={() => handleDelete(slot.id)} className="text-xs text-red-500 hover:text-red-700">Remove</button>
              )}
            </div>
          ))}
        </div>
        {!loading && slots.length === 0 && (
          <p className="text-center text-gray-400 py-8">No slots yet. Add one above.</p>
        )}
      </div>
    </Layout>
  );
}
