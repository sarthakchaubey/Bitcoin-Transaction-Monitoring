import React, { useEffect, useRef } from 'react';
import { Cpu, Database, Activity, Radio } from 'lucide-react';

interface NodeParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  type: 'wallet' | 'tx' | 'ip' | 'target';
}

export const CanvasGraphHUD: React.FC = () => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const resizeCanvas = () => {
      if (canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight;
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Color definitions
    const colors = {
      wallet: '#3182CE',
      tx: '#94A3B8',
      ip: '#B8562E',
      target: '#8B2E2E',
    };

    const nodeTypes: ('wallet' | 'tx' | 'ip' | 'target')[] = ['wallet', 'tx', 'ip', 'target'];
    const nodes: NodeParticle[] = [];

    const numNodes = Math.max(25, Math.floor(canvas.width / 35));
    for (let i = 0; i < numNodes; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.7,
        vy: (Math.random() - 0.5) * 0.7,
        radius: Math.random() * 3 + 2,
        type: nodeTypes[Math.floor(Math.random() * nodeTypes.length)],
      });
    }

    let mouseX = -1000;
    let mouseY = -1000;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      mouseX = e.clientX - rect.left;
      mouseY = e.clientY - rect.top;
    };

    const handleMouseLeave = () => {
      mouseX = -1000;
      mouseY = -1000;
    };

    canvas.addEventListener('mousemove', handleMouseMove);
    canvas.addEventListener('mouseleave', handleMouseLeave);

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      for (let i = 0; i < nodes.length; i++) {
        const n = nodes[i];
        n.x += n.vx;
        n.y += n.vy;

        if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
        if (n.y < 0 || n.y > canvas.height) n.vy *= -1;

        // Gentle mouse repulsion
        const dx = n.x - mouseX;
        const dy = n.y - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 90) {
          n.x += (dx / dist) * 1.6;
          n.y += (dy / dist) * 1.6;
        }

        // Draw particle node
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = colors[n.type];
        ctx.fill();

        // Connect nearby nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const d = Math.hypot(n.x - n2.x, n.y - n2.y);
          if (d < 115) {
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = `rgba(31, 42, 68, ${1 - d / 115})`;
            ctx.lineWidth = 0.8;
            ctx.stroke();
          }
        }
      }

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      canvas.removeEventListener('mousemove', handleMouseMove);
      canvas.removeEventListener('mouseleave', handleMouseLeave);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div
      style={{
        position: 'relative',
        width: '100%',
        height: '240px',
        border: '1px solid var(--border)',
        borderRadius: '8px',
        background: 'radial-gradient(circle at 50% 50%, #152238 0%, var(--bg) 100%)',
        overflow: 'hidden',
        marginBottom: '22px',
        boxShadow: '0 8px 24px rgba(0, 0, 0, 0.5)',
      }}
    >
      <canvas
        ref={canvasRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          display: 'block',
        }}
      />

      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          pointerEvents: 'none',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '18px 22px',
          background: 'linear-gradient(180deg, rgba(11, 18, 32, 0.3) 0%, rgba(11, 18, 32, 0.85) 100%)',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '0.74rem', textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--accent)', fontWeight: 700 }}>
              Autonomous Anomaly Telemetry
            </div>
            <h2 className="font-serif" style={{ fontSize: '1.45rem', fontWeight: 700, color: 'var(--text)', marginTop: '2px' }}>
              🛡️ Bitcoin Forensics Live HUD
            </h2>
          </div>

          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              backgroundColor: 'rgba(19, 27, 46, 0.85)',
              border: '1px solid var(--border)',
              padding: '6px 12px',
              borderRadius: '4px',
              fontFamily: 'IBM Plex Mono, monospace',
              fontSize: '0.78rem',
              color: '#68D391',
              boxShadow: '0 0 10px rgba(72, 187, 120, 0.15)',
            }}
          >
            <div className="beacon-dot" />
            TELEMETRY ACTIVE
          </div>
        </div>

        <div
          className="font-mono"
          style={{
            fontSize: '0.75rem',
            color: 'var(--text-muted)',
            display: 'flex',
            flexWrap: 'wrap',
            gap: '24px',
            borderTop: '1px solid rgba(31, 42, 68, 0.7)',
            paddingTop: '10px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Cpu size={14} color="var(--accent)" />
            <span>ANOMALY ENGINE: <strong style={{ color: '#68D391' }}>ONLINE</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Database size={14} color="var(--accent)" />
            <span>LOUVAIN CLUSTERING: <strong style={{ color: '#68D391' }}>SYNCED</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Activity size={14} color="var(--accent)" />
            <span>EXPLAINABILITY: <strong style={{ color: 'var(--accent)' }}>SHAP v0.42</strong></span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
            <Radio size={14} color="var(--accent)" />
            <span>PIPELINE: <strong style={{ color: 'var(--text)' }}>OFFLINE FORENSICS</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
};
