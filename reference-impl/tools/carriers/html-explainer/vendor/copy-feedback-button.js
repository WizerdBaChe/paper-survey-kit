/**
 * A framework-free copy button behavior with visible success and failure states.
 * The clipboard provider and legacy fallback are injectable so callers can test
 * refusal without depending on the browser's permission state.
 */

function defaultClipboard() {
  return globalThis.navigator?.clipboard ?? null;
}

function defaultLegacyCopy(text, documentRef = globalThis.document) {
  if (!documentRef?.body || typeof documentRef.createElement !== "function") return false;
  if (typeof documentRef.execCommand !== "function") return false;

  const textarea = documentRef.createElement("textarea");
  textarea.value = text;
  Object.assign(textarea.style, {
    position: "fixed",
    opacity: "0",
    pointerEvents: "none",
  });
  documentRef.body.append(textarea);
  textarea.select();

  let copied = false;
  try {
    copied = documentRef.execCommand("copy");
  } catch {
    copied = false;
  }
  textarea.remove();
  return copied;
}

/**
 * Copy text and resolve to false when both browser paths are refused.
 * This function deliberately never throws for clipboard failures.
 */
export async function copyText(text, options = {}) {
  const value = String(text ?? "");
  const clipboard = options.clipboard ?? defaultClipboard();

  try {
    if (!clipboard || typeof clipboard.writeText !== "function") {
      throw new Error("Clipboard API unavailable");
    }
    await clipboard.writeText(value);
    return true;
  } catch {
    try {
      const legacyCopy = options.legacyCopy ?? ((candidate) =>
        defaultLegacyCopy(candidate, options.documentRef ?? globalThis.document));
      return Boolean(await legacyCopy(value));
    } catch {
      return false;
    }
  }
}

/**
 * Attach copy behavior to one button. `text` may be a string or `getText`
 * may read the current value from the button's host context.
 */
export function mountCopyFeedbackButton(button, options = {}) {
  if (!button || typeof button.addEventListener !== "function") {
    throw new TypeError("mountCopyFeedbackButton needs a button-like element");
  }

  const idleLabel = options.idleLabel ?? button.textContent?.trim() ?? "Copy";
  const successLabel = options.successLabel ?? "Copied";
  const failureLabel = options.failureLabel ?? "Copy failed";
  const revertDelay = Number.isFinite(Number(options.revertDelay))
    ? Math.max(0, Number(options.revertDelay))
    : 1600;
  let resetTimer = null;

  const reset = () => {
    button.textContent = idleLabel;
    delete button.dataset.state;
  };

  const copy = async () => {
    let value = "";
    try {
      value = typeof options.getText === "function"
        ? await options.getText(button)
        : options.text ?? button.dataset.copyText ?? "";
    } catch {
      value = "";
    }

    const copied = await copyText(value, options);
    button.textContent = copied ? successLabel : failureLabel;
    button.dataset.state = copied ? "ok" : "fail";
    if (resetTimer !== null) globalThis.clearTimeout(resetTimer);
    resetTimer = globalThis.setTimeout(() => {
      resetTimer = null;
      reset();
    }, revertDelay);
    return copied;
  };

  const onClick = () => { void copy(); };
  button.addEventListener("click", onClick);
  if (!button.textContent?.trim()) button.textContent = idleLabel;

  return {
    copy,
    reset,
    destroy() {
      button.removeEventListener("click", onClick);
      if (resetTimer !== null) globalThis.clearTimeout(resetTimer);
    },
  };
}
