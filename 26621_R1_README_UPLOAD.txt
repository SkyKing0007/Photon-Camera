PHOTON / IRIS 26621 R1 — NEW SIMPLIFIED GLOBAL TONE + TRUE LOCAL LAPLACIAN

UPLOAD TARGET
- Branch: experimental-clean-photon-rebuild
- Expected parent HEAD: a2ee879727707b293781868c13fd70102b9507c7 (successful 26620 R1)
- Commit message: 26621 R1 new simplified tone true local laplacian
- Upload/extract all files in this handoff to repository ROOT, preserving folders.
- Do NOT manually copy handoff_payload_26621_r1/app/** into live app/**.
- Do NOT push APKs.

RUNTIME AUTHORITY
- Successful 26620 R1 commit: a2ee879727707b293781868c13fd70102b9507c7
- Actions run: 34437257967
- Artifact ID/name: 10136699847 / photon-26620-r1-multiscale-local-laplacian
- Artifact ZIP SHA-256: 9c49984b4573a7f2d4e9518faa768baa6859ccad806468e77f651dc6e2daa3d6
- Exact compiled candidate TAR SHA-256: 7a51215a31287d5943be2453597645ad48cebf6c4954bfd77d0b605018ab0e89

VERIFICATION-MECHANICS AUTHORITY
- Exact successful 26620 R1 build/workflow/transform mechanics.
- Compiler/NDK/patch/PRE-BUILD/assemble/postbuild ordering is intentionally unchanged.
- Nested candidate Git isolation with GIT_CEILING_DIRECTORIES remains mandatory.

TARGET
- Version 0.9726621 / build 26621
- Runtime changed-file allowlist: exactly 17 paths.
- Base/candidate app files: 1711 -> 1713.
- Protected: 1699; native protected: 802; vendor protected: 778; DNG: 7.
- No backup created (user request).

PRESENTATION REPLACEMENT
- motionV2DisplayGain remains the sole brightness request; existing 0.80 exposure scale is consumed once.
- Replaces the inherited high-gain cubic plateau with one shared smooth global tone equation used by matcher, adaptive-color predictor, 1x renderer, and true2x CPU/GPU.
- Physically removes all three obsolete 26620 correction-map shaders.
- Adds a seven-level reference-sliced Local-Laplacian-style full-resolution absolute log-tone target after global tone.
- Local stage is luminance/guide driven and applies one common RGB scalar; it does not own independent per-channel color.
- Exact black/deep shadows fade to global-only behavior.
- SDR/UHDR and true2x share the same presentation authority; genuine >1.0 source headroom remains UHDR authority.

PERMANENT REGRESSIONS
- Reproduce and reject the old 26614/26620 high-gain highlight plateau (near-zero useful slope).
- Reject 26618 pre-tone attenuation/ring behavior and 26619/26620 coarse correction-map authority.
- Require global tone monotonicity, useful minimum slope, C1 source-white continuity, and increasing >1 tail.
- Require Local-Laplacian remap monotonicity/detail neutrality, reference partition unity, matched reduce/expand geometry, exact-black/deep-shadow protection, common RGB scalar, and full-resolution target sampling.
- Preserve successful 26620 SHORT/CFA/Sabre/merge/VGN/denoise/DNG/UHDR-gain behavior outside the presentation delta.
- Preserve the prior native namespace compiler regression guard.

LOCAL STATUS
- Sealed source/manifests/patches/validators are locally replayable.
- Real glslang/Kotlin/Java/NDK/full assemble are NOT proven by the handoff itself; GitHub Actions is authoritative.
