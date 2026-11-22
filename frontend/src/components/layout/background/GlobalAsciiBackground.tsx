"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

export type PresetKey = "jellyfish" | "betta" | "manta";
export type AmbientMode = "both" | "stars" | "rain" | "off";

interface Palette {
  name: string;
  primary: [number, number, number];
  secondary: [number, number, number];
  accent: [number, number, number];
}

const PALETTES: Palette[] = [
  { name: "Sapphire & Pearl", primary: [56, 165, 255], secondary: [125, 235, 255], accent: [240, 249, 255] },
  { name: "Coral & Gold", primary: [255, 95, 110], secondary: [255, 200, 85], accent: [255, 247, 230] },
  { name: "Emerald & Mint", primary: [30, 215, 150], secondary: [140, 250, 195], accent: [236, 253, 245] },
  { name: "Amethyst & Rose", primary: [175, 105, 255], secondary: [250, 150, 210], accent: [253, 242, 248] },
  { name: "Amber & Crimson", primary: [250, 135, 50], secondary: [255, 220, 110], accent: [255, 251, 235] },
  { name: "Glacier & Cobalt", primary: [85, 125, 255], secondary: [95, 235, 245], accent: [240, 253, 250] },
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

const AGENTS: AgentConfig[] = [
  { id: 0, scaleMul: 0.92, phase: 0.0, freqX: 0.32, freqY: 0.44, ampX: 0.30, ampY: 0.24, centerBiasX: 0.50, centerBiasY: 0.48, palOffset: 0, zOffset: 0.00 },
  { id: 1, scaleMul: 0.76, phase: 1.4, freqX: 0.28, freqY: 0.39, ampX: 0.26, ampY: 0.25, centerBiasX: 0.22, centerBiasY: 0.30, palOffset: 1, zOffset: 0.25 },
  { id: 2, scaleMul: 0.70, phase: 2.8, freqX: 0.36, freqY: 0.32, ampX: 0.27, ampY: 0.24, centerBiasX: 0.78, centerBiasY: 0.32, palOffset: 2, zOffset: 0.45 },
  { id: 3, scaleMul: 0.64, phase: 4.2, freqX: 0.30, freqY: 0.46, ampX: 0.28, ampY: 0.22, centerBiasX: 0.24, centerBiasY: 0.72, palOffset: 3, zOffset: 0.65 },
  { id: 4, scaleMul: 0.58, phase: 5.5, freqX: 0.39, freqY: 0.35, ampX: 0.26, ampY: 0.23, centerBiasX: 0.76, centerBiasY: 0.70, palOffset: 4, zOffset: 0.85 },
];

const clamp = (v: number, lo: number, hi: number) => (v < lo ? lo : v > hi ? hi : v);
const lerp = (a: number, b: number, u: number) => a + (b - a) * u;

type Vec3 = [number, number, number];

// ---------------------------------------------------------------------------
// Shading
// ---------------------------------------------------------------------------

// Dark -> bright characters used for lit surfaces. A 4x4 ordered dither blends
// neighbouring levels so gradients look smooth instead of banded.
const RAMP = ".:-=+*#%@";
const BAYER4 = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5];

const norm3 = (v: Vec3): Vec3 => {
  const l = Math.hypot(v[0], v[1], v[2]) || 1;
  return [v[0] / l, v[1] / l, v[2] / l];
};

// The viewer sits at -z, so "toward the viewer" is negative z.
// The light comes from the upper left, slightly toward the viewer.
const LIGHT = norm3([-0.45, -0.65, -0.62]);
const HALF = norm3([LIGHT[0], LIGHT[1], LIGHT[2] - 1]);
const AMBIENT_LIGHT = 0.2;

// Diffuse + rim + specular for a (possibly unnormalised) surface normal.
// Surfaces are double sided, so a normal pointing away from the viewer is flipped.
const lightSurface = (nx: number, ny: number, nz: number, rimW: number, specW: number): number => {
  const len = Math.sqrt(nx * nx + ny * ny + nz * nz) || 1;
  nx /= len;
  ny /= len;
  nz /= len;
  if (nz > 0) {
    nx = -nx;
    ny = -ny;
    nz = -nz;
  }
  const diff = Math.max(0, nx * LIGHT[0] + ny * LIGHT[1] + nz * LIGHT[2]);
  const rim = Math.pow(1 + nz, 2.4);
  const spec = Math.pow(Math.max(0, nx * HALF[0] + ny * HALF[1] + nz * HALF[2]), 26);
  return AMBIENT_LIGHT + diff * 0.62 + rim * rimW + spec * specW;
};

