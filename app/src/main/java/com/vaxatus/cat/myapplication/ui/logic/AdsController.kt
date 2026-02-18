package com.vaxatus.cat.myapplication.ui.logic

import android.content.Context
import android.view.View
import com.google.android.gms.ads.AdRequest
import com.google.android.gms.ads.AdView
import com.google.android.gms.ads.LoadAdError
import com.google.android.gms.ads.MobileAds
import com.google.android.gms.ads.interstitial.InterstitialAd
import com.google.android.gms.ads.interstitial.InterstitialAdLoadCallback
import com.vaxatus.cat.myapplication.OnAdLoadedInterface
import com.vaxatus.cat.myapplication.R
import com.vaxatus.cat.myapplication.SingletonHolder

class AdsController private constructor(private val context: Context) {

    private var mInterstitialAdFull: InterstitialAd? = null
    private var mInterstitialAdVideo: InterstitialAd? = null

    companion object : SingletonHolder<AdsController, Context>(::AdsController) {
        const val INTERSTITIAL_AD_FULL = "mInterstitialAdFull"
        const val INTERSTITIAL_AD_VIDEO = "mInterstitialAdVideo"
    }

    init {
        MobileAds.initialize(context) {
            loadInterstitialFull()
            loadInterstitialVideo()
        }
    }

    private fun loadInterstitialFull() {
        InterstitialAd.load(
            context,
            context.getString(R.string.full_video_ad),
            AdRequest.Builder().build(),
            object : InterstitialAdLoadCallback() {
                override fun onAdLoaded(ad: InterstitialAd) {
                    mInterstitialAdFull = ad
                    ad.fullScreenContentCallback = object : com.google.android.gms.ads.FullScreenContentCallback() {
                        override fun onAdDismissedFullScreenContent() {
                            mInterstitialAdFull = null
                            loadInterstitialFull()
                        }
                    }
                }
                override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                    mInterstitialAdFull = null
                }
            }
        )
    }

    private fun loadInterstitialVideo() {
        InterstitialAd.load(
            context,
            context.getString(R.string.full_ad),
            AdRequest.Builder().build(),
            object : InterstitialAdLoadCallback() {
                override fun onAdLoaded(ad: InterstitialAd) {
                    mInterstitialAdVideo = ad
                    ad.fullScreenContentCallback = object : com.google.android.gms.ads.FullScreenContentCallback() {
                        override fun onAdDismissedFullScreenContent() {
                            mInterstitialAdVideo = null
                            loadInterstitialVideo()
                        }
                    }
                }
                override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                    mInterstitialAdVideo = null
                }
            }
        )
    }

    fun setOnInterstitialAdLoaded(onAdLoadedInterface: OnAdLoadedInterface) {
        // Re-load full interstitial and notify when loaded
        InterstitialAd.load(
            context,
            context.getString(R.string.full_video_ad),
            AdRequest.Builder().build(),
            object : InterstitialAdLoadCallback() {
                override fun onAdLoaded(ad: InterstitialAd) {
                    mInterstitialAdFull = ad
                    ad.fullScreenContentCallback = object : com.google.android.gms.ads.FullScreenContentCallback() {
                        override fun onAdDismissedFullScreenContent() {
                            mInterstitialAdFull = null
                            loadInterstitialFull()
                        }
                    }
                    onAdLoadedInterface.loaded()
                }
                override fun onAdFailedToLoad(loadAdError: LoadAdError) {
                    mInterstitialAdFull = null
                    onAdLoadedInterface.failedLoad()
                }
            }
        )
    }

    fun setMainAds(view: View) {
        val mAdView = view.findViewById<AdView>(R.id.adView)
        mAdView.loadAd(AdRequest.Builder().build())
    }

    fun setOptionsAds(view: View) {
        val navAdView = view.findViewById<AdView>(R.id.optionsAdView)
        navAdView.loadAd(AdRequest.Builder().build())
    }

    fun isInterstitialLoaded(adName: String): Boolean = when (adName) {
        INTERSTITIAL_AD_FULL -> mInterstitialAdFull != null
        INTERSTITIAL_AD_VIDEO -> mInterstitialAdVideo != null
        else -> false
    }

    fun showInterstitial(adName: String) {
        val activity = context as? android.app.Activity ?: return
        when (adName) {
            INTERSTITIAL_AD_FULL -> mInterstitialAdFull?.show(activity)
            INTERSTITIAL_AD_VIDEO -> mInterstitialAdVideo?.show(activity)
        }
    }
}
