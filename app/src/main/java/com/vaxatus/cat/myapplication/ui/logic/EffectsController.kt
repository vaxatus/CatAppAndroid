package com.vaxatus.cat.myapplication.ui.logic

import android.app.Activity
import android.content.Context
import android.media.AudioManager
import android.media.MediaPlayer
import android.os.Build
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import com.vaxatus.cat.myapplication.R
import com.vaxatus.cat.myapplication.SharedPref
import com.vaxatus.cat.myapplication.SingletonHolder

class EffectsController private constructor(private val context: Context) {

    private var music: MediaPlayer? = null
    private val vibrator: Vibrator? = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.S) {
        (context.getSystemService(Context.VIBRATOR_MANAGER_SERVICE) as? VibratorManager)?.defaultVibrator
    } else {
        @Suppress("DEPRECATION")
        context.getSystemService(Context.VIBRATOR_SERVICE) as? Vibrator
    }
    private val audio: AudioManager? = context.getSystemService(Context.AUDIO_SERVICE) as? AudioManager

    companion object : SingletonHolder<EffectsController, Context>(::EffectsController)

    internal fun startCat() {
        startVibrate()
        cancelMusic()
        music = MediaPlayer.create(context, R.raw.mrr1)
        music?.isLooping = true
        music?.start()
    }

    private fun cancelMusic() {
        if (music?.isPlaying == true) {
            music?.stop()
            music?.release()
            music = null
        }
    }

    internal fun stopCat() {
        cancelMusic()
        if (context is Activity && SharedPref.instance.getVibration(context)) {
            vibrator?.cancel()
        }
    }

    private fun startVibrate() {
        if (context !is Activity || !SharedPref.instance.getVibration(context)) return
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            vibrator?.vibrate(VibrationEffect.createOneShot(100, VibrationEffect.DEFAULT_AMPLITUDE))
        } else {
            @Suppress("DEPRECATION")
            vibrator?.vibrate(100)
        }
    }

    internal fun setVolumeUp() {
        audio?.adjustStreamVolume(
            AudioManager.STREAM_MUSIC,
            AudioManager.ADJUST_RAISE,
            AudioManager.FLAG_SHOW_UI
        )
    }

    internal fun setVolumeDown() {
        audio?.adjustStreamVolume(
            AudioManager.STREAM_MUSIC,
            AudioManager.ADJUST_LOWER,
            AudioManager.FLAG_SHOW_UI
        )
    }
}