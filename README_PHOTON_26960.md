# Photon 26960 — RAWR HDR+ Higher Quality Motion Restoration and SDR Color Separation

**LOCALLY VALIDATED — PREPARED FOR GITHUB ACTIONS ONLY; NOT BUILD-PROVEN OR DEVICE-QUALITY-PROVEN.**

### Exact successful runtime authority
26959 successful Actions run `44372238333`, commit `a3b25f78e75e81832aa56c2fddb415ec715b204c`, published artifact `14460861326`, artifact ZIP SHA-256 `6819c4229c47459564ec2aa7f2408886d0f18d88c59ad55acf3a854be5feaf4b`, exact compiled-source TAR SHA-256 `2fb326a334f68fe0fd2b1b3c36926c85ea2d35e6dc2001d0ee10ad003258a204`, actual executed builder SHA-256 `967371652445073ea38626d661a01936ad0d02ac499a08264943650be2370691`, actual executed workflow SHA-256 `68ca69943f8072e550ec5034665f2758ec5f0c4dfd142df7db9ba2e23c559a67`, actual APK SHA-256 `34e7ebec2dcc426c1d606d72574699d8a1ffa7ba8083ab8aee1d6eda2c7a09a3`.

### Source targets and justification
- **Experiment B, Super Res OFF only**: restore current RAWR HDR+ Quality strength **13** (actual upstream default) from previous 11, and reenable the 4×4 RAW noise-calibrated signed-displacement plus fine-texture energy **motion rejection**. The prior 26959 gate bypass allowed moving subjects to ghost despite alignment. Keep all existing alignment geometry, 7×7 Fourier shift, four pass tiling, and the successfully compiled protected Vulkan shaders.
- **Mottling protection**: the same active motion rejection is restored, but unlike raw RAWR it does not apply its secondary per-rejected-tile **reference-spectrum shrinkage** in Photo B OFF. This is a targeted, reversible Iris-specific anti-chroma-mottling safeguard. Night retains Rawr's previous shrink 1.0, motion gate and strength 13. Effective accepted frames are read under the existing fence rather than falsely reported as full burst support. This design is plausible, but only a device test can prove the mottling is gone.
- **SDR color-fade**: with the still-large adaptive scene display gain, colored foliage gets compressed into the bright near-white shoulder. A bounded, smooth **scalar** SDR highlight spacing adjustment in the existing Photo B OFF rendering path (max 0.045 linear guide) retains RGB ratios, true source whites and black, and applies without spatial edge changes. The **same guide** is mirrored in the gain-map SDR denominator model so the original extended HDR master and true UHDR target are not intentionally modified. Existing final tone architecture, AMaZE, FCC, sky/foliage borders and UHDR gain-map generation are preserved.

These are code-grounded mechanisms, **not** measured proof of visual corrections. Comparing the SDR and UHDR foliage, stationary texture and the walking subject is mandatory device acceptance.

### Exact source allowlist / protected
The successful 26959 compiled TAR contains **2,055** runtime source files. The 26960 candidate contains **2,055**; exactly **7 changed** and **2,048 byte-identical protected**. No source files added or deleted. Runtime changed paths are listed in `26960_CHANGED_RUNTIME_ALLOWLIST.txt`: two mirrored SDR/gainmap GLSL files, four exact B HDRQ native bridge/header files, version properties. Protected vendor/AMaZE/FCC, DNG/native binaries, Spektra, Motion, SR ON, Night, sky/foliage border shader, LKR and unrelated runtime sources are byte-identical. Infrastructure delta consists of new 26960 builder/workflow/validators/hashes and staged overlay, with prior successful 26959 workflow preflight prefix retained verbatim.

### Exactly three-stage vscode.dev upload (NO standalone scripts to run)

**Stage 1:** Open only GitHub branch `experimental-clean-photon-rebuild` in vscode.dev. Upload all items listed in `26960_STAGE_1_UPLOAD_PATHS.txt` into the matching repository paths, preserving the directories. The candidate source edits live inside `handoff_payload_26960/app/...`; **do not manually overwrite `app/src`**. Commit this stage.

**Stage 2:** Upload `.github/workflows/build-26960-change-aware.yml`, commit the second stage.

**Stage 3:** Upload `TRIGGER_26960.txt` **last**, commit the third stage. The single 26960 guarded Actions job starts. Do not create a backup branch, touch `dev`, or commit/push an APK.

The Actions job must fetch the exact successful 26959 artifact; validate its compiled candidate, actual builder/workflow and APK SHA; rerun historical **26886/26887, 26903, 26904 V2 and V3** checks, prove full-index reversible patches at `core.abbrev=7/12/40`, compile pinned GLSL 16.5.0 ESSL300/310 and Vulkan SPIR-V val/opt (including both modified SDR/gainmap shaders), compile real two-ABI native/NDK + Kotlin and Java, perform `:app:assembleDebug`, verify one new APK, unchanged official LKR binaries and source allowlist, then publish APK + actual compiled source TAR. Fail closed on missing certificates. No compiler steps may be skipped or weakened.

Only once a real Actions job is successful **and** the artifact is published does this become **BUILD-PROVEN**. Build success alone does not establish device image quality.
