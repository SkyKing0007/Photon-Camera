PHOTON 26839 — HUE-PRESERVING CLIP-ZONE CHROMA

Runtime authority: successful 26838 Actions run 38735812736, commit ec04820dc00fc5cb11571fde1b13ddf2aac41ad8, artifact 11973572312, artifact SHA-256 d24efab7d45248ab4bfe16eec1ba26480e87986dcb6fc631bd55787eec7bc384.
Verification mechanics: exact successful 26838 17-stage procedure, inherited unchanged; successful 26821 root mechanics retained.
No backup branch.
Runtime changed-file allowlist: exactly 3 modified / 0 added / 0 deleted.
Infrastructure procedure delta from successful 26838: zero; only authority/version/scope-specific proof names and validators advance.

26839 correction:
- preserve successful 26838 clip-mask ownership and successful 26837 immutable GLES3 FBO fragment backend/lifecycle/placement;
- preserve exact no-op for low-confidence blurred/dilated mask tails;
- preserve source hue direction only when source + small local + broad same-region chroma directions agree;
- donors may cap chroma magnitude but can never rotate accepted hue;
- remove 26838 neutral-white fallback that painted red/tan/gray/yellow highlights white;
- use only a mild warm terminal clipped-highlight axis when hue direction itself is unrecoverable;
- original WB-linear luminance y is reconstructed exactly;
- DNG, LONG chroma authority, SR, high-zoom, native/vendor and unrelated shader assets stay protected.

UPLOAD — vscode.dev only, three stages; push only after stage 3:
1) Upload/replace every file from folder 1 at repository root. Commit: 26839 hue-preserving clip-zone runtime
2) Upload folder 2 workflow to .github/workflows. Commit: 26839 exact 26838 build workflow
3) Upload folder 3 hash manifest + trigger. Commit: 26839 handoff hashes and trigger
Then push once. Only TRIGGER_26839.txt is the workflow push path.

Before Actions succeeds this package is PREPARED / UPLOAD-READY only. GitHub Actions is authoritative for pinned real GLSL, Kotlin/Java, NDK, full assemble, one-APK, post-build invariance and clean-extract replay.
