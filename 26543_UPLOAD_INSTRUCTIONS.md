# Photon 26543 V1.4 upload instructions

Target: `0.9726543 / 26543` on `experimental-clean-photon-rebuild`.

V1.4 keeps the audited 26543 Figure-7 + bounded-Night architecture and incorporates all compiler corrections exposed by the real V1/V1.2/V1.3 Actions runs:

- GLSL reserved identifier `precision` -> `precisionCoeffs`;
- Kotlin `FloatArray.average()` Double->Float conversion and explicit `BayerKernelTuning` parameter flow;
- Java Night spool `ByteBuffer` is now explicitly `java.nio.ByteBuffer`, fixing the sole javac error from V1.3.

Upload all extracted handoff files, replacing the previous 26543 handoff files. Do not edit `app/src` manually. The workflow reconstructs the exact successful 26542 artifact as runtime authority, replays deterministic forward/rollback proofs, compiles active embedded shaders with pinned glslang 16.5.0, then runs the real Android Kotlin+Java compiler and assembleDebug in the same guarded block.
