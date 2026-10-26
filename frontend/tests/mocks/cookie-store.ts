// A fake of the cookie store that Next.js gives from `await cookies()`. Tests of server code
// replace next/headers with it:
//
//   vi.mock("next/headers", async () => {
//     const { cookieStore } = await import("../../mocks/cookie-store");
//     return { cookies: async () => cookieStore };
//   });

export type SetOptions = {
  httpOnly?: boolean;
  secure?: boolean;
  sameSite?: "lax" | "strict" | "none" | boolean;
  path?: string;
  maxAge?: number;
  expires?: Date;
};

class FakeCookieStore {
  private values = new Map<string, string>();
  /** The options of the last set() call for each cookie, for the checks of the tests. */
  readonly options = new Map<string, SetOptions>();

  get(name: string) {
    const value = this.values.get(name);
    return value === undefined ? undefined : { name, value };
  }

  has(name: string) {
    return this.values.has(name);
  }

  set(name: string, value: string, options: SetOptions = {}) {
    this.values.set(name, value);
    this.options.set(name, options);
  }

  delete(name: string) {
    this.values.delete(name);
    this.options.delete(name);
  }

  clear() {
    this.values.clear();
    this.options.clear();
  }

  get names() {
    return [...this.values.keys()];
  }
}

export const cookieStore = new FakeCookieStore();
