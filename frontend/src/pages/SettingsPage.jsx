import { useState, useEffect } from 'react';
import { apiFetch } from '../utils/api';

export default function SettingsPage() {
  const [health, setHealth] = useState(null);

  useEffect(() => {
    apiFetch('/health').then(setHealth).catch(() => setHealth({ status: 'error' }));
  }, []);

  const ollama = health?.ollama || {};
  const isCloud = ollama.cloud || Boolean(ollama.host && ollama.host.includes('ollama.com'));
  const isConnected = ollama.library || ollama.rest;

  return (
    <div className="settings-page">
      <div>
        <h1>SYSTEM & NEURAL ENGINE SETTINGS</h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          Inference backend, speech synthesis engines, and device configuration.
        </p>
      </div>

      <div className="settings-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3>🤖 LLM Core & Cloud Link</h3>
          <span style={{ fontSize: 18 }}>⚡</span>
        </div>

        <div className="connection-status">
          <span className={`status-dot ${isConnected ? '' : 'offline'}`} />
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 15, fontWeight: 700, fontFamily: 'var(--font-display)', color: 'var(--text-primary)' }}>
              {isCloud
                ? 'Connected to Ollama Cloud ☁️'
                : ollama.library
                  ? 'Connected via Ollama Library ⚡'
                  : ollama.rest
                    ? 'Connected via REST API 🌐'
                    : 'Not Connected'}
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
              Active Model: <strong style={{ color: 'var(--accent)' }}>{ollama.model || 'N/A'}</strong>
            </div>
          </div>
        </div>

        {ollama.available_models && (
          <div style={{ marginTop: 20 }}>
            <div style={{
              fontSize: 11,
              color: 'var(--accent-amber)',
              marginBottom: 10,
              fontFamily: 'var(--font-display)',
              fontWeight: 800,
              letterSpacing: 1
            }}>
              AVAILABLE CLOUD & LOCAL MODELS ({ollama.available_models.length})
            </div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
              {ollama.available_models.map((m, i) => {
                const isCurrent = m === ollama.model || m.includes(ollama.model?.replace('-cloud', ''));
                return (
                  <span
                    key={i}
                    className="model-pill"
                    style={{
                      borderColor: isCurrent ? 'var(--accent)' : 'var(--border-bold)',
                      background: isCurrent ? 'rgba(244, 114, 182, 0.15)' : 'var(--bg-tertiary)',
                      color: isCurrent ? 'var(--accent)' : 'var(--text-secondary)'
                    }}
                  >
                    {isCurrent ? '★ ' : ''}{m}
                  </span>
                );
              })}
            </div>
          </div>
        )}
      </div>

      <div className="settings-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3>🎙️ Voice & Whisper Capabilities</h3>
          <span style={{ fontSize: 18 }}>🌸</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.6 }}>
          Using high-fidelity browser Web Speech API for low-latency hands-free companion dialogue.
        </div>
        <div style={{ marginTop: 14, display: 'flex', gap: 16, flexWrap: 'wrap' }}>
          <div style={{ background: 'var(--bg-input)', padding: '10px 16px', borderRadius: '8px', border: '1.5px solid var(--border-bold)' }}>
            <span style={{ color: 'var(--accent-violet)', fontWeight: 700 }}>🎤 Speech-to-Text:</span>{' '}
            {window.SpeechRecognition || window.webkitSpeechRecognition ? 'Available ✓' : 'Not Supported ✕'}
          </div>
          <div style={{ background: 'var(--bg-input)', padding: '10px 16px', borderRadius: '8px', border: '1.5px solid var(--border-bold)' }}>
            <span style={{ color: 'var(--accent)', fontWeight: 700 }}>🔊 Text-to-Speech:</span>{' '}
            {window.speechSynthesis ? 'Available ✓' : 'Not Supported ✕'}
          </div>
        </div>
      </div>

      <div className="settings-card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14 }}>
          <h3>💜 About FENRY</h3>
          <span style={{ fontSize: 18 }}>✨</span>
        </div>
        <div style={{ fontSize: 13, color: 'var(--text-secondary)', lineHeight: 1.8 }}>
          <strong style={{ color: 'var(--accent-amber)', fontSize: 14 }}>FENRY-GF Companion Suite v2.0</strong><br />
          • Powered by <strong>Ollama Cloud ({ollama.model || 'gpt-oss:20b-cloud'})</strong><br />
          • Intelligent Context Window with Long-term Rolling Compaction<br />
          • Persistent Entity-Relationship Knowledge Graph Memory<br />
          • Fast Reactive WebSockets with Python FastAPI + React
        </div>
      </div>
    </div>
  );
}
