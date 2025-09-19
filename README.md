# YALAPM - Yet Another Linux APM Monitor

> 🚀 **A terminal-based Actions Per Minute monitor for Linux**  
> For tracking your performance during coding sessions and gaming

## 🎯 What is YALAPM?

YALAPM is a lightweight, system-wide APM (Actions Per Minute) monitor designed specifically for Linux users who want to track their keyboard and mouse activity during coding sessions, gaming, or any productivity work. Unlike web-based solutions, YALAPM runs natively on Linux and monitors **all** your actions across any application.

## ✨ Features

- 🖥️ **System-wide monitoring** - Tracks keyboard and mouse events globally
- 📊 **Real-time statistics** - Live APM, peak APM, average APM, and total actions
- 📈 **ASCII graph visualization** - Shows APM trends over time right in your terminal
- 💾 **Session persistence** - Save and load your performance statistics  
- ⚡ **Lightweight** - Minimal resource usage, won't impact your workflow
- 🎮 **Gaming & coding ready** - Perfect for RTS games, competitive programming, or productivity tracking
- 🔧 **Robust permission handling** - Smart detection and solutions for Linux permission issues
- 🌙 **Terminal-based UI** - Clean, distraction-free interface that works on any Linux setup

## 🚀 Quick Start

### Installation

1. **Clone or download YALAPM:**
```bash
wget https://raw.githubusercontent.com/splitpierre/yalapm/refs/heads/main/yalapm.py
# or save the script as yalapm.py
```

2. **Install dependencies:**
```bash
pip install pynput
# or
sudo apt install python3-pynput
```

3. **Run YALAPM:**
```bash
python3 yalapm.py
```

### First Run

When you start YALAPM, it will:
1. Check your system permissions
2. Show you the monitoring interface
3. Wait for your commands

**Controls:**
- **[Enter]** - Start/stop monitoring
- **r** - Reset all statistics  
- **s** - Save current session
- **q** - Quit application

## 🖼️ Interface Overview

```
╔══════════════════════════════════════════════════════════════╗
║                    LINUX APM MONITOR                         ║
╠══════════════════════════════════════════════════════════════╣
║  Current APM:        156 🔥                                  ║
║  Peak APM:           203 🏆                                  ║
║  Average APM:         89 📊                                  ║
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

## 🔧 Troubleshooting

### Permission Issues

If YALAPM shows "PERMISSION ERROR 🔴", try these solutions:

**Option 1: Run with sudo (quickest)**
```bash
sudo python3 yalapm.py
```

**Option 2: Add user to input group**
```bash
sudo usermod -a -G input $USER
# Then logout and login again
```

**Option 3: Install system package**
```bash
sudo apt install python3-pynput
```

**Option 4: Check your session type**
```bash
echo $XDG_SESSION_TYPE
```
- If it shows `wayland`, you might need to switch to X11 session
- If it shows `x11`, permissions should work better

### Common Issues

**"Module pynput not found"**
- Install with: `pip install pynput` or `sudo apt install python3-pynput`

**"Permission denied" errors**
- Your user needs access to input devices
- Try running with `sudo` or add user to `input` group

**APM not updating**
- Make sure monitoring is started (press Enter)
- Check that YALAPM window has focus for terminal input
- Verify no permission errors are shown

## 🎮 Use Cases

### For Gamers
- **RTS Games**: Track your APM in StarCraft, Age of Empires, etc.
- **MOBA Games**: Monitor your reaction speed and input intensity
- **Competitive Gaming**: Measure improvement over time

### For Developers
- **Coding Sessions**: See how intensely you're working
- **Productivity Tracking**: Compare different working periods
- **Break Reminders**: Notice when APM drops (time for a break!)

### For General Users
- **Typing Speed**: Track your overall computer interaction
- **Work Patterns**: Understand your productivity rhythms
- **Performance Goals**: Set and track APM targets

## 💾 Data Persistence

YALAPM automatically saves your session statistics to:
```
~/.apm_monitor_stats.json
```

This includes:
- Total actions in session
- Peak APM achieved
- Average APM
- Session duration
- Timestamp

## 🛠️ Technical Details

- **Language**: Python 3.6+
- **Dependencies**: `pynput` (for system-wide input monitoring)
- **Platform**: Linux (tested on Ubuntu, should work on most distributions)
- **Resource Usage**: < 10MB RAM, minimal CPU usage
- **Monitoring Method**: System-wide keyboard and mouse event capture

## 🤝 Contributing

Found a bug? Want to add a feature? Contributions welcome!

1. Fork the project
2. Create your feature branch
3. Test on your Linux system  
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

**Made with ❤️ for the Linux community**  
*Because sometimes you just need to know how fast you're clicking...*
