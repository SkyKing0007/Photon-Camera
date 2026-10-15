PHOTON 26840 — SMOOTH ROLLOFF CLIP-ZONE CHROMA

Runtime authority: successful 26839 Actions run 38767292607, commit c548e4265121c333cd0fd7cc59351bf63a70dc28, artifact 11990048321, artifact SHA-256 cf0670299e58ac094164d531535707afe758137da0181a5a2d382fd302c65805.
Verification mechanics: exact successful 26839 17-stage procedure, inherited unchanged; successful 26821 root mechanics retained.
No backup branch.
Runtime changed-file allowlist: exactly 3 modified / 0 added / 0 deleted.
Infrastructure procedure delta from successful 26839: zero; only authority/version/scope-specific proof names and validators advance.

26840 correction:
- preserve successful 26839 source-hue-direction ownership and donor magnitude-only contract;
- regularize the final mask boundary inward-only with a 3x3 tent footprint so unsupported jagged protrusions shrink but correction can never expand into valid pixels;
- keep boundary chroma on the source hue ray and roll only saturation magnitude continuously;
- prohibit cross-hue blending in the visible boundary, removing gray/silver cancellation rings;
- delay mild warm terminal fallback to the deepest unrecoverable core only;
- preserve exact no-op outside owned mask support and preserve WB-linear luminance exactly;
- DNG, LONG chroma authority, SR, high-zoom, VGN/tone, native/vendor and unrelated shader assets stay protected.

UPLOAD — vscode.dev only, three stages; push only after stage 3:
1) Upload/replace every file from folder 1 at repository root. Commit: 26840 smooth-rolloff clip-zone runtime
2) Upload folder 2 workflow to .github/workflows. Commit: 26840 exact 26839 build workflow
3) Upload folder 3 hash manifest + trigger. Commit: 26840 handoff hashes and trigger
Then push once. Only TRIGGER_26840.txt is the workflow push path.

Before Actions succeeds this package is PREPARED / UPLOAD-READY only. GitHub Actions is authoritative for pinned real GLSL, Kotlin/Java, NDK, full assemble, one-APK, post-build invariance and clean-extract replay.
