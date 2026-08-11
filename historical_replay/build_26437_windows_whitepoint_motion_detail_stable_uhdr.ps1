$ErrorActionPreference = "Stop"

# ============================================================================
# 26437 WINDOWS INTEGRATED MOTION BUILD
# - 26436 exact-state proof first
# - backup branch + binary patch before real source modification
# - candidate-only transforms first
# - real Android NDK glslc validation before source apply
# - Javac proof + assemble in same run
# - no commit / no push / dev untouched
# ============================================================================

function Fail([string]$Message) {
    throw "FAIL: $Message"
}

function ReadT([string]$Path) {
    return [IO.File]::ReadAllText($Path)
}

function Normalize-Lf([string]$Text) {
    if ($null -eq $Text) { return $Text }
    return $Text.Replace("`r`n","`n").Replace("`r","`n")
}

function WriteUtf8NoBom([string]$Path,[string]$Text) {
    $Parent = Split-Path -Parent $Path
    if ($Parent) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }
    [IO.File]::WriteAllText(
        $Path,
        $Text,
        (New-Object Text.UTF8Encoding($false))
    )
}

function Replace-Once(
        [string]$Text,
        [string]$Old,
        [string]$New,
        [string]$Label) {
    $TextLf = Normalize-Lf $Text
    $OldLf  = Normalize-Lf $Old
    $NewLf  = Normalize-Lf $New

    $Count = ([regex]::Matches(
        $TextLf,
        [regex]::Escape($OldLf)
    )).Count

    if ($Count -ne 1) {
        Fail "$Label expected exactly one normalized-LF anchor, found $Count"
    }
    return $TextLf.Replace($OldLf,$NewLf)
}

function Sha([string]$Path) {
    return (Get-FileHash -Algorithm SHA256 -LiteralPath $Path).Hash
}

# Self-parse before any repository action.
$ParserTokens = $null
$ParserErrors = $null
[System.Management.Automation.Language.Parser]::ParseFile(
    $PSCommandPath,
    [ref]$ParserTokens,
    [ref]$ParserErrors
) | Out-Null
if ($ParserErrors.Count -gt 0) {
    foreach ($E in $ParserErrors) {
        Write-Host ("PARSER ERROR line " +
            $E.Extent.StartLineNumber + ": " + $E.Message)
    }
    Fail "PowerShell parser validation failed before repository work"
}
Write-Host "POWERSHELL SCRIPT PARSER: PASS"

$Repo = "C:\Users\nhann\Documents\GitHub\Photon-Camera-clean-rebuild"
if (-not (Test-Path -LiteralPath $Repo)) {
    Fail "Repository not found: $Repo"
}
Set-Location $Repo

$ExpectedBranch = "experimental-clean-photon-rebuild"
$ExpectedHead = "aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"

$DINIT   = 'app\src\main\assets\shaders\motionv2\direct_rgb_init.glsl'
$DACC    = 'app\src\main\assets\shaders\motionv2\direct_rgb_accumulate.glsl'
$COLORG  = 'app\src\main\assets\shaders\motionv2\color_transform.glsl'
$DENOISEG= 'app\src\main\assets\shaders\motionv2\denoise.glsl'
$DENOISEJ= 'app\src\main\java\com\particlesdevs\photoncamera\processing\opengl\postpipeline\MotionV2Denoise.java'
$RENDERG = 'app\src\main\assets\shaders\motionv2\render.glsl'
$GAINMAP = 'app\src\main\assets\shaders\motionv2\gainmap.glsl'
$VERSION = 'app\version.properties'

$Targets = @(
    $DINIT,
    $DACC,
    $COLORG,
    $DENOISEG,
    $DENOISEJ,
    $VERSION
)

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$OutRoot = Join-Path $Repo "fresh_iris_outputs"
$Safety = Join-Path $OutRoot "windows_26437_integrated_$Stamp"
$Originals = Join-Path $Safety "originals"
$Cand = Join-Path $Safety "candidates"
$ProtectedBefore = Join-Path $Safety "protected_before.txt"
$ProtectedAfter = Join-Path $Safety "protected_after.txt"
$PrePatch = Join-Path $Safety "pre_26437_windows_working_tree.patch"
$PostPatch = Join-Path $Safety "post_26437_windows_working_tree.patch"
$GlslLog = Join-Path $Safety "glslc_26437_windows.txt"
$JavacLog = Join-Path $Safety "javac_26437_windows.txt"
$BuildLog = Join-Path $Safety "build_26437_windows.txt"
$Result = Join-Path $OutRoot "windows_26437_result_$Stamp.txt"
$ApkOut = Join-Path $Repo "IrisCamera-0.9726437-26437-whitepoint-motion-detail-stable-uhdr-debug.apk"

