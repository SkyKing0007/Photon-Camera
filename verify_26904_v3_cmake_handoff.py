#!/usr/bin/env python3
"""26904 V3: preserve exact pinned real glslang from the shader step into CMake.

Only Actions --handoff writes GITHUB_ENV and a receipt.  --self-test exercises
this same selection/validation/CMake-probe code on controlled fixtures; it does
NOT claim a real Android compile.  Never alter runtime CMake or Spektra shaders.
"""
from __future__ import annotations
import hashlib
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent
TOOLS_REL = Path('.photon_26904_incremental_work/real_shader_tools')
ARCHIVE_NAME = 'glslang-16.5.0-linux-x86_64-release.tar.gz'
ARCHIVE_SHA = 'b9b1f96acb898a62251b171f7695efcecfc206a530299054071919b06820f657'
CMAKE_REL = Path('app/src/main/cpp/CMakeLists.txt')
EXPECTED_ENV_KEY = 'IRIS26681_SPEKTRA_GLSLANG'

# This is the literal SOURCE-compiled 26904 CMake search/require logic.
CMAKE_SEARCH = '''if(DEFINED ENV{IRIS26681_SPEKTRA_GLSLANG} AND EXISTS "$ENV{IRIS26681_SPEKTRA_GLSLANG}")
    set(IRIS26681_GLSLANG "$ENV{IRIS26681_SPEKTRA_GLSLANG}")
else()
    find_program(IRIS26681_GLSLANG NAMES glslangValidator glslang)
endif()
if(NOT IRIS26681_GLSLANG)
    message(FATAL_ERROR "IRIS_26681 requires the already-pinned glslang 16.5.0 compiler from the guarded build script")
endif()'''


def require(condition: bool, message: str):
    if not condition:
        raise AssertionError('26904 V3 BLOCKED: ' + message)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_cmake_guard(path: Path) -> str:
    require(path.is_file(), f'actual compiled CMake missing: {path}')
    content = path.read_text(encoding='utf-8')
    require(content.count(CMAKE_SEARCH) == 1,
            'compiled CMake Spektra glslang source contract changed')
    return sha(path.read_bytes())


def select_pinned_compiler(tools: Path, archive_pin: str, expected_version: str = '16.5.0') -> tuple[Path, str, str]:
    archive = tools / ARCHIVE_NAME
    require(archive.is_file(), f'original V2 pinned glslang archive missing: {archive}')
    require(sha(archive.read_bytes()) == archive_pin, 'pinned archive SHA mismatch')
    extract_root = (tools / 'glslang').resolve(strict=True)
    # Reuse the EXACT filename preference and `find -print -quit` lookup used
    # by the real successful 26904 V2 shader step.  No different compiler.
    candidate = None
    for name in ('glslang', 'glslangValidator'):
        result = subprocess.run(['find', str(extract_root), '-type', 'f', '-name', name,
                                 '-print', '-quit'], capture_output=True, text=True, check=True)
        if result.stdout.strip():
            candidate = Path(result.stdout.strip())
            break
    require(candidate is not None, 'no executable in SHA-verified glslang archive')
    compiler = candidate.resolve(strict=True)
    require(os.access(compiler, os.X_OK), 'compiler is not executable')
    require(compiler.is_relative_to(extract_root), 'compiler escaped pinned archive extraction')
    require('\n' not in str(compiler) and '\r' not in str(compiler), 'compiler path newline')
    r = subprocess.run([str(compiler), '--version'], capture_output=True, text=True, timeout=12)
    require(r.returncode == 0 and expected_version in r.stdout,
            'executable did not report pinned glslang ' + expected_version)
    return compiler, sha(compiler.read_bytes()), r.stdout.strip()


def cmake_probe(compiler: Path, cmake_file: Path) -> None:
    validate_cmake_guard(cmake_file)
    require(shutil.which('cmake') is not None, 'real cmake executable absent')
    # Run the EXACT CMake source contract (not a regex approximation), plus a
    # real execute_process call through CMake with the selected binary.
    text = CMAKE_SEARCH + '''
execute_process(COMMAND "${IRIS26681_GLSLANG}" --version
    RESULT_VARIABLE GLSLANG_EXIT OUTPUT_VARIABLE GLSLANG_STDOUT ERROR_VARIABLE GLSLANG_STDERR)
if(NOT GLSLANG_EXIT EQUAL 0)
    message(FATAL_ERROR "Pinned glslang cannot execute from CMake")
endif()
if(NOT GLSLANG_STDOUT MATCHES "16\\.5\\.0")
    message(FATAL_ERROR "CMake resolved a glslang with wrong version")
endif()
if(NOT "${IRIS26681_GLSLANG}" STREQUAL "$ENV{IRIS26681_SPEKTRA_GLSLANG}")
    message(FATAL_ERROR "CMake ignored explicit pinned compiler path")
endif()
'''
    with tempfile.TemporaryDirectory(prefix='photon26904_v3_cmake_') as t:
        probe = Path(t)/'actual-source-glslang-guard.cmake'
        probe.write_text(text)
        env = dict(os.environ, IRIS26681_SPEKTRA_GLSLANG=str(compiler))
        r = subprocess.run(['cmake', '-P', str(probe)], env=env, capture_output=True, text=True, timeout=15)
        require(r.returncode == 0, 'real CMake guard probe failed: ' + (r.stderr + r.stdout)[-600:])


