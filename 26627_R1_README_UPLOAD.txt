PHOTON CAMERA 26627 R1 — ADAPTIVE COLOR + SAFE LOWER CONTROLS

UPLOAD TARGET
Branch: experimental-clean-photon-rebuild
Expected direct parent HEAD: 8c6754f06ba0c8c36002c17372d7be1eab6daa43
Target version/build: 0.9726627 / 26627
Backup: NONE (user explicitly requested no backup)

RUNTIME AUTHORITY
Successful 26626 R1 commit: 8c6754f06ba0c8c36002c17372d7be1eab6daa43
Actions run: 34599600068
Artifact ID: 10262774952
Artifact name: photon-26626-r1-bounded-source-structure-short-proof
Artifact ZIP SHA-256: 153ce6abb195f25bd42c459cbc447597f71faf349911f3be3f587759961f44d8
Exact compiled candidate TAR SHA-256: 0d587fc5ba3d239b4496be72979ad4d9bc7dfeca1c4a248c137a14087ffff712

VERIFICATION-MECHANICS AUTHORITY
Exact successful 26626 direct sequence is preserved:
sealed package -> exact prior compiled artifact -> deterministic candidate -> semantic/regression/domain checks -> complete modified runtime-expanded GLSL reserved scan -> pinned real glslang -> authority-seeded live candidate -> real Kotlin/Java -> both NDK ABIs -> deterministic patches -> PRE-BUILD -> full :app:assembleDebug -> exactly one APK -> post-build invariance -> deterministic candidate export.
There is NO wrapper, NO git replace/graft, and NO --local-prebuild invocation from GitHub Actions.

INTENDED RUNTIME CHANGED-FILE ALLOWLIST — EXACTLY FOUR
1. app/src/main/assets/shaders/motionv2/adaptive_color_appearance_26563.glsl
2. app/src/main/java/com/particlesdevs/photoncamera/processing/render/IrisJpegColorSolver.java
3. app/src/main/java/com/particlesdevs/photoncamera/ui/camera/CameraUIViewImpl.java
4. app/version.properties

COLOR
- Reject ForwardMatrix only for the strict dual-illuminant placeholder pattern: both FM anchors present and identical <=1e-6, both ColorMatrices present and materially different >=0.05, and reference illuminants differ.
- Reuse the inherited ColorMatrix + CameraCalibration + Bradford fallback; no new color domain or Camera2 gain/WB owner.
- Profileless appearance adds bounded coherent medium-chroma restoration, still under inherited shadow/highlight/edge/coherence/gamut gates and the existing 1.32x cap.
- Calibrated-profile path remains exact bypass.

UI
- Chevron/manual-toggle owner remains inherited and is not moved by the new safe-region function.
- Selected lens fill is kept >=10dp below measured dummy/viewfinder edge and >=8dp below the chevron/manual-toggle stack.
- Lower mode selector is kept >=18dp above the actual Android navigation/mandatory-gesture bottom inset.
- Preferred full-size layout is retained when possible; flexible gaps reduce first; only then shutter/gallery/camera-switch/mode selector use one shared proportional scale.

PROTECTED OWNERS
All SHORT/Sabre/CFA reconstruction, global tone/Local-Laplacian, true2x/SR, UHDR/gain-map, AE/exposure, DNG, denoise, native and vendor paths are unchanged.

INFRASTRUCTURE SCOPE
26627 handoff/build/validator files are identity/scope adaptations of the exact successful 26626 direct sequence. Core compiler/NDK/patch/PRE-BUILD/assemble/postbuild order is unchanged and Actions verifies the exact successful 26626 build/workflow/transform SHA-256 before runtime source writes.

UPLOAD IN VSCODE.DEV
1. Confirm branch experimental-clean-photon-rebuild and visible HEAD 8c6754f06ba0c8c36002c17372d7be1eab6daa43.
2. Extract this ZIP locally.
3. Upload/replace ALL extracted files into repository ROOT, preserving paths.
4. Do NOT manually copy handoff_payload_26627_r1/app/** into live app/**. Actions reconstructs the candidate from successful 26626 compiled authority plus the canonical patch.
5. Source Control should show only this sealed 26627 handoff package; there should be no live app/** runtime edits.
6. Commit once and push once.

Suggested commit message:
26627 R1 adaptive color and safe lower controls

Expected workflow:
Build 26627 R1 Adaptive Color + Safe Lower Controls

STATUS BEFORE ACTIONS
Prepared/upload-ready only after local clean-extract replay. Real pinned glslang, project Kotlin/Java compilers, both NDK ABIs, full :app:assembleDebug, exactly-one-APK and post-build invariance are authoritative only after GitHub Actions succeeds.
