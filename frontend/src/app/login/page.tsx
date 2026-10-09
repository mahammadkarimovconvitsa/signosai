"use client";

import { useEffect, useState, type FormEvent } from "react";
import { useRouter } from "next/navigation";
import { AnimatePresence, motion } from "framer-motion";
import { useAuth } from "@/lib/auth-context";
import { ApiError } from "@/lib/http";
import { Logo } from "@/components/logo";

type Step = "email" | "password";

const SLIDE_DISTANCE = 56;

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? SLIDE_DISTANCE : -SLIDE_DISTANCE,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction > 0 ? -SLIDE_DISTANCE : SLIDE_DISTANCE,
    opacity: 0,
  }),
};

export default function LoginPage() {
  const { login, user } = useAuth();
  const router = useRouter();
  const [step, setStep] = useState<Step>("email");
  // +1 = moving email -> password (slide in from the right), -1 = reverse.
  const [direction, setDirection] = useState(1);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user) router.replace("/");
  }, [user, router]);

  if (user) {
    return null;
  }

  function handleNext(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!email) return;
    setDirection(1);
    setStep("password");
  }

  function handleBack() {
    setError(null);
    setPassword("");
    setDirection(-1);
    setStep("email");
  }

  async function handleLogin(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password, remember);
      router.replace("/");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Login failed");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="relative flex h-dvh items-center justify-center overflow-hidden bg-bg px-4">
      <div className="pointer-events-none absolute inset-0">
        <div className="absolute -left-40 -top-40 h-96 w-96 rounded-full bg-accent/10 blur-3xl" />
        <div className="absolute -bottom-40 -right-20 h-96 w-96 rounded-full bg-agent/10 blur-3xl" />
      </div>

      <div className="relative flex w-full max-w-md flex-col items-center">
        <div className="flex flex-col items-center text-center">
          <Logo size={48} />
          <div className="wordmark mt-5 text-[30px] leading-none text-ink">
            signos<span className="text-accent">.</span>
          </div>
          <div className="mt-2 text-sm text-muted">
            The SI (Super Intelligence) operating system for mobile network operators
          </div>
        </div>

        <div className="relative mt-12 grid w-full overflow-hidden">
          {/* Both panels are stacked in the same grid cell (not popLayout's
              remove-from-flow approach) so the container's height tracks
              whichever is tallest of the two WHILE they're both present
              mid-crossfade, instead of snapping straight to the entering
              panel's height -- that snap is what made "Next" (short email
              panel -> tall password panel) look like a jump instead of a
              slide, while "Back" (tall -> short) mostly hid it. */}
          <AnimatePresence custom={direction} initial={false}>
            <motion.div
              key={step}
              custom={direction}
              variants={slideVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.28, ease: [0.22, 1, 0.36, 1] }}
              className="col-start-1 row-start-1 flex w-full flex-col items-center"
            >
              <h1 className="text-xl font-semibold text-ink">
                {step === "email" ? (
                  <>
                    Sign in to signos<span className="text-accent">.</span>
                  </>
                ) : (
                  "Enter your password below"
                )}
              </h1>

              {step === "email" ? (
                <form onSubmit={handleNext} className="mt-8 flex w-full flex-col gap-5">
                  <input
                    type="email"
                    required
                    autoFocus
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="Enter your email"
                    className="w-full rounded-xl border border-line-strong bg-surface-raised px-5 py-4 text-[15px] text-ink outline-none transition-colors focus:border-accent"
                  />
                  <button
                    type="submit"
                    className="rounded-xl bg-gradient-to-r from-accent to-accent-strong px-5 py-4 text-[15px] font-semibold text-bg transition-opacity hover:opacity-90"
                  >
                    Next
                  </button>
                </form>
              ) : (
                <form onSubmit={handleLogin} className="mt-8 flex w-full flex-col gap-5">
                  <input
                    type="password"
                    required
                    autoFocus
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="Please enter your password"
                    className="w-full rounded-xl border border-line-strong bg-surface-raised px-5 py-4 text-[15px] text-ink outline-none transition-colors focus:border-accent"
                  />
                  <label className="-mt-1 flex items-center gap-2.5 text-sm text-muted">
                    <input
                      type="checkbox"
                      checked={remember}
                      onChange={(e) => setRemember(e.target.checked)}
                      className="h-4 w-4 rounded border-line-strong bg-surface-raised accent-accent"
                    />
                    Remember me
                  </label>

                  {error && (
                    <div className="rounded-lg border border-breached-line bg-breached-soft px-3 py-2 text-sm text-breached">
                      {error}
                    </div>
                  )}

                  <button
                    type="submit"
                    disabled={submitting}
                    className="rounded-xl bg-gradient-to-r from-accent to-accent-strong px-5 py-4 text-[15px] font-semibold text-bg transition-opacity hover:opacity-90 disabled:opacity-60"
                  >
                    {submitting ? "Signing in…" : "Login"}
                  </button>
                  <button
                    type="button"
                    onClick={handleBack}
                    className="rounded-xl border border-line-strong px-5 py-4 text-[15px] font-semibold text-ink-secondary transition-colors hover:border-muted-2 hover:text-ink"
                  >
                    Back
                  </button>
                </form>
              )}

              <span className="mt-7 select-none text-sm text-muted-2">
                {step === "email"
                  ? "Contact administrator to request an account"
                  : "Forgot password?"}
              </span>
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
}
