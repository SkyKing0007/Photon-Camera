#!/usr/bin/env python3
"""26975 guarded 3-stage successor to actual successful 26974 V3 Actions.

Installs ONLY the full SHA-pinned C-only 26975 candidate atop actual successful
26974 compiled source TAR. Never retrieves source from a mutable dev HEAD.
No commit, push, partial compilation, platform verification bypass or A/B fallback.
"""
import argparse,gzip,hashlib,io,json,os,pathlib,re,shutil,subprocess,sys,tarfile,urllib.request,zipfile
R=pathlib.Path(__file__).resolve().parent
SHADER_COUNT=151 # exact current V14 physical required shader inventory; not skip
TMP=R/'.photon_26975_work';OUT=R/'photon_26975_outputs'
ART=TMP/'26974-success.zip';BASE=TMP/'authority_26974';CAND=TMP/'candidate_26975'
REPO='SkyKing0007/Photon-Camera';BRANCH='experimental-clean-photon-rebuild'
RUN=44936611052;COMMIT='e06263d6f1b5f97ea730a6f34835d5fc2ed0f39f';ART_ID=14720570576
ART_SHA='9eee3a9f00d6c53d675f22c1831d4556c0c9e4ae367769018ef9d58bb625c7e3'
TAR_SHA='5018df1cd830ee7cf371338e953ccf3649b08024708bf4bdb4cfa216d3485a98'
BUILDER_SHA='6b040b5608ed9a453b426dee1b5f33bf5ac3f0fc369505b0b80016bb49eee3c8'
WORKFLOW_SHA='3aba27e38220f8c8995b807ec91b58a82fe68d3e385226b3b3849f3f6f81ef5b'
PRIOR_APK_SHA='25ad6df699e9a232b2f76fbc50777acf376bd13f8a6f07f63909ea3d5c9247e9'
PRIOR_APK_NAME='IrisCamera-0.9726974-26974-iris-rawr-debug.apk'
APKNAME='IrisCamera-0.9726975-26975-iris-rawr-debug.apk'
NBASE=2132;NFILES=2394;NCHANGE=284;NADDED=262;NMODIFIED=22;NDELETED=0;NPROTECTED=2110
NATIVE_SHA={
 'lib/arm64-v8a/liblkrpipeline.so':'037a5f62649dcac7034c789c8e7ea2f250ca818d1c1c364e09a59f6897530105',
 'lib/arm64-v8a/libsrpipeline.so':'f87cc70ad12a69345392a4eb73b6ec33739577ce8c39b7a4916180c344f67069',
 'lib/armeabi-v7a/liblkrpipeline.so':'9297eb7c58ca242986bced32bf773dcc8d16c3beaa33c26142b152c585957b03',
 'lib/armeabi-v7a/libsrpipeline.so':'48788035080e66efa63b693e35f0587d2f02e851b818c367f3915b6154b47d68',
}
DONOR_SHA={
 'lib/arm64-v8a/libiris26972c129.so':'a70ba1b1e4e8c856b07c828bef4141d0097d19013a49f77c1f59e41ee0a52cae',
 'lib/arm64-v8a/libi72.so':'ab0698a4a7006564e22447402468a9e1ca349a9017180bc7767c4feec58e0331',
}
FILES=[
 'README_PHOTON_26975.md','26975_COMMIT_MESSAGE.txt','26975_LOCAL_VERIFICATION.txt',
 '26974_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml','26974_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py',
 'build_26975_incremental.py','compile_26975_shaders.sh','test_26975_gallery_host.py','test_26975_source.py',
 'test_26975_patches.py','test_26975_sealed_negatives.py','test_26975_workflow_refs.py',
 'test_26975_v4_capture_host.py','test_26975_v5_asset_host.py','test_26975_v10_minimal_core.py','26975_V10_MINIMAL_LUT_REACHABILITY_PROOF.json','26975_V5_REMOVED_OPTIONAL_ASSETS.json',
 'verify_26975_v6_current_glsl.py','26975_V6_CURRENT_SHADER_INVENTORY.json','26975_V6_REMOVED_UNREFERENCED_GLASS_SHADERS.json',
 '26975_BASE_26974_FULL_APP.sha256','26975_EXPECTED_FULL_APP.sha256','26975_PROTECTED_SOURCE.sha256',
 '26975_AUTHORITY_AND_SCOPE.json','26975_CHANGED_RUNTIME_ALLOWLIST.txt',
 '26975_MODIFIED_ORIGINAL_PATHS.txt','26975_ADDED_RUNTIME_PATHS.txt',
 '26975_DELETED_RUNTIME_PATHS.txt','26975_FORWARD_FULLINDEX.patch','26975_ROLLBACK_FULLINDEX.patch',
 '26975_STAGE_1_UPLOAD_PATHS.txt','26975_STAGE_2_UPLOAD_PATHS.txt','26975_STAGE_3_UPLOAD_PATHS.txt',
 '26975_EXPECTED_ACTION_EXECUTABLES.txt'
]

