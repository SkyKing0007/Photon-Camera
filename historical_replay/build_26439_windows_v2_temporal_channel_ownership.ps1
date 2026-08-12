$ErrorActionPreference = "Stop"

# ============================================================================
# 26439 MOTION V2 TEMPORAL + CHANNEL OWNERSHIP
# Production modification/build script for the exact audited 26438 Windows tree.
#
# SAFETY:
#   - verifies exact branch / HEAD / version / audited source hashes
#   - creates backup branch BEFORE source modification
#   - creates binary pre-edit patch BEFORE source modification
#   - copies pre-edit source to Explorer-visible safety directory
#   - hashes every other tracked app file as protected
#   - transforms temporary copies first
#   - validates temporary candidate semantically
#   - applies the exact validated transformation to real source
#   - re-verifies protected hashes
#   - runs PRE-BUILD SAFETY PROOF
#   - increments version/build and builds in this same script
#   - does NOT commit or push
#   - never touches dev
# ============================================================================

function Fail([string]$Message) { throw "FAIL: $Message" }
function Pass([string]$Message) { Write-Host ("PASS: " + $Message) -ForegroundColor Green }
function Info([string]$Message) { Write-Host ("INFO: " + $Message) -ForegroundColor Cyan }

function ReadN([string]$Path) {
    return ([IO.File]::ReadAllText((Resolve-Path -LiteralPath $Path))).Replace("`r`n","`n")
}
function WriteN([string]$Path,[string]$Text) {
    [IO.File]::WriteAllText(
        $Path,
        $Text.Replace("`r`n","`n"),
        [Text.UTF8Encoding]::new($false))
}
function Sha([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path)) { return "MISSING" }
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash
}
function ReplaceOnce(
    [string]$Text,
    [string]$Old,
    [string]$New,
    [string]$Label) {

    $Count = ([regex]::Matches($Text,[regex]::Escape($Old))).Count
    if ($Count -ne 1) {
        Fail "$Label anchor count=$Count expected=1"
    }
    return $Text.Replace($Old,$New)
}
function Transform-Reconstruction([string]$Source) {
    $OldFrame = @'
            for (int i = 1; i < frameCount; i++) {
                ImageFrame frame = images.get(i);
                if (frame == null || frame.buffer == null) continue;
'@
    $NewFrame = @'
            for (int i = 1; i < frameCount; i++) {
                ImageFrame frame = images.get(i);
                if (frame == null || frame.buffer == null) continue;

                /*
                 * IRIS_26439_V2_TEMPORAL_OWNERSHIP_PRODUCER
                 *
                 * V2 previously retained frame timestamps in Java but never
                 * delivered temporal distance to the local CFA accumulator.
                 * Keep every RAW available; make age explicit so local
                 * evidence can become stricter as it moves farther from the
                 * immutable reference instant.
                 */
                final float temporalDistanceMs =
                        referenceTimestamp > 0L && frame.timestamp > 0L
                                ? Math.min(
                                        1000.0f,
                                        Math.abs(
                                                frame.timestamp
                                                        - referenceTimestamp)
                                                / 1_000_000.0f)
                                : 1000.0f;
'@
    $Source = ReplaceOnce $Source $OldFrame $NewFrame "temporal producer"

    $OldBind = @'
                            glProg.setVar("maximumSupport", (float) frameCount);
                            glProg.setVar("sensorClipLevel", canonicalGain);
                            glProg.setTexture(
                                    "flowTexture",
                                    ownedAlignment.flowTexture);
'@
    $NewBind = @'
                            glProg.setVar("maximumSupport", (float) frameCount);
                            glProg.setVar("sensorClipLevel", canonicalGain);
                            glProg.setVar(
                                    "temporalDistanceMs",
                                    temporalDistanceMs);
                            glProg.setTexture(
                                    "flowTexture",
                                    ownedAlignment.flowTexture);
'@
    $Source = ReplaceOnce $Source $OldBind $NewBind "temporal shader binding"
    return $Source
}
function Transform-Accumulator([string]$Source) {
    $OldUniform = @'
uniform float maximumSupport;
uniform float sensorClipLevel;
'@
    $NewUniform = @'
uniform float maximumSupport;
uniform float sensorClipLevel;
uniform float temporalDistanceMs;
'@
    $Source = ReplaceOnce $Source $OldUniform $NewUniform "temporal uniform"

    $OldTrust = @'
    float temporalTrust=tukeyWeight(
            temporalResidualSigma/3.0);
    float immutableReferenceTrust=tukeyWeight(
            immutableResidualSigma/3.0);

    float subjectMotionTrust=
            temporalTrust
            *immutableReferenceTrust;
'@
    $NewTrust = @'
    /*
     * IRIS_26439_V2_LOCAL_TEMPORAL_OWNERSHIP
     *
     * Temporal age is not a global frame discard. Static observations with
     * sub-noise residuals can still use the full burst. As an auxiliary gets
     * farther from the reference instant, however, disagreement becomes
     * progressively less acceptable. This prevents a 300-450 ms old pose or
     * changing display content from receiving the same local authority as a
     * nearby observation merely because its flow is geometrically plausible.
     */
    float ageRisk=smoothstep(45.0,190.0,max(temporalDistanceMs,0.0));
    float temporalCutSigma=mix(3.00,1.35,ageRisk);
    float immutableCutSigma=mix(3.00,1.55,ageRisk);

    float temporalTrust=tukeyWeight(
            temporalResidualSigma/max(temporalCutSigma,1.0e-4));
    float immutableReferenceTrust=tukeyWeight(
            immutableResidualSigma/max(immutableCutSigma,1.0e-4));

    float quietStaticEvidence=
            1.0-smoothstep(
                    0.45,
                    1.15,
                    max(temporalResidualSigma,immutableResidualSigma));
    float distantStaticFloor=mix(0.38,1.0,quietStaticEvidence);
    float temporalAgeAuthority=
            mix(1.0,distantStaticFloor,ageRisk);

    float subjectMotionTrust=
            temporalTrust
            *immutableReferenceTrust
            *temporalAgeAuthority;
'@
    $Source = ReplaceOnce $Source $OldTrust $NewTrust "age-aware local trust"

    $OldConflict = @'
    bool temporalConflict =
            temporalResidualSigma > 3.25;
    bool immutableReferenceConflict =
            immutableResidualSigma > 3.25
            || residualTrust < 0.30;
'@
    $NewConflict = @'
    /*
     * IRIS_26439_V2_AGE_AWARE_REFERENCE_VETO
     * Distant frames must clear a stricter noise-normalized test. A genuinely
     * static region can still pass because its residual remains below the
     * tightened threshold.
     */
    bool temporalConflict =
            temporalResidualSigma
                    > mix(3.25,1.55,ageRisk);
    bool immutableReferenceConflict =
            immutableResidualSigma
                    > mix(3.25,1.70,ageRisk)
            || residualTrust < mix(0.30,0.46,ageRisk);
'@
    $Source = ReplaceOnce $Source $OldConflict $NewConflict "age-aware conflict"

    $OldObs = @'
    vec3 obsNumerator = vec3(rObs.x,gObs.x,bObs.x);
    vec3 obsWeight = vec3(rObs.y,gObs.y,bObs.y);

    /*
     * cur * oldSupport is only the running numerator. It has no authority over
'@
    $NewObs = @'
    vec3 obsNumerator = vec3(rObs.x,gObs.x,bObs.x);
    vec3 obsWeight = vec3(rObs.y,gObs.y,bObs.y);

    /*
     * IRIS_26439_V2_SHARED_CHANNEL_OBSERVATION_VALIDITY
     *
     * A frame is one temporal observation. R/G/B still use real same-color
     * CFA sites, but a frame must not strongly update only one color while the
     * companion colors have almost no valid spatial/saturation support.
     *
     * This does not force equal R/G/B Bayer counts. It derives a bounded
     * observation-level authority from the least-supported color relative to
     * the strongest color, then scales all three channels together.
     */
    float strongestObservation=max(
            max(obsWeight.r,obsWeight.g),
            obsWeight.b);
    float weakestObservation=min(
            min(obsWeight.r,obsWeight.g),
            obsWeight.b);
    float channelCoverageRatio=
            weakestObservation
            /max(strongestObservation,1.0e-5);
    float sharedChannelValidity=
            smoothstep(0.10,0.38,channelCoverageRatio);

    obsNumerator*=sharedChannelValidity;
    obsWeight*=sharedChannelValidity;

    /*
     * cur * oldSupport is only the running numerator. It has no authority over
'@
    $Source = ReplaceOnce $Source $OldObs $NewObs "shared channel observation validity"
    return $Source
}
function Validate-Candidate([string]$ReconText,[string]$AccumText) {
    $ReconMarkers = @(
        "IRIS_26439_V2_TEMPORAL_OWNERSHIP_PRODUCER",
        "Math.abs(",
        "frame.timestamp",
        "referenceTimestamp",
        '"temporalDistanceMs",',
        "temporalDistanceMs"
    )
    foreach ($Marker in $ReconMarkers) {
        if (-not $ReconText.Contains($Marker)) {
            Fail "candidate reconstruction missing semantic marker: $Marker"
        }
    }

    $AccumMarkers = @(
        "uniform float temporalDistanceMs;",
        "IRIS_26439_V2_LOCAL_TEMPORAL_OWNERSHIP",
        "ageRisk=smoothstep(45.0,190.0",
        "temporalCutSigma=mix(3.00,1.35,ageRisk)",
        "immutableCutSigma=mix(3.00,1.55,ageRisk)",
        "IRIS_26439_V2_AGE_AWARE_REFERENCE_VETO",
        "IRIS_26439_V2_SHARED_CHANNEL_OBSERVATION_VALIDITY",
        "channelCoverageRatio=",
        "obsNumerator*=sharedChannelValidity;",
        "obsWeight*=sharedChannelValidity;"
    )
    foreach ($Marker in $AccumMarkers) {
        if (-not $AccumText.Contains($Marker)) {
            Fail "candidate accumulator missing semantic marker: $Marker"
        }
    }

    # Must remain honest about unresolved architecture.
    if ($AccumText.Contains("forwardBackward") -or
        $AccumText.Contains("disocclusionMap")) {
        Fail "candidate unexpectedly claims forward/backward or disocclusion implementation"
    }

    # No return of prohibited global-support controls.
    if ($AccumText.Contains("perFrameCap") -or
        $AccumText.Contains("referenceCeiling")) {
        Fail "candidate reintroduced prohibited global support cap markers"
    }
}

# ----------------------------------------------------------------------------
# Exact expected 26438 state
# ----------------------------------------------------------------------------
$Repo = "C:\Users\nhann\Documents\GitHub\Photon-Camera-clean-rebuild"
if (-not (Test-Path -LiteralPath $Repo)) { Fail "missing repo $Repo" }
Set-Location $Repo

$ExpectedBranch = "experimental-clean-photon-rebuild"
$ExpectedHead = "aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"
$ExpectedVersion = "0.9726438"
$ExpectedBuild = "26438"

$Recon = "app\src\main\java\com\particlesdevs\photoncamera\processing\processor\MotionV2CfaReconstruction.java"
$Accum = "app\src\main\assets\shaders\motionv2\direct_rgb_accumulate.glsl"
$Init = "app\src\main\assets\shaders\motionv2\direct_rgb_init.glsl"
$Align = "app\src\main\assets\shaders\motionv2\alignment_local_flow.glsl"
$Version = "app\version.properties"

$ExpectedReconHash = "8B381A959887031EB40DFF102AD58FB3C4C87164ADFBCE7C51DDD38412164E0B"
$ExpectedAccumHash = "685D9BAC6054CDDBE48BE949941801886A55CCCE8E6C7F69A0DE76134FFECD95"
$ExpectedInitHash  = "88631AFEC8A8E14A5E5AE44B9AEE2277C1A7730B1D49666ACFD4FB0972516D6C"
$ExpectedAlignHash = "49E13D87106973807F9C011F634F403A284DAEE715F4BABD0786C335C4304976"

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutDir = Join-Path $Repo "fresh_iris_outputs"
$SafetyDir = Join-Path $OutDir ("26439_preedit_safety_" + $Stamp)
$TempDir = Join-Path $OutDir ("26439_temp_candidate_" + $Stamp)
$BackupBranch = "backup/pre-26439-v2-temporal-channel-ownership-" + $Stamp
$Patch = Join-Path $SafetyDir ("pre_26439_worktree_" + $Stamp + ".patch")
$BuildLog = Join-Path $OutDir ("26439_build_" + $Stamp + ".log")
$SafetyLog = Join-Path $OutDir ("26439_safety_" + $Stamp + ".txt")

New-Item -ItemType Directory -Force -Path $OutDir,$SafetyDir,$TempDir | Out-Null

function Safety([string]$Text="") {
    $Text | Tee-Object -FilePath $SafetyLog -Append | Out-Host
}

Safety "26439 V2 TEMPORAL + CHANNEL OWNERSHIP PRODUCTION BUILD"
Safety "Started: $(Get-Date -Format o)"
Safety ""

# ----------------------------------------------------------------------------
# GATE 1: Exact source state
# ----------------------------------------------------------------------------
Safety "=== GATE 1: EXACT 26438 STATE ==="
$Branch = (& git branch --show-current).Trim()
$Head = (& git rev-parse HEAD).Trim()
Safety "Branch: $Branch"
Safety "HEAD: $Head"

if ($Branch -ne $ExpectedBranch) { Fail "wrong branch: $Branch" }
if ($Branch -eq "dev") { Fail "refusing to modify dev" }
if ($Head -ne $ExpectedHead) { Fail "wrong committed HEAD: $Head" }

$V = ReadN $Version
if ($V -notmatch "(?m)^VERSION_NAME=$([regex]::Escape($ExpectedVersion))$" -or
    $V -notmatch "(?m)^VERSION_BUILD=$ExpectedBuild$") {
    Fail "working version is not exact 0.9726438 / 26438"
}

if ((Sha $Recon) -ne $ExpectedReconHash) { Fail "26438 reconstruction hash mismatch" }
if ((Sha $Accum) -ne $ExpectedAccumHash) { Fail "26438 accumulator hash mismatch" }
if ((Sha $Init)  -ne $ExpectedInitHash)  { Fail "26438 init hash mismatch" }
if ((Sha $Align) -ne $ExpectedAlignHash) { Fail "26438 alignment hash mismatch" }

Pass "exact audited 26438 V2 source verified"
Safety "PASS: exact audited 26438 V2 source verified"

# ----------------------------------------------------------------------------
# GATE 2: Backup branch + binary patch BEFORE edits
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 2: PRE-EDIT BACKUP BRANCH + BINARY PATCH ==="

if ((& git branch --list $BackupBranch).Trim()) {
    Fail "backup branch already exists unexpectedly: $BackupBranch"
}
& git branch $BackupBranch $Head
if ($LASTEXITCODE -ne 0) { Fail "could not create backup branch" }

# Binary patch of the entire current working tree relative to committed HEAD.
$PatchLines = & git diff --binary HEAD --
if ($LASTEXITCODE -ne 0) { Fail "git diff --binary failed" }
$PatchLines | Set-Content -LiteralPath $Patch -Encoding ascii

# Explorer-visible exact copies of intended edit inputs.
Copy-Item -LiteralPath $Recon -Destination (Join-Path $SafetyDir "MotionV2CfaReconstruction.java.pre26439")
Copy-Item -LiteralPath $Accum -Destination (Join-Path $SafetyDir "direct_rgb_accumulate.glsl.pre26439")
Copy-Item -LiteralPath $Version -Destination (Join-Path $SafetyDir "version.properties.pre26439")

Pass "backup branch created: $BackupBranch"
Pass "binary pre-edit patch created: $Patch"
Safety "PASS: backup branch: $BackupBranch"
Safety "PASS: binary patch: $Patch"

# ----------------------------------------------------------------------------
# GATE 3: Protect every other tracked app file
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 3: PROTECTED TRACKED APP FILE HASHES ==="

$Intentional = @(
    ($Recon -replace "\\","/"),
    ($Accum -replace "\\","/"),
    ($Version -replace "\\","/")
)

$Protected = @{}
$TrackedApp = & git ls-files app
if ($LASTEXITCODE -ne 0) { Fail "git ls-files app failed" }

foreach ($RelUnix in $TrackedApp) {
    if ($Intentional -contains $RelUnix) { continue }
    $Rel = $RelUnix -replace "/","\"
    if (-not (Test-Path -LiteralPath $Rel)) {
        # A pre-existing deletion in the dirty 26438 tree is protected as deletion.
        $Protected[$RelUnix] = "MISSING"
    } else {
        $Protected[$RelUnix] = Sha $Rel
    }
}
Safety ("Protected tracked app files: " + $Protected.Count)
Pass "protected-file hash map captured"

# ----------------------------------------------------------------------------
# GATE 4: Temporary-copy transformation + candidate validation
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 4: TEMPORARY-COPY TRANSFORMATION ==="

$TempRecon = Join-Path $TempDir "MotionV2CfaReconstruction.java"
$TempAccum = Join-Path $TempDir "direct_rgb_accumulate.glsl"
Copy-Item -LiteralPath $Recon -Destination $TempRecon
Copy-Item -LiteralPath $Accum -Destination $TempAccum

$TempReconText = Transform-Reconstruction (ReadN $TempRecon)
$TempAccumText = Transform-Accumulator (ReadN $TempAccum)
WriteN $TempRecon $TempReconText
WriteN $TempAccum $TempAccumText

Validate-Candidate $TempReconText $TempAccumText

# Synthetic semantic checks reproduced from the successful 26439 preflight.
function Smooth01([double]$x) {
    $x = [Math]::Max(0.0,[Math]::Min(1.0,$x))
    return $x*$x*(3.0-2.0*$x)
}
function AgeRisk([double]$ms) {
    return Smooth01 (($ms-45.0)/(190.0-45.0))
}
if ((AgeRisk 0) -gt 0.001) { Fail "near-frame age risk is not neutral" }
if ((AgeRisk 450) -lt 0.999) { Fail "450ms age risk does not saturate" }

function ChannelValidity([double]$r,[double]$g,[double]$b) {
    $hi=[Math]::Max($r,[Math]::Max($g,$b))
    $lo=[Math]::Min($r,[Math]::Min($g,$b))
    $ratio=$lo/[Math]::Max($hi,1.0e-5)
    return Smooth01 (($ratio-0.10)/(0.38-0.10))
}
if ((ChannelValidity 1.0 2.0 1.0) -lt 0.999) {
    Fail "normal Bayer green asymmetry is being suppressed"
}
if ((ChannelValidity 0.2 2.0 0.2) -gt 0.001) {
    Fail "severe channel-support imbalance is not collapsing"
}

Pass "candidate/source validation PASS"
Pass "Temporary-copy validation: PASS"
Safety "PASS: candidate/source validation PASS"
Safety "PASS: Temporary-copy validation: PASS"

# ----------------------------------------------------------------------------
# GATE 5: Apply exact already-validated transformation to real source
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 5: APPLY EXACT VALIDATED TRANSFORMATION ==="

$RealReconText = Transform-Reconstruction (ReadN $Recon)
$RealAccumText = Transform-Accumulator (ReadN $Accum)
WriteN $Recon $RealReconText
WriteN $Accum $RealAccumText

# Real source must be byte-identical to the transformed temp candidate.
if ((Sha $Recon) -ne (Sha $TempRecon)) {
    Fail "real reconstruction differs from validated temporary candidate"
}
if ((Sha $Accum) -ne (Sha $TempAccum)) {
    Fail "real accumulator differs from validated temporary candidate"
}
Validate-Candidate (ReadN $Recon) (ReadN $Accum)

Pass "exact validated transformation applied to real source"
Safety "PASS: exact validated transformation applied to real source"

# ----------------------------------------------------------------------------
# GATE 6: Protected-file re-verification
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 6: PROTECTED FILE RE-VERIFICATION ==="

foreach ($RelUnix in $Protected.Keys) {
    $Expected = $Protected[$RelUnix]
    $Rel = $RelUnix -replace "/","\"
    $Actual = if (Test-Path -LiteralPath $Rel) { Sha $Rel } else { "MISSING" }
    if ($Actual -ne $Expected) {
        Fail "protected file changed unexpectedly: $RelUnix"
    }
}
Pass "all protected tracked app files unchanged"
Safety "PASS: all protected tracked app files unchanged"

# ----------------------------------------------------------------------------
# GATE 7: Version/build update in same production script
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 7: VERSION UPDATE ==="

$VersionText = ReadN $Version
$VersionText = ReplaceOnce $VersionText "VERSION_MINOR=9726438" "VERSION_MINOR=9726439" "VERSION_MINOR"
$VersionText = ReplaceOnce $VersionText "VERSION_NAME=0.9726438" "VERSION_NAME=0.9726439" "VERSION_NAME"
$VersionText = ReplaceOnce $VersionText "VERSION_BUILD=26438" "VERSION_BUILD=26439" "VERSION_BUILD"
WriteN $Version $VersionText

$VersionVerify = ReadN $Version
if ($VersionVerify -notmatch "(?m)^VERSION_NAME=0\.9726439$" -or
    $VersionVerify -notmatch "(?m)^VERSION_BUILD=26439$") {
    Fail "version update verification failed"
}

Pass "version/build updated to 0.9726439 / 26439"
Safety "PASS: version/build updated to 0.9726439 / 26439"

# ----------------------------------------------------------------------------
# GATE 8: HARD PRE-BUILD SAFETY PROOF
# ----------------------------------------------------------------------------
Safety ""
Safety "=== GATE 8: HARD PRE-BUILD SAFETY PROOF ==="

if ((& git branch --show-current).Trim() -ne $ExpectedBranch) {
    Fail "branch changed before build"
}
if ((& git rev-parse HEAD).Trim() -ne $ExpectedHead) {
    Fail "committed HEAD changed before build"
}

$FinalRecon = ReadN $Recon
$FinalAccum = ReadN $Accum
Validate-Candidate $FinalRecon $FinalAccum

# Producer -> binding -> consumer semantics, not token-only coincidence.
if ($FinalRecon -notmatch "final float temporalDistanceMs[\s\S]{0,900}frame\.timestamp[\s\S]{0,900}referenceTimestamp") {
    Fail "semantic producer chain proof failed"
}
if ($FinalRecon -notmatch 'setVar\(\s*"temporalDistanceMs"[\s\S]{0,120}temporalDistanceMs') {
    Fail "semantic shader binding proof failed"
}
if ($FinalAccum -notmatch "uniform float temporalDistanceMs;[\s\S]{0,10000}ageRisk=smoothstep\(45\.0,190\.0,max\(temporalDistanceMs,0\.0\)\)") {
    Fail "semantic shader consumer proof failed"
}
if ($FinalAccum -notmatch "sharedChannelValidity[\s\S]{0,1000}obsNumerator\*=sharedChannelValidity;[\s\S]{0,250}obsWeight\*=sharedChannelValidity;") {
    Fail "shared-channel authority consumer proof failed"
}

# Exact unchanged hashes for the two explicitly protected V2 files most relevant
# to this build's architectural boundary.
if ((Sha $Init) -ne $ExpectedInitHash) { Fail "reference initializer changed unexpectedly" }
if ((Sha $Align) -ne $ExpectedAlignHash) { Fail "alignment shader changed unexpectedly" }

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "PRE-BUILD SAFETY PROOF PASSED" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Safety "PRE-BUILD SAFETY PROOF PASSED"

# ----------------------------------------------------------------------------
# BUILD
# ----------------------------------------------------------------------------
Safety ""
Safety "=== BUILD 0.9726439 / 26439 ==="

$Gradle = Join-Path $Repo "gradlew.bat"
if (-not (Test-Path -LiteralPath $Gradle)) {
    Fail "gradlew.bat not found"
}

$BuildOutput = & $Gradle :app:assembleDebug --stacktrace 2>&1
$BuildExit = $LASTEXITCODE
$BuildOutput | Tee-Object -FilePath $BuildLog | Out-Host

if ($BuildExit -ne 0) {
    Fail "Gradle exited with code $BuildExit. See $BuildLog"
}
$BuildText = $BuildOutput -join "`n"
if ($BuildText -notmatch "BUILD SUCCESSFUL") {
    Fail "Gradle returned zero but BUILD SUCCESSFUL marker was not found"
}

# Locate newest debug APK.
$Apks = Get-ChildItem -Path (Join-Path $Repo "app\build\outputs\apk") -Recurse -File -Filter "*.apk" |
        Where-Object { $_.Name -match "debug" } |
        Sort-Object LastWriteTime -Descending
if (-not $Apks -or $Apks.Count -lt 1) {
    Fail "build succeeded but no debug APK was found"
}

$BuiltApk = $Apks[0]
$FinalApk = Join-Path $Repo "IrisCamera-0.9726439-26439-v2-temporal-channel-ownership-debug.apk"
Copy-Item -LiteralPath $BuiltApk.FullName -Destination $FinalApk -Force

$FinalHash = (Get-FileHash -LiteralPath $FinalApk -Algorithm SHA256).Hash
Safety "BUILD SUCCESSFUL"
Safety "Built APK source: $($BuiltApk.FullName)"
Safety "Copied APK: $FinalApk"
Safety "APK SHA256: $FinalHash"
Safety "No commit. No push. dev untouched."

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "26439 BUILD SUCCESS" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "APK: $FinalApk"
Write-Host "SHA256: $FinalHash"
Write-Host "Safety log: $SafetyLog"
Write-Host "Build log:  $BuildLog"
Write-Host "Backup branch: $BackupBranch"
Write-Host "Binary patch: $Patch"
Write-Host ""
Write-Host "No commit or push was performed."
