"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

export type PresetKey = "jellyfish" | "betta";
export type AmbientMode = "both" | "stars" | "rain" | "off";

interface Palette {
  name: string;
  primary: [number, number, number];
  secondary: [number, number, number];
  accent: [number, number, number];
}

const PALETTES: Palette[] = [
  { name: "Ocean Cyan", primary: [35, 130, 255], secondary: [0, 240, 220], accent: [190, 245, 255] },
  { name: "Neon Magma", primary: [220, 45, 185], secondary: [110, 50, 255], accent: [255, 190, 240] },
  { name: "Bio Emerald", primary: [20, 215, 120], secondary: [170, 250, 60], accent: [220, 255, 190] },
  { name: "Solar Gold", primary: [255, 70, 55], secondary: [255, 195, 35], accent: [255, 245, 190] },
  { name: "Royal Abyss", primary: [95, 75, 255], secondary: [255, 135, 50], accent: [225, 220, 255] },
  { name: "Violet Lotus", primary: [165, 65, 250], secondary: [55, 220, 255], accent: [255, 210, 250] },
];

interface Spark {
  x: number;
  y: number;
  z: number;
  vx: number;
  vy: number;
  vz: number;
  age: number;
  life: number;
  color: [number, number, number];
  cx: number;
  cy: number;
}

interface GlintRing {
  t0: number;
  x0: number;
  y0: number;
  r0: number;
  seed: number;
  cx: number;
  cy: number;
}

interface RainDrop {
  x: number;
  y: number;
  speed: number;
  len: number;
  layer: number;
}

interface RainSplash {
  x: number;
  y: number;
  age: number;
}

interface DriftingStar {
  x: number;
  y: number;
  vx: number;
  vy: number;
  layer: number;
  twinklePhase: number;
}

interface ShootingStar {
  x: number;
  y: number;
  vx: number;
  vy: number;
  len: number;
  age: number;
  maxLife: number;
}

interface AgentConfig {
  id: number;
  scaleMul: number;
  phase: number;
  freqX: number;
  freqY: number;
  ampX: number;
  ampY: number;
  centerBiasX: number;
  centerBiasY: number;
  palOffset: number;
  zOffset: number;
}

// 5 independent 3D creatures spread across the screen with distinct depths and trajectories
const AGENTS: AgentConfig[] = [
  { id: 0, scaleMul: 0.90, phase: 0.0, freqX: 0.34, freqY: 0.46, ampX: 0.30, ampY: 0.24, centerBiasX: 0.50, centerBiasY: 0.48, palOffset: 0, zOffset: 0.00 },
  { id: 1, scaleMul: 0.74, phase: 1.4, freqX: 0.29, freqY: 0.41, ampX: 0.26, ampY: 0.25, centerBiasX: 0.22, centerBiasY: 0.30, palOffset: 1, zOffset: 0.25 },
  { id: 2, scaleMul: 0.68, phase: 2.8, freqX: 0.38, freqY: 0.33, ampX: 0.27, ampY: 0.24, centerBiasX: 0.78, centerBiasY: 0.32, palOffset: 2, zOffset: 0.45 },
  { id: 3, scaleMul: 0.62, phase: 4.2, freqX: 0.31, freqY: 0.49, ampX: 0.28, ampY: 0.22, centerBiasX: 0.24, centerBiasY: 0.72, palOffset: 3, zOffset: 0.65 },
  { id: 4, scaleMul: 0.56, phase: 5.5, freqX: 0.42, freqY: 0.36, ampX: 0.26, ampY: 0.23, centerBiasX: 0.76, centerBiasY: 0.70, palOffset: 4, zOffset: 0.85 },
];

const clamp = (v: number, lo: number, hi: number) => (v < lo ? lo : v > hi ? hi : v);
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;

