import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import useAuthStore from "../store/authStore";
import { getErrorMessage } from "../utils";
import AuthHeader from "../components/layout/AuthHeader";

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const STUDENT_EMAIL_DOMAIN = "christuniversity.in";

function EyeIcon({ open }) {
  return open ? (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8Z" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  ) : (
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="w-5 h-5">
      <path d="M9.88 9.88a3 3 0 1 0 4.24 4.24" />
      <path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 0 1-4.24-4.24" />
      <path d="M6.61 6.61A18.5 18.5 0 0 0 1 12s4 8 11 8a10.44 10.44 0 0 0 5.39-1.61" />
      <line x1="1" y1="1" x2="23" y2="23" />
    </svg>
  );
}

export default function Register() {
  const [form, setForm] = useState({ email: "", password: "", fullName: "", role: "student", identifier: "" });
  const [showPassword, setShowPassword] = useState(false);
  const [emailTouched, setEmailTouched] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [loading, setLoading] = useState(false);
  const { register } = useAuthStore();
  const navigate = useNavigate();

  const emailFormatValid = EMAIL_PATTERN.test(form.email);
  const emailDomainValid =
    form.role !== "student" || form.email.toLowerCase().endsWith(`@${STUDENT_EMAIL_DOMAIN}`);
  const emailValid = emailFormatValid && emailDomainValid;
  const passwordValid = form.password.length >= 8;
  const canSubmit = emailValid && passwordValid && form.fullName.trim() && form.identifier.trim();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    if (!emailFormatValid) {
      setError("Enter a valid email address.");
      return;
    }
    if (!emailDomainValid) {
      setError(`Students must register with a @${STUDENT_EMAIL_DOMAIN} email address.`);
      return;
    }
    if (!passwordValid) {
      setError("Password must be at least 8 characters long.");
      return;
    }
    setLoading(true);
    try {
      await register(form.email, form.password, form.role, form.identifier, form.fullName);
      if (form.role === "alumni") {
        setSuccess("Account created! You can log in right away — redirecting to login...");
        setTimeout(() => navigate("/login"), 1500);
      } else {
        setSuccess("Account created! Redirecting to login...");
        setTimeout(() => navigate("/login"), 1500);
      }
    } catch (err) {
      setError(getErrorMessage(err, "Registration failed."));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4 relative">
      <AuthHeader />
      <div className="w-full max-w-md bg-white rounded-2xl shadow-sm border border-gray-100 p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Create Account</h1>
          <p className="text-gray-500 mt-1 text-sm">Join the AlumniLink community</p>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">{error}</div>
        )}
        {success && (
          <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm">{success}</div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">I am a</label>
            <div className="grid grid-cols-2 gap-2">
              {["student", "alumni"].map((r) => (
                <button
                  key={r}
                  type="button"
                  onClick={() => setForm((f) => ({ ...f, role: r }))}
                  className={`py-2.5 rounded-lg text-sm font-medium border transition-colors capitalize ${
                    form.role === r
                      ? "bg-primary-600 text-white border-primary-600"
                      : "border-gray-300 text-gray-700 hover:border-primary-400"
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              value={form.fullName}
              onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
              required
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
            <input
              type="email"
              value={form.email}
              onChange={(e) => setForm((f) => ({ ...f, email: e.target.value }))}
              onBlur={() => setEmailTouched(true)}
              required
              placeholder={form.role === "student" ? `you@${STUDENT_EMAIL_DOMAIN}` : "you@example.com"}
              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 ${
                emailTouched && !emailValid ? "border-red-300 focus:ring-red-400" : "border-gray-300 focus:ring-primary-500"
              }`}
            />
            {emailTouched && !emailFormatValid && (
              <p className="text-xs text-red-600 mt-1">Enter a valid email address.</p>
            )}
            {emailTouched && emailFormatValid && !emailDomainValid && (
              <p className="text-xs text-red-600 mt-1">Students must use a @{STUDENT_EMAIL_DOMAIN} email address.</p>
            )}
            {form.role === "student" && !emailTouched && (
              <p className="text-xs text-gray-400 mt-1">Must be your official @{STUDENT_EMAIL_DOMAIN} email.</p>
            )}
            {form.role === "alumni" && !emailTouched && (
              <p className="text-xs text-gray-400 mt-1">Any email works — your personal/private email is fine.</p>
            )}
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={form.password}
                onChange={(e) => setForm((f) => ({ ...f, password: e.target.value }))}
                required
                minLength={8}
                className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
              <button
                type="button"
                onClick={() => setShowPassword((s) => !s)}
                aria-label={showPassword ? "Hide password" : "Show password"}
                className="absolute inset-y-0 right-0 flex items-center px-3 text-gray-400 hover:text-gray-600"
              >
                <EyeIcon open={showPassword} />
              </button>
            </div>
            <p className={`text-xs mt-1 ${form.password.length === 0 ? "text-gray-400" : passwordValid ? "text-green-600" : "text-red-600"}`}>
              {passwordValid ? "✓ " : ""}At least 8 characters
            </p>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {form.role === "student" ? "Roll Number" : "Register Number"}
            </label>
            <input
              type="text"
              value={form.identifier}
              onChange={(e) => setForm((f) => ({ ...f, identifier: e.target.value }))}
              required
              placeholder={form.role === "student" ? "e.g. 2024DS001" : "e.g. REG2014DS01"}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
            />
            <p className="text-xs text-gray-400 mt-1">
              Must match the {form.role === "student" ? "roll number" : "register number"} on file with your university.
            </p>
          </div>
          {form.role === "alumni" && (
            <p className="text-xs text-amber-600 bg-amber-50 border border-amber-200 rounded-lg p-2.5">
              You can log in right away. An admin still needs to verify your account before you can
              create your mentor profile or list availability.
            </p>
          )}
          <button
            type="submit"
            disabled={loading || !canSubmit}
            className="w-full py-2.5 bg-primary-600 text-white rounded-lg font-semibold text-sm hover:bg-primary-700 transition-colors disabled:opacity-50"
          >
            {loading ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="text-center text-sm text-gray-500 mt-6">
          Already have an account?{" "}
          <Link to="/login" className="text-primary-600 hover:underline font-medium">Sign in</Link>
        </p>
      </div>
    </div>
  );
}
