PHOTON 26755 — RAW-LIFETIME + BOUNDED PLAN-B

Runtime authority:
  successful 26754 Actions run 37129226664
  commit 9dfdc3980bbf1fd7378c6b157793c3200d50fc76
  artifact 11276112743 / photon-26754-physical-owner-streaming-ipol
  artifact SHA-256 e20320de6c386ab56d56e265131e98c96a71ee89746b0602ead41ff8d7c87391
  candidate TAR SHA-256 e33636de48a49ad431ad1f19d047d8760e24d0bedb3cc6ba4847b82be21058d7

Verification-mechanics authority:
  exact successful 26752 build/handoff sequence; stage/toolchain/order unchanged.

Backup: NONE.
Runtime changed-file allowlist: exactly 3 existing files; 0 additions/deletions.

Prepared behavior:
  - after Sabre/VGN has consumed the immutable burst, every admitted NORMAL RAW is copied byte-exactly to independent disk backing before any Plan-B Fourier allocation;
  - original in-memory SafeImage/ImageFrame RAW owners are released only after the complete staged population is proven;
  - Plan B reads only bounded RAW regions from the disk-backed population; fixed 14-frame ownership and physical-camera isolation are unchanged;
  - solver-owned memory is capped at 32 MiB, core tile candidates start at 512 and auto-reduce to 128, native FFT worker reduction remains active;
  - hard RAW staging bound is 8 s; existing Plan-B 20 s stage / 4 s tile bounds remain;
  - real fix-path proof markers record process RSS before/after RAW release and first native tile begin/done;
  - 26754 physical-camera ownership, streaming publication, IPOL Section-7 luma enhancement, universal local-30x zoom, Sabre/VGN RGB/chroma/highlight ownership, DNG/UHDR, and all 271 shaders are preserved.

UPLOAD IN TWO STAGES so only the intended new workflow fires once:

STAGE 1 — upload/replace every path in this handoff EXCEPT:
  .github/workflows/build-26755-raw-lifetime-bounded-ipol.yml
Commit message:
  26755: prepare raw-lifetime bounded IPOL correction

STAGE 2 — upload only:
  .github/workflows/build-26755-raw-lifetime-bounded-ipol.yml
Commit message:
  26755: activate raw-lifetime bounded IPOL build

Do not upload an APK. Do not modify dev. GitHub Actions is the authoritative Kotlin/Java/both-ABI NDK/full assemble proof.
Expected artifact: photon-26755-raw-lifetime-bounded-ipol
Expected APK: IrisCamera-0.9726755-26755-raw-lifetime-bounded-ipol-debug.apk
