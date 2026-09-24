import { useRef, useEffect } from 'react';

export default function AvatarPanel({ affect, connected, speaking }) {
  const canvasRef = useRef(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    const W = 200, H = 200;
    canvas.width = W; canvas.height = H;
    let frame = 0;
    let particles = Array.from({ length: 24 }, () => ({
      x: Math.random() * W, y: Math.random() * H,
      r: Math.random() * 2.5 + 1,
      speed: Math.random() * 0.4 + 0.2,
      angle: Math.random() * Math.PI * 2,
      color: Math.random() > 0.5 ? '#f472b6' : '#a78bfa'
    }));

    function draw() {
      ctx.clearRect(0, 0, W, H);
      const cx = W / 2, cy = H / 2;
      const mood = affect?.mood || 0.7;
      const energy = affect?.energy || 0.8;

      // Outer romantic halo
      const ringPulse = Math.sin(frame * 0.04) * 5;
      ctx.beginPath();
      ctx.arc(cx, cy, 78 + ringPulse, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(244, 114, 182, ${0.2 + mood * 0.25})`;
      ctx.lineWidth = 2.5;
      ctx.stroke();

      // Middle starry ring
      ctx.beginPath();
      ctx.arc(cx, cy, 62 + ringPulse * 0.7, 0, Math.PI * 2);
      ctx.strokeStyle = `rgba(167, 139, 250, ${0.15 + energy * 0.2})`;
      ctx.lineWidth = 2;
      ctx.stroke();

      // Inner ambient aura
      const grad = ctx.createRadialGradient(cx, cy, 10, cx, cy, 55);
      grad.addColorStop(0, speaking ? 'rgba(244, 114, 182, 0.45)' : 'rgba(167, 139, 250, 0.25)');
      grad.addColorStop(0.8, 'rgba(251, 191, 36, 0.1)');
      grad.addColorStop(1, 'transparent');
      ctx.fillStyle = grad;
      ctx.fillRect(0, 0, W, H);

      // Core pulsating sphere
      ctx.beginPath();
      const coreR = 36 + (speaking ? Math.sin(frame * 0.15) * 6 : Math.sin(frame * 0.05) * 2);
      ctx.arc(cx, cy, coreR, 0, Math.PI * 2);
      const coreGrad = ctx.createRadialGradient(cx - 10, cy - 10, 5, cx, cy, 38);
      coreGrad.addColorStop(0, '#fbcfe8');
      coreGrad.addColorStop(0.5, '#f472b6');
      coreGrad.addColorStop(1, '#8b5cf6');
      ctx.fillStyle = coreGrad;
      ctx.globalAlpha = 0.85;
      ctx.fill();
      ctx.globalAlpha = 1;

      // Orbiting starlight sparkles
      particles.forEach(p => {
        p.angle += p.speed * 0.025;
        p.x = cx + Math.cos(p.angle) * (52 + Math.sin(frame * 0.02 + p.angle) * 16);
        p.y = cy + Math.sin(p.angle) * (52 + Math.cos(frame * 0.02 + p.angle) * 16);
        ctx.beginPath();
        ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
        ctx.fillStyle = p.color;
        ctx.globalAlpha = 0.4 + Math.sin(frame * 0.05 + p.angle) * 0.3;
        ctx.fill();
        ctx.globalAlpha = 1;
      });

      frame++;
      requestAnimationFrame(draw);
    }
    const id = requestAnimationFrame(draw);
    return () => cancelAnimationFrame(id);
  }, [affect, speaking]);

  const bondScore = Math.round((affect?.attachment || 0.6) * 100);
  const moodScore = Math.round((affect?.mood || 0.7) * 100);
  const energyScore = Math.round((affect?.energy || 0.8) * 100);

  const getRelationshipLevel = (score) => {
    if (score >= 80) return 'Deeply Devoted 💖';
    if (score >= 60) return 'Sweet & Affectionate 💕';
    if (score >= 40) return 'Warm & Caring 🌸';
    return 'Getting Close ✨';
  };

  return (
    <aside className="avatar-panel">
      <div className="avatar-canvas-wrap">
        <canvas ref={canvasRef} className="avatar-canvas" />
      </div>

      <div className="avatar-label">
        FENRY <span className="heart-badge">💖</span>
      </div>

      <div className="avatar-status">
        <span
          className={`status-dot ${connected ? '' : 'offline'}`}
          style={{ display: 'inline-block', marginRight: 8 }}
        />
        {connected ? 'Neural Link Active ✦' : 'Reconnecting...'}
      </div>

      <div style={{
        background: 'var(--bg-tertiary)',
        border: '1.5px solid var(--border-bold)',
        borderRadius: 'var(--radius-full)',
        padding: '6px 14px',
        fontSize: '11px',
        fontWeight: '700',
        fontFamily: 'var(--font-display)',
        color: 'var(--accent-amber)',
        boxShadow: 'var(--shadow-pop-sm)'
      }}>
        {getRelationshipLevel(bondScore)}
      </div>

      <div className="affect-bars">
        <div className="affect-bar">
          <label>
            <span>💗 MOOD</span>
            <span>{moodScore}%</span>
          </label>
          <div className="affect-track">
            <div className="affect-fill mood" style={{ width: `${moodScore}%` }} />
          </div>
        </div>

        <div className="affect-bar">
          <label>
            <span>⚡ ENERGY</span>
            <span>{energyScore}%</span>
          </label>
          <div className="affect-track">
            <div className="affect-fill energy" style={{ width: `${energyScore}%` }} />
          </div>
        </div>

        <div className="affect-bar">
          <label>
            <span>💞 BOND</span>
            <span>{bondScore}%</span>
          </label>
          <div className="affect-track">
            <div className="affect-fill attachment" style={{ width: `${bondScore}%` }} />
          </div>
        </div>
      </div>
    </aside>
  );
}
