// Every rule is scoped to the .av-desk container so the frappe-ui styles (including the
// Tailwind reset) never change Desk outside our pages. Root selectors map to the container.
const SCOPE = '.av-desk'
const ROOT = /^(?::root|html|body|:host)(?![\w-])/
const DARK = /^\[data-theme=["']?dark["']?\]/

function scope(selector) {
  const s = selector.trim()
  // Vue's scoped-style compiler later replaces the whole selector with the :global() content,
  // so the scope has to go inside it.
  const global = s.match(/^:global\((.*)\)$/)
  if (global) return `:global(${scope(global[1])})`
  const dark = s.match(DARK)
  if (dark) {
    const rest = s.slice(dark[0].length).trim().replace(ROOT, '').trim()
    return rest ? `${dark[0]} ${SCOPE} ${rest}` : `${dark[0]} ${SCOPE}`
  }
  if (ROOT.test(s)) return s.replace(ROOT, SCOPE)
  return `${SCOPE} ${s}`
}

const scopeToDesk = {
  postcssPlugin: 'av-desk-scope',
  Rule(rule) {
    if (rule.parent?.type === 'atrule' && /keyframes$/i.test(rule.parent.name)) return
    const scoped = (s) => /^(?::global\()?\.av-desk(?![\w-])/.test(s.trim()) || s.includes(` ${SCOPE}`)
    if (rule.selectors.every(scoped)) return
    rule.selectors = rule.selectors.map(scope)
  },
}

export default {
  plugins: [
    (await import('tailwindcss')).default(),
    (await import('autoprefixer')).default(),
    scopeToDesk,
  ],
}
