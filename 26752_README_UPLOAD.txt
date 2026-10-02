PHOTON 26752 — IPOL PLAN B TRANSLATIONAL SUPER RESOLUTION

STATUS: PREPARED / UPLOAD-READY ONLY. GitHub Actions has not yet compiled 26752.
NO BACKUP BRANCH was created.

Runtime/IQ authority:
  successful 26733 run 36569631787
  commit 2f0ab8637816acd91a3a4ee331de910a47cad147
  artifact 11033487736 / photon-26733-highlight-safe-color-integrity
  artifact SHA-256 d27333374b4ab1dea2ea4bdb2deed85eab603b44a4eea5a65e4e343665becb52
  candidate TAR SHA-256 6feaf5ef8718f2d60ba6448393b31872644f56407eb89e6aa847f43381a34009

Verification-mechanics authority:
  successful 26751 run 37051394764
  commit de4f3e6389b4e3d94b1e0d5cbaad100818402757
  artifact 11247011528 / photon-26751-frozen-reciprocal-fine-color
  artifact SHA-256 3ecf4b7d3a27e71e91af9461dd2eead77985f79b068d6ee3542c94161eb421fa
  procedural/stage/toolchain delta: ZERO

IPOL authority:
  Abergel / Almansa / Moisan / Noûs, Linear Super-Resolution Through Translational Motion,
  IPOL 2026, DOI 10.5201/ipol.2026.550
  pinned reference implementation commit fef69ef44ed59a42e8f6b268bb6db9bcd0e6fec0

Version: 0.9726752 / 26752
Runtime changed-file allowlist: exactly 11 existing files; 0 additions/deletions.
Plan B starts at lens-relative local zoom >=1.10 on every physical lens/device and is also the Super Res ON luma/detail engine. Native 26733 Sabre/VGN remains RGB/chroma/highlight owner. Plan B never owns DNG. Bright/flattened highlight detail is fail-closed. Optional IPOL sharpening is intentionally not enabled. This revised handoff also includes the critical 26733 Motion capture repair: exact-timestamp early RAW staging and shutter-frozen NORMAL retry request mode.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path listed in 26752_UPLOAD_PATHS.txt EXCEPT:
  .github/workflows/build-26752-ipol-plan-b-translational-sr.yml
Commit message:
  26752: prepare IPOL Plan B translational SR

STAGE 2 — upload only:
  .github/workflows/build-26752-ipol-plan-b-translational-sr.yml
Commit message:
  26752: activate IPOL Plan B translational SR

Do not upload an APK. GitHub Actions is the authoritative real GLSL/Kotlin/Java/both-ABI NDK/full assemble proof.
Expected Actions artifact: photon-26752-ipol-plan-b-translational-sr
Expected APK: IrisCamera-0.9726752-26752-ipol-plan-b-translational-sr-debug.apk
