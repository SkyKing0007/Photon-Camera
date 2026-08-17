#!/usr/bin/env python3
from __future__ import annotations
import argparse, hashlib, json, tempfile, shutil
from pathlib import Path

EXPECTED_GENERATED = [
    "src/main/cpp/deps/archive.h",
    "src/main/cpp/deps/archive_entry.h",
    "src/main/cpp/deps/technicallyflac.h",
    "src/main/cpp/deps/tiny_dng_writer.h",
]
EXCLUDED_TOP = {"build", ".cxx", ".externalNativeBuild"}

def digest(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def files_under(app: Path) -> dict[str, str]:
    out = {}
    for p in sorted(app.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(app).as_posix()
        first = rel.split("/", 1)[0]
        if first in EXCLUDED_TOP:
            continue
        out[rel] = digest(p)
    return out

def snapshot(app: Path, manifest: Path) -> None:
    data = files_under(app)
    manifest.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print(f"SNAPSHOT_COUNT={len(data)}")

def verify(app: Path, manifest: Path) -> None:
    before = json.loads(manifest.read_text())
    after = files_under(app)
    before_keys = set(before)
    after_keys = set(after)
    deleted = sorted(before_keys - after_keys)
    added = sorted(after_keys - before_keys)
    changed = sorted(k for k in before_keys & after_keys if before[k] != after[k])

    if deleted:
        raise SystemExit("ERROR: Gradle deleted pre-existing app files: " + ", ".join(deleted))
    if changed:
        raise SystemExit("ERROR: Gradle changed pre-existing app files: " + ", ".join(changed))
    if added != EXPECTED_GENERATED:
        raise SystemExit(
            "ERROR: unexpected post-Gradle app additions; expected only generated native deps.\n"
            f"expected={EXPECTED_GENERATED}\nactual={added}"
        )
    ignore = app / "src/main/cpp/deps/.gitignore"
    if not ignore.is_file() or ignore.read_text().strip() != "*.*":
        raise SystemExit("ERROR: generated dependency directory is not protected by expected '*.*' .gitignore")
    print(f"PASS: {len(before)} pre-existing app files unchanged")
    print("PASS: only the four expected ignored native dependency headers were generated")

def self_test() -> None:
    root = Path(tempfile.mkdtemp(prefix="iris-v5-integrity-"))
    try:
        app = root / "app"
        (app / "src/main/cpp/deps").mkdir(parents=True)
        (app / "src/main/cpp/deps/.gitignore").write_text("*.*\n")
        (app / "src/main/java/X.java").parent.mkdir(parents=True)
        (app / "src/main/java/X.java").write_text("owned\n")
        (app / "version.properties").write_text("VERSION_BUILD=26498\n")
        (app / "build/generated.txt").parent.mkdir(parents=True)
        (app / "build/generated.txt").write_text("ignored-output\n")
        man = root / "manifest.json"
        snapshot(app, man)

        for rel in EXPECTED_GENERATED:
            p = app / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("generated\n")
        verify(app, man)

        (app / "src/main/java/X.java").write_text("mutated\n")
        try:
            verify(app, man)
        except SystemExit:
            pass
        else:
            raise AssertionError("owned-file mutation was not rejected")
        (app / "src/main/java/X.java").write_text("owned\n")

        rogue = app / "src/main/java/Rogue.java"
        rogue.write_text("rogue\n")
        try:
            verify(app, man)
        except SystemExit:
            pass
        else:
            raise AssertionError("rogue addition was not rejected")
        rogue.unlink()

        (app / "version.properties").unlink()
        try:
            verify(app, man)
        except SystemExit:
            pass
        else:
            raise AssertionError("deletion was not rejected")
        print("PASS: V5 source-integrity verifier self-test")
    finally:
        shutil.rmtree(root, ignore_errors=True)

def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("snapshot")
    s.add_argument("app")
    s.add_argument("manifest")
    v = sub.add_parser("verify")
    v.add_argument("app")
    v.add_argument("manifest")
    sub.add_parser("self-test")
    args = ap.parse_args()
    if args.cmd == "snapshot":
        snapshot(Path(args.app), Path(args.manifest))
    elif args.cmd == "verify":
        verify(Path(args.app), Path(args.manifest))
    else:
        self_test()

if __name__ == "__main__":
    main()
