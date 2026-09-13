# File Juggler — Security, Privacy & Zero-Storage Architecture

This document certifies the end-to-end encryption, zero remote data storage, and local-only security architecture of the File Juggler desktop application.

---

## 1. Zero Remote Storage Guarantee (100% Air-Gapped)

File Juggler operates strictly as an offline, client-side Windows utility:

- **Zero Backend Servers**: The application does not connect to any server, cloud service, API gateway, or database controlled by File Juggler or any third party.
- **Zero Telemetry & Tracking**: There are no telemetry pings, crash reporting beacons, Google Analytics, Mixpanel, or usage tracking modules embedded in the application.
- **Zero Remote Transmission**: No file contents, directory names, filenames, metadata, or IP addresses are transmitted across the network.
- **Air-Gapped Operation**: File Juggler operates identically with full functionality on systems with network adapters disabled or completely disconnected from the Internet.

---

## 2. Client-Side End-to-End Encryption at Rest

To protect user confidentiality on the local device, all persisted data is encrypted client-side before touching disk storage:

### Cryptographic Mechanism
- **Engine**: Windows Data Protection API (**DPAPI**) via `CryptProtectData` and `CryptUnprotectData` (`crypt32.dll`), backed by hardware-accelerated **AES-256**.
- **Key Derivation & Scoping**: Encryption keys are tied directly to the current logged-in Windows user's security identifier (SID) and Master Key. 
  - Other users on the same machine cannot decrypt the data.
  - Data extracted from hard drive images or cold backups cannot be decrypted without the user's Windows credentials.
- **Armored Tokens**: Encrypted payloads are formatted as base64-armored tokens with a version header (`enc:v1:...`).

### What Is Encrypted
1. **Preferences & Settings** (`%LOCALAPPDATA%\FileJuggler\settings.json`):
   - Last accessed source and destination paths
   - Custom organization rules and filter criteria
2. **Session Audit History** (`%LOCALAPPDATA%\FileJuggler\history.json`):
   - File paths, timestamps, original locations, and rollback metadata
3. **Application Logs** (`%LOCALAPPDATA%\FileJuggler\logs\app.log`):
   - Local-only diagnostic logs scoped to the user profile directory.

---

## 3. Data Lifecycle & In-Memory Destruction

- **Scanning Phase**: File metadata (name, size, modification timestamp) is read into transient memory (`FileItem` dataclasses) via non-blocking OS filesystem handles (`os.scandir`). File contents are not read into memory unless hashing is required.
- **Moving Phase**: File operations are executed atomically using Windows OS filesystem primitives (`MoveFileExW` / `shutil.move`).
- **Memory Reclamation**: Once an organization session completes or is cancelled, in-memory references are immediately cleared, and memory pages are reclaimed by Python's garbage collector.

---

## 4. Security Verification & Audit

You can verify that File Juggler does not communicate externally using standard Windows security tools:

1. **Windows Defender Firewall with Advanced Security**:
   - Inspect active inbound/outbound rules. File Juggler creates no network listening ports or outbound connections.
2. **Resource Monitor (Network Tab)**:
   - Run `resmon.exe`, navigate to the **Network** tab, and filter by `FileJuggler.exe`. Network send/receive bytes will remain at **0 B/sec**.
3. **Sysinternals TCPView**:
   - Verify `FileJuggler.exe` creates 0 TCP/UDP endpoints.
