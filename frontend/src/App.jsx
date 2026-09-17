import { Navigate, Route, HashRouter as Router, Routes } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

import Login from "./pages/Login";

import StudentDashboard from "./pages/student/Dashboard";
import StudentTests from "./pages/student/Tests";
import StudentPerformance from "./pages/student/Performance";
import StudentStore from "./pages/student/Store";
import StudentCourses from "./pages/student/Courses";
import StudentMessages from "./pages/student/Messages";

import ParentDashboard from "./pages/parent/Dashboard";
import ParentChildren from "./pages/parent/Children";
import ParentSearchChild from "./pages/parent/SearchChild";
import ParentReports from "./pages/parent/Reports";
import ParentMessages from "./pages/parent/Messages";

import TeacherDashboard from "./pages/teacher/Dashboard";
import TeacherStudents from "./pages/teacher/Students";
import TeacherTests from "./pages/teacher/Tests";
import TeacherCourses from "./pages/teacher/Courses";
import TeacherReports from "./pages/teacher/Reports";
import TeacherMessages from "./pages/teacher/Messages";


import AdminDashboard from "./pages/admin/Dashboard";
import AdminUsers from "./pages/admin/Users";
import AdminStudents from "./pages/admin/Students";
import AdminTeachers from "./pages/admin/Teachers";
import AdminParents from "./pages/admin/Parents";
import AdminCourses from "./pages/admin/Courses";
import AdminOrders from "./pages/admin/Orders";

function HomeRedirect() {
  const { user, ready } = useAuth();
  if (!ready) return null;
  if (!user) return <Navigate to="/login" replace />;
  return <Navigate to={`/${user.role}/dashboard`} replace />;
}

export default function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<HomeRedirect />} />
          <Route path="/login" element={<Login />} />

          {/* Student */}
          <Route path="/student/dashboard" element={<ProtectedRoute roles={["student"]}><StudentDashboard /></ProtectedRoute>} />
          <Route path="/student/tests" element={<ProtectedRoute roles={["student"]}><StudentTests /></ProtectedRoute>} />
          <Route path="/student/performance" element={<ProtectedRoute roles={["student"]}><StudentPerformance /></ProtectedRoute>} />
          <Route path="/student/store" element={<ProtectedRoute roles={["student"]}><StudentStore /></ProtectedRoute>} />
          <Route path="/student/courses" element={<ProtectedRoute roles={["student"]}><StudentCourses /></ProtectedRoute>} />
          <Route path="/student/messages" element={<ProtectedRoute roles={["student"]}><StudentMessages /></ProtectedRoute>} />

          {/* Parent */}
          <Route path="/parent/dashboard" element={<ProtectedRoute roles={["parent"]}><ParentDashboard /></ProtectedRoute>} />
          <Route path="/parent/children" element={<ProtectedRoute roles={["parent"]}><ParentChildren /></ProtectedRoute>} />
          <Route path="/parent/search-child" element={<ProtectedRoute roles={["parent"]}><ParentSearchChild /></ProtectedRoute>} />
          <Route path="/parent/reports" element={<ProtectedRoute roles={["parent"]}><ParentReports /></ProtectedRoute>} />
          <Route path="/parent/messages" element={<ProtectedRoute roles={["parent"]}><ParentMessages /></ProtectedRoute>} />

          {/* Teacher */}
          <Route path="/teacher/dashboard" element={<ProtectedRoute roles={["teacher"]}><TeacherDashboard /></ProtectedRoute>} />
          <Route path="/teacher/students" element={<ProtectedRoute roles={["teacher"]}><TeacherStudents /></ProtectedRoute>} />
          <Route path="/teacher/tests" element={<ProtectedRoute roles={["teacher"]}><TeacherTests /></ProtectedRoute>} />
          <Route path="/teacher/courses" element={<ProtectedRoute roles={["teacher"]}><TeacherCourses /></ProtectedRoute>} />
          <Route path="/teacher/reports" element={<ProtectedRoute roles={["teacher"]}><TeacherReports /></ProtectedRoute>} />
          <Route path="/teacher/messages" element={<ProtectedRoute roles={["teacher"]}><TeacherMessages /></ProtectedRoute>} />

          {/* Admin */}
          <Route path="/admin/dashboard" element={<ProtectedRoute roles={["admin"]}><AdminDashboard /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute roles={["admin"]}><AdminUsers /></ProtectedRoute>} />
          <Route path="/admin/students" element={<ProtectedRoute roles={["admin"]}><AdminStudents /></ProtectedRoute>} />
          <Route path="/admin/teachers" element={<ProtectedRoute roles={["admin"]}><AdminTeachers /></ProtectedRoute>} />
          <Route path="/admin/parents" element={<ProtectedRoute roles={["admin"]}><AdminParents /></ProtectedRoute>} />
          <Route path="/admin/courses" element={<ProtectedRoute roles={["admin"]}><AdminCourses /></ProtectedRoute>} />
          <Route path="/admin/orders" element={<ProtectedRoute roles={["admin"]}><AdminOrders /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </Router>
  );
}
