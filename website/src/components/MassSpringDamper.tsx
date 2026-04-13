import React, { useEffect, useRef, useState } from 'react';
import { useColorMode } from '@docusaurus/theme-common';
import { SIM_DT, SIM_N, SIM_X2_REF, SIM_U_MAX, SIM_X1, SIM_X2, SIM_U } from '@site/src/data/lqr_sim_data';

/**
 * 2-DOF Mass-Spring-Damper — Neural-LQR trajectory playback.
 * Data is pre-computed by scripts/gen_neural_lqr_anim.py and
 * exactly matches the dynamics shown in the documentation GIF.
 *
 * Layout (SVG units):
 *   wall ──[k,c]── m₁ ──[k,c]── m₂ ──→ F(t)
 *   x=14          x≈140         x≈290   setpoint at x≈290+50
 */

const W        = 500;
const H        = 150;
const MID_Y    = 75;
const M_SIZE   = 42;
const SCALE    = 48;          // pixels per metre
const REST1    = 140;         // m₁ SVG x at x₁=0
const REST2    = 290;         // m₂ SVG x at x₂=0
const REF_X    = REST2 + SIM_X2_REF * SCALE;  // setpoint line SVG x

type SpringProps = { x0: number; x1: number; y: number; n?: number; amp?: number };

function Spring({ x0, x1, y, n = 9, amp = 7 }: SpringProps) {
  const len   = x1 - x0;
  const step  = len / (n + 1);
  let d = `M ${x0} ${y}`;
  for (let i = 1; i <= n; i++) {
    const sx = x0 + i * step;
    const sy = y + (i % 2 === 0 ? -amp : amp);
    d += ` L ${sx} ${sy}`;
  }
  d += ` L ${x1} ${y}`;
  return <path d={d} fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />;
}

type DamperProps = { x0: number; x1: number; y: number };

function Damper({ x0, x1, y }: DamperProps) {
  const mid = (x0 + x1) / 2;
  const bw  = 14;
  const bh  = 18;
  return (
    <g stroke="currentColor" fill="none">
      <line x1={x0}      y1={y} x2={mid - bw} y2={y} strokeWidth="1.5" />
      <rect x={mid - bw} y={y - bh / 2} width={bw * 2} height={bh} strokeWidth="1.5" />
      <line x1={mid}     y1={y - bh / 2 - 3} x2={mid} y2={y + bh / 2 + 3} strokeWidth="3" strokeLinecap="round" />
      <line x1={mid + bw} y1={y} x2={x1} y2={y} strokeWidth="1.5" />
    </g>
  );
}

