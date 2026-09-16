PHOTON CAMERA 26648 R1.2 — APK ARTIFACT PACKAGING REPAIR

Upload/replace every path listed in R1_2_26648_UPLOAD_PATHS.txt into experimental-clean-photon-rebuild, commit once, push once.

This is a packaging-only repair. Runtime authority is the exact successful 26648 R1.1 compiled candidate from commit 4dfea0e55f74f18dce453eff4fcdd265f4634f01, Actions run 35052623377, artifact 10429058098, candidate TAR SHA-256 5b4bbc97b0958e7bcf68bfb39651fee051271610ffc69d8d8692eb664c1f46ca.
Runtime delta from R1.1: exactly 0 files / 0 additions. The eight payload files are identity witnesses and must equal the successful R1.1 candidate.

The R1.1 runtime build itself passed real glslang 16.5.0, Kotlin, Java, both NDK ABIs, full assemble, one-APK proof and post-build invariance. R1.1 artifact publication omitted the APK because its build FINAL basename and workflow upload basename differed. R1.2 makes those names exactly identical and adds an explicit pre-upload test -f gate plus a verifier that fails any future mismatch.

No backup created. Target remains 0.9726648 / 26648. Do not modify dev.
