import { Link } from "react-router-dom";

const features = [
  {
    number: "01",
    title: "Keep your tutoring organized",
    description:
      "Bring your courses, learning materials, and student resources together in one place.",
  },
  {
    number: "02",
    title: "Plan lessons and practice",
    description:
      "Share homework and tests, then keep track of what each learner has completed.",
  },
  {
    number: "03",
    title: "Keep students and families in the loop",
    description:
      "Use progress reports and messages to help learners and parents stay connected with you.",
  },
];

const roles = ["Online tutors", "Tuition teachers", "Students", "Parents"];

export default function Landing() {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <Link className="landing-brand" to="/" aria-label="EduManage home">
          Edu<span>Manage</span>
        </Link>
        <nav className="landing-nav" aria-label="Main navigation">
          <a href="#features">Features</a>
          <a href="#community">Who it’s for</a>
          <a href="#demo">Demo access</a>
        </nav>
        <Link className="landing-signin" to="/login">
          Sign in <span aria-hidden="true">↗</span>
        </Link>
      </header>

      <main>
        <section className="landing-hero">
          <div className="landing-hero-copy">
            <p className="landing-eyebrow">
              <span aria-hidden="true" /> Your tutoring, all in one place
            </p>
            <h1>
              Teach your way,
              <br />
              <span>keep learning moving.</span>
            </h1>
            <p className="landing-intro">
              EduManage helps online tutors and tuition teachers manage
              courses, homework, tests, and student progress in one friendly
              place.
            </p>
            <div className="landing-actions">
              <Link className="landing-primary-button" to="/login">
                Explore the platform <span aria-hidden="true">→</span>
              </Link>
              <a className="landing-secondary-link" href="#features">
                See what you can do
              </a>
            </div>
            <div className="landing-role-note">
              <span className="landing-role-dots" aria-hidden="true">
                <i />
                <i />
                <i />
                <i />
              </span>
              Made for tutors, students, and families
            </div>
          </div>

          <div className="landing-preview" aria-label="Platform preview">
            <div className="preview-window">
              <div className="preview-topbar">
                <div className="preview-brand">
                  <span className="preview-brand-mark">E</span>
                  EduManage
                </div>
                <span className="preview-avatar">S</span>
              </div>
              <div className="preview-content">
                <div className="preview-greeting">
                  <div>
                    <span className="preview-overline">STUDENT SPACE</span>
                    <h2>Your learning, at a glance.</h2>
                  </div>
                  <span className="preview-date">THIS WEEK</span>
                </div>
                <div className="preview-stats">
                  <div>
                    <span>My courses</span>
                    <strong>04</strong>
                    <small>Keep it up</small>
                  </div>
                  <div>
                    <span>To do</span>
                    <strong>03</strong>
                    <small>Due this week</small>
                  </div>
                  <div>
                    <span>Progress</span>
                    <strong>82%</strong>
                    <small>Looking good</small>
                  </div>
                </div>
                <div className="preview-lower">
                  <div className="preview-course-card">
                    <div className="preview-section-heading">
                      <strong>Continue learning</strong>
                      <span>View all →</span>
                    </div>
                    <div className="preview-course">
                      <span className="preview-course-icon preview-icon-blue">M</span>
                      <div>
                        <strong>Mathematics</strong>
                        <small>Unit 4 · Algebra</small>
                      </div>
                      <span className="preview-progress">72%</span>
                    </div>
                    <div className="preview-course">
                      <span className="preview-course-icon preview-icon-orange">S</span>
                      <div>
                        <strong>Science</strong>
                        <small>Unit 2 · The natural world</small>
                      </div>
                      <span className="preview-progress">46%</span>
                    </div>
                  </div>
                  <div className="preview-reminder">
                    <span className="preview-reminder-icon" aria-hidden="true">
                      ✓
                    </span>
                    <div>
                      <strong>Small steps add up.</strong>
                      <p>Pick up where you left off.</p>
                    </div>
                    <span aria-hidden="true">↗</span>
                  </div>
                </div>
              </div>
            </div>
            <div className="preview-float-note">
              <span aria-hidden="true">✦</span>
              Progress, made visible
            </div>
          </div>
        </section>

        <section className="landing-features" id="features">
          <div className="landing-section-heading">
            <p className="landing-eyebrow">Made for the way you teach</p>
            <h2>Less juggling. More time for teaching.</h2>
          </div>
          <div className="landing-feature-grid">
            {features.map((feature) => (
              <article className="landing-feature-card" key={feature.number}>
                <span className="landing-feature-number">{feature.number}</span>
                <h3>{feature.title}</h3>
                <p>{feature.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section className="landing-community" id="community">
          <div>
            <p className="landing-eyebrow">A space for your learning community</p>
            <h2>Support every learner, wherever you teach.</h2>
          </div>
          <div className="landing-role-list">
            {roles.map((role, index) => (
              <div className="landing-role" key={role}>
                <span>0{index + 1}</span>
                {role}
                <span aria-hidden="true">↗</span>
              </div>
            ))}
          </div>
        </section>

        <section className="landing-demo" id="demo">
          <div>
            <p className="landing-eyebrow">Take a closer look</p>
            <h2>Curious about EduManage?</h2>
            <p>
              Need a sample ID and password? Contact details for requesting
              demo access will be added here soon.
            </p>
          </div>
          <Link className="landing-demo-button" to="/login">
            Already have an account? Sign in <span aria-hidden="true">→</span>
          </Link>
        </section>
      </main>

      <footer className="landing-footer">
        <Link className="landing-brand" to="/">
          Edu<span>Manage</span>
        </Link>
        <p>Made for tutors and learners.</p>
        <span>© {new Date().getFullYear()} EduManage</span>
      </footer>
    </div>
  );
}
