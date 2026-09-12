package com.traveleresim.app.data

import com.traveleresim.app.core.AppResult
import kotlinx.coroutines.delay

class EsimRepository {
    fun countries(): List<Country> = MockCatalog.countries
    fun plans(code: String): List<Plan> = MockCatalog.plansFor(code)

    suspend fun checkout(plan: Plan, email: String): AppResult<Order> {
        delay(600)
        if (!email.contains("@")) return AppResult.Err("Valid email required")
        val id = "ord" + (100000..999999).random()
        return AppResult.Ok(
            Order(
                id = id,
                planId = plan.id,
                email = email,
                usd = plan.usd,
                status = "PAID",
                activation = "LPA:1$" + "smdp.traveleresim.example$" + id.uppercase()
            )
        )
    }
}
