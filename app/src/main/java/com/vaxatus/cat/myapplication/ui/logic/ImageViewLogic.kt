package com.vaxatus.cat.myapplication.ui.logic

import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.graphics.Bitmap
import android.graphics.Color
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.util.AttributeSet
import android.util.DisplayMetrics
import android.view.MotionEvent
import android.view.WindowManager
import android.widget.ImageView
import com.vaxatus.cat.myapplication.Defaults
import com.vaxatus.cat.myapplication.SharedPref

/**
 * ImageView that plays sound when the user touches the "cat" region.
 * Uses a mask bitmap (black = cat area) scaled to view size so touch coordinates
 * match mask pixels. Alternative approaches (Path hit-test, multiple regions) are
 * possible but mask is flexible for arbitrary shapes.
 */
class ImageViewLogic : ImageView {

    constructor(context: Context) : super(context)

    constructor(context: Context, attrs: AttributeSet) : super(context, attrs)

    constructor(context: Context, attrs: AttributeSet, defStyleAttr: Int) : super(context, attrs, defStyleAttr)

    private val effectsController: EffectsController = EffectsController.getInstance(context)
    private var isTouched = false
    private var catStarted = false
    /** Scaled to view size; used for hit-testing. Rebuilt in onSizeChanged and setImageName. */
    private var mask: Bitmap? = null
    /** Full-size mask from asset; scaled to view size when dimensions known. */
    private var sourceMaskBitmap: Bitmap? = null
    private val handler = Handler(Looper.getMainLooper())

    /** Consider pixel "cat" if it's black or very dark (masks may have antialiasing). */
    private fun isCatPixel(pixel: Int): Boolean {
        val a = Color.alpha(pixel)
        if (a < 128) return false
        val r = Color.red(pixel)
        val g = Color.green(pixel)
        val b = Color.blue(pixel)
        return r < 80 && g < 80 && b < 80
    }

    private fun updateScaledMask() {
        val src = sourceMaskBitmap ?: return
        val w = width
        val h = height
        if (w <= 0 || h <= 0) return
        mask = Bitmap.createScaledBitmap(src, w, h, false)
    }

    override fun onSizeChanged(w: Int, h: Int, oldW: Int, oldH: Int) {
        super.onSizeChanged(w, h, oldW, oldH)
        updateScaledMask()
    }

    init {
        val dm = DisplayMetrics()
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            (context.getSystemService(Context.WINDOW_SERVICE) as? WindowManager)?.currentWindowMetrics?.bounds?.let { bounds ->
                // Used only as fallback for initial load before onSizeChanged
            }
        }
        (context as? Activity)?.let { setImageName(SharedPref.instance.getImagePath(it)) }
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onTouchEvent(event: MotionEvent?): Boolean {
        if (event == null) return false
        val m = mask ?: return true
        val vw = width
        val vh = height
        if (vw <= 0 || vh <= 0) return true
        val x = event.x.toInt().coerceIn(0, vw - 1)
        val y = event.y.toInt().coerceIn(0, vh - 1)
        return when (event.action) {
            MotionEvent.ACTION_DOWN -> {
                if (isCatPixel(m.getPixel(x, y))) start()
                isTouched = true
                true
            }
            MotionEvent.ACTION_MOVE -> {
                if (isTouched) {
                    if (isCatPixel(m.getPixel(x, y))) start() else stop()
                }
                true
            }
            MotionEvent.ACTION_UP -> {
                handler.postDelayed({
                    if (!isTouched) stop()
                }, 200)
                isTouched = false
                true
            }
            else -> false
        }
    }

    private fun start() {
        if (!catStarted) {
            catStarted = true
            effectsController.stopCat()
            effectsController.startCat()
        }
    }

    private fun stop() {
        if (catStarted) {
            effectsController.stopCat()
            catStarted = false
        }
    }

    fun setImageName(imageName: String?) {
        val name = imageName ?: Defaults.DEFAULT_CAT
        val activity = context as? Activity ?: return
        SharedPref.instance.saveImagePath(activity, name)
        setImageDrawable(ImageHelper.getDrawable(context, String.format(Defaults.ASSETS_PATH_FULL, name)))
        sourceMaskBitmap = ImageHelper.getBitmap(context, String.format(Defaults.ASSETS_PATH_MASK, name))
        updateScaledMask()
    }
}
