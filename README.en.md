# Widget Studio

[🇹🇷 Türkçe](README.md) | 🇬🇧 English

A Rainmeter-style multi-widget system that lets you place widgets freely on your desktop. Written with PyQt6.

## Features

### Widget types
- **Clock**: Large, transparent clock. Each digit can be configured separately.
- **Analog clock**: Optional seconds and number display.
- **App bar**: 9-slot (3x3) launcher. Each new bar adds 9 slots. Click a slot to launch a program, or drag and drop a file or app onto it.
- **Calendar**, **Date card**, **Countdown**
- **System monitor** (CPU / RAM / Disk)
- **Network speed** (graph)
- **Battery status**
- **Notes**, **To-do list**
- **Timer** (Pomodoro), **Stopwatch**
- **Media player**: Previous / play / next, volume control, album art, progress bar
- **Audio visualizer**
- **Quick search**
- **Clipboard history** (kept in memory only)
- **Recycle bin**
- **Snipping tool**: Select an area on screen to capture
- **System buttons**: Lock, sleep, log off, restart, shut down (with confirmation)
- **Wallpaper effects**: Snow, rain, stars, fireflies, matrix, sakura, aurora; plus color filter, vignette, and day/night cycle

### General features
- **Shared theme**: All widgets share the same color, glass effect, corner, and border settings. Preset themes are available and apply instantly.
- **Snapping**: Widgets snap to each other and to screen edges.
- **Opacity**: Adjustable from 10% to 100%. Includes a "fade on hover" option.
- **Tray menu**: Add widgets, show/hide all, settings, and exit.
- **Auto-reload**: If you edit the config file by hand, widgets update themselves.

## Requirements

- Python 3.9 or newer
- PyQt6

Optional packages for the full experience:

```bash
pip install winsdk                 # Album art and full track info in the media player (Windows)
pip install numpy pyaudiowpatch    # Audio visualizer (Windows)
```

Without `winsdk`, the media player reads the Spotify and YouTube titles from window names.

## Installation

```bash
git clone https://github.com/USERNAME/widget-studio.git
cd widget-studio
pip install PyQt6
```

## Usage

```bash
python WidgetStudio.py
```

If you don't want a console window, rename the file to `.pyw`.

### Basic actions
- **Adding a widget**: Right-click the tray icon (or a widget) → **Add widget** → choose a type.
- **Moving**: Drag the widget. It snaps to screen edges.
- **Settings**: Right-click a widget → **Settings…** (Double-clicking the clock also opens settings.)
- **Adding programs to the app bar**: Click an empty (+) slot. Programs from the Start menu and Store apps are listed. If you select several, they fill empty slots in order.
- **Changing or clearing a slot**: Right-click the slot → **Change** or **Clear**.
- **Wallpaper effects**: Tray → **Widgets** → **Wallpaper effect** → **Settings**.

## Configuration file

All settings are stored in `~/.widget_studio.json` in your user folder. If you edit this file by hand, changes are applied within a few seconds.

## Platform support

The app is designed for Windows. Start menu scanning, launch at Windows startup, and media and audio features depend on Windows. Some features may not work on other platforms.

## License

This project is distributed under the [MIT](LICENSE) license.
