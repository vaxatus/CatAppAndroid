package com.vaxatus.cat.myapplication

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.Window
import android.widget.GridView
import androidx.fragment.app.DialogFragment
import com.vaxatus.cat.myapplication.ui.logic.ImageHelper

class GridPopup : DialogFragment() {
    private var listener: OnItemBack? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val myView = inflater.inflate(R.layout.img_gallery, container, false)
        val gridView = myView.findViewById<GridView>(R.id.catsGallery)
        val adapter = ViewGridAdapter(requireContext(), getCatsList())
        adapter.setOnItemClick(listener)
        gridView.adapter = adapter
        dialog?.window?.requestFeature(Window.FEATURE_NO_TITLE)
        return myView
    }

    fun setOnGridItemClick(listener: OnItemBack) {
        this.listener = listener
    }

    private fun getCatsList(): ArrayList<ImageItem> {
        val catsList = ArrayList<ImageItem>()
        for (i in 0..Defaults.CATS_NUMBER) {
            val name = "cat$i"
            catsList.add(ImageItem(name, ImageHelper.getDrawable(requireContext(), String.format(Defaults.ASSETS_PATH_MINI, name))))
        }
        return catsList
    }
}
