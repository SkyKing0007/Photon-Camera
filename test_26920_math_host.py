#!/usr/bin/env python3
"""Supplemental real C++17 numerical test, never a stand-in for Android/GLSL."""
from pathlib import Path
import subprocess,tempfile
R=Path(__file__).resolve().parent
with tempfile.TemporaryDirectory(prefix='photon26920_host_cpp_') as d:
 exe=Path(d)/'lk_active_test'
 subprocess.run(['c++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(R/'tests_26920/test_26920_active_math.cpp'),'-o',str(exe)],check=True)
 subprocess.run([str(exe)],check=True)
