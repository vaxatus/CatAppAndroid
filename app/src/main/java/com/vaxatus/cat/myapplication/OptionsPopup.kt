package com.vaxatus.cat.myapplication

import android.app.Activity
import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.Window
import android.widget.CheckBox
import android.widget.CompoundButton
import androidx.fragment.app.DialogFragment

class OptionsPopup : DialogFragment() {
    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val myView = inflater.inflate(R.layout.options_popup, container, false)
        val vibrationCheckbox = myView.findViewById<CheckBox>(R.id.vibration_checkbox)
        dialog?.window?.requestFeature(Window.FEATURE_NO_TITLE)
        vibrationCheckbox.isChecked = SharedPref.instance.getVibration(requireActivity() as Activity)
        vibrationCheckbox.setOnCheckedChangeListener { _: CompoundButton, b: Boolean ->
            SharedPref.instance.saveVibration(requireActivity() as Activity, b)
        }
        return myView
    }
}
