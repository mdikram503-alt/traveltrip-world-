package com.traveleresim.app.ui

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.unit.dp
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewmodel.compose.viewModel
import com.traveleresim.app.core.AppResult
import com.traveleresim.app.data.Country
import com.traveleresim.app.data.EsimRepository
import com.traveleresim.app.data.Order
import com.traveleresim.app.data.Plan
import com.traveleresim.app.esim.DemoEuicc
import kotlinx.coroutines.launch

class CatalogVm : ViewModel() {
    private val repo = EsimRepository()
    val countries = repo.countries()
    fun plans(code: String) = repo.plans(code)
    suspend fun buy(plan: Plan, email: String) = repo.checkout(plan, email)
}

sealed class Screen {
    data object Home : Screen()
    data class Plans(val country: Country) : Screen()
    data class Pay(val plan: Plan) : Screen()
    data class Done(val order: Order) : Screen()
    data object Help : Screen()
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TravelerRoot(vm: CatalogVm = viewModel()) {
    var screen by remember { mutableStateOf<Screen>(Screen.Home) }
    var query by remember { mutableStateOf("") }
    val ctx = LocalContext.current

    Scaffold(topBar = {
        TopAppBar(title = { Text(when (val s = screen) {
            Screen.Home -> "Traveler eSIM"
            is Screen.Plans -> s.country.name
            is Screen.Pay -> "Checkout"
            is Screen.Done -> "Install"
            Screen.Help -> "Help"
        }) })
    }) { pad ->
        Box(Modifier.padding(pad).fillMaxSize()) {
            when (val s = screen) {
                Screen.Home -> {
                    val list = vm.countries.filter {
                        query.isBlank() || it.name.contains(query, true) || it.code.contains(query, true)
                    }
                    Column(Modifier.fillMaxSize()) {
                        OutlinedTextField(
                            value = query, onValueChange = { query = it },
                            modifier = Modifier.fillMaxWidth().padding(16.dp),
                            placeholder = { Text("Search destinations") }
                        )
                        LazyColumn {
                            items(list) { c ->
                                ListItem(
                                    headlineContent = { Text(c.name) },
                                    supportingContent = { Text("${c.region} · from $${c.fromUsd}") },
                                    modifier = Modifier.clickable { screen = Screen.Plans(c) }
                                )
                                HorizontalDivider()
                            }
                        }
                    }
                }
                is Screen.Plans -> {
                    LazyColumn {
                        items(vm.plans(s.country.code)) { p ->
                            ListItem(
                                headlineContent = { Text(p.title) },
                                supportingContent = { Text("$${p.usd} · hotspot · ${p.days} days") },
                                trailingContent = { TextButton(onClick = { screen = Screen.Pay(p) }) { Text("Buy") } }
                            )
                            HorizontalDivider()
                        }
                    }
                }
                is Screen.Pay -> {
                    var email by remember { mutableStateOf("") }
                    var busy by remember { mutableStateOf(false) }
                    var err by remember { mutableStateOf<String?>(null) }
                    val scope = rememberCoroutineScope()
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text(s.plan.title, style = MaterialTheme.typography.titleLarge)
                        Text("$${s.plan.usd} · demo Stripe, no live key")
                        OutlinedTextField(email, { email = it }, label = { Text("Email") }, modifier = Modifier.fillMaxWidth())
                        err?.let { Text(it, color = MaterialTheme.colorScheme.error) }
                        Button(enabled = !busy, onClick = {
                            busy = true
                            scope.launch {
                                when (val r = vm.buy(s.plan, email)) {
                                    is AppResult.Ok -> screen = Screen.Done(r.value)
                                    is AppResult.Err -> err = r.message
                                }
                                busy = false
                            }
                        }, modifier = Modifier.fillMaxWidth()) { Text(if (busy) "Paying…" else "Pay mock") }
                    }
                }
                is Screen.Done -> {
                    Column(Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
                        Text("Paid ${s.order.id}", style = MaterialTheme.typography.titleLarge)
                        Text(s.order.activation)
                        Text("Install over Wi-Fi before you fly. This build opens system network settings — wire EuiccManager when you have SM-DP+ credentials.")
                        Button(onClick = { DemoEuicc.openSystemEsimSettings(ctx) }) { Text("Open eSIM settings") }
                        TextButton(onClick = { screen = Screen.Home }) { Text("Back home") }
                    }
                }
                Screen.Help -> Text("Keep your physical SIM for WhatsApp. Traveler eSIM is data-only.", Modifier.padding(16.dp))
            }
        }
    }
}
