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
from collections import deque, defaultdict
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
    from textual.widgets import Header, Footer, Static, Input, Button, Label, ListView, ListItem
    from textual.containers import Container, Vertical, Horizontal
    from textual.screen import ModalScreen
    from textual.reactive import reactive
except ImportError:
    if not install_package("textual"): sys.exit(1)
    from textual.app import App, ComposeResult
    from textual.widgets import Header, Footer, Static, Input, Button, Label, ListView, ListItem
    from textual.containers import Container, Vertical, Horizontal
    from textual.screen import ModalScreen
    from textual.reactive import reactive


# --- Monitoring Engine ---

class APMMonitorEngine:
    """Handles the backend logic for monitoring APM."""
    def __init__(self):
        self.virtual_eapm_factor = 0.7
        self.actions = deque()
        self.session_start = datetime.now()
        self.apm_history = deque(maxlen=300)
        self.mouse_listener = None
        self.keyboard_listener = None
        self.reports_dir = Path.home() / "Documents" / "YALAPM_Reports"
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.state = "STOPPED"
        self.total_active_duration = timedelta(0)
        self.last_tick_time = None
        self.session_tag = "untagged"
        self.reset_metrics()

    def reset_metrics(self):
        self.actions.clear()
        self.apm_history.clear()
        self.total_actions = 0
        self.peak_apm = 0
        self.session_start = datetime.now()
        self.total_active_duration = timedelta(0)
        self.last_tick_time = None

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and self.state == "RUNNING": self.record_action()

    def on_key_press(self, key):
        if self.state == "RUNNING": self.record_action()

    def record_action(self):
        self.actions.append(datetime.now())
        self.total_actions += 1

    def get_stats(self):
        now = datetime.now()
        if self.state == "RUNNING":
            if self.last_tick_time:
                self.total_active_duration += now - self.last_tick_time
            self.last_tick_time = now

        one_minute_ago = now - timedelta(minutes=1)
        while self.actions and self.actions[0] < one_minute_ago:
            self.actions.popleft()
        current_apm = len(self.actions)

        if self.state == "RUNNING":
            if current_apm > self.peak_apm:
                self.peak_apm = current_apm
            self.apm_history.append(current_apm)
        
        session_duration_min = self.total_active_duration.total_seconds() / 60
        avg_apm = int(self.total_actions / session_duration_min) if session_duration_min > 0 else 0
        
        hours, rem = divmod(int(self.total_active_duration.total_seconds()), 3600)
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

    def start(self, tag: str, veapm: float):
        if self.state != "STOPPED": return
        self.reset_metrics()
        self.session_tag = tag
        self.virtual_eapm_factor = veapm
        try:
            self.mouse_listener = mouse.Listener(on_click=self.on_mouse_click)
            self.keyboard_listener = keyboard.Listener(on_press=self.on_key_press)
            self.mouse_listener.start()
            self.keyboard_listener.start()
            self.state = "RUNNING"
            self.last_tick_time = datetime.now()
        except Exception as e:
            self.state = "STOPPED"

    def pause(self):
        if self.state == "RUNNING":
            self.state = "PAUSED"
            self.last_tick_time = None

    def resume(self):
        if self.state == "PAUSED":
            self.state = "RUNNING"
            self.last_tick_time = datetime.now()

    def reset_and_start(self, tag: str, veapm: float):
        if self.state != "STOPPED": self.stop()
        self.start(tag, veapm)

    def stop(self):
        if self.state == "STOPPED": return None
        self.state = "STOPPED"
        self.last_tick_time = None
        if self.mouse_listener: self.mouse_listener.stop()
        if self.keyboard_listener: self.keyboard_listener.stop()
        return self.save_session()

    def open_report_folder(self):
        if sys.platform == "win32": os.startfile(self.reports_dir)
        elif sys.platform == "darwin": subprocess.run(["open", self.reports_dir])
        else: subprocess.run(["xdg-open", self.reports_dir])

    def get_report_path(self):
        return self.reports_dir / "index.html"

    def save_session(self):
        if self.total_actions == 0: return self.generate_html_report()
        stats = self.get_stats()
        final_stats = {
            'tag': self.session_tag,
            'virtual_eapm_factor': self.virtual_eapm_factor,
            'total_actions': stats['total_actions'],
            'peak_apm': stats['peak_apm'],
            'average_apm': stats['average_apm'],
            'average_veapm': stats['average_veapm'],
            'session_duration_seconds': self.total_active_duration.total_seconds(),
            'report_datetime': datetime.now().isoformat()
        }
        
        filename = f"report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.json"
        filepath = self.reports_dir / filename
        with open(filepath, 'w') as f: json.dump(final_stats, f, indent=2)
        return self.generate_html_report()

    def get_all_reports(self):
        reports_by_tag = defaultdict(list)
        report_files = sorted(self.reports_dir.glob('*.json'))
        for file in report_files:
            try:
                with open(file, 'r') as f:
                    data = json.load(f)
                    data['filename'] = file.name
                    tag = data.get('tag', 'untagged')
                    reports_by_tag[tag].append(data)
            except (json.JSONDecodeError, IOError):
                continue
        return reports_by_tag

    def delete_report(self, filename: str):
        report_path = self.reports_dir / filename
        if report_path.exists() and report_path.is_file():
            report_path.unlink()
            self.generate_html_report()
            return True
        return False

    def delete_tag(self, tag: str):
        reports_by_tag = self.get_all_reports()
        if tag in reports_by_tag:
            for report in reports_by_tag[tag]:
                report_path = self.reports_dir / report['filename']
                if report_path.exists():
                    report_path.unlink()
            self.generate_html_report()
            return True
        return False

    def generate_html_report(self):
        reports_by_tag = self.get_all_reports()
        all_data = [report for reports in reports_by_tag.values() for report in reports]

        # Dynamically create filter options for the dropdown
        filter_options = ['<option value="all">All Tags</option>']
        for tag in sorted(reports_by_tag.keys()):
            filter_options.append(f'<option value="{tag}">{tag}</option>')

        def render_tag_section(tag, reports):
            items = []
            for r in reports:
                dt = datetime.fromisoformat(r['report_datetime']).strftime('%Y-%m-%d %H:%M')
                items.append(f"<li><a href=\"{r['filename']}\">{dt}</a> - Avg APM: {r['average_apm']}</li>")
            return f"""
            <div class="tag-group">
                <h3>Tag: {tag}</h3>
                <ul>{''.join(items)}</ul>
            </div>"""

        html_path = self.reports_dir / "index.html"
        html_content = f"""
        <!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>YALAPM Reports</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
            <style>
                body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 2em; background: #f4f4f9; color: #333; }}
                h1, h2, h3 {{ color: #444; }}
                .container {{ display: flex; flex-wrap: wrap; gap: 2em; }}
                .reports-list {{ flex: 1; min-width: 350px; }}
                .chart-container {{ flex: 2; min-width: 400px; background: #fff; padding: 1em; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }}
                ul {{ list-style-type: none; padding: 0; }} li {{ margin-bottom: 0.5em; padding: 0.5em; background: #fff; border-radius: 4px; }}
                a {{ text-decoration: none; color: #007bff; }} a:hover {{ text-decoration: underline; }}
                .tag-group {{ margin-bottom: 1.5em; border: 1px solid #ddd; padding: 1em; border-radius: 8px; background: #fafafa; }}
                .chart-controls {{ margin-bottom: 1em; }}
                .chart-controls label {{ font-weight: bold; margin-right: 10px; }}
                .chart-controls select {{ padding: 5px; border-radius: 4px; border: 1px solid #ccc; }}
            </style>
        </head><body>
            <h1>YALAPM Session Reports Dashboard</h1>
            <div class="container">
                <div class="reports-list">
                    <h2>Saved Sessions</h2>
                    {''.join(render_tag_section(tag, reports) for tag, reports in reports_by_tag.items())}
                </div>
                <div class="chart-container">
                    <div class="chart-controls">
                        <label for="tagFilter">Filter Chart by Tag:</label>
                        <select id="tagFilter">
                            {''.join(filter_options)}
                        </select>
                    </div>
                    <h2>Historical APM Performance</h2><canvas id="apmChart"></canvas>
                </div>
            </div>
            <script>
                const reportsByTag = {json.dumps(reports_by_tag)};
                const allReports = {json.dumps(all_data)};
                let apmChart;

                function updateChart(selectedTag) {{
                    let sourceData;
                    if (selectedTag === 'all') {{
                        sourceData = allReports;
                    }} else {{
                        sourceData = reportsByTag[selectedTag] || [];
                    }}

                    // Sort data by date to ensure the line chart is chronological
                    sourceData.sort((a, b) => new Date(a.report_datetime) - new Date(b.report_datetime));
                    
                    const labels = sourceData.map(r => new Date(r.report_datetime).toLocaleString());
                    const avgApmData = sourceData.map(r => r.average_apm);
                    const veApmData = sourceData.map(r => r.average_veapm);

                    apmChart.data.labels = labels;
                    apmChart.data.datasets[0].data = avgApmData;
                    apmChart.data.datasets[1].data = veApmData;
                    apmChart.update();
                }}

                document.addEventListener('DOMContentLoaded', () => {{
                    const ctx = document.getElementById('apmChart').getContext('2d');
                    apmChart = new Chart(ctx, {{
                        type: 'line', 
                        data: {{ 
                            labels: [], // Initially empty
                            datasets: [
                                {{ label: 'Average APM', data: [], borderColor: 'rgba(75, 192, 192, 1)', tension: 0.1 }},
                                {{ label: 'Average veAPM', data: [], borderColor: 'rgba(255, 99, 132, 1)', tension: 0.1 }} 
                            ]
                        }},
                        options: {{ 
                            responsive: true, 
                            scales: {{ 
                                x: {{ title: {{ display: true, text: 'Report Date' }} }}, 
                                y: {{ title: {{ display: true, text: 'APM' }} }} 
                            }} 
                        }}
                    }});

                    // Initial chart load
                    updateChart('all');

                    // Add event listener for the filter
                    document.getElementById('tagFilter').addEventListener('change', (event) => {{
                        updateChart(event.target.value);
                    }});
                }});
            </script>
        </body></html>"""
        with open(html_path, 'w') as f: f.write(html_content)
        return html_path

