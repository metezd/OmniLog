import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

// Words that mark a value as a credential. Used to find tokens written to browser storage.
const CREDENTIAL_WORDS = "token|jwt|secret|passw|credential";
// A NEXT_PUBLIC_ variable is sent to the browser, so its name must not look like a secret.
const PUBLIC_SECRET_NAME = "^NEXT_PUBLIC_\\w*(SECRET|PASSWORD|PRIVATE|API_KEY)";
const STORAGE_NAMES = "^(localStorage|sessionStorage)$";
const STORAGE_SET_ITEM =
  `CallExpression[callee.property.name='setItem']:matches(` +
  `[callee.object.name=/${STORAGE_NAMES}/], [callee.object.property.name=/${STORAGE_NAMES}/])`;

// Security rules. They replace the frontend rules of the old Semgrep setup. Next.js turns
// react/jsx-no-target-blank off and does not enable the eval rules, so they are set here.
// A rule can be turned off for one line with a comment that gives the reason, for example:
//   // eslint-disable-next-line no-restricted-syntax -- the HTML is sanitized above
const STORAGE_WARNING =
  "Do not keep an auth token in web storage: any injected script can read it. Check that this value is not a token or secret.";

const securityRules = {
  files: ["**/*.{js,jsx,mjs,ts,tsx}"],
  rules: {
    "no-eval": "error",
    "no-implied-eval": "error",
    "no-new-func": "error",
    "react/jsx-no-target-blank": "error",
    // The old Semgrep rule javascript-token-in-local-storage reported every setItem call as a
    // warning. This keeps that. A value that is named like a credential is an error, see below.
    "no-restricted-properties": [
      "warn",
      { object: "localStorage", property: "setItem", message: STORAGE_WARNING },
      { object: "sessionStorage", property: "setItem", message: STORAGE_WARNING },
    ],
    "no-restricted-syntax": [
      "error",
      {
        selector: "JSXAttribute[name.name='dangerouslySetInnerHTML']",
        message: "dangerouslySetInnerHTML can introduce XSS. Render the content with React instead.",
      },
      {
        selector:
          "AssignmentExpression[left.type='MemberExpression'][left.property.name=/^(innerHTML|outerHTML)$/]",
        message: "Assigning innerHTML or outerHTML can introduce XSS. Use textContent or React.",
      },
      {
        selector:
          `${STORAGE_SET_ITEM} > :matches(` +
          `Literal.arguments[value=/${CREDENTIAL_WORDS}/i], ` +
          `Identifier.arguments[name=/${CREDENTIAL_WORDS}/i], ` +
          `MemberExpression.arguments[property.name=/${CREDENTIAL_WORDS}/i])`,
        message:
          "Do not store a token or secret in localStorage or sessionStorage. Any script on the page can read it. Use an HttpOnly cookie.",
      },
      {
        selector: `:matches(Identifier[name=/${PUBLIC_SECRET_NAME}/i], Literal[value=/${PUBLIC_SECRET_NAME}/i])`,
        message: "NEXT_PUBLIC_ variables are sent to the browser. Do not put secrets in them.",
      },
    ],
  },
};

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  securityRules,
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
  ]),
]);

export default eslintConfig;
