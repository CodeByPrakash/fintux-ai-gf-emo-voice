import { useState, useRef, useEffect } from 'react';
import AvatarPanel from '../components/AvatarPanel';
import { useWebSocket } from '../hooks/useWebSocket';
import { useVoice } from '../hooks/useVoice';

const STEPS = ['plan', 'act', 'respond', 'memorize'];

const ROMANTIC_STARTERS = [
  "How was your day, sweetheart? 🌸",
  "I was just thinking about you 💕",
  "Tell me something cute ✨",
  "What's your favorite thing about us? 💖"
];

function NeuralBar({ steps }) {
  if (!steps.length) return null;
  return (
    <div className="neural-overlay">
      <span className="neural-title">✦ Neural Flow</span>
      {STEPS.map((name, i) => {
        const step = steps.find(s => s.step === name);
        const cls = step ? (step.status === 'done' ? 'done' : 'active') : '';
        return (
          <span key={name} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            {i > 0 && <span className="neural-connector" />}
            <span className={`neural-step ${cls}`}>
              <span className="neural-dot" />
              <span>{name.toUpperCase()}</span>
            </span>
          </span>
        );
      })}
    </div>
  );
}

function ModeToggle({ mode, setMode }) {
  return (
    <div className="mode-toggle">
      <button
        className={`mode-btn ${mode === 'chat' ? 'active' : ''}`}
        onClick={() => setMode('chat')}
      >
        <span>💬</span> Chat
      </button>
      <button
        className={`mode-btn ${mode === 'voice' ? 'active' : ''}`}
        onClick={() => setMode('voice')}
      >
        <span>🎙️</span> Voice
      </button>
    </div>
  );
}

function VoiceTalkView({ listening, speaking, typing, thinkingSteps, onTap, lastFenryMsg }) {
  const pulseClass = listening ? 'listening' : speaking ? 'speaking' : typing ? 'thinking' : 'idle';
  const statusText = listening
    ? 'Listening to you...'
    : speaking
      ? 'FENRY is speaking...'
      : typing
        ? 'Thinking of you...'
        : 'Tap to whisper to FENRY';

  return (
    <div className="voice-talk-view">
      <NeuralBar steps={thinkingSteps} />

      <div className="voice-talk-center">
        {/* Live transcript */}
        {lastFenryMsg && (
          <div className="message-bubble fenry aria" style={{ maxWidth: '100%', marginBottom: 16 }}>
            <div className="msg-name">FENRY</div>
            <div>{lastFenryMsg}</div>
          </div>
        )}

        {/* Big mic button */}
        <button className={`voice-orb ${pulseClass}`} onClick={onTap}>
          <div className="voice-orb-inner">
            {listening ? '⏹' : '🎤'}
          </div>
        </button>

        <div className="voice-status">{statusText}</div>
      </div>
    </div>
  );
}

