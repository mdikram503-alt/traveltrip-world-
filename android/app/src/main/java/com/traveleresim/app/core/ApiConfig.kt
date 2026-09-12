package com.traveleresim.app.core

import com.traveleresim.app.BuildConfig

object ApiConfig {
    val baseUrl: String = BuildConfig.API_BASE
    val stripePk: String = BuildConfig.STRIPE_PK
    const val USE_MOCK: Boolean = true
}