# Exact 56 source files physically left by V7 in the *staging directory*, not
# in the separately reconstructed 26974 baseline or the V8 compiled candidate.
# These bytes are hash-pinned to the actual V7 three-stage seal and GitHub's
# failed Actions head 9dff8881b85d98ea186c99800a217135856ed1bf.
# Never delete anything outside this manifest, and never import stale source.
V7_STALE_STAGE_SHA256 = """\
405dab2f1a59e5a0194dddd71e2bab280e512faf0a41d3a6ac84b21b8c5b67d5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/GlesLanczosResampling.kt
655d997149f21fcaa9bbb42d2bee828eff44c361ef8f4a8a3d41b313fc4be589  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcAlignmentInputScale.kt
a4bcb43ac16f94678f64e6435aa0f3298937f0b6d5abd2934f3b74518f7b9cbb  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcSabreAlignmentOffset.kt
5258353b17802a1e0a5951003f12ef0edad1a001995ecfae17c70ce003a8d220  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcSabreKernelTuning.kt
28f2835847dd6acd0efbc5d045bc7ae8c525e18577e4e1e27bdeca6a13871e92  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcSabreMergedNoiseModel.kt
970d0aaacd54c8f908ec31b43ec2ac558ef703c92011d6748166abfd0c1f7617  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcSabreNoiseEstimatesLut.kt
12e338bb5a247f6b0392c7ef571f922e1cc09c1ed896e85faa19a2aa4b4702e2  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcSabreRejectionTuning.kt
7a7d35c6121eabadc5409fb0d7567729942b46da20b0186ba45540c5c6502bb4  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/MgcSabreResolveTuning.kt
82117c7c206887272bcd3d5c1c8557412dfa95b0a24966fafdb5b98fdb550256  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/PhotonSharpenTuning.kt
89d6f74779f480b4b2c608451977731ed3b5c298534dbb249b3a7ced352cea82  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/processor/RawNoiseModel.kt
cc80f77bf5e22893e73827b05d9bc97ff49f0df1481c309112d7d81e697ec706  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/AdobeCurveToneAlgorithm.kt
31ce91ba2c3f4112b619c48217272acab681c8935738dc5e4acf2ecbd1308dd2  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/ColorSpace.kt
569a433e742c78be7d7965441139a999a5a3d64acb9320330c246432512615a4  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpDefaultBlackRender.kt
71c1082600c299113efad4c1ae1fc2aa59e549f7d6f23bbcee964f00d7af5ab4  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpHueSatMap.kt
02ed466de95efd492088e269c7cdb06056eb53f29293f36a521f83f86445ed91  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpHueSatMapGl.kt
d79202b0b6516b14a3399ff7c9769deaeb62bbf9738df5fd3a3302c3a8d12de2  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpProfile.kt
15576a6e76f1aaba188e0bcac130d14c6927047bef86e92793b15fa3a0a023fa  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpRenderPlan.kt
6d372b8479aa8e4e2b1a8dd13e8092640c66d1285cc458e45e0ec99d210326b7  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpTextureResources.kt
dec750aa88c2c6e87fdb1150f35b6ff678fb87f341317be2cf64007afc32fb9f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DcpToneCurve.kt
e4bf812d8480b1fe5526bc775cb1d8649bb404026658ef0a641402c5cd420567  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DngBaselineExposure.kt
2f45fa722847685d11b3fa5a32881492d6de459b185a8ed2c8d882d811c92bd7  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DngProfileGainTableRenderShader.kt
2fbe106b48f183bdfe4d13efd298e0ca8a466ae693fd3f34842b98fd9a6524ba  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/DngSdkColorSpec.kt
1dc0527580c5b61722add444428d14d2fffb117194fabcccef93243e6bf803b5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/GlesMgcGuidedUpsampleShaders.kt
c4d559b2a07e3c90fb0ec0e3c7acadf8aeab8e7d3ef053735e7c91632da8d976  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/GlesMgcSharpen.kt
a3e4f02541822ef5461b5b685b0d19a1d0dd232710aa1967d61c309faaca8385  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/GlesMgcSharpenShaders.kt
bbd6feb9e16857b75441fd7516b3faaff86bdab51c991e0bccaeeaed56dfdb60  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/MgcFinishResolution.kt
41c7717ddbf8d9df2b77b06d64e53061a771330b3e1f13e2b7dc11739ba788a4  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/MgcGlesSurfaces.kt
2082fd5e7b18cc971698fb6fd819b18756a9b16bc5aa218aaec7f4c939cebaad  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/MgcGuidedUpsample.kt
29568567fff7e7afd369fc3ef2e4346b504f102c25b3c5a97bbaa78c34e4e9ec  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/MgcSharpenCurveBuilder.kt
aeec65a1ef0e45d119b78617771416c90a540f32b1b1cc7e372a824b1a6ef4d5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawAdobeOnlyCompatibility.kt
3ca9b655e37c4dab36f799d487b33d2eddb3039ac26161f30014d0690b43197f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawCameraCalibration.kt
5c3094c1573b9174012d3cc54cdccbfb37cb4ca6469522e95d07212dd7a898b0  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawCurveTextureResources.kt
a94e41d6385ddb759002c08628da7b00abae4a37c266f65bbda1ad8fdd688730  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawEngineColorResources.kt
2421ec0c7b4188836864c92af073e21952043a9875a18cb363a912deffc5035b  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawEngineTonePass.kt
bedbfc8c15de8a50a938d2d7245c579b439a1296f6b307e03969fd43ccaf9b36  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawFullscreenQuad.kt
e8af21cf1a29455df7b3a620e9e656e4346c79630eb6d122c34a45b60741e67e  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawGlesProgram.kt
78384340455e78133bb68d9a49f9821150a07f650b293ece0784236dbf463a35  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawHdrReferenceMath.kt
dfc665ed737f89b5cd70f64b0240e8304b2781fbdcc671d04c403d7dc2a3297b  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawHdrReferencePass.kt
e1c31bd47272a1a94dcf1fcf15c5b2d001fa9346fa9a8657c3211beeded32b3f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawLinearRcdPass.kt
89b15fe777a0a69f83045d68661ce0d7f85b380fd7b5a2ba542f84bead213f0e  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawMetadata.kt
5bede6dc1ebef377b0be6aa2c6f22c72fbb2fb34d45973d7a1e86c66f54cdf55  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawOutputGeometry.kt
28858cf3c6fd7f4322e4d3d021126eb632e21224790eb7c7c7f4e5148f169077  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawOutputPass.kt
0e1cb4c99ae9626b8761702162067564cd87af7d79c17893e40142ea8e88015f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawOutputUpscaleMode.kt
df4a57da8736a720a90dbe399a8b239eac05c4da526f78e3f6ccbb91d02b726e  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawProfileExposureGl.kt
cfcd45734b8da7bf53d10f42e952c614ef21bbb68c8b8f06a3d47e27fadd4c73  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawRenderingEngine.kt
3fd4ee5278263176c5dadafaea69f4af1a75dfb395376e327e1c1d9f9a8e36ad  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawRenderingEngineToneAlgorithm.kt
dc3b29f2a29f606b773de570c63437821428737622d083975e8df52c3b1f6454  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawSharpeningDefaults.kt
d4dc25a8b1a4f8e5133bd1a4bf19028cca2b4e129ebf9eddc2c755f1942f5290  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawSrgbPass.kt
5ad4337e1f53828914eb4e9e2e19aebbe4f393b19160ab1149d60f812ac1282d  app/src/main/java/com/hinnka/mycamera/processor/experimentc/bjzhou/raw/RawTileRect.kt
36d50a44591d542b0c41d645ddeb026ff78bdfc200c3fed4e5786d5c1880c0bf  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvAlignmentShaders.kt
e932e9156f6665c421b3446943f03a3445b11c0ed0083f646802d18b3a3bdceb  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvHardwareBufferInput.kt
b9960f26e2a624f61b14f74118b81de8e0d0e3d58f496113e14691c409913e4e  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvLkPyramidPlan.kt
ad893cafc4058bbbf227b5171c86b7e4eec498ccf087f10e30e7f2814a1bd9e6  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvSabreShaders.kt
8e9ddec98899cde5be0f79b08a1ee7f3090da04753bdeffd64b0faeebfcab2de  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvSpatialShaders.kt
9f2a946934c361b1576a5e1d0c61abe44277acf214196fde0905586d54b6fac0  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvStacker.kt
3bdc66f7ed4625b4cdf670e4999bbd64befae51d79ae1eb3e656dc44f833623c  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesYuvTiming.kt
"""

