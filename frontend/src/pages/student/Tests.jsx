import { useEffect, useState } from "react";
import Layout from "../../components/Layout";
import { Card, Loading, Empty } from "../../components/ui";
import { useApiData } from "../../hooks/useApiData";
import api from "../../api/axiosClient";

export default function StudentTests() {
  const { data: tests, loading, reload } = useApiData("/academics/tests/");
  const [active, setActive] = useState(null);
  const [answers, setAnswers] = useState({});
  const [remaining, setRemaining] = useState(0);
  const [result, setResult] = useState(null);

  useEffect(() => {
    if (!active) return undefined;
    const timer = window.setInterval(() => {
      setRemaining((value) => {
        if (value <= 1) {
          window.clearInterval(timer);
          submit();
          return 0;
        }
        return value - 1;
      });
    }, 1000);
    return () => window.clearInterval(timer);
  }, [active]);

  async function start(test) {
    await api.post(`/academics/tests/${test.id}/start/`);
    setActive(test);
    setRemaining(test.duration_minutes * 60);
    setAnswers({});
    setResult(null);
  }

  async function submit() {
    if (!active) return;
    const response = await api.post(`/academics/tests/${active.id}/submit/`, { answers });
    setResult(response.data);
    setActive(null);
    reload();
  }

  return (
    <Layout title="Tests">
      {loading ? <Loading /> : (tests || []).length === 0 ? <Empty>No tests assigned yet.</Empty> : (
        <div className="grid grid-2">
          {(tests || []).map((test) => (
            <Card key={test.id} title={`${test.title} - ${test.subject}`}>
              <p>{test.duration_minutes} minutes · {test.questions?.length || 0} questions</p>
              {!active && <button className="btn btn-primary" onClick={() => start(test)}>Start test</button>}
              {active?.id === test.id && (
                <form onSubmit={(event) => { event.preventDefault(); submit(); }}>
                  <p><strong>Time remaining:</strong> {Math.floor(remaining / 60)}:{String(remaining % 60).padStart(2, "0")}</p>
                  {(test.questions || []).map((question) => (
                    <div key={question.id} className="form-field">
                      <label>{question.prompt}</label>
                      <select required onChange={(event) => setAnswers((current) => ({ ...current, [question.id]: event.target.value }))}>
                        <option value="">Choose an answer</option>
                        {(question.options || []).map((option) => <option key={option} value={option}>{option}</option>)}
                      </select>
                    </div>
                  ))}
                  <button className="btn btn-primary">Submit test</button>
                </form>
              )}
              {result && result.test === test.id && <p>Score: {result.score}/{result.max_score} · Time: {result.duration_seconds}s</p>}
            </Card>
          ))}
        </div>
      )}
    </Layout>
  );
}
