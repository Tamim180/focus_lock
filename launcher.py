import gi
import os
import subprocess
import threading
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, GLib

def pick_window():
    result = subprocess.run(
        ['qdbus', 'org.kde.KWin', '/KWin', 'org.kde.KWin.queryWindowInfo'],
        capture_output=True, text=True
    )
    info = {}
    for line in result.stdout.strip().split('\n'):
        if ':' in line:
            key, _, value = line.partition(':')
            info[key.strip()] = value.strip()
    return info

def block_shortcuts():
    subprocess.run([
        'qdbus', 'org.kde.kglobalaccel',
        '/kglobalaccel', 'blockGlobalShortcuts', 'true'
    ])

def write_config(window_class):
    with open('/tmp/focuslock.conf', 'w') as f:
        f.write(f'windowClass={window_class}\n')

def load_kwin_script(window_class):
    script = f"""
var lockedWindow = null;
var isLocked = false;

function lockWindow(win) {{
    lockedWindow = win;
    isLocked = true;
    win.fullScreen = true;
    win.keepAbove = true;
    win.noBorder = true;
}}

var enforceFocusTimer = new QTimer();
enforceFocusTimer.interval = 300;
enforceFocusTimer.timeout.connect(function() {{
    if (!isLocked) {{
        var clients = workspace.windowList();
        for (var i = 0; i < clients.length; i++) {{
            var win = clients[i];
            if (win.resourceClass &&
                win.resourceClass.toLowerCase().includes("{window_class.lower()}")) {{
                lockWindow(win);
                break;
            }}
        }}
    }} else {{
        if (lockedWindow && !lockedWindow.fullScreen) {{
            lockedWindow.fullScreen = true;
        }}
        if (lockedWindow && !lockedWindow.noBorder) {{
            lockedWindow.noBorder = true;
        }}
        if (lockedWindow && workspace.activeWindow !== lockedWindow) {{
            workspace.activeWindow = lockedWindow;
        }}
    }}
}});

enforceFocusTimer.start();
"""
    with open('/tmp/focuslock_script.js', 'w') as f:
        f.write(script)

    result = subprocess.run([
        'qdbus', 'org.kde.KWin', '/Scripting',
        'org.kde.kwin.Scripting.loadScript',
        '/tmp/focuslock_script.js',
        'focuslockrunning'
    ], capture_output=True, text=True)

    subprocess.run([
        'qdbus', 'org.kde.KWin', '/Scripting',
        'org.kde.kwin.Scripting.start'
    ])

    print(f"KWin script loaded with ID: {result.stdout.strip()}")

def cleanup_files():
    for f in ['/tmp/focuslock.conf',
              '/tmp/focuslock_script.js',
              '/tmp/focuslock_restore.js']:
        try:
            os.remove(f)
        except:
            pass