New-Item -ItemType Directory -Force -Path `
    $OutRoot,$Safety,$Originals,$Cand | Out-Null

Write-Host "=== GATE 0: EXACT 26436 WINDOWS SOURCE PROOF ==="

$Branch = (& git branch --show-current).Trim()
$Head = (& git rev-parse HEAD).Trim()

if ($Branch -ne $ExpectedBranch) {
    Fail "Expected branch $ExpectedBranch, actual $Branch"
}
if ($Head -ne $ExpectedHead) {
    Fail "Expected historical HEAD $ExpectedHead, actual $Head"
}
if ($Branch -eq 'dev') {
    Fail "Refusing to modify dev"
}

if (-not (Test-Path -LiteralPath 'local.properties')) {
    Fail "local.properties missing"
}
if (-not (Test-Path -LiteralPath 'gradlew.bat')) {
    Fail "gradlew.bat missing"
}

$ExpectedHashes = @{
    $DINIT='7BABF08973ABD74AF81BBC7E3D543443C1ECE745AED6C43A036690CD44CB3B8A'
    $DACC='E5ECB4966AF49DDAF656EF2A7B94A17FF62E8FAC110D0B80A8500965D5A40C47'
    $COLORG='642DDD94D9374C9792A652561AE82C67ADD73D1FB810551A9CC157FD15AAADF1'
    $DENOISEG='420BAB6F8D917BF8A37D5B6F5864080A1179C04AB90FBD51C0474E45898C3A1C'
    $DENOISEJ='C451D4D98BAEA223638CDA2CA116400881440A153720A358BF1C00D1AC381C20'
    $RENDERG='FEBC6CCD70249EE036EEAD47C266DA4A3D7133209555CBCC1A584B1E3A066D7D'
    $VERSION='245C2610BB7FD9741D467BF08D6F6AE89035C50077AC79A0EE94CCF75A589667'
}

foreach ($K in $ExpectedHashes.Keys) {
    if (-not (Test-Path -LiteralPath $K)) {
        Fail "Expected 26436 file missing: $K"
    }
    $Actual = Sha $K
    if ($Actual -ne $ExpectedHashes[$K]) {
        Fail "26436 exact-source mismatch: $K`nExpected $($ExpectedHashes[$K])`nActual   $Actual"
    }
}

$V = ReadT $VERSION
if ($V -notmatch '(?m)^VERSION_NAME=0\.9726436\r?$' -or
    $V -notmatch '(?m)^VERSION_BUILD=26436\r?$') {
    Fail "Expected current version 0.9726436 / 26436"
}

$Required26436 = @(
    @{F=$DINIT; M='IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS_INIT'},
    @{F=$DACC; M='IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS'},
    @{F=$DACC; M='IRIS_26436_REFERENCE_RESIDUAL_SHARED_COLOR_MERGE'},
    @{F=$COLORG; M='IRIS_26430_SENSOR_CLIP_COLOR_SAFETY_ONLY'},
    @{F=$DENOISEG; M='IRIS_26430_LIGHT_SUPPORT_OWNED_RESIDUAL_CLEANUP'},
    @{F=$RENDERG; M='IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV'},
    @{F=$GAINMAP; M='IRIS_26436_BROAD_REGION_CHROMA_PROTECTED_GAINMAP'}
)
foreach ($C in $Required26436) {
    if (-not (Test-Path -LiteralPath $C.F)) {
        Fail "Required architecture file missing: $($C.F)"
    }
    if (-not (ReadT $C.F).Contains($C.M)) {
        Fail "Current 26436 architecture marker missing: $($C.M)"
    }
}

foreach ($Rel in $Targets) {
    if ((ReadT $Rel).Contains('IRIS_26437_')) {
        Fail "26437 marker already exists in $Rel; refusing duplicate apply"
    }
}

Write-Host "PASS: exact tested 26436 target source proven"
Write-Host "PASS: 26436 visual invariants / UHDR foundation present"
Write-Host "PASS: dev untouched"

Write-Host "=== GATE 1: BACKUP BRANCH + BINARY PRE-EDIT PATCH ==="

$Backup = "backup/windows-before-26437-integrated-$Stamp"
& git branch $Backup
if ($LASTEXITCODE -ne 0) {
    Fail "Backup branch creation failed"
}

& git diff --binary HEAD -- app |
    Out-File -LiteralPath $PrePatch -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Fail "Pre-edit binary patch failed"
}

foreach ($Rel in $Targets) {
    $Dest = Join-Path $Originals $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) |
        Out-Null
    Copy-Item -LiteralPath $Rel -Destination $Dest -Force
}
Copy-Item -LiteralPath 'local.properties' `
    -Destination (Join-Path $Originals 'local.properties') -Force

function Hash-Protected([string[]]$Intentional,[string]$OutFile) {
    $Rows = New-Object System.Collections.Generic.List[string]
    $Tracked = & git ls-files app
    foreach ($RelRaw in $Tracked) {
        $Rel = $RelRaw -replace '/','\'
        if ($Intentional -contains $Rel) { continue }
        if (-not (Test-Path -LiteralPath $Rel)) { continue }
        $Rows.Add(("{0}  {1}" -f (Sha $Rel),$Rel))
    }
    $Rows | Sort-Object |
        Set-Content -LiteralPath $OutFile -Encoding UTF8
}

Hash-Protected $Targets $ProtectedBefore

Write-Host "=== GATE 2: BUILD ALL 26437 TEMPORARY CANDIDATES ==="

foreach ($Rel in $Targets) {
    $Dest = Join-Path $Cand $Rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $Dest) |
        Out-Null
    Copy-Item -LiteralPath $Rel -Destination $Dest -Force
}

# --------------------------------------------------------------------------
# 26437 DINIT
# - sensor-white-point ownership at the physical reference
# - reference edge anchor increases only reference support, never caps frames
# --------------------------------------------------------------------------
$P = Join-Path $Cand $DINIT
$S = Normalize-Lf (ReadT $P)

