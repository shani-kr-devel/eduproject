import { NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const NAV_BY_ROLE = {
  student: [
    { to: "/student/dashboard", label: "Dashboard" },
    { to: "/student/tests", label: "Tests" },
    { to: "/student/performance", label: "Performance" },
    { to: "/student/store", label: "Course Store" },
    { to: "/student/courses", label: "My Courses" },
    { to: "/student/messages", label: "Messages" },
  ],
  parent: [
    { to: "/parent/dashboard", label: "Dashboard" },
    { to: "/parent/children", label: "My Children" },
    { to: "/parent/search-child", label: "Add a Child" },
    { to: "/parent/reports", label: "Performance Reports" },
    { to: "/parent/messages", label: "Messages" },
  ],
  teacher: [
    { to: "/teacher/dashboard", label: "Dashboard" },
    { to: "/teacher/students", label: "My Students" },
    { to: "/teacher/tests", label: "Tests" },
    { to: "/teacher/courses", label: "Courses" },
    { to: "/teacher/reports", label: "Reports" },
    { to: "/teacher/messages", label: "Messages" },
  ],
  admin: [
    { to: "/admin/dashboard", label: "Dashboard" },
    { to: "/admin/users", label: "All Users" },
    { to: "/admin/students", label: "Students" },
    { to: "/admin/teachers", label: "Teachers" },
    { to: "/admin/parents", label: "Parents" },
    { to: "/admin/courses", label: "Courses" },
    { to: "/admin/orders", label: "Orders" },
  ],
};

export default function Layout({ title, children }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const items = NAV_BY_ROLE[user?.role] || [];

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="sidebar-brand">
          Edu<span>Manage</span>
        </div>
        <nav>
          {items.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => (isActive ? "active" : "")}
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-footer">
          Signed in as
          <br />
          <strong style={{ color: "#fff" }}>{user?.name}</strong>
        </div>
      </aside>
      <div className="main-area">
        <header className="topbar">
          <div className="topbar-title">{title}</div>
          <div className="topbar-user">
            {user?.role === "student" && user?.student_id && (
              <span className="badge-role">{user.student_id}</span>
            )}
            <span className="badge-role">{user?.role}</span>
            <button
              className="btn btn-outline btn-sm"
              onClick={() => {
                logout();
                navigate("/login");
              }}
            >
              Log out
            </button>
          </div>
        </header>
        <main className="content">{children}</main>
      </div>
    </div>
  );
}
