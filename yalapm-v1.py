#!/usr/bin/env python3
"""
YALAPM - Yet Another Linux APM Monitor
Without TUI - Simple UI version
"""

import sys
import threading
import time
import os
import json
import subprocess
from collections import deque
from datetime import datetime, timedelta

try:
    from pynput import mouse, keyboard
except ImportError:
    print("❌ pynput not found. Installing...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pynput"])
        from pynput import mouse, keyboard
        print("✅ pynput installed successfully")
    except:
        print("❌ Failed to install pynput automatically.")
        print("Please run one of these commands:")
        print("  pip install pynput")
        print("  pip3 install pynput")
        print("  sudo apt install python3-pynput")
        sys.exit(1)


class RobustAPMMonitor:
    def __init__(self):
        self.monitoring_start = None  # Track when monitoring actually starts
        self.virtual_eapm = 0.7  # 70% virtual efficiency
        self.actions = deque(maxlen=3600)
        self.session_start = datetime.now()
        self.is_monitoring = False
        self.total_actions = 0
        self.peak_apm = 0
        self.apm_history = deque(maxlen=60)
        
        # Listeners
        self.mouse_listener = None
        self.keyboard_listener = None
        self.listener_error = None
        
        # Stats file
        self.stats_file = os.path.expanduser("~/.apm_monitor_stats.json")
        
        # Threading for display updates
        self.running = True
        self.display_thread = None
        
    def on_mouse_click(self, x, y, button, pressed):
        if pressed and self.is_monitoring:
            self.record_action()
            
    def on_key_press(self, key):
        if self.is_monitoring:
            self.record_action()
            
    def record_action(self):
        now = datetime.now()
        self.actions.append(now)
        self.total_actions += 1
        
    def calculate_current_apm(self):
        now = datetime.now()
        one_minute_ago = now - timedelta(minutes=1)
        recent_actions = [action for action in self.actions if action > one_minute_ago]
        return len(recent_actions)
        
    def calculate_average_apm(self):
        if not self.actions:
            return 0
        session_duration = (datetime.now() - self.session_start).total_seconds() / 60
        if session_duration > 0:
            return int(self.total_actions / session_duration)
        return 0
        
    def get_session_time(self):
        if self.monitoring_start is None:
            return "00:00:00"
        
        # Calculate total monitoring time
        if self.is_monitoring:
            session_duration = datetime.now() - self.monitoring_start
            hours, remainder = divmod(int(session_duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self._last_session_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            return self._last_session_time
        else:
            # When stopped, return the last calculated time (frozen)
            return getattr(self, '_last_session_time', "00:00:00")
        
    def start_monitoring(self):
        """Start monitoring with error handling"""
        if self.is_monitoring:
            return True
            
        try:
            # Create and start the listeners
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            
            self.mouse_listener.start()
            self.keyboard_listener.start()
            
            # Test if listeners are working
            time.sleep(0.1)
            if self.mouse_listener.running and self.keyboard_listener.running:
                self.is_monitoring = True
                self.monitoring_start = datetime.now()
                self.listener_error = None
                return True
            else:
                raise Exception("Listeners failed to start")
                
        except Exception as e:
            self.listener_error = str(e)
            self.is_monitoring = False
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
            return False
        
    def stop_monitoring(self):
        if self.is_monitoring and self.monitoring_start:
            # Save final session time before stopping
            session_duration = datetime.now() - self.monitoring_start
            hours, remainder = divmod(int(session_duration.total_seconds()), 3600)
            minutes, seconds = divmod(remainder, 60)
            self._last_session_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        self.is_monitoring = False
        try:
            if self.mouse_listener:
                self.mouse_listener.stop()
            if self.keyboard_listener:
                self.keyboard_listener.stop()
        except:
            pass
        
    def reset_stats(self):
        self.actions.clear()
        self.apm_history.clear() 
        self.total_actions = 0
        self.peak_apm = 0
        self.session_start = datetime.now()
        
    def save_stats(self):
        stats = {
            'total_actions': self.total_actions,
            'peak_apm': self.peak_apm,
            'avg_apm': self.calculate_average_apm(),
            'session_duration': (datetime.now() - self.session_start).total_seconds(),
            'timestamp': datetime.now().isoformat()
        }
        
        try:
            with open(self.stats_file, 'w') as f:
                json.dump(stats, f, indent=2)
            return True
        except Exception as e:
            return False
            
    def display_stats(self):
        # current_apm = self.calculate_current_apm()
        if self.is_monitoring:
            current_apm = self.calculate_current_apm()
            if current_apm > self.peak_apm:
                self.peak_apm = current_apm
            self.apm_history.append(current_apm)
        else:
            # When stopped, show last known APM but don't update it
            current_apm = self.apm_history[-1] if self.apm_history else 0

        avg_apm = self.calculate_average_apm()
        
        if current_apm > self.peak_apm:
            self.peak_apm = current_apm
            
        self.apm_history.append(current_apm)
        
        # Clear screen
        os.system('clear' if os.name == 'posix' else 'cls')
        
        print("╔══════════════════════════════════════════════════════════════╗")
        print("║                    LINUX APM MONITOR                         ║") 
        print("╠══════════════════════════════════════════════════════════════╣")
        print(f"║  Current APM:     {current_apm:>6} {'🔥' if current_apm > 100 else '⚡' if current_apm > 50 else '📈' if current_apm > 0 else '💤'}                                  ║")
        print(f"║  Peak APM:        {self.peak_apm:>6} 🏆                                  ║")
        print(f"║  Average APM:     {avg_apm:>6} 📊                                  ║")
        virtual_eapm = int(avg_apm * self.virtual_eapm)
        print(f"║  Average veAPM:   {virtual_eapm:>6} 🎮 (virtual {int(self.virtual_eapm*100)}%)                    ║")
        print(f"║  Total Actions:   {self.total_actions:>6,} 🎯                                  ║")
        print(f"║  Session Time:    {self.get_session_time():>8} ⏱️                                 ║")
        
        # Status with error info
        if self.is_monitoring:
            status = "MONITORING 🟢"
        elif self.listener_error:
            status = "PERMISSION ERROR 🔴"
        else:
            status = "STOPPED 🔴"
        print(f"║  Status:          {status:>15}                           ║")
        
        if self.listener_error:
            print("╠══════════════════════════════════════════════════════════════╣")
            print("║  ⚠️  PERMISSION ISSUE DETECTED                              ║")
            print("║  Try running with sudo, or check accessibility settings     ║")
        
        print("╠══════════════════════════════════════════════════════════════╣")
        
        # Simple ASCII graph
        if len(self.apm_history) > 0:
            print("║  APM Trend (last 30s):                                       ║")
            recent = list(self.apm_history)[-30:]
            if recent and max(recent) > 0:
                max_apm = max(recent)
                graph_line = "║  "
                for apm in recent:
                    height = int((apm / max_apm) * 8) if max_apm > 0 else 0
                    chars = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
                    graph_line += chars[height]
                graph_line += " " * (60 - len(graph_line)) + "   ║"
                print(graph_line)
            else:
                print("║  " + "─" * 56 + "    ║")
                
        print("╠══════════════════════════════════════════════════════════════╣")
        print("║  Press Ctrl+C to stop monitoring and see final report        ║")
        print("╚══════════════════════════════════════════════════════════════╝")
        
        if self.listener_error:
            print("\n🔧 TROUBLESHOOTING:")
            print("1. Try running with: sudo python3 apm_monitor.py")
            print("2. Ubuntu: Install 'python3-pynput' package")
            print("3. Some systems need X11 forwarding or different permissions")
            
    def run_simple_ui(self):
        """Auto-start monitoring, quit with Ctrl+C"""
        print("🚀 YALAPM - Yet Another Linux APM Monitor")
        print("📊 Auto-starting system-wide monitoring...")
        print("💡 Press Ctrl+C to stop and see final report")
        print()
        
        # Auto-start monitoring
        success = self.start_monitoring()
        if not success:
            print("❌ Failed to start monitoring - permission issue")
            print("🔧 Try running with: sudo python3 yalapm.py")
            return
        
        print("🟢 Monitoring active! Tracking all keyboard/mouse events...")
        print()
        
        try:
            # Simple display loop
            while self.running:
                self.display_stats()
                time.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitor...")
            self.stop_monitoring()
            self.print_final_report()
        finally:
            self.running = False
            self.save_stats()

    def print_final_report(self):
        """Print final session summary"""
        print("\n" + "="*60)
        print("📋 FINAL SESSION REPORT")
        print("="*60)
        print(f"🏆 Peak APM:        {self.peak_apm}")
        print(f"📊 Average APM:     {self.calculate_average_apm()}")
        print(f"🎯 Total Actions:   {self.total_actions:,}")
        print(f"⏱️  Session Time:    {self.get_session_time()}")
        print(f"💾 Stats saved to:  {self.stats_file}")
        print("="*60)
        print("Thanks for using YALAPM! 🚀")


def check_permissions():
    """Check if we can access input devices"""
    try:
        # Try to create listeners briefly
        mouse_test = mouse.Listener(on_click=lambda x,y,b,p: None)
        keyboard_test = keyboard.Listener(on_press=lambda k: None)
        
        mouse_test.start()
        keyboard_test.start()
        time.sleep(0.1)
        
        mouse_test.stop()
        keyboard_test.stop()
        
        return True
    except Exception as e:
        return False


if __name__ == "__main__":
    print("🔍 Checking system compatibility...")

    # Check permissions first
    if not check_permissions():
        print("⚠️  Permission issue detected!")
        print("🔧 Solutions:")
        print("   1. Run with sudo: sudo python3 apm_monitor.py")
        print("   2. Install system package: sudo apt install python3-pynput")
        print("   3. Add user to input group: sudo usermod -a -G input $USER")
        print("   4. Some systems need X11 session or different setup")
        print("\n🚀 Starting anyway (some features may not work)...")
    else:
        print("✅ Permissions look good!")
        
    try:
        monitor = RobustAPMMonitor()
        monitor.run_simple_ui()
    except Exception as e:
        print(f"💥 Unexpected error: {e}")
        print("🔧 Try running with sudo or check your Python environment")
