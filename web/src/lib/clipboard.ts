// navigator.clipboard only exists on https / localhost; the app is often opened as http://<ip>:port,
// so fall back to a hidden textarea + execCommand('copy') (still works on http, needs the click).
function legacyCopy(text: string): boolean {
  const ta = document.createElement('textarea')
  ta.value = text
  ta.setAttribute('readonly', '')
  ta.style.cssText = 'position:fixed;top:0;left:0;width:1px;height:1px;opacity:0;'
  document.body.appendChild(ta)
  const sel = document.getSelection()
  const prev = sel && sel.rangeCount ? sel.getRangeAt(0) : null
  ta.focus()
  ta.select()
  ta.setSelectionRange(0, text.length) // iOS / Safari
  let ok = false
  try {
    ok = document.execCommand('copy')
  } catch {
    ok = false
  }
  document.body.removeChild(ta)
  if (prev && sel) {
    sel.removeAllRanges()
    sel.addRange(prev)
  }
  return ok
}

export async function copyText(text: string): Promise<boolean> {
  // Safari drops the click's permission after an await, so try the sync path first when the API is missing.
  if (!window.isSecureContext || !navigator.clipboard?.writeText) return legacyCopy(text)
  try {
    await navigator.clipboard.writeText(text)
    return true
  } catch {
    return legacyCopy(text)
  }
}

export const copyKey = /Mac|iPhone|iPad/.test(navigator.platform || navigator.userAgent) ? '⌘C' : 'Ctrl+C'
