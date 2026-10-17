Photon 26849 — Peripheral phase-safe CFA fringe correction

Runtime authority: successful 26848 GitHub Actions compiled candidate.
Run: 38996199796
Commit: 99b7044a011c6c341c911c063bf42a64550be288
Artifact: 12086564293 photon-26848-same-material-rb-cfa
Artifact SHA-256: a38f0ded84a5b4a44e7f0ec04d61a51ee97978f72aa64ac13af14499d4bbb7ca
Candidate tar SHA-256: b12d98afeac501364ecce2455be0a5ca35e7159668c98b7f1b3b8e901452988b

Runtime scope: exactly GlesMgcRawSabreShaders.kt + app/version.properties.
26846 phase validity, 26847 green same-material ownership and 26848 R/B same-material ownership remain exact. With legacy LCA OFF, 26849 uses the already-calibrated same-phase R/B coefficients only through a smooth normalized outer-field ramp (0 through 0.40, full at 0.58+). The inner field is exact 26848 so the prior chandelier-green LCA regression cannot return there. Green is never shifted. Legacy user-enabled LCA remains mathematically unchanged.

Verification mechanics: exact successful 26848 17-stage sequence, zero mechanics deviation. No backup branch. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.
