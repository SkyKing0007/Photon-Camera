package com.hinnka.mycamera.processor

import android.content.ContentValues
import android.content.Context
import android.graphics.ImageFormat
import android.hardware.camera2.CameraCharacteristics
import android.hardware.camera2.CaptureResult
import android.hardware.camera2.params.ColorSpaceTransform
import android.net.Uri
import android.opengl.GLES30
import android.os.Build
import android.provider.MediaStore
import com.hinnka.mycamera.model.SafeImage
import com.hinnka.mycamera.processor.experimentc.Iris26975COriginalRawBurst
import com.hinnka.mycamera.utils.LargeDirectBuffer
import com.particlesdevs.photoncamera.processing.DngCreator
import com.particlesdevs.photoncamera.processing.experimentc.Iris26975COutputGeometry
import com.particlesdevs.photoncamera.processing.processor.IrisMotionSettings
import com.particlesdevs.photoncamera.processing.processor.IrisNoiseProfileStore
import java.io.File
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale

/** C OFF's independent copy of B's preserved NORMAL-only 26850 normalized Bayer DNG producer.
 * The untouched donor JPEG path never consumes this separate reconstruction. */
internal object Iris26986COffDng {
    class Frozen(val characteristics: CameraCharacteristics,
                 val noise: RawNoiseProfileSelection,
                 val tone: IrisMotionSettings.Snapshot,
                 val edge: IrisMotionSettings.EdgeFalseColorTunables.Snapshot,
                 val options: IrisMotionSettings.DngOptions.Snapshot)
    fun freeze(context: Context, characteristics: CameraCharacteristics, rawSaver: Int): Frozen {
        require(rawSaver in 1..2)
        val tone = IrisMotionSettings.current()
        val noise = if (tone.customNoiseModelEnabled) RawNoiseProfileSelection.Calibrated(
            requireNotNull(IrisNoiseProfileStore.loadSelectedProfile(context)) { "C OFF selected DNG noise profile unavailable" })
        else RawNoiseProfileSelection.Camera2
        return Frozen(characteristics, noise, tone, IrisMotionSettings.EdgeFalseColorTunables.current(tone.edgeFalseColorAllEdges26792), IrisMotionSettings.DngOptions.current())
    }
    private fun positional(f: Iris26975COriginalRawBurst.Frame): FloatArray {
        val black = f.metadata.copyCanonicalBlackForAudit()
        val phase = when (f.metadata.cfaPattern) {
            0 -> intArrayOf(0,1,2,3); 1 -> intArrayOf(1,0,3,2)
            2 -> intArrayOf(2,3,0,1); 3 -> intArrayOf(3,2,1,0)
            else -> error("C OFF unsupported CFA")
        }
        return FloatArray(4) { black[phase[it]] }
    }
    fun save(context: Context, frozen: Frozen, burst: Iris26975COriginalRawBurst,
             geometry: Iris26975COutputGeometry,
             donorGeometry: com.hinnka.mycamera.processor.experimentc.Iris26977CPhysicalGeometry.Frozen, jpegName: String, shutterMillis: Long,
             stillLive: () -> Boolean): Uri {
        val ref = burst.reference
        val meta = ref.metadata
        val result = ref.physicalCaptureResult
        val ch = frozen.characteristics
        val width = burst.rawWidth; val height = burst.rawHeight
        // The spool stores a packed physical RAW crop. Keep the actual CFA samples,
        // and rebase the four-channel shading grid to that plane (never to JPEG size).
        val physical=donorGeometry.physicalCrop
        require(donorGeometry.geometry === geometry && geometry.rawWidth==ref.sensorWidth && geometry.rawHeight==ref.sensorHeight &&
            physical.sourceWidth==ref.sensorWidth && physical.sourceHeight==ref.sensorHeight)
        val packed=Iris26986COffDngGeometry.Bounds(ref.cropLeft,ref.cropTop,ref.cropLeft+width,ref.cropTop+height)
        val active=physical.activeSourceBounds.let{Iris26986COffDngGeometry.Bounds(it.left,it.top,it.right,it.bottom)}
        val requested=Iris26986COffDngGeometry.Bounds(geometry.cropLeft,geometry.cropTop,geometry.cropRight,geometry.cropBottom)
        val defaultCropZoom=Iris26986COffDngGeometry.validate(ref.sensorWidth,ref.sensorHeight,packed,requested,active)
        val white = result.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL) ?: meta.sensorWhiteLevel
        val gains = result.get(CaptureResult.COLOR_CORRECTION_GAINS)
        val wb = gains?.let { floatArrayOf(it.red,it.greenEven,it.greenOdd,it.blue) }
            ?: meta.copyCanonicalWbForAudit()
        val map = result.get(CaptureResult.STATISTICS_LENS_SHADING_CORRECTION_MAP)
            ?.takeUnless { ch.get(CameraCharacteristics.SENSOR_INFO_LENS_SHADING_APPLIED) == true }
        val lsc = map?.let {
            val source=FloatArray(it.gainFactorCount).also { a -> it.copyGainFactors(a,0) }
            Iris26986COffDngGeometry.rebaseGains(source,it.columnCount,it.rowCount,active,packed)
        }
        val frames = burst.frames.map { f ->
            val m=f.metadata
            val camera2=f.physicalCaptureResult.get(CaptureResult.SENSOR_NOISE_PROFILE)?.let { pairs ->
                FloatArray(pairs.size*2) { i -> (if(i%2==0) pairs[i/2].first else pairs[i/2].second).toFloat() }
            }
            when(val choice=frozen.noise) {
                is RawNoiseProfileSelection.Calibrated -> {
                    val model=requireNotNull(choice.profile.evaluate(m.sensitivityIso))
                    require(model.shotNoise.all { it.isFinite()&&it>0f } && model.readNoise.all { it.isFinite()&&it>=0f } && model.readNoise.any { it>0f })
                }
                RawNoiseProfileSelection.Camera2 -> require(camera2!=null && camera2.size>=8 && RawNoiseModel.fromCamera2NoiseProfile(camera2).hasValidCamera2Profile)
            }
            require((f.physicalCaptureResult.get(CaptureResult.SENSOR_DYNAMIC_WHITE_LEVEL) ?: m.sensorWhiteLevel) == white)
            RawStackFrame(SafeImage(width,height,ImageFormat.RAW_SENSOR,m.sensorTimestampNs,f.raw16(),width*2,2),
                sensorTimestampNs=m.sensorTimestampNs,frameNumber=m.frameNumber,exposureTimeNs=m.exposureTimeNs,
                sensitivityIso=m.sensitivityIso,exposureProduct=m.exposureProduct,
                focusDistanceDiopters=m.focusDistanceDiopters,lensState=m.lensState,physicalCameraId=m.physicalCameraId,
                rollingShutterSkewNs=m.rollingShutterSkewNs,channelNoiseProfile=camera2.takeIf { frozen.noise==RawNoiseProfileSelection.Camera2 },
                dynamicBlackLevelByCfaPosition=positional(f),dngOptions26786=frozen.options,role=RawBurstFrameRole.NORMAL)
        }
        var committed: Uri? = null
        try {
            val row = Iris26972CEglProcessingOwner.withNewContext {
                check(stillLive())
                val stack = requireNotNull(C26986GlesMgcRawSpatialStacker26850(
                    width=width,height=height,cfaPattern=meta.cfaPattern,blackLevel=meta.copyCanonicalBlackForAudit(),whiteLevel=white,
                    whiteBalanceGains=wb,noiseProfileSelection=frozen.noise,lensShading=lsc,
                    lensShadingWidth=map?.columnCount ?: 0,lensShadingHeight=map?.rowCount ?: 0,
                    outputMode=MgcSpatialOutputMode.RGB,mergeMethod=MgcMergeMethod.SABRE,outputScale=1f,
                    useCurrentGlContext=true,exportGpuLinearRgbSource=true,gpuLinearRgbStorage=GpuLinearRgbStorage.RGBA16F,
                    processorPipeline=MgcRawProcessorPipeline.SABRE,exportNormalStackedDng=true,
                    vgnChromaCorrectionStrength=frozen.tone.chromaCorrectionStrength.coerceIn(0f,1f),
                    preserveExtendedHdrThroughVgn=true,enableSabreSuperRes=false,enableHighZoomDetail=false,
                    edgeFalseColor26778=frozen.edge,
                    referenceProtectionEv=0f).processFrames(frames))
                try {
                    GLES30.glFinish()
                    val raw=requireNotNull(stack.normalStackedDngRaw16)
                    val noise=requireNotNull(stack.normalStackedDngNoiseProfile)
                    require(stack.normalStackedDngFrameCount==frames.size && noise.size==6 && noise.all{it.isFinite()&&it>=0.0})
                    require(stack.normalStackedDngNoiseEquivalentSupport in 1f..(frames.size+.01f))
                    require(raw.capacity()==Math.multiplyExact(Math.multiplyExact(width,height),2))
                    check(stillLive())
                    val saved = publish(context,jpegName.removeSuffix(".jpg")+".dng",shutterMillis,stillLive) { out ->
                        val writer=DngCreator()
                        try {
                            val identity=DoubleArray(9){if(it%4==0)1.0 else 0.0}
                            fun matrix(t:ColorSpaceTransform?):DoubleArray = t?.let { a -> DoubleArray(9){a.getElement(it%3,it/3).toDouble()} } ?: identity.copyOf()
                            val c1=matrix(requireNotNull(ch.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM1)))
                            val c2=ch.get(CameraCharacteristics.SENSOR_COLOR_TRANSFORM2)?.let(::matrix) ?: c1
                            writer.setColorMatrix1(c1);writer.setColorMatrix2(c2)
                            writer.setForwardMatrix1(matrix(ch.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX1)))
                            writer.setForwardMatrix2(matrix(ch.get(CameraCharacteristics.SENSOR_FORWARD_MATRIX2)))
                            writer.setCameraCalibration1(matrix(ch.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM1)))
                            writer.setCameraCalibration2(matrix(ch.get(CameraCharacteristics.SENSOR_CALIBRATION_TRANSFORM2)))
                            writer.setCalibrationIlluminant1(ch.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT1)?.toShort() ?: 21.toShort())
                            writer.setCalibrationIlluminant2(ch.get(CameraCharacteristics.SENSOR_REFERENCE_ILLUMINANT2)?.toShort() ?: 21.toShort())
                            val neutral=requireNotNull(result.get(CaptureResult.SENSOR_NEUTRAL_COLOR_POINT)).map{it.toDouble()}.toDoubleArray()
                            require(neutral.size==3&&neutral.all{it.isFinite()&&it>0.0});writer.setAsShotNeutral(neutral)
                            writer.setMake(Build.BRAND);writer.setModel(Build.MODEL)
                            writer.setUniqueCameraModel("${Build.MODEL}-${Build.BRAND}-${Build.MANUFACTURER}")
                            writer.setSoftware("PhotonCamera 26986 C OFF")
                            writer.setDateTime(SimpleDateFormat("yyyy:MM:dd HH:mm:ss",Locale.US).format(Date(shutterMillis)))
                            writer.setIso(meta.sensitivityIso.toShort());writer.setExposureTime(meta.exposureTimeNs/1e9)
                            writer.setFocalLength(requireNotNull(result.get(CaptureResult.LENS_FOCAL_LENGTH) ?: ch.get(CameraCharacteristics.LENS_INFO_AVAILABLE_FOCAL_LENGTHS)?.firstOrNull()).toDouble())
                            writer.setAperture(requireNotNull(result.get(CaptureResult.LENS_APERTURE) ?: ch.get(CameraCharacteristics.LENS_INFO_AVAILABLE_APERTURES)?.firstOrNull()).toDouble())
                            writer.setCFAPattern(meta.cfaPattern);writer.setOrientation(geometry.rotation/90)
                            // DngCreator's inherited B convention passes T,L,B,R. Its
                            // GainMap serializer uses the same legacy axis ordering.
                            writer.setGainMap(lsc ?: floatArrayOf(1f,1f,1f,1f),0,0,height,width,map?.columnCount ?: 1,map?.rowCount ?: 1)
                            writer.setDefaultCropZoom(defaultCropZoom)
                            writer.setEmbeddedPreviewEnabled(true);writer.setBitsPerSample(16)
                            writer.setBlackLevel(shortArrayOf(0,0,0,0));writer.setWhiteLevel(65535.0);writer.setNoiseProfile(noise)
                            writer.setDescription("IRIS_26522_STACKED_DNG_DOMAIN=normalized-black-subtracted-16bit FrameCount=${frames.size} BlackLevel=0 WhiteLevel=65535 SupportMin=${stack.normalStackedDngSupportMin} SupportP01=${stack.normalStackedDngSupportP01} SupportP10=${stack.normalStackedDngSupportP10} SupportMedian=${stack.normalStackedDngSupportMedian} SupportMean=${stack.normalStackedDngSupportMean} SupportMax=${stack.normalStackedDngSupportMax} FrameEquivalentNoiseSupport=${stack.normalStackedDngNoiseEquivalentSupport} NoiseProfileBasis=Camera2NormalizedPerFrame/HarmonicReferenceFrameEquivalentSupport IRIS_26523_SINGLE_METADATA=true owner=C_OFF_PRIVATE")
                            writer.setCompression(false);raw.position(0);writer.writeBuffer(out,raw,width,height)
                        } finally { writer.close() }
                    }
                    committed = saved
                    saved
                } finally {
                    stack.gpuLinearRgbSource?.let { s -> s.stackCompletionTimeline?.releasePending();GLES30.glDeleteTextures(1,intArrayOf(s.textureId),0);if(s.clipZoneMaskTextureId26836!=0)GLES30.glDeleteTextures(1,intArrayOf(s.clipZoneMaskTextureId26836),0) }
                    stack.gpuBayerSource?.let{s->s.stackCompletionTimeline?.releasePending();GLES30.glDeleteTextures(1,intArrayOf(s.textureId),0)}
                    LargeDirectBuffer.free(stack.normalStackedDngRaw16)
                    if(stack.fusedBayerUsesNativeAllocator) LargeDirectBuffer.free(stack.fusedBayerBuffer)
                    listOfNotNull(stack.true2xLinearRgbPath,stack.true2xRenderRgbPath,stack.true2xNativeVgnGuidePath,stack.true2xPhaseSupportPath).forEach{File(it).delete()}
                }
            }
            return row
        } catch (failure: Throwable) {
            committed?.let { uri -> try { context.contentResolver.delete(uri,null,null) } catch (cleanup:Throwable) { failure.addSuppressed(cleanup) } }
            throw failure
        } finally { frames.forEach { it.image.close() } }
    }
    private fun publish(context:Context,name:String,time:Long,live:()->Boolean,write:(java.io.OutputStream)->Unit):Uri {
        require(Build.VERSION.SDK_INT>=29) { "C OFF DNG needs scoped MediaStore" }
        val resolver=context.contentResolver
        val values=ContentValues().apply {
            put(MediaStore.Images.Media.DISPLAY_NAME,name);put(MediaStore.Images.Media.MIME_TYPE,"image/x-adobe-dng")
            put(MediaStore.Images.Media.RELATIVE_PATH,"DCIM/Camera");put(MediaStore.Images.Media.DATE_TAKEN,time);put(MediaStore.Images.Media.IS_PENDING,1)
        }
        val uri=requireNotNull(resolver.insert(MediaStore.Images.Media.getContentUri(MediaStore.VOLUME_EXTERNAL_PRIMARY),values))
        try {
            requireNotNull(resolver.openOutputStream(uri,"w")).buffered(1024*1024).use(write)
            check(live());values.clear();values.put(MediaStore.Images.Media.IS_PENDING,0);check(resolver.update(uri,values,null,null)==1)
            return uri
        } catch(t:Throwable) { try{resolver.delete(uri,null,null)}catch(cleanup:Throwable){t.addSuppressed(cleanup)};throw t }
    }
}
