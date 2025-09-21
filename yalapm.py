#!/usr/bin/env python3
"""
YALAPM - Yet Another Linux APM Monitor
Now with a responsive Textual TUI!
"""
import sys
import threading
import time
import os
import json
import subprocess
import webbrowser
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path

# --- Dependency Management ---

def install_package(package_name):
    print(f"❌ {package_name} not found. Attempting to install...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package_name])
        print(f"✅ {package_name} installed successfully.")
        return True
    except Exception as e:
        print(f"❌ Failed to install {package_name} automatically: {e}")
        print(f"   Please run: pip install {package_name}")
        return False

try:
    from pynput import mouse, keyboard
except ImportError:
    if not install_package("pynput"): sys.exit(1)
    from pynput import mouse, keyboard

try:
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static
    from textual.containers import Container
    from textual.reactive import reactive
except ImportError:
    if not install_package("textual"): sys.exit(1)
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static
    from textual.containers import Container
    from textual.reactive import reactive


# --- Monitoring Engine ---

class APMMonitorEngine:
    """Handles the backend logic for monitoring APM."""
    def __init__(self):
        self.monitoring_start = None
        self.virtual_eapm_factor = 0.7
        self.actions = deque()
        self.session_start = datetime.now()
        self.is_monitoring = False
        self.total_actions = 0
        self.peak_apm = 0
        self.apm_history = deque(maxlen=300) # 5 minutes of history

        self.mouse_listener = None
        self.keyboard_listener = None
        self.listener_error = None

        # Save reports to Documents folder for better visibility
        self.reports_dir = Path.home() / "Documents" / "YALAPM_Reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)

        self.state = "STOPPED"  # Can be STOPPED, RUNNING, PAUSED
        self.total_active_duration = timedelta(0)
        self.last_tick_time = None

    def record_action(self):
        if self.state != "RUNNING":
            return # Ignore actions if not running
        self.actions.append(datetime.now())
        self.total_actions += 1

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and self.is_monitoring: self.record_action()

    def on_key_press(self, key):
        if self.is_monitoring: self.record_action()

    def get_stats(self):
        """Calculate and return a dictionary of current stats."""
        now = datetime.now()
        
        if self.state == "RUNNING":
            if self.last_tick_time:
                self.total_active_duration += now - self.last_tick_time
            self.last_tick_time = now

        one_minute_ago = now - timedelta(minutes=1)
        while self.actions and self.actions[0] < one_minute_ago:
            self.actions.popleft()
        current_apm = len(self.actions)

        if self.is_monitoring:
            if current_apm > self.peak_apm:
                self.peak_apm = current_apm
            self.apm_history.append(current_apm)
        
        session_duration_min = self.total_active_duration.total_seconds() / 60
        avg_apm = int(self.total_actions / session_duration_min) if session_duration_min > 0 else 0
        
        hours, rem = divmod(int(self.total_active_duration.total_seconds()), 3600)
        mins, secs = divmod(rem, 60)
        session_time = f"{hours:02d}:{mins:02d}:{secs:02d}"

        # session_time = "00:00:00"
        if self.monitoring_start:
            duration = now - self.monitoring_start
            hours, rem = divmod(int(duration.total_seconds()), 3600)
            mins, secs = divmod(rem, 60)
            session_time = f"{hours:02d}:{mins:02d}:{secs:02d}"

        return {
            "current_apm": current_apm,
            "peak_apm": self.peak_apm,
            "average_apm": avg_apm,
            "average_veapm": int(avg_apm * self.virtual_eapm_factor),
            "total_actions": self.total_actions,
            "session_time": session_time,
            "status": f"{self.state} {'🟢' if self.state == 'RUNNING' else '🟡' if self.state == 'PAUSED' else '🔴'}",
            "apm_history": list(self.apm_history)
        }

    def start(self):
        """Start the input listeners."""
        if self.state != "STOPPED":
            return
        try:
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.mouse_listener.start()
            self.keyboard_listener.start()

            self.state = "RUNNING"
            self.last_tick_time = datetime.now()
            
            self.is_monitoring = True
            self.monitoring_start = datetime.now()
            self.session_start = datetime.now()
            self.listener_error = None
            return True
        except Exception as e:
            self.listener_error = str(e)
            self.is_monitoring = False
            return False
    def pause(self):
        """Pauses the current session."""
        if self.state == "RUNNING":
            self.state = "PAUSED"
            # Invalidate last_tick_time to stop duration accumulation
            self.last_tick_time = None
    def resume(self):
        """Resumes a paused session."""
        if self.state == "PAUSED":
            self.state = "RUNNING"
            self.last_tick_time = datetime.now()
    def reset(self):
        """Resets all stats for a new session."""
        if self.state != "STOPPED":
            self.stop() # Save the previous session first
        
        # Clear all metrics
        self.actions.clear()
        self.apm_history.clear()
        self.total_actions = 0
        self.peak_apm = 0
        self.session_start = datetime.now()
        self.total_active_duration = timedelta(0)
        self.last_tick_time = None
        self.state = "STOPPED"

    def stop(self):
        """Stops the listeners and saves the session if active."""
        if self.state == "STOPPED":
            return None # Nothing to save
            
        self.state = "STOPPED"
        self.last_tick_time = None
        if self.mouse_listener: self.mouse_listener.stop()
        if self.keyboard_listener: self.keyboard_listener.stop()
        return self.save_session()
    
    def open_report_folder(self):
        """Opens the report directory in the system's file explorer."""
        if sys.platform == "win32":
            os.startfile(self.reports_dir)
        elif sys.platform == "darwin":
            subprocess.run(["open", self.reports_dir])
        else:
            subprocess.run(["xdg-open", self.reports_dir])

    def get_report_path(self):
        return self.reports_dir / "index.html"

    def save_session(self):
        """Save the final session stats to a JSON file and update HTML."""
        stats = self.get_stats()
        final_stats = {
            'total_actions': stats['total_actions'],
            'peak_apm': stats['peak_apm'],
            'average_apm': stats['average_apm'],
            'average_veapm': stats['average_veapm'],
            'session_duration_seconds': (datetime.now() - self.session_start).total_seconds(),
            'report_datetime': datetime.now().isoformat()
        }
        
        filename = f"report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        filepath = self.reports_dir / filename
        with open(filepath, 'w') as f:
            json.dump(final_stats, f, indent=2)
            
        return self.generate_html_report()

    def generate_html_report(self):
        """Generate an index.html file with a list of reports and a chart."""
        report_files = sorted(self.reports_dir.glob('*.json'))
        
        all_data = []
        for file in report_files:
            with open(file, 'r') as f:
                all_data.append(json.load(f))

        html_path = self.reports_dir / "index.html"
        html_content = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8"><title>YALAPM Reports</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; margin: 2em; background-color: #f4f4f9; color: #333; }}
                h1, h2 {{ color: #444; }}
                .container {{ display: flex; flex-wrap: wrap; gap: 2em; }}
                .reports-list {{ flex: 1; min-width: 300px; }}
                .chart-container {{ flex: 2; min-width: 400px; background: white; padding: 1em; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                ul {{ list-style-type: none; padding: 0; }} li {{ margin-bottom: 0.5em; }}
                a {{ text-decoration: none; color: #007bff; }} a:hover {{ text-decoration: underline; }}
            </style>
        </head>
        <body>
            <h1>YALAPM Session Reports Dashboard</h1>
            <div class="container">
                <div class="reports-list">
                    <h2>Saved Sessions</h2>
                    <ul>{''.join(f'<li><a href="{f.name}">{f.name}</a></li>' for f in report_files)}</ul>
                </div>
                <div class="chart-container">
                    <h2>Historical APM Performance</h2>
                    <canvas id="apmChart"></canvas>
                </div>
            </div>
            <script>
                const reportsData = {json.dumps(all_data)};
                const labels = reportsData.map(r => new Date(r.report_datetime).toLocaleString());
                new Chart(document.getElementById('apmChart').getContext('2d'), {{
                    type: 'line',
                    data: {{
                        labels: labels,
                        datasets: [
                            {{ label: 'Average APM', data: reportsData.map(r => r.average_apm), borderColor: 'rgba(75, 192, 192, 1)', tension: 0.1 }},
                            {{ label: 'Average veAPM', data: reportsData.map(r => r.average_veapm), borderColor: 'rgba(255, 99, 132, 1)', tension: 0.1 }}
                        ]
                    }},
                    options: {{ responsive: true, scales: {{ x: {{ title: {{ display: true, text: 'Report Date' }} }}, y: {{ title: {{ display: true, text: 'APM' }} }} }} }}
                }});
            </script>
        </body>
        </html>
        """
        with open(html_path, 'w') as f:
            f.write(html_content)
        return html_path


# --- Textual TUI ---

class APMDisplay(Static):
    """A widget to display a single APM metric."""
    value = reactive(0)
    def __init__(self, label, icon, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.icon = icon
    
    def watch_value(self, value: int) -> None:
        self.update(f"{self.icon} {self.label:<16} [b]{value:>6,}[/b]")

class APMGraph(Static):
    """A widget to display the APM trend graph."""
    history = reactive(list)
    MAX_BAR_HEIGHT = 8  # How many lines tall the graph is
    def watch_history(self, history: list) -> None:
        graph_width = self.size.width
        if not history or graph_width <= 0:
            self.update("")
            return

        max_apm = max(history) if history else 1
        grid = [[' '] * graph_width for _ in range(self.MAX_BAR_HEIGHT)]
        bar_chars = [' ', ' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        graph = ""
        for i in range(graph_width):
            idx = int(i * len(history) / graph_width)
            apm = history[idx]
            
            # Calculate bar height, including fractional parts
            bar_height = (apm / max_apm) * self.MAX_BAR_HEIGHT if max_apm > 0 else 0
            full_bars = int(bar_height)
            fractional_part = bar_height - full_bars
            
            # Draw full bars from the bottom up
            for y in range(full_bars):
                grid[self.MAX_BAR_HEIGHT - 1 - y][i] = '█'

            # Draw the fractional top of the bar
            if full_bars < self.MAX_BAR_HEIGHT:
                char_index = int(fractional_part * (len(bar_chars) -1))
                grid[self.MAX_BAR_HEIGHT - 1 - full_bars][i] = bar_chars[char_index]

        # Convert the grid to a single multi-line string
        graph_str = "\n".join("".join(row) for row in grid)
        self.update(graph_str)

class YalapmTUI(App):
    """The Textual TUI application for YALAPM."""

    CSS = """
    Screen {
        background: $surface-darken-1;
    }
    #main_container {
        layout: grid;
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
        border: thick $primary-lighten-2;
        border-title-align: center;
    }
    APMDisplay {
        content-align: left middle;
        height: 3;
        background: $surface-lighten-1;
        padding: 0 1;
    }
    #session_time, #status {
        column-span: 2;
        content-align: center middle;
        background: $surface;
        padding: 0 1;
    }
    #controls_hint {
        column-span: 2;
        height: 3;
        content-align: center middle;
        background: $primary-darken-2;
    }
    #graph {
        column-span: 2;
        height: 12; /* Increased height for the new graph */
        border: wide $surface-lighten-2;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("s", "start_resume", "Start/Resume"),
        ("p", "pause", "Pause"),
        ("r", "reset", "Reset Session"),
        ("f", "open_folder", "Open Folder"),
        ("v", "view_report", "View Report"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, engine):
        super().__init__()
        self.engine = engine

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main_container"):
            yield APMDisplay("Current APM:", "⚡", id="current_apm")
            yield APMDisplay("Peak APM:", "🏆", id="peak_apm")
            yield APMDisplay("Average APM:", "📊", id="avg_apm")
            yield APMDisplay("Average veAPM:", "🎮", id="veapm")
            yield APMDisplay("Total Actions:", "🎯", id="total_actions")
            yield Static("", id="session_time")
            yield Static("", id="status")
            yield Static("", id="controls_hint")
            yield APMGraph(id="graph")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1, self.update_display)
        self.query_one("#main_container").border_title = "YALAPM"
        self.query_one("#graph").border_title = "APM Trend (last 5 mins)"
    
    def update_footer(self) -> None:
        """Dynamically update footer actions based on state."""
        if self.engine.state == "PAUSED":
            self.screen.bindings["s"].key_display = "s (Resume)"
        else:
            self.screen.bindings["s"].key_display = "s (Start)"
        self.refresh()

    def update_display(self) -> None:
        """Called every second to refresh the UI with new stats."""
        stats = self.engine.get_stats()
        self.query_one("#current_apm", APMDisplay).value = stats["current_apm"]
        self.query_one("#peak_apm", APMDisplay).value = stats["peak_apm"]
        self.query_one("#avg_apm", APMDisplay).value = stats["average_apm"]
        self.query_one("#veapm", APMDisplay).value = stats["average_veapm"]
        self.query_one("#total_actions", APMDisplay).value = stats["total_actions"]
        self.query_one("#session_time").update(f"⏱️ Session Time:   [b]{stats['session_time']}[/b]")
        self.query_one("#status").update(f"   Status:         [b]{stats['status']}[/b]")
        self.query_one(APMGraph).history = stats["apm_history"]
        hint_widget = self.query_one("#controls_hint")
        if self.engine.state == "STOPPED":
            hint_widget.update("💡 [b]Press 's' to START Session[/b]")
        elif self.engine.state == "RUNNING":
            hint_widget.update("💡 [b]Press 'p' to PAUSE Session[/b]")
        elif self.engine.state == "PAUSED":
            hint_widget.update("💡 [b]Press 's' to RESUME Session[/b]")
    
    def action_start_resume(self) -> None:
        if self.engine.state == "STOPPED":
            self.engine.start()
        elif self.engine.state == "PAUSED":
            self.engine.resume()

    def action_pause(self) -> None:
        self.engine.pause()

    def action_reset(self) -> None:
        self.engine.reset()
        self.engine.start() # Start a new session immediately

    def action_open_folder(self) -> None:
        self.engine.open_report_folder()
    
    def action_view_report(self) -> None:
        report_path = self.engine.get_report_path()
        if report_path.exists():
            webbrowser.open_new_tab(report_path.as_uri())
        else:
            self.notify("No report file exists yet. Stop a session first.", title="Info", severity="information")

    def action_quit(self) -> None:
        """Called when user presses 'q' or Ctrl+C."""
        report_path = self.engine.stop()
        if report_path:
            webbrowser.open_new_tab(report_path.as_uri())
            self.exit(f"\n✅ Report saved and opened. Location: {report_path}")
        else:
            self.exit("\n✅ Session finished. No data to save.")


# --- Main Execution ---

def check_permissions():
    """Briefly check if we have permissions to listen to input devices."""
    try:
        m_test = mouse.Listener(on_click=lambda *args: None)
        k_test = keyboard.Listener(on_press=lambda k: None)
        m_test.start(); k_test.start()
        time.sleep(0.1)
        m_test.stop(); k_test.stop()
        return True
    except Exception:
        return False

if __name__ == "__main__":
    print("🔍 Checking system compatibility...")
    if not check_permissions():
        print("\n⚠️  Permission issue detected!")
        print("   This script needs permission to listen to keyboard and mouse events.")
        print("   On Linux, you may need to run this with sudo:")
        print("   $ sudo python3 yalapm.py\n")
        sys.exit(1)
    else:
        print("✅ Permissions look good!")

    try:
        engine = APMMonitorEngine()
        app = YalapmTUI(engine)
        app.run()
    except Exception as e:
        print(f"💥 An unexpected error occurred: {e}")