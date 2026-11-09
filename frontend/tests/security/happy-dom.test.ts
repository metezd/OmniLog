// The component tests run in happy-dom. Older versions of it ran the scripts of a page, which made
// it possible to run code on the machine of the developer (for example CVE-2025-61927). The
// settings in vitest.config.mts turn that off, and these tests fail if it is ever turned on again.
import { afterEach, describe, expect, it } from "vitest";

declare global {
  var __ranFromPage: string | undefined;
}

afterEach(() => {
  delete globalThis.__ranFromPage;
  document.body.replaceChildren();
});

// Both tests were checked the other way round: with the settings turned on they fail. Two more
// ideas (a script inside innerHTML, a javascript: link) did not fail even then, so they are not here.
describe("happy-dom does not run code that comes from a page", () => {
  it("does not run the text of a script element", () => {
    const script = document.createElement("script");
    script.textContent = "globalThis.__ranFromPage = 'script'";
    document.body.appendChild(script);

    expect(globalThis.__ranFromPage).toBeUndefined();
  });

  it("does not run an inline event handler", () => {
    const image = document.createElement("img");
    image.setAttribute("onerror", "globalThis.__ranFromPage = 'onerror'");
    document.body.appendChild(image);
    image.dispatchEvent(new Event("error"));

    expect(globalThis.__ranFromPage).toBeUndefined();
  });
});
