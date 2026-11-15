// @vitest-environment node
//
// The security rules in eslint.config.mjs replace the frontend rules of the old Semgrep setup.
// These tests lint a few lines of bad code and fail if a rule stops reporting it, so a rule
// cannot be removed or broken without anyone noticing.
import path from "node:path";

import { ESLint } from "eslint";
import { beforeAll, describe, expect, it } from "vitest";

const SECURITY_RULES = new Set([
  "no-eval",
  "no-implied-eval",
  "no-new-func",
  "react/jsx-no-target-blank",
  "no-restricted-syntax",
]);

let eslint: ESLint;

beforeAll(() => {
  eslint = new ESLint({ cwd: process.cwd() });
});

async function securityMessages(code: string): Promise<string[]> {
  const filePath = path.join(process.cwd(), "src", "security-fixture.tsx");
  const [result] = await eslint.lintText(code, { filePath });
  return result.messages
    .filter((message) => message.ruleId !== null && SECURITY_RULES.has(message.ruleId))
    .map((message) => message.message);
}

const BAD_CODE: Array<[string, string, RegExp]> = [
  ["eval()", `export const a = () => eval("1");`, /eval/i],
  ["new Function()", `export const a = () => new Function("return 1");`, /Function/],
  ["setTimeout with a string", `export const a = () => setTimeout("go()", 0);`, /eval/i],
  [
    "dangerouslySetInnerHTML",
    `export const A = ({ h }: { h: string }) => <div dangerouslySetInnerHTML={{ __html: h }} />;`,
    /dangerouslySetInnerHTML/,
  ],
  [
    "an innerHTML assignment",
    `export const a = (el: HTMLElement, h: string) => { el.innerHTML = h; };`,
    /innerHTML/,
  ],
  [
    "a token in localStorage",
    `export const a = () => { localStorage.setItem("auth_token", "x"); };`,
    /localStorage/,
  ],
  [
    "a token variable in sessionStorage",
    `export const a = (token: string) => { sessionStorage.setItem("k", token); };`,
    /sessionStorage/,
  ],
  [
    "a secret in a NEXT_PUBLIC_ variable",
    `export const a = process.env.NEXT_PUBLIC_API_SECRET;`,
    /NEXT_PUBLIC_/,
  ],
  [
    "target=_blank without rel",
    `export const A = () => <a href="https://example.com" target="_blank">x</a>;`,
    /target="_blank"/,
  ],
];

const GOOD_CODE: Array<[string, string]> = [
  ["a theme in localStorage", `export const a = () => { localStorage.setItem("theme", "dark"); };`],
  ["a public API URL", `export const a = process.env.NEXT_PUBLIC_API_URL;`],
  [
    "target=_blank with rel",
    `export const A = () => <a href="https://example.com" target="_blank" rel="noopener noreferrer">x</a>;`,
  ],
];

describe("the ESLint security rules", () => {
  it.each(BAD_CODE)("report %s", async (_name, code, expected) => {
    const messages = await securityMessages(code);

    expect(messages.length).toBeGreaterThan(0);
    expect(messages.some((message) => expected.test(message))).toBe(true);
  }, 60_000);

  it.each(GOOD_CODE)("accept %s", async (_name, code) => {
    expect(await securityMessages(code)).toEqual([]);
  }, 60_000);
});