export default function MassSpringDamper() {
  const { colorMode } = useColorMode();
  const dark  = colorMode === 'dark';

  const frameRef  = useRef(0);
  const accumRef  = useRef(0);
  const lastTsRef = useRef<number | null>(null);
  const rafRef    = useRef<number | undefined>(undefined);
  const [frame, setFrame] = useState(0);

  useEffect(() => {
    const tick = (ts: number) => {
      if (lastTsRef.current === null) lastTsRef.current = ts;
      const delta = ts - lastTsRef.current;
      lastTsRef.current = ts;

      accumRef.current += delta;
      const dtMs = 10000 / SIM_N;   // 10 s loop — matches GIF (200 frames × 20 fps)
      const steps = Math.floor(accumRef.current / dtMs);
      if (steps > 0) {
        accumRef.current -= steps * dtMs;
        frameRef.current  = (frameRef.current + steps) % SIM_N;
        setFrame(frameRef.current);
      }
      rafRef.current = requestAnimationFrame(tick);
    };
    rafRef.current = requestAnimationFrame(tick);
    return () => { if (rafRef.current) cancelAnimationFrame(rafRef.current); };
  }, []);

  const replay = () => {
    frameRef.current  = 0;
    accumRef.current  = 0;
    lastTsRef.current = null;
    setFrame(0);
  };

  const i   = Math.min(frame, SIM_N - 1);
  const x1v = SIM_X1[i];
  const x2v = SIM_X2[i];
  const uv  = SIM_U[i];
  const t   = i * SIM_DT;

  const px1  = REST1 + x1v * SCALE;
  const px2  = REST2 + x2v * SCALE;

  // force arrow: show when |u| > 1 N, scale capped at 40px
  const fSign  = uv >= 0 ? 1 : -1;
  const fLen   = Math.abs(uv) / SIM_U_MAX * 40;
  const showF  = Math.abs(uv) > 1;

  // colours
  const col     = dark ? '#e2e8f0' : '#1e293b';
  const colDim  = dark ? '#64748b' : '#94a3b8';
  const colM    = dark ? '#1e40af' : '#2563eb';
  const colMF   = dark ? '#1e3a8a' : '#1d4ed8';
  const colRef  = dark ? '#4ade80' : '#16a34a';
  const colF    = dark ? '#fb923c' : '#ea580c';
  const colBg   = dark ? 'rgba(30,41,59,0.55)' : 'rgba(241,245,249,0.7)';

  return (
    <div className="msd-wrap" style={{ color: col }}>
      <svg
        width="100%"
        viewBox={`0 0 ${W} ${H}`}
        preserveAspectRatio="xMidYMid meet"
        style={{ display: 'block', overflow: 'visible' }}
      >
        {/* ── Wall ── */}
        <line x1={14} y1={MID_Y - 44} x2={14} y2={MID_Y + 44} stroke={col} strokeWidth="4" />
        {[-36, -20, -4, 12, 28, 44].map((dy, k) => (
          <line key={k} x1={0} y1={MID_Y + dy} x2={14} y2={MID_Y + dy - 12} stroke={colDim} strokeWidth="1" />
        ))}

        {/* ── Spring + damper wall→m₁ ── */}
        <g color={col} opacity={0.85}>
          <Spring x0={14} x1={px1 - M_SIZE / 2} y={MID_Y - 12} />
          <Damper x0={14} x1={px1 - M_SIZE / 2} y={MID_Y + 18} />
        </g>

        {/* ── Spring + damper m₁→m₂ ── */}
        <g color={col} opacity={0.85}>
          <Spring x0={px1 + M_SIZE / 2} x1={px2 - M_SIZE / 2} y={MID_Y - 12} />
          <Damper x0={px1 + M_SIZE / 2} x1={px2 - M_SIZE / 2} y={MID_Y + 18} />
        </g>

        {/* ── Setpoint dashed line ── */}
        <line
          x1={REF_X} y1={MID_Y - M_SIZE / 2 - 6}
          x2={REF_X} y2={MID_Y + M_SIZE / 2 + 6}
          stroke={colRef} strokeWidth="1.5" strokeDasharray="5,3" opacity={0.75}
        />
        <text x={REF_X} y={MID_Y - M_SIZE / 2 - 10}
              textAnchor="middle" fontSize={10} fill={colRef} fontFamily="monospace">
          r = {SIM_X2_REF} m
        </text>

        {/* ── m₁ ── */}
        <rect
          x={px1 - M_SIZE / 2} y={MID_Y - M_SIZE / 2}
          width={M_SIZE} height={M_SIZE} rx={5}
          fill={colM} stroke={colMF} strokeWidth="1.5" opacity={0.9}
        />
        <text x={px1} y={MID_Y + 5} textAnchor="middle" fontSize={13}
              fontWeight="bold" fill="#fff" fontFamily="sans-serif">m₁</text>

        {/* ── m₂ ── */}
        <rect
          x={px2 - M_SIZE / 2} y={MID_Y - M_SIZE / 2}
          width={M_SIZE} height={M_SIZE} rx={5}
          fill={colM} stroke={colMF} strokeWidth="1.5" opacity={0.9}
        />
        <text x={px2} y={MID_Y + 5} textAnchor="middle" fontSize={13}
              fontWeight="bold" fill="#fff" fontFamily="sans-serif">m₂</text>

        {/* ── Force arrow ── */}
        {showF && (
          <g>
            <defs>
              <marker id="msd-arr" markerWidth="8" markerHeight="8" refX="0" refY="3"
                      orientation="auto" markerUnits="strokeWidth">
                <path d="M0,0 L0,6 L8,3 z" fill={colF} />
              </marker>
            </defs>
            <line
              x1={px2 + (fSign > 0 ? M_SIZE / 2 : -M_SIZE / 2)}
              y1={MID_Y}
              x2={px2 + (fSign > 0 ? M_SIZE / 2 : -M_SIZE / 2) + fSign * fLen}
              y2={MID_Y}
              stroke={colF} strokeWidth="2.5" markerEnd="url(#msd-arr)"
            />
            <text
              x={px2 + (fSign > 0 ? M_SIZE / 2 + fLen + 6 : -M_SIZE / 2 - fLen - 6)}
              y={MID_Y - 6}
              textAnchor={fSign > 0 ? 'start' : 'end'}
              fontSize={10} fill={colF} fontFamily="monospace">
              F={uv.toFixed(1)}N
            </text>
          </g>
        )}

        {/* ── HUD ── */}
        <rect x={8} y={H - 28} width={160} height={22} rx={4}
              fill={colBg} />
        <text x={14} y={H - 13} fontSize={10} fill={col} fontFamily="monospace">
          t={t.toFixed(2)}s  x₂={x2v.toFixed(3)}m  Neural-LQR
        </text>
      </svg>

      <div className="msd-controls">
        <button onClick={replay} className="msd-btn msd-btn--secondary">↺ Replay</button>
      </div>
    </div>
  );
}
