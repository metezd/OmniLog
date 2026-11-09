// The redirect() of Next.js works by throwing a special error. In tests it throws this one, so a
// test can see where the redirect went. Use it like this:
//
//   vi.mock("next/navigation", async () => await import("../../mocks/next-navigation"));
//   await expect(action()).rejects.toMatchObject({ url: "/library" });

export class RedirectSignal extends Error {
  constructor(readonly url: string) {
    super(`NEXT_REDIRECT ${url}`);
    this.name = "RedirectSignal";
  }
}

export function redirect(url: string): never {
  throw new RedirectSignal(url);
}
