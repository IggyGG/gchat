package boo.gchat.app.mobileplatform

import android.Manifest
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.os.Build
import androidx.core.app.NotificationCompat
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import app.tauri.plugin.JSObject
import com.google.firebase.FirebaseApp
import com.google.firebase.messaging.FirebaseMessaging
import com.google.firebase.messaging.FirebaseMessagingService
import com.google.firebase.messaging.RemoteMessage
import org.json.JSONObject

/** Native process singleton; neither tokens nor payloads enter the webview. */
internal object PushNotifications {
    private const val PREFS = "gchat-push-policy"
    private const val TOKEN = "native_push_token"
    private const val CHANNEL = "gchat_activity"
    private const val TAP = "gchat_push_tap"
    private val epoch = PushEpoch()
    private var tapped = false
    @Synchronized fun beginPermission(): Long { return epoch.advance() }
    @Synchronized fun isCurrentPermission(expected: Long): Boolean = epoch.current(expected)
    @Synchronized fun enabled(context: Context): Boolean = context.getSharedPreferences(PREFS, 0).getBoolean("enabled", false)
    @Synchronized fun configure(context: Context, value: Boolean, expected: Long? = null) {
        if (expected != null && !epoch.current(expected)) return
        epoch.advance()
        check(context.getSharedPreferences(PREFS, 0).edit().putBoolean("enabled", value).commit())
        FirebaseApp.initializeApp(context) ?: throw IllegalStateException("Push configuration unavailable")
        val messaging = FirebaseMessaging.getInstance()
        messaging.isAutoInitEnabled = value
        if (!value) {
            // Do not delete/recreate the provider identity during a rapid re-enable.
            // The application unregisters its gateway reference separately.
            UnlockVault(context).delete(TOKEN)
            NotificationManagerCompat.from(context).cancelAll()
            return
        }
        val expected = epoch.advance()
        messaging.token.addOnSuccessListener { token -> synchronized(this) {
            if (epoch.current(expected) && enabled(context)) saveToken(context, token)
        } }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(
            NotificationChannel(CHANNEL, "GChat activity", NotificationManager.IMPORTANCE_DEFAULT)
        )
    }
    @Synchronized fun saveToken(context: Context, token: String) {
        if (!enabled(context) || token.isEmpty() || token.length > 4096) return
        try { UnlockVault(context).store(TOKEN, token, true) } catch (_: Exception) { /* Retry token retrieval after device unlock. */ }
    }
    fun granted(context: Context): Boolean = NotificationManagerCompat.from(context).areNotificationsEnabled() &&
        (Build.VERSION.SDK_INT < 33 || ContextCompat.checkSelfPermission(context, Manifest.permission.POST_NOTIFICATIONS) == PackageManager.PERMISSION_GRANTED)
    @Synchronized fun snapshot(context: Context): JSObject {
        val token = try { if (enabled(context) && granted(context)) UnlockVault(context).read(TOKEN) else null } catch (_: Exception) { null }
        if (enabled(context) && granted(context) && token == null) {
            // A token callback may have arrived while Keystore was locked.
            // Retry only after a normal foreground status poll can read it.
            val expected = epoch.advance()
            val firebase = FirebaseApp.initializeApp(context)
            if (firebase != null) FirebaseMessaging.getInstance().token.addOnSuccessListener { value -> synchronized(this) {
                if (epoch.current(expected) && enabled(context)) saveToken(context, value)
            } }
        }
        return JSObject().put("enabled", enabled(context)).put("permission", if (granted(context)) "granted" else "denied")
            .put("platform", "fcm").put("token", token ?: JSONObject.NULL).put("tapped", tapped).also { tapped = false }
    }
    @Synchronized fun consumeIntent(intent: Intent?) {
        if (intent?.getBooleanExtra(TAP, false) == true) { tapped = true; intent.removeExtra(TAP) }
    }
    fun hint(context: Context, data: Map<String, String>) {
        // Only the gateway's opaque message hint is accepted; names/text in an
        // unexpected payload are never copied into a notification.
        if (!enabled(context) || !granted(context) || data["activity"] != "message" ||
            !validReference(data["reference"])) return
        val launch = context.packageManager.getLaunchIntentForPackage(context.packageName) ?: return
        launch.putExtra(TAP, true).addFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        val pending = PendingIntent.getActivity(context, 0, launch, PendingIntent.FLAG_UPDATE_CURRENT or PendingIntent.FLAG_IMMUTABLE)
        val notice = NotificationCompat.Builder(context, CHANNEL)
            .setSmallIcon(R.drawable.gchat_notification).setContentTitle("GChat")
            .setContentText("New activity in GChat").setContentIntent(pending)
            .setVisibility(NotificationCompat.VISIBILITY_PRIVATE).setAutoCancel(true).build()
        try { NotificationManagerCompat.from(context).notify(1, notice) } catch (_: SecurityException) { /* Permission was revoked. */ }
    }
    fun validReference(value: String?): Boolean = value?.length == 64 && value.all { it in '0'..'9' || it in 'a'..'f' }
}

/** A bounded callback: no profile unlock, relay connection or application runtime. */
class GChatFirebaseService : FirebaseMessagingService() {
    override fun onNewToken(token: String) { PushNotifications.saveToken(this, token) }
    override fun onMessageReceived(message: RemoteMessage) { PushNotifications.hint(this, message.data) }
}
