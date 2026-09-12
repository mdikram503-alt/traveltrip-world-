package com.traveleresim.app

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.activity.enableEdgeToEdge
import com.traveleresim.app.ui.TravelerRoot
import com.traveleresim.app.ui.theme.TravelerTheme

class MainActivity : ComponentActivity() {
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        enableEdgeToEdge()
        setContent { TravelerTheme { TravelerRoot() } }
    }
}