$NeutralAnchor = @'
float neutralFromGreen(float green, int wantedColor) {
    vec3 gains = max(sensorGains, vec3(1.0e-6));
    float greenGain = gains.g;
    if (wantedColor == 0) return green * greenGain / gains.r;
    if (wantedColor == 2) return green * greenGain / gains.b;
    return green;
}
'@

$NeutralNew = @'
float neutralFromGreen(float green, int wantedColor) {
    vec3 gains = max(sensorGains, vec3(1.0e-6));
    float greenGain = gains.g;
    if (wantedColor == 0) return green * greenGain / gains.r;
    if (wantedColor == 2) return green * greenGain / gains.b;
    return green;
}

/*
 * IRIS_26437_WHITE_POINT_OWNED_REFERENCE_AND_EDGE_ANCHOR
 *
 * Sensor white is physical evidence, not a display-tone decision.
 * Once any photosite in the owned reference CFA cell is near physical white,
 * that region loses independent chroma authority coherently across R/G/B.
 */
float referenceWhitePointLoss(ivec2 rawPos) {
    ivec2 q = clamp(
            rawPos >> 1,
            ivec2(0),
            imageSize(referenceCfa) - ivec2(1));
    vec4 cell = max(imageLoad(referenceCfa,q),vec4(0.0));
    float peak = max(max(cell.r,cell.g),max(cell.b,cell.a));
    float clip = max(sensorClipLevel,1.0e-6);
    return smoothstep(0.920*clip,0.992*clip,peak);
}
'@

$S = Replace-Once $S $NeutralAnchor $NeutralNew 'DINIT white-point helper'

$TailOld = @'
    float r = rAcc.y > 1.0e-5 ? rAcc.x/rAcc.y : neutralFromGreen(g,0);
    float b = bAcc.y > 1.0e-5 ? bAcc.x/bAcc.y : neutralFromGreen(g,2);

    // Support is true accumulated kernel weight, independently per channel.
    vec3 support = vec3(rAcc.y, gAcc.y, bAcc.y);

    /* IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS_INIT */
    float consensusMean = max(g,0.0);
    float consensusScale =
            0.018
            + 0.065*sqrt(consensusMean)
            + 0.010*consensusMean;

    imageStore(
            outRgb,
            xy,
            vec4(max(vec3(r,g,b),vec3(0.0)),consensusMean));
    imageStore(
            outSupport,
            xy,
            vec4(max(support,vec3(1.0e-4)),max(consensusScale,1.0e-4)));
'@

$TailNew = @'
    float r = rAcc.y > 1.0e-5 ? rAcc.x/rAcc.y : neutralFromGreen(g,0);
    float b = bAcc.y > 1.0e-5 ? bAcc.x/bAcc.y : neutralFromGreen(g,2);

    vec3 referenceRgb=max(vec3(r,g,b),vec3(0.0));
    vec3 neutralRgb=vec3(
            neutralFromGreen(g,0),
            g,
            neutralFromGreen(g,2));

    float whitePointLoss=referenceWhitePointLoss(xy);
    float rgbPeak=max(referenceRgb.r,max(referenceRgb.g,referenceRgb.b));
    float rgbFloor=min(referenceRgb.r,min(referenceRgb.g,referenceRgb.b));
    float spread=(rgbPeak-rgbFloor)/max(rgbPeak,1.0e-6);
    float chromaFailureEvidence=smoothstep(0.10,0.48,spread);

    /*
     * Only near physical white: progressively replace lost chroma with a
     * sensor-neutral estimate from the owned reference green signal.
     * Normal colorful highlights below physical white pass untouched.
     */
    float whiteNeutralize=clamp(
            whitePointLoss*mix(0.35,1.0,chromaFailureEvidence),
            0.0,1.0);
    float terminalWhite=smoothstep(0.90,0.995,whitePointLoss);
    whiteNeutralize=max(whiteNeutralize,terminalWhite);
    referenceRgb=mix(referenceRgb,neutralRgb,whiteNeutralize);

    /*
     * Reference edge detail is given extra numerator/support authority.
     * This does not discard or cap any auxiliary frame; it simply prevents
     * a crowd of slightly imperfect warps from washing out owned geometry.
     */
    float referenceAnchor=1.0+1.35*edgeStrength;
    referenceAnchor*=mix(1.0,1.30,whitePointLoss);

    // Support remains true per-channel kernel support times reference authority.
    vec3 support =
            vec3(rAcc.y,gAcc.y,bAcc.y)
            *referenceAnchor;

    /* IRIS_26436_REFERENCE_SEEDED_TEMPORAL_CONSENSUS_INIT */
    float consensusMean = max(g,0.0);
    float consensusScale =
            0.018
            + 0.065*sqrt(consensusMean)
            + 0.010*consensusMean;

    imageStore(
            outRgb,
            xy,
            vec4(referenceRgb,consensusMean));
    imageStore(
            outSupport,
            xy,
            vec4(max(support,vec3(1.0e-4)),max(consensusScale,1.0e-4)));
'@

$S = Replace-Once $S $TailOld $TailNew 'DINIT reference ownership'
WriteUtf8NoBom $P $S

# --------------------------------------------------------------------------
# 26437 DACC
# - stronger moving-subject / occlusion rejection
# - white-point-owned reference fallback for clipped/specular regions
# - all frames stay retained/global eligible
# --------------------------------------------------------------------------
$P = Join-Path $Cand $DACC
$S = Normalize-Lf (ReadT $P)

