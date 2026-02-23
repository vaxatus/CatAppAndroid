package com.vaxatus.cat.myapplication

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.view.Window
import android.view.WindowManager
import android.widget.GridView
import androidx.fragment.app.DialogFragment
import com.vaxatus.cat.myapplication.ui.logic.ImageHelper

class GridPopup : DialogFragment() {
    private var listener: OnItemBack? = null
    private var gridAdapter: ViewGridAdapter? = null

    override fun onCreateView(inflater: LayoutInflater, container: ViewGroup?, savedInstanceState: Bundle?): View {
        val myView = inflater.inflate(R.layout.img_gallery, container, false)
        val gridView = myView.findViewById<GridView>(R.id.catsGallery)
        gridAdapter = ViewGridAdapter(requireContext(), getCatsList()).also {
            it.setOnItemClick(clickHandler())
            gridView.adapter = it
        }
        dialog?.window?.requestFeature(Window.FEATURE_NO_TITLE)
        return myView
    }

    override fun onStart() {
        super.onStart()
        dialog?.window?.setLayout(
            WindowManager.LayoutParams.MATCH_PARENT,
            (resources.displayMetrics.heightPixels * 0.7f).toInt()
        )
    }

    override fun onDestroyView() {
        gridAdapter = null
        super.onDestroyView()
    }

    private fun clickHandler(): OnItemBack? = listener?.let { l ->
        object : OnItemBack {
            override fun onClickItem(drawableName: String?) {
                l.onClickItem(drawableName)
                dismiss()
            }
        }
    }

    fun setOnGridItemClick(listener: OnItemBack) {
        this.listener = listener
        gridAdapter?.setOnItemClick(clickHandler())
    }

    private fun getCatsList(): ArrayList<ImageItem> {
        val catsList = ArrayList<ImageItem>()
        val ctx = requireContext()
        val fallback = ctx.getDrawable(android.R.drawable.ic_menu_gallery)!!
        for (i in 0..Defaults.CATS_NUMBER) {
            val name = "cat$i"
            val drawable = try {
                ImageHelper.getDrawable(ctx, String.format(Defaults.ASSETS_PATH_MINI, name))
            } catch (_: Exception) {
                fallback
            }
            catsList.add(ImageItem(name, drawable))
        }
        return catsList
    }
}
