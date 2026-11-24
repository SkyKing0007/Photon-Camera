package com.hinnka.mycamera.processor.experimentc

import android.app.ActivityManager
import android.content.Context
import android.os.PowerManager
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawDemosaicProcessor
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawRenderingEngine
import com.hinnka.mycamera.processor.experimentc.original129.raw.RawSceneExposureEstimator
import com.hinnka.mycamera.processor.experimentc.original129.utils.PLog
import kotlinx.coroutines.*

/** Original startup RAW warmup with donor idle grace and resource guards; never calls A/B. */
object Iris26977CDonorPrewarm {
    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Default)
    private var job: Job? = null
    private var attempted = false
    @JvmStatic @Synchronized fun schedule(context: Context, width: Int, height: Int) {
        if (attempted || job?.isActive == true || width <= 0 || height <= 0) return
        attempted = true
        val app = context.applicationContext
        job = scope.launch {
            delay(1000L)
            val am = app.getSystemService(ActivityManager::class.java)
            val pm = app.getSystemService(PowerManager::class.java)
            if (am == null || am.isLowRamDevice || am.memoryClass < 384 || pm == null ||
                pm.isPowerSaveMode || (android.os.Build.VERSION.SDK_INT >= 29 &&
                    pm.currentThermalStatus >= PowerManager.THERMAL_STATUS_MODERATE)) return@launch
            try {
                ensureActive()
                RawDemosaicProcessor.getInstance().prewarmCapturePipeline(app, RawRenderingEngine.AdobeCurve, width, height)
                ensureActive()
                RawSceneExposureEstimator.warmUp(app)
            } catch (cancelled: CancellationException) { throw cancelled }
              catch (error: Throwable) { PLog.w("CPrewarm", "RAW startup prewarm failed", error) }
        }
    }
    @JvmStatic @Synchronized fun cancel() { job?.cancel(); job = null }
}
