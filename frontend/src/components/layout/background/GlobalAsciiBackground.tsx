"use client";

import React, { useEffect, useRef, useState } from "react";
import { usePathname } from "next/navigation";

export type PresetKey = "butterfly" | "jellyfish" | "dragonfly" | "koi" | "frog" | "bird" | "crab";

interface PresetConfig {
  label: string;
  dotColor: string;
  palette: Record<string, string>;
  frames: string[][];
  speed: number;
}

export const PRESETS: Record<PresetKey, PresetConfig> = {
  butterfly: {
    label: "Butterfly",
    dotColor: "#38bdf8",
    speed: 1.1,
    palette: {
      "#": "#0284c7",
      "@": "#38bdf8",
      "*": "#7dd3fc",
      "+": "#e0f2fe",
      ":": "#f472b6",
    },
    frames: [
      [
        "  .###.      .###.  ",
        " .#@@@#.    .#@@@#. ",
        ".#@@**@#.  .#@**@@#.",
        "#@**++*@#.+#@*++**@#",
        "#@*+::+*@##@*+::+*@#",
        ".#@@**@######@**@@#.",
        " .#@@@#.+##+.#@@@#. ",
        "  .###..#@@#..###.  ",
        "    .#@@@##@@@#.    ",
        "    .#@@*##*@@#.    ",
        "     .###..###.     ",
      ],
      [
        "    .##.    .##.    ",
        "   .#@@#.  .#@@#.   ",
        "   .#@*@#.+#@*@#.   ",
        "    .#@*#::#*@#.    ",
        "    .#@@#::#@@#.    ",
        "     .###::###.     ",
        "     .#@@##@@#.     ",
        "      .##..##.      ",
        "      .#.  .#.      ",
        "                    ",
        "                    ",
      ],
    ],
  },
  jellyfish: {
    label: "Jellyfish",
    dotColor: "#c084fc",
    speed: 0.75,
    palette: {
      "#": "#9333ea",
      "@": "#c084fc",
      "*": "#f3e8ff",
      "~": "#e879f9",
      ":": "#818cf8",
    },
    frames: [
      [
        "     .########.     ",
        "   .##@@@@@@@@##.   ",
        "  .#@@********@@#.  ",
        " .#@************@#. ",
        " #@***@@@@@@@@***@# ",
        " ################## ",
        "   ~  :  ~  :  ~  : ",
        "  ~   :   ~  :  ~   ",
        "   ~  :  ~   : ~  : ",
        "    ~  :  ~  :  ~   ",
      ],
      [
        "    .##########.    ",
        "  .##@@@@@@@@@@##.  ",
        " .#@@**********@@#. ",
        " #@****@@@@@@****@# ",
        "  .##############.  ",
        "    ~ : ~ : ~ : ~   ",
        "   ~  : ~  : ~  :   ",
        "    ~ :  ~ :  ~ :   ",
        "   ~   :  ~  :  ~   ",
        "    ~   :  ~   :    ",
      ],
    ],
  },
  dragonfly: {
    label: "Dragonfly",
    dotColor: "#2dd4bf",
    speed: 1.45,
    palette: {
      "#": "#0d9488",
      "@": "#2dd4bf",
      "*": "#99f6e4",
      "+": "#f0fdfa",
    },
    frames: [
      [
        "       .@@@@.       ",
        "*******######*******",
        " .+++++######+++++. ",
        "*******######*******",
        "       .####.       ",
        "       .####.       ",
        "        .##.        ",
        "        .##.        ",
        "        .++.        ",
      ],
      [
        "       .@@@@.       ",
        " .*****######*****. ",
        "+++++++######+++++++",
        " .*****######*****. ",
        "       .####.       ",
        "       .####.       ",
        "        .##.        ",
        "        .##.        ",
        "        .++.        ",
      ],
    ],
  },
  koi: {
    label: "Koi",
    dotColor: "#fb923c",
    speed: 0.95,
    palette: {
      "#": "#ea580c",
      "@": "#fb923c",
      "*": "#fed7aa",
      "+": "#fff7ed",
    },
    frames: [
      [
        "       .#####.      ",
        "     .##@@@@@##.    ",
        "    .#@@*****@@#.   ",
        " .++#@@@*****@@@#++ ",
        "    .#@@*****@#..   ",
        "     .##@@@@@#.     ",
        "       .#####.      ",
        "      .##...##.     ",
        "     .#.     .#.    ",
      ],
      [
        "       .#####.      ",
        "     .##@@@@@##.    ",
        "    .#@@*****@@#.   ",
        " ++..#@@*****@@@#.. ",
        "    .#@@*****@@@#++ ",
        "     .##@@@@@#.     ",
        "       .#####.      ",
        "        .##..##.    ",
        "         .#.  .#.   ",
      ],
    ],
  },
  frog: {
    label: "Frog",
    dotColor: "#4ade80",
    speed: 0.85,
    palette: {
      "#": "#16a34a",
      "@": "#4ade80",
      "*": "#bbf7d0",
      "+": "#f0fdf4",
    },
    frames: [
      [
        "  .@@@.      .@@@.  ",
        " .#***#.    .#***#. ",
        " .#@@@########@@@#. ",
        ".#@@@@@@@@@@@@@@@@#.",
        "#@****@@@@@@@@****@#",
        "#@++++++++++++++++@#",
        ".#@@@@@@@@@@@@@@@@#.",
        "###..##########..###",
        "#.   .#.    .#.   .#",
      ],
      [
        "  .@@@.      .@@@.  ",
        " .#***#.    .#***#. ",
        " .#@@@########@@@#. ",
        ".#@@@@@@@@@@@@@@@@#.",
        "#@****@@@@@@@@****@#",
        " .#++++++++++++++#. ",
        ".##@@@@@@@@@@@@@@##.",
        "#..   .######.   ..#",
        "#      .++++.      #",
      ],
    ],
  },
  bird: {
    label: "Bird",
    dotColor: "#fbbf24",
    speed: 1.25,
    palette: {
      "#": "#d97706",
      "@": "#fbbf24",
      "*": "#fef3c7",
      "+": "#fffbeb",
    },
    frames: [
      [
        ".###.          .###.",
        "#@@@#.        .#@@@#",
        ".#@@*#. .@@. .#*@@#.",
        " .#@*###@@@@###*@#  ",
        "  .#####@@@@#####.  ",
        "    ...#@@@@#...    ",
        "       .+##+.       ",
        "      .++.++.       ",
      ],
      [
        "        .@@.        ",
        "      .#@@@@#.      ",
        "    .##@@@@@@##.    ",
        "  .#@@*#@@@@#*@@#.  ",
        " .#@*#. #@@# .#*@#. ",
        ".###.   .++.   .###.",
        "       .++++.       ",
        "                    ",
      ],
    ],
  },
  crab: {
    label: "Crab",
    dotColor: "#f43f5e",
    speed: 0.85,
    palette: {
      "#": "#e11d48",
      "@": "#f43f5e",
      "*": "#fecdd3",
      "+": "#fff1f2",
    },
    frames: [
      [
        " .###.        .###. ",
        ".#@@@# .****. #@@@#.",
        " .+#..#@@@@@@#..#+. ",
        "  .##############.  ",
        " .#@@@********@@@#. ",
        ". #@@@@@@@@@@@@@@# .",
        "# .##############. #",
        " .#. .#.    .#. .#. ",
      ],
      [
        ".###.          .###.",
        "#@@@#. .****. .#@@@#",
        " .+#..#@@@@@@#..#+. ",
        "  .##############.  ",
        " .#@@@********@@@#. ",
        "# #@@@@@@@@@@@@@@# #",
        "  .##############.  ",
        ".#. .#.      .#. .#.",
      ],
    ],
  },
};

