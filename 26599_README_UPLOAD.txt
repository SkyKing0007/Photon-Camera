26599 V1 — Effective SHORT Recovery + Shared HDR Tone Normalization

BASE / RUNTIME AUTHORITY
- successful 26598 V1.1 commit: 4127027f5f862513034a22d4de17ad0b1575bae8
- Actions run: 33941164383
- job: 101238751503
- artifact: 9961914943 photon-26598-v1-1-scene-white-capture-ownership
- artifact SHA-256: eeef32156285d100b14854797b37e85f35d9fd0eb55629bbc713cbcce307b2ce
- candidate tar SHA-256: a6f3287393a85b35d409ad7d17200715929b0e4646769f48e8fec0773160c7be

VERIFICATION MECHANICS AUTHORITY
Exact successful 26598 V1.1 build/handoff procedure, itself preserving successful-26593 compiler/build ordering and the 26567 authority-seeded lineage. Do not reorder, simplify, or substitute the packaged build sequence.

BACKUP
backup-26598-before-26599-hdr-tone-ownership
must point exactly to 4127027f5f862513034a22d4de17ad0b1575bae8 before Actions runtime writes.

RUNTIME SCOPE — EXACTLY 8 FILES
See V1_26599_RUNTIME_CHANGED_PATHS.txt. CaptureController, DNG, Sabre flow/alignment, color matrices, MotionV2Render, adaptive appearance, HAL/System AE and NORMAL-only SR detail evidence are intentionally unchanged.

INTENT
1. Keep exact literal RAW sensor clipping recovery.
2. Add an exposure-normalized effective NORMAL-loss route so aligned, radiometrically coherent SHORT can restore real highlight information that NORMAL has lost even when RAW code is not literally at whiteLevel-0.5.
3. Keep whole-RGB SHORT replacement and fail closed on flow/radiometry/headroom uncertainty.
4. Add a low-cost 64x48 exact-shader gate probe plus the existing exact full-resolution final-active counter; no full-resolution diagnostic texture/readback.
5. Replace uniform positive Motion display gain above an 18% guide anchor with one shared whole-RGB monotonic presentation normalization. Darks/midtones through 18% remain exactly the successful-26598 scalar behavior. Night keeps scalar exposure behavior.
6. Use the exact same presentation constants/equation for 1x and true-2x/Super Res. SHORT remains HDR/color evidence only; it never becomes SR detail evidence.
7. Preserve successful-26598 sceneWhite/color/capture ownership semantics.

UPLOAD
Replace/upload every file in this handoff at the matching repository path, commit once on experimental-clean-photon-rebuild, and push. Do not add APKs or live app/src copies beyond the sealed handoff payload.

Suggested commit message:
26599 V1 effective SHORT recovery and shared HDR tone normalization

Before Actions succeeds this handoff is PREPARED / UPLOAD-READY only, not build-proven.
