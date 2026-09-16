import { useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading, Table, Pill } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

const ROLES = ["admin", "teacher", "student", "parent"];

export default function AdminUsers() {
  const { data: users, loading, reload } = useApiData("/accounts/admin/users/");
  const { data: teachers } = useApiData("/accounts/teachers/");
  const { data: parents } = useApiData("/accounts/parents/");
  const { data: students, reload: reloadStudents } = useApiData("/accounts/students/");

  const [form, setForm] = useState({
    email: "",
    first_name: "",
    last_name: "",
    role: "student",
    password: "",
    grade_level: "",

    // Student relationships
    teacher_id: "",

    // Teacher information
    subject_specialization: "",

    // Parent information for student creation
    parent_first_name: "",
    parent_last_name: "",
    parent_email: "",
    parent_password: "",
  });

  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [guardianDraft, setGuardianDraft] = useState({});
  const [guardianBusyId, setGuardianBusyId] = useState(null);
  const [guardianSavedId, setGuardianSavedId] = useState(null);
  const [studentSearch, setStudentSearch] = useState("");
  const existingParent = (parents || []).find(
    (parent) =>
      parent.user.email.toLowerCase() === form.parent_email.trim().toLowerCase()
  );

  async function createUser(e) {
    e.preventDefault();
    setError("");
    setBusy(true);

    try {
      /*
       * Build the main user payload.
       */
      const payload = {
        email: form.email,
        first_name: form.first_name,
        last_name: form.last_name,
        role: form.role,
        password: form.password,
      };

      /*
       * Student-specific information.
       */
      if (form.role === "student") {
        payload.grade_level = form.grade_level;

        /*
         * Send selected teacher.
         */
        if (form.teacher_id) {
          payload.teacher_ids = [Number(form.teacher_id)];
        }

        /*
         * Parent information is sent together with
         * the student creation request.
         */
        if (form.parent_email) {
          payload.parent = {
            first_name: form.parent_first_name,
            last_name: form.parent_last_name,
            email: form.parent_email,
            password: form.parent_password,
          };
        }
      }

      if (form.role === "teacher") {
        payload.subject_specialization = form.subject_specialization;
      }

      /*
       * Create student/user.
       *
       * The backend should create the parent as part
       * of this request when role === "student".
       */
      await api.post(
        "/accounts/admin/users/",
        payload
      );

      /*
       * Reset form.
       */
      setForm({
        email: "",
        first_name: "",
        last_name: "",
        role: "student",
        password: "",
        grade_level: "",

        teacher_id: "",

        subject_specialization: "",

        parent_first_name: "",
        parent_last_name: "",
        parent_email: "",
        parent_password: "",
      });

      /*
       * Reload existing data.
       */
      reload();
      reloadStudents();
    } catch (err) {
      console.error(err);

      setError(
        JSON.stringify(err.response?.data) ||
          "Could not create user."
      );
    } finally {
      setBusy(false);
    }
  }

  async function saveGuardian(student) {
    setGuardianBusyId(student.id);

    try {
      const draft = guardianDraft[student.id] || {};
      const payload = {};

      if (draft.guardian_email !== undefined) {
        payload.guardian_email = draft.guardian_email;
      }

      await api.patch(
        `/accounts/students/${student.id}/set_guardian/`,
        payload
      );

      reloadStudents();

      setGuardianSavedId(student.id);

      setTimeout(() => {
        setGuardianSavedId(null);
      }, 2000);
    } finally {
      setGuardianBusyId(null);
    }
  }

  async function saveRelations(student) {
    setGuardianBusyId(student.id);

    try {
      const draft = guardianDraft[student.id] || {};
      const payload = {};

      if (draft.teacher_ids !== undefined) {
        payload.teacher_ids = draft.teacher_ids;
      }

      if (draft.parent_id !== undefined) {
        payload.parent_id = draft.parent_id || null;
      }

      await api.patch(
        `/accounts/students/${student.id}/assign_relations/`,
        payload
      );

      reloadStudents();

      setGuardianSavedId(student.id);

      setTimeout(() => {
        setGuardianSavedId(null);
      }, 2000);
    } finally {
      setGuardianBusyId(null);
    }
  }

  const visibleStudents = (students || []).filter((student) => {
    const query = studentSearch.trim().toLowerCase();
    if (!query) return true;
    const name = `${student.user.first_name} ${student.user.last_name}`.toLowerCase();
    return name.includes(query) || student.student_id.toLowerCase().includes(query);
  });

  return (
    <Layout title="All Users">

      {/* =====================================================
          CREATE USER
      ====================================================== */}
      <Card title="Create a new user">
        <form
          onSubmit={createUser}
          className="grid grid-3"
        >

          {/* First name */}
          <div className="form-field">
            <label>First name</label>

            <input
              value={form.first_name}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  first_name: e.target.value,
                }))
              }
              required
            />
          </div>

          {/* Last name */}
          <div className="form-field">
            <label>Last name</label>

            <input
              value={form.last_name}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  last_name: e.target.value,
                }))
              }
            />
          </div>

          {/* Role */}
          <div className="form-field">
            <label>Role</label>

            <select
              value={form.role}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  role: e.target.value,
                }))
              }
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>
                  {r}
                </option>
              ))}
            </select>
          </div>

          {/* Email */}
          <div className="form-field">
            <label>Email</label>

            <input
              type="email"
              value={form.email}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  email: e.target.value,
                }))
              }
              required
            />
          </div>

          {/* Password */}
          <div className="form-field">
            <label>Password</label>

            <input
              type="password"
              value={form.password}
              onChange={(e) =>
                setForm((f) => ({
                  ...f,
                  password: e.target.value,
                }))
              }
              required
              minLength={8}
            />
          </div>

          {/* =================================================
              STUDENT FIELDS
          ================================================== */}
          {form.role === "student" && (
            <>
              {/* Grade */}
              <div className="form-field">
                <label>Grade level</label>

                <input
                  value={form.grade_level}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      grade_level: e.target.value,
                    }))
                  }
                />
              </div>

              {/* Teacher */}
              <div className="form-field">
                <label>Teacher</label>

                <select
                  value={form.teacher_id}
                  onChange={(e) =>
                    setForm((f) => ({
                      ...f,
                      teacher_id: e.target.value,
                    }))
                  }
                >
                  <option value="">
                    Select teacher
                  </option>

                  {(teachers || []).map((t) => (
                    <option
                      key={t.id}
                      value={t.id}
                    >
                      {t.user.first_name}{" "}
                      {t.user.last_name}
                    </option>
                  ))}
                </select>
              </div>

              {/* =================================================
                  PARENT SECTION
              ================================================== */}

              <div
                style={{
                  gridColumn: "1 / -1",
                  marginTop: 12,
                  padding: "14px 16px",
                  background: "#f8fafc",
                  border: "1px solid #e2e8f0",
                  borderRadius: 8,
                }}
              >
                <h3
                  style={{
                    margin: "0 0 12px",
                    fontSize: "1rem",
                  }}
                >
                  Parent information
                </h3>

                <div className="grid grid-3">

                  {/* Parent first name */}
                  <div className="form-field">
                    <label>Parent first name</label>

                    <input
                      value={form.parent_first_name}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          parent_first_name:
                            e.target.value,
                        }))
                      }
                    />
                  </div>

                  {/* Parent last name */}
                  <div className="form-field">
                    <label>Parent last name</label>

                    <input
                      value={form.parent_last_name}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          parent_last_name:
                            e.target.value,
                        }))
                      }
                    />
                  </div>

                  {/* Parent email */}
                  <div className="form-field">
                    <label>Parent email</label>

                    <input
                      type="email"
                      placeholder="parent@example.com"
                      value={form.parent_email}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          parent_email:
                            e.target.value,
                        }))
                      }
                    />
                  </div>

                  {/* Parent password */}
                  <div className="form-field">
                    <label>Parent password</label>

                    <input
                      type="password"
                      minLength={existingParent ? undefined : 8}
                      required={!existingParent}
                      value={form.parent_password}
                      onChange={(e) =>
                        setForm((f) => ({
                          ...f,
                          parent_password:
                            e.target.value,
                        }))
                      }
                    />
                  </div>

                </div>

                <p
                  style={{
                    fontSize: "0.8rem",
                    color: "#64748b",
                    margin: "10px 0 0",
                  }}
                >
                  {existingParent
                    ? "This email belongs to an existing parent. The parent account will be reused and this student will be added as another child."
                    : "A new parent account will be created and linked to this student. Use at least 8 characters for the parent password."}
                </p>
              </div>
            </>
          )}

          {form.role === "teacher" && (
            <div className="form-field">
              <label>Subject</label>
              <input
                value={form.subject_specialization}
                onChange={(e) =>
                  setForm((f) => ({
                    ...f,
                    subject_specialization: e.target.value,
                  }))
                }
                placeholder="e.g. Mathematics"
                required
              />
            </div>
          )}

          {/* Error */}
          {error && (
            <div
              className="error-text"
              style={{
                gridColumn: "1 / -1",
              }}
            >
              {error}
            </div>
          )}

          {/* Submit */}
          <button
            className="btn btn-primary"
            disabled={busy}
          >
            {busy
              ? "Creating..."
              : "Create user"}
          </button>
        </form>
      </Card>

      {/* =====================================================
          MANAGE STUDENT RELATIONSHIPS
      ====================================================== */}
      <Card title="Manage student relationships">

        <p
          style={{
            fontSize: "0.85rem",
            color: "#64748b",
            marginTop: 0,
          }}
        >
          Assign which teachers teach each student,
          and (once the parent already has an account) link a parent directly — this
          grants that parent immediate access, no
          separate confirmation step needed. If the
          parent hasn't created an account yet, use
          "Guardian email" instead to pre-authorize them
          for when they sign up and search by Student ID.
        </p>

        <div className="form-field" style={{ maxWidth: 360, marginBottom: 16 }}>
          <label htmlFor="student-relationship-search">Find student</label>
          <input
            id="student-relationship-search"
            type="search"
            value={studentSearch}
            onChange={(e) => setStudentSearch(e.target.value)}
            placeholder="Search by name or Student ID"
          />
        </div>

        <table className="table">
          <thead>
            <tr>
              <th>Student</th>
              <th>Teachers</th>
              <th>Parent (direct link)</th>
              <th>Guardian email (pre-authorize)</th>
              <th></th>
            </tr>
          </thead>

          <tbody>
            {visibleStudents.map((s) => {
              const currentTeacherIds =
                Array.isArray(s.teachers)
                  ? s.teachers
                  : [];

              const draftTeacherIds =
                guardianDraft[s.id]?.teacher_ids ??
                currentTeacherIds;

              return (
                <tr key={s.id}>

                  <td>
                    {s.user.first_name}{" "}
                    {s.user.last_name} (
                    {s.student_id})
                  </td>

                  <td>
                    <select
                      multiple
                      value={draftTeacherIds.map(String)}
                      onChange={(e) =>
                        setGuardianDraft((d) => ({
                          ...d,
                          [s.id]: {
                            ...d[s.id],
                            teacher_ids: Array.from(
                              e.target.selectedOptions,
                              (option) => Number(option.value)
                            ),
                          },
                        }))
                      }
                      aria-label={`Teachers for ${s.user.first_name} ${s.user.last_name}`}
                      style={{ minWidth: 170, minHeight: 72 }}
                    >
                      {(teachers || []).map((t) => (
                        <option key={t.id} value={t.id}>
                          {t.user.first_name} {t.user.last_name}
                        </option>
                      ))}
                    </select>
                  </td>

                  <td>
                    <select
                      defaultValue=""
                      onChange={(e) =>
                        setGuardianDraft((d) => ({
                          ...d,
                          [s.id]: {
                            ...d[s.id],
                            parent_id:
                              e.target.value,
                          },
                        }))
                      }
                    >
                      <option value="">
                        Unchanged
                      </option>

                      {(parents || []).map((p) => (
                        <option
                          key={p.id}
                          value={p.id}
                        >
                          {p.user.first_name}{" "}
                          {p.user.last_name} (
                          {p.user.email})
                        </option>
                      ))}
                    </select>
                  </td>

                  <td>
                    <input
                      style={{
                        width: 160,
                        padding: "6px 8px",
                        border:
                          "1px solid #cbd5e1",
                        borderRadius: 6,
                      }}
                      defaultValue={
                        s.guardian_email || ""
                      }
                      placeholder="parent@example.com"
                      onChange={(e) =>
                        setGuardianDraft((d) => ({
                          ...d,
                          [s.id]: {
                            ...d[s.id],
                            guardian_email:
                              e.target.value,
                          },
                        }))
                      }
                    />
                  </td>

                  <td
                    style={{
                      display: "flex",
                      flexDirection: "column",
                      gap: 4,
                    }}
                  >
                    <button
                      className="btn btn-primary btn-sm"
                      disabled={
                        guardianBusyId === s.id
                      }
                      onClick={() =>
                        saveRelations(s)
                      }
                    >
                      {guardianSavedId === s.id
                        ? "Saved ✓"
                        : "Save teachers/parent"}
                    </button>

                    <button
                      className="btn btn-outline btn-sm"
                      disabled={
                        guardianBusyId === s.id
                      }
                      onClick={() =>
                        saveGuardian(s)
                      }
                    >
                      Save guardian email
                    </button>
                  </td>

                </tr>
              );
            })}
          </tbody>
        </table>
      </Card>

      {/* =====================================================
          ALL USERS
      ====================================================== */}
      <Card title="All users">

        {loading ? (
          <Loading />
        ) : (
          <Table
            columns={[
              {
                key: "name",
                header: "Name",
                render: (r) =>
                  `${r.first_name} ${r.last_name}`,
              },
              {
                key: "email",
                header: "Email",
              },
              {
                key: "role",
                header: "Role",
                render: (r) => (
                  <Pill tone="blue">
                    {r.role}
                  </Pill>
                ),
              },
              {
                key: "is_active",
                header: "Active",
                render: (r) =>
                  r.is_active
                    ? "Yes"
                    : "No",
              },
            ]}
            rows={users || []}
            rowKey={(r) => r.id}
          />
        )}

      </Card>
    </Layout>
  );
}
