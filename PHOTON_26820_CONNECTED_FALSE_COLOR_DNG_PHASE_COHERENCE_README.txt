PHOTON 26820 — CONNECTED FALSE COLOR + DNG NEUTRAL PHASE COHERENCE

STATUS: PREPARED / UPLOAD-READY. Real GLSL/Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME AUTHORITY
- Successful 26819
- Commit: 077203ce2c430b6f14413f7706594c5c36783721
- Actions run: 38251186766
- Artifact: 11749140708 photon-26819-normal-clipped-chroma-validity
- Artifact SHA-256: a130b48152893b907fafb072f7db1d4094f5e64e127ead17a61393415054013f
- Candidate TAR SHA-256: cc669a58048ae4e5a2cde8c68e22ff1203de730f116cd4224646118372a495d2

VERIFICATION MECHANICS
- Exact successful 26819 17-stage procedure inherited unchanged.
- Successful 26812 root mechanics remain inherited.
- No backup branch.
- Runtime scope: exactly 4 modified + 0 added + 0 deleted.
- Infrastructure procedural delta: ZERO; identifiers/manifests/validators/workflow names and shader accounting only.

26820 RUNTIME INTENT
JPEG / render false color:
- Preserve exact 26799 Boolean connectivity and exact 26803 strict 0.92 neutral-parent target.
- Preserve classifier 26800 byte-for-byte.
- Carry classifier evidence codes through propagation instead of collapsing all connected pixels to 1.0.
- Do not repaint weak 0.40 bright-neutral plateaus.
- Apply graded correction to 0.55 / 0.85 / 1.0 evidence and feather weak/strong mask boundaries instead of binary 100% chroma replacement.
- Target the 26819 peach/orange bright-ground fill, cyan/teal/yellow highlight repainting, and local correction-mask seams.

DNG / Bayer phase coherence:
- Keep exact successful 26819 normalDngMerge, alignment, covariance/rejection, phase-scoped headroom, LCA settings, G1/G2 independence and DNG writer bytes.
- In normalizeBayer only, correct R/B phase alias when a strong center-vs-green mismatch + high-frequency structure + sparse 9-quad neutral-material proof agree.
- Leave G1/G2 samples untouched and keep output as Bayer CFA.
- Target both alternating pink/blue road-marker edges and full pink/blue fill of distant thin white marker bodies.
- Coherent colored fine detail fails the neutral-material proof and remains untouched.

FROZEN SUCCESSFUL BEHAVIOR
- 26819 NORMAL Sabre clipped-chroma validity: byte-frozen.
- 26818 VGN green residual cleanup: byte-frozen.
- 26800 classifier: byte-frozen.
- normalDngMerge + DNG alignment/merge weights: byte-frozen.
- SHORT, Resolve, exposure/frame policy, tone, SDR/UHDR, native/vendor and DNG writers: protected.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES

1) Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26820: prepare connected false color and DNG phase coherence
   This stage must NOT start the build.

2) Upload/replace STAGE_2_UPLOAD_SECOND/.github/workflows/build-26820-connected-false-color-dng-phase-coherence.yml
   Commit and push exactly:
   26820: add connected false color and DNG phase workflow
   This stage must NOT start the build.

3) Upload/replace both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26820: activate connected false color and DNG phase build
   Only this stage triggers the workflow.

Expected workflow: Build 26820 Connected False Color + DNG Phase Coherence
Expected artifact: photon-26820-connected-false-color-dng-phase-coherence
Expected APK: IrisCamera-0.9726820-26820-connected-false-color-dng-phase-coherence-debug.apk
