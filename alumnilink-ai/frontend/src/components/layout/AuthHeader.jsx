import { Link } from "react-router-dom";

export default function AuthHeader() {
  return (
    <header className="absolute top-0 left-0 right-0 px-8 py-5">
      <Link to="/" className="text-primary-900 text-xl font-bold hover:text-primary-700 transition-colors">
        AlumniLink AI
      </Link>
    </header>
  );
}
