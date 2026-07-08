import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";

export default function SendRequest() {
  const { alumniId } = useParams();
  const navigate = useNavigate();
  const [message, setMessage] = useState("");
  const [alumni, setAlumni] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get(`/api/v1/profiles/alumni/${alumniId}`).then((res) => setAlumni(res.data));
  }, [alumniId]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await api.post("/api/requests/", { alumni_id: Number(alumniId), message });
      navigate("/student/requests");
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to send request.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Send Connection Request</h2>

        {alumni && (
          <div className="bg-primary-50 border border-primary-100 rounded-xl p-4 mb-6">
            <p className="text-sm font-semibold text-primary-900">To: {alumni.full_name}</p>
            <p className="text-xs text-primary-600 mt-0.5">{alumni.designation}{alumni.company ? ` @ ${alumni.company}` : ""}</p>
          </div>
        )}

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Message <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              rows={5}
              placeholder="Introduce yourself and explain what kind of mentorship you're looking for..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>
          <div className="flex gap-3">
            <button type="button" onClick={() => navigate(-1)} className="flex-1 py-2.5 border border-gray-200 text-gray-700 rounded-lg text-sm font-medium hover:bg-gray-50">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="flex-1 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 disabled:opacity-50">
              {loading ? "Sending..." : "Send Request"}
            </button>
          </div>
        </form>
      </div>
    </Layout>
  );
}
