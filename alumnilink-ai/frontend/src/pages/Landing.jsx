import { Link } from "react-router-dom";

export default function Landing() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-900 via-primary-700 to-accent-600 flex flex-col">
      <header className="flex items-center justify-between px-8 py-5">
        <h1 className="text-white text-2xl font-bold">AlumniLink AI</h1>
        <div className="flex gap-3">
          <Link to="/login" className="px-4 py-2 text-primary-100 hover:text-white text-sm font-medium transition-colors">
            Sign in
          </Link>
          <Link to="/register" className="px-4 py-2 bg-white text-primary-700 rounded-lg text-sm font-semibold hover:bg-primary-50 transition-colors">
            Get started
          </Link>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center text-center px-4">
        <h2 className="text-5xl font-extrabold text-white leading-tight max-w-3xl">
          Connect with alumni who've walked your path
        </h2>
        <p className="mt-6 text-xl text-primary-200 max-w-xl">
          AI-powered mentorship matching. Real connections. Real career growth.
        </p>
        <div className="mt-10 flex gap-4">
          <Link
            to="/register"
            className="px-8 py-3 bg-white text-primary-700 rounded-xl font-semibold text-lg hover:bg-primary-50 transition-colors shadow-lg"
          >
            Join as Student
          </Link>
          <Link
            to="/register"
            className="px-8 py-3 bg-primary-800 text-white rounded-xl font-semibold text-lg hover:bg-primary-900 transition-colors border border-primary-600"
          >
            Join as Alumni
          </Link>
        </div>
      </main>

      <footer className="text-center py-6 text-primary-300 text-sm">
        &copy; 2026 AlumniLink AI. Built for meaningful mentorship.
      </footer>
    </div>
  );
}
