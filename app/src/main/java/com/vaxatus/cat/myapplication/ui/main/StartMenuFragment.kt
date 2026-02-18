package com.vaxatus.cat.myapplication.ui.main

import android.os.Bundle
import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.ImageView
import androidx.fragment.app.Fragment
import com.vaxatus.cat.myapplication.*
import com.vaxatus.cat.myapplication.databinding.StartMenuFragmentBinding
import com.vaxatus.cat.myapplication.ui.logic.AdsController
import com.vaxatus.cat.myapplication.ui.logic.ImageHelper

class StartMenuFragment : Fragment(), OnAdLoadedInterface {
    private lateinit var adsController: AdsController
    private var _binding: StartMenuFragmentBinding? = null
    private val binding get() = _binding!!

    companion object {
        fun newInstance(): StartMenuFragment = StartMenuFragment()
    }

    override fun onCreateView(
        inflater: LayoutInflater,
        container: ViewGroup?,
        savedInstanceState: Bundle?
    ): View {
        _binding = StartMenuFragmentBinding.inflate(inflater, container, false)
        return binding.root
    }

    override fun onViewCreated(view: View, savedInstanceState: Bundle?) {
        super.onViewCreated(view, savedInstanceState)
        adsController = AdsController.getInstance(requireContext())
        val imageName = SharedPref.instance.getImagePath(requireActivity())
        binding.startMenuFragment.setImageDrawable(
            ImageHelper.getDrawable(requireContext(), String.format(Defaults.ASSETS_PATH_FULL, imageName))
        )
        binding.startMenuStart.setOnClickListener {
            parentFragmentManager.beginTransaction()
                .replace(R.id.container, MainFragment.newInstance(), Defaults.MAIN_FRAGMENT)
                .commitNow()
        }
        binding.startMenuOptions.setOnClickListener {
            OptionsPopup().show(parentFragmentManager, "nav_manage")
        }
        binding.startMenuDonate.visibility = if (adsController.isInterstitialLoaded(AdsController.INTERSTITIAL_AD_FULL)) {
            View.VISIBLE
        } else {
            View.INVISIBLE
        }
        adsController.setOnInterstitialAdLoaded(this)
        binding.startMenuDonate.setOnClickListener {
            adsController.showInterstitial(AdsController.INTERSTITIAL_AD_FULL)
            binding.startMenuDonate.visibility = View.INVISIBLE
        }
    }

    override fun onDestroyView() {
        _binding = null
        super.onDestroyView()
    }

    override fun loaded() {
        _binding?.startMenuDonate?.visibility = View.VISIBLE
    }

    override fun failedLoad() {
        _binding?.startMenuDonate?.visibility = View.INVISIBLE
    }
}