V10_STALE_STAGE_SHA256 = """\
33d13b5e4589b13bcdb1a9da698a8f5515ac679af9e27e497d87d09ba9ffe01b  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/EmbeddedGainmapProducer.kt
8257a9f2e70bf5d9151c21174a77995edc7b9f150b01cd4b1724ac3e63e480f8  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/EstimatedSdrGainmapMath.kt
72ae8a02d175b71b644bf3ccdb5681306190c0ee5b10747cafc03f7fb85cf178  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/EstimatedSdrGainmapProducer.kt
4d62008f14daea727059ce5930aacf577902357397f44251cc8b6544156f6db5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/UltraHdrWriter.kt
63d863a46df1e2a705270e366a8dd23a1325b53fc4469154578272ae78287102  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/hdr/UnifiedGainmapProducer.kt
c85aae98c1187ebcb79ce2da842ccef19ef479fd5a904779a508bf768a0e5b9a  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/ml/SharedDepthEstimator.kt
2341c5033d4340c0dbd0a9cd7db2cf7b59bf80d13f93e6269f0cc59bbece0cd3  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesGpuTimerQuery.kt
131aa6fa2460a2832c71c5e5916ad9addbd2dede7189b898150502e50d27671f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/processor/GlesHardwareBufferImage.kt
a01883604bab24089937be7400a5cc260d35ec06bc265eef1ea9a85df1794b27  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/AgXToneAlgorithm.kt
754c4095ee70a13f8e09e916c6d05095662482cfff49b99485e17ce3be8c8334  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonIccGlResources.kt
7effd4df72fee69de0b5f3c6f19968b044baf227f5885ac9d1a09c556c779d66  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonIccProfile.kt
cd92b6e822b67ff8970c64f66dbc6af3a6c9394d96966b1c1c39170e5b8a521e  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonIccShader.kt
66bdb2705a440ce14a6c4583326a73ccbe4301de114cc60c0b2c79a8969a62e3  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonPictureStyle.kt
bf9a8fab294baf040bb6e5d5adebc3ccc3479e57a31d4513339ab96fac24ea13  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonProfile.kt
136e92f3a3e386248da121b5a9d060cc2920859b6cf7560e10ccde648be1c749  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonR5ChromaMath.kt
8edd050f31246e72971f8e3e68ac1cc7dac3d468ec49d5333ad4efee86a63b81  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonRecipeColorMath.kt
df7e94f994f1a306772b8a4ed581ff273bab02fe57b6459f59c5293bf5022bc1  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/CanonToneAlgorithm.kt
316e372aed8e581bdd96b382bdeef142ebf5f6b102126f18a39729bda059ddc5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/DarktableFilmicHighlightReconstructionAlgorithm.kt
d6f5a18b7535612ec51a0d49c5aa4c4563b73f6a4cdec3f8d859c59d47f61201  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/DarktableFilmicToneAlgorithm.kt
40331104687086fbbd36d568e64518925de5414197327de3608b2bf2fa6f6953  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/DarktableSigmoidToneAlgorithm.kt
0525ff9f499b4ef39a383c02373635c1ce1a012854d0eba015223d8a585cfe5f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/DirectCameraColorTransform.kt
4e7e098c439b8976815af7e4123b8170197716081e8143c98a808a0c466711f6  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/EquivalentCameraCalibration.kt
32b100329483ca4397b773a8fd00b663da59a069bce2981c7ce8b76c561997bd  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/FotufilmToneStage.kt
b10da4f9db32910cb13b329f47daf5a10b5c356aab0eb8a7c4218221962698f5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/HncsCameraDomain.kt
e0602cb7874eb16fef32c65646014df88b6ce173eb63a3ee0b8ed58e3bb60820  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/HncsOutputLinearPass.kt
6fff38a826fceee2a5ab07fe21678d46a3bcce7d87b986326b2a1652e11c6c12  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/HncsProfile.kt
f84172ef5d68e389fbac72963a42cca76a2fd00256617047b9e813c1ea9c88b3  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/HncsToneAlgorithm.kt
0d81571466315c4a346474ca663caab53a48baf29b88e79395aba0799a82cd90  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/LeicaProfile.kt
c89b33a6ed51a77668decdb42c26e3e3821442415d4930147448af8f6ceb2413  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/LeicaToneAlgorithm.kt
534bd8d56e622dcd64512cfb1d6f0c882e75e6b22e0502fe28e4d6418e9bcf01  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/LumixColorTemperature.kt
2ee363174d9c854ba2eb8316773f7a14e3701ccf430efd1b7afc67ab219d16d0  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/LumixPhotoStyle.kt
fc4b4e44f55bfe0f6e6e88847bbca29ead65f987b2c773d4c7aff41e23a90acb  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/LumixProfile.kt
c29898527be28e8b75ab0c59284a0d89df7e735e4ca64901f5af347e4568a2f9  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/LumixToneAlgorithm.kt
94034e562bfc453983335999c00621c0aaccfbc9bad7c518381e10df2d191114  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/MgcRaisrUpscale.kt
2bea7033983ab962892cfbcd89d4cebc7b209e401ecf066321e8141ba6c2f288  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpectralFilmEffects.kt
b4f7694e6cdc17ab53eb3ce16194d490dd698742584e2ffb529fe3643281a7ce  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpectralFilmGraph.kt
934868b55ea77488b443fbd1c23174efda8506bfb31496e3359e170fa6b50fb6  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpectralFilmProfile.kt
c1482e7041ae39a39136ffd1d8308c12ced35616555c51dfbb3c80ef97d57eb2  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpectralFilmTuning.kt
ca71526705aa93e63cbcd297a985f095b0d852462acba2b642f7b147d91fe402  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmDiffusionAtlas.kt
25366c12839e9bc04f4029b98929e4e9bd10d85ab40e5351812a415a1276b4af  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmGrainPass.kt
4e38c3416ffdb352c0b8453f5b29a89f0726d1c803a80c003f9e8a5b6ad990fe  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmGraphGl.kt
4b93c9eb234db954507ddd40854cea22f509f6591729f3953cfe381026bb642c  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmGraphShaders.kt
b3b6437cd05c1cd232103e4445070b404ee3a3d405ccc7de00d0ff0e4cadc2af  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmGraphToneStage.kt
356d92ad779cb713dadbd0a83dd3418846766816c5d9de7a9dee21ed8992ad23  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmOpticsKernels.kt
227aea5cebdf5fe9d252efc4677af8015c9c680a739e9b4122e773e97dfebddf  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmOpticsPass.kt
16108c38ceaf6bc52be44fca0151af05ac732194bd43b97b272017873f912ae5  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmOpticsShaders.kt
25db9a81beebd645c611a06df7e0a379ccff75ee0ff95dab8a8fc191fe4ead6b  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmRuntime.kt
4566a88eec29089cdf3ab3290f6b57b877651514f504a2e987874316811553bd  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmScannerPass.kt
5cde7bf3b0b3b970ce81f08c8d77b44470d2a60a33ba93e557201331e036ac68  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/SpektrafilmToneAlgorithm.kt
5d8321120e116b993c98eb09842a06be02e2229354f2f1b4f26aa5546f127566  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmBuildResult.kt
7569d616d5ae40562c376f299e494387f8dd0b00fec771b81a2f404d3a0b73ab  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmCatalogue.kt
4ab76ce607efd66f793ac69e9629c5cadb23d77ec213e96220befd33aa3ff902  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmConfigLayout.kt
14a68aa181af60ca7c770e522339107114b36578fc470fd4ee8be5ab405cb95f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmDocument.kt
98465458e71e935b7cc10be6ce96bfe868bb2db98a02c53a820a4729d97ae8e3  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmFrame.kt
fd32c1dce469af315dccfae7a1803c837684eafa8c96b5917061f1c675d3f752  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmFrameFields.kt
5ad6820ff65580f37e5495677b1fc5cf7dfc63b81db620cc0d19dcc19cd073f4  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmFrameParams.kt
04a78547f17b099dcdb6b837d8c05ce26ab86ebfdc5d1a2caed22a40d81e836e  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmNativeBridge.kt
c0f77908c9f92e2bb6a5e05dd4a473704521c69511b2d21d111b55ac00a510fd  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmRenderer.kt
3ba84fe6eba41127e009fbd6b5935f7d215a44e1ba2f3daf411c76e98a06bf78  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmRuntime.kt
b1f1c936bba3e9d32fe5826e1be537629e15973010fd313649f916adf6a5085f  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmShaders.kt
0bb90c6badb160859a30789fb2ee81f8330d61df7ae080e12e6f42dae035a714  app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/raw/fotufilm/FotufilmStockInfo.kt
"""

