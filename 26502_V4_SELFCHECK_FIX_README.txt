26502 V4 infrastructure-only self-check correction

Reason:
26502 V3 correctly removed the obsolete infrastructure-only backup branch requirement, but its negative verification command searched the workflow file for a literal branch string that was itself embedded in that verification command. grep therefore matched the check's own source text and always failed.

V4 changes only GitHub Actions verification infrastructure:
1. Keeps the negative obsolete-backup check.
2. Constructs the obsolete branch name from two adjacent shell string fragments, so the complete obsolete name does not exist literally in the workflow source being searched.
3. The runtime patch, runtime validator, build script, V6 reconstruction, patch hardening, .orig/.rej gates, version 0.9726502 / 26502, and APK identity are unchanged.
4. No new backup branch is required because this is infrastructure-only.

Files to replace:
- 26502_HANDOFF_HASHES.sha256
- .github/workflows/build-26502-stack-aware-chroma-highlight.yml

Files to add:
- 26502_v4_selfcheck_correction.patch
- 26502_V4_SELFCHECK_FIX_README.txt

Commit statement:
26502 V4: fix obsolete-backup self-check false positive
