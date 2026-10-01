# Antigravity Quota Manager & Monitor for Linux

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Platform: Linux](https://img.shields.io/badge/Platform-Linux-blue.svg)](https://kernel.org)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![Tested on Ubuntu / Debian / Mint](https://img.shields.io/badge/Tested%20on-Ubuntu%20%7C%20Mint%20%7C%20Debian%20%7C%20Arch-orange.svg)]()

<div align="center">
  <img src="assets/icon.png" width="160" alt="Antigravity Quota Logo" />
  <p><em>A native-feeling standalone Linux desktop webapp and rich terminal CLI for tracking real-time 5-hour rolling sprint quotas and weekly capacity limits across multiple Google Antigravity accounts — with automated weekly replenishment timer management.</em></p>
</div>

---

## 💡 Why This Exists

### 1. The Multi-Account Visibility Problem (The Monitor Foundation)
**Google Antigravity 2.0** enforces an opaque dual-quota system:
* **5-Hour Rolling Limit ("Sprint Quota")**: Absorbs intensive multi-turn coding and agent loops, replenishing continuously over a 5-hour window.
* **Weekly Baseline Cap**: Restricts total compute effort over a 7-day period based on your plan tier (Pro/Ultra).

In the official Antigravity IDE, these limits are buried multiple clicks deep inside `Settings > Models & Usage`, and **you can only inspect the currently logged-in account**. Developers who balance multiple Google accounts (e.g. personal, work, secondary development accounts) have no way to monitor their available compute pools side-by-side.

**Antigravity Quota Monitor** was built to solve this:
* **Unified Multi-Account Dashboard**: See all registered Google accounts at a glance with live percentage bars, usage counts, and reset countdowns.
* **Dual Pool Coverage**: Independently tracks both **Gemini Models** (Flash/Pro) and **Claude & GPT Models** (Sonnet/Opus/GPT-OSS).
* **Standalone Desktop WebApp**: Operates as an independent window with **zero browser chrome** (no URL bar, no tabs, no clutter), custom dock icons, and single-instance window focusing via `wmctrl`.
* **Rich Terminal CLI**: For keyboard-driven workflows, run `antigravity-quota status` or live-refreshing `antigravity-quota watch` directly in your terminal or tmux sessions.
* **100% Private & Local**: Zero telemetry or third-party servers. Credentials and tokens remain strictly on your machine with POSIX `0600` permissions.

---

### 2. From Observer to Manager: The "Sliding Reset Window" Trap
While monitoring multiple accounts over time, a critical quirk in Antigravity's quota engine became evident:

> **The Sliding Window Trap:** When an account sits idle at 100% quota, Antigravity **does not start the 7-day replenishment clock**. Instead, the reset date dynamically slides forward (`now + 7 days`). The countdown only anchors into a fixed replenishment schedule (`in 6d 23h`) once tokens are actually consumed.

If you let secondary accounts sit idle waiting for a big project, **you quietly lose weekly replenishment cycles**.

**Antigravity Quota Manager** elevates the tool from a passive observer to an active optimizer:
* **⚡ 7-Day Countdown Kickstarting**: Sends a minimal 1-word micro-ping (`"Reply with 1 word: Pong"`) consuming ~30 tokens (<0.002% quota) to immediately anchor the 7-day countdown to `in 6d 23h`.
* **One-Click UI Controls**: Global `⚡ Kickstart All Timers` in the header, card-level `⚡ Kickstart`, and granular `⚡ Ping` buttons for individual model pools.
* **Real-Time Timer Status**: Live `Active` vs `Idle (Unanchored)` badges inform you instantly whether an account's replenishment timer is running or dormant.
* **CLI Automation**: Run `antigravity-quota kickstart --all` in cron jobs or terminal commands to keep all accounts continuously replenishing on schedule.

---

## ✨ Features

### 📊 Real-Time Monitoring & Observability
- **Multi-Account Overview**: Side-by-side visual cards for all connected accounts.
- **Dual Model Pool Tracking**: Separate progress meters and countdowns for Gemini and Claude/GPT pools.
- **Auto-Discovery**: Automatically detects and displays your active local Antigravity IDE session on startup.
- **In-App Google OAuth**: Click **"+ Add Account"** to connect additional Google accounts via one-time browser login.
- **Session Renaming**: Give accounts friendly nicknames (*"Work"*, *"Personal"*, *"Heavy Agent Run"*) with inline editing.
- **Rich Terminal CLI**: Full terminal dashboard with colored progress bars and live auto-refresh (`status` and `watch`).

### ⚡ Active Quota Management & Optimization
- **Weekly Timer Kickstarting**: Anchor sliding 7-day replenishment countdowns with negligible micro-pings.
- **Granular Controls**: Kickstart all accounts at once, kickstart a specific account, or target a single model pool.
- **Real-Time Badges**: Immediate visual indicators for `Active` (anchored) vs `Idle` (sliding) weekly limits.
- **Zero Orphaned Daemons**: Backend server starts on demand and shuts down cleanly when the window closes.
- **Zero Stale Caching**: Automatic HTTP cache clearance and `--disable-cache` browser flags guarantee live UI updates.

---

## 📦 Requirements

- **Linux Distribution**: Ubuntu, Linux Mint, Debian, Arch Linux, Fedora, etc.
- **Python 3.10+**
- **Chromium-based browser**: `chromium`, `google-chrome`, or `brave-browser`
- **wmctrl**: Standard Linux window management utility

---

## 🚀 Quick Start & Installation

Clone the repository and run the automated installer:

```bash
git clone https://github.com/kylechoidev/antigravity-quota-linux.git
cd antigravity-quota-linux
./install.sh
```

The installer will:
1. Check system prerequisites.
2. Create an isolated virtual environment in `~/.local/share/antigravity-quota-app/.venv`.
3. Install the launcher to `~/.local/bin/antigravity-quota`.
4. Register the desktop entry (`antigravity-quota.desktop`) and high-res icon in your Linux application menu.

---

## 🖥️ Usage

### 1. Launch Desktop WebApp
You can open the app at any time via:
* **Application Menu / Search**: Press Super/Windows key and type **"Antigravity Quota"**.
* **Terminal**:
  ```bash
  antigravity-quota
  ```

### 2. Terminal CLI Commands
Prefer the terminal? The launcher doubles as a full-featured CLI:

```bash
# Print current quota table for all accounts
antigravity-quota status

# Live-updating terminal dashboard (default: updates every 30s)
antigravity-quota watch --interval 15

# List all registered accounts
antigravity-quota list

# Add an account via CLI
antigravity-quota add-account --name "Work"

# Rename an account
antigravity-quota rename "my-account@gmail.com" "Main Dev"

# Remove an account
antigravity-quota remove "Work"

# Kickstart & anchor 7-day countdown on all idle accounts
antigravity-quota kickstart --all

# Force-kickstart all accounts (even if already active)
antigravity-quota kickstart --all --force

# Kickstart a specific account (both pools or targeted pool)
antigravity-quota kickstart "my-account@gmail.com" --pool gemini
antigravity-quota kickstart "my-account@gmail.com" --pool claude
```

---

## 🔒 Security & Privacy

* **Token Storage**: Account tokens are stored strictly on your local filesystem at `~/.config/antigravity-monitor/accounts.json`.
* **File Permissions**: Files are created with POSIX `0600` permissions (read/write only by your Linux user).
* **Zero Telemetry**: All network requests communicate directly between your machine and Google's OAuth / Cloud Code services (`cloudcode-pa.googleapis.com`). No telemetry or third-party servers are involved.

---

## 🗑️ Uninstallation

To completely remove the app, desktop entries, and launchers:

```bash
cd antigravity-quota-linux
./uninstall.sh
```

---

## 📄 License

Distributed under the [MIT License](LICENSE).
