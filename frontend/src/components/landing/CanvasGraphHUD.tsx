import React, { useEffect, useRef } from 'react';
import { motion } from 'motion/react';
import { Cpu, Database, Activity, Radio, ShieldCheck } from 'lucide-react';
import { useTheme } from '@/context/ThemeContext';

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
  const { isDark } = useTheme();

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const resizeCanvas = () => {
      if (canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = canvas.parentElement.clientHeight || 230;
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Color definitions based on active theme
    const colors = isDark
      ? {
          wallet: '#38BDF8',
          tx: '#94A3B8',
          ip: '#FB923C',
          target: '#EF4444',
          line: 'rgba(51, 65, 85, ',
        }
      : {
          wallet: '#0284C7',
          tx: '#64748B',
          ip: '#EA580C',
          target: '#DC2626',
          line: 'rgba(203, 213, 225, ',
        };

    const nodeTypes: ('wallet' | 'tx' | 'ip' | 'target')[] = ['wallet', 'tx', 'ip', 'target'];
    const nodes: NodeParticle[] = [];

    const numNodes = Math.max(28, Math.floor(canvas.width / 32));
    for (let i = 0; i < numNodes; i++) {
      nodes.push({
        x: Math.random() * canvas.width,
        y: Math.random() * canvas.height,
        vx: (Math.random() - 0.5) * 0.6,
        vy: (Math.random() - 0.5) * 0.6,
        radius: Math.random() * 2.5 + 2,
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

        // Mouse interaction
        const dx = n.x - mouseX;
        const dy = n.y - mouseY;
        const dist = Math.sqrt(dx * dx + dy * dy);
        if (dist < 90) {
          n.x += (dx / dist) * 1.5;
          n.y += (dy / dist) * 1.5;
        }

        // Draw node
        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = colors[n.type];
        ctx.fill();

        // Connect nearby nodes
        for (let j = i + 1; j < nodes.length; j++) {
          const n2 = nodes[j];
          const d = Math.hypot(n.x - n2.x, n.y - n2.y);
          if (d < 110) {
            ctx.beginPath();
            ctx.moveTo(n.x, n.y);
            ctx.lineTo(n2.x, n2.y);
            ctx.strokeStyle = `${colors.line}${1 - d / 110})`;
            ctx.lineWidth = 0.75;
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
  }, [isDark]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4 }}
      className="relative w-full h-56 sm:h-60 rounded-xl border border-border bg-card overflow-hidden mb-6 shadow-card"
    >
      <canvas
        ref={canvasRef}
        className="absolute inset-0 w-full h-full block"
      />

      <div className="absolute inset-0 pointer-events-none flex flex-col justify-between p-4 sm:p-6 bg-gradient-to-t from-background/90 via-background/40 to-transparent">
        {/* Header HUD */}
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="text-[11px] font-bold uppercase tracking-widest text-accent flex items-center gap-1.5">
              <ShieldCheck className="h-3.5 w-3.5" />
              Autonomous Forensics Telemetry
            </div>
            <h2 className="font-serif text-lg sm:text-2xl font-bold text-foreground mt-0.5">
              Bitcoin Anomaly Live HUD
            </h2>
          </div>

          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-md border border-border/80 bg-card/80 backdrop-blur-sm text-xs font-mono text-emerald-500 font-semibold shadow-sm">
            <div className="beacon-dot" />
            <span>TELEMETRY ACTIVE</span>
          </div>
        </div>

        {/* Bottom System Status Bar */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 pt-3 border-t border-border/70 font-mono text-[11px] text-muted-foreground backdrop-blur-[2px]">
          <div className="flex items-center gap-2">
            <Cpu className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">
              ANOMALY: <strong className="text-emerald-500 font-bold">ONLINE</strong>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Database className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">
              LOUVAIN: <strong className="text-emerald-500 font-bold">SYNCED</strong>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">
              EXPLAINABILITY: <strong className="text-accent font-bold">SHAP v0.42</strong>
            </span>
          </div>
          <div className="flex items-center gap-2">
            <Radio className="h-3.5 w-3.5 text-accent shrink-0" />
            <span className="truncate">
              PIPELINE: <strong className="text-foreground font-bold">OFFLINE AML</strong>
            </span>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
