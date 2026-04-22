<p align="center">
  <img src="https://img.shields.io/badge/platform-Windows%2011-0078D4?style=for-the-badge&logo=windows11&logoColor=white" alt="Windows 11" />
  <img src="https://img.shields.io/badge/python-3.8+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python" />
  <img src="https://img.shields.io/badge/admin-not%20required-success?style=for-the-badge" alt="No Admin" />
  <img src="https://img.shields.io/badge/license-MIT-blue?style=for-the-badge" alt="License" />
</p>

<h1 align="center">🖱️ Auto Warm-Up</h1>

<p align="center">
  <strong>Lightweight keep-alive utility that prevents Windows from locking the screen due to inactivity.</strong><br/>
  No admin rights required. No installation. Just double-click and forget.
</p>

<p align="center">
  <a href="#-quickstart">Quickstart</a> •
  <a href="#-how-it-works">How It Works</a> •
  <a href="#-download">Download</a> •
  <a href="#%EF%B8%8F-build-from-source">Build</a> •
  <a href="#-cicd-pipeline">CI/CD</a> •
  <a href="#-faq">FAQ</a>
</p>

---

## 📋 Table of Contents

- [Quickstart](#-quickstart)
- [How It Works](#-how-it-works)
- [Download](#-download)
- [Features](#-features)
- [System Tray Interface](#-system-tray-interface)
- [Build from Source](#%EF%B8%8F-build-from-source)
  - [Option A: Download Pre-built .exe](#option-a-download-pre-built-exe-easiest)
  - [Option B: Build on Windows](#option-b-build-on-windows)
  - [Option C: Cross-compile from Linux](#option-c-cross-compile-from-linux-via-docker)
- [CI/CD Pipeline](#-cicd-pipeline)
- [Project Structure](#-project-structure)
- [Configuration](#-configuration)
- [Console Mode (Fallback)](#-console-mode-fallback)
- [FAQ](#-faq)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🚀 Quickstart

1. **Download** `AutoWarmUp.exe` from the [Releases](../../releases/latest) page
2. **Copy** it anywhere on your Windows 11 PC
3. **Double-click** to run — a green circle appears in the system tray
4. Done! Your screen will never lock while it's running

> No installation. No admin rights. No dependencies. Just a single `.exe` file.

---

## 🔬 How It Works

Auto Warm-Up uses **two complementary strategies** to prevent Windows from detecting an idle state:

| Strategy | Windows API | What It Does |
|----------|-------------|--------------|
| **Mouse Jiggle** | `SendInput()` | Moves the cursor 1px right, then 1px left every 30 seconds (invisible to the user) |
| **Idle Timer Reset** | `SetThreadExecutionState()` | Tells Windows the display and system are still required, resetting the lock timer |

Both APIs are **user-level** — they require no elevated privileges and don't modify any system settings or registry keys.

```
┌──────────────────────────────────────────────┐
│              Auto Warm-Up Loop               │
│                                              │
│  ┌─────────────┐    ┌─────────────────────┐  │
│  │  Move mouse │    │ Reset idle timer    │  │
│  │  +1px → ←   │    │ SetThreadExecution  │  │
│  │  -1px ←  →  │    │ State (DISPLAY +    │  │
│  │  (net = 0)  │    │ SYSTEM REQUIRED)    │  │
│  └──────┬──────┘    └──────────┬──────────┘  │
│         │                      │             │
│         └──────┐  ┌────────────┘             │
│                ▼  ▼                          │
│          Sleep 30 seconds                    │
│                │                             │
│                └── Repeat ───────────────┐   │
│                                          │   │
└──────────────────────────────────────────┘   │
                                               │
         System tray: Start / Stop / Quit ─────┘
```

---

## 📥 Download

| Channel | Badge | Description |
|---------|-------|-------------|
| **Stable** | ![stable](https://img.shields.io/badge/branch-main-success?style=flat-square) | Production-ready releases from `main` branch |
| **Beta** | ![beta](https://img.shields.io/badge/branch-beta-yellow?style=flat-square) | Pre-release testing from `beta` branch |
| **Alpha** | ![alpha](https://img.shields.io/badge/branch-alpha-red?style=flat-square) | Experimental builds from `alpha` branch |

👉 **[Download Latest Release](../../releases/latest)**

---

## ✨ Features

- **🔒 No Admin Required** — Uses standard user-level Windows APIs only
- **📌 System Tray** — Runs silently with a color-coded tray icon (green/red)
- **🖱️ Invisible Mouse Jiggle** — 1px movement, net displacement is zero
- **⏱️ Dual Prevention** — Mouse input + `SetThreadExecutionState` for maximum reliability
- **📦 Single File** — Standalone `.exe`, no installation or dependencies
- **🪶 Lightweight** — ~11 MB, minimal CPU/RAM usage
- **🎯 Auto-Start** — Begins preventing idle immediately on launch
- **🔄 Start/Stop** — Toggle via right-click system tray menu
- **🖥️ Console Fallback** — Works even without GUI libraries (headless mode)

---

## 🖥️ System Tray Interface

When running, Auto Warm-Up appears as a small circle in your system tray:

| Icon | State | Meaning |
|------|-------|---------|
| 🟢 | **Green** | Active — preventing screen lock |
| 🔴 | **Red** | Paused — screen lock prevention disabled |

**Right-click menu:**
- **Start** — Resume keeping the screen awake
- **Stop** — Pause (icon turns red)
- **Quit** — Exit the program completely

---

## 🛠️ Build from Source

### Option A: Download Pre-built .exe (Easiest)

Go to [Releases](../../releases/latest) and download `AutoWarmUp.exe`. That's it!

### Option B: Build on Windows

**Prerequisites:** Python 3.8+ ([Download](https://www.python.org/downloads/) — select "Install for current user only", no admin needed)

```cmd
:: Clone the repository
git clone https://github.com/adityabhalsod/auto-warm-up.git
cd auto-warm-up

:: Run the build script (uses Nuitka by default -- lowest AV false-positive rate)
build.bat

:: Legacy PyInstaller path (higher AV false-positive rate, kept for compatibility):
:: build.bat --pyinstaller
```

Your `.exe` will be at `dist\AutoWarmUp.exe`.

> **Why Nuitka by default?** Nuitka compiles Python to C to a real native PE binary, so
> antivirus engines can't fingerprint a shared bootloader (the main reason PyInstaller
> builds get flagged as malware). See the [false-positive FAQ](#-faq) for details.

<details>
<summary><strong>Manual build commands</strong></summary>

```cmd
pip install --user pystray Pillow pyinstaller
pyinstaller --onefile --noconsole --name AutoWarmUp auto_warm_up.py
```
</details>

### Option C: Cross-compile from Linux (via Docker)

**Prerequisites:** Docker installed on your Linux machine

```bash
# Clone the repository
git clone https://github.com/adityabhalsod/auto-warm-up.git
cd auto-warm-up

# Run the cross-compilation build script
chmod +x build_linux.sh
./build_linux.sh
```

This uses Docker with [tobix/pywine](https://hub.docker.com/r/tobix/pywine) to run Wine + Python + PyInstaller inside a container. No Wine installation needed on the host.

Your `.exe` will be at `dist/AutoWarmUp.exe`. Copy it to your Windows PC.

---

## 🔄 CI/CD Pipeline

This project uses **GitHub Actions** to automatically build and release `.exe` files on every push to `main`, `beta`, or `alpha` branches.

### Pipeline Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    GitHub Actions Pipeline                 │
│                                                            │
│  ┌──────────────┐   ┌──────────────┐   ┌────────────────┐  │
│  │   PREPARE    │──▶│    BUILD     │──▶│    RELEASE     │  │
│  │   (~1 min)   │   │  (~6-8 min)  │   │    (~1 min)    │  │
│  ├──────────────┤   ├──────────────┤   ├────────────────┤  │
│  │ • Checkout   │   │ • Checkout   │   │ • Download .exe│  │
│  │ • Compute    │   │ • Free disk  │   │ • Create git   │  │
│  │   version    │   │ • Docker     │   │   tag          │  │
│  │ • Generate   │   │   build with │   │ • Publish      │  │
│  │   changelog  │   │   Wine +     │   │   GitHub       │  │
│  │ • Detect     │   │   PyInstaller│   │   Release      │  │
│  │   channel    │   │ • Extract    │   │ • Attach .exe  │  │
│  │              │   │   .exe       │   │   asset        │  │
│  └──────────────┘   └──────────────┘   └────────────────┘  │
│                                                            │
│  Branch Mapping:                                           │
│    main  → v1.0.0           (stable)                       │
│    beta  → v1.0.0-beta.3    (pre-release)                  │
│    alpha → v1.0.0-alpha.7   (pre-release)                  │
└────────────────────────────────────────────────────────────┘
```

### Pipeline Features

| Feature | Description |
|---------|-------------|
| **3-Stage Pipeline** | Prepare → Build → Release (sequential, fail-fast) |
| **Auto-Versioning** | Reads `VERSION` file + commit count for pre-release suffixes |
| **Conventional Changelog** | Groups commits by `feat:`, `fix:`, `perf:`, `docs:` prefixes |
| **Docker Cross-Compilation** | Builds Windows `.exe` on `ubuntu-latest` via Wine |
| **Layer Caching** | Docker build cache via GitHub Actions for faster rebuilds |
| **Concurrency Control** | Only one release per branch at a time, cancels in-progress runs |
| **Skip CI** | Add `[skip ci]` or `[ci skip]` to commit message to skip |

### Triggering a Release

```bash
# Stable release (from main)
git checkout main
git push origin main

# Beta release
git checkout beta
git push origin beta

# Alpha release
git checkout alpha
git push origin alpha
```

---

## 📁 Project Structure

```
auto-warm-up/
├── .github/
│   └── workflows/
│       └── release.yml        # GitHub Actions CI/CD pipeline
├── auto_warm_up.py            # Main application source code
├── requirements.txt           # Python dependencies (pinned versions)
├── Dockerfile                 # Docker config for cross-compilation
├── build.bat                  # Windows build script
├── build_linux.sh             # Linux cross-compilation build script
├── VERSION                    # Semantic version (e.g. 1.0.0)
├── LICENSE                    # MIT License
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

---

## ⚙️ Configuration

| Parameter | Default | File | Description |
|-----------|---------|------|-------------|
| `interval_seconds` | `30` | `auto_warm_up.py` | Seconds between each mouse jiggle |
| Mouse delta | `1` pixel | `auto_warm_up.py` | Pixels moved per jiggle (1px right, 1px left) |

To change the interval, edit the `interval_seconds` parameter in `auto_warm_up.py`:

```python
# Change 30 to your preferred interval (in seconds)
prevent_idle(interval_seconds=30, stop_event=stop_event)
```

---

## 💻 Console Mode (Fallback)

If `pystray` or `Pillow` are not bundled (e.g., running the `.py` file directly without those packages), the program automatically falls back to **console mode**:

```
==================================================
  Auto Warm-Up — Keep-Alive Utility
==================================================

  Status : RUNNING
  Action : Mouse jiggles every 30 seconds
  Stop   : Press Ctrl+C to exit

==================================================
```

Press `Ctrl+C` to stop.

---

## ❓ FAQ

<details>
<summary><strong>Does it need admin rights?</strong></summary>

No. It uses standard user-level Windows APIs:
- `SendInput()` — simulates mouse movement (same as any mouse/keyboard automation tool)
- `SetThreadExecutionState()` — tells Windows the display is still needed (same as video players)

No drivers, no registry changes, no system services.
</details>

<details>
<summary><strong>Will IT / endpoint protection detect it?</strong></summary>

Auto Warm-Up doesn't install anything, modify the registry, change group policy, or run as a service. It's a standard user-space application that simulates mouse input — functionally identical to moving your physical mouse. Most endpoint protection tools won't flag it, but policies vary by organization.
</details>

<details>
<summary><strong>My antivirus flagged AutoWarmUp.exe as a threat — is it malware?</strong></summary>

**No — this is a false positive.** The source code in this repo is the complete source (≈300 lines of Python) and only does two things: simulate a 1-pixel mouse movement and call `SetThreadExecutionState`. You can read every line.

The detection is a **heuristic false positive** triggered by how the `.exe` is packaged, not by what it does. Specifically:

1. **PyInstaller `--onefile` bootloader** — the same bootloader is reused by real malware authors who bundle malicious Python scripts, so AV engines (McAfee, Avast, Bitdefender, and others) flag the bootloader signature on sight, regardless of the payload.
2. **`SendInput` API** — AVs associate synthetic input with keyloggers and automation malware.
3. **Registry autostart** (`HKCU\...\Run`) — a classic malware persistence pattern, even though here it's an opt-in user-visible menu item.

**What we do about it:**
- The default Windows build now uses **[Nuitka](https://nuitka.net/)** instead of PyInstaller. Nuitka compiles Python to C to a real native PE binary, so there is no shared bootloader for AVs to fingerprint. This dramatically reduces false-positive rates.
- The build pipeline no longer self-signs the `.exe`. Self-signed code-signing certificates actually **increase** AV suspicion ("unknown publisher pretending to be legitimate"). An unsigned binary is treated better by most engines.
- Builds use `--noupx` to avoid UPX compression, which is another major AV heuristic trigger.

**What you can do if you hit this (McAfee example):**
1. **Report the false positive to your AV vendor** — vendors process these reports and whitelist the binary. This is the fastest permanent fix:
   - McAfee: <https://www.mcafee.com/enterprise/en-us/threat-center/submit-sample.html>
   - Windows Defender: <https://www.microsoft.com/en-us/wdsi/filesubmission>
   - Others: search "submit false positive &lt;your AV&gt;".
2. **Restore from quarantine** and add `AutoWarmUp.exe` to the AV's allow-list / exclusions.
3. **Build from source** — clone this repo, run `build.bat`, inspect the code yourself. The Nuitka build has materially fewer false positives than the pre-built PyInstaller release.
4. **Scan on [VirusTotal](https://www.virustotal.com/)** — most engines will pass; the few that flag it will typically clear after a vendor report.

We do not sell, distribute, or bundle anything with this utility. No telemetry, no network calls, no installer.
</details>

<details>
<summary><strong>Does the mouse cursor visibly move?</strong></summary>

No. It moves 1 pixel right, then 1 pixel left on the next cycle. The net displacement is zero, and 1 pixel is imperceptible to the human eye.
</details>

<details>
<summary><strong>How much CPU/RAM does it use?</strong></summary>

Virtually none. The program sleeps for 30 seconds between each 1-pixel move. Typical usage is <1 MB RAM and 0% CPU.
</details>

<details>
<summary><strong>Can I run it on startup without admin?</strong></summary>

Yes. Press `Win+R`, type `shell:startup`, and place a shortcut to `AutoWarmUp.exe` in that folder. It will auto-launch when you log in — no admin required.
</details>

<details>
<summary><strong>Can I change how often it jiggles?</strong></summary>

Yes. Edit `auto_warm_up.py` and change `interval_seconds=30` to your preferred value (in seconds), then rebuild.
</details>

<details>
<summary><strong>What Windows versions are supported?</strong></summary>

Windows 10 and Windows 11 (both x64). The APIs used (`SendInput`, `SetThreadExecutionState`) have been available since Windows XP.
</details>

---

## 🤝 Contributing

1. **Fork** the repository
2. Create a **feature branch** (`git checkout -b feat/my-feature`)
3. **Commit** with conventional commits (`feat:`, `fix:`, `docs:`, `perf:`)
4. **Push** and open a Pull Request

The CI pipeline will automatically build and test your changes.

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