$HighlightOld = @'
float sharedHighlightReliability(ivec2 sourceRaw) {
    ivec2 p=clamp(sourceRaw,ivec2(0),rawSize-ivec2(1));
    ivec2 q=clamp(p>>1,ivec2(0),rawHalf-ivec2(1));
    vec4 cell=max(imageLoad(alterCfa,q),vec4(0.0));
    float peak=max(max(cell.r,cell.g),max(cell.b,cell.a));
    float clip=max(sensorClipLevel,1.0e-6);
    return 1.0-smoothstep(0.915*clip,0.985*clip,peak);
}
'@

$HighlightNew = @'
/*
 * IRIS_26437_SENSOR_WHITE_POINT_SHARED_HIGHLIGHT_AUTHORITY
 *
 * A near-clipped observation is not allowed to vote a different hue into a
 * thin light/reflection. The owned reference controls both geometry and color
 * whenever either side has physically lost highlight channel information.
 */
float cellWhitePointLossReference(ivec2 rawPos) {
    ivec2 p=clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    ivec2 q=clamp(p>>1,ivec2(0),rawHalf-ivec2(1));
    vec4 cell=max(imageLoad(referenceCfa,q),vec4(0.0));
    float peak=max(max(cell.r,cell.g),max(cell.b,cell.a));
    float clip=max(sensorClipLevel,1.0e-6);
    return smoothstep(0.900*clip,0.985*clip,peak);
}

float cellWhitePointLossAlter(ivec2 rawPos) {
    ivec2 p=clamp(rawPos,ivec2(0),rawSize-ivec2(1));
    ivec2 q=clamp(p>>1,ivec2(0),rawHalf-ivec2(1));
    vec4 cell=max(imageLoad(alterCfa,q),vec4(0.0));
    float peak=max(max(cell.r,cell.g),max(cell.b,cell.a));
    float clip=max(sensorClipLevel,1.0e-6);
    return smoothstep(0.900*clip,0.985*clip,peak);
}

float sharedHighlightReliability(
        ivec2 referenceRaw,
        ivec2 sourceRaw) {
    float referenceLoss=cellWhitePointLossReference(referenceRaw);
    float sourceLoss=cellWhitePointLossAlter(sourceRaw);
    float loss=max(referenceLoss,sourceLoss);
    return clamp(1.0-loss,0.0,1.0);
}
'@

$S = Replace-Once $S $HighlightOld $HighlightNew 'DACC white-point reliability'

$CallOld = @'
    float highlightTrust=sharedHighlightReliability(
            ivec2(round(sourceCoord)));
'@
$CallNew = @'
    float highlightTrust=sharedHighlightReliability(
            xy,
            ivec2(round(sourceCoord)));
'@
$S = Replace-Once $S $CallOld $CallNew 'DACC highlight call'

$MotionOld = @'
    float temporalResidual=abs(auxConsensusGreen-oldConsensusMean);
    float temporalTrust=tukeyWeight(
            temporalResidual/max(3.20*oldConsensusScale,1.0e-5));

    float sharedConfidence=clamp(
            alignmentTrust
            *alignmentResidualTrust
            *residualTrust
            *temporalTrust
            *mix(1.0,boundaryTrust,0.90)
            *highlightTrust,
            0.0,1.0);
'@

$MotionNew = @'
    float temporalResidual=abs(auxConsensusGreen-oldConsensusMean);

    /*
     * IRIS_26437_SUBJECT_MOTION_REFERENCE_FALLBACK
     *
     * 26436 proved that alignment confidence alone was still too permissive:
     * a moving subject could retain several incompatible poses. Tighten the
     * independent temporal-consensus test and make disagreement multiplicative.
     */
    float temporalTrust=tukeyWeight(
            temporalResidual/max(2.25*oldConsensusScale,1.0e-5));
    float subjectMotionTrust=temporalTrust*temporalTrust;
    float referenceAgreement=residualTrust*residualTrust;
    float occlusionTrust=boundaryTrust*boundaryTrust;

    float sharedConfidence=clamp(
            alignmentTrust
            *alignmentResidualTrust
            *referenceAgreement
            *subjectMotionTrust
            *occlusionTrust
            *highlightTrust,
            0.0,1.0);

    /*
     * Hard local fallback is permitted, global frame discard is not.
     * These are local observation failures only; static regions from the same
     * frame remain fully eligible.
     */
    bool temporalConflict =
            temporalResidual > 2.75*oldConsensusScale;
    bool referenceConflict =
            residualTrust < 0.22
            || alignmentResidualTrust < 0.12;
    bool occlusionConflict =
            boundaryTrust < 0.08;

    if(temporalConflict || referenceConflict || occlusionConflict) {
        sharedConfidence=0.0;
    }
'@

$S = Replace-Once $S $MotionOld $MotionNew 'DACC subject-motion gating'
WriteUtf8NoBom $P $S

# --------------------------------------------------------------------------
# 26437 COLOR
# - sensor-domain white point owns chroma repair
# - no transformed-space hue invention / generic highlight whitening
# --------------------------------------------------------------------------
$P = Join-Path $Cand $COLORG
$S = Normalize-Lf (ReadT $P)

