package com.vaxatus.cat.myapplication

import android.annotation.SuppressLint
import android.content.Context
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.BaseAdapter
import com.vaxatus.cat.myapplication.databinding.ImgItemBinding

class ViewGridAdapter(context: Context, var imageList: ArrayList<ImageItem>) : BaseAdapter() {
    var context: Context? = context
    var listener: OnItemBack? = null

    override fun getCount(): Int = imageList.size
    override fun getItem(position: Int): Any = imageList[position]
    override fun getItemId(position: Int): Long = position.toLong()

    @SuppressLint("ViewHolder", "InflateParams")
    override fun getView(position: Int, convertView: View?, parent: ViewGroup?): View {
        val item = imageList[position]
        val ctx = requireNotNull(context)
        val inflater = ctx.getSystemService(Context.LAYOUT_INFLATER_SERVICE) as LayoutInflater
        val itemBinding = ImgItemBinding.inflate(inflater, parent, false)
        itemBinding.itemImg.setImageDrawable(
            item.image ?: ctx.getDrawable(android.R.drawable.ic_menu_gallery)
        )
        itemBinding.root.setOnClickListener { listener?.onClickItem(item.name) }
        return itemBinding.root
    }

    fun setOnItemClick(listener: OnItemBack?) {
        this.listener = listener
    }
}
