import { createContext, useContext, useEffect, useState } from "react";
import api, { clearTokens } from "../api/axiosClient";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const raw = localStorage.getItem("auth_user");
    return raw ? JSON.parse(raw) : null;
  });
  const [ready, setReady] = useState(false);

  useEffect(() => {
    // Rehydrate the fuller /me payload (profile details) on first load if a
    // token exists, without blocking the initial paint.
    const access = localStorage.getItem("access");
    if (access && !user?.profile) {
      api
        .get("/accounts/me/")
        .then((res) => {
          const merged = { ...user, ...res.data };
          setUser(merged);
          localStorage.setItem("auth_user", JSON.stringify(merged));
        })
        .catch(() => {})
        .finally(() => setReady(true));
    } else {
      setReady(true);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function login(email, password) {
    const res = await api.post("/accounts/login/", { email, password });
    localStorage.setItem("access", res.data.access);
    localStorage.setItem("refresh", res.data.refresh);
    const basicUser = {
      email: res.data.email,
      role: res.data.role,
      name: res.data.name,
      student_id: res.data.student_id,
    };
    localStorage.setItem("auth_user", JSON.stringify(basicUser));
    setUser(basicUser);
    return basicUser;
  }

  function logout() {
    clearTokens();
    setUser(null);
  }

  return (
    <AuthContext.Provider value={{ user, login, logout, ready }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}