export default function GlobalAsciiBackground() {
  const canvasRef = useRef<HTMLCanvasElement | null>(null);
  const pathname = usePathname();

  const [manualPreset, setManualPreset] = useState<PresetKey>("jellyfish");
  const [ambient, setAmbient] = useState<AmbientMode>("both");
  const [autoRoute, setAutoRoute] = useState<boolean>(true);
  const [paletteIdx, setPaletteIdx] = useState<number>(0);

  const routePreset: PresetKey =
    pathname?.includes("/login") || pathname?.includes("/register") || pathname?.includes("/search")
      ? "jellyfish"
      : "betta";
  const preset: PresetKey = autoRoute ? routePreset : manualPreset;

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
    const canvas = canvasRef.current;
    if (!canvas) return;
    // Use alpha: true so the canvas never gets hidden behind body background stacking
    const ctx = canvas.getContext("2d", { alpha: true });
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

      const dropCount = Math.min(145, Math.floor((cols * rows) / 44));
      for (let i = 0; i < dropCount; i++) {
        const layer = i % 3;
        rainDrops.push({
          x: Math.random() * cols,
          y: Math.random() * rows,
          speed: 15 + layer * 8.5 + Math.random() * 5,
          len: 3 + layer * 2 + Math.floor(Math.random() * 3),
          layer,
        });
      }

      const starCount = Math.min(125, Math.floor((cols * rows) / 50));
      for (let i = 0; i < starCount; i++) {
        const layer = i % 3;
        driftingStars.push({
          x: Math.random() * cols,
          y: Math.random() * rows,
          vx: -(1.2 + layer * 1.5 + Math.random() * 0.7),
          vy: 0.24 + layer * 0.18,
          layer,
          twinklePhase: Math.random() * Math.PI * 2,
        });
      }
    };

    const resize = () => {
      canvas.width = window.innerWidth || 1280;
      canvas.height = window.innerHeight || 720;
      cols = Math.max(10, Math.floor(canvas.width / CELL_W));
      rows = Math.max(10, Math.floor(canvas.height / CELL_H));
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
          vy: Math.cos(phi) * speed - 0.14,
          vz: Math.sin(phi) * Math.sin(theta) * speed,
          age: 0,
          life: 1.35 + Math.random() * 1.1,
          color: i % 2 === 0 ? pal.accent : pal.secondary,
          cx,
          cy,
        });
      }
    };

    // `whiten` pushes the colour toward white (rim light, specular highlights).
    const computeLitRGB = (
      way: number,
      lum: number,
      t: number,
      oldPal: Palette,
      newPal: Palette,
      useAccent: boolean,
      whiten = 0
    ): string => {
      const PERIOD = 3.8;
      const waveFront = ((t % PERIOD) / PERIOD) * 1.45 - 0.15;
      const diff = waveFront - way;
      const on = 1 / (1 + Math.exp(-diff * 14));
      const band = Math.exp(-Math.pow(diff / 0.09, 2)) * 0.75;

      const cOld = useAccent ? oldPal.secondary : oldPal.primary;
      const cNew = useAccent ? newPal.secondary : newPal.primary;

      const baseR = lerp(cOld[0], cNew[0], on);
      const baseG = lerp(cOld[1], cNew[1], on);
      const baseB = lerp(cOld[2], cNew[2], on);

      let r = clamp(Math.floor(baseR * lum + (255 - baseR) * band), 28, 255);
      let g = clamp(Math.floor(baseG * lum + (255 - baseG) * band), 28, 255);
      let b = clamp(Math.floor(baseB * lum + (255 - baseB) * band), 35, 255);
      if (whiten > 0) {
        const w = clamp(whiten, 0, 1);
        r = Math.floor(r + (255 - r) * w);
        g = Math.floor(g + (255 - g) * w);
        b = Math.floor(b + (255 - b) * w);
      }
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

    // Screen-space (cell units, fractional) position of a 3D point.
    const projX = (x: number, z: number, scale: number, cx: number) =>
      cx + (x * scale * (3.4 / (3.4 + z * 0.65))) / CELL_W;
    const projY = (y: number, z: number, scale: number, cy: number) =>
      cy + (y * scale * (3.4 / (3.4 + z * 0.65))) / CELL_H;

    // Character that follows a stroke direction on screen (cells are taller than wide).
    const dirChar = (dx: number, dy: number, flat = "-"): string => {
      const ax = Math.abs(dx) * CELL_W;
      const ay = Math.abs(dy) * CELL_H;
      if (ax + ay < 1e-6) return "|";
      const ang = Math.atan2(ay, ax);
      if (ang > 1.18) return "|";
      if (ang < 0.36) return flat;
      return dx * dy > 0 ? "\\" : "/";
    };

    // Pick a ramp character for a brightness value, dithered against neighbouring cells.
    const shadeChar = (lum: number, gx: number, gy: number): string => {
      const v = clamp(lum, 0, 1) * (RAMP.length - 1) + (BAYER4[((gy & 3) << 2) | (gx & 3)] / 16 - 0.47) * 0.95;
      return RAMP[clamp(Math.round(v), 0, RAMP.length - 1)];
    };

    // Depth-tested plot that picks its own character from the brightness unless `ch` is given.
    // `zBias` pulls a point toward the viewer for the depth test only (eyes, highlights).
    const plotLit = (
      x: number,
      y: number,
      z: number,
      lum: number,
      color: string,
      scale: number,
      centerX: number,
      centerY: number,
      ch?: string,
      zBias = 0
    ) => {
      const fov = 3.4 / (3.4 + z * 0.65);
      const gx = Math.round(centerX + (x * scale * fov) / CELL_W);
      const gy = Math.round(centerY + (y * scale * fov) / CELL_H);
      if (gx < 0 || gx >= cols || gy < 0 || gy >= rows) return false;
      const idx = gy * cols + gx;
      const zt = z - zBias;
      if (zt >= zBuffer[idx]) return false;
      zBuffer[idx] = zt;
      charBuffer[idx] = ch !== undefined ? ch : shadeChar(lum, gx, gy);
      colorBuffer[idx] = color;
      return true;
    };

    const render = (now: number) => {
      if (cols === 0 || rows === 0) resize();
      const t = (now - startTime) * 0.001;
      const dt = 0.016;
      const mode = stateRef.current.preset;
      const amb = stateRef.current.ambient;

      zBuffer.fill(999);
      charBuffer.fill("");

      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Subtle architectural dot grid
      ctx.fillStyle = "rgba(120, 150, 195, 0.16)";
      for (let r = 2; r < rows; r += 3) {
        const py = r * CELL_H;
        for (let c = 2; c < cols; c += 4) {
          ctx.fillRect(c * CELL_W, py, 1, 1);
        }
      }

      const PERIOD = 3.8;
      const globalCycle = Math.floor(t / PERIOD) + stateRef.current.paletteIdx;
      const activePal = PALETTES[globalCycle % PALETTES.length];
      let charCount = 0;

      const showStars = amb === "stars" || amb === "both";
      const showRain = amb === "rain" || amb === "both";

      if (showStars) {
        const [pr, pg, pb] = activePal.secondary;
        for (const st of driftingStars) {
          st.x += (st.vx - stateRef.current.mouseX * 1.1) * dt;
          st.y += (st.vy - stateRef.current.mouseY * 0.35) * dt;

          if (st.x < 0) st.x += cols;
          if (st.x >= cols) st.x -= cols;
          if (st.y < 0) st.y += rows;
          if (st.y >= rows) st.y -= rows;

          const twinkle = 0.55 + 0.45 * Math.sin(t * (2.1 + st.layer) + st.twinklePhase);
          const alpha = (0.25 + st.layer * 0.18) * twinkle;
          const glyph = st.layer === 2 ? (twinkle > 0.85 ? "✦" : "*") : st.layer === 1 ? "+" : "·";
          const col = `rgba(${pr}, ${pg}, ${pb}, ${alpha.toFixed(2)})`;
          if (plotCell(Math.floor(st.x), Math.floor(st.y), 50 - st.layer, glyph, col)) {
            charCount++;
          }
        }

        if (t - lastMeteorTime > 0.50) {
          lastMeteorTime = t;
          if (shootingStars.length < 6) {
            shootingStars.push({
              x: Math.random() * cols * 1.1,
              y: Math.random() * rows * 0.5,
              vx: -(38 + Math.random() * 22),
              vy: 14 + Math.random() * 10,
              len: 8 + Math.floor(Math.random() * 6),
              age: 0,
              maxLife: 0.9 + Math.random() * 0.55,
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
                : `rgba(${sr}, ${sg}, ${sb}, ${(tailFade * 0.90).toFixed(2)})`;
            if (plotCell(tx, ty, 35, ch, col)) {
              charCount++;
            }
          }
        }
      }

      if (showRain) {
        const [rr, rg, rb] = activePal.primary;
        const windX = stateRef.current.mouseX * 3.2 + 1.4;

        for (const drop of rainDrops) {
          drop.y += drop.speed * dt;
          drop.x += windX * dt;

          if (drop.x < 0) drop.x += cols;
          if (drop.x >= cols) drop.x -= cols;

          if (drop.y >= rows - 2) {
            if (drop.layer === 2 && rainSplashes.length < 28) {
              rainSplashes.push({ x: Math.floor(drop.x), y: rows - 2, age: 0 });
            }
            drop.y = -Math.random() * 8;
            drop.x = Math.random() * cols;
          }

          const headX = Math.floor(drop.x);
          const headY = Math.floor(drop.y);
          const baseAlpha = 0.22 + drop.layer * 0.18;

          for (let k = 0; k < drop.len; k++) {
            const gx = Math.round(headX - windX * k * 0.08);
            const gy = headY - k;
            const fade = baseAlpha * (1 - k / drop.len);
            const ch = k === 0 ? (drop.layer === 2 ? "|" : ":") : k < 3 ? ":" : ".";
            const col =
              k === 0 && drop.layer === 2
                ? `rgba(235, 248, 255, ${(fade * 1.3).toFixed(2)})`
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
          const alpha = (1 - sp.age / 0.35) * 0.60;
          const col = `rgba(210, 240, 255, ${alpha.toFixed(2)})`;
          plotCell(sp.x - spread, sp.y, 38, "~", col);
          plotCell(sp.x + spread, sp.y, 38, "~", col);
          if (spread === 0) plotCell(sp.x, sp.y - 1, 38, "o", col);
        }
      }

      const baseScale = Math.min(canvas.width, canvas.height) * 0.34;
      const agentCenters: { cx: number; cy: number; pal: Palette; scale: number }[] = [];

      for (const ag of AGENTS) {
        const ta = t + ag.phase;
        const scale = baseScale * ag.scaleMul;
        const cycle = Math.floor(ta / PERIOD) + stateRef.current.paletteIdx + ag.palOffset;
        const oldPal = PALETTES[cycle % PALETTES.length];
        const newPal = PALETTES[(cycle + 1) % PALETTES.length];

        // Sample density follows the on-screen size, so big screens get no holes and small ones stay cheap.
        const dens = clamp(scale / 200, 0.7, 2.4);
        // Creatures further back are a little dimmer.
        const depthDim = 1 - ag.zOffset * 0.22;

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
          // betta and manta share the same horizontal cruising path
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

          const cTz = Math.cos(tiltZ);
          const sTz = Math.sin(tiltZ);
          const cTx = Math.cos(tiltX);
          const sTx = Math.sin(tiltX);

          // Rotation only (also used for surface normals); position adds bobY and the depth offset.
          const rotVecJelly = (lx: number, ly: number, lz: number): Vec3 => {
            const bx = lx * cTz - ly * sTz;
            const by = lx * sTz + ly * cTz;
            return [bx, by * cTx - lz * sTx, by * sTx + lz * cTx];
          };

          // Bell surface: u runs from the apex (0) to the scalloped rim (1)
          const bellLocal = (u: number, th: number): Vec3 => {
            const contract = 1 - 0.22 * squeeze * Math.pow(u, 1.45);
            let r = Math.sin(u * Math.PI * 0.62) * 0.68 * contract;
            const y0 = -Math.cos(u * Math.PI * 0.62) * 0.52 * (1 + 0.12 * squeeze);
            const lap = Math.cos(th * 8);
            r *= 1 + 0.06 * Math.pow(u, 3.5) * lap + 0.05 * Math.pow(u, 6);
            const y = y0 + 0.04 * Math.pow(u, 4) * Math.sin(th * 8);
            return [r * Math.cos(th), y, r * Math.sin(th)];
          };

          // Bell: lit like a translucent glass dome, bright at the rim, with radial canals
          // and the four horseshoe-shaped gonads seen through the top.
          const U_STEPS = Math.ceil(22 * dens);
          const TH_STEPS = Math.ceil(96 * dens);
          for (let iu = 0; iu <= U_STEPS; iu++) {
            const u = 0.012 + 0.988 * (iu / U_STEPS);
            for (let ith = 0; ith < TH_STEPS; ith++) {
              const th = (ith / TH_STEPS) * Math.PI * 2 + rotY;
              const p0 = bellLocal(u, th);
              const pu = bellLocal(u + 0.012, th);
              const pt = bellLocal(u, th + 0.03);

              const tux = pu[0] - p0[0];
              const tuy = pu[1] - p0[1];
              const tuz = pu[2] - p0[2];
              const tvx = pt[0] - p0[0];
              const tvy = pt[1] - p0[1];
              const tvz = pt[2] - p0[2];
              const n = rotVecJelly(tuy * tvz - tuz * tvy, tuz * tvx - tux * tvz, tux * tvy - tuy * tvx);
              const q = rotVecJelly(p0[0], p0[1], p0[2]);

              const rib = Math.abs(Math.cos(th * 8));
              const canal = rib > 0.9 ? 1 : 0;

              let gon = 0;
              if (u < 0.88) {
                for (let k = 0; k < 4; k++) {
                  const phi = k * (Math.PI / 2) + rotY * 0.5;
                  const dx = p0[0] - 0.27 * Math.cos(phi);
                  const dz = p0[2] - 0.27 * Math.sin(phi);
                  const d = Math.abs(Math.sqrt(dx * dx + dz * dz) - 0.16);
                  if (d < 0.06) {
                    // the open side of each horseshoe faces the bell axis
                    const ang = Math.atan2(dz, dx) - (phi + Math.PI);
                    const wrapped = Math.abs(Math.atan2(Math.sin(ang), Math.cos(ang)));
                    if (wrapped > 0.55) gon = Math.max(gon, Math.exp(-Math.pow(d / 0.024, 2)));
                  }
                }
              }

              let lum = lightSurface(n[0], n[1], n[2], 0.8, 0.55);
              lum = lum * (0.82 + 0.18 * rib) + canal * 0.12 + gon * 0.55;
              if (u > 0.9) lum += (u - 0.9) * 3.0;
              lum *= depthDim;

              const whiten = clamp((lum - 0.85) * 1.1, 0, 0.6) + gon * 0.25;
              const color = computeLitRGB(
                u * 0.65,
                0.3 + clamp(lum, 0, 1.2) * 0.85,
                ta,
                oldPal,
                newPal,
                canal === 1 || gon > 0.3 || u > 0.9,
                whiten
              );
              const rimChar = u > 0.955 ? (Math.cos(th * 8) > 0 ? "*" : "o") : undefined;
              if (plotLit(q[0], q[1] + bobY, q[2] + ag.zOffset, lum, color, scale, roamX, roamY, rimChar)) {
                charCount++;
              }
            }
          }

          // Frilled oral arms in the middle (two strands each, ruffling as they trail)
          const ARMS = 4;
          const ARM_STEPS = Math.ceil(30 * dens);
          for (let k = 0; k < ARMS; k++) {
            const baseAngle = (k / ARMS) * Math.PI * 2 + rotY * 0.7 + 0.4;
            for (const strand of [-1, 1]) {
              for (let is = 0; is <= ARM_STEPS; is++) {
                const s = is / ARM_STEPS;
                const td = ta * 2.35 - s * 2.5 - k * 0.3;
                const sq = Math.sin(td);
                const ruffle = 0.075 * s * Math.sin(ta * 1.7 + s * 9 + k * 2.1 + strand * 0.9);
                const rad =
                  0.16 * (1 - 0.35 * s) * (1 - 0.15 * sq * Math.sqrt(s)) + strand * 0.03 * (0.4 + s) + ruffle;
                const th = baseAngle + s * 0.9;
                const swayX = -velX * s * 0.6 + 0.08 * s * Math.cos(ta * 1.2 + s * 3 + k);
                const swayZ = 0.08 * s * Math.sin(ta * 1.0 + s * 3.4 + k);

                const lx = rad * Math.cos(th) + swayX;
                const lz = rad * Math.sin(th) + swayZ;
                const ly = -0.05 + s * 1.15 * (1 - 0.08 * sq);
                const q = rotVecJelly(lx, ly, lz);

                const lum = (1 - s * 0.45) * 0.95 * depthDim;
                const ch = s < 0.72 ? ((is + k) % 2 === 0 ? "%" : "&") : ":";
                const color = computeLitRGB(0.4 + s * 0.6, 0.3 + lum * 0.85, ta, oldPal, newPal, true, (1 - s) * 0.15);
                if (plotLit(q[0], q[1] + bobY, q[2] + ag.zOffset, lum, color, scale, roamX, roamY, ch)) {
                  charCount++;
                }
              }
            }
          }

          // Fine tentacles hang from the scalloped rim and follow the pulse with a delay
          const T_OUT = 14;
          const T_STEPS = Math.ceil(34 * dens);
          for (let k = 0; k < T_OUT; k++) {
            const base = bellLocal(1, (k / T_OUT) * Math.PI * 2 + rotY + 0.11);
            const length = 1.0 + 0.18 * Math.sin(k * 2.3);
            let prevX = NaN;
            let prevY = NaN;

            for (let is = 0; is <= T_STEPS; is++) {
              const s = is / T_STEPS;
              const td = ta * 2.35 - s * 2.9 - (k % 3) * 0.25;
              const sq = Math.sin(td);

              const gather = 1 - (0.2 * s + 0.1 * sq * Math.sqrt(s));
              const swayX = -velX * s * 0.85 + 0.13 * s * Math.cos(ta * 1.3 + s * 4.1 + k * 1.7);
              const swayZ = 0.13 * s * Math.sin(ta * 1.1 + s * 3.7 + k);

              const lx = base[0] * gather + swayX;
              const lz = base[2] * gather + swayZ;
              const ly = base[1] + s * length * (1 - 0.08 * sq);

              const q = rotVecJelly(lx, ly, lz);
              const px = q[0];
              const py = q[1] + bobY;
              const pz = q[2] + ag.zOffset;
              const sx = projX(px, pz, scale, roamX);
              const sy = projY(py, pz, scale, roamY);

              if (is > 0) {
                const ch = s > 0.84 ? "." : dirChar(sx - prevX, sy - prevY, "~");
                const lum = (0.95 - s * 0.55) * depthDim;
                const color = computeLitRGB(0.45 + s * 0.65, 0.3 + lum * 0.85, ta, oldPal, newPal, false, (1 - s) * 0.1);
                if (plotLit(px, py, pz, lum, color, scale, roamX, roamY, ch)) {
                  charCount++;
                }
              }
              prevX = sx;
              prevY = sy;
            }
          }
        } else if (mode === "manta") {
          // Local frame: x = forward (nose at +x), y = wingspan, z = depth (negative = toward the viewer / back of the ray)
          const vy =
            Math.cos(t * ag.freqY * 1.4 + ag.phase) * ag.ampY * ag.freqY * 1.4 -
            Math.sin(t * 0.27 + ag.phase) * 0.06 * 0.27;
          const swimPhase = Math.cos(t * ag.freqX + ag.phase);

          // 0 = facing right, PI = facing left; the turn only happens near the screen edges
          const turnK = clamp((0.35 - swimPhase) / 0.7, 0, 1);
          const turnAngle = Math.PI * turnK * turnK * (3 - 2 * turnK);
          const noseTilt = clamp(-vy * 1.8, -0.32, 0.32);
          // mostly a top-down view with a slight bank, so the wing flap reads as a V opening and closing
          const roll = 0.38 + 0.08 * Math.sin(ta * 0.45) + stateRef.current.mouseY * 0.10;
          // keeps the nose a little closer to the viewer than the tail, in both swim directions
          const yaw = turnAngle - 0.3 * Math.cos(turnAngle);

          const cr = Math.cos(roll);
          const sr = Math.sin(roll);
          const ct = Math.cos(noseTilt);
          const st = Math.sin(noseTilt);
          const cyaw = Math.cos(yaw);
          const syaw = Math.sin(yaw);

          // rotation only (also used for surface normals)
          const rotVecManta = (mx: number, my: number, mz: number): Vec3 => {
            // roll around the body axis so we look at the ray from above at an angle
            const ry = my * cr - mz * sr;
            const rz = my * sr + mz * cr;
            // nose up / down in the screen plane
            const px = mx * ct + ry * st;
            const py = ry * ct - mx * st;
            // heading (face left or right)
            return [px * cyaw - rz * syaw, py, px * syaw + rz * cyaw];
          };
          const transformManta = (mx: number, my: number, mz: number) => {
            const v = rotVecManta(mx, my, mz);
            return { x: v[0], y: v[1], z: v[2] + ag.zOffset };
          };

          const FLAP_SPEED = 2.2;
          const domeAt = (a: number, c: number) =>
            Math.exp(-Math.pow(a / 0.26, 2)) * Math.pow(Math.sin(clamp(c, 0, 1) * Math.PI), 0.7);

          // Body + wings: one continuous surface, span `s` from tip to tip, chord `c` from trailing to leading edge
          const mantaLocal = (s: number, c: number): Vec3 => {
            const a = Math.abs(s);
            const xLe = 0.4 - 0.44 * Math.pow(a, 1.3);
            const xTe = -0.34 + 0.3 * Math.pow(a, 0.95);
            const mx = lerp(xTe, xLe, c);

            // each span station is rotated about the body axis: both wings swing up and down together
            const flapAngle = Math.sin(ta * FLAP_SPEED - a * 1.7) * 0.62 * (0.15 + 0.85 * a);
            const my = s * 0.95 * Math.cos(flapAngle);
            const lift = a * 0.95 * Math.sin(flapAngle);

            const edgeLag = Math.sin(ta * FLAP_SPEED - a * 1.7 - (1 - c) * 1.1) * 0.06 * (1 - c) * a;
            const ripple = 0.02 * Math.sin(ta * FLAP_SPEED - mx * 2.5) * (1 - a);
            const mz = -0.1 * domeAt(a, c) - lift - edgeLag + 0.05 * a * a + ripple;
            return [mx, my, mz];
          };

          const S_STEPS = Math.ceil(80 * dens);
          const C_STEPS = Math.ceil(30 * dens);
          for (let is = 0; is <= S_STEPS; is++) {
            const s = (is / S_STEPS) * 2 - 1;
            const a = Math.abs(s);

            for (let ic = 0; ic <= C_STEPS; ic++) {
              const c = ic / C_STEPS;
              const p0 = mantaLocal(s, c);
              const ps = mantaLocal(s + 0.012, c);
              const pc = mantaLocal(s, c + 0.02);

              let nxl = (ps[1] - p0[1]) * (pc[2] - p0[2]) - (ps[2] - p0[2]) * (pc[1] - p0[1]);
              let nyl = (ps[2] - p0[2]) * (pc[0] - p0[0]) - (ps[0] - p0[0]) * (pc[2] - p0[2]);
              let nzl = (ps[0] - p0[0]) * (pc[1] - p0[1]) - (ps[1] - p0[1]) * (pc[0] - p0[0]);
              // orient the local normal toward the dorsal (back) side
              if (nzl > 0) {
                nxl = -nxl;
                nyl = -nyl;
                nzl = -nzl;
              }
              const n = rotVecManta(nxl, nyl, nzl);
              const q = rotVecManta(p0[0], p0[1], p0[2]);
              // when the back faces the viewer we see the dark dorsal side, otherwise the pale belly
              const dorsal = n[2] <= 0;

              const rib = Math.abs(Math.cos(a * Math.PI * 9 + c * 1.4));
              const dome = domeAt(a, c);

              // pale shoulder patches on the back, gill slits and mouth on the belly
              const onPatch = dorsal && Math.abs(a - 0.2) < 0.05 && c > 0.42 && c < 0.82;
              const onSlit = !dorsal && a > 0.05 && a < 0.3 && c > 0.2 && c < 0.75 && Math.abs(Math.sin(c * Math.PI * 6)) > 0.93;
              const onMouth = !dorsal && c > 0.88 && a < 0.07;

              let lum = lightSurface(n[0], n[1], n[2], 0.45, 0.45);
              lum = dorsal ? lum * 0.85 + rib * 0.06 + dome * 0.05 : lum * 0.95 + 0.14;
              if (onPatch) lum = Math.max(lum, 0.85);
              if (onSlit || onMouth) lum *= 0.45;

              let ch: string | undefined;
              if (a > 0.95) {
                ch = "*";
                lum = Math.max(lum, 0.9);
              } else if (c > 0.94) {
                ch = "#";
                lum = Math.max(lum, 0.78);
              } else if (c < 0.05) {
                ch = ":";
                lum = Math.max(lum, 0.45);
              } else if (onSlit) {
                ch = "=";
              } else if (onMouth) {
                ch = "-";
              }
              lum *= depthDim;

              const whiten = dorsal
                ? onPatch
                  ? 0.7
                  : clamp((lum - 0.9) * 1.0, 0, 0.5)
                : 0.5 + clamp(lum - 0.8, 0, 0.3);
              const color = computeLitRGB(
                0.12 + a * 0.55 + (1 - c) * 0.12,
                0.3 + clamp(lum, 0, 1.2) * 0.85,
                ta,
                oldPal,
                newPal,
                c > 0.9 || (dorsal && rib > 0.9),
                whiten
              );

              if (plotLit(q[0], q[1], q[2] + ag.zOffset, lum, color, scale, roamX, roamY, ch)) {
                charCount++;
              }
            }
          }

          // Cephalic fins (the little "horns" on each side of the mouth)
          for (const side of [1, -1]) {
            for (let ik = 0; ik <= 12; ik++) {
              const k = ik / 12;
              const mx = 0.4 + 0.22 * k;
              const my = side * (0.075 + 0.045 * Math.sin(k * Math.PI * 0.9) - 0.02 * k);
              const mz = -0.03 - 0.03 * k + 0.02 * Math.sin(ta * FLAP_SPEED - k * 2);

              const p = transformManta(mx, my, mz);
              const lum = clamp(0.8 - (p.z - ag.zOffset) * 0.38, 0.35, 1.15) * depthDim;
              const ch = k > 0.8 ? "." : k > 0.45 ? "-" : "=";
              const color = computeLitRGB(0.05 + k * 0.1, 0.3 + lum * 0.85, ta, oldPal, newPal, true, 0.2);
              if (plotLit(p.x, p.y, p.z, lum, color, scale, roamX, roamY, ch, 0.02)) {
                charCount++;
              }
            }
          }

          // Eyes
          for (const side of [1, -1]) {
            const p = transformManta(0.27, side * 0.17, -0.06);
            if (plotLit(p.x, p.y, p.z, 1, "#ffffff", scale, roamX, roamY, "@", 0.05)) {
              charCount++;
            }
          }

          // Whip tail
          const TAIL_STEPS = Math.ceil(64 * dens);
          let tailPrevX = NaN;
          let tailPrevY = NaN;
          for (let it = 0; it <= TAIL_STEPS; it++) {
            const r = it / TAIL_STEPS;
            const wave = ta * 2.4 - r * 5.2;
            const mx = -0.32 - 1.0 * r;
            const my = Math.sin(wave) * 0.13 * r * (0.4 + r);
            const mz = -0.01 + Math.cos(wave) * 0.04 * r;

            const p = transformManta(mx, my, mz);
            const sx = projX(p.x, p.z, scale, roamX);
            const sy = projY(p.y, p.z, scale, roamY);
            if (it > 0) {
              const lum = clamp((1 - r * 0.45) * (0.8 - (p.z - ag.zOffset) * 0.38), 0.32, 1.1) * depthDim;
              const ch = r < 0.3 ? "#" : dirChar(sx - tailPrevX, sy - tailPrevY, "~");
              const color = computeLitRGB(0.45 + r * 0.55, 0.3 + lum * 0.85, ta, oldPal, newPal, r > 0.5, (1 - r) * 0.1);
              if (plotLit(p.x, p.y, p.z, lum, color, scale, roamX, roamY, ch)) {
                charCount++;
              }
            }
            tailPrevX = sx;
            tailPrevY = sy;
          }
        } else {
          const vy =
            Math.cos(t * ag.freqY * 1.4 + ag.phase) * ag.ampY * ag.freqY * 1.4 -
            Math.sin(t * 0.27 + ag.phase) * 0.06 * 0.27;
          const swimPhase = Math.cos(t * ag.freqX + ag.phase);

          // The head leads: the fish faces right while swimming right and turns around near the screen edges.
          const turnK = clamp((0.35 - swimPhase) / 0.7, 0, 1);
          const turnAngle = Math.PI - Math.PI * turnK * turnK * (3 - 2 * turnK) + Math.sin(ta * 0.6) * 0.22;
          // nose pitches up while rising and down while sinking
          const pitchAngle = clamp(vy * 1.4, -0.38, 0.38);

          const cp = Math.cos(pitchAngle);
          const sp = Math.sin(pitchAngle);
          const cyw = Math.cos(turnAngle);
          const syw = Math.sin(turnAngle);

          // travelling body wave, strongest toward the tail
          const waveLocal = (fx: number, fy: number, fz: number): Vec3 => {
            const spineLag = Math.max(0, fx + 0.25);
            return [fx, fy, fz + Math.sin(ta * 4.6 - spineLag * 5.4) * (0.09 * Math.pow(spineLag, 1.25))];
          };
          // pitch, then heading (rotation only; also used for surface normals)
          const rotFish = (x: number, y: number, z: number): Vec3 => {
            const py = y * cp - x * sp;
            const px = y * sp + x * cp;
            return [px * cyw - z * syw, py, px * syw + z * cyw];
          };

          // Body: u runs snout (0) to tail base (1), th goes around the cross-section
          const bodyLocal = (u: number, th: number): Vec3 => {
            const fx = -0.44 + u * 0.62;
            const archY = -0.04 * Math.sin(u * Math.PI);
            const halfH = 0.165 * Math.sin(Math.pow(u, 0.65) * Math.PI) * (1 - 0.2 * u);
            const halfW = halfH * 0.58;
            return waveLocal(fx, archY + Math.sin(th) * halfH, Math.cos(th) * halfW);
          };

          const BU = Math.ceil(52 * dens);
          const BT = Math.ceil(36 * dens);
          for (let iu = 0; iu <= BU; iu++) {
            const u = 0.015 + 0.975 * (iu / BU);
            for (let ith = 0; ith < BT; ith++) {
              const th = (ith / BT) * Math.PI * 2;
              const p0 = bodyLocal(u, th);
              const pu = bodyLocal(u + 0.01, th);
              const pt = bodyLocal(u, th + 0.05);

              const tux = pu[0] - p0[0];
              const tuy = pu[1] - p0[1];
              const tuz = pu[2] - p0[2];
              const tvx = pt[0] - p0[0];
              const tvy = pt[1] - p0[1];
              const tvz = pt[2] - p0[2];
              const n = rotFish(tuy * tvz - tuz * tvy, tuz * tvx - tux * tvz, tux * tvy - tuy * tvx);
              const q = rotFish(p0[0], p0[1], p0[2]);

              // glossy scales and a dark gill crease behind the head
              const tex = (0.5 + 0.5 * Math.sin(u * 68 + Math.sin(th * 2) * 1.4)) * Math.sin(th * 11 + u * 6);
              let lum = lightSurface(n[0], n[1], n[2], 0.4, 0.65) + tex * 0.07;
              if (Math.abs(u - 0.21) < 0.012) lum *= 0.55;
              lum *= depthDim;

              const color = computeLitRGB(
                u * 0.35,
                0.3 + clamp(lum, 0, 1.2) * 0.85,
                ta,
                oldPal,
                newPal,
                false,
                clamp((lum - 0.95) * 1.2, 0, 0.6)
              );
              if (plotLit(q[0], q[1], q[2] + ag.zOffset, lum, color, scale, roamX, roamY)) {
                charCount++;
              }
            }
          }

          // Eyes
          for (const side of [1, -1]) {
            const p = waveLocal(-0.385, -0.012, side * 0.06);
            const q = rotFish(p[0], p[1], p[2]);
            if (plotLit(q[0], q[1], q[2] + ag.zOffset, 1, "#ffffff", scale, roamX, roamY, "@", 0.05)) {
              charCount++;
            }
          }

          // Tail fin: a translucent veil with brighter rays and a glowing scalloped edge
          const TAIL_RAYS = Math.ceil(40 * dens);
          const RAY_STEPS = Math.ceil(28 * dens);
          for (let ir = 0; ir < TAIL_RAYS; ir++) {
            const a = (ir / (TAIL_RAYS - 1)) * 2 - 1;
            const spreadAngle = a * 1.28;
            const isRay = ir % 3 === 0;
            let prevX = NaN;
            let prevY = NaN;

            for (let is = 0; is <= RAY_STEPS; is++) {
              const r = is / RAY_STEPS;
              const scallop = 1 + 0.06 * Math.cos(a * Math.PI * 12) * Math.pow(r, 2);
              const rayLen = 0.88 * r * scallop;

              const flutter = Math.sin(ta * 4.2 - r * 4.6 + a * 3.2) * (0.15 * r * r);
              const droop = 0.12 * r * r * (1 - 0.3 * Math.cos(a * Math.PI));

              const fx = 0.16 + Math.cos(spreadAngle * 0.72) * rayLen;
              const fy = Math.sin(spreadAngle) * rayLen * 0.78 + droop;
              const fz = flutter + Math.sin(a * 5 + r * 3) * 0.05 * r;

              const p = waveLocal(fx, fy, fz);
              const q = rotFish(p[0], p[1], p[2]);
              const pz = q[2] + ag.zOffset;
              const sx = projX(q[0], pz, scale, roamX);
              const sy = projY(q[1], pz, scale, roamY);

              if (is > 0) {
                const rib = Math.abs(Math.cos(a * Math.PI * 14));
                const depthTerm = clamp(0.95 - (pz - ag.zOffset) * 0.3, 0.55, 1.2);
                const edge = r > 0.93;
                const base = isRay ? 0.92 - r * 0.3 : 0.34 + 0.3 * (1 - r) + 0.1 * rib;
                const lum = (edge ? 0.95 : base) * depthTerm * depthDim;

                const ch = edge ? "*" : isRay ? dirChar(sx - prevX, sy - prevY) : undefined;
                const color = computeLitRGB(
                  0.32 + r * 0.68,
                  0.3 + lum * 0.9,
                  ta,
                  oldPal,
                  newPal,
                  r > 0.5,
                  edge ? 0.35 : 0
                );
                if (plotLit(q[0], q[1], pz, lum, color, scale, roamX, roamY, ch)) {
                  charCount++;
                }
              }
              prevX = sx;
              prevY = sy;
            }
          }

          // Dorsal and anal fins
          for (const up of [1, -1]) {
            const RAYS = Math.ceil(22 * dens);
            const STEPS = Math.ceil(16 * dens);
            for (let ir = 0; ir < RAYS; ir++) {
              const s = ir / (RAYS - 1);
              const isRay = ir % 3 === 0;
              let prevX = NaN;
              let prevY = NaN;

              for (let is = 0; is <= STEPS; is++) {
                const r = is / STEPS;
                const finLen = (up === 1 ? 0.52 : 0.58) * Math.sin(Math.pow(s, 0.7) * Math.PI) * r;
                const sweepX = -0.15 + s * 0.38 + r * (0.28 + s * 0.22);
                const sweepY = -up * (0.11 + finLen * 0.85) + 0.06 * r * r;
                const sweepZ = Math.sin(ta * 4.4 - (s + r) * 4.2 + up) * 0.12 * r;

                const p = waveLocal(sweepX, sweepY, sweepZ);
                const q = rotFish(p[0], p[1], p[2]);
                const pz = q[2] + ag.zOffset;
                const sx = projX(q[0], pz, scale, roamX);
                const sy = projY(q[1], pz, scale, roamY);

                if (is > 0) {
                  const depthTerm = clamp(0.95 - (pz - ag.zOffset) * 0.3, 0.55, 1.2);
                  const edge = r > 0.9;
                  const base = isRay ? 0.9 - r * 0.28 : 0.34 + 0.26 * (1 - r);
                  const lum = (edge ? 0.9 : base) * depthTerm * depthDim;
                  const ch = edge ? "." : isRay ? dirChar(sx - prevX, sy - prevY) : undefined;
                  const color = computeLitRGB(0.25 + (s + r) * 0.38, 0.3 + lum * 0.9, ta, oldPal, newPal, true, edge ? 0.3 : 0);
                  if (plotLit(q[0], q[1], pz, lum, color, scale, roamX, roamY, ch)) {
                    charCount++;
                  }
                }
                prevX = sx;
                prevY = sy;
              }
            }
          }

          // Pelvic streamers: two long thin filaments trailing from the belly
          for (const side of [1, -1]) {
            const ST = Math.ceil(26 * dens);
            let prevX = NaN;
            let prevY = NaN;
            for (let is = 0; is <= ST; is++) {
              const s = is / ST;
              const fx = -0.22 + 0.6 * s + 0.03 * Math.sin(ta * 3.0 - s * 5);
              const fy = 0.11 + 0.26 * s - 0.08 * s * s + 0.03 * Math.sin(ta * 3.2 - s * 6) * s;
              const fz = side * (0.05 + 0.04 * s) + 0.05 * Math.sin(ta * 3.6 - s * 7) * s;

              const p = waveLocal(fx, fy, fz);
              const q = rotFish(p[0], p[1], p[2]);
              const pz = q[2] + ag.zOffset;
              const sx = projX(q[0], pz, scale, roamX);
              const sy = projY(q[1], pz, scale, roamY);
              if (is > 0) {
                const lum = (0.9 - s * 0.4) * depthDim;
                const ch = s > 0.9 ? "." : dirChar(sx - prevX, sy - prevY);
                const color = computeLitRGB(0.3 + s * 0.4, 0.3 + lum * 0.9, ta, oldPal, newPal, true, 0.2);
                if (plotLit(q[0], q[1], pz, lum, color, scale, roamX, roamY, ch)) {
                  charCount++;
                }
              }
              prevX = sx;
              prevY = sy;
            }
          }

          // Pectoral fins: small fans that flutter just behind the gills
          for (const side of [1, -1]) {
            const RAYS_P = 7;
            const STEPS_P = Math.ceil(9 * dens);
            for (let ir = 0; ir < RAYS_P; ir++) {
              const ang = -0.55 + (ir / (RAYS_P - 1)) * 1.5;
              for (let is = 1; is <= STEPS_P; is++) {
                const r = is / STEPS_P;
                const flutter = Math.sin(ta * 9 - r * 3 + ir * 0.4) * 0.05 * r;
                const fx = -0.2 + Math.cos(ang) * 0.17 * r;
                const fy = 0.035 + Math.sin(ang) * 0.17 * r;
                const fz = side * (0.085 + 0.1 * r + flutter);

                const p = waveLocal(fx, fy, fz);
                const q = rotFish(p[0], p[1], p[2]);
                const lum = (0.5 + 0.35 * (1 - r)) * depthDim;
                const color = computeLitRGB(0.2 + r * 0.2, 0.3 + lum * 0.9, ta, oldPal, newPal, true, r > 0.85 ? 0.3 : 0);
                if (plotLit(q[0], q[1], q[2] + ag.zOffset, lum, color, scale, roamX, roamY)) {
                  charCount++;
                }
              }
            }
          }
        }
      }

      if (t - lastGlintTime > 0.26 && agentCenters.length > 0) {
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
            const col = `rgba(240, 249, 255, ${fade.toFixed(2)})`;
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

      // Soft glow: a faint dot in every empty cell touching a creature (creatures are the only
      // things drawn with z < 20; stars and rain sit further back).
      for (let r = 1; r < rows - 1; r++) {
        for (let c = 1; c < cols - 1; c++) {
          const idx = r * cols + c;
          if (charBuffer[idx]) continue;
          let src = -1;
          if (zBuffer[idx - 1] < 20) src = idx - 1;
          else if (zBuffer[idx + 1] < 20) src = idx + 1;
          else if (zBuffer[idx - cols] < 20) src = idx - cols;
          else if (zBuffer[idx + cols] < 20) src = idx + cols;
          if (src < 0) continue;
          const m = colorBuffer[src].match(/\d+/g);
          if (!m || m.length < 3) continue;
          charBuffer[idx] = ".";
          colorBuffer[idx] = `rgba(${m[0]},${m[1]},${m[2]},0.30)`;
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
      ctx.fillStyle = "rgba(186, 208, 235, 0.55)";
      const hudText = `omnilog.ascii  |  ${mode}.3d (x5)  |  theme: ${activePal.name.toLowerCase()}  |  fx: ${amb}  |  chars ${charCount}`;
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
          top: 0,
          left: 0,
          width: "100vw",
          height: "100vh",
          pointerEvents: "none",
          zIndex: 1,
          opacity: 0.92,
        }}
      />

      <div
        style={{
          position: "fixed",
          bottom: 14,
          right: 18,
          zIndex: 9999,
          display: "flex",
          flexWrap: "wrap",
          justifyContent: "flex-end",
          maxWidth: "calc(100vw - 36px)",
          gap: 6,
          padding: "5px 10px",
          borderRadius: 18,
          background: "rgba(8, 12, 22, 0.85)",
          backdropFilter: "blur(14px)",
          border: "1px solid rgba(255,255,255,0.16)",
          fontFamily: "monospace",
          fontSize: 11,
          color: "#cbd5e1",
        }}
      >
        <button
          type="button"
          onClick={() => {
            setAutoRoute(false);
            setManualPreset("jellyfish");
          }}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: preset === "jellyfish" ? "rgba(56, 189, 248, 0.24)" : "transparent",
            color: preset === "jellyfish" ? "#7dd3fc" : "#94a3b8",
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
            setManualPreset("betta");
          }}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: preset === "betta" ? "rgba(251, 146, 60, 0.24)" : "transparent",
            color: preset === "betta" ? "#fdba74" : "#94a3b8",
            border: preset === "betta" ? "1px solid rgba(251,146,60,0.45)" : "1px solid transparent",
            cursor: "pointer",
          }}
        >
          ● 3D Betta (x5)
        </button>
        <button
          type="button"
          onClick={() => {
            setAutoRoute(false);
            setManualPreset("manta");
          }}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: preset === "manta" ? "rgba(45, 212, 191, 0.22)" : "transparent",
            color: preset === "manta" ? "#5eead4" : "#94a3b8",
            border: preset === "manta" ? "1px solid rgba(45,212,191,0.45)" : "1px solid transparent",
            cursor: "pointer",
          }}
        >
          ● 3D Manta (x5)
        </button>
        <button
          type="button"
          onClick={cycleAmbient}
          style={{
            padding: "3px 9px",
            borderRadius: 999,
            background: ambient !== "off" ? "rgba(52, 211, 153, 0.20)" : "rgba(255,255,255,0.05)",
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
            background: "rgba(255,255,255,0.08)",
            color: "#f8fafc",
            border: "1px solid rgba(255,255,255,0.16)",
            cursor: "pointer",
          }}
        >
          ✦ Theme: {PALETTES[paletteIdx % PALETTES.length].name}
        </button>
      </div>
    </>
  );
}