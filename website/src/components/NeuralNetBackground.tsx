import { useEffect, useRef, type ReactElement } from 'react';
import { useColorMode } from '@docusaurus/theme-common';

// ── Network topology ──────────────────────────────────────────────────────────
const LAYERS_DESKTOP = [4, 7, 8, 8, 7, 1];
const LABELS_DESKTOP = ['INPUT', 'HIDDEN 1', 'HIDDEN 2', 'HIDDEN 3', 'HIDDEN 4', 'OUTPUT'];
const LAYERS_MOBILE  = [3, 4, 4, 1];
const LABELS_MOBILE  = ['INPUT', 'HIDDEN 1', 'HIDDEN 2', 'OUTPUT'];
const MAX_PARTICLES  = 100;
const SPAWN_INTERVAL = 180;
const SPEED_MIN      = 0.004;
const SPEED_MAX      = 0.009;
const TRAIL_LEN      = 14;

interface NodeT     { x: number; y: number; layer: number; activation: number; activatedAt: number }
interface EdgeT     { from: NodeT; to: NodeT; fromLayer: number; kind?: 'entry' | 'exit' | 'net' }
interface TrailPt   { x: number; y: number }
interface ParticleT { edge: EdgeT; progress: number; speed: number; alpha: number; trail: TrailPt[] }

