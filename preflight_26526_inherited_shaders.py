#!/usr/bin/env python3
from __future__ import annotations
import argparse, subprocess, tempfile
from pathlib import Path

SHADERS = [
    "app/src/main/assets/shaders/preview/main_fs.glsl",
    "app/src/main/assets/shaders/motionv2/render.glsl",
    "app/src/main/assets/shaders/motionv2/gainmap.glsl",
]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--validator", default="glslangValidator")
    a = ap.parse_args()

    with tempfile.TemporaryDirectory(prefix="iris26526_glsl_") as td:
        td = Path(td)
        for i, rel in enumerate(SHADERS):
            p = a.root / rel
            if not p.is_file():
                raise SystemExit("missing " + rel)
            body = p.read_text(encoding="utf-8").replace("\r\n", "\n")
            f = td / f"inherited_{i}.frag"
            f.write_text("#version 300 es\n" + body, encoding="utf-8")
            cp = subprocess.run(
                [a.validator, "-S", "frag", str(f)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            if cp.returncode != 0:
                print(cp.stdout)
                raise SystemExit("glslang failed " + rel)
            print("PASS: glslang " + rel)
    print("PASS: inherited preview/render/gainmap shaders compile unchanged")

if __name__ == "__main__":
    main()
