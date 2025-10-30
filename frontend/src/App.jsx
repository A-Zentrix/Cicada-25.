import { useEffect, useRef, useState } from 'react'
import './App.css'
import { getJson, postForm, download } from './api'

function Message({ type, sender, content }) {
  return (
    <div className={`message ${type}`}>
      <div className={`msgAvatar ${type === 'bot' ? 'bot' : 'user'}`}>{type === 'bot' ? 'AI' : 'U'}</div>
      <div>
        <span className="sender">{sender}</span>
        <div className="bubble">{content}</div>
      </div>
    </div>
  )
}

function App() {
  const [messages, setMessages] = useState([
    { type: 'bot', sender: 'AI Assistant', content: "Hello! I'm here to support your mental wellness. How can I help you today?" },
  ])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)

  // language
  const [language, setLanguage] = useState('en-US')
  const [languages, setLanguages] = useState([])

  // emotion + memory + reports
  const [statusMsg, setStatusMsg] = useState('')
  const [currentEmotion, setCurrentEmotion] = useState('')
  const [memoryStatus, setMemoryStatus] = useState('')
  const [reports, setReports] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [detectorEnabled, setDetectorEnabled] = useState(true)
  const [autoSpeak, setAutoSpeak] = useState(true)

  const chatRef = useRef(null)

  useEffect(() => {
    if (chatRef.current) chatRef.current.scrollTop = chatRef.current.scrollHeight
  }, [messages])

  useEffect(() => {
    ;(async () => {
      try {
        const cur = await getJson('/language/current')
        if (cur?.success && cur.language) setLanguage(cur.language)
      } catch {}
      try {
        const list = await getJson('/language/list')
        if (list?.success && Array.isArray(list.languages)) setLanguages(list.languages)
      } catch {}
      try {
        const st = await getJson('/emotion_detector/status')
        if (st?.success) {
          setStatusMsg(formatStatus(st.status))
          if (typeof st.status?.enabled === 'boolean') setDetectorEnabled(st.status.enabled)
        }
      } catch {}
      try { await refreshReports() } catch {}
    })()
  }, [])

  function addMessage(type, sender, content) {
    setMessages(prev => [...prev, { type, sender, content }])
  }

  function formatStatus(status) {
    if (!status) return 'No status'
    return `Status: ${status.running ? 'Running' : 'Stopped'}\nEnabled: ${status.enabled ? 'Yes' : 'No'}\nDetection Interval: ${status.detection_interval} seconds\nLog File: ${status.log_file}`
  }

  async function sendMessage() {
    const text = input.trim()
    if (!text) return
    addMessage('user', 'You', text)
    setInput('')
    setLoading(true)
    try {
      const fd = new FormData()
      fd.append('message', text)
      const res = await postForm('/send_message', fd)
      if (res?.success) {
        addMessage('bot', 'AI Assistant', res.response)
        try {
          if (autoSpeak && typeof res.response === 'string' && res.response.trim()) {
            const sfd = new FormData(); sfd.append('text', res.response)
            await postForm('/speak', sfd)
          }
        } catch {}
      } else {
        addMessage('bot', 'Error', 'Sorry, I encountered an error. Please try again.')
      }
    } catch (e) {
      addMessage('bot', 'Error', 'Sorry, I encountered an error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  async function detectEmotion() {
    setLoading(true)
    addMessage('bot', 'AI Assistant', 'Detecting your emotion... Please look at the camera.')
    try {
      const res = await fetch('/detect_emotion', { method: 'POST' }).then(r => r.json())
      if (res?.success) {
        addMessage('bot', 'Emotion Detection', `I detected that you're feeling: ${res.emotion}`)
        addMessage('bot', 'AI Assistant', res.response)
      } else {
        addMessage('bot', 'Error', "Sorry, I couldn't detect your emotion. Please try again.")
      }
    } catch {
      addMessage('bot', 'Error', 'Sorry, I encountered an error during emotion detection.')
    } finally { setLoading(false) }
  }

  async function voiceCommand() {
    setLoading(true)
    addMessage('bot', 'AI Assistant', 'Listening... Please speak now.')
    try {
      const res = await fetch('/voice_command', { method: 'POST' }).then(r => r.json())
      if (res?.success) {
        addMessage('user', 'You (Voice)', res.command)
        addMessage('bot', 'AI Assistant', res.response)
      } else {
        addMessage('bot', 'Error', "Sorry, I couldn't understand your voice command. Please try again.")
      }
    } catch {
      addMessage('bot', 'Error', 'Sorry, I encountered an error with voice recognition.')
    } finally { setLoading(false) }
  }

  async function refreshStatus() { try { const st = await getJson('/emotion_detector/status'); if (st?.success) { setStatusMsg(formatStatus(st.status)); if (typeof st.status?.enabled==='boolean') setDetectorEnabled(st.status.enabled) } } catch {} }
  async function start() { const r = await fetch('/emotion_detector/start', { method: 'POST' }).then(r=>r.json()); setStatusMsg(r.message || ''); await refreshStatus() }
  async function stop() { const r = await fetch('/emotion_detector/stop', { method: 'POST' }).then(r=>r.json()); setStatusMsg(r.message || ''); await refreshStatus() }
  async function enable() { const r = await fetch('/emotion_detector/enable', { method: 'POST' }).then(r=>r.json()); setStatusMsg(r.message || ''); await refreshStatus() }
  async function disable() { const r = await fetch('/emotion_detector/disable', { method: 'POST' }).then(r=>r.json()); setStatusMsg(r.message || ''); await refreshStatus() }
  async function setIntervalSeconds(sec) {
    const v = Number(sec)
    if (!Number.isFinite(v) || v < 1) { setStatusMsg('Please enter a valid interval (1-60 seconds)'); return }
    const fd = new FormData(); fd.append('interval', v)
    const r = await postForm('/emotion_detector/set_interval', fd)
    setStatusMsg(r.message || '')
  }
  async function getCurrent() { const d = await getJson('/emotion_detector/current'); if (d?.success) setCurrentEmotion(d.emotion || '') }
  async function getAIWithEmotion() {
    setLoading(true)
    addMessage('bot', 'AI Assistant', 'Getting AI response with your current emotion...')
    try {
      const d = await getJson('/emotion_detector/ai_with_emotion')
      if (d?.success) {
        addMessage('bot', 'AI Assistant (Emotion-Aware)', d.response)
        try {
          if (autoSpeak && typeof d.response === 'string' && d.response.trim()) {
            const sfd = new FormData(); sfd.append('text', d.response)
            await postForm('/speak', sfd)
          }
        } catch {}
      }
      else addMessage('bot', 'Error', "Sorry, I couldn't get an AI response with emotion context.")
    } catch { addMessage('bot', 'Error', 'Sorry, I encountered an error getting AI response with emotion.') }
    finally { setLoading(false) }
  }
  async function downloadEmotionFile() { try { await download('/emotion_detector/emotion_file', 'current_emotion.txt'); setStatusMsg('Emotion file downloaded successfully') } catch { setStatusMsg('Error downloading emotion file') } }
  async function downloadConversation() { try { await download('/conversation/download', 'conversation_log.txt'); setStatusMsg('Conversation log downloaded successfully') } catch { setStatusMsg('Error downloading conversation log') } }

  async function refreshMemory() {
    try {
      const d = await getJson('/memory/status')
      if (d?.success) {
        const txt = `Memory Entries: ${d.memory_entries}\nRecent Conversations: ${d.recent_conversations.length}\n\nRecent Conversations:\n${(d.recent_conversations||[]).map(conv => `[${conv.timestamp}]\nUser: ${conv.user}\nAI: ${conv.ai}\n${conv.emotion ? `Emotion: ${conv.emotion}` : ''}\n---`).join('\n')}`
        setMemoryStatus(txt)
      } else setMemoryStatus('Error getting memory status')
    } catch { setMemoryStatus('Error getting memory status') }
  }
  async function clearMemory() { try { const r = await fetch('/memory/clear', { method: 'POST' }).then(r=>r.json()); if (r?.success) { setMemoryStatus('Memory cleared successfully'); refreshMemory() } else setMemoryStatus('Error clearing memory') } catch { setMemoryStatus('Error clearing memory') } }
  async function downloadMemory() { try { await download('/memory/download', 'conversation_memory.json'); setMemoryStatus('Memory file downloaded successfully') } catch { setMemoryStatus('Error downloading memory file') } }

  async function generateReport() {
    setLoading(true)
    try {
      const r = await fetch('/generate_report', { method: 'POST' }).then(r=>r.json())
      if (r?.success) {
        setAnalysis(r.analysis)
        await refreshReports()
        addMessage('bot', 'Report Generator', `Mental health analysis report generated successfully! The report has been saved as ${r.report_filename} and contains analysis of ${r.conversation_count} conversations.`)
      } else {
        addMessage('bot', 'Error', `Sorry, I couldn't generate the report: ${r.message}`)
      }
    } catch {
      addMessage('bot', 'Error', 'Sorry, I encountered an error generating the report.')
    } finally { setLoading(false) }
  }
  async function refreshReports() { const d = await getJson('/reports/list'); if (d?.success) setReports(d.reports || []) }
  async function downloadReport(filename) { try { await download(`/reports/download/${filename}`, filename) } catch {} }

  async function setLanguageServer(code) {
    const fd = new FormData(); fd.append('language', code)
    const r = await postForm('/language/set', fd)
    if (r?.success) {
      setLanguage(r.language)
      addMessage('bot', 'Language Settings', `Language successfully changed to ${r.language}. I will now respond in this language and recognize voice commands in this language.`)
    } else {
      addMessage('bot', 'Error', `Failed to change language: ${r?.message || 'Unknown error'}`)
    }
  }

  return (
    <div className="container">
      <a className="analysisBtn" href="/ui/reports.html">Analysis</a>
      <header className="header">
        <div className="headerInner">
          <div className="headerLeft">
            <div className="agentAvatar">AI<div className="statusDot" /></div>
            <h1>Mindful Chat</h1>
          </div>
          <div className="statusRow"><span className="statusDotLive" /> <span className="readyText">Ready to Listen</span></div>
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <div className="panel">
            <h3>Language Settings</h3>
            <div className="row">
              <span className="label">Select Language:</span>
              <select className="select" value={language} onChange={(e)=>setLanguage(e.target.value)}>
                {[{code: 'en-US', name: 'English (US)'}].concat(languages).reduce((acc, cur) => {
                  if (acc.find(a => a.code === cur.code)) return acc; acc.push(cur); return acc;
                }, []).map(l => (
                  <option key={l.code} value={l.code}>{l.name || l.code}</option>
                ))}
              </select>
              <button className="btn" onClick={()=>setLanguageServer(language)}>Set Language</button>
            </div>
          </div>

          <div className="panel">
            <h3>Emotion Detection</h3>
            <div className="row" style={{ alignItems: 'center', justifyContent: 'space-between' }}>
              <span className="label">Background Detection</span>
              <div role="switch" aria-checked={detectorEnabled} className={`toggle ${detectorEnabled ? 'on' : ''}`} onClick={() => detectorEnabled ? disable() : enable()}>
                <div className="toggleKnob" />
              </div>
            </div>
            <div className="row" style={{ justifyContent: 'center', gap: 10 }}>
              <button className="btn success" onClick={start}>Start</button>
              <button className="btn danger" onClick={stop}>Stop</button>
            </div>
            <div className="row" style={{ marginTop: 10 }}>
              <span className="label">Interval (s):</span>
              <input className="select" type="number" min="1" max="60" defaultValue={5} onBlur={(e)=>setIntervalSeconds(e.target.value)} />
              <button className="btn" onClick={()=>{ const el=document.activeElement; if (el && el.blur) el.blur(); }}>Set</button>
            </div>
            <div className="row" style={{ justifyContent: 'center', gap: 10, marginTop: 10 }}>
              <button className="btn secondary" onClick={getCurrent}>Current Emotion</button>
              <button className="btn" onClick={getAIWithEmotion}>AI with Emotion</button>
            </div>
            <div className="row" style={{ justifyContent: 'center', gap: 10, marginTop: 10 }}>
              <button className="btn secondary" onClick={downloadEmotionFile}>Download Emotion</button>
              <button className="btn success" onClick={downloadConversation}>Download Chat</button>
            </div>
            <div className="status" style={{ marginTop: 10 }}>{statusMsg}</div>
            <div className="status" style={{ marginTop: 10 }}>{currentEmotion ? `Current Emotion: ${currentEmotion}` : 'No emotion detected yet'}</div>
          </div>

          <div className="panel">
            <h3>Conversation Memory</h3>
            <div className="row" style={{ justifyContent: 'center', gap: 10 }}>
              <button className="btn info" onClick={refreshMemory}>Memory Status</button>
              <button className="btn warning" onClick={clearMemory}>Clear Memory</button>
              <button className="btn secondary" onClick={downloadMemory}>Download Memory</button>
            </div>
            <div className="status" style={{ marginTop: 10 }}>{memoryStatus || 'No memory status yet'}</div>
          </div>

          <div className="panel">
            <h3>Mental Health Reports</h3>
            <div className="row" style={{ justifyContent: 'center', gap: 10 }}>
              <button className="btn" onClick={generateReport} disabled={loading}>Generate Report</button>
              <button className="btn info" onClick={refreshReports}>List Reports</button>
            </div>
            <div className="status" style={{ marginTop: 10 }}>
              {reports.length === 0 ? 'No reports available yet. Generate a report first!' : (
      <div>
                  <div style={{ fontWeight: 600, marginBottom: 6 }}>Available Reports ({reports.length})</div>
                  <div className="reportsList">
                    {reports.map(r => (
                      <div key={r.filename} className="reportItem">
                        <div className="reportMeta">
                          <div className="reportName" title={r.filename}>{r.filename}</div>
                          <div className="reportSub">Created: {r.created} | Size: {(r.size/1024).toFixed(1)} KB</div>
                        </div>
                        <button className="reportBtn" onClick={() => downloadReport(r.filename)}>Download</button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            {analysis && (
              <div className="status" style={{ marginTop: 10 }}>
                <div style={{ fontWeight: 600, marginBottom: 6 }}>Latest Analysis Report</div>
                <div style={{ background: '#fff', border: '1px solid #e9ecef', borderRadius: 6, padding: 10 }}>
                  <div style={{ marginBottom: 8 }}><strong>Analysis Report:</strong> {analysis.analysied_report || 'No analysis report available'}</div>
                  <div style={{ marginBottom: 8 }}><strong>Root Cause:</strong> {analysis.root_case || 'No root cause identified'}</div>
                  <div style={{ marginBottom: 8 }}><strong>Mental Health Assessment:</strong> {analysis.mental_illness || 'No mental health assessment available'}</div>
                  <div style={{ marginBottom: 8 }}><strong>Identified Problems:</strong> {analysis.problem || 'No specific problems identified'}</div>
                  <div style={{ marginBottom: 0 }}><strong>Recommendations:</strong> {analysis.recommendation || 'No specific recommendations available'}</div>
                </div>
              </div>
            )}
          </div>
        </aside>

        <main className="card">
          <div className="chatHeader">
            <div className="chatTitle">
              <div className="agentAvatar">AI</div>
              <span>Mindful Chat</span>
              <span className="chatBadge">Buoyant Day</span>
            </div>
            <div className="statusRow"><span className="statusDotLive" /> Ready to Listen</div>
          </div>
          <div className="chat" ref={chatRef}>
            {messages.map((m, i) => (
              <Message key={i} type={m.type} sender={m.sender} content={m.content} />
            ))}
          </div>
          <div className="inputBar">
            <div className="inputRow">
              <div className="inputField">
                <input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  onKeyDown={(e) => { if (e.key === 'Enter') sendMessage() }}
                  placeholder="Share what's on your mind..."
                  autoComplete="off"
                />
                <button type="button" className="micBtn" title="Voice" onClick={voiceCommand} disabled={loading}>🎤</button>
                <select
                  className="langSelect"
                  value={language}
                  onChange={async (e)=>{ const code = e.target.value; setLanguage(code); try { await setLanguageServer(code) } catch {} }}
                >
                  {[{code: 'en-US', name: 'English (US)'}].concat(languages).reduce((acc, cur) => { if (acc.find(a => a.code === cur.code)) return acc; acc.push(cur); return acc; }, []).map(l => (
                    <option key={l.code} value={l.code}>{l.name || l.code}</option>
                  ))}
                </select>
              </div>
              <button className="sendBtn" onClick={sendMessage} disabled={loading}>Send</button>
            </div>
            <div className="row" style={{ justifyContent: 'flex-end', gap: 10 }}>
              <span className="label">Speak replies</span>
              <div role="switch" aria-checked={autoSpeak} className={`toggle ${autoSpeak ? 'on' : ''}`} onClick={() => setAutoSpeak(v => !v)}>
                <div className="toggleKnob" />
              </div>
            </div>
            {/* Quick mood chips removed as requested */}
          </div>
        </main>
      </div>

      {/* Removed global Processing overlay to avoid blocking the UI */}
      </div>
  )
}

export default App