V13_STALE_STAGE_SHA256="""b2cb975989affbca5cc6726dfcf5228714da927adf87b014981a4cf6ebb0c1c5  app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26975CFlickerModeFreeze.java
c41ba8bca62961de811766207654ee3997e5c717c68091f8b178e379863f6aec  app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26975CNightExposureFreeze.java"""

def stale_stage_manifest():
    out={}
    for line in V7_STALE_STAGE_SHA256.splitlines():
        h,path=line.split('  ',1)
        if not re.fullmatch('[0-9a-f]{64}',h) or path in out or not path.startswith('app/src/main/java/com/hinnka/mycamera/processor/experimentc/'):
            fail('bad V7 stale stage SHA-256 manifest')
        out[path]=h
    if len(out)!=56 or sum('/bjzhou/' in p for p in out)!=49 or sum('GlesYuv' in p for p in out)!=7:
        fail('V7 stale stage list changed')
    for line in V10_STALE_STAGE_SHA256.splitlines():
        h,path=line.split('  ',1)
        if not re.fullmatch('[0-9a-f]{64}',h) or path in out or not path.startswith('app/src/main/java/com/hinnka/mycamera/processor/experimentc/original129/'):
            fail('bad V10 stale stage SHA-256 manifest')
        out[path]=h
    if len(out)!=117:fail('V10 stale stage list changed')
    for line in V13_STALE_STAGE_SHA256.splitlines():
        h,path=line.split('  ',1)
        if not re.fullmatch('[0-9a-f]{64}',h) or path in out or not path.startswith('app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/'):
            fail('bad V13 stale stage SHA-256 manifest')
        out[path]=h
    if len(out)!=119:fail('V13 stale stage list changed')
    return out

