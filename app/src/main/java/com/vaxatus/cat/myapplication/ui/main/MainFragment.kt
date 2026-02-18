package com.vaxatus.cat.myapplication.ui.main

import android.annotation.SuppressLint
import android.content.Context
import android.content.Intent
import android.graphics.Bitmap
import android.graphics.drawable.BitmapDrawable
import android.os.Bundle
import android.view.*
import androidx.fragment.app.Fragment
import androidx.lifecycle.ViewModelProvider
import com.google.android.material.navigation.NavigationView
import com.vaxatus.cat.myapplication.*
import com.vaxatus.cat.myapplication.databinding.MainFragmentBinding
import com.vaxatus.cat.myapplication.ui.logic.AdsController
import com.vaxatus.cat.myapplication.ui.logic.EffectsController
import com.vaxatus.cat.myapplication.ui.logic.ImageViewLogic
import androidx.core.view.GravityCompat
import androidx.drawerlayout.widget.DrawerLayout

class MainFragment : Fragment(), OnItemBack, NavigationView.OnNavigationItemSelectedListener {

    private lateinit var catImageView: ImageViewLogic
    private lateinit var imageController: ImageController
    private lateinit var viewModel: MainViewModel
    private lateinit var adsController: AdsController
    private lateinit var effectsController: EffectsController
    private var _binding: MainFragmentBinding? = null
    private val binding get() = _binding!!

    companion object {
        fun newInstance(): MainFragment = MainFragment()
    }

    override fun onAttach(context: Context) {
        super.onAttach(context)
        imageController = ImageController(context)
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = MainFragmentBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: android.view.View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        viewModel = ViewModelProvider(this)[MainViewModel::class.java]
        effectsController = EffectsController.getInstance(requireContext())
        adsController = AdsController.getInstance(requireContext())
        adsController.setMainAds(binding.root)

        catImageView = binding.root.findViewById(R.id.imageView)
        binding.root.findViewById<android.widget.Button>(R.id.optionsButton).setOnClickListener {
            if (!binding.drawerLayout.isDrawerOpen(GravityCompat.START)) {
                binding.drawerLayout.openDrawer(GravityCompat.START)
            }
        }

        binding.drawerLayout.setDrawerLockMode(DrawerLayout.LOCK_MODE_LOCKED_CLOSED)
        binding.navView.setNavigationItemSelectedListener(this)
        binding.drawerLayout.addDrawerListener(
            object : DrawerLayout.DrawerListener {
                override fun onDrawerSlide(drawerView: View, slideOffset: Float) {}
                override fun onDrawerOpened(drawerView: View) {
                    adsController.setOptionsAds(drawerView)
                    binding.navView.menu.findItem(R.id.nav_interstitial).isVisible =
                        adsController.isInterstitialLoaded(AdsController.INTERSTITIAL_AD_VIDEO)
                }
                override fun onDrawerClosed(drawerView: View) {}
                override fun onDrawerStateChanged(newState: Int) {}
            }
        )
    }

    override fun onDestroyView() {
        _binding = null
        super.onDestroyView()
    }

    @SuppressLint("ClickableViewAccessibility")
    override fun onActivityResult(requestCode: Int, resultCode: Int, data: Intent?) {
        super.onActivityResult(requestCode, resultCode, data)
        val bp: Bitmap? = imageController.onActivityResult(requestCode, resultCode, data)
        if (bp != null && _binding != null) {
            catImageView.setImageDrawable(BitmapDrawable(resources, bp))
        }
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        imageController.onRequestPermissionsResult(requestCode, permissions, grantResults)
    }

    override fun onClickItem(drawableName: String?) {
        catImageView.setImageName(drawableName)
    }

    override fun onPause() {
        effectsController.stopCat()
        super.onPause()
    }

    override fun onStop() {
        effectsController.stopCat()
        super.onStop()
    }

    override fun onNavigationItemSelected(item: MenuItem): Boolean {
        when (item.itemId) {
            R.id.nav_slideshow -> showGridPopup()
            R.id.nav_interstitial -> adsController.showInterstitial(AdsController.INTERSTITIAL_AD_VIDEO)
            R.id.nav_manage -> OptionsPopup().show(parentFragmentManager, "nav_manage")
        }
        binding.drawerLayout.closeDrawer(GravityCompat.START)
        return true
    }

    private fun showGridPopup() {
        val pop = GridPopup()
        pop.show(parentFragmentManager, "nav_slideshow")
        pop.setOnGridItemClick(this)
    }

    fun closeDrawer(): Boolean {
        val b = _binding ?: return false
        return if (b.drawerLayout.isDrawerOpen(GravityCompat.START)) {
            b.drawerLayout.closeDrawer(GravityCompat.START)
            true
        } else {
            false
        }
    }
}
