package com.vaxatus.cat.myapplication.ui.logic

import android.content.Context
import android.graphics.Bitmap
import android.graphics.BitmapFactory
import android.graphics.drawable.Drawable
import android.net.Uri
import android.widget.Toast
import java.io.InputStream

class ImageHelper {
    companion object {
        fun getDrawable(context: Context, name: String?): Drawable {
            val n = name ?: return context.getDrawable(android.R.drawable.ic_menu_gallery)!!
            val ims: InputStream = context.assets.open(n)
            return Drawable.createFromStream(ims, null) ?: context.getDrawable(android.R.drawable.ic_menu_gallery)!!
        }
        fun getBitmap(context: Context, name: String?): Bitmap {
            val n = name ?: throw IllegalArgumentException("name is null")
            val ims: InputStream = context.assets.open(n)
            return BitmapFactory.decodeStream(ims) ?: throw IllegalArgumentException("Failed to decode bitmap")
        }
        fun getBitmapFromUri(context: Context, uri: Uri): Bitmap? {
            return context.contentResolver.openInputStream(uri)?.use { ins ->
                BitmapFactory.decodeStream(ins)
            } ?: run {
                Toast.makeText(context, "error!", Toast.LENGTH_SHORT).show()
                null
            }
        }
    }
}