export default function GlobalAsciiBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const pathname = usePathname();

  const [preset, setPreset] = useState<PresetKey>("jellyfish");
  const [ambient, setAmbient] = useState<AmbientMode>("both");
  const [autoRoute, setAutoRoute] = useState<boolean>(true);
  const [paletteIdx, setPaletteIdx] = useState<number>(0);

  const stateRef = useRef({
    preset: "jellyfish" as PresetKey,
    ambient: "both" as AmbientMode,
    paletteIdx: 0,
    mouseX: 0,
    mouseY: 0,
    burstRequest: false,
  });

  useEffect(() => {
    stateRef.current.preset = preset;
  }, [preset]);

  useEffect(() => {
    stateRef.current.ambient = ambient;
  }, [ambient]);

  useEffect(() => {
    stateRef.current.paletteIdx = paletteIdx;
  }, [paletteIdx]);

  useEffect(() => {
    if (!autoRoute) return;
    if (pathname?.includes("/login") || pathname?.includes("/register") || pathname?.includes("/search")) {
      setPreset("jellyfish");
    } else {
      setPreset("betta");
    }
  }, [pathname, autoRoute]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d", { alpha: false });
    if (!ctx) return;

    const CELL_W = 8;
    const CELL_H = 14;
    let cols = 0;
    let rows = 0;
    let zBuffer = new Float32Array(0);
    let charBuffer: string[] = [];
    let colorBuffer: string[] = [];

    const rainDrops: RainDrop[] = [];
    const rainSplashes: RainSplash[] = [];
    const driftingStars: DriftingStar[] = [];
    const shootingStars: ShootingStar[] = [];

    const initAmbientParticles = () => {
      rainDrops.length = 0;
      driftingStars.length = 0;

      const dropCount = Math.min(150, Math.floor((cols * rows) / 42));
      for (let i = 0; i < dropCount; i++) {
        const layer = i % 3;
        rainDrops.push({
          x: Math.random() * cols,
          y: Math.random() * rows,
          speed: 15 + layer * 9 + Math.random() * 6,
          len: 3 + layer * 2 + Math.floor(Math.random() * 3),
          layer,
        });
      }

      const starCount = Math.min(130, Math.floor((cols * rows) / 48));
      for (let i = 0; i < starCount; i++) {
        const layer = i % 3;
        driftingStars.push({
          x: Math.random() * cols,
          y: Math.random() * rows,
          vx: -(1.3 + layer * 1.6 + Math.random() * 0.8),
          vy: 0.25 + layer * 0.2,
          layer,
          twinklePhase: Math.random() * Math.PI * 2,
        });
      }
    };

    const resize = () => {
      canvas.width = window.innerWidth;
      canvas.height = window.innerHeight;
      cols = Math.max(1, Math.floor(canvas.width / CELL_W));
      rows = Math.max(1, Math.floor(canvas.height / CELL_H));
      zBuffer = new Float32Array(cols * rows);
      charBuffer = new Array(cols * rows);
      colorBuffer = new Array(cols * rows);
      initAmbientParticles();
    };
    resize();
    window.addEventListener("resize", resize);

    const onMove = (e: MouseEvent) => {
      stateRef.current.mouseX = (e.clientX / Math.max(1, window.innerWidth) - 0.5) * 2;
      stateRef.current.mouseY = (e.clientY / Math.max(1, window.innerHeight) - 0.5) * 2;
    };
    const onDown = () => {
      stateRef.current.burstRequest = true;
      setPaletteIdx((p) => (p + 1) % PALETTES.length);
    };
    window.addEventListener("mousemove", onMove);
    window.addEventListener("mousedown", onDown);

    const GOLDEN_ANGLE = Math.PI * (3 - Math.sqrt(5));
    const bettaBodySamples: { u: number; th: number }[] = [];
    for (let i = 0; i < 460; i++) {
      bettaBodySamples.push({
        u: i / 460,
        th: (i * GOLDEN_ANGLE) % (Math.PI * 2),
      });
    }

    const sparks: Spark[] = [];
    const glints: GlintRing[] = [];
    let lastPulseIdx = -1;
    let lastGlintTime = 0;
    let lastMeteorTime = 0;

    const spawnBurst = (cx: number, cy: number, pal: Palette) => {
      for (let i = 0; i < 24; i++) {
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos(2 * Math.random() - 1);
        const speed = 0.45 + Math.random() * 0.95;
        sparks.push({
          x: 0,
          y: -0.1,
          z: 0,
          vx: Math.sin(phi) * Math.cos(theta) * speed,
          vy: Math.cos(phi) * speed - 0.15,
          vz: Math.sin(phi) * Math.sin(theta) * speed,
          age: 0,
          life: 1.3 + Math.random() * 1.1,
          color: i % 2 === 0 ? pal.accent : pal.secondary,
          cx,
          cy,
        });
      }
    };

    const computeLitRGB = (
      way: number,
      lum: number,
      t: number,
      oldPal: Palette,
      newPal: Palette,
      useAccent: boolean
    ): string => {
      const PERIOD = 3.2;
      const waveFront = ((t % PERIOD) / PERIOD) * 1.45 - 0.15;
      const diff = waveFront - way;
      const on = 1 / (1 + Math.exp(-diff * 15));
      const band = Math.exp(-Math.pow(diff / 0.085, 2)) * 0.72;

      const cOld = useAccent ? oldPal.secondary : oldPal.primary;
      const cNew = useAccent ? newPal.secondary : newPal.primary;

      const baseR = lerp(cOld[0], cNew[0], on);
      const baseG = lerp(cOld[1], cNew[1], on);
      const baseB = lerp(cOld[2], cNew[2], on);

      const r = clamp(Math.floor(baseR * lum + (255 - baseR) * band), 18, 255);
      const g = clamp(Math.floor(baseG * lum + (255 - baseG) * band), 18, 255);
      const b = clamp(Math.floor(baseB * lum + (255 - baseB) * band), 24, 255);
      return `rgb(${r},${g},${b})`;
    };

    let animId = 0;
    const startTime = performance.now();

    const plotCell = (gx: number, gy: number, z: number, ch: string, color: string) => {
      if (gx < 0 || gx >= cols || gy < 0 || gy >= rows) return false;
      const idx = gy * cols + gx;
      if (z < zBuffer[idx]) {
        zBuffer[idx] = z;
        charBuffer[idx] = ch;
        colorBuffer[idx] = color;
        return true;
      }
      return false;
    };

    const plot3D = (
      x: number,
      y: number,
      z: number,
      ch: string,
      color: string,
      scale: number,
      centerX: number,
      centerY: number
    ) => {
      const fov = 3.4 / (3.4 + z * 0.65);
      const gx = Math.round(centerX + (x * scale * fov) / CELL_W);
      const gy = Math.round(centerY + (y * scale * fov) / CELL_H);
      return plotCell(gx, gy, z, ch, color);
    };

    const render = (now: number) => {
      const t = (now - startTime) * 0.001;
      const dt = 0.016;
      const mode = stateRef.current.preset;
      const amb = stateRef.current.ambient;

      zBuffer.fill(999);
      charBuffer.fill("");

      ctx.fillStyle = "#04060b";
      ctx.fillRect(0, 0, canvas.width, canvas.height);

      // Subtle dark dot matrix grid
      ctx.fillStyle = "rgba(45, 65, 95, 0.18)";
      for (let r = 2; r < rows; r += 3) {
        const py = r * CELL_H;
        for (let c = 2; c < cols; c += 4) {
          ctx.fillRect(c * CELL_W, py, 1, 1);
        }
      }

      const PERIOD = 3.2;
      const globalCycle = Math.floor(t / PERIOD) + stateRef.current.paletteIdx;
      const activePal = PALETTES[globalCycle % PALETTES.length];
      let charCount = 0;

      // ====================================================================
      // 1. AMBIENT BACKGROUND FX: SLIDING / SHOOTING STARS & ASCII RAIN
      // ====================================================================
      const showStars = amb === "stars" || amb === "both";
      const showRain = amb === "rain" || amb === "both";

      if (showStars) {
        const [pr, pg, pb] = activePal.accent;
        for (const st of driftingStars) {
          st.x += (st.vx - stateRef.current.mouseX * 1.2) * dt;
          st.y += (st.vy - stateRef.current.mouseY * 0.4) * dt;

          if (st.x < 0) st.x += cols;
          if (st.x >= cols) st.x -= cols;
          if (st.y < 0) st.y += rows;
          if (st.y >= rows) st.y -= rows;

          const twinkle = 0.55 + 0.45 * Math.sin(t * (2.2 + st.layer) + st.twinklePhase);
          const alpha = (0.18 + st.layer * 0.14) * twinkle;
          const glyph = st.layer === 2 ? (twinkle > 0.85 ? "✦" : "*") : st.layer === 1 ? "+" : "·";
          const col = `rgba(${pr}, ${pg}, ${pb}, ${alpha.toFixed(2)})`;
          if (plotCell(Math.floor(st.x), Math.floor(st.y), 50 - st.layer, glyph, col)) {
            charCount++;
          }
        }

        if (t - lastMeteorTime > 0.45) {
          lastMeteorTime = t;
          if (shootingStars.length < 7) {
            shootingStars.push({
              x: Math.random() * cols * 1.1,
              y: Math.random() * rows * 0.5,
              vx: -(38 + Math.random() * 24),
              vy: 14 + Math.random() * 11,
              len: 8 + Math.floor(Math.random() * 6),
              age: 0,
              maxLife: 0.9 + Math.random() * 0.6,
            });
          }
        }

        const [sr, sg, sb] = activePal.secondary;
        for (let i = shootingStars.length - 1; i >= 0; i--) {
          const ms = shootingStars[i];
          ms.age += dt;
          if (ms.age >= ms.maxLife) {
            shootingStars.splice(i, 1);
            continue;
          }
          ms.x += ms.vx * dt;
          ms.y += ms.vy * dt;
          const lifeFade = 1 - ms.age / ms.maxLife;

          for (let k = 0; k < ms.len; k++) {
            const tx = Math.round(ms.x - ms.vx * k * 0.018);
            const ty = Math.round(ms.y - ms.vy * k * 0.018);
            const tailFade = lifeFade * (1 - k / ms.len);
            const ch = k === 0 ? "★" : k === 1 ? "*" : k < 4 ? "=" : k < 6 ? "-" : ".";
            const col =
              k === 0
                ? `rgba(255, 255, 255, ${tailFade.toFixed(2)})`
                : `rgba(${sr}, ${sg}, ${sb}, ${(tailFade * 0.85).toFixed(2)})`;
            if (plotCell(tx, ty, 35, ch, col)) {
              charCount++;
            }
          }
        }
      }

      if (showRain) {
        const [rr, rg, rb] = activePal.primary;
        const windX = stateRef.current.mouseX * 3.5 + 1.5;

        for (const drop of rainDrops) {
          drop.y += drop.speed * dt;
          drop.x += windX * dt;

          if (drop.x < 0) drop.x += cols;
          if (drop.x >= cols) drop.x -= cols;

          if (drop.y >= rows - 2) {
            if (drop.layer === 2 && rainSplashes.length < 30) {
              rainSplashes.push({ x: Math.floor(drop.x), y: rows - 2, age: 0 });
            }
            drop.y = -Math.random() * 8;
            drop.x = Math.random() * cols;
          }

          const headX = Math.floor(drop.x);
          const headY = Math.floor(drop.y);
          const baseAlpha = 0.16 + drop.layer * 0.15;

          for (let k = 0; k < drop.len; k++) {
            const gx = Math.round(headX - windX * k * 0.08);
            const gy = headY - k;
            const fade = baseAlpha * (1 - k / drop.len);
            const ch = k === 0 ? (drop.layer === 2 ? "|" : ":") : k < 3 ? ":" : ".";
            const col =
              k === 0 && drop.layer === 2
                ? `rgba(200, 240, 255, ${(fade * 1.3).toFixed(2)})`
                : `rgba(${rr}, ${rg}, ${rb}, ${fade.toFixed(2)})`;
            if (plotCell(gx, gy, 40 - drop.layer, ch, col)) {
              charCount++;
            }
          }
        }

        for (let i = rainSplashes.length - 1; i >= 0; i--) {
          const sp = rainSplashes[i];
          sp.age += dt;
          if (sp.age > 0.35) {
            rainSplashes.splice(i, 1);
            continue;
          }
          const spread = Math.floor(sp.age * 10);
          const alpha = (1 - sp.age / 0.35) * 0.55;
          const col = `rgba(180, 235, 255, ${alpha.toFixed(2)})`;
          plotCell(sp.x - spread, sp.y, 38, "~", col);
          plotCell(sp.x + spread, sp.y, 38, "~", col);
          if (spread === 0) plotCell(sp.x, sp.y - 1, 38, "o", col);
        }
      }

      // ====================================================================
      // 2. FOREGROUND 3D PARAMETRIC CREATURES (5X SWARM)
      // ====================================================================
      const baseScale = Math.min(canvas.width, canvas.height) * 0.33;
      const agentCenters: { cx: number; cy: number; pal: Palette; scale: number }[] = [];

      for (const ag of AGENTS) {
        const ta = t + ag.phase;
        const scale = baseScale * ag.scaleMul;
        const cycle = Math.floor(ta / PERIOD) + stateRef.current.paletteIdx + ag.palOffset;
        const oldPal = PALETTES[cycle % PALETTES.length];
        const newPal = PALETTES[(cycle + 1) % PALETTES.length];

        let roamX = cols * ag.centerBiasX;
        let roamY = rows * ag.centerBiasY;

        if (mode === "jellyfish") {
          const pulseThrust = Math.sin(ta * 2.35 - 0.5) * 0.025;
          const normX =
            Math.sin(t * ag.freqX + ag.phase) * ag.ampX +
            Math.cos(t * 0.19 + ag.phase) * 0.08 +
            stateRef.current.mouseX * (0.10 / (ag.id * 0.4 + 1));
          const normY =
            Math.cos(t * ag.freqY + ag.phase) * ag.ampY -
            pulseThrust +
            stateRef.current.mouseY * (0.08 / (ag.id * 0.4 + 1));
          roamX = cols * clamp(ag.centerBiasX + normX, 0.08, 0.92);
          roamY = rows * clamp(ag.centerBiasY + normY, 0.10, 0.90);
        } else {
          const normX =
            Math.sin(t * ag.freqX + ag.phase) * ag.ampX +
            stateRef.current.mouseX * (0.11 / (ag.id * 0.4 + 1));
          const normY =
            Math.sin(t * ag.freqY * 1.4 + ag.phase) * ag.ampY +
            Math.cos(t * 0.27 + ag.phase) * 0.06 +
            stateRef.current.mouseY * (0.09 / (ag.id * 0.4 + 1));
          roamX = cols * clamp(ag.centerBiasX + normX, 0.08, 0.92);
          roamY = rows * clamp(ag.centerBiasY + normY, 0.12, 0.88);
        }

        agentCenters.push({ cx: roamX, cy: roamY, pal: newPal, scale });

        if (mode === "jellyfish") {
          const squeeze = 0.5 + 0.5 * Math.sin(ta * 2.35 - 0.4);
          const velX = Math.cos(t * ag.freqX + ag.phase) * ag.freqX;
          const tiltZ = -velX * 0.65;
          const tiltX = 0.22 * Math.sin(ta * 0.55) + stateRef.current.mouseY * 0.12;
          const rotY = ta * 0.6 + stateRef.current.mouseX * 0.3;
          const bobY = -0.16;

          const rotateJelly = (lx: number, ly: number, lz: number) => {
            const bx = lx * Math.cos(tiltZ) - ly * Math.sin(tiltZ);
            const by = lx * Math.sin(tiltZ) + ly * Math.cos(tiltZ);
            const y3 = by * Math.cos(tiltX) - lz * Math.sin(tiltX) + bobY;
            const z3 = by * Math.sin(tiltX) + lz * Math.cos(tiltX) + ag.zOffset;
            return { x: bx, y: y3, z: z3 };
          };

          const U_STEPS = 18;
          const TH_STEPS = 38;
          for (let iu = 0; iu <= U_STEPS; iu++) {
            const u = iu / U_STEPS;
            const contract = 1 - 0.22 * squeeze * Math.pow(u, 1.45);
            const baseR = Math.sin(u * Math.PI * 0.62) * 0.68 * contract;
            const baseY = -Math.cos(u * Math.PI * 0.62) * 0.52 * (1 + 0.12 * squeeze);

            for (let ith = 0; ith < TH_STEPS; ith++) {
              const th = (ith / TH_STEPS) * Math.PI * 2 + rotY;
              const lappet = 1 + 0.045 * Math.pow(u, 3) * Math.cos(th * 8);
              const r = baseR * lappet;

              const lx = r * Math.cos(th);
              const lz = r * Math.sin(th);
              const ly = baseY + 0.025 * Math.pow(u, 2) * Math.sin(th * 8);

              const p = rotateJelly(lx, ly, lz);
              const rib = Math.abs(Math.cos(th * 8));
              const depthLum = clamp(0.62 - (p.z - ag.zOffset) * 0.55 + rib * 0.22, 0.22, 1.15);

              let ch = ".";
              if (u > 0.91) ch = "*";
              else if (rib > 0.82) ch = "#";
              else if (depthLum > 0.85) ch = "@";
              else if (depthLum > 0.68) ch = "O";
              else if (depthLum > 0.50) ch = "=";
              else if (depthLum > 0.35) ch = ":";

              const color = computeLitRGB(u * 0.65, depthLum, ta, oldPal, newPal, rib > 0.8);
              if (plot3D(p.x, p.y, p.z, ch, color, scale, roamX, roamY)) {
                charCount++;
              }
            }
          }

          const N_TENT = 10;
          const S_STEPS = 32;
          for (let k = 0; k < N_TENT; k++) {
            const isInner = k < 3;
            const baseAngle = (k / N_TENT) * Math.PI * 2 + rotY * 0.7;
            const ringR = isInner ? 0.18 : 0.44;
            const length = isInner ? 1.25 : 1.08;

            for (let is = 0; is < S_STEPS; is++) {
              const s = is / S_STEPS;
              const td = ta * 2.35 - s * 2.9 - (k % 3) * 0.25;
              const sq = Math.sin(td);

              const spiralTh = baseAngle + s * 0.55 + 0.14 * Math.sin(td * 0.7 + k);
              const rad = ringR * (1 - 0.25 * s) * (1 - 0.18 * sq * Math.sqrt(s));

              const dragX = -velX * s * 0.85;
              const swayX = dragX + 0.14 * s * Math.cos(ta * 1.3 + s * 3.2 + k);
              const swayZ = 0.14 * s * Math.sin(ta * 1.1 + s * 3.0 + k);

              const lx = rad * Math.cos(spiralTh) + swayX;
              const lz = rad * Math.sin(spiralTh) + swayZ;
              const ly = 0.04 + s * length * (1 - 0.08 * sq);

              const p = rotateJelly(lx, ly, lz);
              const dx = Math.cos(spiralTh + s);
              const ch = isInner
                ? s < 0.7
                  ? "%"
                  : ":"
                : Math.abs(dx) < 0.32
                ? "|"
                : dx > 0
                ? "\\"
                : "/";

              const lum = clamp((1 - s * 0.55) * (0.72 - (p.z - ag.zOffset) * 0.4), 0.22, 1.0);
              const color = computeLitRGB(0.45 + s * 0.65, lum, ta, oldPal, newPal, isInner);
              if (plot3D(p.x, p.y, p.z, ch, color, scale, roamX, roamY)) {
                charCount++;
              }
            }
          }
        } else {
          // 5x Betta Fish School
          const vy =
            Math.cos(t * ag.freqY * 1.4 + ag.phase) * ag.ampY * ag.freqY * 1.4 -
            Math.sin(t * 0.27 + ag.phase) * 0.06 * 0.27;
          const swimPhase = Math.cos(t * ag.freqX + ag.phase);
          const turnAngle = (1 - (swimPhase * 0.5 + 0.5)) * Math.PI + Math.sin(ta * 0.6) * 0.22;
          const pitchAngle = clamp(-vy * 1.4, -0.38, 0.38);

          const transformFish = (fx: number, fy: number, fz: number) => {
            const spineLag = Math.max(0, fx + 0.25);
            const waveZ = fz + Math.sin(ta * 4.6 - spineLag * 5.4) * (0.09 * Math.pow(spineLag, 1.25));
            const py = fy * Math.cos(pitchAngle) - fx * Math.sin(pitchAngle);
            const px = fy * Math.sin(pitchAngle) + fx * Math.cos(pitchAngle);
            const rx = px * Math.cos(turnAngle) - waveZ * Math.sin(turnAngle);
            const rz = px * Math.sin(turnAngle) + waveZ * Math.cos(turnAngle) + ag.zOffset;
            return { x: rx, y: py, z: rz };
          };

          for (let i = 0; i < bettaBodySamples.length; i++) {
            const { u, th } = bettaBodySamples[i];
            const fx = -0.44 + u * 0.62;
            const archY = -0.04 * Math.sin(u * Math.PI);
            const halfH = 0.165 * Math.sin(Math.pow(u, 0.65) * Math.PI) * (1 - 0.2 * u);
            const halfW = halfH * 0.58;

            const fy = archY + Math.sin(th) * halfH;
            const fz = Math.cos(th) * halfW;

            const p = transformFish(fx, fy, fz);
            const lum = clamp(0.68 - (p.z - ag.zOffset) * 0.7 + Math.cos(th) * 0.2, 0.25, 1.15);

            const isEye = u > 0.08 && u < 0.15 && Math.abs(fy + 0.02) < 0.035 && Math.abs(fz) > 0.03;
            const ch = isEye ? "@" : lum > 0.85 ? "#" : lum > 0.65 ? "@" : lum > 0.45 ? "+" : ".";
            const color = isEye
              ? "#ffffff"
              : computeLitRGB(u * 0.35, lum, ta, oldPal, newPal, false);

            if (plot3D(p.x, p.y, p.z, ch, color, scale, roamX, roamY)) {
              charCount++;
            }
          }

          const TAIL_RAYS = 32;
          const RAY_STEPS = 24;
          for (let ir = 0; ir < TAIL_RAYS; ir++) {
            const a = (ir / (TAIL_RAYS - 1)) * 2 - 1;
            const spreadAngle = a * 1.28;

            for (let is = 1; is <= RAY_STEPS; is++) {
              const r = is / RAY_STEPS;
              const scallop = 1 + 0.06 * Math.cos(a * Math.PI * 12) * Math.pow(r, 2);
              const rayLen = 0.88 * r * scallop;

              const flutter = Math.sin(ta * 4.2 - r * 4.6 + a * 3.2) * (0.15 * r * r);
              const droop = 0.12 * r * r * (1 - 0.3 * Math.cos(a * Math.PI));

              const fx = 0.16 + Math.cos(spreadAngle * 0.72) * rayLen;
              const fy = Math.sin(spreadAngle) * rayLen * 0.78 + droop;
              const fz = flutter + Math.sin(a * 5 + r * 3) * 0.05 * r;

              const p = transformFish(fx, fy, fz);
              const rib = Math.abs(Math.cos(a * Math.PI * 14));
              const lum = clamp((1.05 - r * 0.38) * (0.72 - (p.z - ag.zOffset) * 0.45 + rib * 0.2), 0.22, 1.1);

              let ch = ":";
              if (r > 0.92) ch = "*";
              else if (rib > 0.75) ch = Math.abs(a) < 0.35 ? "=" : a > 0 ? "\\" : "/";
              else if (lum > 0.75) ch = "+";

              const color = computeLitRGB(0.32 + r * 0.68, lum, ta, oldPal, newPal, r > 0.55);
              if (plot3D(p.x, p.y, p.z, ch, color, scale, roamX, roamY)) {
                charCount++;
              }
            }
          }

          for (const up of [1, -1]) {
            const RAYS = 18;
            const STEPS = 15;
            for (let ir = 0; ir < RAYS; ir++) {
              const s = ir / (RAYS - 1);
              for (let is = 1; is <= STEPS; is++) {
                const r = is / STEPS;
                const finLen = (up === 1 ? 0.52 : 0.58) * Math.sin(Math.pow(s, 0.7) * Math.PI) * r;
                const sweepX = -0.15 + s * 0.38 + r * (0.28 + s * 0.22);
                const sweepY = -up * (0.11 + finLen * 0.85) + 0.06 * r * r;
                const sweepZ = Math.sin(ta * 4.4 - (s + r) * 4.2 + up) * 0.12 * r;

                const p = transformFish(sweepX, sweepY, sweepZ);
                const lum = clamp((1 - r * 0.35) * (0.72 - (p.z - ag.zOffset) * 0.4), 0.25, 1.05);
                const ch = r > 0.88 ? "." : up === 1 ? "/" : "\\";
                const color = computeLitRGB(0.25 + (s + r) * 0.38, lum, ta, oldPal, newPal, true);
                if (plot3D(p.x, p.y, p.z, ch, color, scale, roamX, roamY)) {
                  charCount++;
                }
              }
            }
          }
        }
      }

      // Glint rings & fireworks sparks across all 5 creatures
      if (t - lastGlintTime > 0.25 && agentCenters.length > 0) {
        lastGlintTime = t;
        const pick = agentCenters[Math.floor(Math.random() * agentCenters.length)];
        glints.push({
          t0: t,
          x0: (Math.random() - 0.5) * 0.45,
          y0: (Math.random() - 0.3) * 0.45,
          r0: 0.28 + Math.random() * 0.32,
          seed: Math.random() * Math.PI * 2,
          cx: pick.cx,
          cy: pick.cy,
        });
        if (glints.length > 20) glints.shift();
      }

      const pulseStep = Math.floor(t / (PERIOD * 2));
      if (pulseStep !== lastPulseIdx || stateRef.current.burstRequest) {
        lastPulseIdx = pulseStep;
        stateRef.current.burstRequest = false;
        for (const ac of agentCenters) {
          spawnBurst(ac.cx, ac.cy, ac.pal);
        }
      }

      for (let i = glints.length - 1; i >= 0; i--) {
        const g = glints[i];
        const age = t - g.t0;
        if (age > 1.9) {
          glints.splice(i, 1);
          continue;
        }
        const N_GLINTS = 12;
        const rad = g.r0 * (1 + 0.35 * (1 - Math.exp(-1.5 * age)));
        const y = g.y0 + 0.08 * age + 0.04 * age * age;
        for (let k = 0; k < N_GLINTS; k++) {
          const a = (k / N_GLINTS) * Math.PI * 2 + g.seed + age * 0.4;
          const twinkle = Math.sin(t * 6.5 + k * 1.7);
          if (twinkle > 0.35) {
            const x = g.x0 + rad * Math.cos(a);
            const z = rad * Math.sin(a);
            const ch = twinkle > 0.75 ? "*" : "+";
            const fade = Math.pow(1 - age / 1.9, 0.7);
            const col = `rgba(235, 250, 255, ${fade.toFixed(2)})`;
            if (plot3D(x, y, z, ch, col, baseScale * 0.75, g.cx, g.cy)) {
              charCount++;
            }
          }
        }
      }

      const DRAG = 1.65;
      for (let i = sparks.length - 1; i >= 0; i--) {
        const sp = sparks[i];
        sp.age += dt;
        if (sp.age >= sp.life) {
          sparks.splice(i, 1);
          continue;
        }
        const dragFactor = Math.exp(-DRAG * sp.age);
        const sx = sp.x + (sp.vx * (1 - dragFactor)) / DRAG;
        const sy = sp.y + (sp.vy * (1 - dragFactor)) / DRAG + 0.09 * sp.age * sp.age;
        const sz = sp.z + (sp.vz * (1 - dragFactor)) / DRAG;

        const fade = Math.pow(1 - sp.age / sp.life, 0.8);
        const [r, g, b] = sp.color;
        const headCol = `rgba(${r},${g},${b},${fade.toFixed(2)})`;
        if (plot3D(sx, sy, sz, "*", headCol, baseScale * 0.75, sp.cx, sp.cy)) {
          charCount++;
        }
        for (let tail = 1; tail <= 2; tail++) {
          const tAge = Math.max(0, sp.age - tail * 0.045);
          const df = Math.exp(-DRAG * tAge);
          const tx = sp.x + (sp.vx * (1 - df)) / DRAG;
          const ty = sp.y + (sp.vy * (1 - df)) / DRAG + 0.09 * tAge * tAge;
          const tz = sp.z + (sp.vz * (1 - df)) / DRAG;
          const tCol = `rgba(${r},${g},${b},${(fade * (1 - tail * 0.3)).toFixed(2)})`;
          plot3D(tx, ty, tz, tail === 1 ? "+" : ".", tCol, baseScale * 0.75, sp.cx, sp.cy);
        }
      }

      ctx.font = "bold 13px 'JetBrains Mono', 'Fira Code', Consolas, monospace";
      ctx.textBaseline = "top";
      for (let r = 0; r < rows; r++) {
        const rowOffset = r * cols;
        const py = r * CELL_H;
        for (let c = 0; c < cols; c++) {
          const ch = charBuffer[rowOffset + c];
          if (ch) {
            ctx.fillStyle = colorBuffer[rowOffset + c];
            ctx.fillText(ch, c * CELL_W, py);
          }
        }
      }

      ctx.font = "11px 'JetBrains Mono', Consolas, monospace";
      ctx.fillStyle = "rgba(160, 185, 215, 0.45)";
      const hudText = `omnilog.ascii  |  ${mode}.3d (x5 swarm)  |  fx: ${amb}  |  meteors ${shootingStars.length}   sparks ${sparks.length}   chars ${charCount}`;
      ctx.fillText(hudText, 18, canvas.height - 22);

      animId = requestAnimationFrame(render);
    };

    animId = requestAnimationFrame(render);

    return () => {
      cancelAnimationFrame(animId);
      window.removeEventListener("resize", resize);
      window.removeEventListener("mousemove", onMove);
      window.removeEventListener("mousedown", onDown);
    };
  }, []);

  const cycleAmbient = () => {
    const order: AmbientMode[] = ["both", "stars", "rain", "off"];
    setAmbient((prev) => order[(order.indexOf(prev) + 1) % order.length]);
  };

  return (
    <>
      <canvas
        ref={canvasRef}
        style={{
          position: "fixed",
          inset: 0,
          width: "100vw",
          height: "100vh",
          pointerEvents: "none",
          zIndex: 0,
          opacity: 0.82,
        }}
      />

      <div
        style={{
          position: "fixed",
          bottom: 14,
          right: 18,
          zIndex: 50,
          display: "flex",
          gap: 6,
          padding: "5px 10px",
          borderRadius: 9999,
          background: "rgba(8, 12, 22, 0.78)",
          backdropFilter: "blur(12px)",
          border: "1px solid rgba(255,255,255,0.14)",
          fontFamily: "monospace",
          fontSize: 11,
          color: "#cbd5e1",
        }}
      >
        <button
          type="button"
          onClick={() => {
            setAutoRoute(false);
            setPreset("jellyfish");
          }}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: preset === "jellyfish" ? "rgba(56, 189, 248, 0.22)" : "transparent",
            color: preset === "jellyfish" ? "#38bdf8" : "#94a3b8",
            border: preset === "jellyfish" ? "1px solid rgba(56,189,248,0.45)" : "1px solid transparent",
            cursor: "pointer",
          }}
        >
          ● 3D Jellyfish (x5)
        </button>
        <button
          type="button"
          onClick={() => {
            setAutoRoute(false);
            setPreset("betta");
          }}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: preset === "betta" ? "rgba(232, 121, 249, 0.22)" : "transparent",
            color: preset === "betta" ? "#e879f9" : "#94a3b8",
            border: preset === "betta" ? "1px solid rgba(232,121,249,0.45)" : "1px solid transparent",
            cursor: "pointer",
          }}
        >
          ● 3D Betta (x5)
        </button>
        <button
          type="button"
          onClick={cycleAmbient}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: ambient !== "off" ? "rgba(52, 211, 153, 0.18)" : "rgba(255,255,255,0.05)",
            color: ambient !== "off" ? "#6ee7b7" : "#94a3b8",
            border: ambient !== "off" ? "1px solid rgba(52,211,153,0.4)" : "1px solid rgba(255,255,255,0.1)",
            cursor: "pointer",
          }}
        >
          ☄ FX: {ambient.toUpperCase()}
        </button>
        <button
          type="button"
          onClick={() => {
            stateRef.current.burstRequest = true;
            setPaletteIdx((p) => (p + 1) % PALETTES.length);
          }}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: "rgba(255,255,255,0.06)",
            color: "#e2e8f0",
            border: "1px solid rgba(255,255,255,0.12)",
            cursor: "pointer",
          }}
        >
          ✦ Pulse / Colour
        </button>
      </div>
    </>
  );
}
