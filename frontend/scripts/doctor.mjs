import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../', import.meta.url))
const html = await readFile(new URL('../index.html', import.meta.url), 'utf8')
const expectedTitle = html.match(/<title>(.*?)<\/title>/s)?.[1]
console.log(`Frontend folder: ${root}`)
console.log(`Expected page title: ${expectedTitle}`)
console.log('Checking local addresses only; no accounts or data are changed.\n')

async function inspect(port) {
  const origin = `http://localhost:${port}`
  try {
    const page = await fetch(origin, { signal: AbortSignal.timeout(3000), redirect: 'error' })
    const source = await page.text()
    const title = source.match(/<title>(.*?)<\/title>/s)?.[1]
    const current = title === expectedTitle
    const type = source.includes('/@vite/client') ? 'Vite development server' : 'static or other server'
    const lines = [`${origin}: HTTP ${page.status}, ${type}`, `  Page: ${title || '(no HTML title)'}`, `  ${current ? 'Matches the current frontend title.' : 'Does NOT match the current frontend title.'}`]
    try {
      const health = await fetch(`${origin}/api/health`, { signal: AbortSignal.timeout(3000) })
      const data = await health.json().catch(() => null)
      lines.push(`  API health: ${health.ok && data?.status === 'ok' ? 'OK' : `not healthy (HTTP ${health.status})`}`)
      if (health.ok && data?.status === 'ok') {
        const response = await fetch(`${origin}/api/events`, { signal: AbortSignal.timeout(3000) })
        const events = await response.json().catch(() => null)
        lines.push(`  Public events: ${response.ok && Array.isArray(events) ? `${events.length} upcoming, published events` : `could not read the list (HTTP ${response.status})`}`)
      }
    } catch { lines.push('  API: unreachable or timed out.') }
    return lines.join('\n')
  } catch { return `${origin}: no reachable server.` }
}

const results = await Promise.all([5173, 5174, 8000].map(inspect))
console.log(results.join('\n\n'))
console.log('\nLive source: npm run dev → http://localhost:5173')
console.log('Fresh production preview: npm run preview → http://localhost:5174')
console.log('Port 8000 belongs to the existing Docker gateway; it serves a prebuilt frontend, not live source.')
console.log('Zero public events means no upcoming published events are returned; publish one using an organizer account.')
