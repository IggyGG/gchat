package boo.gchat.app.mobileplatform

import android.Manifest
import android.os.Build
import android.content.Intent
import android.app.Activity
import android.util.Log
import android.webkit.WebView
import app.tauri.annotation.Permission
import app.tauri.annotation.PermissionCallback
import app.tauri.annotation.Command
import app.tauri.annotation.InvokeArg
import app.tauri.annotation.TauriPlugin
import app.tauri.plugin.Invoke
import app.tauri.plugin.JSObject
import app.tauri.plugin.Plugin
import org.json.JSONObject
import java.util.concurrent.Executors

@InvokeArg
class SlotArgs { var slot: String = "" }

@InvokeArg
class StoreArgs {
    var slot: String = ""
    var secret: String = ""
    var confirmed: Boolean = false
}

@InvokeArg
class PushArgs { var enabled: Boolean? = null }

@TauriPlugin(permissions = [Permission(strings = [Manifest.permission.POST_NOTIFICATIONS], alias = "notifications")])
class MobilePlatformPlugin(private val activity: Activity) : Plugin(activity) {
    private val vault = UnlockVault(activity)
    private val permissionRequests = java.util.concurrent.ConcurrentHashMap<Invoke, Long>()

    companion object {
        // A process-wide serial worker preserves store/delete order, including
        // activity recreation. Keystore and filesystem work never blocks UI.
        private val worker = Executors.newSingleThreadExecutor { task ->
            Thread(task, "gchat-unlock-vault").apply { isDaemon = true }
        }
    }

    // Tauri has already loaded the GChat native library before registering this plugin.
    private external fun nativeLifecycle(state: Int)

    private val lifecycleTarget = ProcessLifecycleTarget { state ->
        Log.i("GChatLifecycle", if (state == 1) "process foreground" else "process background")
        nativeLifecycle(state)
    }

    override fun load(webView: WebView) {
        super.load(webView)
        PushNotifications.consumeIntent(activity.intent)
        // Tauri 2.11.5 defines its process observer but does not register it.
        // Bind directly instead of relying on unconnected Plugin lifecycle hooks.
        // ProcessLifecycleOwner debounces configuration recreation itself.
        activity.runOnUiThread { ProcessLifecycleBridge.bind(lifecycleTarget) }
    }

    override fun onNewIntent(intent: Intent) { PushNotifications.consumeIntent(intent) }

    @Command
    fun pushDevice(invoke: Invoke) {
        val args = try { invoke.parseArgs(PushArgs::class.java) } catch (_: Exception) {
            invoke.reject("Invalid notification request", "INVALID_ARGUMENT"); return
        }
        if (args.enabled == true && Build.VERSION.SDK_INT >= 33 && !PushNotifications.granted(activity)) {
            permissionRequests[invoke] = PushNotifications.beginPermission()
            requestPermissionForAlias("notifications", invoke, "pushPermissionResult")
            return
        }
        completePush(invoke, args.enabled)
    }

    @PermissionCallback
    fun pushPermissionResult(invoke: Invoke) {
        val expected = permissionRequests.remove(invoke)
        if (expected == null || !PushNotifications.isCurrentPermission(expected)) {
            completePush(invoke, null); return
        }
        completePush(invoke, PushNotifications.granted(activity), expected)
    }

    private fun completePush(invoke: Invoke, enabled: Boolean?, expected: Long? = null) {
        worker.execute {
            try {
                if (enabled != null) PushNotifications.configure(activity, enabled, expected)
                invoke.resolve(PushNotifications.snapshot(activity))
            } catch (_: Exception) { invoke.reject("Notifications are unavailable; chat reconnect is unaffected", "PUSH_UNAVAILABLE") }
        }
    }

    @Command
    fun getSecret(invoke: Invoke) {
        val args = try { invoke.parseArgs(SlotArgs::class.java) } catch (_: Exception) {
            invoke.reject("Invalid unlock storage request", "INVALID_ARGUMENT"); return
        }
        worker.execute {
            try {
                val secret = vault.read(args.slot)
                invoke.resolve(JSObject().put("secret", secret ?: JSONObject.NULL))
            } catch (_: Exception) { invoke.reject("Unlock storage is unavailable", "VAULT_UNAVAILABLE") }
        }
    }

    @Command
    fun storeSecret(invoke: Invoke) {
        val args = try { invoke.parseArgs(StoreArgs::class.java) } catch (_: Exception) {
            invoke.reject("Invalid unlock storage request", "INVALID_ARGUMENT"); return
        }
        worker.execute {
            try {
                vault.store(args.slot, args.secret, args.confirmed)
                invoke.resolve()
            } catch (_: Exception) { invoke.reject("Unlock storage is unavailable", "VAULT_UNAVAILABLE") }
            finally { args.secret = "" }
        }
    }

    @Command
    fun deleteSecret(invoke: Invoke) {
        val args = try { invoke.parseArgs(SlotArgs::class.java) } catch (_: Exception) {
            invoke.reject("Invalid unlock storage request", "INVALID_ARGUMENT"); return
        }
        worker.execute {
            try { vault.delete(args.slot); invoke.resolve() }
            catch (_: Exception) { invoke.reject("Unlock storage is unavailable", "VAULT_UNAVAILABLE") }
        }
    }
}
