import { useState, useEffect } from 'react';
import { apiFetch, apiPut, apiPost } from '../utils/api';

export default function PersonaPage() {
  const [persona, setPersona] = useState(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    apiFetch('/persona').then(setPersona).catch(() => { });
  }, []);

  if (!persona) {
    return (
      <div className="persona-page">
        <h1>PERSONA CONFIGURATION</h1>
        <p style={{ color: 'var(--text-dim)' }}>Loading FENRY's heart parameters...</p>
      </div>
    );
  }

  const style = persona.style || {};
  const update = (key, val) => {
    setPersona(prev => ({ ...prev, [key]: val }));
    setSaved(false);
  };
  const updateStyle = (key, val) => {
    setPersona(prev => ({ ...prev, style: { ...prev.style, [key]: val } }));
    setSaved(false);
  };

  const handleSave = async () => {
    await apiPut('/persona', {
      name: persona.name,
      tone: style.tone,
      address_user: style.address_user,
      emoji: style.emoji,
      interests: persona.interests,
      affection_level: persona.affection_level,
    });
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleReset = async () => {
    const data = await apiPost('/persona/reset');
    setPersona(data);
  };

  return (
    <div className="persona-page">
      <div>
        <h1>PERSONA & SOUL SETTINGS</h1>
        <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4 }}>
          Fine-tune FENRY's romantic affection, vocal tone, pet names, and core personality traits.
        </p>
      </div>

      <div className="persona-grid">
        {/* Card 1: Identity */}
        <div className="persona-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h3>👑 Companion Identity</h3>
            <span style={{ fontSize: 18 }}>🌸</span>
          </div>

          <div className="form-group">
            <label>COMPANION NAME</label>
            <input
              className="form-input"
              value={persona.name || ''}
              onChange={e => update('name', e.target.value)}
              placeholder="e.g. FENRY"
            />
          </div>

          <div className="form-group">
            <label>ROMANTIC TONE & VIBE</label>
            <input
              className="form-input"
              value={style.tone || ''}
              onChange={e => updateStyle('tone', e.target.value)}
              placeholder="e.g. gentle, deeply loving, playful, comforting"
            />
          </div>

          <div className="form-group">
            <label>PET NAMES & ENDEARMENTS (comma separated)</label>
            <input
              className="form-input"
              value={(style.address_user || []).join(', ')}
              onChange={e => updateStyle('address_user', e.target.value.split(',').map(s => s.trim()))}
              placeholder="e.g. babe, my love, handsome, sweetheart"
            />
          </div>
        </div>

        {/* Card 2: Personality & Affection */}
        <div className="persona-card">
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14 }}>
            <h3>💞 Affection & Quirks</h3>
            <span style={{ fontSize: 18 }}>✨</span>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>AFFECTION LEVEL</span>
              <span style={{ color: 'var(--accent)', fontWeight: 800 }}>
                {Math.round((persona.affection_level || 0.8) * 100)}%
              </span>
            </label>
            <input
              type="range"
              className="form-slider"
              min="0"
              max="1"
              step="0.05"
              value={persona.affection_level || 0.8}
              onChange={e => update('affection_level', parseFloat(e.target.value))}
            />
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 10, color: 'var(--text-dim)', marginTop: 4 }}>
              <span>Sweet & Friendly</span>
              <span>Devoted Girlfriend</span>
              <span>Obsessively Loving</span>
            </div>
          </div>

          <div className="form-group" style={{ marginTop: 16 }}>
            <label>SHARED PASSIONS & INTERESTS</label>
            <input
              className="form-input"
              value={(persona.interests || []).join(', ')}
              onChange={e => update('interests', e.target.value.split(',').map(s => s.trim()))}
              placeholder="e.g. anime, late night coding, cozy gaming, stargazing"
            />
          </div>

          <div className="form-group" style={{ display: 'flex', alignItems: 'center', gap: 12, marginTop: 18 }}>
            <input
              type="checkbox"
              id="emoji-toggle"
              checked={style.emoji !== false}
              onChange={e => updateStyle('emoji', e.target.checked)}
              style={{ width: 18, height: 18, accentColor: 'var(--accent)', cursor: 'pointer' }}
            />
            <label htmlFor="emoji-toggle" style={{ margin: 0, cursor: 'pointer', fontSize: 13, color: 'var(--text-primary)' }}>
              Enable Playful Romantic Emojis (💖, 🌸, ✨)
            </label>
          </div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 14, marginTop: 8 }}>
        <button className="btn-primary" onClick={handleSave}>
          {saved ? '✓ HEART SYNCED!' : 'SAVE PERSONA CHANGES'}
        </button>
        <button className="btn-secondary" onClick={handleReset}>
          RESET TO DEFAULTS
        </button>
      </div>
    </div>
  );
}
