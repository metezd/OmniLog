import { screen } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";

/** How a field is filled: `paste` puts the whole value in at once, `type` presses one key at a time. */
export type FillMode = "paste" | "type";

/**
 * A user for a test. user-event waits one timer tick between two actions, even with its default
 * delay of 0. `delay: null` removes that wait, and the tests of the forms were about 18% faster.
 */
export function setupUser(): UserEvent {
  return userEvent.setup({ delay: null });
}

/**
 * Fill the field with this label. The default is `paste`: it makes one input event with the whole
 * value, which is enough for a test that only looks at the value that the form sends. A test that
 * is about the typing itself passes `type` (key by key, with a keydown and a keyup for each key),
 * and is about 3 times slower for a value of 15 characters.
 */
export async function fillField(user: UserEvent, label: string, value: string, mode: FillMode = "paste") {
  const field = screen.getByLabelText(label);
  if (mode === "type") {
    await user.type(field, value);
    return;
  }
  await user.click(field); // paste goes to the focused element
  await user.paste(value);
}
