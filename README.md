# 🔒 FocusLock

Lock any window fullscreen and block all keyboard shortcuts for a set amount of time. Built for students and anyone who struggles to stay focused.

> **Inspired by Android focus apps — but for Linux.**

---

## ✨ Features

- 🖱️ Pick any open window with a crosshair picker
- ⏱️ Set a custom duration in minutes (supports decimals like 0.5)
- 🔒 Locks the window fullscreen with no titlebar
- ⌨️ Disables ALL keyboard shortcuts (Alt+F4, Alt+Tab, Super key)
- 🔓 Automatically restores everything when timer ends
- ⚠️ Warning dialog before locking so you know what you're getting into

---

## 📦 Installation

### From AUR (recommended)
```bash
yay -S focuslock
```
or
```bash
paru -S focuslock
```

### Manual
```bash
git clone https://github.com/Tamim180/focus_lock.git
cd focus_lock
makepkg -si
```

---

## 🚀 Usage

Launch from your app menu or run:
```bash
focuslock
```

1. Enter duration in minutes
2. Click **"Click to Pick Window"** — your cursor becomes a crosshair
3. Click the window you want to lock
4. Hit **"Start Focus Session"**
5. Confirm the warning dialog
6. You're locked in until the timer ends!

---

## 🆘 Emergency Exit

If you need to escape before the timer ends:

1. Switch to TTY: `Ctrl+Alt+F2`
2. Login and run: `pkill focuslock`
3. Switch back to desktop: `Ctrl+Alt+F1`

This will immediately restore all shortcuts and window decorations.

---

## ⚠️ Requirements

| Requirement | Notes |
|-------------|-------|
| Arch Linux | AUR package |
| KDE Plasma | Required — uses KWin scripting |
| Wayland | X11 not tested |
| Python 3 | Core language |
| python-gobject | GTK4 bindings |
| gtk4 | UI toolkit |
| qt5-tools | For qdbus |
| kwin | Window manager |

> ⚠️ **This app currently only works on KDE Plasma.** Support for other window managers (Hyprland, GNOME, Sway) is planned for future releases.

---

## 🗺️ Roadmap

- [x] KDE Plasma + Wayland support
- [x] Crosshair window picker
- [x] Fractional minutes (e.g. 0.5)
- [x] Emergency restore via SIGTERM
- [ ] Timer overlay window
- [ ] Hyprland support
- [ ] GNOME support
- [ ] Sway/i3 support
- [ ] System tray indicator

---

## 🐛 Known Limitations

- **Flatpak apps** running under XWayland may not lose their titlebar correctly
- **Only works on KDE Plasma** — other DEs/WMs not supported yet
- Emergency exit requires TTY access

---

## 👨‍💻 Author

**Tamim Bhuyan** (Omni_king on AUR)

Built in one day with a lot of determination and help from Claude 😄

---

## 📄 License

MIT