export default function ChatPage() {
  const { connected, messages, typing, affect, thinkingSteps, sendMessage, triggerProactive } = useWebSocket();
  const { listening, speaking, startListening, stopListening, speak } = useVoice();
  const [input, setInput] = useState('');
  const [mode, setMode] = useState('chat');
  const bottomRef = useRef(null);
  const lastSpokenRef = useRef(-1);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, typing]);

  // Auto-speak ARIA's completed messages in VOICE mode
  useEffect(() => {
    if (mode !== 'voice') return;
    const lastIdx = messages.length - 1;
    const last = messages[lastIdx];
    if (last && (last.role === 'aria' || last.role === 'fenry') && !last.streaming && last.content && lastSpokenRef.current !== lastIdx) {
      lastSpokenRef.current = lastIdx;
      speak(last.content);
    }
  }, [messages, mode]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input.trim());
    setInput('');
  };

  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleVoice = () => {
    if (listening) {
      stopListening();
    } else {
      startListening((text) => {
        sendMessage(text);
      });
    }
  };

  const formatTime = (t) => {
    if (!t) return '';
    const d = new Date(t);
    return d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const lastAriaMsg = [...messages].reverse().find(m => (m.role === 'aria' || m.role === 'fenry') && !m.streaming)?.content || '';

  return (
    <div className="chat-page">
      <div className="chat-center">
        <div className="chat-header">
          <span className={`status-dot ${connected ? '' : 'offline'}`} />
          <h2>FENRY</h2>
          <span style={{ fontSize: 13, color: 'var(--text-secondary)', flex: 1, fontFamily: 'var(--font-display)', fontWeight: 600 }}>
            {connected ? 'Your AI Companion • Spontaneous Mode 💫' : 'Reconnecting to heart link...'}
          </span>
          <button
            className="poke-btn"
            onClick={triggerProactive}
            title="Poke FENRY to casually start a conversation or check in"
          >
            🌸 Poke FENRY
          </button>
          <ModeToggle mode={mode} setMode={setMode} />
        </div>

        {mode === 'voice' ? (
          <VoiceTalkView
            listening={listening}
            speaking={speaking}
            typing={typing}
            thinkingSteps={thinkingSteps}
            onTap={handleVoice}
            lastFenryMsg={lastAriaMsg}
          />
        ) : (
          <>
            <NeuralBar steps={thinkingSteps} />

            <div className="messages-container">
              {messages.length === 0 && (
                <div style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'center',
                  justifyContent: 'center',
                  marginTop: 40,
                  textAlign: 'center',
                  gap: 16
                }}>
                  <div style={{
                    width: 72, height: 72,
                    borderRadius: '50%',
                    background: 'radial-gradient(circle, var(--accent) 0%, var(--accent-violet) 100%)',
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: 32,
                    boxShadow: 'var(--shadow-pop-rose)',
                    border: '2px solid #060509'
                  }}>
                    💖
                  </div>

                  <div>
                    <h3 style={{ fontFamily: 'var(--font-display)', fontSize: 22, fontWeight: 900, color: 'var(--text-primary)' }}>
                      Welcome Back, Darling
                    </h3>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginTop: 4, maxWidth: 360 }}>
                      I'm right here with you. What's on your mind today?
                    </p>
                  </div>

                  {/* Romantic Starters */}
                  <div style={{
                    display: 'flex',
                    flexWrap: 'wrap',
                    justifyContent: 'center',
                    gap: 10,
                    maxWidth: 500,
                    marginTop: 10
                  }}>
                    {ROMANTIC_STARTERS.map((text, idx) => (
                      <button
                        key={idx}
                        className="btn-secondary"
                        style={{ fontSize: 12, padding: '8px 16px' }}
                        onClick={() => sendMessage(text)}
                      >
                        {text}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {messages.map((msg, i) => (
                <div key={i} className={`message-bubble ${msg.role === 'user' ? 'user' : 'fenry'}`}>
                  <div className="msg-name">
                    {msg.role === 'user' ? 'YOU' : 'FENRY'}
                    {msg.isProactive && <span className="proactive-tag">🌸 Spontaneous</span>}
                  </div>
                  <div>{msg.content}</div>
                  <div className="msg-time">{formatTime(msg.time)}</div>
                </div>
              ))}

              {typing && (
                <div className="typing-indicator">
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                  <span className="typing-dot" />
                </div>
              )}
              <div ref={bottomRef} />
            </div>

            <div className="chat-input-area">
              <button
                className={`btn-icon ${listening ? 'recording' : ''}`}
                onClick={handleVoice}
                title={listening ? 'Stop listening' : 'Voice input'}
              >
                {listening ? '⏹' : '🎤'}
              </button>
              <textarea
                className="chat-input"
                rows={1}
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={handleKey}
                placeholder="Whisper something to FENRY..."
              />
              <button
                className="btn-icon send"
                onClick={handleSend}
                title="Send"
              >
                ➤
              </button>
            </div>
          </>
        )}
      </div>

      <AvatarPanel affect={affect} connected={connected} speaking={speaking} />
    </div>
  );
}