def prune_only_pinned_stale_stage(payload,changed,known_stale):
    # Pure, isolated staging cleanup: fail closed for missing V8 inputs,
    # unexpected extras, tampered old inputs, or symlinks; only remove
    # the EXACT historic V7 paths. The compiled candidate never includes these.
    for path in payload.rglob('*'):
        if path.is_symlink():
            fail('symlink in 26975 staging payload '+str(path))
    got={p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}
    missing=changed-got
    extra=got-changed
    if missing or extra-set(known_stale) or (set(known_stale)&changed):
        fail('payload missing/extra (stale guard): missing='+str(sorted(missing)[:8])+' extra='+str(sorted(extra-set(known_stale))[:8]))
    for rel in sorted(extra):
        p=payload/rel
        if sha(p)!=known_stale[rel]:
            fail('tampered SHA-pinned historical staging file '+rel)
    for rel in sorted(extra):
        path=payload/rel
        path.unlink()
        # Git tracks files, not directories. Remove now-empty historical
        # directories too, because source tests forbid a residual bjzhou tree.
        parent=path.parent
        while parent!=payload:
            try:parent.rmdir()
            except OSError:break
            parent=parent.parent
    if extra:
        print(f'PASS exact V7/V10/V13 stale staging cleanup: {len(extra)} SHA-256 pinned files excluded from V14 C candidate')
    return len(extra)


def fail(msg):raise RuntimeError('26975 BLOCKED: '+str(msg))
def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for b in iter(lambda:f.read(4*1024*1024),b''):h.update(b)
 return h.hexdigest()
def parse(path):
 d={}
 for line in path.read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad manifest '+str(path))
  if not re.fullmatch('[0-9a-f]{64}',h) or not p.startswith('app/') or '..' in pathlib.PurePosixPath(p).parts or p in d:fail('malformed/duplicate manifest '+p)
  d[p]=h
 return d
def scan(root):
 src=root/'app/src';required=[root/'app/build.gradle',root/'app/version.properties']
 if not src.is_dir() or not all(x.is_file() for x in required):fail('missing complete app/source/Gradle '+str(root))
 d={}
 for p in [*src.rglob('*'),*required]:
  if p.is_symlink():fail('source symlink '+str(p))
  if p.is_file():d[p.relative_to(root).as_posix()]=sha(p)
 return d
def exact(root,file,label):
 want=parse(R/file);got=scan(root)
 if got!=want:fail(label+f' missing={sorted(set(want)-set(got))[:8]} extra={sorted(set(got)-set(want))[:8]} mismatched={[p for p in want.keys()&got.keys() if want[p]!=got[p]][:8]}')
 print('PASS '+label+f': {len(got)} physical files')
 return got

def scope():
 a=parse(R/'26975_BASE_26974_FULL_APP.sha256');b=parse(R/'26975_EXPECTED_FULL_APP.sha256')
 changed=set((R/'26975_CHANGED_RUNTIME_ALLOWLIST.txt').read_text().splitlines())
 added=set((R/'26975_ADDED_RUNTIME_PATHS.txt').read_text().splitlines())
 modified=set((R/'26975_MODIFIED_ORIGINAL_PATHS.txt').read_text().splitlines())
 deleted=set((R/'26975_DELETED_RUNTIME_PATHS.txt').read_text().splitlines())
 if (len(a),len(b),len(changed),len(added),len(modified),len(deleted))!=(NBASE,NFILES,NCHANGE,NADDED,NMODIFIED,NDELETED):fail('count/protected source regression')
 if changed!=added|modified or added&set(a) or modified-set(a) or set(b)!=(set(a)|added) or deleted:fail('unexpected runtime change/deletion')
 if {p for p in set(a)&set(b) if a[p]!=b[p]}!=modified:fail('original source edits outside allowlist')
 protected={p:h for p,h in a.items() if p not in changed}
 if len(protected)!=NPROTECTED or protected!=parse(R/'26975_PROTECTED_SOURCE.sha256'):fail('protected source failed')
 if sha(R/'26974_SUCCESSFUL_EXECUTED_WORKFLOW_REFERENCE.yml')!=WORKFLOW_SHA or sha(R/'26974_SUCCESSFUL_EXECUTED_BUILDER_REFERENCE.py')!=BUILDER_SHA:fail('26974 actual executed reference changed')
 if (R/'handoff_payload_26975/app/version.properties').read_text()!='VERSION_MAJOR=0\nVERSION_MINOR=9726440\nVERSION_NAME=0.9726975\nVERSION_BUILD=26975\n':fail('26975 version not exact')
 allowed_modified=set(json.loads((R/'26975_AUTHORITY_AND_SCOPE.json').read_text())['allowed_modified_exact'])
 if allowed_modified!=modified:fail('changed original paths not explicit')
 for p in added:
  if not (p.startswith(('app/src/main/java/com/hinnka/mycamera/processor/experimentc/',
                        'app/src/main/assets/experimentc/',
                        'app/src/main/cpp/iris26975c/',
                        'app/src/main/cpp/mgc1271_upstream/experiment_c_26975/',
                        'app/src/main/java/com/hinnka/mycamera/processor/Iris26975C',
                        'app/src/main/java/com/hinnka/mycamera/raw/Iris26975C',
                        'app/src/main/java/com/particlesdevs/photoncamera/processing/experimentc/Iris26975C'))
          or p=='app/src/main/res/values/experimentc_original129_noise_strings.xml'):
   fail('additional file outside protected C namespace '+p)
 if a['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']!=b['app/src/main/java/com/particlesdevs/photoncamera/util/SimpleStorageHelper.java']:fail('A/B gallery changed')
 return changed,a,b

