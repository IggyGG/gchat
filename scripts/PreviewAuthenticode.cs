// Windows-only verifier for the pinned, untimestamped preview policy.
// WINTRUST_ACTION_GENERIC_CHAIN_VERIFY retains Windows' SIP/digest/signature
// verification while using an exclusive, memory-only certificate chain engine.
// No system certificate store is opened for writing.
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Runtime.InteropServices;
using System.Security.Cryptography.X509Certificates;

public static class PreviewAuthenticode
{
    [StructLayout(LayoutKind.Sequential)] struct EngineConfig
    {
        public uint size;
        public IntPtr restrictedRoot, restrictedTrust, restrictedOther;
        public uint additionalCount;
        public IntPtr additionalStores;
        public uint flags, timeout, maximumCached, cycleModulus;
        public IntPtr exclusiveRoot, exclusivePeople;
        public uint exclusiveFlags;
    }
    [StructLayout(LayoutKind.Sequential)] struct Usage
    {
        public uint count;
        public IntPtr identifiers;
    }
    [StructLayout(LayoutKind.Sequential)] struct UsageMatch
    {
        public uint type;
        public Usage usage;
    }
    // The original CERT_CHAIN_PARA layout (cbSize selects this version).
    [StructLayout(LayoutKind.Sequential)] struct ChainParameters
    {
        public uint size;
        public UsageMatch requestedUsage;
    }
    [StructLayout(LayoutKind.Sequential)] struct ChainInfo
    {
        public uint size;
        public IntPtr engine, parameters;
        public uint flags;
        public IntPtr reserved;
    }
    [StructLayout(LayoutKind.Sequential)] struct PolicyData
    {
        public uint size;
        public IntPtr signerInfo, counterSignerInfo, callback, argument;
    }
    [StructLayout(LayoutKind.Sequential)] struct SignerInfo
    {
        public uint size;
        public IntPtr chain;
        public uint type;
        public IntPtr messageSigner;
        public uint error, counterSignerCount;
        public IntPtr counterSigners;
    }
    [StructLayout(LayoutKind.Sequential)] struct PolicyParameters
    {
        public uint size, flags;
        public IntPtr extra;
    }
    [StructLayout(LayoutKind.Sequential)] struct PolicyStatus
    {
        public uint size, error;
        public int chainIndex, elementIndex;
        public IntPtr extra;
    }
    [StructLayout(LayoutKind.Sequential)] struct FileInfo
    {
        public uint size;
        public IntPtr path, handle, knownSubject;
    }
    [StructLayout(LayoutKind.Sequential)] struct TrustData
    {
        public uint size;
        public IntPtr policy, sip;
        public uint ui, revocation, choice;
        public IntPtr file;
        public uint action;
        public IntPtr state, url;
        public uint flags, context;
        public IntPtr signatureSettings;
    }
    [UnmanagedFunctionPointer(CallingConvention.Winapi)]
    delegate uint PolicyCallback(IntPtr provider, uint stepError, uint registrySettings,
        uint count, IntPtr signers, IntPtr argument);

    [DllImport("crypt32.dll", SetLastError=true)]
    static extern IntPtr CertOpenStore(IntPtr provider, uint encoding, IntPtr crypt,
        uint flags, IntPtr parameter);
    [DllImport("crypt32.dll", SetLastError=true)]
    static extern bool CertAddCertificateContextToStore(IntPtr store, IntPtr certificate,
        uint disposition, IntPtr output);
    [DllImport("crypt32.dll", SetLastError=true)]
    static extern bool CertCreateCertificateChainEngine(ref EngineConfig config, out IntPtr engine);
    [DllImport("crypt32.dll")]
    static extern void CertFreeCertificateChainEngine(IntPtr engine);
    [DllImport("crypt32.dll")]
    static extern bool CertCloseStore(IntPtr store, uint flags);
    [DllImport("crypt32.dll", SetLastError=true)]
    static extern bool CertVerifyCertificateChainPolicy(IntPtr policy, IntPtr chain,
        ref PolicyParameters parameters, ref PolicyStatus status);
    [DllImport("wintrust.dll", ExactSpelling=true)]
    static extern uint WinVerifyTrust(IntPtr window, ref Guid action, ref TrustData data);

    static uint Size<T>() { return (uint)Marshal.SizeOf(typeof(T)); }
    static IntPtr Allocate<T>(T value, List<IntPtr> allocations)
    {
        IntPtr pointer = Marshal.AllocHGlobal(Marshal.SizeOf(typeof(T)));
        allocations.Add(pointer);
        Marshal.StructureToPtr(value, pointer, false);
        return pointer;
    }

