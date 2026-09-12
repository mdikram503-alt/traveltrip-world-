package com.traveleresim.app.domain

import com.traveleresim.app.core.AppResult
import com.traveleresim.app.data.EsimRepository
import com.traveleresim.app.data.Order
import com.traveleresim.app.data.Plan

class BuyPlan(private val repo: EsimRepository = EsimRepository()) {
    suspend operator fun invoke(plan: Plan, email: String): AppResult<Order> = repo.checkout(plan, email)
}