def seal():
 changed,a,b=scope();wf='.github/workflows/build-26975-change-aware.yml';trigger='TRIGGER_26975.txt'
 expect=set(FILES)|{wf,trigger}|{'handoff_payload_26975/'+p for p in changed}
 sealed={}
 for line in (R/'26975_HANDOFF_HASHES.sha256').read_text().splitlines():
  try:h,p=line.split('  ',1)
  except ValueError:fail('bad handoff hash seal')
  if p in sealed or not (R/p).is_file() or sha(R/p)!=h:fail('missing/tampered handoff file '+p)
  sealed[p]=h
 if set(sealed)!=expect:fail('missing/extra handoff file set '+str(sorted(set(sealed)^expect)[:10]))
 stages=[(R/f'26975_STAGE_{i}_UPLOAD_PATHS.txt').read_text().splitlines() for i in (1,2,3)]
 if stages[0]!=sorted((expect|{'26975_HANDOFF_HASHES.sha256'})-{wf,trigger}) or stages[1]!=[wf] or stages[2]!=[trigger]:fail('three upload stages not strict')
 payload=R/'handoff_payload_26975'
 prune_only_pinned_stale_stage(payload, changed, stale_stage_manifest())
 if {p.relative_to(payload).as_posix() for p in payload.rglob('*') if p.is_file()}!=changed:fail('payload missing/extra')
 for p in changed:
  if sha(payload/p)!=b[p]:fail('source input tampering '+p)
 if sha(R/'.github/workflows/build-26975-change-aware.yml')!=sealed[wf]:fail('workflow after seal changed')
 subprocess.run([sys.executable,'-S','test_26975_workflow_refs.py'],cwd=R,check=True)
 print(f'PASS 26975 three-stage SHA seal, {NPROTECTED} protected, {NCHANGE} source delta')

def fetch():
 seal();token=os.getenv('GITHUB_TOKEN','')
 if not token or os.getenv('GITHUB_REPOSITORY')!=REPO or os.getenv('GITHUB_REF_NAME')!=BRANCH:fail('Actions credentials/target branch unavailable')
 def get(endpoint):
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/'+endpoint,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json'})
  with urllib.request.urlopen(req,timeout=120) as resp:return json.load(resp)
 run=get('actions/runs/'+str(RUN));art=get('actions/artifacts/'+str(ART_ID))
 if run.get('id')!=RUN or run.get('conclusion')!='success' or run.get('head_sha')!=COMMIT or run.get('head_branch')!=BRANCH:fail('26974 Actions run not successful/exact')
 if art.get('id')!=ART_ID or art.get('expired') or art.get('digest')!='sha256:'+ART_SHA or art.get('workflow_run',{}).get('id') not in (RUN,None):fail('26974 artifact identity/published digest')
 TMP.mkdir(parents=True,exist_ok=True)
 subprocess.run(['curl','--fail','--location','--retry','3','--silent','--show-error','-H','Authorization: Bearer '+token,'-H','Accept: application/vnd.github+json',f'https://api.github.com/repos/{REPO}/actions/artifacts/{ART_ID}/zip','-o',str(ART)],check=True)
 if sha(ART)!=ART_SHA:fail('downloaded successful 26974 ZIP mismatch')
 print('PASS exact successful 26974 Actions artifact fetched')

def prior_zip():
 if not ART.is_file() or sha(ART)!=ART_SHA:fail('successful 26974 ZIP inaccessible or wrong hash')
 return zipfile.ZipFile(ART)
def safe_extract_tar(data,dest):
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as t:
  for m in t:
   path=pathlib.PurePosixPath(m.name)
   if not m.isfile() or not path.parts or path.parts[0]!='app' or path.is_absolute() or '..' in path.parts or m.issym() or m.islnk():fail('unsafe 26974 compiled TAR entry '+m.name)
  t.extractall(dest,filter='data')

