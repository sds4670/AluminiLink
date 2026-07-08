import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import AlumniCard from "../../components/cards/AlumniCard";
import api from "../../api/axios";

export default function BrowseAlumni() {
  const [alumni, setAlumni] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    api.get("/api/v1/matching/alumni")
      .then((res) => setAlumni(res.data))
      .catch((err) => setError(err.response?.data?.detail || "Failed to load alumni."))
      .finally(() => setLoading(false));
  }, []);

  return (
    <Layout>
      <div className="max-w-5xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Browse Alumni</h2>
        <p className="text-gray-500 text-sm mb-6">Sorted by AI match score for your profile.</p>

        {loading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {alumni.map((a) => (
            <AlumniCard key={a.user_id} alumni={a} />
          ))}
        </div>

        {!loading && !error && alumni.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">No alumni available yet.</p>
            <p className="text-sm mt-1">Check back soon as more mentors join.</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