$ColorMainOld = @'
void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));

    float sensorClip=max(sensorClipLevel,1.0e-6);
    vec3 sensorRelative=cameraRgb/sensorClip;

    /*
     * Start withdrawing chroma authority only very near physical RAW white.
     * This is deliberately later than 26427's 0.900 threshold.
     */
    vec3 sensorReliable=
            vec3(1.0)-smoothstep(
                    vec3(0.955),
                    vec3(0.997),
                    sensorRelative);
    float sensorLoss=1.0-min3(sensorReliable);

    vec3 balanced=cameraRgb*sensorGains;
    vec3 linearSrgb=max(transformBalanced(balanced),vec3(0.0));

    float outMax=max3(linearSrgb);
    float outMin=min3(linearSrgb);
    float y=max(
            dot(linearSrgb,vec3(0.2126,0.7152,0.0722)),
            0.0);

    /*
     * A colorful or >1.0 transformed pixel is NOT automatically invalid.
     * Neutralization requires genuine physical sensor authority loss.
     */
    float brightHighlight=smoothstep(0.78,1.15,y);
    float channelSpread=
            (outMax-outMin)/max(outMax,1.0e-6);
    float spreadConcern=smoothstep(0.25,0.60,channelSpread);

    float safetyLoss=
            brightHighlight
            * sensorLoss
            * mix(0.65,1.0,spreadConcern);

    float neutralize=smoothstep(0.28,0.88,safetyLoss);
    float neutralEnergy=max(outMax,y);
    vec3 safeRgb=mix(
            linearSrgb,
            vec3(neutralEnergy),
            neutralize);

    /*
     * Fully lost physical highlight color becomes coherent white. This is a
     * terminal safety condition, not normal HDR rendering.
     */
    float terminal=
            smoothstep(0.88,0.995,sensorLoss)
            * smoothstep(0.95,1.25,y);
    float terminalEnergy=max3(safeRgb);
    safeRgb=mix(
            safeRgb,
            vec3(terminalEnergy),
            terminal);

    Output=max(safeRgb,vec3(0.0));
}
'@

$ColorMainNew = @'
/*
 * IRIS_26437_SENSOR_WHITE_POINT_COLOR_OWNERSHIP
 *
 * Repair chroma before white balance / matrix conversion, while camera-space
 * samples can still be compared to the real sensor white point.
 */
vec3 sensorNeutralFromGreen(vec3 cameraRgb) {
    vec3 gains=max(sensorGains,vec3(1.0e-6));
    float g=max(cameraRgb.g,0.0);
    return vec3(
            g*gains.g/gains.r,
            g,
            g*gains.g/gains.b);
}

void main() {
    ivec2 xy=ivec2(gl_FragCoord.xy);
    vec3 cameraRgb=max(texelFetch(InputBuffer,xy,0).rgb,vec3(0.0));

    float sensorClip=max(sensorClipLevel,1.0e-6);
    vec3 sensorRelative=cameraRgb/sensorClip;
    float peakRelative=max3(sensorRelative);

    /*
     * Real colors below sensor white are left untouched.
     * Near physical white, channel disagreement becomes progressively
     * untrustworthy because one or more CFA channels can already be saturated.
     */
    float whitePointLoss=smoothstep(0.920,0.995,peakRelative);
    float cameraPeak=max3(cameraRgb);
    float cameraFloor=min3(cameraRgb);
    float cameraSpread=
            (cameraPeak-cameraFloor)/max(cameraPeak,1.0e-6);
    float corruptionEvidence=smoothstep(0.10,0.48,cameraSpread);

    float neutralize=clamp(
            whitePointLoss*mix(0.30,1.0,corruptionEvidence),
            0.0,1.0);
    float terminal=smoothstep(0.985,1.005,peakRelative);
    neutralize=max(neutralize,terminal);

    vec3 safeCameraRgb=mix(
            cameraRgb,
            sensorNeutralFromGreen(cameraRgb),
            neutralize);

    vec3 balanced=safeCameraRgb*sensorGains;
    vec3 linearSrgb=max(transformBalanced(balanced),vec3(0.0));

    /*
     * No transformed-space overflow neutralization. White-point evidence alone
     * decides when highlight chroma has lost authority.
     */
    Output=linearSrgb;
}
'@

$S = Replace-Once $S $ColorMainOld $ColorMainNew 'COLOR sensor-white ownership'
WriteUtf8NoBom $P $S

# --------------------------------------------------------------------------
# 26437 DENOISE / DETAIL
# - no generic sharpening
# - materially lower residual cleanup
# - reference-edge anchor in DINIT is the primary detail recovery mechanism
# --------------------------------------------------------------------------
$P = Join-Path $Cand $DENOISEG
$S = Normalize-Lf (ReadT $P)

$StrengthOld = @'
    float flatLuma=mix(0.045,0.015,supportConfidence);
    float detailLuma=mix(0.012,0.003,supportConfidence);
    float lumaStrength=mix(
            flatLuma,
            detailLuma,
            detailEvidence);

    float flatChroma=mix(0.18,0.05,supportConfidence);
    float detailChroma=mix(0.06,0.015,supportConfidence);
    float chromaStrength=mix(
            flatChroma,
            detailChroma,
            detailEvidence);
'@

$StrengthNew = @'
    /*
     * IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP
     *
     * 26436 remained visibly soft. The owned reference-edge anchor now protects
     * real high-frequency geometry upstream, so this residual cleanup becomes
     * still lighter. This is preservation, not an unsharp-mask/sharpen pass.
     */
    float flatLuma=mix(0.028,0.008,supportConfidence);
    float detailLuma=mix(0.006,0.001,supportConfidence);
    float lumaStrength=mix(
            flatLuma,
            detailLuma,
            detailEvidence);

    float flatChroma=mix(0.12,0.035,supportConfidence);
    float detailChroma=mix(0.040,0.008,supportConfidence);
    float chromaStrength=mix(
            flatChroma,
            detailChroma,
            detailEvidence);
