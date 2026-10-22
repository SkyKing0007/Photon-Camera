#!/usr/bin/env python3
"""Strict shaderc-compatible invocation for the original pinned RAWR CMake.

RAWR's upstream target names, shader source, descriptor ABI, and per-mode
macros are not modified. This narrow adapter uses the already pinned *real*
glslangValidator and SPIRV-Tools, failing if any tool or requested mode is
missing. It is NOT a mock shader compiler and does not synthesize .spv data.
"""
import argparse
from pathlib import Path
import re
import subprocess
import sys
import tempfile


def main():
    parser = argparse.ArgumentParser(allow_abbrev=False)
    parser.add_argument('--validator', required=True)
    parser.add_argument('--spirv-val', required=True)
    parser.add_argument('--spirv-opt', required=True)
    opts, source_args = parser.parse_known_args()
    if not source_args or source_args.count('-o') != 1:
        raise RuntimeError('26864 native RAWR compiler missing exact shader output')
    outidx = source_args.index('-o')
    if outidx + 1 >= len(source_args):
        raise RuntimeError('26864 missing shader output')
    dest = Path(source_args[outidx+1]); remaining = source_args[:outidx] + source_args[outidx+2:]
    defines = []; includes = []; files = []; target_seen = False; optimized = False
    for item in remaining:
        if item == '--target-env=vulkan1.1':
            if target_seen: raise RuntimeError('duplicate Vulkan target')
            target_seen = True
        elif item == '-O':
            if optimized: raise RuntimeError('duplicate pinned optimization')
            optimized = True
        elif re.fullmatch(r'-D[A-Z][A-Z0-9_]*=[01]', item):
            defines.append(item)
        elif item.startswith('-I') and len(item)>2 and Path(item[2:]).is_dir():
            includes.append(item)
        elif item.endswith('.comp') and not item.startswith('-'):
            files.append(Path(item))
        else:
            raise RuntimeError('unrecognized RAWR upstream compile option: ' + item)
    if not target_seen or not optimized or len(files) != 1 or not files[0].is_file():
        raise RuntimeError('26864 RAWR requires pinned Vulkan1.1 optimized real GLSL input')
    for label, tool in [('glslangValidator',opts.validator),('spirv-val',opts.spirv_val),('spirv-opt',opts.spirv_opt)]:
        if not Path(tool).is_file(): raise RuntimeError('missing real '+label+' executable: '+tool)
    version = subprocess.run([opts.validator,'--version'],check=True,text=True,
                             capture_output=True).stdout
    if 'glslang Khronos. 16.5.0' not in version:
        raise RuntimeError('26864 glslang version differs from successful 26863 pinned 16.5.0')
    dest.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='iris26864_glsl_',dir=dest.parent) as td:
        uncomp = Path(td)/'source.spv'; optimized_out = Path(td)/'opt.spv'
        cmd=[opts.validator,'-V','--target-env','vulkan1.1','-S','comp',*defines,*includes,
             str(files[0]),'-o',str(uncomp)]
        subprocess.run(cmd,check=True)
        subprocess.run([opts.spirv_val,'--target-env','vulkan1.1',str(uncomp)],check=True)
        subprocess.run([opts.spirv_opt,'-O',str(uncomp),'-o',str(optimized_out)],check=True)
        subprocess.run([opts.spirv_val,'--target-env','vulkan1.1',str(optimized_out)],check=True)
        # Only validated optimized SPIR-V is exported. Upstream embedded source
        # headers are produced by the unmodified RAWR EmbedBinary.cmake.
        dest.write_bytes(optimized_out.read_bytes())
    return 0

if __name__ == '__main__':
    try: sys.exit(main())
    except (RuntimeError,subprocess.CalledProcessError) as ex:
        print('IRIS_26864_RAWR_COMPILE_FATAL: '+str(ex),file=sys.stderr)
        sys.exit(1)
