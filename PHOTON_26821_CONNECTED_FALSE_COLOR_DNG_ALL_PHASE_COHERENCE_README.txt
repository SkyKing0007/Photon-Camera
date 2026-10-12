PHOTON 26821 — CONNECTED FALSE COLOR + DNG ALL-PHASE COHERENCE

STATUS: PREPARED / UPLOAD-READY. Real Kotlin/Java/NDK/full assemble are NOT RUN locally; GitHub Actions is authority.

RUNTIME AUTHORITY
- Successful 26820
- Commit: a4011eac86bfb3cdbcf937869c0b21df9958cd0d
- Actions run: 38281309301
- Artifact: 11761243695 photon-26820-connected-false-color-dng-phase-coherence
- Artifact SHA-256: 3f424a99fb79b6dc6bc091e8b4f3d056c3296f631b7297d91923063635ba11f1
- Candidate TAR SHA-256: dbc7d3cc6d7c63d49d64d6410fb490d4904c59cb1c65a08d9af0d8ea417279e0

VERIFICATION MECHANICS
- Exact successful 26820 17-stage procedure inherited unchanged.
- Successful 26812 root mechanics remain inherited.
- No backup branch.
- Runtime scope: exactly 4 modified + 0 added + 0 deleted.
- Infrastructure procedural delta: ZERO.

26821 RUNTIME INTENT
JPEG / render false color:
- Preserve successful 26800 classifier and exact 26803 strict neutral-parent target.
- Separate connectivity state from classifier confidence inside the existing R8 carrier, so weak/plateau candidates can propagate through the full inherited eight passes without losing their evidence class.
- Connected plateau pixels remain topology-only and receive no chroma repaint.
- Strongly proven highlight false-color cannot inherit arbitrary cyan/yellow/peach material hue; the target is continuously capped near neutral in the display-highlight regime.
- Proven highlight false-color reaches full correction; lower-domain correction remains continuously feathered.
- Target the cyan/teal/yellow railing inserts, peach/orange highlight fill and horizontal/local correction seam.

DNG / Bayer phase coherence:
- Preserve exact successful 26820 normalDngMerge, alignment, covariance/rejection, LCA settings and DNG writer bytes.
- Replace the 26820 R/B-only final coherence rule with evidence-gated all-four-phase R/G1/G2/B neutral coherence.
- Preserve the WB-neutral quad mean exactly; do not demosaic or change CFA format.
- Use sparse neutral-material proof plus two-neighbor same-hue persistence to protect genuine colored thin structure.
- Add a narrow CFA-Nyquist non-identifiable override only when G1/G2 disagreement and full-quad phase spread are both extreme; periodic phase alias cannot masquerade as protected real hue there, while the WB-neutral quad mean/luma remains exact.
- Target both residual pink/blue marker edges and full-body pink/blue fill in distant white road markers, including G1/G2-dominated residuals proven in 26820.

SPEED / LATENCY
- No DNG lifecycle/readback reordering in 26821: the audit proved that change would cross GPU/buffer lifetime ownership and is not safe to fold into this IQ correction without a separate lifecycle proof.
- Super Resolution routing/frame count are unchanged. Ordinary 1.0x Motion with Super Resolution OFF does not activate the true-2x/high-zoom extension.

FROZEN SUCCESSFUL BEHAVIOR
- 26819 NORMAL Sabre clipped-chroma validity: byte-frozen.
- 26818 VGN green residual cleanup: byte-frozen.
- 26800 classifier: byte-frozen.
- normalDngMerge, MotionV2Render host, DNG accumulator/lifecycle and alignment/merge weights: byte-frozen.
- SHORT, Resolve, exposure/frame policy, tone, SDR/UHDR, native/vendor and DNG writers: protected.

UPLOAD IN VSCODE.DEV — EXACTLY THREE STAGES

1) Upload/replace everything inside STAGE_1_UPLOAD_FIRST/ at repository root.
   Commit and push exactly:
   26821: prepare connected false color and DNG all-phase coherence
   This stage must NOT start the build.

2) Upload/replace STAGE_2_UPLOAD_SECOND/.github/workflows/build-26821-connected-false-color-dng-all-phase-coherence.yml
   Commit and push exactly:
   26821: add connected false color and DNG all-phase workflow
   This stage must NOT start the build.

3) Upload/replace both files inside STAGE_3_UPLOAD_LAST/ at repository root.
   Commit and push exactly:
   26821: activate connected false color and DNG all-phase build
   Only this stage triggers the workflow.

Expected workflow: Build 26821 Connected False Color + DNG All-Phase Coherence
Expected artifact: photon-26821-connected-false-color-dng-all-phase-coherence
Expected APK: IrisCamera-0.9726821-26821-connected-false-color-dng-all-phase-coherence-debug.apk
