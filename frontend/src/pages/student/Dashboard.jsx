import { Link } from "react-router-dom";
import Layout from "../../components/Layout";
import { Card, Empty, Loading, Pill, StatCard } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import { useAuth } from "../../context/AuthContext";

export default function StudentDashboard() {
  const { user } = useAuth();
  const { data: tests, loading: testsLoading } = useApiData("/academics/tests/");
  const { data: enrollments, loading: enrollLoading } = useApiData("/courses/enrollments/");
  const { data: assignments, loading: assignmentsLoading } = useApiData("/courses/assignments/");
  const { data: homework, loading: homeworkLoading } = useApiData("/academics/homework/");

  const profile = user?.profile;
  const assignedCourses = (assignments || []).map((item) => item.course);
  const courses = [
    ...(enrollments || []).map((item) => item.course),
    ...assignedCourses,
  ].filter((course, index, all) => all.findIndex((candidate) => candidate.id === course.id) === index);
  const incompleteLessons = courses.flatMap((course) => (
    (course.contents || [])
      .filter((content) => !content.is_completed)
      .map((content) => ({ ...content, courseTitle: course.title }))
  ));
  const incompleteTests = (tests || []).filter((test) => !test.completed_attempt);
  const completedTests = (tests || []).filter((test) => test.completed_attempt);
  const incompleteHomework = (homework || []).filter((item) => item.status !== "submitted");
  const dailyTasks = [
    ...incompleteTests.slice(0, 2).map((test) => ({
      id: `test-${test.id}`,
      title: test.title,
      detail: `${test.subject} · ${test.duration_minutes} minutes`,
      to: "/student/tests",
      type: "Test",
    })),
    ...incompleteLessons.slice(0, 3).map((lesson) => ({
      id: `lesson-${lesson.id}`,
      title: lesson.title,
      detail: lesson.courseTitle,
      to: "/student/courses",
      type: "Lesson",
    })),
    ...incompleteHomework.slice(0, 2).map((item) => ({
      id: `homework-${item.id}`,
      title: item.title,
      detail: `Due ${item.due_date}`,
      to: "/student/homework",
      type: "Homework",
    })),
  ].slice(0, 4);

  return (
    <Layout title="Student Dashboard">
      {testsLoading || enrollLoading || assignmentsLoading || homeworkLoading ? (
        <Loading />
      ) : (
        <>
          <div className="grid grid-4">
            <StatCard label="Student ID" value={user?.student_id} />
            <StatCard label="Tests on Record" value={(tests || []).length} />
            <StatCard label="Purchased Courses" value={(enrollments || []).length} />
          </div>

          <div className="grid grid-2" style={{ marginTop: 16 }}>
            <Card title="Profile">
              <p><strong>Grade level:</strong> {profile?.grade_level || "—"}</p>
              <p><strong>Teachers:</strong> {(profile?.teacher_names || []).join(", ") || "—"}</p>
            </Card>
            <Card title="Tests">
              <p>Complete your assigned timed tests and review your results.</p>
              <Link to="/student/tests">Open tests →</Link>
            </Card>
          </div>

          <div className="student-dashboard-grid">
            <Card
              title="Today's tasks"
              actions={<span className="dashboard-section-note">{dailyTasks.length} to focus on</span>}
            >
              {dailyTasks.length === 0 ? (
                <Empty>Everything is caught up. Nice work.</Empty>
              ) : (
                <div className="dashboard-task-list">
                  {dailyTasks.map((task) => (
                    <Link className="dashboard-task" to={task.to} key={task.id}>
                      <span className="dashboard-task-icon">{task.type === "Test" ? "T" : task.type === "Homework" ? "H" : "L"}</span>
                      <span className="dashboard-task-copy">
                        <strong>{task.title}</strong>
                        <span>{task.detail}</span>
                      </span>
                      <span className="dashboard-task-arrow">→</span>
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            <Card title="Completed tests" actions={<Pill tone="blue">{completedTests.length} done</Pill>}>
              {completedTests.length === 0 ? (
                <Empty>No tests completed yet.</Empty>
              ) : (
                <div className="dashboard-incomplete-list">
                  {completedTests.slice(0, 4).map((test) => (
                    <Link className="dashboard-incomplete-item" to="/student/tests" key={`completed-${test.id}`}>
                      <span>
                        <strong>{test.title}</strong>
                        <small>{test.subject}</small>
                      </span>
                      <Pill tone="blue">
                        Done · {test.completed_attempt.score}/{test.completed_attempt.max_score}
                      </Pill>
                    </Link>
                  ))}
                </div>
              )}
            </Card>

            <Card
              title="Incomplete work"
              actions={<Pill tone="slate">{incompleteLessons.length + incompleteTests.length + incompleteHomework.length} items</Pill>}
            >
              {incompleteLessons.length === 0 && incompleteTests.length === 0 && incompleteHomework.length === 0 ? (
                <Empty>No incomplete work right now.</Empty>
              ) : (
                <div className="dashboard-incomplete-list">
                  {incompleteTests.slice(0, 3).map((test) => (
                    <Link className="dashboard-incomplete-item" to="/student/tests" key={`test-${test.id}`}>
                      <span>
                        <strong>{test.title}</strong>
                        <small>{test.subject}</small>
                      </span>
                      <Pill tone="blue">Test</Pill>
                    </Link>
                  ))}
                  {incompleteLessons.slice(0, 4).map((lesson) => (
                    <Link className="dashboard-incomplete-item" to="/student/courses" key={`lesson-${lesson.id}`}>
                      <span>
                        <strong>{lesson.title}</strong>
                        <small>{lesson.courseTitle}</small>
                      </span>
                      <Pill tone="slate">Lesson</Pill>
                    </Link>
                  ))}
                  {incompleteHomework.slice(0, 4).map((item) => (
                    <Link className="dashboard-incomplete-item" to="/student/homework" key={`homework-${item.id}`}>
                      <span>
                        <strong>{item.title}</strong>
                        <small>Due {item.due_date}</small>
                      </span>
                      <Pill tone="slate">Homework</Pill>
                    </Link>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </Layout>
  );
}
