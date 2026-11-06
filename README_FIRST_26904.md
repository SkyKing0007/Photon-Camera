# Photon 26904 — independent, change-aware Android build handoff

**This is a new release procedure**, not a tweak or bypass of the prior historical
17-stage generator. The user's goal is change-scoped source correctness, real
Android compiler execution in GitHub Actions and one APK. The first transition
build establishes compiler outputs for subsequent cache-aware builds. No APK
binary editing or substitution of the raw repository `app/src` occurs.

## Runtime authority and status

- Successful 26903 V3: Actions run 42064099430, commit
  `4a809afa81b885d2d47f27885d378763601fb667`, artifact 13433183917,
  artifact SHA `ff8c629e520c1afe96613a0d4295949852661dff6817d362bc99e188635a21aa`.
- Actual successful compiled 26903 candidate TAR SHA
  `da7773b9554c4db903e961a12a524e6990c3630295ce7c37efa23f8251ce561d`,
  2,027 source files. Executed successful runner SHA
  `a5e9b4923325a13d3ab54fbfe233f3fca0d79b3a6f43ae194fa5edcb1ab67b44`.
- The exact original 26903 Actions ZIP exceeds the connected download cap. Local
  development candidate was reproduced from the actual successful 26900 TAR,
  plus original SHA-verified 26901, 26902, 26903 stage overlays; every single
  recovered 26903 source file matches the successful expected source manifest.
- Local source edits: **six files** (rotation GLSL, AMaZE export GLSL,
  B-only Jin Java, Night B dispatch Java, native CMake release-version decoupling, version). A **seventh generated file**
  (`app/src/main/assets/iris26856/rawr/amaze/spv/amaze_export.spv`) must be
  compiled in Actions and proven as the ONLY additional candidate difference.
- Existing 26903 source and runner remain authority unless a new successful
  26904 Actions job with final artifact is published.

## Three-stage vscode.dev upload — SINGLE commit on experimental branch

1. Upload **all files inside `STAGE_1_PAYLOAD_VALIDATORS/`** to the repository
   ROOT, preserving their exact relative paths. Do not upload the wrapper.
2. Upload the single Stage 2 workflow to
   `.github/workflows/build-26904-change-aware.yml`.
3. Upload the single `TRIGGER_26904.txt` file to the repository ROOT **LAST**.
   Commit/push **ONCE** on `experimental-clean-photon-rebuild`.

The root trigger is immutable and the workflow filters on it ONLY. Do not touch
`dev`. Do not upload an APK, downloaded runner or entire compiled candidate.
The runtime overlay is **not** intended as directly installed `app/src` source:
Actions recovers the verified previous compiled candidate from the real
successful 26903 artifact, overlays only the six sealed files and generates
one real Vulkan SPV asset using pinned glslang/SPIR-V Tools.

## New change-aware Actions workflow

- Verify 26903 successful run/artifact, SHA of actual GitHub ZIP, ORIGINAL
  26903 internal compiled TAR, archived successful runner and all compiler
  receipts; verify complete 2027-file baseline manifest.
- Stage exactly six edited sources; verify all 2,027 precompile candidate
  hashes. Reconstruct canonical live app source, not stale checkout app/src.
- Run source ownership, 8-way rotation-coordinate geometry, original 26903
  rotation bug negative case, Java compiled Night B streak guard tests;
  protect Night A and B Photo routing.
- Compile real full expanded ESSL310 rotation shader watermark 1/0 and native
  Vulkan 1.1 AMaZE export using pinned real glslang 16.5.0, SPIR-V
  validation and optimization. Replace only the generated AMaZE SPV asset.
- Restore Gradle's input-aware task/dependency cache. Restore native CMake
  `.cxx` object outputs ONLY from an exact-native-source SHA and GitHub
  runner-image/toolchain provenance key computed AFTER the trusted source candidate is installed; no native prefix fallback
  and no old `app/build`/APK reuse. Every native-source or build-script
  change invalidates that object cache; the no-longer-consumed release
  version does NOT trigger needless C++ recompilation. The initial 26904 transition starts
  with no matching native `.cxx` cache and compiles both ABIs in Actions.
- Freeze source scope (seven and only seven file differences); run one real
  `:app:assembleDebug` with input-tracked Gradle task caches on GitHub Android
  SDK/NDK and JDK17, including both target ABIs and Kotlin/Java.
- Verify compiled source invariance, exactly one intended APK, archive new
  complete compiled-candidate TAR, receipt hashes and actual builder SHA.
- Upload one successful artifact with APK and complete source proof. Failed
  compiler, source SHA, unexpected native diff or missing APK blocks upload.

## Image-quality correction status — IMPORTANT LIMITATION

- **Proven 26903 defect:** rotation shader produced duplicate column 0/1
  for portrait 90 degrees. All orientation/mirror/crop geometry is corrected.
- **Provisional** B AMaZE output-border repair: physical 14px CFA agreement
  check, Bayer-parity mirrored neighborhood, native luminance held constant,
  no processing on confident edges, clipped highlights or weak signal. This is
  the most conservative source-level response to the remaining 8–10px gray
  border, whose FIRST damaging stage could not be proven without a same-shot
  native pre-/post-AMaZE readback. **Not device-proven to eliminate the strip.**
- **Provisional** B Night Jin-only after-ONNX directional residual acceptance
  guard: rejects model-only narrow same-sign coherent streaks in smooth very
  dark guides, preserving normal low light, true structures and existing
  Night A. Actual 26903 Night streak may originate before Jin; a pass here
  does not prove full physical scene correction.
- Frame counts, existing RAWR Fourier/Wiener, Super Res ON Wronski, DNG,
  Spektra, JPEG/HEIC and UHDR algorithms remain source-protected except the
  six intentional edits. The output needs an on-device side-by-side check.

## Compiler honesty

**Locally validated**: exact source-manifest and five-file diff, Javac-executed
unit tests, runtime shader import/syntax/source structural checks, package
negative tests, SHA seals and clean extraction. No local Android SDK/NDK,
pinned real glslang or phone GPU is present; **real shader compile, SPIR-V,
Kotlin, native ABIs and full APK are NOT RUN locally**. GitHub Actions performs
those real compiler steps. A handoff ZIP is PREPARED/NOT BUILD-PROVEN until a
successful new 26904 Actions job AND final artifact. Not a guarantee against
on-device artifacts; return logs and photos if either visible artifact remains.
