PHOTON 26870 — PREPARED / UPLOAD-READY

RUNTIME AUTHORITY: exact successful 26868 compiled-candidate Actions run 39863379652,
commit 7800265e6a5909ddea770c93cfeaed244c489247,
artifact 12462853558 ZIP sha256 c22e4b592ff63884f6bdce1c1dba2d4543be5f2cf3b017ee957678f9b431241b.
Exact source tar sha256 7ac33dfa920060b97465e6a1815573f56cdaf5548e444abd20d9366063ec5596.

VERIFICATION-MECHANICS AUTHORITY: exact successful 26868 guarded 17-stage
script git blob 1117b831cb4582db3f5949db11e93fde56fa6e33,
including canonical authority-seeded source, strict 8-file allowlist, pinned
GLSL ES and SPIR-V compilation, real Kotlin/Java compiler, native two ABI
compiler, full :app:assembleDebug, patch replay, prebuild proof and final
clean-extract artifact checks. No stage reordered or removed.

LIVE REPO BRANCH: experimental-clean-photon-rebuild; required upload scaffold
base HEAD ddb0538cd11c061755862c91e5595e12f018cf96.
26869 compiled but FAILED device acceptance; it is NOT runtime source authority.
This handoff starts from successful 26868 compiled-candidate source, and does
NOT copy the broken 26869 settings/persistence implementation.

RUNTIME CHANGED ALLOWLIST: 8 paths, see 26870_CHANGED_ALLOWLIST.txt.
1992 prior files -> 1994 candidate, 1986 unchanged protected bytes.
No settings, experiment selection, per-lens persistence, DNG, native/vendor
or generated module scaffolding changed. A/NIGHT/LONG isolated.

Automatic B-only changes:
* GPU RAW16 structural reliability reference ranking over frozen NORMAL frames,
  gate noise/highlight/sparse/reliability and prefer shutter-ref fallback;
  both HDRq and Wronski use selected native reference.
* One B-native post-AMaZE camera-linear local RGB residual chroma pass before
  Lab defringe and FCC; fused into the existing temporary WB pass with two
  distinct GL program caches for native vs legacy ownership, no new full-frame
  RGBA texture. Local structural and hue protection + bounded anticipated
  presentation amplification. The native RAWR burst noise estimator remains
  genuine but does NOT expose pixelwise variance to this new shader; the new
  pass relies on actual post-AMaZE local RGB evidence, not falsely fabricated
  measured temporal confidence.
* Scene-percentile/gain automatic B-only near-black toe inside existing linear
  manual tone node (no new settings or extra independent tone mapper).

INFRASTRUCTURE:
Existing successful 26868/26869 infrastructure files are NOT modified.
New 26870 versioned build script/validators/regressions/manifests/workflow,
plus 26870 trigger. The guard's 17 stage ordering and real compiler commands
are exact inherited. The new-versioned build-script contents differ from
26868 to implement this version, protect the changed files, verify the
historical 26869 nested validator failure and enforce the new source checks.
These differences are intentional and manifest-audited.

REAL GLSL+SPIRV+KOTLIN+JAVA+NDK+FULL ASSEMBLE: NOT RUN LOCALLY.
The Github Actions workflow MUST run ALL of them before 26870 is BUILD-PROVEN.
The previous successful 26868 real compiler proof does not prove these changes.

UPLOAD IN vscode.dev ONLY. DO NOT RUN .sh LOCALLY, COMMIT FROM CHATGPT,
CREATE A BACKUP, COPY app/src DIRECTLY, OR UPLOAD APKs.

1) S1: upload ALL contents into EXACT repository-relative paths; the runtime
   replacements stay under handoff_payload_26870/app/**. Commit and push:
   26870 Stage 1: Rebuild B automatic IQ from verified 26868 authority
2) S2: upload .github/workflows/build-26870-iris-rawr.yml only.
   Commit and push:
   26870 Stage 2: Add isolated guarded 17-stage Actions workflow
3) S3: upload TRIGGER_26870.txt only, LAST. Commit and push:
   26870 Stage 3: Trigger guarded automatic B IQ build

Stage 3 alone triggers workflow (push paths only TRIGGER_26870.txt).
The script reconstructs source from Actions 26868, then compiles/assembles.
Expected one root APK IrisCamera-0.9726870-26870-iris-rawr-debug.apk.
After Actions succeeds, inspect actual Android runtime before acceptance.

HASH MANIFEST: 26870_HANDOFF_HASHES.sha256 (all upload files excluding itself).
STRICT SCOPE: 26870_REPOSITORY_UPLOAD_ALLOWLIST.txt.
