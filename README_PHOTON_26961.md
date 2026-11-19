# Photon 26961 — successful 26959-based indoor neutral tone and SDR foliage luminance correction

**LOCALLY VALIDATED — PREPARED FOR ACTIONS; NOT BUILD-PROVEN or device image-quality proven.**

This is **one three-stage vscode.dev ZIP**, not a script the user runs. Upload the paths in `26961_STAGE_1_UPLOAD_PATHS.txt` to `experimental-clean-photon-rebuild` (preserving their paths), then upload `26961_STAGE_2_UPLOAD_PATHS.txt`, then `26961_STAGE_3_UPLOAD_PATHS.txt` (trigger last). The branch `dev` must never be modified. No commits, pushes or GitHub Actions were initiated in preparation of this ZIP. The user controls the GitHub commit/upload and the job.

## Absolute runtime and verification authority

- **Build 26959 V2** successful GitHub Actions run **44372238333**, commit `a3b25f78e75e81832aa56c2fddb415ec715b204c`, published artifact ID `14460861326`, complete ZIP SHA-256 `6819c4229c47459564ec2aa7f2408886d0f18d88c59ad55acf3a854be5feaf4b`.
- Actual 26959 Actions **compiled source TAR** SHA-256 `2fb326a334f68fe0fd2b1b3c36926c85ea2d35e6dc2001d0ee10ad003258a204`, executed builder SHA-256 `967371652445073ea38626d661a01936ad0d02ac499a08264943650be2370691`, executed workflow SHA-256 `68ca69943f8072e550ec5034665f2758ec5f0c4dfd142df7db9ba2e23c559a67`, actual successful 26959 APK SHA-256 `34e7ebec2dcc426c1d606d72574699d8a1ffa7ba8083ab8aee1d6eda2c7a09a3`.
- **Not 26960**: the 26960 source, its modified HDR+ motion gate, new noise behavior and changed strength are *not* used. The 26959 B/Super-Res-OFF active frequency merge, noise estimator, AMaZE, FCC, reference spectrum and motion behavior are **exactly byte-for-byte unchanged**. 26959 is the user-reported mottling-free visual reference, not laboratory-proven for all scenes. Its known moving-subject ghosting remains unresolved in this candidate, intentionally.

## Intended 26961 source edits — exactly 5 of 2,055 files

1. `MotionV2Render.java`: using the actual supplied `170542` image's recorded *pre-tone* histogram (`P25≈0.00715`, `P50≈0.01811`, `P95≈0.08099`, `P99≈1`), recognize only a bounded, low-zoom Experiment B/Super Res OFF indoor-like signature and suppress legacy positive shadow/toe lift. Other scenes remain exactly on 26959's authority. Preserve the viewfinder brightness matching and the user-selected SDR Body Contrast (0.35 in the reference). Skip extra B visual-toe, optional Local Laplacian and scene-adaptive backlit/flat tone for qualifying scenes. The successful default exposure, native RAW and HDR+ steps are untouched.
2. `IrisMotionToneControls.java`: ensure that the separate automatic shadow toe cannot silently reintroduce the same boost for those qualified scenes. User-controlled exposure/shadow/contrast values and viewfinder matcher are not touched.
3. `render.glsl` and `gainmap.glsl`: suppress the stale 26932 B-OFF SDR bridge and object-color-gamma extra body effect *only* under the indoor neutral flag; keep the **original SDR Body Contrast** in both. Separately, for **Photo B/OFF below 1.10x only** and **not the neutral indoor case**, use an analytic, bounded, hue-preserving scalar *luminance shoulder* starting at mapped guide 0.82 on actual warm/chromatic highlight evidence. No artificial saturation increase, no neighbor sampling, no sky-blue/neutral-white change, no sensor-white or RAW clipping logic change. Render and UHDR SDR denominator model use an identical function and site-specific flags, while leaving the original HDR master untouched. The observed foliage fading is not confirmed solved without device tests.
4. `app/version.properties`: build 26961 / `0.9726961`.

**Protected**: 2,050 other compiled runtime files byte-identical, including all native/vendor/RAWR, AMaZE, FCC, HDRQ frequency and border shaders, sky border correction, Spektra, Experiment A, Super Res ON, Night, DNG, video, and existing original post-merge image processing. No added/deleted runtime source.

## Verification and infrastructure

The existing successful 26959 historical prefix and historical 26886/26887, 26903/26904 V2/V3 compiler regressions remain unchanged. The next 26961 actions workflow first acquires and SHA-authenticates **the exact published successful 26959 artifact**, reconstructs 2,055 real compiled source files, rejects extra/removed/modified protected files, replays original successful shader compilation, installs only the five allowlisted overlays, and *requires actual pinned GLSL ES300/310, Vulkan shader + SPIR-V validator/optimizer, exact CMake compiler handoff, two-ABI NDK, Kotlin, Java and `:app:assembleDebug`*. The shader stage must exit nonzero on unavailable glslang/SPIR-V. No stubs, skipped native tasks, or reduced compilation. Only after actual verified APK compilation is exactly one APK and the candidate-source TAR published. The new job is the first opportunity to claim BUILD-PROVEN; device visual quality is never proven by compilation alone.

Local clean extraction and SHA-verification, 2,055/5/2,050 scope proof, full-index forward and rollback patches under `core.abbrev` 7/12/40, syntax, linked-source/historical reference scans, GPU shader reserved words (`coherent`/`flat`), negative/tamper tests and numerical scene/SDR/gain-map checks are recorded in `26961_LOCAL_VERIFICATION.txt`. The local environment lacks the pinned GLSL/Android toolchain, so **new shader, SPIR-V, NDK/Kotlin/Java/Gradle assemble: NOT RUN LOCALLY**. No new 26961 APK, APK SHA or successful 26961 Actions artifact exists in this handoff.

## Device evaluation after successful Actions

- Reproduce the **17:05:42** indoor scene: viewfinder gain should remain the same; log `IRIS_26961_B_OFF_NEUTRAL_INDOOR neutral=true`, positive body tone strength should be `0.0`, manual tone controls unchanged, SDR Body Contrast at its established 0.35.
- Check outdoor foliage yellow/green/red near white against 26959 SDR and UHDR, genuine neutral whites, blue-sky gradients and branch/foliage borders. The luminance shoulder is an analytic targeted hypothesis, **not an asserted visual fix**.
- Verify stationary and moving subjects, the absence of returned chroma mottling and the known unchanged 26959 motion-ghosting limitation. No 26960 motion code has been reintroduced. If any step fails, reject candidate rather than approving a new algorithm on speculation.
