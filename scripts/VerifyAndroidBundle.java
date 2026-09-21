import java.io.InputStream;
import java.nio.file.Path;
import java.security.CodeSigner;
import java.security.MessageDigest;
import java.security.cert.Certificate;
import java.util.HexFormat;
import java.util.Locale;
import java.util.jar.JarEntry;
import java.util.jar.JarFile;

/** Verify every bundle payload entry against the pinned signing certificate. */
class VerifyAndroidBundle {
    public static void main(String[] args) throws Exception {
        if (args.length != 2 || !args[1].matches("[0-9a-f]{64}")) {
            throw new IllegalArgumentException("expected bundle path and SHA-256 certificate pin");
        }
        int verified = 0;
        var names = new java.util.HashSet<String>();
        try (var jar = new JarFile(Path.of(args[0]).toFile(), true)) {
            var entries = jar.entries();
            var bytes = new byte[65536];
            while (entries.hasMoreElements()) {
                JarEntry entry = entries.nextElement();
                if (!names.add(entry.getName())) throw new SecurityException("duplicate archive entry");
                if (entry.isDirectory()) continue;
                try (InputStream input = jar.getInputStream(entry)) {
                    while (input.read(bytes) != -1) { /* Reading verifies signed entry digests. */ }
                }
                String upper = entry.getName().toUpperCase(Locale.ROOT);
                if (upper.equals("META-INF/MANIFEST.MF") ||
                    upper.matches("META-INF/[^/]+\\.(SF|RSA|DSA|EC)")) continue;
                CodeSigner[] signers = entry.getCodeSigners();
                if (signers == null || signers.length != 1) {
                    throw new SecurityException("unsigned or multiply signed bundle entry: " + entry.getName());
                }
                Certificate leaf = signers[0].getSignerCertPath().getCertificates().get(0);
                String pin = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(leaf.getEncoded()));
                if (!pin.equals(args[1])) throw new SecurityException("bundle signer does not match publisher pin");
                verified++;
            }
        }
        if (verified == 0) throw new SecurityException("bundle has no signed payload entries");
        System.out.println("{\"passed\":true,\"certificate_sha256\":\"" + args[1] +
            "\",\"verified_entries\":" + verified + "}");
    }
}
