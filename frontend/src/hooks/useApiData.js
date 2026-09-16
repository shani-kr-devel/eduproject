import { useCallback, useEffect, useState } from "react";
import api from "../api/axiosClient";

/**
 * useApiData("/courses/courses/") -> { data, loading, error, reload }
 * `data` is normalised so both paginated ({results: [...]}) and plain list
 * responses work the same way for the UI.
 */
export function useApiData(url, { enabled = true, params } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const reload = useCallback(() => {
    if (!enabled || !url) {
      setLoading(false);
      return;
    }
    setLoading(true);
    api
      .get(url, { params })
      .then((res) => {
        const payload = res.data;
        setData(Array.isArray(payload) ? payload : payload.results ?? payload);
        setError(null);
      })
      .catch((err) => setError(err))
      .finally(() => setLoading(false));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url, JSON.stringify(params), enabled]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { data, loading, error, reload };
}
