import React, { useEffect, useRef, useState } from 'react';
import type { EvidencePackage, SubgraphNode, SubgraphEdge } from '../../types/forensics';
import { RefreshCw } from 'lucide-react';

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
        canvas.height = Math.max(520, canvas.parentElement.clientHeight || 520);
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
      const radius = isTarget ? 14 : n.type === 'transaction' ? 10 : 8;
      const dist = isTarget ? 0 : 90 + Math.random() * 80;

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
        if (d <= n.radius + 4) {
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

    const colors: Record<string, string> = {
      target: '#8B2E2E',
      wallet: '#3182CE',
      transaction: '#A0AEC0',
      ip: '#B8562E',
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
            if (dist < 180) {
              const force = (180 - dist) / 180;
              const fx = (dx / dist) * force * 1.2;
              const fy = (dy / dist) * force * 1.2;
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
            const idealDist = 90;
            const force = (dist - idealDist) * 0.03;
            const fx = (dx / dist) * force;
            const fy = (dy / dist) * force;

            if (!n1.isDragging) {
              n1.vx += fx;
              n1.vy += fy;
            }
            if (!n2.isDragging) {
              n2.vx -= fx;
              n2.vy -= fy;
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
          ctx.strokeStyle = '#1F2A44';
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
          ctx.fillStyle = '#1F2A44';
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
          ctx.fillStyle = 'rgba(139, 46, 46, 0.25)';
          ctx.fill();
        }

        ctx.beginPath();
        ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
        ctx.fillStyle = color;
        ctx.fill();
        ctx.strokeStyle = '#0B1220';
        ctx.lineWidth = 2;
        ctx.stroke();

        // Node Label
        ctx.font = '10px "IBM Plex Mono", monospace';
        ctx.fillStyle = '#E8E6DE';
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
  }, [currentPkg, physicsActive, hopDistance]);

  if (!currentPkg) {
    return <div className="card">No network data available.</div>;
  }

  return (
    <div>
      {/* Network Header & Controls */}
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          marginBottom: '16px',
          flexWrap: 'wrap',
          gap: '12px',
        }}
      >
        <div>
          <h2 className="font-serif" style={{ fontSize: '1.4rem', color: 'var(--text)' }}>
            🕸️ Topological Subgraph Explorer
          </h2>
          <p style={{ fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Directed multi-hop transaction flow and broadcast IP geolocations
          </p>
        </div>

        <div style={{ display: 'flex', gap: '10px', alignItems: 'center' }}>
          <select
            className="search-input"
            value={currentPkg.wallet_id}
            onChange={(e) => onSelectWallet(e.target.value)}
            style={{ width: '280px', cursor: 'pointer' }}
          >
            {evidenceList.map((e) => (
              <option key={e.wallet_id} value={e.wallet_id}>
                {e.wallet_id.substring(0, 16)}... ({Number(e.final_risk_score).toFixed(1)})
              </option>
            ))}
          </select>

          <div style={{ display: 'flex', gap: '4px', backgroundColor: 'var(--surface-raised)', padding: '2px', borderRadius: '4px', border: '1px solid var(--border)' }}>
            {[1, 2, 3].map((h) => (
              <button
                key={h}
                className={`btn btn-sm ${hopDistance === h ? 'btn-accent' : ''}`}
                style={{ padding: '2px 8px', fontSize: '0.72rem' }}
                onClick={() => setHopDistance(h)}
              >
                {h} Hop{h > 1 ? 's' : ''}
              </button>
            ))}
          </div>

          <button
            className={`btn btn-sm ${physicsActive ? 'btn-accent' : ''}`}
            onClick={() => setPhysicsActive(!physicsActive)}
          >
            <RefreshCw size={13} /> {physicsActive ? 'Physics: On' : 'Physics: Frozen'}
          </button>
        </div>
      </div>

      {/* Main Canvas Container with Floating Overlay */}
      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '520px',
          backgroundColor: 'var(--surface)',
          border: '1px solid var(--border)',
          borderRadius: '8px',
          overflow: 'hidden',
          marginBottom: '16px',
        }}
      >
        <canvas ref={canvasRef} style={{ width: '100%', height: '100%', display: 'block', cursor: 'grab' }} />

        {/* Legend Overlay */}
        <div
          style={{
            position: 'absolute',
            bottom: '14px',
            left: '14px',
            backgroundColor: 'rgba(19, 27, 46, 0.9)',
            border: '1px solid var(--border)',
            borderRadius: '6px',
            padding: '10px 14px',
            fontSize: '0.75rem',
            fontFamily: 'IBM Plex Sans, sans-serif',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            flexDirection: 'column',
            gap: '6px',
          }}
        >
          <div style={{ fontWeight: 700, color: 'var(--text)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Node Taxonomy Legend
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#8B2E2E' }} />
            <span>Target Anomaly Wallet (Score: {Number(currentPkg.final_risk_score).toFixed(1)})</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#3182CE' }} />
            <span>Counterparty Wallets</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#A0AEC0' }} />
            <span>Transaction Intermediary Hubs</span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: '#B8562E' }} />
            <span>Broadcast IP Geolocation</span>
          </div>
        </div>

        {/* Selected Node Details Drawer */}
        {inspectedNode && (
          <div
            style={{
              position: 'absolute',
              top: '14px',
              right: '14px',
              backgroundColor: 'rgba(19, 27, 46, 0.92)',
              border: '1px solid var(--border)',
              borderRadius: '6px',
              padding: '12px 16px',
              maxWidth: '280px',
              backdropFilter: 'blur(4px)',
              fontSize: '0.78rem',
            }}
          >
            <div style={{ fontWeight: 600, color: 'var(--accent)', textTransform: 'uppercase', marginBottom: '4px' }}>
              Selected Graph Node
            </div>
            <div className="font-mono" style={{ color: 'var(--text)', wordBreak: 'break-all', marginBottom: '6px' }}>
              {inspectedNode.id}
            </div>
            <div style={{ color: 'var(--text-muted)' }}>
              Type: <strong style={{ color: 'var(--text)' }}>{inspectedNode.type}</strong>
            </div>
            {inspectedNode.country && (
              <div style={{ color: 'var(--text-muted)' }}>
                Jurisdiction: <strong style={{ color: 'var(--text)' }}>{inspectedNode.country}</strong>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
