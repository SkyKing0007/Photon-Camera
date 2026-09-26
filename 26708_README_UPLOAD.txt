PHOTON 26708 — ISOLATED SHORT HIGHLIGHT OWNERSHIP

Runtime authority: exact successful 26707 Actions compiled candidate. No backup created, per user request.
Runtime changes: exactly 8 files in handoff_payload_26708.

Behavior:
- restores successful 26706-style HAL/user-only repeating preview and NORMAL exposure ownership;
- removes 26707 automatic NORMAL AE-compensation highlight writer and hard-zeros Motion NORMAL referenceProtectionEv;
- classifies highlight need read-only from a fresh complete 9-phase RAW cycle;
- schedules only no SHORT / ~0.67 EV SHORT / ~1.33 EV SHORT;
- terminal SHORT failure degrades to NORMAL-only rather than failing the Motion photo;
- carries compact 64x48 SHORT radiance provenance from existing Sabre telemetry and excludes SHORT-owned cells from global WYSIWYG body-gain solve;
- preserves established Sabre fusion equations, MotionV2Render/UHDR, 26707 neutral-surface chroma leak correction, and 26707 moving-content tail safeguard.

Real Kotlin/Java/NDK/full assemble are Actions-only.