'@

$S = Replace-Once $S $StrengthOld $StrengthNew 'DENOISE lighter residual cleanup'
WriteUtf8NoBom $P $S

$P = Join-Path $Cand $DENOISEJ
$S = Normalize-Lf (ReadT $P)
$LogOld = @'
        Log.d(Name, "IRIS_26430_V2_OWNED_RESIDUAL_CLEANUP"
                + " effectiveSupport=" + effectiveSupport
                + " kernel=3x3"
                + " photonNoiseStateConsumed=false"
                + " noiseRstrConsumed=false"
                + " temporalReconstructionPrimaryDenoiser=true"
                + " sharpening=false");
'@
$LogNew = @'
        Log.d(Name, "IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP"
                + " effectiveSupport=" + effectiveSupport
                + " kernel=3x3"
                + " referenceEdgeAnchor=true"
                + " whitePointOwnedHighlights=true"
                + " residualCleanupReduced=true"
                + " photonNoiseStateConsumed=false"
                + " noiseRstrConsumed=false"
                + " temporalReconstructionPrimaryDenoiser=true"
                + " sharpening=false");
'@
$S = Replace-Once $S $LogOld $LogNew 'DENOISE Java permanent runtime marker'
WriteUtf8NoBom $P $S

# Version must be incremented in this same build script.
$VersionCandidate = @"
VERSION_MAJOR=0
VERSION_MINOR=9726437
VERSION_NAME=0.9726437
VERSION_BUILD=26437
"@
$VersionCandidate = ($VersionCandidate.TrimEnd("`r","`n") + "`r`n")
WriteUtf8NoBom (Join-Path $Cand $VERSION) $VersionCandidate

Write-Host "=== GATE 2A: TEMPORARY CANDIDATE ARCHITECTURE PROOF ==="

$CandidateChecks = @(
    @{F=$DINIT; M='IRIS_26437_WHITE_POINT_OWNED_REFERENCE_AND_EDGE_ANCHOR'},
    @{F=$DINIT; M='referenceAnchor=1.0+1.35*edgeStrength'},
    @{F=$DACC; M='IRIS_26437_SENSOR_WHITE_POINT_SHARED_HIGHLIGHT_AUTHORITY'},
    @{F=$DACC; M='IRIS_26437_SUBJECT_MOTION_REFERENCE_FALLBACK'},
    @{F=$DACC; M='temporalResidual > 2.75*oldConsensusScale'},
    @{F=$COLORG; M='IRIS_26437_SENSOR_WHITE_POINT_COLOR_OWNERSHIP'},
    @{F=$COLORG; M='Output=linearSrgb;'},
    @{F=$DENOISEG; M='IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP'},
    @{F=$DENOISEJ; M='IRIS_26437_DETAIL_PRESERVE_RESIDUAL_CLEANUP'}
)

foreach ($C in $CandidateChecks) {
    $Text = ReadT (Join-Path $Cand $C.F)
    if (-not $Text.Contains($C.M)) {
        Fail "Candidate missing $($C.M) in $($C.F)"
    }
}

$Acc = ReadT (Join-Path $Cand $DACC)
if ($Acc.Contains('perFrameCap')) {
    Fail "Hard per-frame cap returned"
}
if ($Acc.Contains('referenceCeiling')) {
    Fail "Hard total-support ceiling returned"
}
if ($Acc -match '\bcur\.r\b') {
    Fail "Evolving visible RGB entered motion trust"
}
if (-not $Acc.Contains('maximumSupport*8.0')) {
    Fail "Normal unrestricted support path missing"
}

$RenderInvariant = ReadT $RENDERG
if (-not $RenderInvariant.Contains('IRIS_26435_EXACT_26430_HEADROOM_BASE_MINUS_032EV')) {
    Fail "26436 render/exposure invariant changed unexpectedly"
}
if (-not $RenderInvariant.Contains('linearSrgb*=outputExposureScale;')) {
    Fail "0.80 render path invariant missing"
}

$GainInvariant = ReadT $GAINMAP
if (-not $GainInvariant.Contains('IRIS_26436_BROAD_REGION_CHROMA_PROTECTED_GAINMAP')) {
    Fail "Stable 26436 UHDR gain-map foundation missing"
}

$VC = ReadT (Join-Path $Cand $VERSION)
if ($VC -notmatch '(?m)^VERSION_NAME=0\.9726437\r?$' -or
    $VC -notmatch '(?m)^VERSION_BUILD=26437\r?$') {
    Fail "Candidate version is not 0.9726437 / 26437"
}

Write-Host "ALL TEMPORARY TRANSFORMATION ANCHORS: PASS"
Write-Host "candidate/source validation PASS"

Write-Host "=== GATE 3: REAL GLSL COMPILER VALIDATION ==="

$SdkDir = $null
$SdkLine = Get-Content -LiteralPath 'local.properties' |
    Where-Object { $_ -match '^\s*sdk\.dir\s*=' } |
    Select-Object -First 1
