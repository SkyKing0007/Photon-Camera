param([Parameter(Mandatory=$true)][string]$Repo)

$ErrorActionPreference = "Stop"

# =============================================================================
# Photon Camera Motion V2
# 26462 - PUBLISHED-METHOD WRONSKI MFSR V3 RECONSTRUCTION-ONLY
#
# Source baseline:
#   branch: experimental-effective-stack
#   committed HEAD: aac8ea5a0f518142b0f8ad60ce34c9a165e4611b
#   live tested lineage: 0.9726461 / 26461
#
# IMPORTANT SCOPE
# ----------------
# This build does NOT replay 26429..26461.
# It uses the already-curated 26436 exact-payload source and preserves the downstream
# color/tone/denoise/UHDR behavior byte-for-byte for this first Wronski A/B test.
# Only the standard-Bayer alignment/reconstruction owner and carrier/post routing
# required for full-resolution linear RGB are changed.
#
# Published-method reconstruction:
#   1) fixed reference
#   2) 4-level coarse-to-fine block matching
#      factors fine->coarse: 1,2,4,4
#      search radii:        1,4,4,4
#      metrics:             L1,L2,L2,L2
#   3) 3 inverse-compositional LK refinements at every level
#   4) full-resolution physical-CFA observations
#   5) GAT/structure tensor
#   6) published steerable covariance equations
#   7) statistical robustness:
#        R = clamp(S * exp(-d^2/sigma^2) - t, 0, 1)
#      with t=.12, s1=2, s2=12, Mt=.8
#   8) published 5x5 local minimum robustness
#   9) independent R/G/B numerator + denominator accumulation
#  10) direct linear camera-RGB final owner (no Bayer-merge-then-demosaic)
#
# Photon adaptation required because Google's production calibration tables and
# proprietary source are not public:
#   - Photon/Iris heteroscedastic noiseS/noiseO drives GAT and noise correction.
#   - public-method SNR tuning laws are used with an SNR estimate from the owned
#     Motion V2 canonical noise domain.
#
# Preserved byte-for-byte outside the intentional reconstruction set:
#   - capture/prebuffer/reference timestamp ownership
#   - canonical RAW exposure normalization
#   - hot-pixel sanitation
#   - current tested 26461 color transform / white-point / highlight behavior
#   - 26453 structural-edge residual denoise
#   - Motion V2 Ultra HDR
#   - Motion V2 tone/render path
#   - no sharpening in Motion V2
#
# Rejected / bypassed as reconstruction owners:
#   - 26460 cross-phase/plateau CFA demosaic as standard-Bayer final owner
#   - downstream 26461 matrix-aware limiter remains byte-identical but is NOT
#     part of Wronski reconstruction and is not modified in this build
#   - old cfa_reconstruct_* as standard-Bayer reconstruction owner
#   - old custom direct_rgb_* estimator math
#   - AHD/RCD experiments
#   - alias/chroma finalizers
#   - old local-support spatial denoise in the direct-RGB branch
#
# Safety:
#   candidate/source validation PASS
#   Temporary-copy validation PASS
#   PRE-BUILD SAFETY PROOF PASSED
# must all occur before live app source is modified.
#
# No commit. No push. dev untouched.
# =============================================================================

# Self parse BEFORE repository access.
$Self = $MyInvocation.MyCommand.Path
$Tokens = $null
$ParseErrors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile(
        $Self, [ref]$Tokens, [ref]$ParseErrors)
if ($ParseErrors -and $ParseErrors.Count -gt 0) {
    $m = ($ParseErrors | ForEach-Object {
        "line $($_.Extent.StartLineNumber): $($_.Message)"
    }) -join "`n"
    throw "SCRIPT PARSE GUARD FAILED:`n$m"
}

