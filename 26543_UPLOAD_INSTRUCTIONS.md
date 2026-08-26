# Photon 26543 V1.3 upload instructions

Target: `0.9726543 / 26543` on `experimental-clean-photon-rebuild`.

V1.3 keeps the audited V1.2 Figure-7 + bounded-Night architecture and fixes only the Kotlin compiler errors exposed by the real V1.2 Gradle run:

- converts `FloatArray.average()` results from Double back to Float after Double-domain clamping;
- passes the existing `BayerKernelTuning` explicitly into low-memory `renderRgbMerge()`;
- uses that local parameter for banded Figure-7 covariance reconstruction.

Upload all extracted handoff files, replacing the previous 26543 handoff files. Do not edit `app/src` manually. The workflow reconstructs exact successful 26542 as runtime authority.
