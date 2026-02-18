package com.vaxatus.cat.myapplication

import android.app.Activity
import android.content.Context


class SharedPref private constructor() {
    private object Holder { val INSTANCE = SharedPref() }
    private val KEY_IMAGE_PATH = "imagePath"
    private val KEY_VIBRATION = "vibration"

    companion object {
        val instance: SharedPref by lazy { Holder.INSTANCE }
    }

    fun getImagePath(activity: Activity): String {
        val sharedPref = activity.getPreferences(Context.MODE_PRIVATE)
        val path = sharedPref.getString(KEY_IMAGE_PATH, Defaults.DEFAULT_CAT) ?: Defaults.DEFAULT_CAT
        if (path.contains("/")) {
            saveImagePath(activity, Defaults.DEFAULT_CAT)
            return Defaults.DEFAULT_CAT
        }
        return path
    }
    fun saveImagePath(activity: Activity, path: String) {
        val sharedPref = activity.getPreferences(Context.MODE_PRIVATE)
        sharedPref.edit().putString(KEY_IMAGE_PATH, path).apply()
    }
    fun saveVibration(activity: Activity, vibration: Boolean) {
        val sharedPref = activity.getPreferences(Context.MODE_PRIVATE)
        sharedPref.edit().putBoolean(KEY_VIBRATION, vibration).apply()
    }
    fun getVibration(activity: Activity): Boolean {
        val sharedPref = activity.getPreferences(Context.MODE_PRIVATE)
        return sharedPref.getBoolean(KEY_VIBRATION, true)
    }
}