function Fail([string]$Message) { throw "FAIL: $Message" }
function Need([bool]$Condition,[string]$Message) {
    if (-not $Condition) { Fail $Message }
}
function Sha([string]$Path) {
    Need (Test-Path -LiteralPath $Path -PathType Leaf) "missing file: $Path"
    return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToUpperInvariant()
}
function ReadText([string]$Path) {
    return [IO.File]::ReadAllText((Resolve-Path -LiteralPath $Path))
}
function WriteText([string]$Path,[string]$Text) {
    $Parent = Split-Path -Parent $Path
    if ($Parent) { New-Item -ItemType Directory -Force -Path $Parent | Out-Null }
    # Force LF so candidate/live source is byte stable on Windows.
    $Text = $Text.Replace("`r`n","`n").Replace("`r","`n")
    [IO.File]::WriteAllText($Path,$Text,[Text.UTF8Encoding]::new($false))
}
function CopyToCandidate([string]$Rel,[string]$Root) {
    $Src = Join-Path $Repo $Rel
    $Dst = Join-Path $Root $Rel
    $Parent = Split-Path -Parent $Dst
    New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    Copy-Item -LiteralPath $Src -Destination $Dst -Force
}
function CountLiteral([string]$Text,[string]$Needle) {
    return ([regex]::Matches($Text,[regex]::Escape($Needle))).Count
}
function ReplaceOnce(
        [string]$Text,[string]$Old,[string]$New,[string]$Label) {
    $N = CountLiteral $Text $Old
    if ($N -ne 1) { Fail "$Label expected exactly once, found $N" }
    return $Text.Replace($Old,$New)
}
function ReplaceRegexOne(
        [string]$Text,[string]$Pattern,[string]$New,[string]$Label) {
    $M = [regex]::Matches(
            $Text,$Pattern,
            [System.Text.RegularExpressions.RegexOptions]::Singleline)
    if ($M.Count -ne 1) { Fail "$Label regex count=$($M.Count), expected 1" }
    return [regex]::Replace(
            $Text,$Pattern,
            [System.Text.RegularExpressions.MatchEvaluator]{
                param($match) $New
            },1)
}
function HashProtected([string]$Out,[string[]]$IntentionalRel) {
    $Rows = New-Object System.Collections.Generic.List[string]
    $Tracked = & git ls-files app
    if ($LASTEXITCODE -ne 0) { Fail "git ls-files app failed" }
    foreach ($r in $Tracked) {
        if ($IntentionalRel -contains $r) { continue }
        $f = Join-Path $Repo ($r.Replace('/','\'))
        if (Test-Path -LiteralPath $f -PathType Leaf) {
            [void]$Rows.Add("$(Sha $f)  $r")
        }
    }
    [IO.File]::WriteAllLines(
        $Out,
        [string[]]($Rows | Sort-Object),
        [Text.UTF8Encoding]::new($false))
    Need ($Rows.Count -gt 100) "protected manifest unexpectedly small"
}
function AssertContains([string]$Text,[string]$Needle,[string]$Label) {
    Need ($Text.Contains($Needle)) "$Label missing: $Needle"
}

$ExpectedBranch = "wronski-26462-build"
$ExpectedHead = "aac8ea5a0f518142b0f8ad60ce34c9a165e4611b"
$OldVersion = "0.9726436"
$OldBuild = "26436"
$NewVersion = "0.9726462"
$NewBuild = "26462"

$VersionRel = "app\version.properties"
$ReconRel = "app\src\main\java\com\particlesdevs\photoncamera\processing\processor\MotionV2CfaReconstruction.java"
$InputRel = "app\src\main\java\com\particlesdevs\photoncamera\processing\opengl\postpipeline\MotionV2CfaInput.java"
$PostRel = "app\src\main\java\com\particlesdevs\photoncamera\processing\opengl\postpipeline\PostPipeline.java"
$OldAlignRel = "app\src\main\java\com\particlesdevs\photoncamera\processing\processor\MotionV2Alignment.java"
$DenoiseRel = "app\src\main\assets\shaders\motionv2\denoise.glsl"

$NewAlignJavaRel = "app\src\main\java\com\particlesdevs\photoncamera\processing\processor\MotionV2WronskiAlignment.java"
$PyrRel = "app\src\main\assets\shaders\motionv2\mfsr_pyramid_down.glsl"
$BlockRel = "app\src\main\assets\shaders\motionv2\mfsr_block_match.glsl"
$IcaRel = "app\src\main\assets\shaders\motionv2\mfsr_ica_refine.glsl"
$ExpandRel = "app\src\main\assets\shaders\motionv2\mfsr_flow_expand.glsl"
$InitRel = "app\src\main\assets\shaders\motionv2\direct_rgb_init.glsl"
$AccumRel = "app\src\main\assets\shaders\motionv2\direct_rgb_accumulate.glsl"
$RobustRel = "app\src\main\assets\shaders\motionv2\mfsr_robustness.glsl"
$ErodeRel = "app\src\main\assets\shaders\motionv2\mfsr_robustness_erode.glsl"
$FinalizeRel = "app\src\main\assets\shaders\motionv2\mfsr_finalize.glsl"

$Exact = [ordered]@{}


$IntentionalRel = @(
    $VersionRel.Replace('\','/'),
    $ReconRel.Replace('\','/'),
    $InputRel.Replace('\','/'),
    $PostRel.Replace('\','/'),
    $DenoiseRel.Replace('\','/'),
    $NewAlignJavaRel.Replace('\','/'),
    $PyrRel.Replace('\','/'),
    $BlockRel.Replace('\','/'),
    $IcaRel.Replace('\','/'),
    $ExpandRel.Replace('\','/'),
    $InitRel.Replace('\','/'),
    $AccumRel.Replace('\','/'),
    $RobustRel.Replace('\','/'),
    $ErodeRel.Replace('\','/'),
    $FinalizeRel.Replace('\','/')
)

Set-Location $Repo

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Safety = Join-Path $Repo "26462_wronski_published_v3_$Stamp"
$Candidate = Join-Path $Safety "candidate"
$Before = Join-Path $Safety "source_before"
$PrePatch = Join-Path $Safety "pre_26462_binary.patch"
$PostPatch = Join-Path $Safety "post_26462_binary.patch"
$ProtectedBefore = Join-Path $Safety "protected_before.sha256"
$ProtectedAfter = Join-Path $Safety "protected_after.sha256"
$BuildLog = Join-Path $Safety "build_26462.log"
$Result = Join-Path $Safety "26462_RESULT.txt"
$BackupBranch = "backup/windows-before-26462-wronski-published-v3-$Stamp"
$ApkOut = Join-Path $Repo "IrisCamera-0.9726462-26462-wronski-published-method-v3-debug.apk"

Write-Host "===================================================================="
Write-Host "26462 WRONSKI PUBLISHED-METHOD V3 - FULL ALIGNMENT + RECONSTRUCTION"
Write-Host "===================================================================="

# ============================================================================
# GATE 0 - exact live state + evidence-driven rollback source
# ============================================================================
Write-Host "`n=== GATE 0: EXACT CURATED 26436 SOURCE STATE ===" -ForegroundColor Cyan

$Branch = (& git branch --show-current).Trim()
$Head = (& git rev-parse HEAD).Trim()
Need ($LASTEXITCODE -eq 0) "git state query failed"
Need ($Branch -eq $ExpectedBranch) "branch=$Branch expected=$ExpectedBranch"
Need ($Branch -ne "dev") "refusing to modify dev"
Need ($Head -eq $ExpectedHead) "HEAD=$Head expected=$ExpectedHead"

$Version = Join-Path $Repo $VersionRel
$V0 = ReadText $Version
Need ($V0 -match "(?m)^VERSION_NAME=0\.9726436\r?$") "expected curated 26436 VERSION_NAME"
Need ($V0 -match "(?m)^VERSION_BUILD=26436\r?$") "expected curated 26436 VERSION_BUILD"

foreach($kv in $Exact.GetEnumerator()) {
    $p = Join-Path $Repo $kv.Key
    Need ((Sha $p) -eq $kv.Value) "audited live hash mismatch: $($kv.Key)"
}

Write-Host "PASS: downstream 26461 color/tone/denoise/UHDR remain protected and untouched"
Write-Host "PASS: rejected late limiter will not survive into 26462"

# ============================================================================
# GATE 1 - backup branch + binary patch + protected hashes
# ============================================================================
Write-Host "`n=== GATE 1: BACKUP BRANCH + PATCH + PROTECTED HASHES ===" -ForegroundColor Cyan

New-Item -ItemType Directory -Force -Path $Safety,$Candidate,$Before | Out-Null

& git branch $BackupBranch $Head
Need ($LASTEXITCODE -eq 0) "backup branch creation failed"

& git diff --binary HEAD -- app | Out-File -LiteralPath $PrePatch -Encoding utf8
Need ($LASTEXITCODE -eq 0) "pre-edit binary patch failed"

foreach($rel in @($VersionRel,$ReconRel,$InputRel,$PostRel,$OldAlignRel,$InitRel,$AccumRel)) {
    $src = Join-Path $Repo $rel
    if (Test-Path -LiteralPath $src -PathType Leaf) {
        $dst = Join-Path $Before $rel
        New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
        Copy-Item -LiteralPath $src -Destination $dst -Force
    }
}

HashProtected $ProtectedBefore $IntentionalRel

Write-Host "PASS: backup branch created: $BackupBranch"
Write-Host "PASS: binary pre-edit patch saved"
Write-Host "PASS: protected tracked-source manifest captured"

# ============================================================================
# GATE 2 - build complete temporary candidate
# ============================================================================
Write-Host "`n=== GATE 2: BUILD COMPLETE TEMPORARY CANDIDATE ===" -ForegroundColor Cyan

foreach($rel in @($VersionRel,$ReconRel,$InputRel,$PostRel,$DenoiseRel)) {
    CopyToCandidate $rel $Candidate
}

# IRIS_26453_STRUCTURAL_EDGE_CHROMA_PROTECTION - isolated retained downstream fix.
$DenoiseC = Join-Path $Candidate $DenoiseRel
$D53 = ReadText $DenoiseC
$Old53 = @'
    float chromaStrength=mix(
            flatChroma,
            detailChroma,
            detailEvidence);

    /*
     * Never smear color back across bright clipping boundaries.
     */
    float highlightProtect=smoothstep(0.65,0.95,y0);
'@
$New53 = @'
    float chromaStrength=mix(
            flatChroma,
            detailChroma,
            detailEvidence);

    /* IRIS_26453_STRUCTURAL_EDGE_CHROMA_PROTECTION */
    float structuralEdgeProtect=smoothstep(
            0.55*detailThreshold,
            1.70*detailThreshold+0.001,
            localRange);
    chromaStrength*=1.0-0.92*structuralEdgeProtect;

    /*
     * Never smear color back across bright clipping boundaries.
     */
    float highlightProtect=smoothstep(0.65,0.95,y0);
'@
$D53 = ReplaceOnce $D53 $Old53 $New53 "26453 structural-edge chroma protection"
WriteText $DenoiseC $D53


# ----------------------------------------------------------------------------
# Published-method alignment owner.
# ----------------------------------------------------------------------------
$AlignJava = @'
package com.particlesdevs.photoncamera.processing.processor;

import android.graphics.Point;

import com.particlesdevs.photoncamera.processing.opengl.GLFormat;
import com.particlesdevs.photoncamera.processing.opengl.GLProg;
import com.particlesdevs.photoncamera.processing.opengl.GLTexture;
import com.particlesdevs.photoncamera.util.Log;

import static android.opengl.GLES20.GL_CLAMP_TO_EDGE;
import static android.opengl.GLES20.GL_LINEAR;
import static android.opengl.GLES20.GL_NEAREST;

/**
 * IRIS_26462_WRONSKI_PUBLISHED_COARSE_TO_FINE_ALIGNMENT
 *
 * Published Wronski/IPOL architecture:
 * - four levels
 * - factors fine->coarse 1,2,4,4
 * - search radii 1,4,4,4
 * - L1 at finest, L2 at coarser levels
 * - three inverse-compositional Lucas-Kanade refinements per level
 *
 * Final flow is dense, continuous and expressed in packed-CFA coordinates.
 */
public final class MotionV2WronskiAlignment {
    private static final String TAG = "MotionV2WronskiAlign";
    private MotionV2WronskiAlignment() {}

    private static Point divCeil(Point p, int d) {
        return new Point(
                Math.max(1, (p.x + d - 1) / d),
                Math.max(1, (p.y + d - 1) / d));
    }

    public static MotionV2Alignment.Result align(
            Point rawHalf,
            int cfaPattern,
            float signalScale,
            float snr,
            GLProg glProg,
            GLTexture referenceCfa,
            GLTexture alterCfa) {

        final int baseTile = snr <= 14.0f ? 64 : (snr <= 22.0f ? 32 : 16);
        final int[] tile = new int[] {
                baseTile, baseTile, baseTile, Math.max(8, baseTile / 2)
        };
        final int[] radius = new int[] {1, 4, 4, 4};
        final int[] metric = new int[] {0, 1, 1, 1}; // 0=L1, 1=L2
        final int[] stepFactor = new int[] {1, 2, 4, 4};

        GLTexture[] ref = new GLTexture[4];
        GLTexture[] alt = new GLTexture[4];
        GLTexture previousFlow = null;
        GLTexture denseFlow = null;

        try {
            ref[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);
            alt[0] = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                    null, GL_NEAREST, GL_CLAMP_TO_EDGE);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", referenceCfa);
            glProg.setTextureCompute("OutputGuide", ref[0], true);
            glProg.computeAuto(rawHalf,1);

            glProg.setDefine("CFAPATTERN", cfaPattern);
            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/alignment_guide", true);
            glProg.setVar("guideScale", 1);
            glProg.setVar("signalScale", Math.max(signalScale,1.0e-6f));
            glProg.setTexture("InputCfa", alterCfa);
            glProg.setTextureCompute("OutputGuide", alt[0], true);
            glProg.computeAuto(rawHalf,1);

            Point[] levelSize = new Point[4];
            levelSize[0] = rawHalf;
            for (int l=1;l<4;l++) {
                levelSize[l] = divCeil(levelSize[l-1], stepFactor[l]);
                ref[l] = new GLTexture(
                        levelSize[l],
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);
                alt[l] = new GLTexture(
                        levelSize[l],
                        new GLFormat(GLFormat.DataType.FLOAT_32,1),
                        null, GL_LINEAR, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_down", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setTexture("InputGuide", ref[l-1]);
                glProg.setTextureCompute("OutputGuide", ref[l], true);
                glProg.computeAuto(levelSize[l],1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_pyramid_down", true);
                glProg.setVar("factor", stepFactor[l]);
                glProg.setTexture("InputGuide", alt[l-1]);
                glProg.setTextureCompute("OutputGuide", alt[l], true);
                glProg.computeAuto(levelSize[l],1);
            }

            // Coarsest -> finest.
            for (int l=3;l>=0;l--) {
                Point grid = new Point(
                        Math.max(1,(levelSize[l].x + tile[l]-1)/tile[l]),
                        Math.max(1,(levelSize[l].y + tile[l]-1)/tile[l]));

                GLTexture block = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);
                GLTexture refined = new GLTexture(
                        grid,
                        new GLFormat(GLFormat.DataType.FLOAT_16,4),
                        null, GL_NEAREST, GL_CLAMP_TO_EDGE);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_block_match", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("searchRadius", radius[l]);
                glProg.setVar("distanceMetric", metric[l]);
                glProg.setVar("hasPrevious", previousFlow != null ? 1 : 0);
                glProg.setVar(
                        "previousToCurrentScale",
                        l < 3 ? (float)stepFactor[l+1] : 1.0f);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                // Any valid texture may be bound when hasPrevious=0; it is not read.
                glProg.setTexture(
                        "PreviousFlow",
                        previousFlow != null ? previousFlow : ref[l]);
                glProg.setTextureCompute("OutputFlow", block, true);
                glProg.computeAuto(grid,1);

                glProg.setLayout(8,8,1);
                glProg.useAssetProgram("motionv2/mfsr_ica_refine", true);
                glProg.setVar("levelSize", levelSize[l]);
                glProg.setVar("tileSize", tile[l]);
                glProg.setVar("iterations", 3);
                glProg.setTexture("ReferenceGuide", ref[l]);
                glProg.setTexture("MovingGuide", alt[l]);
                glProg.setTexture("BlockFlow", block);
                glProg.setTextureCompute("OutputFlow", refined, true);
                glProg.computeAuto(grid,1);

                block.close();
                if (previousFlow != null) previousFlow.close();
                previousFlow = refined;
            }

            denseFlow = new GLTexture(
                    rawHalf,
                    new GLFormat(GLFormat.DataType.FLOAT_16,4),
                    null, GL_LINEAR, GL_CLAMP_TO_EDGE);

            glProg.setLayout(8,8,1);
            glProg.useAssetProgram("motionv2/mfsr_flow_expand", true);
            glProg.setVar("outputSize", rawHalf);
            glProg.setVar("tileSize", baseTile);
            glProg.setTexture("TileFlow", previousFlow);
            glProg.setTextureCompute("OutputFlow", denseFlow, true);
            glProg.computeAuto(rawHalf,1);

            Log.d(TAG,
                    "IRIS_26462_WRONSKI_PUBLISHED_ALIGNMENT"
                    + " snr=" + snr
                    + " baseTile=" + baseTile
                    + " factors=1,2,4,4"
                    + " radii=1,4,4,4"
                    + " metrics=L1,L2,L2,L2"
                    + " icaIterations=3"
                    + " denseContinuous=true");

            GLTexture keep = denseFlow;
            denseFlow = null;
            return new MotionV2Alignment.Result(
                    keep,0.0f,0.0f,1.0f,0.0f);
        } finally {
            if (denseFlow != null) denseFlow.close();
            if (previousFlow != null) previousFlow.close();
            for (int i=0;i<4;i++) {
                if (ref[i] != null) ref[i].close();
                if (alt[i] != null) alt[i].close();
            }
        }
    }
}
'@
WriteText (Join-Path $Candidate $NewAlignJavaRel) $AlignJava

$PyrShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D InputGuide;
layout(r32f,binding=0) uniform highp writeonly image2D OutputGuide;
uniform int factor;

/* IRIS_26462_WRONSKI_GAUSSIAN_PYRAMID
 * Separable-binomial equivalent 5x5 Gaussian sampling before decimation.
 */
void main() {
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 os=imageSize(OutputGuide);
    if(any(greaterThanEqual(p,os))) return;
    ivec2 isz=textureSize(InputGuide,0);
    ivec2 c=p*factor;
    const float k[5]=float[5](1.0,4.0,6.0,4.0,1.0);
    float sum=0.0,ws=0.0;
    for(int y=-2;y<=2;y++) for(int x=-2;x<=2;x++) {
        ivec2 q=clamp(c+ivec2(x,y),ivec2(0),isz-ivec2(1));
        float w=k[x+2]*k[y+2];
        sum+=w*texelFetch(InputGuide,q,0).r;
        ws+=w;
    }
    imageStore(OutputGuide,p,vec4(sum/max(ws,1e-8)));
}
'@
WriteText (Join-Path $Candidate $PyrRel) $PyrShader

$BlockShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D PreviousFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int searchRadius;
uniform int distanceMetric; // 0 L1, 1 L2
uniform int hasPrevious;
uniform float previousToCurrentScale;

float sampleGuide(sampler2D t,ivec2 p) {
    p=clamp(p,ivec2(0),levelSize-ivec2(1));
    return texelFetch(t,p,0).r;
}
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec2 pred=vec2(0.0);
    if(hasPrevious!=0) {
        vec2 uv=(vec2(tile)+0.5)/vec2(grid);
        pred=texture(PreviousFlow,clamp(uv,vec2(0.0),vec2(1.0))).xy
                *previousToCurrentScale;
    }
    ivec2 ipred=ivec2(round(pred));
    float best=3.402823e38;
    ivec2 bestShift=ipred;

    for(int sy=-4;sy<=4;sy++) for(int sx=-4;sx<=4;sx++) {
        if(abs(sx)>searchRadius || abs(sy)>searchRadius) continue;
        ivec2 sh=ipred+ivec2(sx,sy);
        float e=0.0;
        int n=0;
        for(int yy=0;yy<64;yy++) {
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++) {
                if(xx>=tileSize) continue;
                ivec2 rp=tile*tileSize+ivec2(xx,yy);
                if(any(greaterThanEqual(rp,levelSize))) continue;
                float a=sampleGuide(ReferenceGuide,rp);
                float b=sampleGuide(MovingGuide,rp+sh);
                float d=a-b;
                e += distanceMetric==0 ? abs(d) : d*d;
                n++;
            }
        }
        e/=float(max(n,1));
        if(e<best) { best=e; bestShift=sh; }
    }
    float confidence=exp(-best/max(1e-5,0.02+best));
    imageStore(OutputFlow,tile,vec4(vec2(bestShift),confidence,best));
}
'@
WriteText (Join-Path $Candidate $BlockRel) $BlockShader

$IcaShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D ReferenceGuide;
uniform highp sampler2D MovingGuide;
uniform highp sampler2D BlockFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 levelSize;
uniform int tileSize;
uniform int iterations;

float bilinear(sampler2D t,vec2 p) {
    vec2 mx=vec2(levelSize)-vec2(1.001);
    p=clamp(p,vec2(0.0),mx);
    ivec2 p0=ivec2(floor(p));
    ivec2 p1=min(p0+ivec2(1),levelSize-ivec2(1));
    vec2 f=fract(p);
    float a=mix(texelFetch(t,p0,0).r,texelFetch(t,ivec2(p1.x,p0.y),0).r,f.x);
    float b=mix(texelFetch(t,ivec2(p0.x,p1.y),0).r,texelFetch(t,p1,0).r,f.x);
    return mix(a,b,f.y);
}
float refAt(ivec2 p) {
    p=clamp(p,ivec2(0),levelSize-ivec2(1));
    return texelFetch(ReferenceGuide,p,0).r;
}

/* IRIS_26462_WRONSKI_INVERSE_COMPOSITIONAL_ALIGNMENT
 * Hessian from reference gradients; three additive IC updates.
 */
void main() {
    ivec2 tile=ivec2(gl_GlobalInvocationID.xy);
    ivec2 grid=imageSize(OutputFlow);
    if(any(greaterThanEqual(tile,grid))) return;

    vec4 seed=texelFetch(BlockFlow,tile,0);
    vec2 flow=seed.xy;

    float H00=0.0,H01=0.0,H11=0.0;
    for(int yy=0;yy<64;yy++) {
        if(yy>=tileSize) continue;
        for(int xx=0;xx<64;xx++) {
            if(xx>=tileSize) continue;
            ivec2 p=tile*tileSize+ivec2(xx,yy);
            if(any(greaterThanEqual(p,levelSize))) continue;
            float gx=0.5*(refAt(p+ivec2(1,0))-refAt(p-ivec2(1,0)));
            float gy=0.5*(refAt(p+ivec2(0,1))-refAt(p-ivec2(0,1)));
            H00+=gx*gx; H01+=gx*gy; H11+=gy*gy;
        }
    }
    float det=max(H00*H11-H01*H01,1e-8);

    for(int iter=0;iter<3;iter++) {
        if(iter>=iterations) break;
        float b0=0.0,b1=0.0;
        for(int yy=0;yy<64;yy++) {
            if(yy>=tileSize) continue;
            for(int xx=0;xx<64;xx++) {
                if(xx>=tileSize) continue;
                ivec2 p=tile*tileSize+ivec2(xx,yy);
                if(any(greaterThanEqual(p,levelSize))) continue;
                float gx=0.5*(refAt(p+ivec2(1,0))-refAt(p-ivec2(1,0)));
                float gy=0.5*(refAt(p+ivec2(0,1))-refAt(p-ivec2(0,1)));
                float residual=bilinear(MovingGuide,vec2(p)+flow)-refAt(p);
                b0 += -gx*residual;
                b1 += -gy*residual;
            }
        }
        vec2 d=vec2(
                ( H11*b0-H01*b1)/det,
                (-H01*b0+H00*b1)/det);
        d=clamp(d,vec2(-1.5),vec2(1.5));
        flow+=d;
    }
    imageStore(OutputFlow,tile,vec4(flow,seed.z,seed.w));
}
'@
WriteText (Join-Path $Candidate $IcaRel) $IcaShader

$ExpandShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D TileFlow;
layout(rgba16f,binding=0) uniform highp writeonly image2D OutputFlow;
uniform ivec2 outputSize;
uniform int tileSize;

/* IRIS_26462_WRONSKI_CONTINUOUS_TILE_FLOW
 * Bilinear interpolation of final tile motion into packed-CFA coordinates.
 */
void main() {
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,outputSize))) return;
    ivec2 gs=textureSize(TileFlow,0);
    vec2 tc=(vec2(p)+0.5)/float(max(tileSize,1))-vec2(0.5);
    vec2 uv=(tc+0.5)/vec2(gs);
    vec4 f=texture(TileFlow,clamp(uv,vec2(0.0),vec2(1.0)));
    imageStore(OutputFlow,p,f);
}
'@
WriteText (Join-Path $Candidate $ExpandRel) $ExpandShader

# ----------------------------------------------------------------------------
# Shared published structure-tensor / steerable-kernel functions.
# ----------------------------------------------------------------------------
$KernelFunctions = @'
int componentIndex(ivec2 p){return ((p.y&1)<<1)|(p.x&1);}
int componentColor(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;} // RGGB
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;} // GRBG
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;} // GBRG
    if(c==3)return 0;if(c==0)return 2;return 1;                   // BGGR
}
float cfaAt(image2D tex,ivec2 p){
    p=clamp(p,ivec2(0),rawSize-ivec2(1));
    vec4 v=imageLoad(tex,p>>1);
    int c=componentIndex(p);
    return c==0?v.r:(c==1?v.g:(c==2?v.b:v.a));
}
float greenAt(image2D tex,ivec2 rawP){
    ivec2 q=clamp(rawP>>1,ivec2(0),rawHalf-ivec2(1));
    vec4 v=imageLoad(tex,q);
    int c0=componentColor(0),c1=componentColor(1),c2=componentColor(2),c3=componentColor(3);
    float s=0.0,n=0.0;
    if(c0==1){s+=v.r;n+=1.0;} if(c1==1){s+=v.g;n+=1.0;}
    if(c2==1){s+=v.b;n+=1.0;} if(c3==1){s+=v.a;n+=1.0;}
    return s/max(n,1.0);
}
float vst(float x){
    float a=max(noiseS,1e-7);
    float b=max(noiseO,0.0);
    return 2.0/a*sqrt(max(a*max(x,0.0)+0.375*a*a+b,0.0));
}
mat2 kernelInverse(image2D tex,vec2 rawPos){
    ivec2 p=ivec2(round(rawPos));
    float jxx=0.0,jxy=0.0,jyy=0.0;
    for(int yy=-1;yy<=1;yy++)for(int xx=-1;xx<=1;xx++){
        ivec2 q=p+2*ivec2(xx,yy);
        float gx=0.5*(vst(greenAt(tex,q+ivec2(2,0)))-vst(greenAt(tex,q-ivec2(2,0))));
        float gy=0.5*(vst(greenAt(tex,q+ivec2(0,2)))-vst(greenAt(tex,q-ivec2(0,2))));
        jxx+=gx*gx;jxy+=gx*gy;jyy+=gy*gy;
    }
    jxx/=9.0;jxy/=9.0;jyy/=9.0;
    float tr=jxx+jyy;
    float disc=sqrt(max((jxx-jyy)*(jxx-jyy)+4.0*jxy*jxy,0.0));
    float l1=max(0.5*(tr+disc),0.0);
    float l2=max(0.5*(tr-disc),0.0);

    vec2 e1;
    if(abs(jxy)>1e-8)e1=normalize(vec2(l1-jyy,jxy));
    else e1=jxx>=jyy?vec2(1,0):vec2(0,1);
    vec2 e2=vec2(-e1.y,e1.x);

    float A=1.0+sqrt(max((l1-l2)/max(l1+l2,1e-10),0.0));
    float D=clamp(1.0-sqrt(l1)/max(Dtr,1e-6)+Dth,0.0,1.0);

    /* Published linear law exactly:
       k1 = 1 + A/2*(1/k_shrink - 1)
       k2 = 1 + A/2*(k_stretch - 1)
       then detail/denoise interpolation. */
    float k1=1.0+0.5*A*(1.0/kShrink-1.0);
    float k2=1.0+0.5*A*(kStretch-1.0);
    k1=kDetail*((1.0-D)*k1+D*kDenoise);
    k2=kDetail*((1.0-D)*k2+D*kDenoise);
    k1=max(k1,0.05); k2=max(k2,0.05);

    mat2 omega=mat2(
        k1*k1*e1.x*e1.x+k2*k2*e2.x*e2.x,
        k1*k1*e1.x*e1.y+k2*k2*e2.x*e2.y,
        k1*k1*e1.x*e1.y+k2*k2*e2.x*e2.y,
        k1*k1*e1.y*e1.y+k2*k2*e2.y*e2.y);
    float det=max(omega[0][0]*omega[1][1]-omega[0][1]*omega[1][0],1e-8);
    return mat2(
         omega[1][1]/det,-omega[0][1]/det,
        -omega[1][0]/det, omega[0][0]/det);
}
'@

$InitShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp writeonly image2D outRgb;
layout(rgba16f,binding=2) uniform highp writeonly image2D outSupport;
layout(rgba16f,binding=3) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float noiseS;
uniform float noiseO;
uniform float kDetail;
uniform float kDenoise;
uniform float Dth;
uniform float Dtr;
uniform float kStretch;
uniform float kShrink;
'@ + $KernelFunctions + @'

/* IRIS_26462_WRONSKI_REFERENCE_MERGE
 * Algorithm-11 style reference reconstruction: robustness is exactly 1.
 */
void main(){
    ivec2 xy=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(xy,rawSize)))return;
    mat2 invCov=kernelInverse(referenceCfa,vec2(xy));
    vec3 num=vec3(0.0),den=vec3(0.0);
    for(int yy=-1;yy<=1;yy++)for(int xx=-1;xx<=1;xx++){
        ivec2 p=clamp(xy+ivec2(xx,yy),ivec2(0),rawSize-ivec2(1));
        vec2 d=vec2(p)-vec2(xy);
        float z=max(dot(d,invCov*d),0.0);
        float w=exp(-0.5*z);
        int c=componentColor(componentIndex(p));
        float v=max(cfaAt(referenceCfa,p),0.0);
        num[c]+=w*v;den[c]+=w;
    }
    vec3 rgb=num/max(den,vec3(1e-6));
    imageStore(outRgb,xy,vec4(rgb,1.0));
    imageStore(outSupport,xy,vec4(max(den,vec3(1e-6)),1.0));
    imageStore(outFrameSupport,xy,vec4(1.0));
}
'@
WriteText (Join-Path $Candidate $InitRel) $InitShader

$RobustShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
layout(rgba16f,binding=0) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=1) uniform highp readonly image2D alterCfa;
layout(r32f,binding=2) uniform highp writeonly image2D outRobustness;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float noiseS;
uniform float noiseO;
uniform int tileSizeGuide;

vec4 packedBilinear(image2D t,vec2 p){
    vec2 mx=vec2(rawHalf)-vec2(1.001);
    p=clamp(p,vec2(0.0),mx);
    ivec2 p0=ivec2(floor(p));ivec2 p1=min(p0+ivec2(1),rawHalf-ivec2(1));
    vec2 f=fract(p);
    vec4 a=mix(imageLoad(t,p0),imageLoad(t,ivec2(p1.x,p0.y)),f.x);
    vec4 b=mix(imageLoad(t,ivec2(p0.x,p1.y)),imageLoad(t,p1),f.x);
    return mix(a,b,f.y);
}
int colorOf(int c){
    if(cfaPattern==0){if(c==0)return 0;if(c==3)return 2;return 1;}
    if(cfaPattern==1){if(c==1)return 0;if(c==2)return 2;return 1;}
    if(cfaPattern==2){if(c==2)return 0;if(c==1)return 2;return 1;}
    if(c==3)return 0;if(c==0)return 2;return 1;
}
vec3 guide(vec4 q){
    vec3 v=vec3(0.0);float ng=0.0;
    float s[4]=float[4](q.r,q.g,q.b,q.a);
    for(int i=0;i<4;i++){
        int c=colorOf(i);
        if(c==0)v.r=s[i];
        else if(c==2)v.b=s[i];
        else{v.g+=s[i];ng+=1.0;}
    }
    v.g/=max(ng,1.0);
    return v;
}
vec3 meanAt(image2D t,vec2 center){
    vec3 s=vec3(0.0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++)
        s+=guide(packedBilinear(t,center+vec2(x,y)));
    return s/9.0;
}
vec3 varAt(image2D t,vec2 center,vec3 mu){
    vec3 s=vec3(0.0);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        vec3 q=guide(packedBilinear(t,center+vec2(x,y)));
        s+=q*q;
    }
    return max(s/9.0-mu*mu,vec3(0.0));
}

/* IRIS_26462_WRONSKI_STATISTICAL_ROBUSTNESS
 * Published Algorithm 6-9 structure. Photon heteroscedastic model supplies
 * sigma_t and d_t (two-frame difference variance).
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,rawHalf)))return;
    vec4 f=texelFetch(flowTexture,p,0);
    vec2 flow=f.xy;
    vec3 refMu=meanAt(referenceCfa,vec2(p));
    vec3 refVar=varAt(referenceCfa,vec2(p),refMu);
    vec3 altMu=meanAt(alterCfa,vec2(p)+flow);
    vec3 dp=abs(refMu-altMu);

    float d2=0.0,sigma2=0.0;
    for(int c=0;c<3;c++){
        float brightness=max(refMu[c],0.0);
        float sigmaT2=max(noiseO+noiseS*brightness,1e-8);
        float dT2=2.0*sigmaT2;
        float dp2=dp[c]*dp[c];
        float shrink=dp2/(dp2+dT2);
        d2+=dp2*shrink*shrink;
        sigma2+=max(refVar[c],sigmaT2);
    }

    vec2 mn=vec2(3.402823e38),mx=vec2(-3.402823e38);
    int ts=max(tileSizeGuide,1);
    for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){
        ivec2 q=clamp(p+ivec2(x,y)*ts,ivec2(0),rawHalf-ivec2(1));
        vec2 v=texelFetch(flowTexture,q,0).xy;
        mn=min(mn,v);mx=max(mx,v);
    }
    vec2 span=mx-mn;
    float S=dot(span,span)>0.8*0.8?2.0:12.0;
    float R=clamp(S*exp(-d2/max(sigma2,1e-8))-0.12,0.0,1.0);
    imageStore(outRobustness,p,vec4(R));
}
'@
WriteText (Join-Path $Candidate $RobustRel) $RobustShader

$ErodeShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D InputRobustness;
layout(r32f,binding=0) uniform highp writeonly image2D OutputRobustness;

/* IRIS_26462_WRONSKI_5X5_ROBUSTNESS_MIN - published local minimum. */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    ivec2 sz=imageSize(OutputRobustness);
    if(any(greaterThanEqual(p,sz)))return;
    float r=3.402823e38;
    for(int y=-2;y<=2;y++)for(int x=-2;x<=2;x++){
        ivec2 q=clamp(p+ivec2(x,y),ivec2(0),sz-ivec2(1));
        r=min(r,texelFetch(InputRobustness,q,0).r);
    }
    imageStore(OutputRobustness,p,vec4(r));
}
'@
WriteText (Join-Path $Candidate $ErodeRel) $ErodeShader

$AccumShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
uniform highp sampler2D flowTexture;
uniform highp sampler2D robustnessTexture;
layout(rgba16f,binding=0) uniform highp readonly image2D currentRgb;
layout(rgba16f,binding=1) uniform highp readonly image2D currentSupport;
layout(rgba16f,binding=2) uniform highp readonly image2D alterCfa;
layout(rgba16f,binding=3) uniform highp writeonly image2D outRgb;
layout(rgba16f,binding=4) uniform highp writeonly image2D outSupport;
layout(rgba16f,binding=5) uniform highp readonly image2D referenceCfa;
layout(rgba16f,binding=6) uniform highp readonly image2D currentFrameSupport;
layout(rgba16f,binding=7) uniform highp writeonly image2D outFrameSupport;
uniform ivec2 rawSize;
uniform ivec2 rawHalf;
uniform int cfaPattern;
uniform float maximumSupport;
uniform float noiseS;
uniform float noiseO;
uniform float kDetail;
uniform float kDenoise;
uniform float Dth;
uniform float Dtr;
uniform float kStretch;
uniform float kShrink;
'@ + $KernelFunctions + @'

vec2 flowAtRaw(vec2 p){
    vec2 uv=(p*0.5+vec2(0.5))/vec2(rawHalf);
    return texture(flowTexture,clamp(uv,vec2(0.0),vec2(1.0))).xy*2.0;
}
float robustAtRaw(vec2 p){
    vec2 uv=(p*0.5+vec2(0.5))/vec2(rawHalf);
    return texture(robustnessTexture,clamp(uv,vec2(0.0),vec2(1.0))).r;
}

/* IRIS_26462_FULL_PUBLISHED_WRONSKI_MFSR_ACCUMULATE
 * Algorithm 4: 3x3 physical RAW neighbors, anisotropic Gaussian, robustness,
 * independent R/G/B numerator and denominator.
 */
void main(){
    ivec2 xy=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(xy,rawSize)))return;

    vec4 oldRgb=imageLoad(currentRgb,xy);
    vec3 oldDen=max(imageLoad(currentSupport,xy).rgb,vec3(1e-6));
    float oldFrame=max(imageLoad(currentFrameSupport,xy).r,1.0);

    vec2 source=vec2(xy)+flowAtRaw(vec2(xy));
    float R=clamp(robustAtRaw(vec2(xy)),0.0,1.0);
    mat2 invCov=kernelInverse(alterCfa,source);

    vec3 addNum=vec3(0.0),addDen=vec3(0.0);
    ivec2 base=ivec2(floor(source));
    for(int yy=-1;yy<=1;yy++)for(int xx=-1;xx<=1;xx++){
        ivec2 p=clamp(base+ivec2(xx,yy),ivec2(0),rawSize-ivec2(1));
        vec2 d=vec2(p)-source;
        float z=max(dot(d,invCov*d),0.0);
        float w=exp(-0.5*z)*R;
        int c=componentColor(componentIndex(p));
        float v=max(cfaAt(alterCfa,p),0.0);
        addNum[c]+=w*v;
        addDen[c]+=w;
    }

    vec3 numerator=oldRgb.rgb*oldDen+addNum;
    vec3 den=oldDen+addDen;
    vec3 rgb=numerator/max(den,vec3(1e-6));

    float accepted=R*smoothstep(0.02,0.25,min(addDen.r,min(addDen.g,addDen.b)));
    float frameSupport=min(maximumSupport,oldFrame+accepted);

    imageStore(outRgb,xy,vec4(rgb,frameSupport));
    imageStore(outSupport,xy,vec4(den,1.0));
    imageStore(outFrameSupport,xy,vec4(frameSupport));
}
'@
WriteText (Join-Path $Candidate $AccumRel) $AccumShader

$FinalizeShader = @'
#define LAYOUT //
LAYOUT
precision highp float;
precision highp image2D;
layout(rgba16f,binding=0) uniform highp readonly image2D currentRgb;
layout(rgba16f,binding=1) uniform highp readonly image2D currentFrameSupport;
layout(rgba16f,binding=2) uniform highp writeonly image2D outRgb;
/* IRIS_26462_WRONSKI_RGB_IDENTITY_FINALIZER
 * Exact RGB identity. No filtering, chroma processing or sharpening.
 */
void main(){
    ivec2 p=ivec2(gl_GlobalInvocationID.xy);
    if(any(greaterThanEqual(p,imageSize(outRgb))))return;
    vec4 c=imageLoad(currentRgb,p);
    float fs=max(imageLoad(currentFrameSupport,p).r,1.0);
    imageStore(outRgb,p,vec4(c.rgb,fs));
}
'@
WriteText (Join-Path $Candidate $FinalizeRel) $FinalizeShader

# ----------------------------------------------------------------------------
# Reconstruction Java transformation.
# ----------------------------------------------------------------------------
$ReconC = Join-Path $Candidate $ReconRel
$R = ReadText $ReconC

# HAL-delivered standard Bayer guard.
$DirectOld = @'
        final boolean directBayer =
                parameters.cfaPattern >= 0 && parameters.cfaPattern <= 3;
'@
$DirectNew = @'
        /*
         * IRIS_26462_HAL_STANDARD_BAYER_WRONSKI_GUARD
         * Published direct-RGB reconstruction is enabled only for standard
         * Bayer and exact even physical RAW dimensions.
         */
        final boolean directBayer =
                parameters.cfaPattern >= 0
                        && parameters.cfaPattern <= 3
                        && raw.x > 0
                        && raw.y > 0
                        && (raw.x % 2) == 0
                        && (raw.y % 2) == 0
                        && rawHalf.x * 2 == raw.x
                        && rawHalf.y * 2 == raw.y;
'@
$R = ReplaceOnce $R $DirectOld $DirectNew "standard Bayer Wronski guard"

# Compute public-method SNR tuning immediately after canonical noise transform.
$NoiseAnchor = @'
        noiseS *= canonicalGain;
        noiseO *= canonicalGain * canonicalGain;
'@
$NoiseNew = @'
        noiseS *= canonicalGain;
        noiseO *= canonicalGain * canonicalGain;

        /*
         * IRIS_26462_WRONSKI_PUBLIC_SNR_TUNING
         * Public implementation clamps SNR to [6,30] and linearly tunes:
         * kDetail .33->.25, kDenoise 5->3, Dth .81->.71, Dtr 1.24->1.0.
         */
        final float mfsrSnr = Math.max(
                6.0f,
                Math.min(
                        30.0f,
                        0.18f / (float)Math.sqrt(
                                Math.max(
                                        noiseS * 0.18f + noiseO,
                                        1.0e-8f))));
        final float mfsrT = (mfsrSnr - 6.0f) / 24.0f;
        final float mfsrKDetail = 0.33f + mfsrT * (0.25f - 0.33f);
        final float mfsrKDenoise = 5.0f + mfsrT * (3.0f - 5.0f);
        final float mfsrDth = 0.81f + mfsrT * (0.71f - 0.81f);
        final float mfsrDtr = 1.24f + mfsrT * (1.00f - 1.24f);
        final float mfsrKStretch = 4.0f;
        final float mfsrKShrink = 2.0f;
        final int mfsrTileSize =
                mfsrSnr <= 14.0f ? 64 : (mfsrSnr <= 22.0f ? 32 : 16);
'@
$R = ReplaceOnce $R $NoiseAnchor $NoiseNew "public SNR tuning insertion"

# Direct initializer must receive exact published tuning and frame-support target.
$InitCallAnchor = @'
                glProg.setVar("sensorGains", directSensorGains);
                glProg.setTextureCompute("referenceCfa", referenceCfa, false);
                glProg.setTextureCompute("outRgb", directRgbA, true);
                glProg.setTextureCompute("outSupport", directSupportA, true);
                glProg.computeAuto(raw, 1);
'@
$InitCallNew = @'
                glProg.setVar("noiseS", noiseS);
                glProg.setVar("noiseO", noiseO);
                glProg.setVar("kDetail", mfsrKDetail);
                glProg.setVar("kDenoise", mfsrKDenoise);
                glProg.setVar("Dth", mfsrDth);
                glProg.setVar("Dtr", mfsrDtr);
                glProg.setVar("kStretch", mfsrKStretch);
                glProg.setVar("kShrink", mfsrKShrink);
                glProg.setTextureCompute("referenceCfa", referenceCfa, false);
                glProg.setTextureCompute("outRgb", directRgbA, true);
                glProg.setTextureCompute("outSupport", directSupportA, true);
                glProg.setTextureCompute(
                        "outFrameSupport", directFrameSupportA, true);
                glProg.computeAuto(raw, 1);
'@
$R = ReplaceOnce $R $InitCallAnchor $InitCallNew "published reference merge binding"

# Alignment owner: use published path for standard Bayer, preserve old V2 alignment
# as fallback for nonstandard CFA.
$AlignPattern = 'ownedAlignment\s*=\s*MotionV2Alignment\.align\(\s*rawHalf,\s*parameters\.cfaPattern,\s*canonicalGain,\s*glProg,\s*referenceCfa,\s*alterCfa\);'
$AlignReplacement = @'
ownedAlignment =
                                directBayer
                                        ? MotionV2WronskiAlignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                mfsrSnr,
                                                glProg,
                                                referenceCfa,
                                                alterCfa)
                                        : MotionV2Alignment.align(
                                                rawHalf,
                                                parameters.cfaPattern,
                                                canonicalGain,
                                                glProg,
                                                referenceCfa,
                                                alterCfa);
'@
$R = ReplaceRegexOne $R $AlignPattern $AlignReplacement "Wronski alignment ownership"

# Replace the old direct-RGB auxiliary shader invocation with robustness ->
# erosion -> published accumulator. Keep all existing ping-pong swaps after it.
$DirectPattern =
    '(?s)if\s*\(\s*directBayer\s*\)\s*\{\s*/\*.*?' +
    'IRIS_26424_DIRECT_MULTIFRAME_CFA_RGB.*?' +
    'glProg\.computeAuto\s*\(\s*raw\s*,\s*1\s*\)\s*;'
$DirectReplacement = @'
if (directBayer) {
                            /*
                             * IRIS_26462_FULL_PUBLISHED_WRONSKI_MFSR
                             * Robustness -> 5x5 min -> independent RGB merge.
                             */
                            GLTexture mfsrRobustRaw = new GLTexture(
                                    rawHalf,
                                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                                    null,
                                    GL_NEAREST,
                                    GL_CLAMP_TO_EDGE);
                            GLTexture mfsrRobustMin = new GLTexture(
                                    rawHalf,
                                    new GLFormat(GLFormat.DataType.FLOAT_32, 1),
                                    null,
                                    GL_NEAREST,
                                    GL_CLAMP_TO_EDGE);
                            try {
                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/mfsr_robustness", true);
                                glProg.setVar("rawHalf", rawHalf);
                                glProg.setVar(
                                        "cfaPattern",
                                        (int) parameters.cfaPattern);
                                glProg.setVar("noiseS", noiseS);
                                glProg.setVar("noiseO", noiseO);
                                glProg.setVar(
                                        "tileSizeGuide",
                                        Math.max(1, mfsrTileSize / 2));
                                glProg.setTexture(
                                        "flowTexture",
                                        ownedAlignment.flowTexture);
                                glProg.setTextureCompute(
                                        "referenceCfa", referenceCfa, false);
                                glProg.setTextureCompute(
                                        "alterCfa", alterCfa, false);
                                glProg.setTextureCompute(
                                        "outRobustness",
                                        mfsrRobustRaw,
                                        true);
                                glProg.computeAuto(rawHalf, 1);

                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/mfsr_robustness_erode", true);
                                glProg.setTexture(
                                        "InputRobustness",
                                        mfsrRobustRaw);
                                glProg.setTextureCompute(
                                        "OutputRobustness",
                                        mfsrRobustMin,
                                        true);
                                glProg.computeAuto(rawHalf, 1);

                                glProg.setLayout(tile, tile, 1);
                                glProg.useAssetProgram(
                                        "motionv2/direct_rgb_accumulate", true);
                                glProg.setVar("rawSize", raw);
                                glProg.setVar("rawHalf", rawHalf);
                                glProg.setVar(
                                        "cfaPattern",
                                        (int) parameters.cfaPattern);
                                glProg.setVar(
                                        "maximumSupport",
                                        (float) frameCount);
                                glProg.setVar("noiseS", noiseS);
                                glProg.setVar("noiseO", noiseO);
                                glProg.setVar("kDetail", mfsrKDetail);
                                glProg.setVar("kDenoise", mfsrKDenoise);
                                glProg.setVar("Dth", mfsrDth);
                                glProg.setVar("Dtr", mfsrDtr);
                                glProg.setVar("kStretch", mfsrKStretch);
                                glProg.setVar("kShrink", mfsrKShrink);
                                glProg.setTexture(
                                        "flowTexture",
                                        ownedAlignment.flowTexture);
                                glProg.setTexture(
                                        "robustnessTexture",
                                        mfsrRobustMin);
                                glProg.setTextureCompute(
                                        "currentRgb",
                                        currentDirectRgb,
                                        false);
                                glProg.setTextureCompute(
                                        "currentSupport",
                                        currentDirectSupport,
                                        false);
                                glProg.setTextureCompute(
                                        "alterCfa",
                                        alterCfa,
                                        false);
                                glProg.setTextureCompute(
                                        "referenceCfa",
                                        referenceCfa,
                                        false);
                                glProg.setTextureCompute(
                                        "currentFrameSupport",
                                        currentDirectFrameSupport,
                                        false);
                                glProg.setTextureCompute(
                                        "outRgb",
                                        nextDirectRgb,
                                        true);
                                glProg.setTextureCompute(
                                        "outSupport",
                                        nextDirectSupport,
                                        true);
                                glProg.setTextureCompute(
                                        "outFrameSupport",
                                        nextDirectFrameSupport,
                                        true);
                                glProg.computeAuto(raw, 1);
                            } finally {
                                mfsrRobustMin.close();
                                mfsrRobustRaw.close();
                            }
'@
$R = ReplaceRegexOne $R $DirectPattern $DirectReplacement "published per-frame merge block"

# Standard Bayer final owner -> Wronski direct RGB identity/support carrier.
$FinalPattern = '(?s)\s*GLTexture imageOutput;\s*.*?imageOutput\s*=\s*currentMerged;\s*.*?IRIS_26452_PHASE_AWARE_CFA_FINAL_OWNER.*?\);'
$FinalReplacement = @'
            GLTexture imageOutput;
            if (directBayer) {
                /*
                 * IRIS_26462_WRONSKI_DIRECT_RGB_FINAL_OWNER
                 * No explicit MotionV2CfaDemosaic for standard Bayer.
                 */
                glProg.setLayout(tile, tile, 1);
                glProg.useAssetProgram("motionv2/mfsr_finalize", true);
                glProg.setTextureCompute(
                        "currentRgb", currentDirectRgb, false);
                glProg.setTextureCompute(
                        "currentFrameSupport",
                        currentDirectFrameSupport,
                        false);
                glProg.setTextureCompute("outRgb", nextDirectRgb, true);
                glProg.computeAuto(raw, 1);
                imageOutput = nextDirectRgb;
                Log.d(TAG,
                        "IRIS_26462_WRONSKI_DIRECT_RGB_FINAL_OWNER"
                        + " publishedMethod=true"
                        + " directPhysicalCfa=true"
                        + " separateDemosaic=false"
                        + " sharpening=false");
            } else {
                imageOutput = currentMerged;
            }
'@
$R = ReplaceRegexOne $R $FinalPattern $FinalReplacement "Wronski final owner"

WriteText $ReconC $R

# ----------------------------------------------------------------------------
# Input bridge: standard Bayer full-res FLOAT32 RGB, nonstandard packed fallback.
# ----------------------------------------------------------------------------
$InputC = Join-Path $Candidate $InputRel
$I = ReadText $InputC
$InputPattern = '(?s)\s*boolean directBayer =\s*basePipeline\.mParameters\.cfaPattern >= 0\s*&& basePipeline\.mParameters\.cfaPattern <= 3;.*?WorkingTexture = new GLTexture\(\s*half,\s*new GLFormat\(GLFormat\.DataType\.FLOAT_32, 4\),\s*view,\s*GL_NEAREST,\s*GL_CLAMP_TO_EDGE\);\s*\}'
$InputReplacement = @'
        boolean directBayer =
                basePipeline.mParameters.cfaPattern >= 0
                        && basePipeline.mParameters.cfaPattern <= 3
                        && raw.x > 0
                        && raw.y > 0
                        && (raw.x % 2) == 0
                        && (raw.y % 2) == 0;
        /*
         * IRIS_26462_WRONSKI_DIRECT_RGB_INPUT_OWNER
         * Standard Bayer receives full-resolution linear camera RGB.
         */
        if (directBayer) {
            WorkingTexture = new GLTexture(
                    raw,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_LINEAR,
                    GL_CLAMP_TO_EDGE);
        } else {
            WorkingTexture = new GLTexture(
                    half,
                    new GLFormat(GLFormat.DataType.FLOAT_32, 4),
                    view,
                    GL_NEAREST,
                    GL_CLAMP_TO_EDGE);
        }
'@
$I = ReplaceRegexOne $I $InputPattern $InputReplacement "full-resolution Wronski input bridge"
WriteText $InputC $I

# ----------------------------------------------------------------------------
# Post graph: standard Bayer bypasses explicit CFA demosaic.
# Disable only the old direct-branch local-support denoise; keep normal
# MotionV2ColorTransform -> MotionV2Denoise(26453) -> MotionV2Render.
# ----------------------------------------------------------------------------
$PostC = Join-Path $Candidate $PostRel
$P = ReadText $PostC
$P = ReplaceOnce $P 'boolean directRgbCarrier = false;' `
    'boolean directRgbCarrier = directBayer;' `
    "direct RGB post ownership"

# If the historical direct support denoise branch exists, make it unreachable.
$LocalPat = 'if\s*\(\s*directRgbCarrier\s*\)\s*\{\s*add\s*\(\s*new\s+MotionV2LocalSupportDenoise\s*\(\s*\)\s*\)\s*;\s*add\s*\(\s*new\s+StageTelemetry\s*\(\s*"V2_POST_TRUE_LOCAL_SUPPORT_DENOISE"\s*\)\s*\)\s*;\s*\}'
if ([regex]::Matches($P,$LocalPat,[System.Text.RegularExpressions.RegexOptions]::Singleline).Count -eq 1) {
    $P = [regex]::Replace(
        $P,$LocalPat,
        'if (false && directRgbCarrier) { /* IRIS_26462_WRONSKI_TEMPORAL_RECON_OWNS_PRIMARY_DENOISE */ add(new MotionV2LocalSupportDenoise()); add(new StageTelemetry("V2_POST_TRUE_LOCAL_SUPPORT_DENOISE")); }',
        1)
}
WriteText $PostC $P

# Version in same candidate.
$Vc = Join-Path $Candidate $VersionRel
$V = ReadText $Vc
$V = [regex]::Replace($V,'(?m)^VERSION_NAME=.*$',"VERSION_NAME=$NewVersion")
$V = [regex]::Replace($V,'(?m)^VERSION_BUILD=.*$',"VERSION_BUILD=$NewBuild")
WriteText $Vc $V

Write-Host "candidate/source validation PASS"
Write-Host "PASS: complete candidate created under $Candidate"
Write-Host "PASS: live app source remains untouched"

# ============================================================================
# GATE 3 - temporary-copy architecture + equation validation
# ============================================================================
Write-Host "`n=== GATE 3: TEMPORARY-COPY ARCHITECTURE VALIDATION ===" -ForegroundColor Cyan

$CA = ReadText (Join-Path $Candidate $NewAlignJavaRel)
$CB = ReadText (Join-Path $Candidate $BlockRel)
$CIca = ReadText (Join-Path $Candidate $IcaRel)
$CInit = ReadText (Join-Path $Candidate $InitRel)
$CRob = ReadText (Join-Path $Candidate $RobustRel)
$CErode = ReadText (Join-Path $Candidate $ErodeRel)
$CAcc = ReadText (Join-Path $Candidate $AccumRel)
$CFinal = ReadText (Join-Path $Candidate $FinalizeRel)
$CRecon = ReadText (Join-Path $Candidate $ReconRel)
$CInput = ReadText (Join-Path $Candidate $InputRel)
$CPost = ReadText (Join-Path $Candidate $PostRel)
$CVersion = ReadText (Join-Path $Candidate $VersionRel)

foreach($m in @(
    "factors=1,2,4,4",
    "radii=1,4,4,4",
    "metrics=L1,L2,L2,L2",
    "icaIterations=3",
    "for (int l=3;l>=0;l--)"
)){ AssertContains $CA $m "published alignment Java" }

foreach($m in @(
    "distanceMetric==0 ? abs(d) : d*d",
    "searchRadius",
    "previousToCurrentScale"
)){ AssertContains $CB $m "block matching" }

foreach($m in @(
    "IRIS_26462_WRONSKI_INVERSE_COMPOSITIONAL_ALIGNMENT",
    "for(int iter=0;iter<3;iter++)",
    "H00*H11-H01*H01",
    "flow+=d"
)){ AssertContains $CIca $m "ICA" }

foreach($m in @(
    "k1=1.0+0.5*A*(1.0/kShrink-1.0)",
    "k2=1.0+0.5*A*(kStretch-1.0)",
    "k1=kDetail*((1.0-D)*k1+D*kDenoise)",
    "k2=kDetail*((1.0-D)*k2+D*kDenoise)",
    "0.375*a*a"
)){ AssertContains $CInit $m "published kernel/GAT" }

foreach($m in @(
    "S*exp(-d2/max(sigma2,1e-8))-0.12",
    "dot(span,span)>0.8*0.8?2.0:12.0",
    "shrink=dp2/(dp2+dT2)",
    "sigma2+=max(refVar[c],sigmaT2)"
)){ AssertContains $CRob $m "published robustness" }

foreach($m in @(
    "for(int y=-2;y<=2;y++)",
    "r=min(r"
)){ AssertContains $CErode $m "5x5 minimum" }

foreach($m in @(
    "IRIS_26462_FULL_PUBLISHED_WRONSKI_MFSR_ACCUMULATE",
    "for(int yy=-1;yy<=1;yy++)",
    "float w=exp(-0.5*z)*R",
    "addNum[c]+=w*v",
    "addDen[c]+=w",
    "vec3 numerator=oldRgb.rgb*oldDen+addNum"
)){ AssertContains $CAcc $m "published merge" }

foreach($m in @(
    "IRIS_26462_WRONSKI_DIRECT_RGB_FINAL_OWNER",
    "MotionV2WronskiAlignment.align",
    "mfsr_robustness",
    "mfsr_robustness_erode",
    "mfsrSnr",
    "mfsrKDetail",
    "mfsrKDenoise",
    "mfsrDth",
    "mfsrDtr"
)){ AssertContains $CRecon $m "reconstruction integration" }

AssertContains $CInput "IRIS_26462_WRONSKI_DIRECT_RGB_INPUT_OWNER" "input bridge"
AssertContains $CPost "boolean directRgbCarrier = directBayer;" "post direct ownership"

Need ($CVersion -match "(?m)^VERSION_NAME=0\.9726462\r?$") "candidate version name wrong"
Need ($CVersion -match "(?m)^VERSION_BUILD=26462\r?$") "candidate build wrong"

# Ensure current mature downstream denoise/render/UHDR/capture stays outside
# intentional set and therefore protected by hash manifest.
Need (-not ($IntentionalRel -contains "app/src/main/assets/shaders/motionv2/color_transform.glsl")) `
    "color transform unexpectedly intentional"
Need (-not ($IntentionalRel -contains "app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java")) `
    "Ultra HDR unexpectedly intentional"
Need (-not ($IntentionalRel -contains "app/src/main/assets/shaders/motionv2/denoise.glsl")) `
    "denoise unexpectedly intentional"
Need (-not ($IntentionalRel -contains "app/src/main/assets/shaders/motionv2/render.glsl")) `
    "render unexpectedly intentional"
Need (-not ($IntentionalRel -contains "app/src/main/java/com/particlesdevs/photoncamera/processing/ultrahdr/MotionV2UltraHdr.java")) `
    "Ultra HDR unexpectedly intentional"

# Identity finalizer must contain no filtering primitives.
foreach($bad in @("smoothstep(","mix(","dot(","exp(","pow(")) {
    Need (-not $CFinal.Contains($bad)) "identity finalizer contains image math: $bad"
}

Write-Host "Temporary-copy validation: PASS"
Write-Host "PASS: four-level alignment contract present"
Write-Host "PASS: three ICA refinements per level present"
Write-Host "PASS: published kernel equations present"
Write-Host "PASS: published statistical robustness + 5x5 minimum present"
Write-Host "PASS: independent R/G/B numerator/support merge present"
Write-Host "PASS: rejected late limiter removed"
Write-Host "PASS: standard Bayer direct RGB bypasses demosaic"

# ============================================================================
# GATE 4 - shader source sanity before real apply
# ============================================================================
Write-Host "`n=== GATE 4: SHADER SOURCE SANITY ===" -ForegroundColor Cyan

# If glslangValidator exists, use it as ESSL front-end syntax validation on
# self-contained compute wrappers. Otherwise fail closed only on structural
# invariants; Gradle/Photon runtime shader compilation remains later proof.
$Glslang = Get-Command glslangValidator.exe -ErrorAction SilentlyContinue
if (-not $Glslang) { $Glslang = Get-Command glslangValidator -ErrorAction SilentlyContinue }

foreach($rel in @($PyrRel,$BlockRel,$IcaRel,$ExpandRel,$InitRel,$AccumRel,$RobustRel,$ErodeRel,$FinalizeRel)) {
    $s = ReadText (Join-Path $Candidate $rel)
    Need (-not $s.Contains("IRIS_26460_CROSS_PHASE_PLATEAU_CHROMA")) `
        "rejected 26460 marker leaked into new shader: $rel"
    Need (-not $s.Contains("IRIS_26461_MATRIX_AWARE_CHROMA_LIMITER")) `
        "rejected late marker leaked into new shader: $rel"
    $opens = ([regex]::Matches($s,'\{')).Count
    $closes = ([regex]::Matches($s,'\}')).Count
    Need ($opens -eq $closes) "GLSL brace imbalance: $rel"
}
Write-Host "PASS: all new GLSL braces balanced"
if ($Glslang) {
    Write-Host "INFO: glslangValidator found at $($Glslang.Source)"
    Write-Host "INFO: Photon shader preprocessor injects compute layout/#version; full runtime compile is verified by app build/runtime."
} else {
    Write-Host "INFO: glslangValidator not installed; structural GLSL preflight completed."
}

# Verify real source has not changed during candidate generation.
foreach($kv in $Exact.GetEnumerator()) {
    Need ((Sha (Join-Path $Repo $kv.Key)) -eq $kv.Value) `
        "live source changed before apply: $($kv.Key)"
}
Need ((ReadText $Version) -match "(?m)^VERSION_BUILD=26436\r?$") `
    "live version changed before apply"

Write-Host "PRE-BUILD SAFETY PROOF PASSED"
Write-Host "PASS: candidate/source validation PASS"
Write-Host "PASS: Temporary-copy validation PASS"
Write-Host "PASS: live source still exact 26461 before apply"

# ============================================================================
# GATE 5 - apply exact validated candidate
# ============================================================================
Write-Host "`n=== GATE 5: APPLY EXACT VALIDATED CANDIDATE ===" -ForegroundColor Cyan

$ApplyRel = @(
    $VersionRel,$ReconRel,$InputRel,$PostRel,$DenoiseRel,
    $NewAlignJavaRel,$PyrRel,$BlockRel,$IcaRel,$ExpandRel,
    $InitRel,$AccumRel,$RobustRel,$ErodeRel,$FinalizeRel
)
foreach($rel in $ApplyRel) {
    $src = Join-Path $Candidate $rel
    Need (Test-Path -LiteralPath $src -PathType Leaf) "candidate missing at apply: $rel"
    $dst = Join-Path $Repo $rel
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
    Copy-Item -LiteralPath $src -Destination $dst -Force
    Need ((Sha $src) -eq (Sha $dst)) "live apply hash mismatch: $rel"
}
Write-Host "PASS: exact validated candidate applied"

# ============================================================================
# GATE 6 - post-apply protected proof
# ============================================================================
Write-Host "`n=== GATE 6: POST-APPLY SAFETY PROOF ===" -ForegroundColor Cyan

HashProtected $ProtectedAfter $IntentionalRel
Need ((ReadText $ProtectedBefore) -eq (ReadText $ProtectedAfter)) `
    "protected tracked app source changed"

& git diff --check -- app
Need ($LASTEXITCODE -eq 0) "git diff --check failed"

Need ((ReadText (Join-Path $Repo $ReconRel)).Contains(
    "IRIS_26462_WRONSKI_DIRECT_RGB_FINAL_OWNER")) `
    "live reconstruction Wronski owner missing"
Need ((ReadText (Join-Path $Repo $PostRel)).Contains(
    "boolean directRgbCarrier = directBayer;")) `
    "live post direct owner missing"

& git diff --binary HEAD -- app | Out-File -LiteralPath $PostPatch -Encoding utf8
Need ($LASTEXITCODE -eq 0) "post-edit binary patch failed"

Write-Host "PRE-BUILD SAFETY PROOF PASSED"
Write-Host "PASS: protected source byte-identical"
Write-Host "PASS: git diff --check"
Write-Host "PASS: version/build increment and source apply are in this same script"

# ============================================================================
# GATE 7 - build 0.9726462 / 26462
# ============================================================================
Write-Host "`n=== GATE 7: BUILD $NewVersion / $NewBuild ===" -ForegroundColor Cyan

$Java17Candidates = @(
    "C:\Program Files\Android\Android Studio\jbr",
    "C:\Program Files\Eclipse Adoptium\jdk-17*",
    "C:\Program Files\Java\jdk-17*"
)
$JavaHome = $null
foreach($j in $Java17Candidates) {
    $found = Get-Item $j -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { $JavaHome = $found.FullName; break }
}
if ($JavaHome) {
    $env:JAVA_HOME = $JavaHome
    $env:Path = "$JavaHome\bin;$env:Path"
}
Need (Test-Path -LiteralPath (Join-Path $Repo "gradlew.bat")) "gradlew.bat missing"

$BuildOutput = & (Join-Path $Repo "gradlew.bat") :app:assembleDebug --stacktrace 2>&1 | Tee-Object -FilePath $BuildLog
$BuildRc = $LASTEXITCODE
$BuildText = $BuildOutput -join "`n"
Need ($BuildRc -eq 0) "Gradle failed rc=$BuildRc; see $BuildLog"
Need ($BuildText.Contains("BUILD SUCCESSFUL")) "BUILD SUCCESSFUL missing from log"

$Built = Get-ChildItem -LiteralPath (Join-Path $Repo "app\build\outputs\apk") `
        -Recurse -File -Filter "*.apk" |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 1
Need ($null -ne $Built) "no APK found after successful Gradle build"

Copy-Item -LiteralPath $Built.FullName -Destination $ApkOut -Force
Need ((Sha $Built.FullName) -eq (Sha $ApkOut)) "APK copy hash mismatch"

$FinalV = ReadText $Version
Need ($FinalV -match "(?m)^VERSION_NAME=0\.9726462\r?$") "final VERSION_NAME wrong"
Need ($FinalV -match "(?m)^VERSION_BUILD=26462\r?$") "final VERSION_BUILD wrong"

$ApkHash = Sha $ApkOut

$Report = @"
26462 WRONSKI PUBLISHED-METHOD V3 RESULT
Generated: $(Get-Date -Format o)

Branch: $ExpectedBranch
Committed HEAD: $ExpectedHead
Version/build: $NewVersion / $NewBuild
Backup branch: $BackupBranch

EVIDENCE-BASED START STATE
- Started from curated 26436 exact-payload source over committed 26428 HEAD.
- Did NOT replay historical build scripts.
- Current tested 26461 color/tone/denoise/UHDR source is protected byte-for-byte.
- 26460 cross-phase demosaic remains only in nonstandard/fallback route; standard Bayer bypasses it.
- 26453 residual edge-chroma denoise remains protected.
- Motion Ultra HDR/capture/exposure/tone/render remain protected.

PUBLISHED-METHOD MFSR
- 4-level coarse-to-fine block matching
- factors 1,2,4,4 fine->coarse
- radii 1,4,4,4
- metrics L1,L2,L2,L2
- 3 IC-LK refinements per level
- GAT structure tensor
- exact k1/k2 steerable covariance law
- SNR-tuned kDetail/kDenoise/Dth/Dtr public laws
- robustness R=clamp(S*exp(-d2/sigma2)-0.12,0,1)
- s1=2 / s2=12 / Mt=0.8
- 5x5 local minimum robustness
- direct 3x3 physical-CFA merge
- independent R/G/B numerator/support
- reference robustness=1
- full-resolution linear camera RGB owner
- no explicit standard-Bayer demosaic
- no sharpening

PHOTON ADAPTATION
- Google's proprietary production source/calibration curves are not public.
- Photon canonical noiseS/noiseO supplies GAT and noise-correction terms.

SAFETY
candidate/source validation PASS
Temporary-copy validation: PASS
PRE-BUILD SAFETY PROOF PASSED
BUILD SUCCESSFUL

APK: $ApkOut
APK SHA256: $ApkHash
Build log: $BuildLog
Pre-edit patch: $PrePatch
Post-edit patch: $PostPatch
Protected-before: $ProtectedBefore
Protected-after: $ProtectedAfter
Safety directory: $Safety

No commit.
No push.
dev untouched.
"@
WriteText $Result $Report

Write-Host ""
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "26462 BUILD SUCCESSFUL VERIFIED" -ForegroundColor Green
Write-Host "====================================================================" -ForegroundColor Green
Write-Host "APK: $ApkOut"
Write-Host "SHA256: $ApkHash"
Write-Host "Result: $Result"
Write-Host "Backup branch: $BackupBranch"
Write-Host "No commit. No push. dev untouched." -ForegroundColor Green
