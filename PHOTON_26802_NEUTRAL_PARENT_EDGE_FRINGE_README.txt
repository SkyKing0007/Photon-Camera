PHOTON 26802 NEUTRAL-PARENT EDGE-FRINGE

Runtime authority:
- successful 26801
- commit d4f9539cb523a771aec10c570dc505b2624a2d7c
- Actions run 38061616847
- artifact 11673073279
- artifact name photon-26801-telemetry-gl-cleanup-repair
- artifact SHA-256 3a9c27a88be6a8d9439137b3719f497d8100c5eda1b03873d3dca5dc7ea4e3dd
- candidate TAR SHA-256 7cf74bd5eecb377099c4fce7684ffd679f0fddf24c6083380377948ee5363ec4

Verification mechanics:
- exact successful 26801 17-stage build/handoff procedure
- root mechanics authority successful 26752
- no backup branch
- no source commit/push performed by ChatGPT

26802 runtime allowlist: exactly 3 modified paths
- app/src/main/assets/shaders/motionv2/false_color_classify_26800.glsl
- app/src/main/java/com/particlesdevs/photoncamera/processing/opengl/postpipeline/MotionV2Render.java
- app/version.properties

26802 correction:
- keeps successful 26800 high-chroma classifier and 26799 recursive connectivity/correction architecture
- adds a narrow, hue-independent achromatic-core / neutral-parent edge-fringe admission
- evidence is geometric: extreme neutral/high-luminance parent, edge-normal narrow chroma excursion, and lack of same-hue persistence into the outer material
- does not require an opponent hue, so green/cyan chandelier fringe and magenta/yellow-green grow-light fringe can enter the same correction
- strict true-2D material protection remains intact except for this narrowly proven fringe topology
- reuses the existing correction strength; render.glsl is unchanged
- reuses previously unused 28-entry stats counter 19; no telemetry buffer resize

Frozen behavior:
- exact successful 26799 8-pass propagation
- existing connected correction strength, luma preservation, and ordering before presentation tone
- 26801 telemetry-buffer ownership repair
- 26801 Motion failure-safe GL cleanup
- Sabre/VGN/denoise/bridge/color transform/ACR3/exposure/tone/LCA/UHDR/DNG/SR/native/vendor
- luma/detail path
- genuine colored materials and broad scene illumination

Permanent regression intent:
- admit thin unsupported green/cyan fringe around neutral chandelier bulb/chrome boundaries
- admit thin unsupported magenta/pink/yellow-green fringe along near-white grow-light emitter boundaries
- do not require alternating/opponent hue topology
- preserve green foliage, flowers, colored objects/materials, genuine colored emitters, and broad warm grow-light illumination
- do not reintroduce alternating zipper/dotted color, worm/maze/fuzzy-connected texture, broad desaturation, or luma/detail changes

COMPILER STATUS BEFORE UPLOAD
- real GLSL: NOT RUN locally
- real Kotlin: NOT RUN locally
- real Java: NOT RUN locally
- native/NDK: NOT RUN locally
- full assembleDebug: NOT RUN locally
GitHub Actions is authoritative. Until successful Actions proof, 26802 is PREPARED / UPLOAD-READY, not build-proven.

VSCODE.DEV UPLOAD / COMMIT / PUSH — USE THE SAME THREE-STAGE ACTIVATION PATTERN AS 26801

Stage A — sealed package except workflow/hash/trigger:
Upload/replace all files from this handoff EXCEPT:
- .github/workflows/build-26802-neutral-parent-edge-fringe.yml
- 26802_HANDOFF_HASHES.sha256
- TRIGGER_26802.txt
Commit and push Stage A.

Stage B — workflow only:
Upload:
- .github/workflows/build-26802-neutral-parent-edge-fringe.yml
Commit and push Stage B.
This workflow listens only to TRIGGER_26802.txt, so Stage B does not launch 26802.

Stage C — final seal + trigger:
Upload:
- 26802_HANDOFF_HASHES.sha256
- TRIGGER_26802.txt
Commit and push Stage C.
This should launch exactly one intended 26802 workflow.

Do not upload an APK from this handoff. GitHub Actions builds the authoritative APK.
