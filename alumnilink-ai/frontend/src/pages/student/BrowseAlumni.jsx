import { useEffect, useState } from "react";
import Layout from "../../components/layout/Layout";
import AlumniCard from "../../components/cards/AlumniCard";
import api from "../../api/axios";
import { getErrorMessage, isRequestStillBlocking } from "../../utils";

export default function BrowseAlumni() {
  const [alumni, setAlumni] = useState([]);
  const [requestStatusByAlumni, setRequestStatusByAlumni] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");

  useEffect(() => {
    Promise.all([
      api.get("/api/v1/matching/alumni"),
      api.get("/api/v1/requests/my").catch(() => ({ data: [] })),
    ])
      .then(([alumniRes, reqRes]) => {
        setAlumni(alumniRes.data);
        const statusMap = {};
        reqRes.data.forEach((r) => {
          if (isRequestStillBlocking(r)) {
            statusMap[r.alumni_user_id] = r.status;
          }
        });
        setRequestStatusByAlumni(statusMap);
      })
      .catch((err) => setError(getErrorMessage(err, "Failed to load alumni.")))
      .finally(() => setLoading(false));
  }, []);

  const query = search.trim().toLowerCase();
  const filtered = query
    ? alumni.filter((a) => {
        const haystack = [a.name, a.company, a.designation, a.industry, ...(a.skills || [])]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return haystack.includes(query);
      })
    : alumni;

  return (
    <Layout>
      <div className="max-w-5xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Browse Alumni</h2>
        <p className="text-gray-500 text-sm mb-4">Sorted by AI match score for your profile.</p>

        <div className="relative mb-6 max-w-md">
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-4 h-4 absolute left-3 top-1/2 -translate-y-1/2 text-gray-400">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, company, role, or skill..."
            className="w-full pl-9 pr-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
          />
        </div>

        {loading && <p className="text-gray-500">Loading...</p>}
        {error && <p className="text-red-600">{error}</p>}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filtered.map((a) => (
            <AlumniCard key={a.user_id} alumni={a} requestStatus={requestStatusByAlumni[a.user_id] || null} />
          ))}
        </div>

        {!loading && !error && alumni.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">No alumni available yet.</p>
            <p className="text-sm mt-1">Check back soon as more mentors join.</p>
          </div>
        )}

        {!loading && !error && alumni.length > 0 && filtered.length === 0 && (
          <div className="text-center py-16 text-gray-400">
            <p className="text-lg">No matches for "{search}".</p>
            <p className="text-sm mt-1">Try a different name, company, or skill.</p>
          </div>
        )}
      </div>
    </Layout>
  );
}
