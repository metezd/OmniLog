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
  "no-restricted-properties",
]);

const WARNING = 1;
const ERROR = 2;

let eslint: ESLint;

beforeAll(() => {
  eslint = new ESLint({ cwd: process.cwd() });
});

type Finding = { severity: number; message: string };

async function securityFindings(code: string): Promise<Finding[]> {
  const filePath = path.join(process.cwd(), "src", "security-fixture.tsx");
  const [result] = await eslint.lintText(code, { filePath });
  return result.messages
    .filter((message) => message.ruleId !== null && SECURITY_RULES.has(message.ruleId))
    .map((message) => ({ severity: message.severity, message: message.message }));
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

// The old Semgrep rule reported every setItem call on web storage as a warning. A warning does
// not fail `npm run lint`, but it must stay visible.
const WARNING_CODE: Array<[string, string]> = [
  ["a theme in localStorage", `export const a = () => { localStorage.setItem("theme", "dark"); };`],
  [
    "a tab name in sessionStorage",
    `export const a = (tab: string) => { sessionStorage.setItem("lastTab", tab); };`,
  ],
];

const GOOD_CODE: Array<[string, string]> = [
  ["reading from localStorage", `export const a = () => localStorage.getItem("theme");`],
  ["a public API URL", `export const a = process.env.NEXT_PUBLIC_API_URL;`],
  [
    "target=_blank with rel",
    `export const A = () => <a href="https://example.com" target="_blank" rel="noopener noreferrer">x</a>;`,
  ],
];

describe("the ESLint security rules", () => {
  it.each(BAD_CODE)("report %s as an error", async (_name, code, expected) => {
    const findings = await securityFindings(code);

    expect(findings.some((finding) => finding.severity === ERROR)).toBe(true);
    expect(findings.some((finding) => expected.test(finding.message))).toBe(true);
  }, 60_000);

  it.each(WARNING_CODE)("report %s as a warning only", async (_name, code) => {
    const findings = await securityFindings(code);

    expect(findings.length).toBeGreaterThan(0);
    expect(findings.every((finding) => finding.severity === WARNING)).toBe(true);
  }, 60_000);

  it.each(GOOD_CODE)("accept %s", async (_name, code) => {
    expect(await securityFindings(code)).toEqual([]);
  }, 60_000);
});