def prepare_base():
 seal()
 for folder in (BASE,CAND):
  if folder.exists():shutil.rmtree(folder)
 BASE.mkdir(parents=True)
 with prior_zip() as z:
  if z.testzip():fail('26974 ZIP CRC invalid')
  def get(name):
   p='photon_26974_outputs/'+name
   if p not in z.namelist():fail('26974 successful compiled receipt missing '+p)
   return z.read(p)
  src=get('26974_candidate_app_source.tar.gz')
  if hashlib.sha256(src).hexdigest()!=TAR_SHA or get('26974_candidate_app_source.tar.gz.sha256')!=f'{TAR_SHA}  26974_candidate_app_source.tar.gz\n'.encode():fail('26974 actual compiled TAR mismatch')
  if get('26974_EXPECTED_FULL_APP.sha256')!=(R/'26975_BASE_26974_FULL_APP.sha256').read_bytes() or get('26974_PREBUILD_SEALED_APP.sha256')!=(R/'26975_BASE_26974_FULL_APP.sha256').read_bytes():fail('compiled source manifest authority differs')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build_26974_incremental.py')).hexdigest()!=BUILDER_SHA or BUILDER_SHA not in get('26974_ACTUAL_EXECUTED_BUILDER.sha256').decode():fail('successful executed builder not pinned')
  if hashlib.sha256(get('ACTUAL_EXECUTED_build-26974-change-aware.yml')).hexdigest()!=WORKFLOW_SHA or WORKFLOW_SHA not in get('26974_ACTUAL_EXECUTED_WORKFLOW.sha256').decode():fail('successful executed workflow not pinned')
  if PRIOR_APK_NAME not in z.namelist() or PRIOR_APK_SHA not in get('26974_APK.sha256').decode() or hashlib.sha256(z.read(PRIOR_APK_NAME)).hexdigest()!=PRIOR_APK_SHA:fail('successful 26974 APK identity')
  identity=get('26974_ACTIONS_IDENTITY.txt').decode()
  if 'git_sha='+COMMIT not in identity or 'github_run_id='+str(RUN) not in identity:fail('26974 Actions job identity')
  compiler=get('26974_COMPILER_STATUS.txt').decode()
  for phrase in ('REAL PINNED GLSL COMPILE: PASS','REAL SPIR-V VALIDATION/OPTIMIZATION: PASS','REAL KOTLIN COMPILE: PASS','REAL JAVA COMPILE: PASS','REAL TWO-ABI NDK/CMake COMPILE: PASS','REAL ANDROID Gradle :app:assembleDebug: PASS','RUNTIME SOURCE INVARIANCE: PASS'):
   if phrase not in compiler:fail('26974 compiler proof absent: '+phrase)
  for task in (':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL'):
   if 'PASS '+task not in get('26974_REAL_GRADLE_TASKS.txt').decode():fail('26974 predecessor Gradle task absent: '+task)
  safe_extract_tar(src,BASE)
 exact(BASE,'26975_BASE_26974_FULL_APP.sha256','actual successful 26974 compiled source')
 shutil.copytree(BASE,CAND)
 changed,_,b=scope()
 for p in sorted(changed):
  dest=CAND/p;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(R/'handoff_payload_26975'/p,dest)
 exact(CAND,'26975_EXPECTED_FULL_APP.sha256','exact 26975 isolated candidate')
 if not (R/'gradlew').is_file() or not (R/'app/build.gradle').is_file():fail('live checkout missing real Gradle')
 if (R/'app/src').exists():shutil.rmtree(R/'app/src')
 shutil.copytree(BASE/'app/src',R/'app/src')
 shutil.copyfile(BASE/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(BASE/'app/build.gradle',R/'app/build.gradle')
 if (R/'app/.cxx').exists():shutil.rmtree(R/'app/.cxx')
 exact(R,'26975_BASE_26974_FULL_APP.sha256','historical preflight source restored')
 OUT.mkdir(parents=True,exist_ok=True)
 (OUT/'26975_SOURCE_SCOPE.txt').write_text(f'26974 Actions={RUN} commit={COMMIT} artifact={ART_ID} artifact_zip_sha={ART_SHA} actual_compiled_source_tar_sha={TAR_SHA}\nactual_runner_sha={BUILDER_SHA} actual_workflow_sha={WORKFLOW_SHA} prior_apk_sha={PRIOR_APK_SHA}\nbase={NBASE} candidate={NFILES} changes={NCHANGE} modified={NMODIFIED} added={NADDED} protected={NPROTECTED} deleted={NDELETED}\n'+''.join(p+'\n' for p in sorted(changed)))
 print('PASS 26974 compiled baseline reconstructed; isolated 26975 candidate ready')

def install():
 seal();exact(BASE,'26975_BASE_26974_FULL_APP.sha256','26974 baseline before install')
 exact(CAND,'26975_EXPECTED_FULL_APP.sha256','26975 frozen candidate before install')
 old=OUT/'26974_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 # Historical 26904 checks have been run; require predecessor successful Actions compiler receipt too.
 with prior_zip() as z:
  source=z.read('photon_26974_outputs/26974_REAL_GLSL_SPIRV_COMPILER.txt').decode()
  if 'PASS actual 26974 24/24 C GLES' not in source:fail('26974 real pinned GLSL/SPIR-V receipt missing')
 (OUT/'26974_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt').write_text(source)
 shutil.rmtree(R/'app/src');shutil.copytree(CAND/'app/src',R/'app/src')
 shutil.copyfile(CAND/'app/version.properties',R/'app/version.properties')
 shutil.copyfile(CAND/'app/build.gradle',R/'app/build.gradle')
 exact(R,'26975_EXPECTED_FULL_APP.sha256','live installed 26975 SHA source')
 print('PASS installed exact 26975 C-only Pro Sabre source; production unapproved')

def regress():
 seal();exact(R,'26975_EXPECTED_FULL_APP.sha256','26975 live protected runtime')
 subprocess.run([sys.executable,'-S','test_26975_source.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_gallery_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v4_capture_host.py','--root',str(R/'app')],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v5_asset_host.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','verify_26975_v6_current_glsl.py','--audit'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v5_asset_host.py','--live'],cwd=R,check=True)
 subprocess.run([sys.executable,'-S','test_26975_v10_minimal_core.py','--live'],cwd=R,check=True)
 print('PASS live 26975 C-only tests and protected file invariance')

def stage_native():
 seal()
 with prior_zip() as z:
  with zipfile.ZipFile(io.BytesIO(z.read(PRIOR_APK_NAME))) as apk:
   if apk.testzip():fail('26974 published APK CRC')
   for p,want in NATIVE_SHA.items():
    data=apk.read(p)
    if hashlib.sha256(data).hexdigest()!=want:fail('successful native ABI hash regression '+p)
    dest=R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/')
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
    if sha(dest)!=want:fail('staged native binary differs '+p)
 print('PASS exact successful 26974 dual ABI RawLens native binaries')

def verify_compiled():
 regress();success=OUT/'26974_SUCCESSFUL_REAL_GLSL_SPIRV_COMPILER.txt'
 current=OUT/'26975_REAL_GLSL_SPIRV_COMPILER.txt'
 if not success.is_file() or 'PASS actual 26974 24/24 C GLES' not in success.read_text():fail('26974 actual successful shader proof missing')
 if not current.is_file() or 'PASS actual 26974 24/24 C GLES' not in current.read_text() or 'PASS inherited historical 24/24 and actual current {SHADER_COUNT}/{SHADER_COUNT} V14 donor/Iris C shader compilation'.format(SHADER_COUNT=SHADER_COUNT) not in current.read_text():fail('current Actions 24/24 + V14 151/151 shader recompilation proof missing')
 v6=OUT/'26975_V6_CURRENT_STATIC_GLSL_SPIRV_COMPILER.txt'
 if not v6.is_file() or f'PASS 26975 V14 physical current {SHADER_COUNT}/{SHADER_COUNT} static donor/Iris C ESSL GLSL + SPIR-V opt/val' not in v6.read_text():fail('current C shader parser and SPIR-V optimizer must actually pass')
 for p,want in NATIVE_SHA.items():
  if sha(R/'app/build/verified_rawlens26931/jniLibs'/p.removeprefix('lib/'))!=want:fail('staged dual ABI LKR mismatch')
 for p,want in DONOR_SHA.items():
  if sha(R/'app/src/main/jniLibs'/p.removeprefix('lib/'))!=want:fail('original pinned donor sidecar mismatch')
 OUT.mkdir(exist_ok=True)
 (OUT/'26975_PREBUILD_SEALED_APP.sha256').write_bytes((R/'26975_EXPECTED_FULL_APP.sha256').read_bytes())
 print('PASS prebuild source seal + current actual pinned SPIR-V/GLSL + dual ABI native input')