function getRoutePreset(pathname: string): PresetKey {
  if (pathname.startsWith("/search")) return "dragonfly";
  if (pathname.startsWith("/library")) return "jellyfish";
  if (pathname.startsWith("/diary")) return "koi";
  if (pathname.startsWith("/lists")) return "bird";
  if (pathname.startsWith("/stats") || pathname.startsWith("/recommendations")) return "frog";
  if (pathname.startsWith("/login") || pathname.startsWith("/register") || pathname.startsWith("/friends")) return "crab";
  return "butterfly";
}

interface CellOffset {
  dx: number;
  dy: number;
  vx: number;
  vy: number;
}

interface Creature {
  x: number;
  y: number;
  vx: number;
  vy: number;
  frameOffset: number;
  scale: number;
  scatterCells: Record<string, CellOffset>;
}

interface BurstParticle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  char: string;
  color: string;
  alpha: number;
}

export default function GlobalAsciiBackground() {
  const pathname = usePathname() || "/";
  const canvasRef = useRef<HTMLCanvasElement | null>(null);

  const [manualPreset, setManualPreset] = useState<PresetKey>("butterfly");
  const [autoRoute, setAutoRoute] = useState(true);
  const [zoomed, setZoomed] = useState(false);

  const preset: PresetKey = autoRoute ? getRoutePreset(pathname) : manualPreset;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let animId: number;
    let width = (canvas.width = window.innerWidth);
    let height = (canvas.height = window.innerHeight);

    const cfg = PRESETS[preset];
    const creatures: Creature[] = [];
    const bursts: BurstParticle[] = [];
    const pointer = { x: -9999, y: -9999 };
    const paletteColors = Object.values(cfg.palette);

    // 7 well-spaced creatures (fast 60 FPS & clear visual layout like the demo)
    const spawnPositions = [
      { rx: 0.17, ry: 0.46, scale: 1.35 },
      { rx: 0.83, ry: 0.46, scale: 1.35 },
      { rx: 0.50, ry: 0.22, scale: 1.25 },
      { rx: 0.16, ry: 0.24, scale: 1.05 },
      { rx: 0.84, ry: 0.24, scale: 1.05 },
      { rx: 0.22, ry: 0.78, scale: 1.15 },
      { rx: 0.78, ry: 0.78, scale: 1.15 },
    ];

    spawnPositions.forEach((sp, i) => {
      const angle = (Math.PI * 2 * i) / spawnPositions.length + (Math.random() - 0.5) * 0.4;
      creatures.push({
        x: width * sp.rx,
        y: height * sp.ry,
        vx: Math.cos(angle) * cfg.speed,
        vy: Math.sin(angle) * cfg.speed * 0.8,
        frameOffset: i * 8,
        scale: sp.scale * (zoomed ? 1.4 : 1.0),
        scatterCells: {},
      });
    });

    const handleResize = () => {
      width = canvas.width = window.innerWidth;
      height = canvas.height = window.innerHeight;
    };

    const onPointerMove = (e: PointerEvent) => {
      pointer.x = e.clientX;
      pointer.y = e.clientY;
    };

    const triggerScatter = (clickX: number, clickY: number) => {
      const asciiPool = ["#", "@", "*", "+", "~", ":"];

      for (let i = 0; i < 24; i++) {
        const a = Math.random() * Math.PI * 2;
        const sp = 2 + Math.random() * 6;
        bursts.push({
          x: clickX,
          y: clickY,
          vx: Math.cos(a) * sp,
          vy: Math.sin(a) * sp,
          char: asciiPool[Math.floor(Math.random() * asciiPool.length)],
          color: paletteColors[Math.floor(Math.random() * paletteColors.length)],
          alpha: 1,
        });
      }

      creatures.forEach((c) => {
        const dx = c.x - clickX;
        const dy = c.y - clickY;
        const dist = Math.hypot(dx, dy) || 1;
        if (dist < 420) {
          const push = ((420 - dist) / 420) * 10;
          c.vx += (dx / dist) * push;
          c.vy += (dy / dist) * push;

          const frame = cfg.frames[0];
          for (let r = 0; r < frame.length; r++) {
            for (let col = 0; col < frame[r].length; col++) {
              if (frame[r][col] !== " ") {
                const key = `${r}-${col}`;
                c.scatterCells[key] = {
                  dx: 0,
                  dy: 0,
                  vx: (Math.random() - 0.5) * 18,
                  vy: (Math.random() - 0.5) * 18,
                };
              }
            }
          }
        }
      });
    };

    const onPointerDown = (e: PointerEvent) => {
      const target = e.target as HTMLElement | null;
      if (target?.closest("button, a, input, textarea, select, [role='button']")) {
        return;
      }
      triggerScatter(e.clientX, e.clientY);
    };

    window.addEventListener("resize", handleResize);
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("pointerdown", onPointerDown);

    let tick = 0;
    const render = () => {
      tick++;
      ctx.clearRect(0, 0, width, height);

      // Lightweight background dot grid (step 34 for fast rendering)
      const gridStep = 34;
      for (let gx = 18; gx < width; gx += gridStep) {
        for (let gy = 18; gy < height; gy += gridStep) {
          const dx = gx - pointer.x;
          const dy = gy - pointer.y;
          if (dx * dx + dy * dy < 19600) {
            ctx.fillStyle = cfg.dotColor + "66";
            ctx.fillRect(gx - 1, gy - 1, 2.5, 2.5);
          } else {
            ctx.fillStyle = "rgba(148, 163, 184, 0.08)";
            ctx.fillRect(gx, gy, 1.5, 1.5);
          }
        }
      }

      creatures.forEach((c) => {
        c.x += c.vx;
        c.y += c.vy;

        const speed = Math.hypot(c.vx, c.vy) || 1;
        if (speed > cfg.speed * 1.2) {
          c.vx *= 0.94;
          c.vy *= 0.94;
        }

        const topPad = 85;
        const sidePad = 75;
        const bottomPad = 75;
        if (c.x < sidePad) c.vx = Math.abs(c.vx);
        if (c.x > width - sidePad) c.vx = -Math.abs(c.vx);
        if (c.y < topPad) c.vy = Math.abs(c.vy);
        if (c.y > height - bottomPad) c.vy = -Math.abs(c.vy);

        const frameIdx = Math.floor((tick + c.frameOffset) / 14) % cfg.frames.length;
        const matrix = cfg.frames[frameIdx];
        const cellSize = Math.round(11 * c.scale);
        ctx.font = `bold ${cellSize}px monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";

        const rows = matrix.length;
        const cols = matrix[0].length;
        const startX = c.x - (cols * cellSize) / 2;
        const startY = c.y - (rows * cellSize) / 2;

        for (let r = 0; r < rows; r++) {
          for (let col = 0; col < cols; col++) {
            const ch = matrix[r][col];
            if (ch === " ") continue;

            const key = `${r}-${col}`;
            const offset = c.scatterCells[key];
            let ox = 0;
            let oy = 0;
            if (offset) {
              offset.dx += offset.vx;
              offset.dy += offset.vy;
              offset.dx *= 0.84;
              offset.dy *= 0.84;
              offset.vx *= 0.82;
              offset.vy *= 0.82;
              ox = offset.dx;
              oy = offset.dy;
            }

            const cx = startX + col * cellSize + ox;
            const cy = startY + r * cellSize + oy;
            const color = cfg.palette[ch] || cfg.dotColor;

            // Fast flat pixel backing + crisp text (zero shadowBlur overhead)
            ctx.fillStyle = color + "38";
            ctx.fillRect(cx - cellSize / 2, cy - cellSize / 2, cellSize - 1, cellSize - 1);

            ctx.fillStyle = color;
            ctx.fillText(ch, cx, cy);
          }
        }
      });

      for (let i = bursts.length - 1; i >= 0; i--) {
        const b = bursts[i];
        b.x += b.vx;
        b.y += b.vy;
        b.vx *= 0.92;
        b.vy *= 0.92;
        b.alpha -= 0.025;
        if (b.alpha <= 0) {
          bursts.splice(i, 1);
          continue;
        }
        ctx.globalAlpha = b.alpha;
        ctx.fillStyle = b.color;
        ctx.font = "bold 12px monospace";
        ctx.fillText(b.char, b.x, b.y);
        ctx.globalAlpha = 1;
      }

      animId = requestAnimationFrame(render);
    };

    render();

    return () => {
      window.removeEventListener("resize", handleResize);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("pointerdown", onPointerDown);
      cancelAnimationFrame(animId);
    };
  }, [preset, zoomed]);

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
          zIndex: 25,
          pointerEvents: "none",
        }}
        aria-hidden="true"
      />

      <div className="liquid-glass relative z-40 flex flex-wrap items-center justify-center gap-1.5 border-b border-white/10 bg-white/[0.02] px-4 py-2.5 backdrop-blur-md">
        {(Object.keys(PRESETS) as PresetKey[]).map((key) => {
          const item = PRESETS[key];
          const active = preset === key;
          return (
            <button
              key={key}
              type="button"
              onClick={() => {
                setAutoRoute(false);
                setManualPreset(key);
              }}
              className={`flex items-center gap-1.5 rounded-full border px-3 py-1 text-[11px] font-medium transition-all ${
                active
                  ? "border-white/25 bg-white/15 text-white shadow-lg"
                  : "border-white/10 bg-white/[0.03] text-slate-300 hover:border-white/20 hover:text-white"
              }`}
            >
              <span
                className="h-2 w-2 rounded-full"
                style={{
                  backgroundColor: item.dotColor,
                  boxShadow: active ? `0 0 8px ${item.dotColor}` : "none",
                }}
              />
              {item.label}
            </button>
          );
        })}

        <button
          type="button"
          onClick={() => setAutoRoute((a) => !a)}
          className="ml-1 rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 font-mono text-[10px] text-slate-300 hover:border-white/25 hover:text-white"
        >
          Auto-Route: {autoRoute ? "ON" : "OFF"}
        </button>
        <button
          type="button"
          onClick={() => setZoomed((z) => !z)}
          className="rounded-full border border-white/10 bg-white/[0.04] px-2.5 py-1 font-mono text-[10px] text-slate-300 hover:border-cyan-400/40 hover:text-white"
        >
          Grid: {zoomed ? "1.65x" : "1.0x"}
        </button>
      </div>
    </>
  );
}
