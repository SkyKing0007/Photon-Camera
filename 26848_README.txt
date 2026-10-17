Photon 26848 — Same-material R/B CFA topology

Runtime authority: successful 26847 GitHub Actions compiled candidate.
Run: 38993894728
Commit: 7a013fe72f39de8d115ffe9695160d9248778079
Artifact: 12086711684 photon-26847-same-material-cfa
Artifact SHA-256: e28daf6a62dd386c898d281008583e1215540137ee6793fe40b83d7f0a1e8627
Candidate tar SHA-256: 901559c201f8a041d67ebaba40d332fba73cdbf855e19e7c2d73c93803723714

Runtime scope: exactly GlesMgcRawSabreShaders.kt + app/version.properties.
26847 same-material green topology is preserved exactly. 26848 changes only R/B contributor ownership inside the same active NORMAL CFA->chroma function: at a green-proven material boundary, weaker same-channel Sabre RBF contributors are continuously de-emphasized while the strongest output-side sample stays exact. LCA remains unchanged; no post-RGB neutralization, no hue borrowing, no luma/detail owner change.

Verification mechanics: exact successful 26847 17-stage sequence, zero mechanics deviation. No backup branch. GitHub Actions is authoritative for real GLSL/Kotlin/Java/NDK/full assemble proof.
