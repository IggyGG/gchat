package boo.gchat.app.mobileplatform

import android.app.Activity
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

@TauriPlugin
class MobilePlatformPlugin(private val activity: Activity) : Plugin(activity) {
    private val vault = UnlockVault(activity)

    companion object {
        // A process-wide serial worker preserves store/delete order, including
        // activity recreation. Keystore and filesystem work never blocks UI.
        private val worker = Executors.newSingleThreadExecutor { task ->
            Thread(task, "gchat-unlock-vault").apply { isDaemon = true }
        }
    }

    // Tauri has already loaded the GChat native library before registering this plugin.
    private external fun nativeLifecycle(state: Int)

    override fun onResume() { nativeLifecycle(1) }
    override fun onStop() {
        if (!activity.isChangingConfigurations) nativeLifecycle(2)
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
