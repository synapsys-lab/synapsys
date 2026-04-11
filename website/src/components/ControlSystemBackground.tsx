import { useEffect, useRef } from 'react';
import { useColorMode } from '@docusaurus/theme-common';

// ─────────────────────────────────────────────────────────────────────────────
//  ControlSystemDiagram
//  Animated closed-loop control system block diagram.
//  Fills the parent container (position: relative, any size).
//  Particles represent signals: r(t) → Σ → PID → G(s) → y(t) → feedback
// ─────────────────────────────────────────────────────────────────────────────

const TRAIL_LEN      = 16;
const MAX_PARTICLES  = 80;
const SPEED_MIN      = 0.0045;
const SPEED_MAX      = 0.010;

const LY = {
  yFwd:  0.42,
  yFB:   0.74,
  xRef:  0.01,
  xSig:  0.17,
  xCtrl: 0.36,
  xPlt:  0.57,
  xOut:  0.76,
  bw:    0.095,
  bh:    0.13,
};

interface TrailPt { x: number; y: number }
type SignalKind = 'ref' | 'err' | 'ctrl' | 'out' | 'fb';

interface Particle {
  pts:      { x: number; y: number }[];
  seg:      number;
  progress: number;
  speed:    number;
  alpha:    number;
  trail:    TrailPt[];
  kind:     SignalKind;
}

interface BlockRect {
  cx: number; cy: number;
  hw: number; hh: number;
  label: string;
  sub?: string;
}

interface SumJunction { cx: number; cy: number; r: number }

// ── palette ───────────────────────────────────────────────────────────────────
const DARK = {
  edgeLine:     'rgba(121,134,203,0.28)',
  edgeActive:   'rgba(128,222,234,0.70)',
  edgeFB:       'rgba(159,168,218,0.22)',
  edgeFBActive: 'rgba(159,168,218,0.65)',
  blockFill:    'rgba(92,107,192,0.14)',
  blockStroke:  'rgba(121,134,203,0.55)',
  blockLabel:   'rgba(179,188,230,0.90)',
  blockSub:     'rgba(128,222,234,0.60)',
  sigLabel:     'rgba(128,222,234,0.55)',
  partRef:      '#9fa8da',
  partCtrl:     '#80deea',
  partFB:       '#b39ddb',
  partOut:      '#80deea',
  glowRef:      'rgba(159,168,218,0.28)',
  glowCtrl:     'rgba(128,222,234,0.32)',
  glowFB:       'rgba(179,157,219,0.28)',
  sumFill:      'rgba(92,107,192,0.20)',
  sumStroke:    'rgba(121,134,203,0.65)',
  sumSign:      'rgba(200,210,255,0.80)',
};
const LIGHT = {
  edgeLine:     'rgba(92,107,192,0.22)',
  edgeActive:   'rgba(0,100,180,0.55)',
  edgeFB:       'rgba(92,107,192,0.18)',
  edgeFBActive: 'rgba(92,107,192,0.55)',
  blockFill:    'rgba(92,107,192,0.08)',
  blockStroke:  'rgba(92,107,192,0.42)',
  blockLabel:   'rgba(40,55,140,0.92)',
  blockSub:     'rgba(0,120,180,0.68)',
  sigLabel:     'rgba(0,100,160,0.58)',
  partRef:      '#3949ab',
  partCtrl:     '#0277bd',
  partFB:       '#6a3fbf',
  partOut:      '#0277bd',
  glowRef:      'rgba(57,73,171,0.20)',
  glowCtrl:     'rgba(2,119,189,0.20)',
  glowFB:       'rgba(106,63,191,0.20)',
  sumFill:      'rgba(92,107,192,0.12)',
  sumStroke:    'rgba(92,107,192,0.55)',
  sumSign:      'rgba(40,55,140,0.88)',
};

interface Props {
  className?: string;
  style?: React.CSSProperties;
}

