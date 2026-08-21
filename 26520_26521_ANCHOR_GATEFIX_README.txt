26520/26521 shared reconstruct-call anchor gate fix

Failure fixed:
AssertionError: reconstruct DNG request anchor count=0

Cause:
The old handoff required one exact whitespace/line-wrapping representation of the
HdrxProcessor call to MotionV2CfaReconstruction.reconstruct(). GitHub Actions patches
the recovered successful-26519 source artifact, whose formatting can differ from the
dormant repository source.

Correction:
- No runtime architecture or requested math changed.
- The transformer now requires exactly ONE semantic reconstruct invocation.
- It balances Java parentheses.
- It verifies all five expected pre-26520 argument tokens:
  new Point(width, height)
  images
  iris26363ReferenceTimestamp
  processingParameters
  mMotion26486ShortSlot
- It refuses a duplicate call.
- It refuses a missing expected argument.
- It refuses if saveRAW >= 1 was already inserted.
- It appends only the sixth argument: saveRAW >= 1.
- Both 26520 and 26521 continue using the exact same shared transform.

Shared apply SHA-256:
d1f99b815edcdf0922cd688278bdaff577728e670195e941e7d9483d6c0e0991

Patch SHA-256:
5e4d2ff1dc8bed9c496d403d172ba385ac6acc0c2e4780ec5c9e7a077dd9d529

This overlay replaces only:
- apply_26520_zsl_stacked_dng.py
- 26520_HANDOFF_HASHES.sha256
- 26521_HANDOFF_HASHES.sha256

The included .patch/.sha256 are audit/rollback evidence and do not need to be
referenced by the workflows.
