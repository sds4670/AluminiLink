import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import Layout from "../../components/layout/Layout";
import MatchBadge from "../../components/ui/MatchBadge";
import api from "../../api/axios";
import { isRequestStillBlocking } from "../../utils";

const WHY_RECOMMENDED_LABELS = [
  "Similar Career Goal",
  "Matching Skills",
  "High Semantic Similarity",
  "Active Mentor",
];

const RESPONSE_STYLES = {
  High: "bg-green-100 text-green-800",
  Medium: "bg-amber-100 text-amber-800",
  Low: "bg-gray-100 text-gray-600",
};

export default function AlumniProfile() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [profile, setProfile] = useState(null);
  const [matchScore, setMatchScore] = useState(null);
  const [responsePrediction, setResponsePrediction] = useState(null);
  const [requestStatus, setRequestStatus] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.get(`/api/v1/profiles/alumni/${id}`),
      api.get(`/api/v1/matching/alumni/${id}/score`).catch(() => null),
      api.get(`/api/v1/predict/response/${id}`).catch(() => null),
      api.get("/api/v1/requests/my").catch(() => ({ data: [] })),
    ])
      .then(([profileRes, scoreRes, predictRes, reqRes]) => {
        setProfile(profileRes.data);
        if (scoreRes) setMatchScore(scoreRes.data.match_score);
        if (predictRes) setResponsePrediction(predictRes.data);
        const existing = reqRes.data.find(
          (r) => r.alumni_user_id === Number(id) && isRequestStillBlocking(r)
        );
        setRequestStatus(existing?.status || null);
      })
      .finally(() => setLoading(false));
  }, [id]);

  if (loading) return <Layout><p className="text-gray-500">Loading...</p></Layout>;
  if (!profile) return <Layout><p className="text-red-600">Profile not found.</p></Layout>;

  return (
    <Layout>
      <div className="max-w-2xl mx-auto space-y-6">
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-8">
          <div className="flex items-center gap-5 mb-6">
            <div className="w-20 h-20 rounded-full bg-accent-500 text-white flex items-center justify-center text-3xl font-bold">
              {profile.full_name?.[0]}
            </div>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <h2 className="text-2xl font-bold text-gray-900">{profile.full_name}</h2>
              </div>
              <p className="text-gray-500">{profile.designation}{profile.company ? ` at ${profile.company}` : ""}</p>
              <p className="text-sm text-gray-400">{profile.industry} · {profile.experience_years} yrs experience</p>
            </div>
            {matchScore != null && <MatchBadge score={matchScore} />}
          </div>

          {responsePrediction && (
            <div className="mb-5 flex items-center gap-2">
              <span className="text-xs text-gray-500">Predicted response likelihood:</span>
              <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${RESPONSE_STYLES[responsePrediction.interpretation]}`}>
                {responsePrediction.interpretation} ({Math.round(responsePrediction.response_likelihood * 100)}%)
              </span>
            </div>
          )}

          {profile.about_me && (
            <div className="mb-5">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">About</h3>
              <p className="text-sm text-gray-600">{profile.about_me}</p>
            </div>
          )}

          {profile.skills?.length > 0 && (
            <div className="mb-6">
              <h3 className="text-sm font-semibold text-gray-700 mb-2">Skills</h3>
              <div className="flex flex-wrap gap-2">
                {profile.skills.map((tag) => (
                  <span key={tag} className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                    {tag}
                  </span>
                ))}
              </div>
            </div>
          )}

          {requestStatus === "pending" && (
            <span
              title="You already have a pending request with this alumnus"
              className="inline-block px-6 py-2.5 bg-gray-100 text-gray-400 rounded-xl font-semibold text-sm cursor-not-allowed"
            >
              Request Pending
            </span>
          )}
          {requestStatus === "accepted" && (
            <button
              onClick={() => navigate("/student/requests")}
              title="You're already connected — continue in chat"
              className="inline-block px-6 py-2.5 bg-green-50 text-green-700 border border-green-200 rounded-xl font-semibold text-sm hover:bg-green-100 transition-colors"
            >
              Connected — Go to Chat
            </button>
          )}
          {!requestStatus && (
            <button
              onClick={() => navigate(`/student/request/${id}`)}
              className="inline-block px-6 py-2.5 bg-primary-600 text-white rounded-xl font-semibold text-sm hover:bg-primary-700 transition-colors"
            >
              Send Mentorship Request
            </button>
          )}
        </div>

        {matchScore != null && (
          <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold text-gray-900">Why Recommended</h3>
              <MatchBadge score={matchScore} />
            </div>
            <ul className="space-y-2">
              {WHY_RECOMMENDED_LABELS.map((label) => (
                <li key={label} className="flex items-center gap-2 text-sm text-gray-700">
                  <span className="text-green-600">✓</span>
                  {label}
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </Layout>
  );
}
