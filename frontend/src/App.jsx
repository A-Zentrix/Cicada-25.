import React, { useState } from 'react'

export default function App() {
  const [messages, setMessages] = useState([])
  const [text, setText] = useState('')
  const [language, setLanguage] = useState('en-US')
  const [busy, setBusy] = useState(false)

  async function send() {
    const value = text.trim()
    if (!value || busy) return
    setText('')
    setBusy(true)
    setMessages(prev => [...prev, { role: 'user', text: value }])
    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: value, language })
      })
      const data = await res.json()
      setMessages(prev => [...prev, { role: 'assistant', text: data.reply || '...' }])
    } catch (e) {
      setMessages(prev => [...prev, { role: 'assistant', text: 'Sorry, something went wrong.' }])
    } finally {
      setBusy(false)
      requestAnimationFrame(() => {
        const el = document.getElementById('scroll')
        if (el) el.scrollTop = el.scrollHeight
      })
    }
  }

  return (
    <div style={{ maxWidth: 820, margin: '0 auto', padding: 24, color: '#e5e7eb', fontFamily: 'system-ui, -apple-system, Segoe UI, Roboto, sans-serif', background: '#0f172a', minHeight: '100vh' }}>
      <div style={{ background: '#111827', borderRadius: 12, padding: 20, boxShadow: '0 10px 30px rgba(0,0,0,.25)' }}>
        <h1 style={{ margin: 0, marginBottom: 12, fontSize: 20 }}>Cicada-25 Chatbot</h1>
        <div id="scroll" style={{ height: '60vh', overflowY: 'auto', border: '1px solid #1f2937', borderRadius: 10, padding: 12, background: '#0b1220' }}>
          {messages.map((m, i) => (
            <div key={i} style={{ margin: '10px 0', padding: '10px 12px', borderRadius: 10, maxWidth: '90%', lineHeight: 1.4, background: m.role === 'user' ? '#0e7490' : '#374151', marginLeft: m.role === 'user' ? 'auto' : undefined }}>
              {m.role === 'user' ? 'You' : 'Bot'}: {m.text}
            </div>
          ))}
        </div>
        <div style={{ display: 'flex', gap: 10, marginTop: 12 }}>
          <input value={text} onChange={e => setText(e.target.value)} onKeyDown={e => e.key === 'Enter' && send()} placeholder="Type your message..." style={{ flex: 1, padding: '10px 12px', borderRadius: 8, border: '1px solid #374151', background: '#0b1220', color: '#e5e7eb' }} />
          <select value={language} onChange={e => setLanguage(e.target.value)} style={{ padding: '10px 12px', borderRadius: 8, border: '1px solid #374151', background: '#0b1220', color: '#e5e7eb' }}>
            <option value="en-US">English (US)</option>
            <option value="en-GB">English (UK)</option>
            <option value="ta-IN">Tamil</option>
            <option value="hi-IN">Hindi</option>
            <option value="es-ES">Spanish</option>
            <option value="fr-FR">French</option>
          </select>
          <button onClick={send} disabled={busy} style={{ padding: '10px 14px', borderRadius: 8, background: '#6366f1', color: '#fff', border: 'none', cursor: 'pointer', opacity: busy ? .6 : 1 }}>Send</button>
        </div>
        <div style={{ color: '#9ca3af', fontSize: 12, marginTop: 6 }}>Tip: Press Enter to send</div>
      </div>
    </div>
  )
}


