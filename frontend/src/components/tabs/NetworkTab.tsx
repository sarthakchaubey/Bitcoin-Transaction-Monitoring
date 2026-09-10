import React, { useEffect, useRef, useState } from 'react';
import { motion } from 'motion/react';
import type { EvidencePackage, SubgraphNode, SubgraphEdge } from '@/types/forensics';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useTheme } from '@/context/ThemeContext';
import { RefreshCw, Share2, ShieldAlert } from 'lucide-react';
import { cn } from '@/lib/utils';

interface NetworkTabProps {
  evidenceList: EvidencePackage[];
  selectedWalletId: string;
  onSelectWallet: (walletId: string) => void;
}

interface SimNode extends SubgraphNode {
  x: number;
  y: number;
  vx: number;
  vy: number;
  radius: number;
  isDragging?: boolean;
}

export const NetworkTab: React.FC<NetworkTabProps> = ({
  evidenceList,
  selectedWalletId,
  onSelectWallet,
}) => {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const [hopDistance, setHopDistance] = useState<number>(2);
  const [physicsActive, setPhysicsActive] = useState<boolean>(true);
  const [inspectedNode, setInspectedNode] = useState<SubgraphNode | null>(null);
  const { isDark } = useTheme();

  const currentPkg =
    evidenceList.find((e) => e.wallet_id === selectedWalletId) ||
    evidenceList[0] ||
    null;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas || !currentPkg) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    let animationFrameId: number;

    const resizeCanvas = () => {
      if (canvas.parentElement) {
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = Math.max(540, canvas.parentElement.clientHeight || 540);
      }
    };

    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Build Sim Nodes
    const rawNodes = currentPkg.subgraph?.nodes || [];
    const rawEdges: SubgraphEdge[] = currentPkg.subgraph?.edges || [];

    const nodeMap = new Map<string, SimNode>();
    const centerX = canvas.width / 2;
    const centerY = canvas.height / 2;

    rawNodes.forEach((n, idx) => {
      const angle = (idx / Math.max(1, rawNodes.length)) * Math.PI * 2;
      const isTarget = n.id === currentPkg.wallet_id || n.type === 'target';
      const radius = isTarget ? 15 : n.type === 'transaction' ? 11 : 9;
      const dist = isTarget ? 0 : 100 + Math.random() * 90;

      nodeMap.set(n.id, {
        ...n,
        type: isTarget ? 'target' : n.type,
        x: centerX + Math.cos(angle) * dist,
        y: centerY + Math.sin(angle) * dist,
        vx: 0,
        vy: 0,
        radius: radius,
      });
    });

    const simNodes = Array.from(nodeMap.values());

    let draggedNode: SimNode | null = null;
    let panX = 0;
    let panY = 0;
    let zoom = 1.0;
    let isPanning = false;
    let startPanX = 0;
    let startPanY = 0;

    const handleMouseDown = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const mouseX = (e.clientX - rect.left - panX) / zoom;
      const mouseY = (e.clientY - rect.top - panY) / zoom;

      // Check if clicking node
      for (const n of simNodes) {
        const d = Math.hypot(n.x - mouseX, n.y - mouseY);
        if (d <= n.radius + 5) {
          draggedNode = n;
          n.isDragging = true;
          setInspectedNode(n);
          return;
        }
      }

      // Otherwise pan
      isPanning = true;
      startPanX = e.clientX - panX;
      startPanY = e.clientY - panY;
    };

    const handleMouseMove = (e: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      if (draggedNode) {
        draggedNode.x = (e.clientX - rect.left - panX) / zoom;
        draggedNode.y = (e.clientY - rect.top - panY) / zoom;
        draggedNode.vx = 0;
        draggedNode.vy = 0;
      } else if (isPanning) {
        panX = e.clientX - startPanX;
        panY = e.clientY - startPanY;
      }
    };

    const handleMouseUp = () => {
      if (draggedNode) {
        draggedNode.isDragging = false;
        draggedNode = null;
      }
      isPanning = false;
    };

    const handleWheel = (e: WheelEvent) => {
      e.preventDefault();
      const zoomFactor = e.deltaY < 0 ? 1.08 : 0.92;
      zoom = Math.max(0.4, Math.min(2.5, zoom * zoomFactor));
    };

    canvas.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel);

    const colors: Record<string, string> = isDark
      ? {
          target: '#EF4444',
          wallet: '#38BDF8',
          transaction: '#94A3B8',
          ip: '#FB923C',
          edge: '#334155',
          text: '#E2E8F0',
          bg: '#0B1220',
        }
      : {
          target: '#DC2626',
          wallet: '#0284C7',
          transaction: '#64748B',
          ip: '#EA580C',
          edge: '#CBD5E1',
          text: '#1E293B',
          bg: '#F8FAFC',
        };

    const animate = () => {
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      ctx.save();
      ctx.translate(panX, panY);
      ctx.scale(zoom, zoom);

      // Simple spring physics
      if (physicsActive) {
        // Repulsion
        for (let i = 0; i < simNodes.length; i++) {
          for (let j = i + 1; j < simNodes.length; j++) {
            const n1 = simNodes[i];
            const n2 = simNodes[j];
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.hypot(dx, dy) || 1;
            if (dist < 190) {
              const force = (190 - dist) / 190;
              const fx = (dx / dist) * force * 1.3;
              const fy = (dy / dist) * force * 1.3;
              if (!n1.isDragging) {
                n1.vx -= fx;
                n1.vy -= fy;
              }
              if (!n2.isDragging) {
                n2.vx += fx;
                n2.vy += fy;
              }
            }
          }
        }

        // Attraction for edges
        for (const edge of rawEdges) {
          const n1 = nodeMap.get(edge.source);
          const n2 = nodeMap.get(edge.target);
          if (n1 && n2) {
            const dx = n2.x - n1.x;
            const dy = n2.y - n1.y;
            const dist = Math.hypot(dx, dy) || 1;
            const idealDist = 95;
            const force = (dist - idealDist) * 0.035;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (!n1.isDragging) {
              n1.vx += fx;
              n1.vy += fy;
            }
            if (!n2.isDragging) {
              n2.vx += fx;
              n2.vy += fy;
            }
          }
        }

        // Apply velocity & damping
        simNodes.forEach((n) => {
          if (!n.isDragging) {
            // Pull towards center
            n.vx += (centerX - n.x) * 0.005;
            n.vy += (centerY - n.y) * 0.005;

            n.vx *= 0.85;
            n.vy *= 0.85;

            n.x += n.vx;
            n.y += n.vy;
          }
        });
      }

      // Draw Edges
      rawEdges.forEach((edge) => {
        const n1 = nodeMap.get(edge.source);
        const n2 = nodeMap.get(edge.target);
        if (n1 && n2) {
          ctx.beginPath();
          ctx.moveTo(n1.x, n1.y);
          ctx.lineTo(n2.x, n2.y);
          ctx.strokeStyle = colors.edge;
          ctx.lineWidth = 1.5;
          ctx.stroke();

          // Arrow head
          const angle = Math.atan2(n2.y - n1.y, n2.x - n1.x);
          const arrowX = n2.x - Math.cos(angle) * (n2.radius + 3);
          const arrowY = n2.y - Math.sin(angle) * (n2.radius + 3);

          ctx.beginPath();
          ctx.moveTo(arrowX, arrowY);
          ctx.lineTo(arrowX - 7 * Math.cos(angle - Math.PI / 6), arrowY - 7 * Math.sin(angle - Math.PI / 6));
          ctx.lineTo(arrowX - 7 * Math.cos(angle + Math.PI / 6), arrowY - 7 * Math.sin(angle + Math.PI / 6));
          ctx.closePath();
          ctx.fillStyle = colors.edge;
          ctx.fill();
        }
      });

      // Draw Nodes
      simNodes.forEach((n) => {
        const color = colors[n.type] || '#A0AEC0';

        if (n.type === 'target') {
          // Outer glow for target
          ctx.beginPath();
          ctx.arc(n.x, n.y, n.radius + 8, 0, Math.PI * 2);
          ctx.fillStyle = isDark ? 'rgba(239, 68, 68, 0.25)' : 'rgba(220, 38, 38, 0.2)';
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = colors.bg;
        ctx.lineWidth = 2.5;
        ctx.stroke();

        // Node Label
        ctx.font = '10px "IBM Plex Mono", monospace';
        ctx.fillStyle = colors.text;
        ctx.textAlign = 'center';
        const label = (n.label || n.id).substring(0, 10);
        ctx.fillText(label, n.x, n.y + n.radius + 13);
      });

      ctx.restore();

      animationFrameId = requestAnimationFrame(animate);
    };

    animate();

    return () => {
      window.removeEventListener('resize', resizeCanvas);
      canvas.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('wheel', handleWheel);
      cancelAnimationFrame(animationFrameId);
    };
  }, [currentPkg, physicsActive, hopDistance, isDark]);

  if (!currentPkg) {
    return (
      <Card className="text-center py-16 px-4">
        <ShieldAlert className="h-12 w-12 text-muted-foreground mx-auto mb-3 opacity-40" />
        <h3 className="font-serif text-base font-bold text-foreground">No network data available</h3>
      </Card>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-4"
    >
      {/* Network Header & Controls */}
      <div className="flex flex-wrap items-center justify-between gap-4 pb-2">
        <div>
          <h2 className="font-serif text-xl sm:text-2xl font-bold tracking-tight text-foreground flex items-center gap-2">
            <Share2 className="h-5 w-5 text-accent" />
            Topological Subgraph Explorer
          </h2>
          <p className="text-xs text-muted-foreground mt-0.5">
            Directed multi-hop transaction flow and broadcast IP geolocations
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <select
            className="h-9 px-3 py-1 text-xs font-mono rounded-md border border-input bg-card-raised text-foreground focus:outline-none focus:ring-1 focus:ring-accent max-w-xs cursor-pointer shadow-sm"
            value={currentPkg.wallet_id}
            onChange={(e) => onSelectWallet(e.target.value)}
          >
            {evidenceList.map((e) => (
              <option key={e.wallet_id} value={e.wallet_id} className="bg-card text-foreground">
                {e.wallet_id.substring(0, 16)}... ({Number(e.final_risk_score).toFixed(1)})
              </option>
            ))}
          </select>

          {/* Hop Selector */}
          <div className="inline-flex bg-card-raised border border-border rounded-md p-0.5 gap-0.5">
            {[1, 2, 3].map((h) => (
              <button
                key={h}
                onClick={() => setHopDistance(h)}
                className={cn(
                  'px-2.5 py-1 text-xs font-mono rounded transition-all font-medium',
                  hopDistance === h
                    ? 'bg-accent text-accent-foreground font-semibold shadow-sm'
                    : 'text-muted-foreground hover:text-foreground'
                )}
              >
                {h} Hop{h > 1 ? 's' : ''}
              </button>
            ))}
          </div>

          <Button
            variant={physicsActive ? 'accent' : 'outline'}
            size="sm"
            onClick={() => setPhysicsActive(!physicsActive)}
            className="text-xs h-9 gap-1.5"
          >
            <RefreshCw className={cn('h-3.5 w-3.5', physicsActive && 'animate-spin')} style={{ animationDuration: '8s' }} />
            {physicsActive ? 'Physics: Live' : 'Physics: Frozen'}
          </Button>
        </div>
      </div>

      {/* Main Canvas Container with Floating Overlay */}
      <Card className="relative w-full h-[540px] shadow-card border-border/80 overflow-hidden bg-card">
        <canvas
          ref={canvasRef}
          className="w-full h-full block cursor-grab active:cursor-grabbing"
        />

        {/* Legend Overlay */}
        <div className="absolute bottom-4 left-4 p-3.5 rounded-lg border border-border/80 bg-card/90 backdrop-blur-md text-xs shadow-lg space-y-2 max-w-xs pointer-events-none sm:pointer-events-auto">
          <div className="font-bold text-foreground text-[11px] uppercase tracking-wider">
            Node Taxonomy Legend
          </div>
          <div className="space-y-1.5 text-[11px] text-muted-foreground">
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-red-500 shadow-[0_0_6px_rgba(239,68,68,0.7)]" />
              <span className="text-foreground font-medium">Target Anomaly Wallet ({Number(currentPkg.final_risk_score).toFixed(1)})</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-sky-400" />
              <span>Counterparty Wallets</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-slate-400" />
              <span>Transaction Intermediary Hubs</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="h-2.5 w-2.5 rounded-full bg-orange-400" />
              <span>Broadcast IP Geolocation</span>
            </div>
          </div>
        </div>

        {/* Selected Node Details Drawer */}
        {inspectedNode && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="absolute top-4 right-4 p-4 rounded-lg border border-border/80 bg-card/95 backdrop-blur-md shadow-2xl max-w-xs text-xs space-y-2"
          >
            <div className="flex items-center justify-between">
              <span className="text-[10px] font-bold uppercase tracking-wider text-accent">
                Inspected Graph Node
              </span>
              <Badge variant="outline" className="text-[10px] uppercase font-mono">
                {inspectedNode.type}
              </Badge>
            </div>
            <div className="font-mono text-xs font-bold text-foreground break-all select-all">
              {inspectedNode.id}
            </div>
            {inspectedNode.country && (
              <div className="text-muted-foreground pt-1 border-t border-border/60">
                Jurisdiction: <strong className="text-foreground">{inspectedNode.country}</strong>
              </div>
            )}
          </motion.div>
        )}
      </Card>
    </motion.div>
  );
};
