package com.vaxatus.cat.myapplication

import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.isDisplayed
import androidx.test.espresso.matcher.ViewMatchers.withText
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Rule
import org.junit.Test
import org.junit.runner.RunWith

/**
 * UI automation tests for MainActivity and start flow.
 * Run on device/emulator: ./gradlew connectedDebugAndroidTest
 */
@RunWith(AndroidJUnit4::class)
class MainActivityUiTest {

    @get:Rule
    val activityRule = ActivityScenarioRule(MainActivity::class.java)

    @Test
    fun launchApp_showsStartMenu() {
        onView(withText("Start"))
            .check(matches(isDisplayed()))
    }

    @Test
    fun launchApp_showsAppName() {
        onView(withText("Purring Kittens"))
            .check(matches(isDisplayed()))
    }

    @Test
    fun launchApp_showsOptionsButton() {
        onView(withText("Options"))
            .check(matches(isDisplayed()))
    }
}