def finalize():
 regress()
 if (OUT/'26975_PREBUILD_SEALED_APP.sha256').read_bytes()!=(R/'26975_EXPECTED_FULL_APP.sha256').read_bytes():fail('prebuild SHA seal absent')
 log=(OUT/'26975_gradle_assemble.log').read_text(errors='replace')
 tasks=(':app:compileDebugKotlin',':app:compileDebugJavaWithJavac',':app:configureCMakeDebug[arm64-v8a]',':app:buildCMakeDebug[arm64-v8a]',':app:configureCMakeDebug[armeabi-v7a]',':app:buildCMakeDebug[armeabi-v7a]',':app:assembleDebug','BUILD SUCCESSFUL')
 for task in tasks:
  if task not in log:fail('not proven actual Gradle task '+task)
 subprocess.run([sys.executable,'-S','verify_26906_native_cache.py','postflight'],cwd=R,check=True)
 apks=list((R/'app/build/outputs/apk').rglob('*.apk'))
 if len(apks)!=1:fail('exactly one newly assembled Android APK required')
 shutil.copy2(apks[0],R/APKNAME)
 if (R/APKNAME).stat().st_size<1_000_000:fail('suspicious APK size')
 with zipfile.ZipFile(R/APKNAME) as apk:
  if apk.testzip() or not {'AndroidManifest.xml','classes.dex'}<=set(apk.namelist()):fail('invalid Android output APK archive')
  for p,want in {**NATIVE_SHA,**DONOR_SHA}.items():
   if hashlib.sha256(apk.read(p)).hexdigest()!=want:fail('assembled APK native binary hash mismatch '+p)
  if not any(x.startswith('lib/arm64-v8a/libiris26972c.so') for x in apk.namelist()):fail('original C native library not linked')
 exact(R,'26975_EXPECTED_FULL_APP.sha256','actual assembled 26975 source unchanged')
 OUT.mkdir(exist_ok=True)
 (OUT/'26975_COMPILER_STATUS.txt').write_text('REAL PINNED GLSL COMPILE: PASS\nREAL SPIR-V VALIDATION/OPTIMIZATION: PASS\nREAL KOTLIN COMPILE: PASS\nREAL JAVA COMPILE: PASS\nREAL TWO-ABI NDK/CMake COMPILE: PASS\nREAL ANDROID Gradle :app:assembleDebug: PASS\nRUNTIME SOURCE INVARIANCE: PASS (2110 protected, 22 modified, 263 added)\nEXPERIMENT C CONTROLLED DEVICE TRIAL: ENABLED\nEXPERIMENT C PRODUCTION READY: NO\nDEVICE IQ VALIDATION: NOT RUN\n')
 (OUT/'26975_REAL_GRADLE_TASKS.txt').write_text(''.join('PASS '+p+'\n' for p in tasks))
 (OUT/'26975_APK.sha256').write_text(sha(R/APKNAME)+'  '+APKNAME+'\n')
 wf=R/'.github/workflows/build-26975-change-aware.yml'
 (OUT/'26975_ACTUAL_EXECUTED_BUILDER.sha256').write_text(sha(R/'build_26975_incremental.py')+'  build_26975_incremental.py\n')
 (OUT/'26975_ACTUAL_EXECUTED_WORKFLOW.sha256').write_text(sha(wf)+'  '+wf.relative_to(R).as_posix()+'\n')
 (OUT/'26975_ACTIONS_IDENTITY.txt').write_text('git_sha='+os.getenv('GITHUB_SHA','NOT_IN_ACTIONS')+'\ngithub_run_id='+os.getenv('GITHUB_RUN_ID','NOT_IN_ACTIONS')+'\n')
 for item in ('26975_BASE_26974_FULL_APP.sha256','26975_EXPECTED_FULL_APP.sha256','26975_PROTECTED_SOURCE.sha256','26975_CHANGED_RUNTIME_ALLOWLIST.txt','26975_ADDED_RUNTIME_PATHS.txt','26975_MODIFIED_ORIGINAL_PATHS.txt','26975_DELETED_RUNTIME_PATHS.txt','26975_AUTHORITY_AND_SCOPE.json'):
  shutil.copy2(R/item,OUT/item)
 shutil.copy2(R/'build_26975_incremental.py',OUT/'ACTUAL_EXECUTED_build_26975_incremental.py')
 shutil.copy2(wf,OUT/'ACTUAL_EXECUTED_build-26975-change-aware.yml')
 with (OUT/'26975_candidate_app_source.tar.gz').open('wb') as f:
  with gzip.GzipFile(filename='',mode='wb',compresslevel=1,mtime=0,fileobj=f) as gz:
   with tarfile.open(fileobj=gz,mode='w') as t:
    for rel in sorted(parse(R/'26975_EXPECTED_FULL_APP.sha256')):
     path=R/rel;m=t.gettarinfo(str(path),arcname=rel);m.uid=m.gid=0;m.uname=m.gname='';m.mtime=0
     with path.open('rb') as opened:t.addfile(m,opened)
 (OUT/'26975_candidate_app_source.tar.gz.sha256').write_text(sha(OUT/'26975_candidate_app_source.tar.gz')+'  26975_candidate_app_source.tar.gz\n')
 print('PASS real compiled 26975 source/APK SHA proof; IQ not proven until on-device')

if __name__=='__main__':
 try:
  parser=argparse.ArgumentParser();parser.add_argument('command',choices=('seal','fetch','prepare-base','install','regress','stage-native','verify-compiled','finalize'));args=parser.parse_args()
  globals()[args.command.replace('-','_')]()
 except Exception as e:print('26975 BUILD ERROR:',e,file=sys.stderr);sys.exit(1)
