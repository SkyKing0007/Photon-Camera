PHOTON 26858 — EXACT SUCCESSFUL 26857 GUARDED A/B BUILD

BRANCH: experimental-clean-photon-rebuild only. NO backup, no dev, no APK push.
Last SUCCESSFUL runtime authority: 26857 run 39357853711 / commit
26db71e77eb54cf59b9e94f3deb12946c9b11f76 / artifact 12236078590.
Verification mechanics: exact successful 26857 inherited 17 stages, same real
compiler, native and Gradle commands, protected file freeze and patch order.

UPLOAD IN THREE SEPARATE STAGES USING vscode.dev (all <100 files):
1. Unzip STAGE_1_ROOT and upload its CONTENTS to the repository root with paths
   intact (never the stage-folder name). Commit+push the new guarded source,
   proof, validators and patch package. This does not trigger the 26858 workflow.
2. Unzip STAGE_2_WORKFLOW and upload its .github/workflows path intact.
   Commit+push once; still does not trigger 26858.
3. Only AFTER stages 1+2 complete, unzip STAGE_3_TRIGGER and upload the root
   TRIGGER_26858.txt file. Commit+push once. Exactly this action triggers 26858.

DO NOT UPLOAD handoff_payload_26858/app/* directly into live app/src. The
inherited build script reconstructs the exact successful 26857 compiled
candidate and overlays only four frozen changed files, then replaces the
compiler live app with that candidate in guarded Actions.

INTENDED RUNTIME: 3 B-only source paths (2 modified, 1 added), plus
app/version.properties = 0.9726858 / 26858.
A separately owned source/algorithm, B AMaZE math, LONG luminance only,
26857 WB, lens settings, DNG/UHDR, native/vendor/shader assets are protected.
The explicit changed-file allowlist and SHA manifests are authoritative.

Before successful Actions: this package is PREPARED / UPLOAD-READY only.
Pinned GLSL, real project Kotlin/Java, NDK and full assemble have NOT RUN locally.
If an Actions gate fails, STOP, retain artifacts/logs and do not bypass gate.
No commits/pushes performed by ChatGPT.
