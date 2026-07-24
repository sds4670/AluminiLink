import { useState, useEffect } from "react";
import Layout from "../../components/layout/Layout";
import api from "../../api/axios";
import { getErrorMessage } from "../../utils";

const DEPARTMENTS = ["Data Science", "Computer Science", "Electronics", "Mechanical", "Commerce", "Business Administration"];
const DEGREES = ["B.Sc", "B.Tech", "BBA", "M.Sc", "MBA", "M.Tech"];

export default function StudentProfile() {
  const [form, setForm] = useState({
    department: DEPARTMENTS[0],
    degree: DEGREES[0],
    graduation_year: new Date().getFullYear() + 1,
    career_goal: "",
    profile_description: "",
  });
  const [skills, setSkills] = useState([]);
  const [skillInput, setSkillInput] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isEditing, setIsEditing] = useState(false);

  useEffect(() => {
    api.get("/api/v1/profiles/student/me")
      .then((res) => {
        const p = res.data;
        setForm({
          department: p.department,
          degree: p.degree,
          graduation_year: p.graduation_year,
          career_goal: p.career_goal,
          profile_description: p.profile_description,
        });
        setSkills(p.skills || []);
        setIsEditing(true);
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

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
      const payload = { ...form, graduation_year: Number(form.graduation_year), skills: finalSkills };
      if (isEditing) {
        await api.put("/api/v1/profiles/student/me", payload);
      } else {
        await api.post("/api/v1/profiles/student", payload);
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
          <h2 className="text-2xl font-bold text-gray-900 mb-6">My Profile</h2>
          <p className="text-gray-400 text-sm">Loading...</p>
        </div>
      </Layout>
    );
  }

  return (
    <Layout>
      <div className="max-w-2xl mx-auto">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">My Profile</h2>

        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">
            {isEditing ? "Profile updated! Your matches will reflect the new details." : "Profile saved! You can now browse AI-matched alumni."}
          </div>
        )}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}

        <form onSubmit={handleSubmit} className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Department</label>
              <select
                value={form.department}
                onChange={(e) => setForm((f) => ({ ...f, department: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-600 mb-1">Degree</label>
              <select
                value={form.degree}
                onChange={(e) => setForm((f) => ({ ...f, degree: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              >
                {DEGREES.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Graduation Year</label>
            <input
              type="number"
              value={form.graduation_year}
              onChange={(e) => setForm((f) => ({ ...f, graduation_year: e.target.value }))}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>

          <div>
            <label className="block text-xs font-medium text-gray-600 mb-1">Career Goal</label>
            <input
              type="text"
              value={form.career_goal}
              onChange={(e) => setForm((f) => ({ ...f, career_goal: e.target.value }))}
              required
              placeholder="e.g. Become a machine learning engineer"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
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
            <label className="block text-xs font-medium text-gray-600 mb-1">Profile Description</label>
            <textarea
              value={form.profile_description}
              onChange={(e) => setForm((f) => ({ ...f, profile_description: e.target.value }))}
              required
              rows={4}
              placeholder="Tell mentors a bit about yourself and what you're looking for..."
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