class WarningDialog(Gtk.Dialog):
    def __init__(self, parent, minutes, window_name):
        super().__init__(transient_for=parent, modal=True)
        self.set_title("⚠️ FocusLock Warning")
        self.set_default_size(420, 250)

        box = self.get_content_area()
        box.set_spacing(16)
        box.set_margin_top(24)
        box.set_margin_bottom(24)
        box.set_margin_start(24)
        box.set_margin_end(24)

        title = Gtk.Label(label="⚠️ Are you sure?")
        title.add_css_class("warning-title")

        msg = Gtk.Label()
        msg.set_markup(
            f"You are about to lock <b>{window_name}</b> for <b>{minutes} minutes</b>.\n\n"
            f"• All keyboard shortcuts will be <b>disabled</b>\n"
            f"• Alt+F4, Alt+Tab, Super key — all blocked\n"
            f"• Selected window will be locked fullscreen\n"
            f"• <b>Emergency exit: TTY (Ctrl+Alt+F2) → pkill -f timer.py</b>\n\n"
            f"There is no turning back until the timer ends!"
        )
        msg.set_wrap(True)
        msg.set_halign(Gtk.Align.START)

        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        btn_box.set_halign(Gtk.Align.END)

        cancel_btn = Gtk.Button(label="Cancel")
        cancel_btn.connect("clicked", lambda _: self.response(Gtk.ResponseType.CANCEL))

        confirm_btn = Gtk.Button(label="🚀 Lock me in!")
        confirm_btn.add_css_class("destructive-action")
        confirm_btn.connect("clicked", lambda _: self.response(Gtk.ResponseType.OK))

        btn_box.append(cancel_btn)
        btn_box.append(confirm_btn)

        box.append(title)
        box.append(msg)
        box.append(btn_box)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("""
            .warning-title {
                font-size: 22px;
                font-weight: bold;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.show()

class LauncherWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="🔒 FocusLock")
        self.set_default_size(420, 320)
        self.selected_window = {}
        cleanup_files()

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(24)
        main_box.set_margin_bottom(24)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)

        title = Gtk.Label(label="🔒 FocusLock")
        title.add_css_class("app-title")

        subtitle = Gtk.Label(label="Lock a window. Stay focused.")
        subtitle.set_opacity(0.6)

        timer_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        timer_label = Gtk.Label(label="Duration (minutes):")
        self.timer_entry = Gtk.Entry()
        self.timer_entry.set_placeholder_text("e.g. 25")
        self.timer_entry.set_max_length(3)
        self.timer_entry.set_hexpand(True)
        timer_box.append(timer_label)
        timer_box.append(self.timer_entry)

        self.pick_btn = Gtk.Button(label="🖱️ Click to Pick Window")
        self.pick_btn.connect("clicked", self.on_pick_window)

        self.selected_label = Gtk.Label(label="No window selected")
        self.selected_label.set_opacity(0.6)

        self.start_btn = Gtk.Button(label="🚀 Start Focus Session")
        self.start_btn.add_css_class("suggested-action")
        self.start_btn.connect("clicked", self.on_start)

        self.status_label = Gtk.Label(label="")
        self.status_label.set_opacity(0.7)

        main_box.append(title)
        main_box.append(subtitle)
        main_box.append(timer_box)
        main_box.append(self.pick_btn)
        main_box.append(self.selected_label)
        main_box.append(self.start_btn)
        main_box.append(self.status_label)
        self.set_child(main_box)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_string("""
            .app-title {
                font-size: 32px;
                font-weight: bold;
            }
        """)
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def on_pick_window(self, btn):
        self.status_label.set_label("Click on the window you want to lock...")
        threading.Thread(target=self.do_pick, daemon=True).start()

    def do_pick(self):
        info = pick_window()
        GLib.idle_add(self.on_window_picked, info)

    def on_window_picked(self, info):
        if not info or 'resourceClass' not in info:
            self.status_label.set_label("⚠️ Failed to pick window, try again!")
            return
        self.selected_window = info
        caption = info.get('caption', info.get('resourceClass', 'Unknown'))
        resource = info.get('resourceClass', '')
        self.selected_label.set_label(f"✅ Selected: {caption} ({resource})")
        self.selected_label.set_opacity(1.0)
        self.status_label.set_label("")

    def on_start(self, button):
        try:
            minutes = int(self.timer_entry.get_text().strip())
            if minutes <= 0:
                raise ValueError
        except ValueError:
            self.status_label.set_label("⚠️ Please enter a valid number of minutes!")
            return

        if not self.selected_window:
            self.status_label.set_label("⚠️ Please pick a window first!")
            return

        dialog = WarningDialog(
            self,
            minutes,
            self.selected_window.get('caption', 'selected window')
        )
        dialog.connect("response", self.on_warning_response, minutes)

    def on_warning_response(self, dialog, response, minutes):
        dialog.destroy()
        if response != Gtk.ResponseType.OK:
            return

        window_class = self.selected_window.get('resourceClass', '')
        seconds = minutes * 60

        write_config(window_class)
        load_kwin_script(window_class)
        block_shortcuts()

        script_dir = os.path.dirname(os.path.abspath(__file__))
        subprocess.Popen(
            ['python', os.path.join(script_dir, 'timer.py'), str(seconds)]
        )

        self.get_application().quit()

class LauncherApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id="com.focuslock.launcher")
        self.connect("activate", self.on_activate)

    def on_activate(self, app):
        win = LauncherWindow(app)
        win.present()

app = LauncherApp()
app.run()