if ($SdkLine) {
    $SdkDir = (($SdkLine -split '=',2)[1].Trim()) `
        -replace '\\:', ':' `
        -replace '\\\\', '\' `
        -replace '\\ ', ' '
}
if (-not $SdkDir -or -not (Test-Path -LiteralPath $SdkDir)) {
    Fail "Decoded Android SDK path not found"
}

$Glslc = $null
$NdkRoot = Join-Path $SdkDir 'ndk'
if (Test-Path -LiteralPath $NdkRoot) {
    foreach ($Ndk in (Get-ChildItem -LiteralPath $NdkRoot -Directory |
                      Sort-Object Name -Descending)) {
        $Candidate = Join-Path $Ndk.FullName `
            'shader-tools\windows-x86_64\glslc.exe'
        if (Test-Path -LiteralPath $Candidate) {
            $Glslc = $Candidate
            break
        }
    }
}
if (-not $Glslc) {
    Fail "Android NDK glslc.exe not found; real source has NOT been modified"
}

Write-Host ("Shader compiler: " + $Glslc)

$WrapDir = Join-Path $Safety "glsl_wrapped"
$SpvDir = Join-Path $Safety "glsl_spv"
New-Item -ItemType Directory -Force -Path $WrapDir,$SpvDir | Out-Null

$ShaderFiles = @(
    @{P=(Join-Path $Cand $DINIT); Stage='compute'; Name='direct_init'},
    @{P=(Join-Path $Cand $DACC); Stage='compute'; Name='direct_accumulate'},
    @{P=(Join-Path $Cand $COLORG); Stage='fragment'; Name='color'},
    @{P=(Join-Path $Cand $DENOISEG); Stage='fragment'; Name='denoise'}
)

$CompilerOutput = New-Object System.Collections.Generic.List[string]

foreach ($Item in $ShaderFiles) {
    $Text = Normalize-Lf (ReadT $Item.P)

    if ($Item.Stage -eq 'compute') {
        $Text = [regex]::Replace(
            $Text,
            '(?m)^#define\s+LAYOUT\s+//\s*\nLAYOUT\s*\n',
            '',
            1)
        $Text =
            "#version 310 es`n" +
            "layout(local_size_x=8, local_size_y=8, local_size_z=1) in;`n" +
            $Text
    } else {
        $Text = "#version 310 es`n" + $Text
    }

    $Wrapped = Join-Path $WrapDir ($Item.Name + '.glsl')
    $Spv = Join-Path $SpvDir ($Item.Name + '.spv')
    WriteUtf8NoBom $Wrapped $Text

    $Args = @(
        '--target-env=opengl',
        '-fauto-map-locations',
        '-fauto-bind-uniforms',
        ('-fshader-stage=' + $Item.Stage),
        $Wrapped,
        '-o',
        $Spv
    )

    $OldEA = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $Lines = & $Glslc @Args 2>&1
        $Rc = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $OldEA
    }

    $CompilerOutput.Add(
        ("===== {0} stage={1} =====" -f $Item.Name,$Item.Stage))
    foreach ($Line in $Lines) {
        $CompilerOutput.Add([string]$Line)
    }

    if ($Rc -ne 0 -or -not (Test-Path -LiteralPath $Spv)) {
        $CompilerOutput |
            Set-Content -LiteralPath $GlslLog -Encoding UTF8
        Fail "glslc failed for $($Item.Name); see $GlslLog. Real source has NOT been modified."
    }
}

$CompilerOutput | Set-Content -LiteralPath $GlslLog -Encoding UTF8

Write-Host "REAL GLSL COMPILER PROOF: PASS"
Write-Host "Temporary-copy validation: PASS"

Write-Host "=== GATE 4: APPLY EXACT VALIDATED CANDIDATES ==="

foreach ($Rel in $Targets) {
    $From = Join-Path $Cand $Rel
    Copy-Item -LiteralPath $From -Destination $Rel -Force
}

Hash-Protected $Targets $ProtectedAfter
if ((Get-Content $ProtectedBefore -Raw) -ne
    (Get-Content $ProtectedAfter -Raw)) {
    Fail "Protected tracked app source changed"
}

