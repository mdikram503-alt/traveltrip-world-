package com.traveleresim.app.data

object MockCatalog {
    val countries = listOf(
        Country("AE", "United Arab Emirates", "Asia", "AE", 4.99, true),
        Country("SA", "Saudi Arabia", "Asia", "SA", 5.49, true),
        Country("TR", "Turkey", "Asia", "TR", 3.99, true),
        Country("JP", "Japan", "Asia", "JP", 5.99, true),
        Country("TH", "Thailand", "Asia", "TH", 3.49, true),
        Country("GB", "United Kingdom", "Europe", "GB", 4.49, true),
        Country("FR", "France", "Europe", "FR", 4.49, true),
        Country("DE", "Germany", "Europe", "DE", 4.49, true),
        Country("IT", "Italy", "Europe", "IT", 4.49, true),
        Country("ES", "Spain", "Europe", "ES", 4.49, true),
        Country("US", "United States", "Americas", "US", 5.99, true),
        Country("BD", "Bangladesh", "Asia", "BD", 2.99, true),
        Country("IN", "India", "Asia", "IN", 2.99, true),
        Country("AU", "Australia", "Oceania", "AU", 6.49, true),
        Country("EG", "Egypt", "Africa", "EG", 4.49, true)
    )

    fun plansFor(code: String): List<Plan> {
        val base = countries.find { it.code == code }?.fromUsd ?: 4.99
        val name = countries.find { it.code == code }?.name ?: code
        val sizes = listOf(1 to 7, 3 to 15, 5 to 30, 10 to 30)
        return sizes.mapIndexed { i, (gb, days) ->
            Plan(
                id = "and-$code-$i",
                country = code,
                title = "$name $gb GB / $days days",
                gb = gb, days = days,
                usd = kotlin.math.round(base * Math.pow(gb.toDouble(), 0.72) * 100) / 100.0,
                hotspot = true, fiveG = true, type = "local"
            )
        }
    }
}
