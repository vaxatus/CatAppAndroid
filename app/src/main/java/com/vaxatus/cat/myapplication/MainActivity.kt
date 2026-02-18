package com.vaxatus.cat.myapplication

import android.os.Bundle
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import android.view.*
import com.vaxatus.cat.myapplication.databinding.MainActivityBinding
import com.vaxatus.cat.myapplication.ui.logic.EffectsController
import com.vaxatus.cat.myapplication.ui.main.MainFragment
import com.vaxatus.cat.myapplication.ui.main.StartMenuFragment

class MainActivity : AppCompatActivity() {
    private lateinit var effectsController: EffectsController
    private lateinit var binding: MainActivityBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = MainActivityBinding.inflate(layoutInflater)
        setContentView(binding.root)
        window.addFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN)
        effectsController = EffectsController.getInstance(this)
        if (savedInstanceState == null) {
            supportFragmentManager.beginTransaction()
                .replace(R.id.container, StartMenuFragment.newInstance(), Defaults.START_FRAGMENT)
                .commitNow()
        }
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                val fragment = supportFragmentManager.findFragmentByTag(Defaults.MAIN_FRAGMENT) as? MainFragment
                if (fragment == null) {
                    isEnabled = false
                    onBackPressedDispatcher.onBackPressed()
                } else if (!fragment.closeDrawer()) {
                    supportFragmentManager.beginTransaction()
                        .replace(R.id.container, StartMenuFragment.newInstance(), Defaults.START_FRAGMENT)
                        .commitNow()
                }
            }
        })
    }

    override fun dispatchKeyEvent(event: KeyEvent?): Boolean {
        if (event == null) return super.dispatchKeyEvent(event)
        val action = event.action
        val keyCode = event.keyCode
        return when (keyCode) {
            KeyEvent.KEYCODE_VOLUME_UP -> {
                if (action == KeyEvent.ACTION_DOWN) {
                    effectsController.setVolumeUp()
                }
                true
            }
            KeyEvent.KEYCODE_VOLUME_DOWN -> {
                if (action == KeyEvent.ACTION_DOWN) {
                    effectsController.setVolumeDown()
                }
                true
            }
            else -> super.dispatchKeyEvent(event)
        }
    }
}