export default function ControlSystemBackground({ className, style }: Props): JSX.Element {
  const { colorMode } = useColorMode();
  const dark = colorMode === 'dark';
  const canvasRef  = useRef<HTMLCanvasElement>(null);
  const wrapperRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas  = canvasRef.current;
    const wrapper = wrapperRef.current;
    if (!canvas || !wrapper) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    const C = dark ? DARK : LIGHT;

    let W = 0, H = 0;
    let blocks: BlockRect[] = [];
    let sigma:  SumJunction = { cx: 0, cy: 0, r: 0 };

    let wRefIn = {x:0,y:0}, wSig = {x:0,y:0};
    let wCtrlIn={x:0,y:0}, wCtrlOut={x:0,y:0};
    let wPltIn ={x:0,y:0}, wPltOut ={x:0,y:0};
    let wOut   ={x:0,y:0}, wRefEnd ={x:0,y:0};
    let wFBcorR={x:0,y:0}, wFBcorL={x:0,y:0}, wFBtop={x:0,y:0};

    let routeFwd: { x: number; y: number }[] = [];
    let routeFB:  { x: number; y: number }[] = [];

    const build = () => {
      W = canvas.width;
      H = canvas.height;
      const isMobile = W < 640;

      const yFwd = H * LY.yFwd;
      const yFB  = H * LY.yFB;
      const bw   = W * LY.bw;
      const bh   = H * LY.bh;
      const sr   = isMobile ? H * 0.048 : H * 0.058;

      wRefIn   = { x: 0,                y: yFwd };
      wSig     = { x: W * LY.xSig,      y: yFwd };
      wCtrlIn  = { x: W * LY.xCtrl - bw, y: yFwd };
      wCtrlOut = { x: W * LY.xCtrl + bw, y: yFwd };
      wPltIn   = { x: W * LY.xPlt  - bw, y: yFwd };
      wPltOut  = { x: W * LY.xPlt  + bw, y: yFwd };
      wOut     = { x: W * LY.xOut,      y: yFwd };
      wRefEnd  = { x: W,                 y: yFwd };
      wFBcorR  = { x: W * LY.xOut,      y: yFB  };
      wFBcorL  = { x: W * LY.xSig,      y: yFB  };
      wFBtop   = { x: W * LY.xSig,      y: yFwd };

      sigma = { cx: wSig.x, cy: wSig.y, r: sr };

      blocks = [
        { cx: W * LY.xCtrl, cy: yFwd, hw: bw, hh: bh,
          label: 'PID',  sub: isMobile ? '' : 'Controller' },
        { cx: W * LY.xPlt,  cy: yFwd, hw: bw, hh: bh,
          label: 'G(s)', sub: isMobile ? '' : 'Plant'      },
      ];

      routeFwd = [wRefIn, wSig, wCtrlIn, wCtrlOut, wPltIn, wPltOut, wOut, wRefEnd];
      routeFB  = [wOut, wFBcorR, wFBcorL, wFBtop];

      particles = particles.filter(p => p.seg < p.pts.length - 1);
    };

    // ── particles ─────────────────────────────────────────────────────────────
    let particles: Particle[] = [];

    const makeParticle = (
      route: typeof routeFwd, kind: SignalKind, initSeg = 0,
    ): Particle => ({
      pts: route, seg: initSeg, progress: 0,
      speed: SPEED_MIN + Math.random() * (SPEED_MAX - SPEED_MIN),
      alpha: 0.55 + Math.random() * 0.45,
      trail: [], kind,
    });

    const spawnFwd = (initSeg = 0) => {
      if (particles.length >= MAX_PARTICLES) return;
      particles.push(makeParticle(routeFwd, 'ref', initSeg));
    };
    const spawnFB = () => {
      if (particles.length >= MAX_PARTICLES) return;
      particles.push(makeParticle(routeFB, 'fb', 0));
    };

    const scatter = () => {
      for (let s = 0; s < routeFwd.length - 1; s++) {
        if (Math.random() > 0.45) spawnFwd(s);
      }
      for (let k = 0; k < 2; k++) spawnFB();
    };

    // ── resize (uses ResizeObserver on the wrapper div) ───────────────────────
    const syncSize = () => {
      const rect = wrapper.getBoundingClientRect();
      canvas.width  = rect.width  || wrapper.offsetWidth;
      canvas.height = rect.height || wrapper.offsetHeight;
      build();
      scatter();
    };

    const ro = new ResizeObserver(syncSize);
    ro.observe(wrapper);
    syncSize();

    // ── helpers ───────────────────────────────────────────────────────────────
    const drawArrow = (
      x: number, y: number, dx: number, dy: number,
      sz: number, color: string, alpha: number,
    ) => {
      const len = Math.sqrt(dx*dx + dy*dy);
      if (!len) return;
      const ux = dx/len, uy = dy/len;
      ctx.beginPath();
      ctx.moveTo(x, y);
      ctx.lineTo(x - ux*sz + (-uy)*(sz*0.5), y - uy*sz + ux*(sz*0.5));
      ctx.lineTo(x - ux*sz - (-uy)*(sz*0.5), y - uy*sz - ux*(sz*0.5));
      ctx.closePath();
      ctx.fillStyle   = color;
      ctx.globalAlpha = alpha;
      ctx.fill();
      ctx.globalAlpha = 1;
    };

    const kindColor = (k: SignalKind) =>
      k === 'fb' ? C.partFB : k === 'ctrl' ? C.partCtrl : C.partRef;
    const kindGlow  = (k: SignalKind) =>
      k === 'fb' ? C.glowFB : k === 'ctrl' ? C.glowCtrl : C.glowRef;
    const segKind   = (s: number): SignalKind =>
      s <= 1 ? 'ref' : s <= 3 ? 'err' : s <= 5 ? 'ctrl' : 'out';

    // ── animation loop ─────────────────────────────────────────────────────────
    let animId: number;
    let lastTime     = 0;
    let lastSpawnFwd = 0;
    let lastSpawnFB  = 0;
    const SPAWN_FWD  = 320;
    const SPAWN_FB   = 480;

    const draw = (ts: number) => {
      const dt = Math.min(ts - lastTime, 50);
      lastTime = ts;
      ctx.clearRect(0, 0, W, H);

      const activeFwdSegs = new Set<number>();
      const activeFBSegs  = new Set<number>();
      for (const p of particles) {
        if (p.pts === routeFwd) activeFwdSegs.add(p.seg);
        if (p.pts === routeFB)  activeFBSegs.add(p.seg);
      }

      // Forward path
      ctx.save();
      ctx.lineWidth = 1.4;
      for (let s = 0; s < routeFwd.length - 1; s++) {
        const a = routeFwd[s], b = routeFwd[s+1];
        const active = activeFwdSegs.has(s);
        ctx.setLineDash(s === 0 || s === routeFwd.length-2 ? [5, 7] : []);
        ctx.strokeStyle = active ? C.edgeActive : C.edgeLine;
        ctx.globalAlpha = 1;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        const mx = (a.x+b.x)/2, my = (a.y+b.y)/2;
        drawArrow(mx, my, b.x-a.x, b.y-a.y, 6,
          active ? C.edgeActive : C.edgeLine, active ? 0.85 : 0.40);
      }
      ctx.setLineDash([]);
      ctx.restore();

      // Signal labels
      const labelY = H * LY.yFwd - H * 0.060;
      const labels: [string, number][] = [
        ['r(t)', 0.09], ['e(t)', 0.27], ['u(t)', 0.47], ['y(t)', 0.68],
      ];
      ctx.save();
      ctx.font      = `italic 600 ${Math.max(11, H*0.024)}px 'JetBrains Mono', monospace`;
      ctx.textAlign = 'center';
      ctx.fillStyle = C.sigLabel;
      for (const [lbl, fx] of labels) {
        if (W < 600 && lbl !== 'r(t)' && lbl !== 'y(t)') continue;
        ctx.fillText(lbl, W*fx, labelY);
      }
      ctx.restore();

      // Feedback path
      ctx.save();
      ctx.lineWidth = 1.2;
      for (let s = 0; s < routeFB.length - 1; s++) {
        const a = routeFB[s], b = routeFB[s+1];
        const active = activeFBSegs.has(s);
        ctx.strokeStyle = active ? C.edgeFBActive : C.edgeFB;
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke();
        const mx = (a.x+b.x)/2, my = (a.y+b.y)/2;
        drawArrow(mx, my, b.x-a.x, b.y-a.y, 5,
          active ? C.edgeFBActive : C.edgeFB, active ? 0.78 : 0.35);
      }
      if (W >= 640) {
        ctx.font      = `italic 600 ${Math.max(10, H*0.022)}px 'JetBrains Mono', monospace`;
        ctx.textAlign = 'center';
        ctx.fillStyle = C.sigLabel;
        ctx.globalAlpha = 0.78;
        ctx.fillText('ŷ(t)', W*((LY.xSig+LY.xOut)/2), H*LY.yFB + H*0.046);
      }
      ctx.restore();

      // Blocks
      ctx.save();
      for (const b of blocks) {
        const x = b.cx - b.hw, y = b.cy - b.hh;
        const bw = b.hw*2, bh = b.hh*2;
        ctx.fillStyle   = C.blockFill;
        ctx.strokeStyle = C.blockStroke;
        ctx.lineWidth   = 1.5;
        ctx.beginPath();
        ctx.roundRect(x, y, bw, bh, 6);
        ctx.fill(); ctx.stroke();

        ctx.textAlign    = 'center';
        ctx.textBaseline = 'middle';
        const fs = Math.max(13, H*0.032);
        ctx.font      = `700 ${fs}px 'JetBrains Mono', monospace`;
        ctx.fillStyle = C.blockLabel;
        ctx.globalAlpha = 1;
        const off = b.sub ? H*0.018 : 0;
        ctx.fillText(b.label, b.cx, b.cy - off);
        if (b.sub) {
          ctx.font      = `400 ${Math.max(9, H*0.019)}px 'Inter', sans-serif`;
          ctx.fillStyle = C.blockSub;
          ctx.fillText(b.sub, b.cx, b.cy + H*0.032);
        }
      }
      ctx.restore();

      // Summing junction
      ctx.save();
      const { cx, cy, r } = sigma;
      ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI*2);
      ctx.fillStyle   = C.sumFill;
      ctx.strokeStyle = C.sumStroke;
      ctx.lineWidth   = 1.5;
      ctx.fill(); ctx.stroke();
      ctx.strokeStyle = C.sumStroke;
      ctx.lineWidth   = 1.2;
      ctx.beginPath();
      ctx.moveTo(cx - r*0.55, cy); ctx.lineTo(cx + r*0.55, cy);
      ctx.moveTo(cx, cy - r*0.55); ctx.lineTo(cx, cy + r*0.55);
      ctx.stroke();
      const ss = Math.max(9, r*0.55);
      ctx.font = `700 ${ss}px sans-serif`;
      ctx.textBaseline = 'middle'; ctx.textAlign = 'center';
      ctx.fillStyle = C.sumSign; ctx.globalAlpha = 0.9;
      ctx.fillText('+', cx - r*0.62, cy - r*0.30);
      ctx.fillText('−', cx - r*0.62, cy + r*0.42);
      if (W >= 640) {
        ctx.font = `italic ${Math.max(9, H*0.019)}px 'JetBrains Mono', monospace`;
        ctx.fillStyle = C.sigLabel; ctx.globalAlpha = 0.72;
        ctx.textAlign = 'center';
        ctx.fillText('Σ', cx, cy - r - H*0.042);
      }
      ctx.restore();

      // Spawn
      if (ts - lastSpawnFwd > SPAWN_FWD) { spawnFwd(0); lastSpawnFwd = ts; }
      if (ts - lastSpawnFB  > SPAWN_FB)  { spawnFB();   lastSpawnFB  = ts; }

      // Update & draw particles
      for (let i = particles.length - 1; i >= 0; i--) {
        const p = particles[i];
        if (p.pts === routeFwd) p.kind = segKind(p.seg);
        const a = p.pts[p.seg], b = p.pts[p.seg+1];
        if (!a || !b) { particles.splice(i, 1); continue; }

        p.progress += p.speed * (dt / 16);
        const x = a.x + (b.x - a.x) * p.progress;
        const y = a.y + (b.y - a.y) * p.progress;
        p.trail.push({ x, y });
        if (p.trail.length > TRAIL_LEN) p.trail.shift();

        if (p.progress >= 1) {
          p.seg++;
          p.progress = 0;
          if (p.seg >= p.pts.length - 1) { particles.splice(i, 1); continue; }
        }

        const col  = kindColor(p.kind);
        const glow = kindGlow(p.kind);

        p.trail.forEach((pt, ti) => {
          const ratio = ti / TRAIL_LEN;
          ctx.beginPath();
          ctx.arc(pt.x, pt.y, 0.7 + ratio*1.6, 0, Math.PI*2);
          ctx.fillStyle   = col;
          ctx.globalAlpha = ratio * p.alpha * 0.35;
          ctx.fill();
        });

        const gr = ctx.createRadialGradient(x, y, 0, x, y, 9);
        gr.addColorStop(0, glow); gr.addColorStop(1, 'transparent');
        ctx.beginPath(); ctx.arc(x, y, 9, 0, Math.PI*2);
        ctx.fillStyle   = gr;
        ctx.globalAlpha = p.alpha * 0.45;
        ctx.fill();

        ctx.beginPath(); ctx.arc(x, y, 2.2, 0, Math.PI*2);
        ctx.fillStyle   = col;
        ctx.globalAlpha = p.alpha;
        ctx.fill();
        ctx.globalAlpha = 1;
      }

      animId = requestAnimationFrame(draw);
    };

    animId = requestAnimationFrame(draw);
    return () => {
      cancelAnimationFrame(animId);
      ro.disconnect();
    };
  }, [dark]);

  return (
    <div
      ref={wrapperRef}
      className={className}
      style={{ position: 'relative', width: '100%', height: '100%', ...style }}
    >
      <canvas
        ref={canvasRef}
        style={{ position: 'absolute', inset: 0, width: '100%', height: '100%' }}
      />
    </div>
  );
}
