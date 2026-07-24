import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import useAuthStore from "../../store/authStore";
import { getErrorMessage } from "../../utils";

const INDUSTRIES = ["Technology", "Finance", "Banking", "Healthcare", "E-commerce", "Consulting", "Automotive", "Cloud Computing", "Other"];

export default function AlumniProfile() {
  const { user } = useAuthStore();
  const [form, setForm] = useState({
    company: "",
    designation: "",
    industry: INDUSTRIES[0],
    experience_years: 0,
    about_me: "",
  });
  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    // Deliberately fetched regardless of verification_status — a pending
    // alumnus needs to be able to see/edit what they've already filled in,
    // since this is exactly what an admin reviews to verify them.
    api.get("/api/v1/profiles/alumni/me")
      .then((res) => {
        const p = res.data;
        setForm({
          company: p.company,
          designation: p.designation,
          industry: p.industry,
          experience_years: p.experience_years,
          about_me: p.about_me,
        });
        setSkills(p.skills || []);
        setIsEditing(true);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const isPending = user && user.verification_status === "pending";

  const addSkill = (e) => {
    if (e.key !== "Enter") return;
    e.preventDefault();
    const value = skillInput.trim();
    if (value && !skills.includes(value)) {
      setSkills((prev) => [...prev, value]);
    }
    setSkillInput("");
  };

  const removeSkill = (skill) => {
    setSkills((prev) => prev.filter((s) => s !== skill));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    // Fold in whatever's still sitting in the skill box but wasn't committed
    // with Enter — typing a skill and clicking Save should still count it.
    let finalSkills = skills;
    const pendingSkill = skillInput.trim();
    if (pendingSkill && !skills.includes(pendingSkill)) {
      finalSkills = [...skills, pendingSkill];
      setSkills(finalSkills);
      setSkillInput("");
    }

    if (finalSkills.length === 0) {
      setError("Add at least one skill.");
      return;
    }
    setSubmitting(true);
    try {
      const payload = { ...form, experience_years: Number(form.experience_years), skills: finalSkills };
      if (isEditing) {
        await api.put("/api/v1/profiles/alumni/me", payload);
      } else {
        await api.post("/api/v1/profiles/alumni", payload);
        setIsEditing(true);
      }
      setSuccess(true);
    } catch (err) {
      setError(getErrorMessage(err, "Failed to save profile."));
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <Layout>
        <div className="max-w-2xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">My Mentor Profile</h2>
          <p className="text-gray-400 text-sm">Loading...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Mentor Profile</h2>

        {isPending && (
          <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-lg text-amber-800 text-sm">
            Your account is awaiting admin verification. Fill this in fully and accurately — it's
            what the admin reviews to verify you. You won't appear in student matches or be able
            to post availability until you're verified.
          </div>
        )}

        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {isEditing ? "Profile updated! Students will see the new details in their matches." : "Profile saved! Students will now see you in their AI-matched recommendations."}
          </div>
        )}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Company</label>
              <input
                type="text"
                value={form.company}
                onChange={(e) => setForm((f) => ({ ...f, company: e.target.value }))}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Designation</label>
              <input
                type="text"
                value={form.designation}
                onChange={(e) => setForm((f) => ({ ...f, designation: e.target.value }))}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Industry</label>
              <select
                value={form.industry}
                onChange={(e) => setForm((f) => ({ ...f, industry: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {INDUSTRIES.map((i) => <option key={i} value={i}>{i}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Years of Experience</label>
              <input
                type="number"
                min={0}
                value={form.experience_years}
                onChange={(e) => setForm((f) => ({ ...f, experience_years: e.target.value }))}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Skills</label>
            <input
              type="text"
              value={skillInput}
              onChange={(e) => setSkillInput(e.target.value)}
              onKeyDown={addSkill}
              placeholder="Type a skill and press Enter"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            {skills.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {skills.map((skill) => (
                  <span key={skill} className="inline-flex items-center gap-1 px-2.5 py-1 bg-primary-50 text-primary-700 rounded-full text-xs font-medium">
                    {skill}
                    <button type="button" onClick={() => removeSkill(skill)} className="text-primary-400 hover:text-primary-700">×</button>
                  </span>
                ))}
              </div>
            )}
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">About Me</label>
            <textarea
              value={form.about_me}
              onChange={(e) => setForm((f) => ({ ...f, about_me: e.target.value }))}
              required
              rows={4}
              placeholder="Tell students about your experience and how you can mentor them..."
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 resize-none"
            />
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="px-4 py-2.5 bg-primary-600 text-white rounded-lg text-sm font-semibold hover:bg-primary-700 disabled:opacity-50"
          >
            {submitting ? "Saving..." : isEditing ? "Update Profile" : "Save Profile"}
          </button>
        </form>
      </div>
    </Layout>
  );
}
