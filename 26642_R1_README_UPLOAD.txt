PHOTON/IRIS 26642 R1 — HEIC ANDROID-16 COMPATIBILITY + UI/SETTINGS CLEANUP + PHOTO PREFIX NAME

Runtime authority:
  successful 26641 R1 commit 6856814b2e072a7c9974f7b93f2d946dd9d1947e
  Actions run 34924928568
  artifact 10379707013
  artifact SHA-256 a321bfce16db3a8cc2b3fb56818aeb2f76c157a87e89f84226312daf5e70e89d
  deterministic candidate TAR SHA-256 66ae8daf38c96067ac227d38c768cdf284450c8b1775dc323f72ec00560de9f9

Verification-mechanics authority:
  exact successful 26641 implementation (build-script blob 53bf57126a97d684a35c3d2a04e33bcdaa4f31ee; workflow blob 1577eeb875644495578e08196514fd7c0bc99c47), preserving the successful 26639 compiler/build/patch/PRE-BUILD/assemble/postbuild ordering.

Target: 0.9726642 / 26642
Backup: none created/requested. 26642 is a localized HEIC compatibility + UI/settings/filename change.

Runtime changes: exactly 14 paths: 12 modified + 2 added. See R1_26642_RUNTIME_CHANGED_PATHS.txt and R1_26642_ADDED_PATHS_MUST_BE_ABSENT.txt.
Infrastructure changes: 26642 identity/authority/scope/regressions, 0-GLSL applicability, and the minimal patch-verifier cleanup required for two legitimate added runtime files. Compiler/build order is unchanged from successful 26641.

Implementation owners:
  A) HEIC compatibility: retain successful 26641 base/gain hardware color signaling and ISO 21496 gain metadata, but align the tmap derived-item publication with Android 16 framework semantics: 8-bit, Display-P3/sRGB base authority, unspecified gain-map color aspects. Add post-save Android framework decode proof for both JPG and HEIC (hasGainmap + decoded metadata) without altering saved bytes.
  B) Mode selector UI: remove the legacy visible Photo action, relabel the proven internal Motion route as visible Photo, collapse the picker to five entries, and map any persisted legacy PHOTO selection to MOTION so startup never falls to Unlimited.
  C) Quick/settings cleanup: remove Exposure Bracketing from the quick settings provider so Super Res/settings reflow; remove Process 4x lower resolution, Battery saver, Hide gallery icon, Bayer filter pattern, Align method, Color method, and Tunable Settings from the full Settings UI.
  D) Photo filename prefix: add General > Prefix Name directly below Per Lens Settings with the exact dialog title "Photo Prefix Name", default IMG_, persistent global storage, literal underscore behavior, and filename-safe validation. Video naming remains VID_.

Frozen successful 26641 behavior:
  true matched SDR/HDR UHDR quotient, 1536x2048 Motion gain map, measured stored-range metadata, shared-GL correction, SHORT/Sabre, color/denoise/Local-Laplacian/highlight, capture routing, DNG and all 257 asset shaders remain byte-identical unless listed in the 14-path runtime allowlist.

Upload workflow:
  Extract this ZIP locally.
  In vscode.dev on branch experimental-clean-photon-rebuild, upload/replace every path listed in R1_26642_UPLOAD_PATHS.txt exactly.
  Confirm Source Control shows exactly that upload scope and no live app/ path.
  Commit once and push. Do not manually edit runtime source.
  The 26642 workflow reconstructs from the successful 26641 Actions artifact and runs the same guarded compiler/build sequence as successful 26641.

Before Actions, this handoff is PREPARED / UPLOAD-READY only. Real Kotlin/Java, both NDK ABIs, full assemble, one-APK proof and post-build invariance become authoritative only after the 26642 Actions run succeeds. Real GLSL is not applicable because all 257 asset shaders are byte-identical to successful 26641.
