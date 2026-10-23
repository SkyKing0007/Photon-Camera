PHOTON 26871 — PREPARED / UPLOAD-READY FOR VSCODE.DEV
This is the final guarded SOURCE HANDOFF, not an APK and not a locally build-proven release.

Branch: experimental-clean-photon-rebuild
Prior successful runtime: 26870 GitHub Actions run 39954786811
Prior HEAD: 5e567577a06053a1feb2a94bd40681c2731ce554
Prior artifact ID: 12502775416
Prior artifact ZIP SHA-256: 432b88b36857d477272ed5db64411491ac99d899f3b4e03a90ca7de439377cd1
Prior compiled candidate TAR SHA-256: 47ac58d8817353148f6d8ab98f01d995750c69002b3b763c424022e70cd78211
Prior guarded mechanics Git blob: 9d266c45e62ec3c8701acec6aaf1bf80b970a740
Generated 26871 guarded script SHA-256: ca2d99d38c1de9a310205ba2c2af0fd7b49399f506e39a24fa94a6f15a338e0e
Version: VERSION_NAME=0.9726871; VERSION_BUILD=26871

Precisely THREE runtime candidate files, under handoff_payload_26871/app/:
  app/src/main/java/com/particlesdevs/photoncamera/capture/CaptureController.java
  app/src/main/java/com/hinnka/mycamera/processor/GlesIris26870PostAmazeChroma.kt
  app/version.properties
They are NOT copied into the repository's live app/ by the user. GitHub Actions reconstructs the exact compiled candidate and installs it after all gates.

WHAT CHANGES:
  B-only NORMAL highlight exposure with real sensor headroom; B preview/ZSL HAL AUTO anti-banding request plus actual result logging; B-only equal-energy/different-shutter RAW admission check; multiscale post-AMaZE chroma cleanup.
  Experiment A, LONG luminance-only, RAWR HDRq/AMaZE architecture, native/vendor, DNG, UHDR and known destructive flicker-correction disablement remain protected.

CHECKS COMPLETED BEFORE UPLOAD:
  Exact successful 26870 artifact ZIP, candidate TAR and complete 1,994-file base hashes;
  deterministic candidate reconstruction; exact 3-file runtime allowlist;
  1,991 unchanged/protected-source hashes; full-index forward/rollback patches
  at 7/12/40 and fuzz=0; B ownership and shutter regression; static expanded
  GLSL identifier check; Python syntax; exact successful 26870 build script
  Git blob replay; deterministic guarded 26871 generator, original 17-stage
  order, unchanged real compiler commands, pinned generated script/diff hash,
  Bash syntax, clean-extraction and packaged hashes.
  Local pinned glslang, Kotlin/Java, NDK, and :app:assembleDebug NOT RUN.
  GitHub Actions MUST run these real compilers before build can be called successful.

VSCODE.DEV — THREE STAGES, ONE PUSH:
  1. Extract this ZIP. On experimental-clean-photon-rebuild, upload all files
     at their exact relative paths EXCEPT .github/workflows/build-26871-iris-rawr.yml
     and TRIGGER_26871.txt. Commit Stage 1 but DO NOT PUSH yet.
  2. Upload .github/workflows/build-26871-iris-rawr.yml; commit Stage 2
     but DO NOT PUSH yet.
  3. Upload TRIGGER_26871.txt; commit Stage 3 and PUSH once. This alone
     triggers the intended 26871 GitHub Actions build.
Do not upload any APK. Do not run .sh/.ps1 locally. No backup branch is needed.

WORKFLOW:
  Actions first checks sealed hashes and exact prior successful mechanics,
  generates the 26871 guarded script from the verified 26870 Git blob, obtains
  successful 26870 Actions candidate TAR, verifies it and overlays only the
  three listed candidate source files. Inherited real pinned GLSL/SPIR-V,
  project Kotlin/Java, native 2-ABI compiler, full APK assembly, patch proofs,
  PRE-BUILD SAFETY PROOF and final clean-extract replay are mandatory.

AFTER ACTIONS:
  Only a successful run with one intended APK, compiler proof, final source
  manifests, and post-build invariance makes 26871 the new runtime authority.
  Preview flicker and JPEG IQ require actual device evaluation after installation.
