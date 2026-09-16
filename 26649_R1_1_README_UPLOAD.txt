PHOTON 26649 R1.1 — GLSL EXPANSION VERIFIER REPAIR

Purpose: infrastructure-only repair for failed 26649 R1 Actions run 35093754362.
Runtime candidate is unchanged from intended 26649 R1: exactly the same 5 runtime changed files reconstructed from successful 26648 R1.2 authority.

Failure fixed permanently:
- R1 verify_26649_shaders.py incorrectly passed raw asset GLSL directly to glslangValidator.
- Photon runtime GLInterface prepends #version 310 es + #line 1 and resolves runtime preprocessing before compilation.
- R1.1 verifies and compiles the exact GLInterface-expanded source. Raw asset text is forbidden as the compiler input.

No backup. No HEIC work. No SHORT/fusion redesign. No runtime source changes versus intended R1.
Expected Source Control additions: 9 files.
Commit suggestion: 26649 R1.1: repair runtime-expanded GLSL verification
