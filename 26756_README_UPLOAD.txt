PHOTON 26756 — PLAN-B JNI LIFETIME CORRECTION

Runtime authority:
  successful 26755 Actions run 37133486763
  commit 34dab86e71e704e82ee171cb6a606079dacad6a9
  artifact 11278010569 / photon-26755-raw-lifetime-bounded-ipol
  artifact SHA-256 efdc257ac38a9087af74c6ab1ba0ef18b6c83c1b294e3c64fa4fec6f80650b7b
  candidate TAR SHA-256 4125ad77b048122ea46ded7a9db5f9f6a6791d515ce54e2620e6f9897aa71876

Verification-mechanics authority:
  exact successful 26752 build/handoff sequence; stage/toolchain/order unchanged.

Backup: NONE.
Runtime changed-file allowlist: exactly 2 existing files; 0 additions/deletions.

Prepared behavior:
  - fixes the exact 26755 first-tile JNI lifetime error: ReleaseStringUTFChars now occurs while its jstring local reference is still valid, before DeleteLocalRef;
  - permanent regression requires the exact 26755 failing source condition in authority and proves it is absent from 26756;
  - minimal real-path proof telemetry: PATH_BEGIN, PATH_UTF_ACQUIRED, PATH_UTF_RELEASED, DFT_DONE, plus inherited TILE0_NATIVE_BEGIN/DONE;
  - no unrelated native C++ drift; 26755 RAW staging/release, 32MiB solver cap, <=512 core tiles, physical-camera ownership, IPOL math/Section-7 enhancement, universal local-30x zoom, Sabre/VGN RGB/chroma/highlight ownership, DNG/UHDR, and all 271 shaders remain unchanged.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path in this handoff EXCEPT:
  .github/workflows/build-26756-plan-b-jni-lifetime.yml
Commit message:
  26756: prepare Plan-B JNI lifetime correction

STAGE 2 — upload only:
  .github/workflows/build-26756-plan-b-jni-lifetime.yml
Commit message:
  26756: activate Plan-B JNI lifetime build

Do not upload an APK. Do not modify dev. GitHub Actions is the authoritative Kotlin/Java/both-ABI NDK/full assemble proof.
Expected artifact: photon-26756-plan-b-jni-lifetime
Expected APK: IrisCamera-0.9726756-26756-plan-b-jni-lifetime-debug.apk
