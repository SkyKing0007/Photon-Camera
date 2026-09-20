PHOTON / IRIS 26675 R1 — PREVIEW-DECOUPLED HDR + PROTECTED-NORMAL SHORT ADMISSION + MANUAL VISIBLE-ICON MIDPOINT

STATUS: PREPARED / UPLOAD-READY ONLY. GitHub Actions real compiler/build proof is required before 26675 becomes runtime authority.
BACKUP: NONE, by explicit request.
BRANCH: experimental-clean-photon-rebuild
EXPECTED PARENT / RUNTIME AUTHORITY: successful 26674 commit c73b5e95be2b1d762f044d79318603afa1d8b0d3
ACTIONS AUTHORITY: run 35492860182 / artifact 10600250297 / photon-26674-r1-protected-normal-manual-geometry
ARTIFACT SHA-256: c370ebc345468e9238546b8df765a9d00a20f823e2cba3b6a3dd75bae07fd41f
COMPILED-CANDIDATE TAR SHA-256: 106354ca57e85acba47851be060f7cabf48a402d604876ffb2fbf49df6639a61
VERIFICATION-MECHANICS AUTHORITY: exact successful 26674 build script blob 18bfa3508552b641faf873727b264f891307bd78 and workflow blob 40907c1831bbde676c38325f25587cf1911d33a8.
FUNCTIONAL INFRASTRUCTURE MECHANICS DELTA: ZERO.

RUNTIME SCOPE: exactly 8 modified files, 0 additions, 0 deletions. See R1_26675_RUNTIME_CHANGED_PATHS.txt.
PROTECTED SCOPE: 1718 non-allowlisted app files byte-identical; native-protected 806, vendor 778, DNG 7 byte-identical.

26675 CONTRACT
1. CAPTURE HARDLOCK: successful-26674 protected NORMAL sensor/ZSL acquisition, metadata, canonical FLOAT normalization, frame-exact metadata handoff and final HDR ownership are byte-identical. Preview presentation must never feed capture authority.
2. VIEWFINDER ONLY: the exact frame-matched protection gain is used only to reconstruct a virtual unprotected presentation and normal display clipping. Protected RAW/ZSL may improve invisibly; final JPEG/HEIC may recover highlights the preview shows as blown.
3. SHORT: when selected NORMAL carries meaningful highlight protection, inferred brightness difference alone cannot grant SHORT radiance authority; actual measured NORMAL source loss still can. Unprotected NORMAL retains the successful-26674 inferred-loss path.
4. MANUAL UI: buttons_container remains structural and translationY=0. The actual Focus/Shutter/ISO/EV top compound-drawable centers are measured and receive one identical frozen group translation to the midpoint between slider outer bottom and activated-chevron visible upper tip.
5. HEIC/UHDR gainmap/render, Local-Laplacian, final MotionV2 render, color, DNG, SR and protected NORMAL acquisition are not redesigned.

UPLOAD
Extract this entire handoff ZIP at the repository root in vscode.dev and replace matching files. Do not move handoff_payload_26675 into app/src manually. Do not upload an APK. Source Control must match R1_26675_UPLOAD_PATHS.txt exactly before commit/push.
Suggested commit message: 26675 R1: decouple HDR preview and refine short/manual geometry

LOCAL COMPILER STATUS: real GLSL/Kotlin/Java/NDK/full assemble are intentionally NOT claimed locally. The packaged GitHub Actions workflow performs the exact successful-26674 compiler/build sequence and becomes authoritative only after success.