# --- Textual TUI ---

class APMDisplay(Static):
    value = reactive(0)
    def __init__(self, label, icon, **kwargs):
        super().__init__(**kwargs)
        self.label, self.icon = label, icon
    def watch_value(self, value: int):
        self.update(f"{self.icon} {self.label:<16} [b]{value:>6,}[/b]")

class APMGraph(Static):
    history = reactive(list)
    MAX_BAR_HEIGHT = 8
    def watch_history(self, history: list):
        graph_width = self.size.width
        if not history or graph_width <= 0:
            self.update(""); return
        max_apm = max(history) if history else 1
        grid = [[' '] * graph_width for _ in range(self.MAX_BAR_HEIGHT)]
        bar_chars = [' ', ' ', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        for i in range(graph_width):
            idx = int(i * len(history) / graph_width)
            bar_height = (history[idx] / max_apm) * self.MAX_BAR_HEIGHT if max_apm > 0 else 0
            full_bars, fractional_part = int(bar_height), bar_height - int(bar_height)
            for y in range(full_bars): grid[self.MAX_BAR_HEIGHT - 1 - y][i] = '█'
            if full_bars < self.MAX_BAR_HEIGHT:
                grid[self.MAX_BAR_HEIGHT - 1 - full_bars][i] = bar_chars[int(fractional_part * (len(bar_chars) - 1))]
        self.update("\n".join("".join(row) for row in grid))

class StartSessionScreen(ModalScreen):
    def compose(self) -> ComposeResult:
        with Vertical(id="start_dialog"):
            yield Label("Start New Session", id="start_title")
            yield Input(placeholder="Session Tag (e.g., coding, aoe2)", id="tag_input")
            yield Input(value="70", placeholder="Virtual eAPM % (e.g., 70)", id="veapm_input")
            yield Button("Start", variant="primary", id="start_button")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "start_button":
            tag = self.query_one("#tag_input").value or "untagged"
            try:
                veapm_percent = float(self.query_one("#veapm_input").value)
                veapm = veapm_percent / 100.0
                if not (0 <= veapm <= 1): veapm = 0.7
            except (ValueError, TypeError):
                veapm = 0.7
            self.dismiss((tag, veapm))

class ReportItem(Static):
    def __init__(self, report_data: dict) -> None:
        super().__init__()
        self.report_data = report_data
    def compose(self) -> ComposeResult:
        dt = datetime.fromisoformat(self.report_data['report_datetime']).strftime('%Y-%m-%d %H:%M')
        info = f"{dt} - Avg APM: {self.report_data['average_apm']}"
        with Horizontal(id="horizontal_item"):
            yield Label(info, classes="report_label")
            yield Button("Delete", variant="error", classes="delete_report")

class TagHeader(Static):
    def __init__(self, tag_name: str) -> None:
        super().__init__()
        self.tag_name = tag_name
    def compose(self) -> ComposeResult:
        with Horizontal(id="horizontal_tag"):
            yield Label(f"Tag: {self.tag_name}", classes="tag_label")
            yield Button("Delete Tag", variant="error", classes="delete_tag")

class ReportManagerScreen(ModalScreen):
    def __init__(self, engine: APMMonitorEngine) -> None:
        super().__init__()
        self.engine = engine
    def compose(self) -> ComposeResult:
        with Vertical(id="report_manager_dialog"):
            yield Label("Report Manager", id="report_manager_title")
            yield ListView(id="report_list")
            yield Button("Close", variant="primary", id="close_manager")

    def on_mount(self) -> None:
        self.populate_list()

    def populate_list(self) -> None:
        list_view = self.query_one(ListView)
        list_view.clear()
        reports_by_tag = self.engine.get_all_reports()
        for tag, reports in reports_by_tag.items():
            list_view.append(ListItem(TagHeader(tag), classes="tag_header_item"))
            for report in reports:
                list_view.append(ListItem(ReportItem(report)))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "close_manager":
            self.app.pop_screen()
            return
        
        # --- Start of Fix ---
        # A widget's parent is found via the .parent attribute.
        # The button's parent is a Horizontal container.
        # The Horizontal's parent is the ReportItem or TagHeader we want.
        widget = event.button.parent.parent
        
        if "delete_report" in event.button.classes and isinstance(widget, ReportItem):
            self.engine.delete_report(widget.report_data['filename'])
            self.populate_list()
        
        if "delete_tag" in event.button.classes and isinstance(widget, TagHeader):
            self.engine.delete_tag(widget.tag_name)
            self.populate_list()

class YalapmTUI(App):
    CSS = """
    Screen { background: $surface-darken-1; }
    #main_container { layout: grid; grid-size: 2; grid-gutter: 1; padding: 1; border: thick $primary-lighten-2; border-title-align: center; }
    APMDisplay { content-align: left middle; height: 3; background: $surface-lighten-1; padding: 0 1; }
    #session_time, #status { column-span: 2; content-align: center middle; background: $surface; padding: 0 1; }
    #controls_hint { column-span: 2; height: 3; content-align: center middle; background: $primary-darken-2; color: $text; }
    #graph { column-span: 2; height: 12; border: wide $surface-lighten-2; padding: 1; }
    #start_dialog { align: center middle; background: $surface; width: 50; height: 20; border: thick $primary; padding: 1; }
    #start_title { content-align: center middle; width: 100%; margin-bottom: 1; }
    #tag_input, #veapm_input { margin-bottom: 1; }
    #report_manager_dialog { align: center middle; background: $surface; width: 80%; height: 80%; border: thick $primary; padding: 1; }
    #report_manager_title { content-align: center middle; width: 100%; margin-bottom: 1; }
    #report_list { background: $surface-darken-1; }
    .tag_header_item { background: $primary-darken-2; }
    ReportItem, TagHeader { padding: 0 1; }
    #horizontal_tag {height: 5; background: $primary-darken-3; }
    #horizontal_item {height: 5; background: $primary-darken-3; }
    Horizontal { align: center middle; width: 100%; }
    .report_label, .tag_label { width: 1fr; }
    """
    BINDINGS = [
        ("s", "start_resume", "Start/Resume"), ("p", "pause", "Pause"), ("r", "reset", "Reset"),
        ("m", "manage", "Manage Reports"), ("f", "open_folder", "Folder"), ("v", "view_report", "Report"),
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
            yield APMDisplay("Average APM:", "📊", id="average_apm")
            yield APMDisplay("Average veAPM:", "🎮", id="average_veapm")
            yield APMDisplay("Total Actions:", "🎯", id="total_actions")
            yield Static("", id="session_time")
            yield Static("", id="status")
            yield Static("💡 [b]Press 's' to START Session[/b]", id="controls_hint")
            yield APMGraph(id="graph")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(1, self.update_display)
        self.query_one("#main_container").border_title = "YALAPM"
        self.query_one("#graph").border_title = "APM Trend (last 5 mins)"

    def update_display(self) -> None:
        stats = self.engine.get_stats()
        for key in ["current_apm", "peak_apm", "average_apm", "average_veapm", "total_actions"]:
            self.query_one(f"#{key}", APMDisplay).value = stats[key]
        self.query_one("#session_time").update(f"⏱️ Session Time:   [b]{stats['session_time']}[/b]")
        self.query_one("#status").update(f"   Status:         [b]{stats['status']}[/b]")
        self.query_one(APMGraph).history = stats["apm_history"]
        hint_widget = self.query_one("#controls_hint")
        if self.engine.state == "STOPPED": hint_widget.update("💡 [b]Press 's' to START Session[/b]")
        elif self.engine.state == "RUNNING": hint_widget.update("💡 [b]Press 'p' to PAUSE Session[/b]")
        elif self.engine.state == "PAUSED": hint_widget.update("💡 [b]Press 's' to RESUME Session[/b]")

    def action_start_resume(self) -> None:
        if self.engine.state == "STOPPED":
            def start_session_callback(data: tuple):
                tag, veapm = data
                self.engine.start(tag, veapm)
            self.push_screen(StartSessionScreen(), start_session_callback)
        elif self.engine.state == "PAUSED": self.engine.resume()

    def action_pause(self) -> None: self.engine.pause()

    def action_reset(self) -> None:
        def reset_session_callback(data: tuple):
            tag, veapm = data
            self.engine.reset_and_start(tag, veapm)
        self.push_screen(StartSessionScreen(), reset_session_callback)

    def action_manage(self) -> None: self.push_screen(ReportManagerScreen(self.engine))
    def action_open_folder(self) -> None: self.engine.open_report_folder()
    
    def action_view_report(self) -> None:
        report_path = self.engine.get_report_path()
        if report_path.exists(): webbrowser.open_new_tab(report_path.as_uri())
        else: self.notify("No report file exists yet. Stop a session first.", title="Info")

    def action_quit(self) -> None:
        report_path = self.engine.stop()
        if report_path: webbrowser.open_new_tab(report_path.as_uri())
        self.exit()

# --- Main Execution ---

def check_permissions():
    try:
        m_test = mouse.Listener(on_click=lambda *args: None)
        k_test = keyboard.Listener(on_press=lambda k: None)
        m_test.start(); k_test.start()
        time.sleep(0.1)
        m_test.stop(); k_test.stop()
        return True
    except Exception:
        return False


def main():
    """Entry point for yalapm CLI."""
    print("🔍 Checking system compatibility...")
    if not check_permissions():
        print("\n⚠️  Permission issue detected! Please run with sudo:\n   $ sudo yalapm\n")
        sys.exit(1)
    else:
        print("✅ Permissions look good!")

    engine = APMMonitorEngine()
    app = YalapmTUI(engine)
    app.run()


if __name__ == "__main__":
    main()