if (-not (Test-Path -LiteralPath 'local.properties')) {
    Fail "local.properties was lost"
}
if (-not (Select-String -LiteralPath 'local.properties' `
        -Pattern 'sdk.dir' -SimpleMatch -Quiet)) {
    Fail "sdk.dir was lost"
}

& git diff --check -- $Targets
if ($LASTEXITCODE -ne 0) {
    Fail "git diff --check failed"
}

# Re-prove real source after application.
foreach ($C in $CandidateChecks) {
    $Text = ReadT $C.F
    if (-not $Text.Contains($C.M)) {
        Fail "Post-apply source missing $($C.M)"
    }
}

# Important visual invariants: render and gain map were intentionally NOT edited.
if ((Sha $RENDERG) -ne $ExpectedHashes[$RENDERG]) {
    Fail "Render/exposure source changed unexpectedly"
}
if (-not (ReadT $GAINMAP).Contains('IRIS_26436_BROAD_REGION_CHROMA_PROTECTED_GAINMAP')) {
    Fail "Stable UHDR source changed unexpectedly"
}

Write-Host "candidate/source validation PASS"
Write-Host "Temporary-copy validation: PASS"
Write-Host "PRE-BUILD SAFETY PROOF PASSED"

& git diff --binary HEAD -- app |
    Out-File -LiteralPath $PostPatch -Encoding utf8
if ($LASTEXITCODE -ne 0) {
    Fail "Post-edit patch failed"
}

Write-Host "=== GATE 5: JAVAC PROOF ==="

$JdkCandidates = @(
    'C:\Program Files\Eclipse Adoptium\jdk-17.0.20.8-hotspot',
    'C:\Program Files\Android\Android Studio\jbr'
)
foreach ($Jdk in $JdkCandidates) {
    if (Test-Path (Join-Path $Jdk 'bin\java.exe')) {
        $env:JAVA_HOME = $Jdk
        break
    }
}
if (-not $env:JAVA_HOME -or
    -not (Test-Path (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
    Fail "Java 17 / Android Studio JBR not found"
}
$env:Path = "$env:JAVA_HOME\bin;$env:Path"

$OldEA = $ErrorActionPreference
try {
    $ErrorActionPreference = 'Continue'
    & .\gradlew.bat :app:compileDebugJavaWithJavac --stacktrace 2>&1 |
        Tee-Object -FilePath $JavacLog
    $JavacRc = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $OldEA
}

if ($JavacRc -ne 0) {
    Fail "Javac failed; see $JavacLog"
}
if (-not (ReadT $JavacLog).Contains('BUILD SUCCESSFUL')) {
    Fail "Javac BUILD SUCCESSFUL missing"
}
Write-Host "JAVAC PROOF PASSED"

Write-Host "=== GATE 6: BUILD 0.9726437 / 26437 ==="

try {
    $ErrorActionPreference = 'Continue'
    & .\gradlew.bat :app:assembleDebug --stacktrace 2>&1 |
        Tee-Object -FilePath $BuildLog
    $BuildRc = $LASTEXITCODE
}
finally {
    $ErrorActionPreference = $OldEA
}

if ($BuildRc -ne 0) {
    Fail "Gradle build failed; see $BuildLog"
}
if (-not (ReadT $BuildLog).Contains('BUILD SUCCESSFUL')) {
    Fail "BUILD SUCCESSFUL missing from build log"
}

$Built = Get-ChildItem -LiteralPath 'app\build\outputs\apk' `
    -Recurse -File -Filter '*.apk' |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1

if (-not $Built) {
    Fail "Built APK not found"
}

Get-ChildItem -LiteralPath $Repo -File -Filter 'IrisCamera-*.apk' `
    -ErrorAction SilentlyContinue |
    Remove-Item -Force

Move-Item -LiteralPath $Built.FullName -Destination $ApkOut -Force

# Exactly one APK: root artifact only.
Get-ChildItem -LiteralPath 'app\build' -Recurse -File -Filter '*.apk' `
    -ErrorAction SilentlyContinue |
    Remove-Item -Force

@(
    '26437 WINDOWS INTEGRATED MOTION BUILD'
    ('Timestamp: ' + (Get-Date -Format o))
    'Version/build: 0.9726437 / 26437'
    ''
    'WHITE POINT / MAGENTA ZIPPER'
    '- sensor physical white point now owns highlight chroma authority'
    '- near-white auxiliary observations locally fall back to physical reference'
    '- reference init coherently neutralizes only physically lost highlight chroma'
    '- no transformed-space generic highlight whitening'
    ''
    'MOTION / GHOSTING'
    '- all frames retained and globally eligible'
    '- temporal-consensus threshold tightened locally'
    '- reference-patch disagreement squared'
    '- flow discontinuity / occlusion trust squared'
    '- hard local reference fallback for temporal/reference/occlusion conflict'
    '- no global frame cap / no hard total-support ceiling'
    ''
    'DETAIL'
    '- owned reference edges receive more merge authority'
    '- residual luma/chroma cleanup reduced'
    '- no generic sharpening / unsharp mask'
    ''
    'EXPOSURE / UHDR'
    '- 26436 0.80 output exposure scale intentionally unchanged'
    '- stable 26436 broad chroma-protected UHDR gain map intentionally unchanged'
    ''
    'RUNTIME OBSERVABILITY'
    '- MotionV2Denoise runtime marker upgraded to IRIS_26437'
    '- existing 26436 alignment/support/gain-map permanent logging preserved'
    ''
    'SAFETY'
    ('Backup branch: ' + $Backup)
    ('Pre patch: ' + $PrePatch)
    ('Post patch: ' + $PostPatch)
    ('GLSL proof: ' + $GlslLog)
    ('Javac proof: ' + $JavacLog)
    ('Build log: ' + $BuildLog)
    ('APK: ' + $ApkOut)
    ''
    'POWERSHELL SCRIPT PARSER: PASS'
    'ALL TEMPORARY TRANSFORMATION ANCHORS: PASS'
    'candidate/source validation PASS'
    'REAL GLSL COMPILER PROOF: PASS'
    'Temporary-copy validation: PASS'
    'PRE-BUILD SAFETY PROOF PASSED'
    'JAVAC PROOF PASSED'
    'BUILD SUCCESSFUL VERIFIED'
    ''
    'No commit.'
    'No push.'
    'dev untouched.'
    'local.properties protected.'
) | Set-Content -LiteralPath $Result -Encoding UTF8

Write-Host "======================================================================"
Write-Host "26437 WINDOWS BUILD SUCCESSFUL"
Write-Host "APK: $ApkOut"
Write-Host "RESULT: $Result"
Write-Host "No commit. No push. dev untouched."
Write-Host "======================================================================"
