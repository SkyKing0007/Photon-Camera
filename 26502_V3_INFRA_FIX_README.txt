26502 V3 infrastructure-only correction

Reason:
26502 V2 correctly hardened GNU patch handling against .orig/.rej artifacts, but it accidentally retained a requirement for backup-26502-v1-before-buildfix-20260818. That backup was intentionally not created because V2 changed build infrastructure only, not runtime app source. The workflow would therefore fail before reconstruction.

V3 changes only build infrastructure:
1. Removes V1_HANDOFF_HEAD and BUILDFIX_BACKUP_BRANCH from the guarded build script.
2. Removes the corresponding fetch/test from the GitHub Actions workflow.
3. Adds a negative gate that fails if the obsolete infrastructure-only backup requirement ever reappears.
4. Preserves all V2 patch hardening: --batch --forward --fuzz=0 --no-backup-if-mismatch and explicit .orig/.rej contamination checks.
5. Runtime patch, runtime validator, V6 reconstruction, version 0.9726502 / 26502, and APK identity are unchanged.

Files to replace:
- build_26502_stack_aware_chroma_highlight.sh
- 26502_HANDOFF_HASHES.sha256
- .github/workflows/build-26502-stack-aware-chroma-highlight.yml

Files to add:
- 26502_v3_infrastructure_correction.patch
- 26502_V3_INFRA_FIX_README.txt

Commit statement:
26502 V3: remove obsolete build-fix backup requirement