def handoff():
    require(os.environ.get('GITHUB_ACTIONS') == 'true', '--handoff restricted to GitHub Actions')
    require(os.environ.get('GITHUB_REPOSITORY') == 'SkyKing0007/Photon-Camera', 'wrong repository')
    require(os.environ.get('GITHUB_REF_NAME') == 'experimental-clean-photon-rebuild', 'wrong branch')
    env_path = Path(os.environ.get('GITHUB_ENV',''))
    require(os.environ.get('GITHUB_ENV') and env_path.is_file(), 'GitHub cross-step environment file missing')
    root = ROOT
    tools = root / TOOLS_REL
    compiler, binary_sha, version = select_pinned_compiler(tools, ARCHIVE_SHA)
    cmake_sha = validate_cmake_guard(root/CMAKE_REL)
    cmake_probe(compiler, root/CMAKE_REL)
    receipt = (root/'photon_26904_incremental_outputs/26904_SPEKTRA_GLSLANG_CMAKE_HANDOFF.txt')
    receipt.parent.mkdir(parents=True, exist_ok=True)
    receipt.write_text('SOURCE: exact compiled 26904 CMake guard\n'
                       f'GLSLANG ARCHIVE SHA256: {ARCHIVE_SHA}\n'
                       f'GLSLANG EXECUTABLE SHA256: {binary_sha}\n'
                       f'CMAKE SOURCE SHA256: {cmake_sha}\n'
                       f'PINNED VERSION: {version.splitlines()[0]}\n'
                       'REAL CMAKE -P GUARD AND EXECUTE_PROCESS: PASS\n'
                       'NEXT STEP: IRIS26681_SPEKTRA_GLSLANG exported by GITHUB_ENV\n')
    # The GitHub runner exposes this to ALL subsequent steps, including Gradle.
    # A local "export" in the prior shader-step shell would NOT be inherited.
    with env_path.open('a', encoding='utf-8') as f:
        f.write(f'{EXPECTED_ENV_KEY}={compiler}\n')
    print('PASS pinned glslang archive SHA, real CMake code and exact executable; GITHUB_ENV handoff recorded')


def self_test():
    require(shutil.which('cmake') is not None, 'local CMake probe test NOT RUN')
    with tempfile.TemporaryDirectory(prefix='photon26904_v3_negative_') as temp:
        root = Path(temp)
        tools = root/'tools';extract = tools/'glslang'/'bin'
        extract.mkdir(parents=True)
        compiler = extract/'glslang'
        compiler.write_text('#!/bin/sh\nprintf "Glslang Version: 11:16.5.0\\n"\n')
        compiler.chmod(0o755)
        archive = tools/ARCHIVE_NAME
        archive.write_bytes(b'controlled-fixture-archive')
        pin = sha(archive.read_bytes())
        cmake = root/'CMakeLists.txt'
        cmake.write_text('cmake_minimum_required(VERSION 3.10)\n' + CMAKE_SEARCH + '\n')
        f, sha_bin, ver = select_pinned_compiler(tools, pin)
        require(f == compiler.resolve() and '16.5.0' in ver and len(sha_bin)==64, 'positive binary selection')
        cmake_probe(f, cmake)
        negatives = 0
        def reject(fn, label):
            nonlocal negatives
            try: fn()
            except AssertionError:
                negatives += 1
            else: raise AssertionError('26904 V3 expected FAIL: ' + label)
        reject(lambda: select_pinned_compiler(tools, '0'*64),'corrupt archive pin')
        cmake.write_text('cmake_minimum_required(VERSION 3.10)\n# corrupted\n' + CMAKE_SEARCH.replace('glslangValidator glslang','glslang')+'\n')
        reject(lambda: validate_cmake_guard(cmake),'CMake guard mutated')
        cmake.write_text('cmake_minimum_required(VERSION 3.10)\n' + CMAKE_SEARCH+'\n')
        compiler.write_text('#!/bin/sh\nprintf "Glslang Version: 11:15.0.0\\n"\n')
        reject(lambda: select_pinned_compiler(tools, pin),'wrong glslang version')
        compiler.unlink()
        reject(lambda: select_pinned_compiler(tools,pin),'missing compiler')
        require(negatives==4, 'not all negative checks executed')
        print('PASS actual CMake guard selection and 4 negative source/archive/compiler fixtures; real pinned binary still Actions-only')


if __name__=='__main__':
    try:
        require(len(sys.argv)==2 and sys.argv[1] in ('--handoff','--self-test'), 'usage: --handoff or --self-test')
        {'--handoff':handoff,'--self-test':self_test}[sys.argv[1]]()
    except Exception as e:
        print('26904 V3 FAIL:', e, file=sys.stderr)
        sys.exit(1)
