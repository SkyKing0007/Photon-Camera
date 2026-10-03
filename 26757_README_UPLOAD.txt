PHOTON 26757 — EVIDENCE-LIMITED FAST PLAN-B + NO-WAIT SUPER RES

Runtime authority:
  successful 26756 Actions run 37136416615
  commit c5ecc2a67ba375aa5f7d78ab8a59e7d36cd7aa0c
  artifact 11277954295 / photon-26756-plan-b-jni-lifetime
  artifact SHA-256 68e50cdd2fe1af5141d67c8803a180b3016e535a04f64d28f7ca90ece9a96d4a
  candidate TAR SHA-256 394686abc7f043c9b9369bc164da8084a69f0df87088490399b03a11257b3dc3

Verification-mechanics authority:
  exact successful 26752 build/handoff sequence; stage/toolchain/order unchanged.

Backup: NONE.
Runtime changed-file allowlist: exactly 5 existing files; 0 additions/deletions.

Prepared behavior:
  - Super Res frame slider is a maximum: use exact-exposure ZSL NORMALs already owned at shutter when >=4; top up only to four if fewer exist; non-SR exact-count policy unchanged.
  - full-frame Super Res uses the already-current direct-CFA GPU-first 2x owner; no CPU Plan-B RAW staging or 50 MP Fourier reconstruction in the normal SR path.
  - Sabre still merges every admitted NORMAL; high-zoom Plan B uses a deterministic phase-diverse detail subset (up to 6 for <=2x, 9 for <=3x).
  - high zoom solves only evidence-supported <=3x scalar detail, then existing final VGN/Sabre publication samples that detail once; no second RGB scaler and no RGB/chroma/highlight ownership change.
  - Plan B uses the mathematically equivalent smaller primal alias-space Moore-Penrose solve and FFT-friendly 976-core tiling on the proven radix2/Bluestein implementation; the 32 MiB solver cap and hard 4 s tile / 20 s stage watchdogs remain unchanged.
  - 26756 JNI lifetime correction, 26755 RAW release, physical-camera ownership, Section-7 luma enhancement, universal local-30x zoom, DNG/UHDR, and all 271 shaders are preserved.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path in this handoff EXCEPT:
  .github/workflows/build-26757-evidence-limited-fast-plan-b.yml
Commit message:
  26757: prepare evidence-limited fast Plan-B correction

STAGE 2 — upload only:
  .github/workflows/build-26757-evidence-limited-fast-plan-b.yml
Commit message:
  26757: activate evidence-limited fast Plan-B build

Do not upload an APK. Do not modify dev. GitHub Actions is authoritative for Kotlin/Java/both-ABI NDK/full assemble proof.
Expected artifact: photon-26757-evidence-limited-fast-plan-b
Expected APK: IrisCamera-0.9726757-26757-evidence-limited-fast-plan-b-debug.apk
