package com.vaxatus.cat.myapplication

import android.Manifest
import android.app.Activity
import android.content.ContentValues
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.net.Uri
import android.provider.MediaStore
import android.widget.Toast
import android.content.pm.PackageManager
import androidx.core.app.ActivityCompat
import com.vaxatus.cat.myapplication.ui.logic.ImageHelper

class ImageController(private val context: Context) {
    private var mImageUri: Uri? = null

    companion object {
        private const val REQUEST_TAKE_PHOTO = 0
        private const val REQUEST_SELECT_IMAGE_IN_ALBUM = 1
        private const val REQUEST_CAMERA = 2
    }

    fun selectImageInAlbum() {
        val intent = Intent().apply {
            type = "image/*"
            action = Intent.ACTION_GET_CONTENT
        }
        ActivityCompat.startActivityForResult(
            context as Activity,
            Intent.createChooser(intent, "Select Picture"),
            REQUEST_SELECT_IMAGE_IN_ALBUM,
            null
        )
    }

    fun takePhoto() {
        val activity = context as Activity
        if (ActivityCompat.checkSelfPermission(activity, Manifest.permission.WRITE_EXTERNAL_STORAGE) != PackageManager.PERMISSION_GRANTED ||
            ActivityCompat.checkSelfPermission(activity, Manifest.permission.CAMERA) != PackageManager.PERMISSION_GRANTED
        ) {
            ActivityCompat.requestPermissions(
                activity,
                arrayOf(Manifest.permission.WRITE_EXTERNAL_STORAGE, Manifest.permission.CAMERA),
                REQUEST_CAMERA
            )
        } else {
            startCamera()
        }
    }

    private fun startCamera() {
        val filename = "${System.currentTimeMillis()}.jpg"
        val values = ContentValues().apply {
            put(MediaStore.MediaColumns.TITLE, filename)
            put(MediaStore.MediaColumns.MIME_TYPE, "image/jpeg")
        }
        mImageUri = context.contentResolver?.insert(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, values)
        val intent = Intent(MediaStore.ACTION_IMAGE_CAPTURE).apply {
            putExtra(MediaStore.EXTRA_OUTPUT, mImageUri)
        }
        ActivityCompat.startActivityForResult(context as Activity, intent, REQUEST_TAKE_PHOTO, null)
    }

    fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?): Bitmap? {
        if (requestCode == REQUEST_SELECT_IMAGE_IN_ALBUM && resultCode == Activity.RESULT_OK) {
            return data?.data?.let { getAlbumBitmap(it) }
        }
        if (requestCode == REQUEST_TAKE_PHOTO && resultCode == Activity.RESULT_OK) {
            return getPhotoBitmap()
        }
        return null
    }

    private fun getAlbumBitmap(uri: Uri): Bitmap? = ImageHelper.getBitmapFromUri(context, uri)

    private fun getPhotoBitmap(): Bitmap? {
        val uri = mImageUri ?: return null
        return ImageHelper.getBitmapFromUri(context, uri)
    }

    fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        if (requestCode == REQUEST_CAMERA) {
            if (grantResults.isNotEmpty() && grantResults[0] == PackageManager.PERMISSION_GRANTED) {
                startCamera()
            } else {
                Toast.makeText(context, R.string.camera_permission_denied, Toast.LENGTH_SHORT).show()
            }
        }
    }
}
