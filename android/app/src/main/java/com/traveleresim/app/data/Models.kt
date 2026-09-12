package com.traveleresim.app.data

data class Country(
    val code: String,
    val name: String,
    val region: String,
    val flag: String,
    val fromUsd: Double,
    val fiveG: Boolean
)

data class Plan(
    val id: String,
    val country: String,
    val title: String,
    val gb: Int,
    val days: Int,
    val usd: Double,
    val hotspot: Boolean,
    val fiveG: Boolean,
    val type: String
)

data class Order(
    val id: String,
    val planId: String,
    val email: String,
    val usd: Double,
    val status: String,
    val activation: String
)
