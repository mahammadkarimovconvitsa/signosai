// The "S" spine, shared by both renderings below -- a thick rounded stroke
// with two ball terminals, matching the brand mark.
const S_PATH = "M70,25 C48,25 28,33 28,45 C28,57 72,43 72,55 C72,67 52,75 30,75";

/** Bare two-tone mark: stroke follows currentColor, terminals are Signal orange.
 * For use directly on a page background (e.g. a hero), not in a small badge. */
export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" aria-hidden>
      <path d={S_PATH} stroke="currentColor" strokeWidth="13" strokeLinecap="round" />
      <circle cx="70" cy="25" r="9" fill="#ff5a1f" />
      <circle cx="30" cy="75" r="9" fill="#ff5a1f" />
    </svg>
  );
}

/** The "Signal" app-icon tile: orange rounded-square badge, monochrome ink
 * mark. Used anywhere a compact, self-contained brand badge is needed
 * (sidebar, login, favicon-style contexts). */
export function Logo({ size = 32 }: { size?: number }) {
  return (
    <div
      className="flex shrink-0 items-center justify-center rounded-[28%]"
      style={{ width: size, height: size, background: "#ff5a1f" }}
    >
      <svg width={size * 0.6} height={size * 0.6} viewBox="0 0 100 100" fill="none" aria-hidden>
        <path d={S_PATH} stroke="#0e1116" strokeWidth="15" strokeLinecap="round" />
        <circle cx="70" cy="25" r="10" fill="#0e1116" />
        <circle cx="30" cy="75" r="10" fill="#0e1116" />
      </svg>
    </div>
  );
}
