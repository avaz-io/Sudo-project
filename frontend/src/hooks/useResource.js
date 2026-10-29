import { useCallback, useEffect, useState } from 'react'
import { request } from '../api/client.js'
export default function useResource(path, auth = false) {
  const [version, setVersion] = useState(0)
  const key = `${path}:${auth}:${version}`
  const [result, setResult] = useState({ key: '', data: null, error: null })
  const reload = useCallback(() => setVersion((value) => value + 1), [])
  useEffect(() => {
    const controller = new AbortController()
    request(path, { auth, signal: controller.signal })
      .then((data) => { if (!controller.signal.aborted) setResult({ key, data, error: null }) })
      .catch((error) => { if (!controller.signal.aborted) setResult({ key, data: null, error }) })
    return () => controller.abort()
  }, [path, auth, key])
  return { data: result.key === key ? result.data : null, error: result.key === key ? result.error : null, loading: result.key !== key, reload }
}
