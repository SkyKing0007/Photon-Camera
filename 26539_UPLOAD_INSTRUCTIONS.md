# 26539 V1.1 compile-only correction

This replaces the previous 26539 handoff files on `experimental-clean-photon-rebuild`.

Runtime architecture is unchanged from 26539. The only source correction is two `ImageSaver.java` logging calls: the nonfatal EXIF catches remain `Throwable`, but now use this project's `Log.w(tag, message, Throwable)` overload instead of passing `Throwable` to `Log.getStackTraceString(Exception)`.

Upload/replace all files in this package, preserving `.github/workflows/`. Do not create a backup branch. Do not modify or push `dev`.

Expected workflow: **Build 26539 V1.1 Compile Fix**

Expected artifact: `photon-26539-v1-1-night-owned-lifecycle-publication-pecan`
