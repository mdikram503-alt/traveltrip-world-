package com.traveleresim.app.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val Teal = Color(0xFF3EE0C5)
private val Night = Color(0xFF0B1220)
private val Card = Color(0xFF172033)

@Composable
fun TravelerTheme(content: @Composable () -> Unit) {
    val dark = isSystemInDarkTheme()
    val colors = if (dark) darkColorScheme(
        primary = Teal, background = Night, surface = Card, onPrimary = Color(0xFF06221C)
    ) else lightColorScheme(primary = Color(0xFF0B8F7A))
    MaterialTheme(colorScheme = colors, content = content)
}
