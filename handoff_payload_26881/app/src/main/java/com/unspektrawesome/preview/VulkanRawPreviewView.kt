package com.unspektrawesome.preview

import android.content.Context
import android.util.AttributeSet
import android.view.SurfaceHolder
import android.view.SurfaceView
import android.view.ViewGroup
import kotlin.math.min
import androidx.lifecycle.LifecycleOwner

/** SurfaceView host suitable for Compose AndroidView and traditional view hierarchies. */
class VulkanRawPreviewView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
) : SurfaceView(context, attrs), SurfaceHolder.Callback {
    private var controller: RawVulkanPreviewController? = null
    private var lifecycleOwner: LifecycleOwner? = null

    init {
        holder.addCallback(this)
    }

    fun bind(controller: RawVulkanPreviewController, lifecycleOwner: LifecycleOwner) {
        if (this.controller === controller && this.lifecycleOwner === lifecycleOwner) return
        unbind()
        this.controller = controller
        this.lifecycleOwner = lifecycleOwner
        // IRIS_26881_SPEKTRA_TRUE_FOV_ASPECT_FIT:
        // The native renderer receives a Surface with the oriented RAW
        // image's ratio. No aspect-fill cropping of the left/right sides.
        controller.setAspectFitListener26881 { sourceW, sourceH ->
            if (sourceW <= 0 || sourceH <= 0) return@setAspectFitListener26881
            post {
                if (this.controller !== controller || !isAttachedToWindow) return@post
                val host = parent as? ViewGroup ?: return@post
                val availableW = host.width
                val availableH = host.height
                if (availableW <= 0 || availableH <= 0) return@post
                val fittedW = min(availableW.toDouble(),
                    availableH.toDouble() * sourceW / sourceH).toInt().coerceAtLeast(1)
                val fittedH = min(availableH.toDouble(),
                    fittedW.toDouble() * sourceH / sourceW).toInt().coerceAtLeast(1)
                val current = layoutParams ?: return@post
                if (current.width != fittedW || current.height != fittedH) {
                    current.width = fittedW
                    current.height = fittedH
                    layoutParams = current
                }
            }
        }
        lifecycleOwner.lifecycle.addObserver(controller)
        if (holder.surface.isValid) {
            controller.updateViewport(width, height)
            controller.attachSurface(holder.surface)
        }
    }

    fun unbind() {
        controller?.setAspectFitListener26881(null)
        controller?.detachSurface(holder.surface)
        lifecycleOwner?.lifecycle?.removeObserver(controller ?: return)
        controller = null
        lifecycleOwner = null
    }

    override fun surfaceCreated(holder: SurfaceHolder) {
        controller?.updateViewport(width, height)
        controller?.attachSurface(holder.surface)
    }

    override fun surfaceChanged(holder: SurfaceHolder, format: Int, width: Int, height: Int) {
        if (width > 0 && height > 0) {
            controller?.updateViewport(width, height)
            controller?.attachSurface(holder.surface)
        }
    }

    override fun surfaceDestroyed(holder: SurfaceHolder) {
        controller?.detachSurface(holder.surface)
    }

    override fun onDetachedFromWindow() {
        controller?.detachSurface(holder.surface)
        super.onDetachedFromWindow()
    }
}
