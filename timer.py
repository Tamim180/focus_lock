import sys
import time
import subprocess
import os

def restore_window(window_class):
    script = f"""
var clients = workspace.windowList();
for (var i = 0; i < clients.length; i++) {{
    var win = clients[i];
    if (win.resourceClass &&
        win.resourceClass.toLowerCase().includes("{window_class.lower()}")) {{
        win.fullScreen = false;
        win.keepAbove = false;
        win.noBorder = false;
        break;
    }}
}}
"""
    with open('/tmp/focuslock_restore.js', 'w') as f:
        f.write(script)

    subprocess.run([
        'qdbus', 'org.kde.KWin', '/Scripting',
        'org.kde.kwin.Scripting.loadScript',
        '/tmp/focuslock_restore.js',
        'focuslockRestore'
    ])
    subprocess.run([
        'qdbus', 'org.kde.KWin', '/Scripting',
        'org.kde.kwin.Scripting.start'
    ])
    time.sleep(1)

    # Force KWin to redraw window decorations
    subprocess.run([
        'qdbus', 'org.kde.KWin', '/KWin',
        'org.kde.KWin.reconfigure'
    ])

    subprocess.run([
        'qdbus', 'org.kde.KWin', '/Scripting',
        'org.kde.kwin.Scripting.unloadScript',
        'focuslockRestore'
    ])

def restore_shortcuts():
    subprocess.run([
        'qdbus', 'org.kde.kglobalaccel',
        '/kglobalaccel', 'blockGlobalShortcuts', 'false'
    ])

def unload_kwin_script():
    subprocess.run([
        'qdbus', 'org.kde.KWin', '/Scripting',
        'org.kde.kwin.Scripting.unloadScript',
        'focuslockrunning'
    ])

def cleanup_files():
    for f in ['/tmp/focuslock.conf',
              '/tmp/focuslock_script.js',
              '/tmp/focuslock_restore.js']:
        try:
            os.remove(f)
        except:
            pass

if __name__ == '__main__':
    seconds = int(sys.argv[1])

    window_class = ''
    try:
        with open('/tmp/focuslock.conf', 'r') as f:
            for line in f:
                if line.startswith('windowClass='):
                    window_class = line.split('=')[1].strip()
    except:
        pass

    time.sleep(seconds)
    unload_kwin_script()
    # Small delay so enforcer stops before we restore
    time.sleep(0.5)
    restore_window(window_class)
    restore_shortcuts()
    cleanup_files()
