# 🔵 QRadar Smart DSM Builder
 
<div align="center">

![QRadar DSM Builder](https://img.shields.io/badge/QRadar-DSM_Builder-00b0f0?style=for-the-badge&logo=ibm&logoColor=white)
![Python](https://img.shields.io/badge/Python-2.7%2B_%7C_3.x-3776AB?style=for-the-badge&logo=python&logoColor=white)
![JavaScript](https://img.shields.io/badge/JavaScript-ES8-F7DF1E?style=for-the-badge&logo=javascript&logoColor=black)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-1.0.0-blue?style=for-the-badge)

**Auto-analyze logs → Detect format → Map events → Generate & Import DSM to QRadar**

*Built by [Tarek Farag](https://www.linkedin.com/in/tarekfarag45) — Sr. Cyber Security Engineer*

</div>

---

## 🎯 What is this?

A browser-based tool that eliminates the pain of manual DSM development in IBM QRadar. Instead of spending hours writing regex patterns and XML files by hand, this tool does it automatically:

1. **Connects to QRadar** via REST API using your SEC token
2. **Fetches real logs** for any source IP using Ariel queries
3. **Auto-detects log format** (CEF, LEEF, Syslog, JSON, Key=Value, W3C, NCSA)
4. **Maps Event IDs** to meaningful names using AI-powered analysis
5. **Generates complete DSM XML** with regex patterns and event mappings
6. **Imports directly** to QRadar Extension Management — one click

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Your Browser                         │
│                                                         │
│   ┌─────────────────────────────────────────────────┐   │
│   │          DSM_Builder.html                       │   │
│   │  ┌──────────┐  ┌──────────┐  ┌──────────────┐  │   │
│   │  │ QRadar   │  │  Auto    │  │  DSM Export  │  │   │
│   │  │ Connect  │  │ Analyzer │  │  & Import    │  │   │
│   │  └──────────┘  └──────────┘  └──────────────┘  │   │
│   └─────────────────────────────────────────────────┘   │
│              │  calls /qradar-proxy/                     │
└──────────────┼──────────────────────────────────────────┘
               │
┌──────────────▼──────────────────────────────────────────┐
│           dsm_server.py (Python — same server)          │
│                                                         │
│   ┌─────────────────┐    ┌───────────────────────────┐  │
│   │  Static File    │    │    QRadar API Proxy       │  │
│   │  Server :8080   │    │  /qradar-proxy/ → QRadar  │  │
│   └─────────────────┘    └───────────────────────────┘  │
└──────────────┬──────────────────────────────────────────┘
               │  HTTPS + SEC Token (server-to-server)
┌──────────────▼──────────────────────────────────────────┐
│              IBM QRadar Console                         │
│   ┌──────────────┐    ┌─────────────────────────────┐   │
│   │ Ariel Search │    │ Extension Management API    │   │
│   │ /api/ariel/  │    │ /api/config/extension_mgmt/ │   │
│   └──────────────┘    └─────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 🔌 **QRadar Live Fetch** | Fetch real logs via Ariel API by source IP |
| ⏱️ **Flexible Time Windows** | 30min / 1h / 2h / 6h / 12h / 24h / 48h / 72h + Custom range |
| 🔍 **Auto Format Detection** | CEF, LEEF, Syslog, JSON, Key=Value, W3C, NCSA, Windows Event Log |
| 🧠 **Smart Event Mapping** | Auto-maps Event IDs to meaningful QRadar event names |
| 📦 **DSM ZIP Generation** | Generates complete `content.xml` packaged as importable ZIP |
| 🚀 **Direct QRadar Import** | Uploads & installs DSM via Extension Management API |
| ⬇️ **Log Source Extension** | Exports LSE XML for existing log source types |
| 🌙 **Demo Mode** | Works offline with generated sample logs (no QRadar needed) |
| 🔒 **CORS-free Proxy** | Built-in Python proxy eliminates browser CORS restrictions |

---

## 📋 Requirements

| Component | Requirement |
|-----------|-------------|
| Python | 2.7+ or 3.x (no external packages needed) |
| Browser | Chrome / Firefox / Edge (modern) |
| QRadar | 7.3.x — 7.5.x (2021.6+) |
| Network | Server must reach QRadar Console on port 443 |
| SEC Token | QRadar API token with `ADMIN` or appropriate role |

---

## 🚀 Quick Start

### 1. Clone the repo

```bash
git clone https://github.com/0xTarek/Q-radar-dsm-builder.git
cd Q-radar-dsm-builder
```

### 2. Deploy files

```bash
sudo mkdir -p /opt/dsm-builder
sudo cp DSM_Builder.html /opt/dsm-builder/index.html
sudo cp dsm_server.py /opt/dsm-builder/dsm_server.py
```

### 3. Install as a service (runs permanently)

> **Python 3 only? (Ubuntu/Debian)** Run this first before installing the service:
> ```bash
> sudo sed -i 's|/usr/bin/python |/usr/bin/python3 |g' /etc/systemd/system/dsm-builder.service
> sudo sed -i 's|import urllib2|import urllib.request as urllib2|g' /opt/dsm-builder/dsm_server.py
> sudo sed -i 's|import BaseHTTPServer|import http.server as BaseHTTPServer|g' /opt/dsm-builder/dsm_server.py
> sudo sed -i 's|import SimpleHTTPServer|import http.server as SimpleHTTPServer|g' /opt/dsm-builder/dsm_server.py
> ```

```bash
sudo cp dsm-builder.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dsm-builder
sudo systemctl start dsm-builder
```

### 4. Verify it's running

```bash
sudo systemctl status dsm-builder
curl http://localhost:8080/index.html | head -3
```

### 5. Open in browser

```
http://<your-server-ip>:8080/index.html
```

---

## 🔑 Getting a QRadar SEC Token

1. Login to QRadar as Admin
2. Go to: **Admin → User Management → Users**
3. Select your user → **User Details**
4. Click **Authorized Services** → **Add Authorized Service**
5. Set: Name = `DSM-Builder`, Permissions = `Admin`
6. Copy the generated token

---

## 📖 Usage

### Live Mode (QRadar connected)

1. Enter **QRadar Console IP** and **SEC Token**
2. Enter **Source IP** of the log source device
3. Enter **DSM Name** (e.g. `Palo_Alto_DMZ`)
4. Select **Time Window** (or set custom range)
5. Click **Fetch & Analyze Logs**
6. Review the analysis results
7. Go to **DSM tab** → click **Import Directly to QRadar**

### Demo Mode (offline)

Leave QRadar IP and SEC Token empty — the tool generates realistic sample logs locally for testing and development.

---

## 📁 Repository Structure

```
qradar-dsm-builder/
├── DSM_Builder.html        ← Main tool (self-contained HTML/JS/CSS)
├── dsm_server.py           ← Python web server + QRadar API proxy
├── dsm-builder.service     ← systemd service file
├── README.md               ← This file
└── docs/
    └── INSTALL.md          ← Detailed installation guide
```

---

## 🔧 Supported Log Formats

| Format | Detection Method |
|--------|-----------------|
| **CEF** | `CEF:0|vendor|product` header |
| **LEEF** | `LEEF:1.0|vendor|product` header |
| **Syslog RFC5424** | `<priority>version timestamp` |
| **Syslog RFC3164** | `<priority>Month Day HH:MM:SS` |
| **JSON** | Valid JSON object/array |
| **Key=Value** | `key=value key2=value2` pairs |
| **W3C** | `#Version: #Fields:` directives |
| **NCSA/Combined** | Apache/nginx access log format |
| **Windows Event Log** | EventID/Source/Level structure |

---

## ⚠️ Notes

- The proxy server (`dsm_server.py`) must be on a host that can reach QRadar on port 443
- QRadar uses self-signed SSL certificates — the proxy disables SSL verification by design
- DSM import requires QRadar API version 14.0+ (QRadar 7.3.3+)
- Large time windows (48h/72h) may timeout — reduce Max Logs if needed

---

## 📜 License

MIT License — free to use, modify, and distribute.

---

## 👤 Author

**Tarek Farag**
Sr. Cyber Security Engineer | SIEM/SOAR Engineer

[![LinkedIn](https://img.shields.io/badge/LinkedIn-Connect-0A66C2?style=flat-square&logo=linkedin)](https://www.linkedin.com/in/tarekfarag45)
[![GitHub](https://img.shields.io/badge/GitHub-0xTarek-181717?style=flat-square&logo=github)](https://github.com/0xTarek)
[![Blog](https://img.shields.io/badge/Blog-0xtarek.github.io-00b0f0?style=flat-square)](https://0xtarek.github.io)

---

<div align="center">

*If this tool saved you time, give it a ⭐ — it helps others find it.*

</div>
