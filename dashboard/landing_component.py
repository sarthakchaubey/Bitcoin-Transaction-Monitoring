"""Interactive JavaScript & TypeScript forensics command landing component."""

from __future__ import annotations

import json
from typing import Any

import streamlit as st
import streamlit.components.v1 as components

from dashboard.utils import DESIGN_TOKENS, compute_network_summary_stats


def render_interactive_landing(evidence_list: list[dict[str, Any]]) -> None:
    """Render a responsive, rich JavaScript/TypeScript cyber-forensics landing console."""
    if not evidence_list:
        st.info("No evidence records available to render interactive console.")
        return

    stats = compute_network_summary_stats(evidence_list)
    evidence_json = json.dumps(evidence_list, default=str)
    stats_json = json.dumps(stats, default=str)

    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Forensics Command Landing</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600;700&family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Serif+4:ital,opsz,wght@0,8..60,600;0,8..60,700;1,8..60,600&display=swap" rel="stylesheet">
        <style>
            :root {{
                --bg: {DESIGN_TOKENS['bg']};
                --surface: {DESIGN_TOKENS['surface']};
                --surface-raised: {DESIGN_TOKENS['surface_raised']};
                --border: {DESIGN_TOKENS['border']};
                --text: {DESIGN_TOKENS['text']};
                --text-muted: {DESIGN_TOKENS['text_muted']};
                --accent: {DESIGN_TOKENS['accent']};
                --accent-hover: {DESIGN_TOKENS['accent_hover']};
                --risk-low: {DESIGN_TOKENS['risk_low']};
                --risk-medium: {DESIGN_TOKENS['risk_medium']};
                --risk-high: {DESIGN_TOKENS['risk_high']};
                --risk-critical: {DESIGN_TOKENS['risk_critical']};
            }}

            * {{
                box-sizing: border-box;
                margin: 0;
                padding: 0;
            }}

            body {{
                background-color: var(--bg);
                color: var(--text);
                font-family: 'IBM Plex Sans', sans-serif;
                overflow-x: hidden;
                padding: 12px;
            }}

            /* Canvas Background */
            #canvas-container {{
                position: relative;
                width: 100%;
                height: 240px;
                border: 1px solid var(--border);
                border-radius: 8px;
                background: radial-gradient(circle at 50% 50%, #152238 0%, var(--bg) 100%);
                overflow: hidden;
                margin-bottom: 18px;
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
            }}

            #network-canvas {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                display: block;
            }}

            .canvas-overlay {{
                position: absolute;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                pointer-events: none;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
                padding: 16px 20px;
                background: linear-gradient(180deg, rgba(11, 18, 32, 0.4) 0%, rgba(11, 18, 32, 0.8) 100%);
            }}

            .hud-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}

            .hud-title {{
                font-family: 'Source Serif 4', Georgia, serif;
                font-size: 1.4rem;
                font-weight: 700;
                color: var(--text);
                letter-spacing: -0.01em;
            }}

            .hud-status-badge {{
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background-color: rgba(19, 27, 46, 0.85);
                border: 1px solid var(--border);
                padding: 4px 10px;
                border-radius: 4px;
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.78rem;
                color: #68D391;
            }}

            .status-dot {{
                width: 7px;
                height: 7px;
                background-color: #48BB78;
                border-radius: 50%;
                box-shadow: 0 0 8px #48BB78;
                animation: pulse 2s infinite;
            }}

            @keyframes pulse {{
                0% {{ opacity: 0.4; }}
                50% {{ opacity: 1; }}
                100% {{ opacity: 0.4; }}
            }}

            .hud-ticker {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.75rem;
                color: var(--text-muted);
                display: flex;
                gap: 20px;
                border-top: 1px solid rgba(31, 42, 68, 0.6);
                padding-top: 8px;
            }}

            .ticker-item span {{
                color: var(--accent);
                font-weight: 600;
            }}

            /* Gauges & Summary Cards Grid */
            .stats-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 12px;
                margin-bottom: 20px;
            }}

            .stat-card {{
                background-color: var(--surface);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 14px 16px;
                position: relative;
                overflow: hidden;
                transition: transform 0.2s ease, border-color 0.2s ease;
            }}

            .stat-card:hover {{
                transform: translateY(-2px);
                border-color: var(--accent);
            }}

            .stat-card::before {{
                content: '';
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                height: 3px;
                background: var(--card-accent, var(--accent));
            }}

            .stat-label {{
                font-size: 0.75rem;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                color: var(--text-muted);
                margin-bottom: 6px;
            }}

            .stat-value {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 1.6rem;
                font-weight: 700;
                color: var(--text);
                line-height: 1.1;
            }}

            .stat-sub {{
                font-size: 0.75rem;
                color: var(--text-muted);
                margin-top: 4px;
            }}

            /* Quick Triage Section */
            .section-header {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 12px;
                padding-bottom: 6px;
                border-bottom: 1px solid var(--border);
            }}

            .section-title {{
                font-family: 'Source Serif 4', Georgia, serif;
                font-size: 1.15rem;
                color: var(--text);
            }}

            .search-box {{
                background-color: var(--surface);
                border: 1px solid var(--border);
                color: var(--text);
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.85rem;
                padding: 6px 12px;
                border-radius: 4px;
                width: 260px;
                outline: none;
                transition: border-color 0.2s ease;
            }}

            .search-box:focus {{
                border-color: var(--accent);
            }}

            /* Triage Cards List */
            .triage-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
                gap: 12px;
            }}

            .triage-card {{
                background-color: var(--surface);
                border: 1px solid var(--border);
                border-radius: 6px;
                padding: 14px;
                cursor: pointer;
                transition: all 0.2s ease;
                display: flex;
                flex-direction: column;
                justify-content: space-between;
            }}

            .triage-card:hover {{
                background-color: var(--surface-raised);
                border-color: var(--accent);
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
            }}

            .card-top {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                margin-bottom: 8px;
            }}

            .wallet-addr {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.88rem;
                font-weight: 600;
                color: var(--text);
                word-break: break-all;
            }}

            .risk-pill {{
                font-family: 'IBM Plex Mono', monospace;
                font-size: 0.75rem;
                font-weight: 700;
                padding: 2px 8px;
                border-radius: 3px;
                white-space: nowrap;
            }}

            .pill-critical {{
                background-color: rgba(139, 46, 46, 0.25);
                color: #FC8181;
                border: 1px solid var(--risk-critical);
            }}

            .pill-high {{
                background-color: rgba(184, 86, 46, 0.25);
                color: #F6AD55;
                border: 1px solid var(--risk-high);
            }}

            .pill-medium {{
                background-color: rgba(200, 151, 59, 0.25);
                color: #F6E05E;
                border: 1px solid var(--risk-medium);
            }}

            .pill-low {{
                background-color: rgba(91, 122, 107, 0.25);
                color: #9AE6B4;
                border: 1px solid var(--risk-low);
            }}

            .card-finding {{
                font-size: 0.82rem;
                color: var(--text-muted);
                line-height: 1.4;
                margin: 8px 0;
                display: -webkit-box;
                -webkit-line-clamp: 2;
                -webkit-box-orient: vertical;
                overflow: hidden;
            }}

            .shap-bars {{
                display: flex;
                flex-direction: column;
                gap: 4px;
                margin-top: 8px;
                border-top: 1px solid rgba(31, 42, 68, 0.6);
                padding-top: 8px;
            }}

            .shap-bar-row {{
                display: flex;
                align-items: center;
                gap: 8px;
                font-size: 0.75rem;
                font-family: 'IBM Plex Mono', monospace;
            }}

            .shap-name {{
                width: 120px;
                overflow: hidden;
                text-overflow: ellipsis;
                white-space: nowrap;
                color: var(--text-muted);
            }}

            .shap-bar-track {{
                flex: 1;
                height: 5px;
                background-color: var(--surface-raised);
                border-radius: 2px;
                overflow: hidden;
            }}

            .shap-bar-fill {{
                height: 100%;
                border-radius: 2px;
            }}

            .card-footer {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 10px;
                padding-top: 8px;
                border-top: 1px solid var(--border);
                font-size: 0.75rem;
                color: var(--text-muted);
            }}

            .inspect-btn {{
                background-color: var(--surface-raised);
                border: 1px solid var(--border);
                color: var(--accent);
                font-family: 'IBM Plex Sans', sans-serif;
                font-size: 0.75rem;
                font-weight: 600;
                padding: 3px 10px;
                border-radius: 3px;
                cursor: pointer;
            }}

            .inspect-btn:hover {{
                background-color: var(--accent);
                color: var(--bg);
            }}

            /* Case Modal */
            .modal-backdrop {{
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background-color: rgba(11, 18, 32, 0.85);
                backdrop-filter: blur(4px);
                display: none;
                justify-content: center;
                align-items: center;
                z-index: 1000;
                padding: 16px;
            }}

            .modal-content {{
                background-color: var(--surface);
                border: 1px solid var(--border);
                border-radius: 8px;
                width: 100%;
                max-width: 600px;
                max-height: 90vh;
                overflow-y: auto;
                padding: 20px;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.8);
            }}

            .modal-header {{
                display: flex;
                justify-content: space-between;
                align-items: flex-start;
                border-bottom: 1px solid var(--border);
                padding-bottom: 12px;
                margin-bottom: 14px;
            }}

            .modal-close {{
                background: none;
                border: none;
                color: var(--text-muted);
                font-size: 1.4rem;
                cursor: pointer;
            }}

            .modal-close:hover {{
                color: var(--text);
            }}
        </style>
    </head>
    <body>

        <!-- Canvas Animated Network Background & HUD -->
        <div id="canvas-container">
            <canvas id="network-canvas"></canvas>
            <div class="canvas-overlay">
                <div class="hud-header">
                    <div class="hud-title">🛡️ Bitcoin Forensics Live HUD</div>
                    <div class="hud-status-badge">
                        <div class="status-dot"></div>
                        TELEMETRY ACTIVE
                    </div>
                </div>
                <div class="hud-ticker">
                    <div class="ticker-item">ANOMALY ENGINE: <span>ONLINE</span></div>
                    <div class="ticker-item">LOUVAIN CLUSTERING: <span>SYNCED</span></div>
                    <div class="ticker-item">EXPLAINABILITY: <span>SHAP v0.42</span></div>
                    <div class="ticker-item">MEMPOOL FEED: <span>OFFLINE FORENSICS</span></div>
                </div>
            </div>
        </div>

        <!-- Headline Metric Gauges -->
        <div class="stats-grid" id="stats-container">
            <!-- Populated dynamically by TypeScript/JavaScript -->
        </div>

        <!-- Quick Triage Terminal -->
        <div class="section-header">
            <div class="section-title">⚡ High-Risk Entity Triage Stream</div>
            <input type="text" id="wallet-search" class="search-box" placeholder="Search address or pattern...">
        </div>

        <div class="triage-grid" id="triage-container">
            <!-- Populated dynamically -->
        </div>

        <!-- Modal Inspection Window -->
        <div class="modal-backdrop" id="case-modal">
            <div class="modal-content">
                <div class="modal-header">
                    <div>
                        <div style="font-size: 0.72rem; color: var(--text-muted); text-transform: uppercase;">Entity Forensic Dossier</div>
                        <h3 id="modal-wallet-id" style="font-family: 'IBM Plex Mono', monospace; font-size: 1.05rem; word-break: break-all; margin-top: 4px;"></h3>
                    </div>
                    <button class="modal-close" onclick="closeModal()">&times;</button>
                </div>
                <div id="modal-body"></div>
            </div>
        </div>

        <script>
            // --- DATA INJECTION ---
            const evidenceData = {evidence_json};
            const networkStats = {stats_json};

            // --- 1. CANVAS PARTICLE GRAPH ANIMATION (TypeScript-style logic) ---
            const canvas = document.getElementById('network-canvas');
            const ctx = canvas.getContext('2d');

            function resizeCanvas() {{
                canvas.width = canvas.parentElement.clientWidth;
                canvas.height = canvas.parentElement.clientHeight;
            }}
            window.addEventListener('resize', resizeCanvas);
            resizeCanvas();

            // Particle nodes representing transaction hubs and broadcast endpoints
            const nodes = [];
            const nodeTypes = ['wallet', 'tx', 'ip', 'target'];
            const colors = {{
                wallet: '#3182CE',
                tx: '#94A3B8',
                ip: '#B8562E',
                target: '#8B2E2E'
            }};

            for (let i = 0; i < 35; i++) {{
                nodes.push({{
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    vx: (Math.random() - 0.5) * 0.6,
                    vy: (Math.random() - 0.5) * 0.6,
                    radius: Math.random() * 3 + 2,
                    type: nodeTypes[Math.floor(Math.random() * nodeTypes.length)],
                }});
            }}

            let mouseX = -1000;
            let mouseY = -1000;

            canvas.addEventListener('mousemove', (e) => {{
                const rect = canvas.getBoundingClientRect();
                mouseX = e.clientX - rect.left;
                mouseY = e.clientY - rect.top;
            }});

            canvas.addEventListener('mouseleave', () => {{
                mouseX = -1000;
                mouseY = -1000;
            }});

            function animate() {{
                ctx.clearRect(0, 0, canvas.width, canvas.height);

                // Update & draw nodes
                for (let i = 0; i < nodes.length; i++) {{
                    const n = nodes[i];
                    n.x += n.vx;
                    n.y += n.vy;

                    if (n.x < 0 || n.x > canvas.width) n.vx *= -1;
                    if (n.y < 0 || n.y > canvas.height) n.vy *= -1;

                    // Mouse gentle repulsion
                    const dx = n.x - mouseX;
                    const dy = n.y - mouseY;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 80) {{
                        n.x += (dx / dist) * 1.5;
                        n.y += (dy / dist) * 1.5;
                    }}

                    ctx.beginPath();
                    ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
                    ctx.fillStyle = colors[n.type];
                    ctx.fill();

                    // Connect nearby nodes
                    for (let j = i + 1; j < nodes.length; j++) {{
                        const n2 = nodes[j];
                        const d = Math.hypot(n.x - n2.x, n.y - n2.y);
                        if (d < 110) {{
                            ctx.beginPath();
                            ctx.moveTo(n.x, n.y);
                            ctx.lineTo(n2.x, n2.y);
                            ctx.strokeStyle = `rgba(31, 42, 68, ${{1 - d / 110}})`;
                            ctx.lineWidth = 0.8;
                            ctx.stroke();
                        }}
                    }}
                }}
                requestAnimationFrame(animate);
            }}
            animate();

            // --- 2. RENDER SUMMARY STAT CARDS ---
            function renderStats() {{
                const container = document.getElementById('stats-container');
                const cards = [
                    {{
                        label: 'Monitored Entities',
                        val: networkStats.total_wallets || 0,
                        sub: 'Cluster-aggregated',
                        color: '{DESIGN_TOKENS['accent']}'
                    }},
                    {{
                        label: 'Mean Network Risk',
                        val: (networkStats.avg_risk_score || 0).toFixed(1) + ' / 100',
                        sub: 'Composite ensemble score',
                        color: '{DESIGN_TOKENS['accent']}'
                    }},
                    {{
                        label: 'Critical / High Alerts',
                        val: ((networkStats.critical_count || 0) + (networkStats.high_count || 0)),
                        sub: 'Requires triage priority',
                        color: '{DESIGN_TOKENS['risk_critical']}'
                    }},
                    {{
                        label: 'Flagged Volume (BTC)',
                        val: (networkStats.total_flagged_volume_btc || 0).toFixed(2) + ' ₿',
                        sub: 'Ingress subgraph value',
                        color: '{DESIGN_TOKENS['risk_high']}'
                    }}
                ];

                container.innerHTML = cards.map(c => `
                    <div class="stat-card" style="--card-accent: ${{c.color}}">
                        <div class="stat-label">${{c.label}}</div>
                        <div class="stat-value">${{c.val}}</div>
                        <div class="stat-sub">${{c.sub}}</div>
                    </div>
                `).join('');
            }}
            renderStats();

            // --- 3. RENDER TRIAGE CARDS & SEARCH ---
            function getPillClass(score) {{
                if (score >= 90) return 'pill-critical';
                if (score >= 70) return 'pill-high';
                if (score >= 40) return 'pill-medium';
                return 'pill-low';
            }}

            function renderTriageGrid(items) {{
                const container = document.getElementById('triage-container');
                if (!items || items.length === 0) {{
                    container.innerHTML = '<div style="color: var(--text-muted); padding: 20px;">No matching entities found.</div>';
                    return;
                }}

                container.innerHTML = items.map(item => {{
                    const score = parseFloat(item.final_risk_score || 0);
                    const pillClass = getPillClass(score);
                    const shaps = (item.shap_explanation || []).slice(0, 2);

                    const shapRows = shaps.map(s => {{
                        const val = Math.abs(parseFloat(s.shap_value || 0));
                        const pct = Math.min(100, Math.round(val * 200));
                        const isRisk = s.direction === 'increases_risk' || parseFloat(s.shap_value) > 0;
                        const fillColor = isRisk ? '{DESIGN_TOKENS['risk_high']}' : '{DESIGN_TOKENS['risk_low']}';
                        return `
                            <div class="shap-bar-row">
                                <div class="shap-name" title="${{s.feature}}">${{s.feature}}</div>
                                <div class="shap-bar-track">
                                    <div class="shap-bar-fill" style="width: ${{pct}}%; background-color: ${{fillColor}};"></div>
                                </div>
                                <div style="color: var(--text);">${{parseFloat(s.shap_value || 0).toFixed(2)}}</div>
                            </div>
                        `;
                    }}).join('');

                    return `
                        <div class="triage-card" onclick="openModal('${{item.wallet_id}}')">
                            <div>
                                <div class="card-top">
                                    <div class="wallet-addr">${{item.wallet_id.substring(0, 16)}}...</div>
                                    <div class="risk-pill ${{pillClass}}">${{score.toFixed(1)}} / 100</div>
                                </div>
                                <div style="font-size: 0.72rem; color: var(--accent); font-family: 'IBM Plex Mono', monospace;">
                                    🏷️ ${{item.pattern_hint || 'unknown'}}
                                </div>
                                <div class="card-finding">${{item.reason_sentence || 'Anomalous network activity detected.'}}</div>
                                <div class="shap-bars">
                                    ${{shapRows}}
                                </div>
                            </div>
                            <div class="card-footer">
                                <div>Confidence: <strong style="color: var(--text);">${{item.confidence_label || 'Normal'}}</strong></div>
                                <button class="inspect-btn">Inspect Dossier →</button>
                            </div>
                        </div>
                    `;
                }}).join('');
            }}
            renderTriageGrid(evidenceData);

            // Live Search Filter
            document.getElementById('wallet-search').addEventListener('input', (e) => {{
                const q = e.target.value.toLowerCase().trim();
                const filtered = evidenceData.filter(item => 
                    (item.wallet_id && item.wallet_id.toLowerCase().includes(q)) ||
                    (item.pattern_hint && item.pattern_hint.toLowerCase().includes(q)) ||
                    (item.reason_sentence && item.reason_sentence.toLowerCase().includes(q))
                );
                renderTriageGrid(filtered);
            }});

            // --- 4. MODAL DIALOG ---
            function openModal(walletId) {{
                const item = evidenceData.find(e => e.wallet_id === walletId);
                if (!item) return;

                document.getElementById('modal-wallet-id').innerText = item.wallet_id;
                const score = parseFloat(item.final_risk_score || 0);
                const pillClass = getPillClass(score);

                const shapList = (item.shap_explanation || []).map(s => `
                    <div style="display: flex; justify-content: space-between; padding: 4px 0; border-bottom: 1px solid var(--border); font-family: 'IBM Plex Mono', monospace; font-size: 0.8rem;">
                        <span style="color: var(--text-muted);">${{s.feature}}</span>
                        <span style="color: ${{s.direction === 'increases_risk' ? '{DESIGN_TOKENS['risk_high']}' : '{DESIGN_TOKENS['risk_low']}'}};">${{parseFloat(s.shap_value || 0).toFixed(4)}} (raw: ${{s.raw_value}})</span>
                    </div>
                `).join('');

                document.getElementById('modal-body').innerHTML = `
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="risk-pill ${{pillClass}}" style="font-size: 0.9rem;">SCORE: ${{score.toFixed(1)}} / 100</span>
                        <span style="color: var(--accent); font-family: 'IBM Plex Mono', monospace; font-size: 0.85rem;">Pattern: ${{item.pattern_hint}}</span>
                    </div>
                    <div style="background-color: var(--surface-raised); border-left: 3px solid var(--accent); padding: 12px; margin-bottom: 16px; border-radius: 4px; font-size: 0.92rem; line-height: 1.5;">
                        ${{item.reason_sentence}}
                    </div>
                    <div style="font-weight: 600; font-size: 0.85rem; text-transform: uppercase; color: var(--text-muted); margin-bottom: 8px;">Top Model Explanations (SHAP)</div>
                    <div style="margin-bottom: 16px;">${{shapList}}</div>
                    <div style="display: flex; gap: 8px;">
                        <button onclick="copyWallet('${{item.wallet_id}}')" class="inspect-btn" style="flex: 1; padding: 8px;">📋 Copy Wallet ID</button>
                    </div>
                `;

                document.getElementById('case-modal').style.display = 'flex';
            }}

            function closeModal() {{
                document.getElementById('case-modal').style.display = 'none';
            }}

            function copyWallet(addr) {{
                navigator.clipboard.writeText(addr);
                alert('Wallet address copied to clipboard: ' + addr);
            }}

            // Close on click outside
            document.getElementById('case-modal').addEventListener('click', (e) => {{
                if (e.target.id === 'case-modal') closeModal();
            }});
        </script>
    </body>
    </html>
    """

    components.html(html_code, height=880, scrolling=True)
