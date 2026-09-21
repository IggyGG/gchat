package boo.gchat.app.mobileplatform

import android.app.KeyguardManager
import android.content.Context
import android.os.UserManager
import android.security.keystore.KeyGenParameterSpec
import android.security.keystore.KeyProperties
import android.util.AtomicFile
import java.io.File
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.security.KeyStore
import javax.crypto.Cipher
import javax.crypto.KeyGenerator
import javax.crypto.SecretKey
import javax.crypto.spec.GCMParameterSpec

internal class VaultFailure : Exception("Native unlock storage unavailable")

/** Ciphertext lives only in app-private, backup-excluded storage. No plaintext preferences. */
internal class UnlockVault(context: Context) {
    private val context = context.applicationContext
    private val directory = File(this.context.noBackupFilesDir, "gchat-unlock-v1")

    companion object {
        private const val SERVICE = "boo.gchat.app.unlock.v1"
        private const val MAX_BYTES = 4096
        private const val NONCE_BYTES = 12
        private const val MAX_RECORD_BYTES = 1 + NONCE_BYTES + MAX_BYTES + 16
        private val gate = Any()

        fun validSlot(slot: String): Boolean = slot.length in 1..128 &&
            slot.all { it in 'a'..'z' || it in 'A'..'Z' || it in '0'..'9' || it == '_' || it == '-' }

        fun validSecret(secret: String): Boolean = secret.isNotEmpty() &&
            !secret.contains('\u0000') && secret.toByteArray(Charsets.UTF_8).size <= MAX_BYTES
    }

    private fun requireSlot(slot: String) { if (!validSlot(slot)) throw VaultFailure() }
    private fun alias(slot: String) = "$SERVICE.$slot"
    private fun aad(slot: String) = "$SERVICE:$slot".toByteArray(Charsets.UTF_8)
    private fun file(slot: String) = AtomicFile(File(directory, "$slot.bin"))
    private fun keyStore() = KeyStore.getInstance("AndroidKeyStore").apply { load(null) }

    private fun requireUnlocked() {
        val users = context.getSystemService(UserManager::class.java)
        val keyguard = context.getSystemService(KeyguardManager::class.java)
        if (!users.isUserUnlocked || keyguard.isDeviceLocked) throw VaultFailure()
    }

    private fun existingKey(slot: String): SecretKey? = keyStore().getKey(alias(slot), null) as? SecretKey

    private fun createKey(slot: String): SecretKey {
        val generator = KeyGenerator.getInstance(KeyProperties.KEY_ALGORITHM_AES, "AndroidKeyStore")
        val spec = KeyGenParameterSpec.Builder(
            alias(slot), KeyProperties.PURPOSE_ENCRYPT or KeyProperties.PURPOSE_DECRYPT
        ).setKeySize(256)
            .setBlockModes(KeyProperties.BLOCK_MODE_GCM)
            .setEncryptionPaddings(KeyProperties.ENCRYPTION_PADDING_NONE)
            .setRandomizedEncryptionRequired(true)
        // API26+ baseline has app-level lock checks above. AndroidKeyStore keeps
        // key material non-exportable; this does not claim biometric authentication.
        generator.init(spec.build())
        return generator.generateKey()
    }

    fun store(slot: String, secret: String, confirmed: Boolean) = synchronized(gate) {
        requireSlot(slot)
        if (!confirmed || !validSecret(secret)) throw VaultFailure()
        requireUnlocked()
        if (!directory.isDirectory && !directory.mkdirs()) throw VaultFailure()
        val key = existingKey(slot) ?: createKey(slot)
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.ENCRYPT_MODE, key)
        cipher.updateAAD(aad(slot))
        val plaintext = secret.toByteArray(Charsets.UTF_8)
        val ciphertext = try { cipher.doFinal(plaintext) } finally { plaintext.fill(0) }
        val nonce = cipher.iv
        if (nonce.size != NONCE_BYTES) throw VaultFailure()
        val record = byteArrayOf(1) + nonce + ciphertext
        val target = file(slot)
        val output = target.startWrite()
        try {
            output.write(record)
            target.finishWrite(output)
        } catch (error: Exception) {
            target.failWrite(output)
            throw VaultFailure()
        }
    }

    fun read(slot: String): String? = synchronized(gate) {
        requireSlot(slot)
        requireUnlocked()
        val target = file(slot)
        // AtomicFile may have a valid .bak left by an interrupted write.
        if (!target.baseFile.exists() && !File(target.baseFile.path + ".bak").exists()) return@synchronized null
        val key = existingKey(slot) ?: throw VaultFailure()
        val record = target.openRead().use { input ->
            val bytes = ByteArray(MAX_RECORD_BYTES + 1)
            var used = 0
            while (used < bytes.size) {
                val n = input.read(bytes, used, bytes.size - used)
                if (n < 0) break
                used += n
            }
            bytes.copyOf(used)
        }
        if (record.size !in (1 + NONCE_BYTES + 16)..MAX_RECORD_BYTES || record[0] != 1.toByte()) throw VaultFailure()
        val cipher = Cipher.getInstance("AES/GCM/NoPadding")
        cipher.init(Cipher.DECRYPT_MODE, key, GCMParameterSpec(128, record.copyOfRange(1, 1 + NONCE_BYTES)))
        cipher.updateAAD(aad(slot))
        val plaintext = cipher.doFinal(record, 1 + NONCE_BYTES, record.size - 1 - NONCE_BYTES)
        try {
            val secret = Charsets.UTF_8.newDecoder()
                .onMalformedInput(CodingErrorAction.REPORT)
                .onUnmappableCharacter(CodingErrorAction.REPORT)
                .decode(ByteBuffer.wrap(plaintext)).toString()
            if (!validSecret(secret)) throw VaultFailure()
            secret
        } finally { plaintext.fill(0) }
    }

    fun delete(slot: String) = synchronized(gate) {
        requireSlot(slot)
        // Removing the key first makes a leftover ciphertext file unusable even
        // if filesystem removal fails. No unlock check prevents opt-out cleanup.
        keyStore().deleteEntry(alias(slot))
        val target = file(slot)
        target.delete()
        if (target.baseFile.exists() || File(target.baseFile.path + ".bak").exists() ||
            File(target.baseFile.path + ".new").exists()) throw VaultFailure()
    }
}
