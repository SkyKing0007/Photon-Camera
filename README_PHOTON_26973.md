# Photon 26973 — Experiment C selectable, controlled device trial

**Exact authority:** successful 26972 Actions run 44923896617; commit 583b87148fa21d49df4b359991439e1d475ac526; artifact 14715277974. Artifact SHA-256 `3c9dee79f816eb1ef2cd7e62e1b88c2556a86ee2d53b95984bb8b7486fb12921`; actual compiled TAR SHA `0ce0b5910f379011db3dc9fc8db7eee093fcf22bf746595bc69bd96f9667271f`. Executed 26972 runner `39eb9bedafc467e1faeb98c7a9c94c4ac20151fdce6fb53a2930a5b97cf26137`, workflow `60b71ec1c86f3e809aebcdefa0008502277fa1d7e5d63648affe6012191dcc08`, APK `6c56cfa3ef71508c4e454e81978e39fe4a7ce24b5acd05c8baa2c5ef4546dacc`.

## Upload order — four folders (each under 100 files)

1. Stage 1A: upload contents into **original repository paths** on `experimental-clean-photon-rebuild`. Commit.
2. Stage 1B: upload contents into original repository paths. Commit. Do not trigger yet.
3. Stage 2: upload **only** `.github/workflows/build-26973-change-aware.yml` into the existing `.github/workflows/` folder. Commit.
4. Stage 3: upload **only** `TRIGGER_26973.txt` into repository root. Commit to trigger. Do not upload stage folder names.

Never modify `dev`, commit/push source outside these explicit handoff files, or push APKs. These are instructions for optional user-approved uploads, not actions performed by the assistant.

## Behavior and safety

C now appears next to A and B in the existing physical-lens-specific selector, using the same persistence and shutter-selected freeze. Only an explicit C choice uses isolated Camera2 RAW/Sabre/RAISR/JPEG-R. It is **a controlled device trial**, not production-proven: `PRODUCTION_READY=false` and `ACTUAL_CAMERA2_CALLBACK_WIRED=false` remain truthful. The independently compiled C route uses `CONTROLLED_DEVICE_TRIAL_ENABLED=true`, but retains all capture bounds, ABI/metadata checks, non-fallback and cancellation/cleanup protections. Device output, gain-map orientation, memory, image quality and reliability remain unverified until Android device tests.

Exactly 11 modified source files (the C-only gate sites, the A/B/C list and version), 0 additions/deletions, 2,121 protected files unchanged. No original A/B/Native/vendor/shader algorithm bytes changed; no infrastructure source delta. The historical successful 26972 workflow preflight is byte-identical; real pinned GLSL/SPIR-V, Java/Kotlin, dual ABI CMake/NDK, assembleDebug, 26886/26887 + 26903 + 26904 history and source protection remain mandatory. Build success requires successful Actions **and published artifact**; compile success does not prove photo appearance.
