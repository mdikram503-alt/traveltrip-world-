package com.traveleresim.app.esim

import android.content.Context
import android.content.Intent
import android.provider.Settings

/**
 * Production path: EuiccManager.downloadSubscription(...) with an
 * activation code from your SM-DP+ partner. That needs carrier
 * privileges or an LPA implementation — not bundled here.
 */
object DemoEuicc {
    fun openSystemEsimSettings(context: Context) {
        val intent = Intent(Settings.ACTION_WIRELESS_SETTINGS)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        context.startActivity(intent)
    }
}
