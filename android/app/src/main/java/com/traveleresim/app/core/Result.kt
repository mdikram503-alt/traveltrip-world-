package com.traveleresim.app.core

sealed class AppResult<out T> {
    data class Ok<T>(val value: T) : AppResult<T>()
    data class Err(val message: String) : AppResult<Nothing>()
}
