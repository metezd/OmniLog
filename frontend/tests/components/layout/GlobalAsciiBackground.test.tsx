import { cleanup, render } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import GlobalAsciiBackground from "@/components/layout/background/GlobalAsciiBackground";

vi.mock("next/navigation", () => ({ usePathname: () => "/" }));

type Listener = (event: { matches: boolean }) => void;

/** A canvas context whose methods do nothing, and that records every text it draws. */
function fakeContext(texts: string[]) {
  const target: Record<string, unknown> = {
    fillText: (text: string) => texts.push(text),
    measureText: () => ({ width: 8 }),
    createLinearGradient: () => ({ addColorStop: () => {} }),
    createRadialGradient: () => ({ addColorStop: () => {} }),
  };
  return new Proxy(target, {
    get: (object, key: string) => (key in object ? object[key] : () => {}),
    set: () => true,
  });
}

/** prefers-reduced-motion with a value the test can change later. */
function motionSetting(reduce: boolean) {
  const listeners: Listener[] = [];
  const query = {
    matches: reduce,
    addEventListener: (_type: string, listener: Listener) => listeners.push(listener),
    removeEventListener: vi.fn(),
  };
  vi.stubGlobal("matchMedia", vi.fn(() => query));
  return {
    change(next: boolean) {
      query.matches = next;
      listeners.forEach((listener) => listener({ matches: next }));
    },
  };
}

let frames: FrameRequestCallback[];
let texts: string[];

/** Runs the frames that are waiting, as the browser would, at most `count` of them. */
function runFrames(count: number) {
  for (let i = 0; i < count && frames.length > 0; i++) {
    const frame = frames.shift()!;
    // A frame time after the start, as in a browser (the component counts from performance.now())
    frame(performance.now() + 16 * (i + 1));
  }
}

beforeEach(() => {
  frames = [];
  texts = [];
  vi.stubGlobal("requestAnimationFrame", vi.fn((callback: FrameRequestCallback) => frames.push(callback)));
  vi.stubGlobal("cancelAnimationFrame", vi.fn(() => frames.splice(0)));
  vi.spyOn(HTMLCanvasElement.prototype, "getContext").mockImplementation(
    () => fakeContext(texts) as unknown as CanvasRenderingContext2D,
  );
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("GlobalAsciiBackground and reduced motion (#429)", () => {
  it("keeps animating when the user allows motion", () => {
    motionSetting(false);
    render(<GlobalAsciiBackground />);

    runFrames(3);

    expect(frames).toHaveLength(1); // every frame asks for the next one
  });

  it("draws one still frame and stops with prefers-reduced-motion: reduce", () => {
    motionSetting(true);
    render(<GlobalAsciiBackground />);

    runFrames(1);

    expect(frames).toHaveLength(0);
  });

  it("follows a change of the setting", () => {
    const setting = motionSetting(false);
    render(<GlobalAsciiBackground />);
    runFrames(1);

    setting.change(true);
    runFrames(1);
    expect(frames).toHaveLength(0);

    setting.change(false);
    runFrames(1);
    expect(frames).toHaveLength(1);
  });

  it("draws no debug line outside development", () => {
    motionSetting(false);
    render(<GlobalAsciiBackground />);

    runFrames(2);

    expect(texts.some((text) => text.includes("omnilog.ascii"))).toBe(false);
  });
});
