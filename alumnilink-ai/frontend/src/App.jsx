import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import useAuthStore from "./store/authStore";

import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Register from "./pages/Register";

import StudentDashboard from "./pages/student/Dashboard";
import StudentProfile from "./pages/student/Profile";
import BrowseAlumni from "./pages/student/BrowseAlumni";
import AlumniProfile from "./pages/student/AlumniProfile";
import SendRequest from "./pages/student/SendRequest";
import MyRequests from "./pages/student/MyRequests";
import ActiveWindow from "./pages/student/ActiveWindow";
import StudentSessions from "./pages/student/MySessions";
import StudentFeed from "./pages/student/Feed";

import AlumniDashboard from "./pages/alumni/Dashboard";
import AlumniProfileForm from "./pages/alumni/Profile";
import AvailabilitySlots from "./pages/alumni/AvailabilitySlots";
import MentorshipRequests from "./pages/alumni/MentorshipRequests";
import MyStudents from "./pages/alumni/MyStudents";
import AlumniSessions from "./pages/alumni/MySessions";
import AlumniFeed from "./pages/alumni/Feed";

import AdminDashboard from "./pages/admin/Dashboard";
import AlumniApprovalQueue from "./pages/admin/AlumniApprovalQueue";
import UserManagement from "./pages/admin/UserManagement";
import ModerationQueue from "./pages/admin/ModerationQueue";
import AuditLogs from "./pages/admin/AuditLogs";
import Reports from "./pages/admin/Reports";

function ProtectedRoute({ children, allowedRoles }) {
  const { isAuthenticated, role } = useAuthStore();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  if (allowedRoles && !allowedRoles.includes(role)) return <Navigate to="/" replace />;
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Student routes */}
        <Route path="/student" element={<ProtectedRoute allowedRoles={["student"]}><StudentDashboard /></ProtectedRoute>} />
        <Route path="/student/profile" element={<ProtectedRoute allowedRoles={["student"]}><StudentProfile /></ProtectedRoute>} />
        <Route path="/student/browse" element={<ProtectedRoute allowedRoles={["student"]}><BrowseAlumni /></ProtectedRoute>} />
        <Route path="/student/alumni/:id" element={<ProtectedRoute allowedRoles={["student"]}><AlumniProfile /></ProtectedRoute>} />
        <Route path="/student/request/:alumniId" element={<ProtectedRoute allowedRoles={["student"]}><SendRequest /></ProtectedRoute>} />
        <Route path="/student/requests" element={<ProtectedRoute allowedRoles={["student"]}><MyRequests /></ProtectedRoute>} />
        <Route path="/student/window" element={<ProtectedRoute allowedRoles={["student"]}><ActiveWindow /></ProtectedRoute>} />
        <Route path="/student/sessions" element={<ProtectedRoute allowedRoles={["student"]}><StudentSessions /></ProtectedRoute>} />
        <Route path="/student/feed" element={<ProtectedRoute allowedRoles={["student"]}><StudentFeed /></ProtectedRoute>} />

        {/* Alumni routes */}
        <Route path="/alumni" element={<ProtectedRoute allowedRoles={["alumni"]}><AlumniDashboard /></ProtectedRoute>} />
        <Route path="/alumni/profile" element={<ProtectedRoute allowedRoles={["alumni"]}><AlumniProfileForm /></ProtectedRoute>} />
        <Route path="/alumni/availability" element={<ProtectedRoute allowedRoles={["alumni"]}><AvailabilitySlots /></ProtectedRoute>} />
        <Route path="/alumni/requests" element={<ProtectedRoute allowedRoles={["alumni"]}><MentorshipRequests /></ProtectedRoute>} />
        <Route path="/alumni/students" element={<ProtectedRoute allowedRoles={["alumni"]}><MyStudents /></ProtectedRoute>} />
        <Route path="/alumni/sessions" element={<ProtectedRoute allowedRoles={["alumni"]}><AlumniSessions /></ProtectedRoute>} />
        <Route path="/alumni/feed" element={<ProtectedRoute allowedRoles={["alumni"]}><AlumniFeed /></ProtectedRoute>} />

        {/* Admin routes */}
        <Route path="/admin" element={<ProtectedRoute allowedRoles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
        <Route path="/admin/approvals" element={<ProtectedRoute allowedRoles={["admin"]}><AlumniApprovalQueue /></ProtectedRoute>} />
        <Route path="/admin/users" element={<ProtectedRoute allowedRoles={["admin"]}><UserManagement /></ProtectedRoute>} />
        <Route path="/admin/moderation" element={<ProtectedRoute allowedRoles={["admin"]}><ModerationQueue /></ProtectedRoute>} />
        <Route path="/admin/audit" element={<ProtectedRoute allowedRoles={["admin"]}><AuditLogs /></ProtectedRoute>} />
        <Route path="/admin/reports" element={<ProtectedRoute allowedRoles={["admin"]}><Reports /></ProtectedRoute>} />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
