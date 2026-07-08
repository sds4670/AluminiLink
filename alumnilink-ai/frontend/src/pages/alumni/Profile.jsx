import { useState } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import useAuthStore from "../../store/authStore";

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

  if (user && user.verification_status !== "verified") {
    return (
      <Layout>
        <div className="max-w-2xl">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6 text-amber-800">
            <h2 className="font-semibold mb-1">Verification pending</h2>
            <p className="text-sm">
              Your alumni account is awaiting admin verification. You'll be able to create your
              mentor profile once an admin verifies your account.
            </p>
          </div>
        </div>
      </Layout>
    );
  }

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
    if (skills.length === 0) {
      setError("Add at least one skill.");
      return;
    }
    setSubmitting(true);
    try {
      await api.post("/api/v1/profiles/alumni", {
        ...form,
        experience_years: Number(form.experience_years),
        skills,
      });
      setSuccess(true);
    } catch (err) {
      setError(err.response?.data?.detail || "Failed to save profile.");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Layout>
      <div className="max-w-2xl">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Mentor Profile</h2>

        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            Profile saved! Students will now see you in their AI-matched recommendations.
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
            {submitting ? "Saving..." : "Save Profile"}
          </button>
        </form>
      </div>
    </Layout>
  );
}