export default function NeuralNetBackground(): ReactElement {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const { colorMode } = useColorMode();
  const dark = colorMode === 'dark';

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const C = dark
      ? {
          node:       '#c8a870',
          nodeAlpha:  0.45,
          edge:       'rgba(200,168,112,0.18)',
          edgeActive: 'rgba(200,168,112,0.55)',
          edgeIO:     'rgba(200,168,112,0.28)',
          particle:   '#c8a870',
          glow:       'rgba(200,168,112,0.22)',
          label:      'rgba(200,168,112,0.18)',
        }
      : {
          node:       '#8a6e30',
          nodeAlpha:  0.28,
          edge:       'rgba(138,110,48,0.12)',
          edgeActive: 'rgba(138,110,48,0.42)',
          edgeIO:     'rgba(138,110,48,0.22)',
          particle:   '#8a6e30',
          glow:       'rgba(138,110,48,0.14)',
          label:      'rgba(138,110,48,0.15)',
        };

    let nodes:         NodeT[][]    = [];
    let edges:         EdgeT[]      = [];
    let entryEdges:    EdgeT[]      = [];
    let exitEdge:      EdgeT | null = null;
    let particles:     ParticleT[]  = [];
    let animId:        number;
    let lastTime       = 0;
    let lastSpawn      = 0;
    let lastEntrySpawn = 0;
    let activeLabels   = LABELS_DESKTOP;

    const build = () => {
      const w        = canvas.width;
      const h        = canvas.height;
      const isMobile = w < 768;
      const layers   = isMobile ? LAYERS_MOBILE  : LAYERS_DESKTOP;
      activeLabels   = isMobile ? LABELS_MOBILE  : LABELS_DESKTOP;
      const padX     = w * (isMobile ? 0.06 : 0.07);
      const padY     = h * (isMobile ? 0.10 : 0.14);

      nodes = layers.map((count, li) =>
        Array.from({ length: count }, (_, ni) => ({
          x:           padX + (li / (layers.length - 1)) * (w - padX * 2),
          y:           count === 1 ? h / 2 : padY + (ni / (count - 1)) * (h - padY * 2),
          layer:       li,
          activation:  0,
          activatedAt: 0,
        }))
      );

      edges = [];
      for (let li = 0; li < layers.length - 1; li++)
        for (const from of nodes[li])
          for (const to of nodes[li + 1])
            edges.push({ from, to, fromLayer: li, kind: 'net' });

      entryEdges = nodes[0].map(n => ({
        from:      { x: -50, y: n.y, layer: -1, activation: 0, activatedAt: 0 },
        to:        n,
        fromLayer: -1,
        kind:      'entry' as const,
      }));

      const outNode = nodes[nodes.length - 1][0];
      exitEdge = {
        from:      outNode,
        to:        { x: w + 50, y: h / 2, layer: layers.length, activation: 0, activatedAt: 0 },
        fromLayer: layers.length - 1,
        kind:      'exit',
      };

      particles = [];
      for (let i = 0; i < 20; i++) spawnNet(Math.random());
      for (let i = 0; i < nodes[0].length; i++) spawnEntry(Math.random());
    };

    const spawnNet = (initProgress = 0, fromLayer = 0) => {
      if (particles.length >= MAX_PARTICLES) return;
      const pool = edges.filter(e => e.fromLayer === fromLayer);
      if (!pool.length) return;
      const edge = pool[Math.floor(Math.random() * pool.length)];
      particles.push({ edge, progress: initProgress, speed: SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN), alpha: 0.55 + Math.random() * 0.45, trail: [] });
    };

    const spawnEntry = (initProgress = 0) => {
      if (particles.length >= MAX_PARTICLES || !entryEdges.length) return;
      const edge = entryEdges[Math.floor(Math.random() * entryEdges.length)];
      particles.push({ edge, progress: initProgress, speed: SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN), alpha: 0.8 + Math.random() * 0.2, trail: [] });
    };

    const spawnExit = (a: number) => {
      if (!exitEdge || particles.length >= MAX_PARTICLES) return;
      particles.push({ edge: exitEdge, progress: 0, speed: SPEED_MIN * 1.2 + Math.random() * (SPEED_MAX - SPEED_MIN), alpha: a, trail: [] });
    };

    const resize = () => {
      canvas.width  = window.innerWidth;
      canvas.height = window.innerHeight;
      build();
    };
    resize();
    window.addEventListener('resize', resize);

    const drawArrow = (e: EdgeT, alpha: number, sz = 4) => {
      const dx = e.to.x - e.from.x, dy = e.to.y - e.from.y;
      const len = Math.sqrt(dx * dx + dy * dy);
      if (!len) return;
      const ux = dx / len, uy = dy / len;
      const tip = { x: e.to.x - ux * 5, y: e.to.y - uy * 5 };
      ctx.beginPath();
      ctx.moveTo(tip.x, tip.y);
      ctx.lineTo(tip.x - ux * sz + (-uy * sz), tip.y - uy * sz + (ux * sz));
      ctx.lineTo(tip.x - ux * sz - (-uy * sz), tip.y - uy * sz - (ux * sz));
      ctx.closePath();
      ctx.globalAlpha = alpha;
      ctx.fill();
      ctx.globalAlpha = 1;
    };

    const draw = (ts: number) => {
      const dt = Math.min(ts - lastTime, 50);
      lastTime = ts;
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Layer labels
      ctx.save();
      ctx.font      = `bold 9px 'JetBrains Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.fillStyle = C.label;
      nodes.forEach((layer, li) => ctx.fillText(activeLabels[li], layer[0].x, 26));
      ctx.restore();

      const activeEdges = new Set(particles.map(p => p.edge));

      // Entry dashed lines
      ctx.save();
      ctx.setLineDash([4, 6]);
      ctx.lineWidth = 0.8;
      for (const e of entryEdges) {
        const isActive = activeEdges.has(e);
        ctx.strokeStyle = isActive ? C.edgeActive : C.edgeIO;
        ctx.beginPath();
        ctx.moveTo(0, e.to.y);
        ctx.lineTo(e.to.x, e.to.y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle = isActive ? C.edgeActive : C.edgeIO;
        drawArrow(e, isActive ? 0.7 : 0.35, 4);
        ctx.setLineDash([4, 6]);
      }
      ctx.setLineDash([]);

      // Exit dashed line
      if (exitEdge) {
        const isActive = activeEdges.has(exitEdge);
        ctx.setLineDash([4, 6]);
        ctx.strokeStyle = isActive ? C.edgeActive : C.edgeIO;
        ctx.lineWidth   = 0.8;
        ctx.beginPath();
        ctx.moveTo(exitEdge.from.x, exitEdge.from.y);
        ctx.lineTo(canvas.width, exitEdge.from.y);
        ctx.stroke();
        ctx.setLineDash([]);
        ctx.fillStyle   = isActive ? C.edgeActive : C.edgeIO;
        const tip = { x: canvas.width - 5, y: exitEdge.from.y };
        ctx.beginPath();
        ctx.moveTo(tip.x + 4, tip.y);
        ctx.lineTo(tip.x - 4, tip.y - 4);
        ctx.lineTo(tip.x - 4, tip.y + 4);
        ctx.closePath();
        ctx.globalAlpha = isActive ? 0.7 : 0.35;
        ctx.fill();
        ctx.globalAlpha = 1;
      }
      ctx.restore();

      // Network edges
      ctx.save();
      ctx.lineWidth = 0.7;
      for (const e of edges) {
        const isActive = activeEdges.has(e);
        ctx.strokeStyle = isActive ? C.edgeActive : C.edge;
        ctx.beginPath();
        ctx.moveTo(e.from.x, e.from.y);
        ctx.lineTo(e.to.x,   e.to.y);
        ctx.stroke();
        ctx.fillStyle = isActive ? C.edgeActive : C.edge;
        drawArrow(e, isActive ? 0.7 : 0.35);
      }
      ctx.restore();

      // Spawn
      if (ts - lastSpawn > SPAWN_INTERVAL) { spawnNet(0, 0); lastSpawn = ts; }
      if (ts - lastEntrySpawn > SPAWN_INTERVAL * 0.75) { spawnEntry(0); lastEntrySpawn = ts; }

      // Particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        p.progress += p.speed * (dt / 16);

        const x = p.edge.from.x + (p.edge.to.x - p.edge.from.x) * p.progress;
        const y = p.edge.from.y + (p.edge.to.y - p.edge.from.y) * p.progress;

        p.trail.push({ x, y });
        if (p.trail.length > TRAIL_LEN) p.trail.shift();

        if (p.progress >= 1) {
          const dest = p.edge.to;
          if (p.edge.kind !== 'exit') {
            dest.activation  = 1;
            dest.activatedAt = ts;
          }
          if (p.edge.kind === 'entry') {
            spawnNet(0, 0);
          } else if (p.edge.kind !== 'exit') {
            if (dest.layer < activeLabels.length - 1) {
              const pool  = edges.filter(e => e.from === dest);
              const count = 1 + Math.floor(Math.random() * 2);
              for (let k = 0; k < count && particles.length < MAX_PARTICLES; k++) {
                const pick = pool[Math.floor(Math.random() * pool.length)];
                if (pick) particles.push({ edge: pick, progress: 0, speed: SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN), alpha: p.alpha * 0.82, trail: [] });
              }
            } else {
              spawnExit(p.alpha * 0.9);
            }
          }
          particles.splice(i, 1);
          continue;
        }

        // Trail
        p.trail.forEach((pt, ti) => {
          const ratio = ti / TRAIL_LEN;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 0.8 + ratio * 1.4, 0, Math.PI * 2);
          ctx.fillStyle   = C.particle;
          ctx.globalAlpha = ratio * p.alpha * 0.38;
          ctx.fill();
        });

        // Glow
        const gr = ctx.createRadialGradient(x, y, 0, x, y, 7);
        gr.addColorStop(0, C.particle);
        gr.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(x, y, 7, 0, Math.PI * 2);
        ctx.fillStyle   = gr;
        ctx.globalAlpha = p.alpha * 0.4;
        ctx.fill();

        // Core dot
        ctx.beginPath();
        ctx.arc(x, y, 2, 0, Math.PI * 2);
        ctx.fillStyle   = C.particle;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      // Nodes
      for (const layer of nodes) {
        for (const node of layer) {
          const age   = ts - node.activatedAt;
          const pulse = node.activation * Math.max(0, 1 - age / 900);
          if (age > 900) node.activation = 0;
          const r = 3.5 + pulse * 5;

          if (pulse > 0.04) {
            const glowR = 16 + pulse * 22;
            const gg = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, glowR);
            gg.addColorStop(0, C.glow);
            gg.addColorStop(1, 'transparent');
            ctx.beginPath();
            ctx.arc(node.x, node.y, glowR, 0, Math.PI * 2);
            ctx.fillStyle   = gg;
            ctx.globalAlpha = pulse * 0.9;
            ctx.fill();
            ctx.globalAlpha = 1;
          }

          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
          ctx.fillStyle   = C.node;
          ctx.globalAlpha = C.nodeAlpha + pulse * 0.65;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(node.x, node.y, r, 0, Math.PI * 2);
          ctx.strokeStyle = C.node;
          ctx.lineWidth   = 0.8;
          ctx.globalAlpha = 0.45 + pulse * 0.55;
          ctx.stroke();
          ctx.globalAlpha = 1;
        }
      }

      animId = requestAnimationFrame(draw);
    };

    animId = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener('resize', resize);
    };
  }, [dark]);

  return (
    <canvas
      ref={canvasRef}
      style={{
        position: 'fixed',
        inset: 0,
        zIndex: 0,
        pointerEvents: 'none',
        opacity: dark ? 0.55 : 0.18,
      }}
    />
  );
}