    public static void Verify(string path, X509Certificate2 certificate)
    {
        const uint Untrusted = 0x800B0004;
        string expected = certificate.Thumbprint;
        var allocations = new List<IntPtr>();
        IntPtr store = IntPtr.Zero, engine = IntPtr.Zero;
        bool verifiedPolicy = false, calledTrust = false;
        Guid action = new Guid("fc451c16-ac75-11d1-b4b8-00c04fb66ea0");
        var data = new TrustData();
        PolicyCallback callback = delegate(IntPtr provider, uint error, uint settings,
            uint count, IntPtr signers, IntPtr argument)
        {
            // Never let a managed exception escape an unmanaged callback.
            try
            {
                if (error != 0) return error;
                if (count != 1 || signers == IntPtr.Zero) return Untrusted;
                var signer = (SignerInfo)Marshal.PtrToStructure(Marshal.ReadIntPtr(signers), typeof(SignerInfo));
                if (signer.error != 0) return signer.error;
                if (signer.chain == IntPtr.Zero || signer.type != 0 || signer.counterSignerCount != 0)
                    return Untrusted;
                using (var chain = new X509Chain(signer.chain))
                {
                    if (chain.ChainElements.Count != 1 ||
                        !String.Equals(chain.ChainElements[0].Certificate.Thumbprint, expected,
                            StringComparison.OrdinalIgnoreCase)) return Untrusted;
                }
                // No error-ignore or machine registry policy flags. The chain
                // engine also requires the code-signing EKU, at current time.
                var parameters = new PolicyParameters { size = Size<PolicyParameters>() };
                var status = new PolicyStatus { size = Size<PolicyStatus>() };
                if (!CertVerifyCertificateChainPolicy(new IntPtr(1), signer.chain,
                    ref parameters, ref status)) return Untrusted;
                verifiedPolicy = status.error == 0;
                return status.error;
            }
            catch { return Untrusted; }
        };
        // Hold the exact file open without write/delete sharing throughout verification.
        using (var artifact = new FileStream(path, FileMode.Open, FileAccess.Read, FileShare.Read))
        try
        {
            store = CertOpenStore(new IntPtr(2), 0, IntPtr.Zero, 0x2000, IntPtr.Zero); // MEMORY, CREATE_NEW
            if (store == IntPtr.Zero || !CertAddCertificateContextToStore(store, certificate.Handle, 4, IntPtr.Zero))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            var config = new EngineConfig { size = Size<EngineConfig>(), exclusiveRoot = store,
                flags = 0x2004 }; // disable AIA; cache-only URL retrieval
            if (!CertCreateCertificateChainEngine(ref config, out engine))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            IntPtr oid = Marshal.StringToHGlobalAnsi("1.3.6.1.5.5.7.3.3");
            allocations.Add(oid);
            var parameters = new ChainParameters { size = Size<ChainParameters>(),
                requestedUsage = new UsageMatch { usage = new Usage { count = 1,
                    identifiers = Allocate(oid, allocations) } } };
            var chainInfo = new ChainInfo { size = Size<ChainInfo>(), engine = engine,
                parameters = Allocate(parameters, allocations), flags = 0x2104 };
            var policy = new PolicyData { size = Size<PolicyData>(),
                signerInfo = Allocate(chainInfo, allocations),
                callback = Marshal.GetFunctionPointerForDelegate(callback) };
            IntPtr filePath = Marshal.StringToHGlobalUni(Path.GetFullPath(path));
            allocations.Add(filePath);
            var file = new FileInfo { size = Size<FileInfo>(), path = filePath,
                handle = artifact.SafeFileHandle.DangerousGetHandle() };
            data = new TrustData { size = Size<TrustData>(), policy = Allocate(policy, allocations),
                ui = 2, choice = 1, file = Allocate(file, allocations), action = 1,
                flags = 0x3010 }; // offline, no CA revocation service for self-signed leaf; disable MD2/MD4
            calledTrust = true;
            uint result = WinVerifyTrust(new IntPtr(-1), ref action, ref data);
            if (result != 0 || !verifiedPolicy)
                throw new InvalidOperationException("Pinned Authenticode verification failed: 0x" + result.ToString("X8"));
        }
        finally
        {
            if (calledTrust)
            {
                data.action = 2; // WTD_STATEACTION_CLOSE, including failed verifications
                WinVerifyTrust(new IntPtr(-1), ref action, ref data);
            }
            GC.KeepAlive(callback);
            if (engine != IntPtr.Zero) CertFreeCertificateChainEngine(engine);
            if (store != IntPtr.Zero) CertCloseStore(store, 0);
            foreach (IntPtr allocation in allocations) Marshal.FreeHGlobal(allocation);
        }
    }
}
