# YALAPM - Yet Another Linux APM Monitor

> 🚀 **A terminal-based Actions Per Minute monitor for Linux**  
> For tracking your performance during coding sessions and gaming

## 🎯 What is YALAPM?

YALAPM is a lightweight, system-wide APM (Actions Per Minute) monitor designed specifically for Linux users who want to track their keyboard and mouse activity during coding sessions, gaming, or any productivity work. Unlike web-based solutions, YALAPM runs natively on Linux and monitors **all** your actions across any application.

## ✨ Features

- 🖥️ **System-wide monitoring** - Tracks keyboard and mouse events globally
- 📊 **Real-time statistics** - Live APM, peak APM, average APM, average virtual effective APM and total actions
- 📉 **ASCII graph visualization** - Shows APM trends over time right in your terminal
- 📈 **Charts, tagging and report management** - Organize different sessions with tags, manage your reports and html generation for chart visualizations
- ✋ **Session control** - Start, Pause, Resume your sessions
- ⚡ **Lightweight** - Minimal resource usage, won't impact your workflow
- 🎮 **Gaming & coding ready** - Perfect for RTS games, competitive programming, or productivity tracking
- 🌙 **Terminal-based UI** - Clean, distraction-free interface that works on any Linux setup

## 🚀 Quick Start

### Installation

1. **Clone or download YALAPM:**
```bash
git clone https://github.com/splitpierre/yalapm.git
# or save the script as yalapm.py
```

2. **Install:**
```bash
pip install .
```

3. **Run YALAPM:**
```bash
yalapm
```

### First Run

When you start YALAPM, it will:
1. Check your system permissions
2. Show you the monitoring interface
3. Wait for your commands

## 🖼️ Interface Overview

![alt text](resources/yalapmTui.png)
---
![alt text](resources/dashboard.png)

### V1
```
╔══════════════════════════════════════════════════════════════╗
║                    LINUX APM MONITOR                         ║
╠══════════════════════════════════════════════════════════════╣
║  Current APM:        156 🔥                                  ║
║  Peak APM:           203 🏆                                  ║
║  Average APM:         89 📊                                  ║
║  Average veAPM:       56 🎮 (virtual 70%)                    ║
║  Total Actions:    4,521 🎯                                  ║
║  Session Time:    00:15:32 ⏱️                                ║
║  Status:       MONITORING 🟢                                 ║
╠══════════════════════════════════════════════════════════════╣
║  APM Trend (last 30s):                                       ║
║  ▃▅▇█▆▄▃▅▇██▆▄▂▁▃▄▆▇█▇▅▃▁▂▄▆▇█▇▅▃                            ║
╠══════════════════════════════════════════════════════════════╣
║  Press Ctrl+C to stop monitoring and see final report        ║
╚══════════════════════════════════════════════════════════════╝
```

## 💾 Basic Data Persistence

YALAPM automatically saves your reports to:
```
# Report Visualization
~/$HOME/Documents/YALAPM_Reports/index.html

# Report Files
~/$HOME/Documents/YALAPM_Reports/report_2025-[.....].json
```

This includes:
- Total actions in session
- Peak APM achieved
- Average APM
- Average veAPM
- Session duration
- Timestamp

## 🛠️ Technical Details

- **Language**: Python 3.6+
- **Dependencies**: `pynput` (for system-wide input monitoring), `textual` (for terminal UI)
- **Platform**: Linux (tested on Ubuntu, should work on most distributions)
- **Resource Usage**: < 10MB RAM, minimal CPU usage
- **Monitoring Method**: System-wide keyboard and mouse event capture

## 🤝 Contributing

Feel free to copy, modify, or contribute!

Found a bug? Want to add a feature? Contributions welcome!

1. Fork the project
2. Create your feature branch
3. Test on your Linux system  
4. Submit a pull request

---

**Made with ❤️ for the Linux community (and new influx of gamers).**

*May competitive RTS on linux be a thing, some day, right? 💭*

This code was generated with Claude.AI & Gemini assist, then tested/adapted by me ;) I just couldn't find something simple, that works system-wide, minimum dependencies, to display APM on my coding/gaming sessions.. 

*I`ll be working on this to fit my needs, if you like it give it a star and let me know what you'd like to see here!*

