PHOTON 26707 REVISED — NEUTRAL CHROMA + BOUNDED NORMAL HIGHLIGHT PROTECTION + MOVING-CONTENT TAIL REJECTION

This supersedes the earlier unbuilt 26707 package. Use only this revised package.

Runtime authority: exact successful 26706 Actions compiled candidate. No backup created.
Runtime changes: exactly 5 files in handoff_payload_26707.

Behavior:
- preserves the original 26707 lens-agnostic blue-speck/neutral-surface chroma leak correction;
- adds absolute NORMAL highlight protection states 0 / -0.67 EV / -1.33 EV relative to the settled HAL/user baseline, never cumulative;
- preserves 26705 six-frame genuine AE/AWB/energy convergence and removes no cold-start safeguard;
- restores the true baseline on physical reframe before any new scene decision;
- carries total frame-exact referenceProtectionEv for existing one-time float-domain normalization;
- rejects only extreme low-confidence NORMAL temporal tails when both frame and pixel agreement reject moving content; SHORT/LONG contracts are unchanged.

Real GLSL/Kotlin/Java/NDK/full assemble are Actions-only.
