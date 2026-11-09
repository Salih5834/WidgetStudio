"""
Widget Studio  –  Rainmeter tarzı çoklu widget sistemi (PyQt6)
================================================================
Kurulum :  pip install PyQt6
Çalıştır:  python widget_studio.py          (konsolsuz: dosyayı .pyw yap)

WIDGET TÜRLERİ
  • Saat              : büyük, şeffaf, her rakamı ayrı ayarlanabilir saat
  • Uygulama çubuğu   : 9 slotlu (3x3) başlatıcı. Her yeni çubuk +9 slot demektir
                        (2 çubuk = 18 slot, 3 çubuk = 27 ...). İstediğin kadar ekle,
                        her biri masaüstünde serbestçe konumlanır.

v3 YENİLİKLER (Rainmeter uyumu)
  • Ortak tema: tüm widget'lar aynı renk / cam / köşe / kenarlık ayarını paylaşır
    (tepsi → "Ortak tema…"). Hazır temalar var, canlı uygulanır.
  • Widget'lar birbirine yapışır (yan yana / alt alta / hizalı) – boşluk temadan gelir.
  • Saat artık cam panelli + kenarlıklı (uygulama çubuğuyla aynı görünüm).
  • Rainmeter sağ-tık menüsü: Şeffaflık %10…%100, "Üstüne gelince soluklaştır".
  • Tepsi: "Tümünü gizle / göster".
  • 5 yeni widget: Takvim, Sistem monitörü, Not defteri, Analog saat, Zamanlayıcı (Pomodoro).
    Hepsi ortak temayı, yapışmayı ve boyut (%) ayarını kullanır.
  • 5 widget daha: Pil durumu, Hızlı arama, Kronometre, Geri sayım, Tarih kartı.
  • Medya oynatıcı: önceki/oynat/sonraki, ses +/-, kapak, ilerleme. Tekerlek = ses.
    Her oynatıcıyı kontrol eder. Kapak + tam bilgi için (isteğe bağlı): pip install winsdk
    Kurulu değilse Spotify ve YouTube başlığını pencere adından okur.
  • Yapılacaklar, Ağ hızı (grafik), Çöp kutusu, Pano geçmişi (yalnızca bellekte),
    Ses görselleştirici (pip install numpy pyaudiowpatch), Sistem düğmeleri (onaylı).
  • Duvar kağıdı efektleri: kar, yağmur, yıldız, ateşböceği, matrix, sakura, kutup ışığı +
    renk filtresi, vinyet, gün döngüsü. Ayarlar: tepsi → Widget'lar → Duvar kağıdı efekti → Ayarlar.
  • Kırpma aracı: sürükleyerek alan seç; el titremesi kenarlara/orana/ekran kenarına yapışarak düzeltilir.

NASIL KULLANILIR
  • Tepsi simgesi (veya widget'a sağ tık) → "Widget ekle" → tür seç
  • Uygulama çubuğunda boş slota (+) tıkla → Başlat menüsündeki programlar
    (shell:Programs / shell:Common Programs + Store uygulamaları) listelenir.
    Birden fazla seçersen boş slotlara sırayla yerleşir.
  • Dosya/uygulamayı slotun üstüne sürükleyip bırakabilirsin.
  • Slota sağ tık: Değiştir / Temizle.   Slota tık: uygulamayı başlatır.
  • Widget'ı sürükleyerek taşı (ekran kenarına yapışır). Çift tık = ayarlar (saat).
  • Her widget'ın ayarı: sağ tık → Ayarlar…
  • Her şey ~/.widget_studio.json dosyasına kaydedilir; dosyayı elle
    düzenlersen widget'lar otomatik yenilenir.
"""

import json
import os
import subprocess
import sys
import calendar
import math
import random
import shutil
import threading
import time
import uuid
import webbrowser
import zlib
from urllib.parse import quote
from datetime import date, datetime, timedelta

from PyQt6.QtCore import (QEventLoop, QFileInfo, QPoint, QPointF, QRect, QRectF, QSize, Qt,
                          QThread, QTimer, pyqtSignal)
from PyQt6.QtGui import (QBrush, QColor, QCursor, QFont, QFontMetrics, QIcon, QImage, QLinearGradient, QPainter,
                         QPainterPath, QPen, QPixmap, QPolygonF, QRadialGradient, QTransform)
from PyQt6.QtWidgets import (QAbstractItemView, QApplication, QCheckBox,
                             QColorDialog, QComboBox, QDialog, QFileDialog,
                             QFileIconProvider, QFontComboBox, QFormLayout,
                             QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget,
                             QListWidgetItem, QMenu, QMessageBox, QPlainTextEdit, QPushButton, QSlider,
                             QSpinBox, QSystemTrayIcon, QTabWidget,
                             QVBoxLayout, QWidget)

IS_WIN = sys.platform.startswith("win")
IS_MAC = sys.platform == "darwin"
HOME = os.path.expanduser("~")
STORE_PATH = os.path.join(HOME, ".widget_studio.json")
OLD_CLOCK_PATH = os.path.join(HOME, ".buyuk_saat_widget.json")
APP_NAME = "WidgetStudio"

ALIGN_CENTER = Qt.AlignmentFlag.AlignCenter.value
ALIGN_L = (Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter).value
ALIGN_R = (Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter).value

SEGMENTS = {
    "0": "abcdef", "1": "bc", "2": "abdeg", "3": "abcdg", "4": "bcfg",
    "5": "acdfg", "6": "acdefg", "7": "abc", "8": "abcdefg", "9": "abcdfg",
}
ITEM_NAMES = ["Saat - onlar", "Saat - birler", "İki nokta",
              "Dakika - onlar", "Dakika - birler"]
COLON_IDX = 2
ZPOS = [("desktop", "Masaüstünde"), ("normal", "Normal"), ("top", "Her zaman üstte")]
TYPE_LABELS = {"clock": "Saat", "appbar": "Uygulama çubuğu (+9 slot)",
               "calendar": "Takvim", "sysmon": "Sistem monitörü (CPU/RAM/Disk)",
               "notes": "Not defteri", "analog": "Analog saat",
               "timer": "Zamanlayıcı (Pomodoro)", "battery": "Pil durumu",
               "search": "Hızlı arama", "stopwatch": "Kronometre",
               "countdown": "Geri sayım", "datecard": "Tarih kartı",
               "media": "Medya oynatıcı", "todo": "Yapılacaklar", "netspeed": "Ağ hızı (grafik)",
               "recycle": "Çöp kutusu", "clipboard": "Pano geçmişi",
               "snip": "Kırpma aracı (düzeltmeli)", "wallfx": "Duvar kağıdı efekti (kar, yağmur, matrix…)", "audioviz": "Ses görselleştirici", "power": "Sistem düğmeleri (kapat/yeniden başlat)"}
MAX_SLOTS = 36


# ======================================================================
# Ayar şemaları
# ======================================================================
def new_id():
    return uuid.uuid4().hex[:8]


def common_defaults():
    return {"x": 120, "y": 120, "zpos": "desktop", "locked": False,
            "click_through": False, "snap": True, "global_opacity": 100,
            "hide_hover": False, "border_alpha": 30}


def default_clock():
    digit = {"w": 62, "h": 230, "t": 15, "color": "#FFFFFF", "alpha": 90}
    colon = {"w": 30, "h": 230, "t": 16, "color": "#FFFFFF", "alpha": 90}
    d = {"id": new_id(), "type": "clock"}
    d.update(common_defaults())
    d.update({"gap": 20, "pad": 24, "use_24h": True, "blink": True,
              "shadow": True, "mode": "segment", "font": "Arial",
              "panel_color": "#000000", "panel_alpha": 22, "radius": 16,
              "items": [dict(digit), dict(digit), dict(colon), dict(digit), dict(digit)]})
    return d


def default_appbar():
    d = {"id": new_id(), "type": "appbar"}
    d.update(common_defaults())
    d.update({"n_slots": 9, "slots": [None] * 9, "cols": 3, "tile": 88, "icon": 44,
              "gap": 10, "pad": 14, "radius": 18,
              "tile_color": "#FFFFFF", "tile_alpha": 16, "hover_alpha": 36,
              "panel_color": "#000000", "panel_alpha": 28,
              "show_labels": True, "label_color": "#FFFFFF", "label_size": 9})
    return d


def panel_defaults(typ, **extra):
    d = {"id": new_id(), "type": typ}
    d.update(common_defaults())
    d.update({"scale": 100, "accent": "#6C63E8", "text": "#FFFFFF",
              "panel_color": "#000000", "panel_alpha": 24, "radius": 18})
    d.update(extra)
    return d


def fx_defaults():
    d = {"id": new_id(), "type": "wallfx"}
    d.update(common_defaults())
    d.update({"click_through": True, "zpos": "desktop", "effect": "snow", "color": "#FFFFFF",
              "amount": 140, "speed": 100, "fps": 30, "tint_color": "#0B1A3A", "tint_alpha": 0,
              "vignette": 0, "auto_tone": False, "mouse_react": True, "monitor": 0})
    return d


DEFAULTS = {
    "clock": default_clock, "appbar": default_appbar,
    "calendar": lambda: panel_defaults("calendar", monday_first=True),
    "sysmon": lambda: panel_defaults("sysmon", show_cpu=True, show_ram=True, show_disk=True),
    "notes": lambda: panel_defaults("notes", text="Not yazmak için çift tıkla…", font_px=18),
    "analog": lambda: panel_defaults("analog", show_seconds=True, show_numbers=True),
    "timer": lambda: panel_defaults("timer", focus_min=25, break_min=5, auto_next=False),
    "battery": lambda: panel_defaults("battery"),
    "search": lambda: panel_defaults("search", engine=0),
    "stopwatch": lambda: panel_defaults("stopwatch"),
    "countdown": lambda: panel_defaults("countdown", label="Yeni Yıl",
                                        year=date.today().year + 1, month=1, day=1),
    "datecard": lambda: panel_defaults("datecard", show_year=True),
    "media": lambda: panel_defaults("media", show_art=True, show_progress=True, scale=100),
    "todo": lambda: panel_defaults("todo", tasks=[{"t": "İlk görevini ekle", "d": False}],
                                   max_rows=8, hide_done=False),
    "netspeed": lambda: panel_defaults("netspeed", history=60, show_graph=True),
    "recycle": lambda: panel_defaults("recycle", confirm=True),
    "clipboard": lambda: panel_defaults("clipboard", rows=6),
    "audioviz": lambda: panel_defaults("audioviz", bars=32, mirror=False),
    "wallfx": lambda: fx_defaults(),
    "snip": lambda: panel_defaults("snip", snap_px=12, snap_ratio=True, snap_screen=True,
                                   copy_clip=True, save_file=True,
                                   show_labels=False, show_status=False),
    "power": lambda: panel_defaults("power", show_lock=True, show_sleep=True, show_logoff=True,
                                    show_restart=True, show_shutdown=True, confirm=True),
}

DEFAULT_THEME = {"accent": "#6C63E8", "text": "#FFFFFF", "glass": "#000000",
                 "glass_alpha": 24, "border_alpha": 30, "radius": 18, "gap": 10}
PRESETS = {
    "Mor cam": {"accent": "#6C63E8", "text": "#FFFFFF", "glass": "#000000",
                "glass_alpha": 24, "border_alpha": 30, "radius": 18},
    "Buz": {"accent": "#FFFFFF", "text": "#FFFFFF", "glass": "#FFFFFF",
            "glass_alpha": 16, "border_alpha": 45, "radius": 20},
    "Gece": {"accent": "#00E5FF", "text": "#DDF8FF", "glass": "#05070F",
             "glass_alpha": 55, "border_alpha": 22, "radius": 14},
    "Kehribar": {"accent": "#FFB347", "text": "#FFF1DD", "glass": "#1A1208",
                 "glass_alpha": 45, "border_alpha": 28, "radius": 16},
}


def load_theme():
    th = dict(DEFAULT_THEME)
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            th.update({k: v for k, v in json.load(f).get("theme", {}).items() if k in th})
    except (OSError, ValueError, AttributeError):
        pass
    return th


def style_cfg(cfg, th):
    """Ortak temayı bir widget ayarına uygular."""
    if cfg["type"] == "wallfx":
        return
    cfg["panel_color"] = th["glass"]
    cfg["panel_alpha"] = int(th["glass_alpha"])
    cfg["border_alpha"] = int(th["border_alpha"])
    if cfg["type"] == "clock":
        cfg["radius"] = int(th["radius"])
        for it in cfg["items"]:
            it["color"] = th["accent"]
    elif cfg["type"] == "appbar":
        cfg["label_color"] = th["text"]
        cfg["tile_color"] = th["text"]
        cfg["radius"] = max(4, int(th["radius"] - cfg["pad"] / 2))
    else:
        cfg["accent"] = th["accent"]
        cfg["text"] = th["text"]
        cfg["radius"] = int(th["radius"])


def clean_slot(s):
    if isinstance(s, dict) and s.get("path"):
        out = {"name": str(s.get("name") or os.path.splitext(os.path.basename(s["path"]))[0]),
               "path": str(s["path"]), "kind": s.get("kind", "file")}
        if s.get("icon"):
            out["icon"] = str(s["icon"])
        return out
    return None


def normalize(raw):
    if not isinstance(raw, dict) or raw.get("type") not in DEFAULTS:
        return None
    typ = raw["type"]
    cfg = DEFAULTS[typ]()
    for k, v in raw.items():
        if k == "items" and typ == "clock":
            if isinstance(v, list) and len(v) == 5:
                for i, it in enumerate(v):
                    if isinstance(it, dict):
                        cfg["items"][i].update(it)
        elif k == "slots":
            continue
        elif k in cfg:
            cfg[k] = v
    if typ == "appbar":
        try:
            n = max(1, min(MAX_SLOTS, int(cfg["n_slots"])))
        except (TypeError, ValueError):
            n = 9
        cfg["n_slots"] = n
        slots = raw.get("slots") if isinstance(raw.get("slots"), list) else []
        slots = [clean_slot(s) for s in slots[:n]]
        slots += [None] * (n - len(slots))
        cfg["slots"] = slots
    return cfg


def load_store():
    """[(cfg), ...]  döndürür. Dosya yoksa eski saat ayarından geçiş yapar."""
    try:
        with open(STORE_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        widgets = [normalize(r) for r in data.get("widgets", [])]
        return [w for w in widgets if w]
    except (OSError, ValueError, AttributeError):
        pass
    try:  # eski tek-saat ayarı
        with open(OLD_CLOCK_PATH, "r", encoding="utf-8") as f:
            old = json.load(f)
        if "opacity" in old and "global_opacity" not in old:
            old["global_opacity"] = int(float(old["opacity"]) * 100)
        if "pin_desktop" in old and "zpos" not in old:
            old["zpos"] = "desktop" if old["pin_desktop"] else "normal"
        old.pop("id", None)
        old["type"] = "clock"
        c = normalize(old)
        return [c] if c else []
    except (OSError, ValueError, TypeError):
        return []


# ======================================================================
# Platform yardımcıları
# ======================================================================
class WinDesktopPinner:
    """Pencereyi masaüstü simgelerinin hemen üstüne, diğer pencerelerin altına koyar."""

    def __init__(self):
        import ctypes
        from ctypes import wintypes
        u = ctypes.windll.user32
        self.u = u
        u.FindWindowExW.argtypes = [wintypes.HWND, wintypes.HWND,
                                    wintypes.LPCWSTR, wintypes.LPCWSTR]
        u.FindWindowExW.restype = wintypes.HWND
        u.SetWindowPos.argtypes = [wintypes.HWND, wintypes.HWND, ctypes.c_int,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   wintypes.UINT]
        u.IsWindow.argtypes = [wintypes.HWND]
        self.proc_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        self.host = None

    def _find_host(self):
        if self.host and self.u.IsWindow(self.host):
            return self.host
        found = []

        def cb(hwnd, _):
            if self.u.FindWindowExW(hwnd, None, "SHELLDLL_DefView", None):
                found.append(hwnd)
                return False
            return True

        self.u.EnumWindows(self.proc_t(cb), 0)
        self.host = found[0] if found else None
        return self.host

    def pin(self, hwnd):
        host = self._find_host()
        if host and hwnd:
            self.u.SetWindowPos(hwnd, host, 0, 0, 0, 0, 0x0001 | 0x0002 | 0x0010)


def autostart_enabled():
    if not IS_WIN:
        return False
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r"Software\Microsoft\Windows\CurrentVersion\Run") as k:
            winreg.QueryValueEx(k, APP_NAME)
            return True
    except OSError:
        return False


def set_autostart(on):
    if not IS_WIN:
        return
    import winreg
    exe = sys.executable
    pyw = os.path.join(os.path.dirname(exe), "pythonw.exe")
    if os.path.exists(pyw):
        exe = pyw
    cmd = f'"{exe}" "{os.path.abspath(__file__)}"'
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0, winreg.KEY_SET_VALUE) as k:
        if on:
            winreg.SetValueEx(k, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(k, APP_NAME)
            except OSError:
                pass


# ======================================================================
# Program tarama (Başlat menüsü / shell:Programs)
# ======================================================================
def scan_windows():
    apps, seen = [], set()
    roots = [os.path.join(os.environ.get("ProgramData", ""),
                          r"Microsoft\Windows\Start Menu\Programs"),   # shell:Common Programs
             os.path.join(os.environ.get("APPDATA", ""),
                          r"Microsoft\Windows\Start Menu\Programs")]   # shell:Programs
    for root in roots:
        if not root or not os.path.isdir(root):
            continue
        for dirpath, _dirs, files in os.walk(root):
            for fn in files:
                if not fn.lower().endswith(".lnk"):
                    continue
                name = fn[:-4]
                if name.lower().startswith("uninstall") or name.lower() in seen:
                    continue
                seen.add(name.lower())
                apps.append({"name": name, "path": os.path.join(dirpath, fn), "kind": "file"})
    # Microsoft Store (UWP) uygulamaları
    try:
        cmd = ("[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; "
               "Get-StartApps | ConvertTo-Json -Compress")
        r = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", cmd],
                           capture_output=True, text=True, encoding="utf-8",
                           errors="replace", timeout=25, creationflags=0x08000000)
        data = json.loads(r.stdout) if r.stdout.strip() else []
        if isinstance(data, dict):
            data = [data]
        for it in data:
            name, appid = it.get("Name"), it.get("AppID", "")
            if name and "!" in appid and name.lower() not in seen:
                seen.add(name.lower())
                apps.append({"name": name, "path": appid, "kind": "uwp"})
    except Exception:
        pass
    return apps


def scan_mac():
    apps = []
    for root in ("/Applications", "/Applications/Utilities", "/System/Applications",
                 os.path.join(HOME, "Applications")):
        if os.path.isdir(root):
            for fn in os.listdir(root):
                if fn.endswith(".app"):
                    apps.append({"name": fn[:-4], "path": os.path.join(root, fn), "kind": "file"})
    return apps


def scan_linux():
    apps, seen = [], set()
    roots = ["/usr/share/applications", os.path.join(HOME, ".local/share/applications"),
             "/var/lib/flatpak/exports/share/applications",
             os.path.join(HOME, ".local/share/flatpak/exports/share/applications"),
             "/var/lib/snapd/desktop/applications"]
    for root in roots:
        if not os.path.isdir(root):
            continue
        for fn in os.listdir(root):
            if not fn.endswith(".desktop"):
                continue
            path = os.path.join(root, fn)
            name = icon = None
            hidden = False
            in_entry = False
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    for line in f:
                        line = line.strip()
                        if line.startswith("["):
                            in_entry = line == "[Desktop Entry]"
                        elif in_entry and line.startswith("Name=") and name is None:
                            name = line[5:]
                        elif in_entry and line.startswith("Icon="):
                            icon = line[5:]
                        elif in_entry and line in ("NoDisplay=true", "Hidden=true"):
                            hidden = True
            except OSError:
                continue
            if hidden or not name or name.lower() in seen:
                continue
            seen.add(name.lower())
            d = {"name": name, "path": path, "kind": "file"}
            if icon:
                d["icon"] = icon
            apps.append(d)
    return apps


def scan_apps():
    apps = scan_windows() if IS_WIN else scan_mac() if IS_MAC else scan_linux()
    apps.sort(key=lambda a: a["name"].casefold())
    return apps


class ScanThread(QThread):
    done = pyqtSignal(list)

    def run(self):
        try:
            apps = scan_apps()
        except Exception:
            apps = []
        self.done.emit(apps)


APP_CACHE = None
_KEEP_THREADS = []
MANAGER = None
_PICKERS = []


def _store_cache(apps):
    global APP_CACHE
    APP_CACHE = apps


def launch(slot):
    kind, path = slot.get("kind", "file"), slot["path"]
    if kind == "uwp":
        subprocess.Popen(["explorer.exe", f"shell:AppsFolder\\{path}"])
    elif IS_WIN:
        os.startfile(path)  # noqa: S606
    elif IS_MAC:
        subprocess.Popen(["open", path])
    elif path.endswith(".desktop"):
        try:
            subprocess.Popen(["gio", "launch", path])
        except FileNotFoundError:
            subprocess.Popen(["xdg-open", path])
    else:
        subprocess.Popen(["xdg-open", path])


# ======================================================================
# İkonlar
# ======================================================================
_provider = None
ICON_CACHE = {}


def letter_icon(name):
    pm = QPixmap(128, 128)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    hue = zlib.crc32(name.encode("utf-8")) % 360
    p.setBrush(QColor.fromHsv(hue, 150, 210))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(6, 6, 116, 116), 28, 28)
    f = QFont()
    f.setPixelSize(70)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#FFFFFF"))
    p.drawText(QRectF(0, 0, 128, 128), ALIGN_CENTER, (name[:1] or "?").upper())
    p.end()
    return QIcon(pm)


def icon_for_slot(slot):
    global _provider
    kind, path = slot.get("kind", "file"), slot.get("path", "")
    key = (kind, path)
    if key in ICON_CACHE:
        return ICON_CACHE[key]
    icon = QIcon()
    if kind == "file":
        theme = slot.get("icon")
        if theme:
            icon = QIcon.fromTheme(theme)
        if icon.isNull() and os.path.exists(path):
            if _provider is None:
                _provider = QFileIconProvider()
            fi = QFileInfo(path)
            if path.lower().endswith(".lnk"):
                tgt = fi.symLinkTarget()
                if tgt and os.path.exists(tgt):
                    fi = QFileInfo(tgt)
            icon = _provider.icon(fi)
    if icon.isNull():
        icon = letter_icon(slot.get("name", "?"))
    ICON_CACHE[key] = icon
    return icon


def make_tray_icon():
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setBrush(QColor(30, 30, 30))
    p.setPen(Qt.PenStyle.NoPen)
    p.drawRoundedRect(QRectF(2, 2, 60, 60), 14, 14)
    p.setBrush(QColor(255, 255, 255))
    for x in (12, 24, 38, 50):
        p.drawRoundedRect(QRectF(x - 4, 14, 8, 36), 3, 3)
    p.end()
    return QIcon(pm)



# ======================================================================
# Renk seçici + damlalık (ekrandan / duvar kağıdından renk al)
# ======================================================================
def pipette_icon():
    pm = QPixmap(64, 64)
    pm.fill(Qt.GlobalColor.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.translate(32, 32)
    p.rotate(45)
    p.setPen(QPen(QColor("#2b2b2b"), 3))
    p.setBrush(QColor("#ffffff"))
    p.drawRoundedRect(QRectF(-7, -26, 14, 34), 4, 4)      # gövde
    p.setBrush(QColor("#6C63E8"))
    p.drawRoundedRect(QRectF(-12, -30, 24, 10), 4, 4)     # baş
    p.setBrush(QColor("#2b2b2b"))
    p.drawPolygon(QPolygonF([QPointF(-5, 8), QPointF(5, 8), QPointF(0, 24)]))  # uç
    p.end()
    return QIcon(pm)


class ScreenPickerOverlay(QWidget):
    """Ekranın dondurulmuş görüntüsü üzerinde büyüteçle renk seçtirir."""

    def __init__(self, screen, pixmap, done):
        super().__init__()
        self.done = done
        self.pm = pixmap
        self.img = pixmap.toImage()
        self.cur = None
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
                            | Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)

    def color_at(self, pt):
        r = self.img.width() / max(1, self.width())
        x = max(0, min(self.img.width() - 1, int(pt.x() * r)))
        y = max(0, min(self.img.height() - 1, int(pt.y() * r)))
        return self.img.pixelColor(x, y)

    def mouseMoveEvent(self, e):
        self.cur = e.position().toPoint()
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.done(self.color_at(e.position().toPoint()))
        else:
            self.done(None)

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.done(None)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.drawPixmap(self.rect(), self.pm)
        if self.cur is None:
            return
        n, z = 11, 11
        size = n * z
        lx, ly = self.cur.x() + 26, self.cur.y() + 26
        if lx + size + 8 > self.width():
            lx = self.cur.x() - 26 - size
        if ly + size + 40 > self.height():
            ly = self.cur.y() - 26 - size - 34
        r = self.img.width() / max(1, self.width())
        cx, cy = int(self.cur.x() * r), int(self.cur.y() * r)
        clip = QPainterPath()
        clip.addEllipse(QRectF(lx, ly, size, size))
        p.save()
        p.setClipPath(clip)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        for dy in range(n):
            for dx in range(n):
                px = max(0, min(self.img.width() - 1, cx + dx - n // 2))
                py = max(0, min(self.img.height() - 1, cy + dy - n // 2))
                p.fillRect(lx + dx * z, ly + dy * z, z, z, self.img.pixelColor(px, py))
        p.restore()
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(QColor(0, 0, 0), 3))
        p.drawEllipse(QRectF(lx, ly, size, size))
        p.setPen(QPen(QColor(255, 255, 255), 1.5))
        p.drawEllipse(QRectF(lx, ly, size, size))
        c0 = lx + (n // 2) * z
        p.setPen(QPen(QColor(0, 0, 0), 2))
        p.drawRect(QRectF(c0, ly + (n // 2) * z, z, z))
        p.setPen(QPen(QColor(255, 255, 255), 1))
        p.drawRect(QRectF(c0 + 1, ly + (n // 2) * z + 1, z - 2, z - 2))
        col = self.color_at(self.cur)
        box = QRectF(lx, ly + size + 6, size, 24)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 20, 20, 220))
        p.drawRoundedRect(box, 8, 8)
        p.setBrush(col)
        p.drawEllipse(QRectF(box.x() + 7, box.y() + 5, 14, 14))
        p.setPen(QColor("#FFFFFF"))
        f = QFont()
        f.setPixelSize(13)
        p.setFont(f)
        p.drawText(QRectF(box.x() + 26, box.y(), box.width() - 30, box.height()),
                   int(Qt.AlignmentFlag.AlignVCenter.value), col.name().upper())


def pick_screen_color(callback):
    """Widget ve pencereleri gizler, ekranı yakalar, seçtirir; callback(QColor|None)."""
    hidden, faded = [], []
    if MANAGER:
        for w in MANAGER.widgets:
            if w.isVisible():
                hidden.append(w)
                w.hide()
    for t in QApplication.topLevelWidgets():
        if isinstance(t, QDialog) and t.isVisible():
            faded.append((t, t.windowOpacity()))
            t.setWindowOpacity(0.0)

    def grab():
        overlays = []
        state = {"done": False}

        def finish(col):
            if state["done"]:
                return
            state["done"] = True
            for o in overlays:
                o.hide()
                o.deleteLater()
                if o in _PICKERS:
                    _PICKERS.remove(o)
            for w in hidden:
                w.show()
                w.pin_tick()
            for t, op in faded:
                t.setWindowOpacity(op)
            callback(col)

        for sc in QApplication.screens():
            ov = ScreenPickerOverlay(sc, sc.grabWindow(0), finish)
            overlays.append(ov)
            _PICKERS.append(ov)
            ov.show()
        if overlays:
            overlays[0].activateWindow()
            overlays[0].setFocus()
        else:
            finish(None)

    QTimer.singleShot(300, grab)


def choose_color(parent, initial, title="Renk seç"):
    """QColorDialog + damlalık düğmesi. Seçilmezse geçersiz QColor döner."""
    dlg = QColorDialog(QColor(initial), parent)
    dlg.setWindowTitle(title)
    dlg.setOption(QColorDialog.ColorDialogOption.DontUseNativeDialog, True)
    btn = QPushButton(pipette_icon(), "  Damlalık: ekrandan / duvar kağıdından renk seç")
    btn.setIconSize(QSize(24, 24))
    btn.setMinimumHeight(36)

    def got(col):
        if col is not None and col.isValid():
            dlg.setCurrentColor(col)
        dlg.show()
        dlg.raise_()
        dlg.activateWindow()

    btn.clicked.connect(lambda _c=False: pick_screen_color(got))
    lay = dlg.layout()
    try:
        if isinstance(lay, QVBoxLayout):
            lay.insertWidget(0, btn)
        else:
            lay.addWidget(btn, lay.rowCount(), 0, 1, -1)
    except Exception:
        pass
    loop = QEventLoop()
    dlg.finished.connect(loop.quit)
    dlg.show()
    loop.exec()
    if dlg.result() == QDialog.DialogCode.Accepted.value:
        return dlg.currentColor()
    return QColor()


# ======================================================================
# Küçük UI yardımcıları
# ======================================================================
def add_act(menu, text, fn, checked=None):
    a = menu.addAction(text)
    if checked is None:
        a.triggered.connect(lambda _c=False: fn())
    else:
        a.setCheckable(True)
        a.setChecked(bool(checked))
        a.triggered.connect(lambda c: fn(bool(c)))
    return a


def row_slider(form, label, lo, hi, slot):
    s = QSlider(Qt.Orientation.Horizontal)
    s.setRange(lo, hi)
    s.setMinimumWidth(220)
    sp = QSpinBox()
    sp.setRange(lo, hi)
    s.valueChanged.connect(sp.setValue)
    sp.valueChanged.connect(s.setValue)
    s.valueChanged.connect(slot)
    lay = QHBoxLayout()
    lay.addWidget(s, 1)
    lay.addWidget(sp)
    form.addRow(label, lay)
    return s


def poly(pts):
    return QPolygonF([QPointF(pts[i], pts[i + 1]) for i in range(0, len(pts), 2)])


def hex_h(cx, cy, L, t):
    return poly([cx - L / 2, cy, cx - L / 2 + t / 2, cy - t / 2,
                 cx + L / 2 - t / 2, cy - t / 2, cx + L / 2, cy,
                 cx + L / 2 - t / 2, cy + t / 2, cx - L / 2 + t / 2, cy + t / 2])


def hex_v(cx, cy, L, t):
    return poly([cx, cy - L / 2, cx + t / 2, cy - L / 2 + t / 2,
                 cx + t / 2, cy + L / 2 - t / 2, cx, cy + L / 2,
                 cx - t / 2, cy + L / 2 - t / 2, cx - t / 2, cy - L / 2 + t / 2])


# ======================================================================
# Taban widget
# ======================================================================
class BaseWidget(QWidget):
    def __init__(self, mgr, cfg):
        super().__init__()
        self.mgr = mgr
        self.app = mgr.app
        self.cfg = cfg
        self.dialog = None
        self._press = None
        self._drag_off = None
        self._dragging = False
        self._flags_sig = None
        self._hovering = False
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating, True)
        self.setMouseTracking(True)
        self.setWindowTitle(TYPE_LABELS.get(cfg["type"], "Widget"))

    # ---- alt sınıfların doldurduğu
    def content_size(self):
        return 100, 100

    def paint_content(self, p):
        pass

    def make_dialog(self):
        return None

    def keep_on_reset(self):
        return {}

    def on_hover(self, pt):
        pass

    def on_leave(self):
        pass

    def on_click(self, pt):
        pass

    def on_double_click(self):
        pass

    def slot_menu(self, m, pt):
        pass

    # ---- ortak
    def start(self):
        self.apply_flags()
        self.relayout()

    def apply_flags(self):
        z = self.cfg["zpos"]
        sig = (z, bool(self.cfg["click_through"]))
        if sig == self._flags_sig:
            return
        self._flags_sig = sig
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
        if z == "top":
            flags |= Qt.WindowType.WindowStaysOnTopHint
        elif z == "desktop" and not IS_WIN:
            flags |= Qt.WindowType.WindowStaysOnBottomHint
        if self.cfg["click_through"]:
            flags |= Qt.WindowType.WindowTransparentForInput
        self.setWindowFlags(flags)
        self.show()
        self.pin_tick()

    def relayout(self):
        W, H = self.content_size()
        geo = self.app.primaryScreen().virtualGeometry()
        x = max(geo.left() - W + 60, min(int(self.cfg["x"]), geo.right() - 60))
        y = max(geo.top() - H + 60, min(int(self.cfg["y"]), geo.bottom() - 60))
        self.cfg["x"], self.cfg["y"] = x, y
        self.setGeometry(x, y, W, H)
        self.update()

    def pin_tick(self):
        if self.cfg["zpos"] != "desktop":
            return
        try:
            if self.mgr.pinner:
                self.mgr.pinner.pin(int(self.winId()))
            elif not IS_WIN:
                self.lower()
        except Exception:
            pass

    def changed(self):
        self.relayout()
        self.mgr.schedule_save()

    def set_flag(self, key, val):
        self.cfg[key] = val
        if key in ("zpos", "click_through"):
            self.apply_flags()
        self.changed()
        if self.dialog:
            self.dialog.sync()

    def cfg_replaced(self):
        """Dosyadan yeniden yüklenince çağrılır."""
        self._flags_sig = None
        self.apply_flags()
        self.relayout()
        if self.dialog:
            self.dialog.sync()

    def reset_defaults(self):
        keep = {k: self.cfg[k] for k in ("id", "type", "x", "y")}
        keep.update(self.keep_on_reset())
        new = DEFAULTS[self.cfg["type"]]()
        new.update(keep)
        self.cfg.clear()
        self.cfg.update(new)
        self._flags_sig = None
        self.apply_flags()
        self.changed()
        if self.dialog:
            self.dialog.sync()

    def open_settings(self):
        if self.dialog is None:
            self.dialog = self.make_dialog()
        if self.dialog is None:
            return
        self.dialog.sync()
        self.dialog.show()
        self.dialog.raise_()
        self.dialog.activateWindow()

    # ---- menü
    def fill_menu(self, m, pt=None):
        if pt is not None:
            self.slot_menu(m, pt)
        add_act(m, "Ayarlar…", self.open_settings)
        sub = m.addMenu("Widget ekle")
        for typ, label in TYPE_LABELS.items():
            add_act(sub, label, lambda t=typ: self.mgr.add_widget(t, near=self))
        add_act(m, "Bu widget'ı kaldır", lambda: self.mgr.remove_widget(self))
        add_act(m, "Ortak tema…", self.mgr.open_theme)
        m.addSeparator()
        om = m.addMenu("Şeffaflık")
        for v in (100, 90, 80, 70, 60, 50, 40, 30, 20, 10):
            add_act(om, f"%{v}", lambda _c, v=v: self.set_flag("global_opacity", v),
                    checked=self.cfg["global_opacity"] == v)
        if self.cfg["type"] == "clock":
            add_act(m, "Üstüne gelince soluklaştır",
                    lambda c: self.set_flag("hide_hover", c), checked=self.cfg["hide_hover"])
        zs = m.addMenu("Katman")
        for key, label in ZPOS:
            add_act(zs, label, lambda _c, k=key: self.set_flag("zpos", k),
                    checked=self.cfg["zpos"] == key)
        add_act(m, "Konumu kilitle", lambda c: self.set_flag("locked", c),
                checked=self.cfg["locked"])
        add_act(m, "Tıklamayı geçir (tepsiden kapatılır)",
                lambda c: self.set_flag("click_through", c),
                checked=self.cfg["click_through"])
        add_act(m, "Kenarlara yapış", lambda c: self.set_flag("snap", c),
                checked=self.cfg["snap"])
        m.addSeparator()
        add_act(m, "Çıkış", self.mgr.quit)

    def contextMenuEvent(self, e):
        m = QMenu()
        self.fill_menu(m, QPointF(e.pos()))
        m.exec(e.globalPos())

    # ---- fare
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._press = e.globalPosition().toPoint()
            self._drag_off = self._press - self.frameGeometry().topLeft()
            self._dragging = False

    def mouseMoveEvent(self, e):
        self.on_hover(e.position())
        if self._press is None:
            return
        gp = e.globalPosition().toPoint()
        if (not self._dragging and not self.cfg["locked"]
                and (gp - self._press).manhattanLength() > 6):
            self._dragging = True
        if self._dragging:
            pos = gp - self._drag_off
            if self.cfg["snap"]:
                pos = self.snap(pos)
            self.move(pos)

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or self._press is None:
            return
        if self._dragging:
            self.cfg["x"], self.cfg["y"] = self.x(), self.y()
            self.mgr.schedule_save()
            if self.dialog:
                self.dialog.common.sync_position()
        else:
            self.on_click(e.position())
        self._press = None
        self._dragging = False

    def mouseDoubleClickEvent(self, e):
        self.on_double_click()

    def enterEvent(self, e):
        self._hovering = True
        if self.cfg["hide_hover"]:
            self.update()

    def leaveEvent(self, e):
        self._hovering = False
        self.on_leave()
        if self.cfg["hide_hover"]:
            self.update()

    def snap(self, pos, th=18):
        pad = int(self.cfg.get("pad", 0))
        cw, ch = self.width() - 2 * pad, self.height() - 2 * pad
        screen = (self.app.screenAt(QPoint(pos.x() + self.width() // 2,
                                           pos.y() + self.height() // 2))
                  or self.app.primaryScreen())
        g = screen.availableGeometry()
        x, y = pos.x(), pos.y()
        if abs(x + pad - g.left()) < th:
            x = g.left() - pad
        elif abs(x + pad + cw - (g.right() + 1)) < th:
            x = g.right() + 1 - cw - pad
        if abs(y + pad - g.top()) < th:
            y = g.top() - pad
        elif abs(y + pad + ch - (g.bottom() + 1)) < th:
            y = g.bottom() + 1 - ch - pad
        # ---- diğer widget'lara yapış (yan yana / alt alta / kenar hizası)
        w, h = self.width(), self.height()
        gap = int(self.mgr.theme.get("gap", 10))
        bx = by = None
        for o in self.mgr.widgets:
            if o is self or not o.isVisible() or o.cfg.get("type") == "wallfx":
                continue
            ox, oy, ow, oh = o.x(), o.y(), o.width(), o.height()
            near_y = y < oy + oh + th and y + h > oy - th
            near_x = x < ox + ow + th and x + w > ox - th
            xs = [ox, ox + ow - w]
            ys = [oy, oy + oh - h]
            if near_y:
                xs += [ox + ow + gap, ox - w - gap]
            if near_x:
                ys += [oy + oh + gap, oy - h - gap]
            for cand in xs:
                d = abs(x - cand)
                if d < th and (bx is None or d < bx[0]):
                    bx = (d, cand)
            for cand in ys:
                d = abs(y - cand)
                if d < th and (by is None or d < by[0]):
                    by = (d, cand)
        if bx:
            x = bx[1]
        if by:
            y = by[1]
        return QPoint(x, y)

    def paint_panel(self, p, r, radius):
        """Ortak cam panel: yarı saydam dolgu + üst parlama + ince kenarlık."""
        c = self.cfg
        pa = int(c.get("panel_alpha", 0))
        if pa > 0:
            col = QColor(c["panel_color"])
            col.setAlphaF(pa / 100)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
            p.drawRoundedRect(r, radius, radius)
            gr = QLinearGradient(r.topLeft(), r.bottomLeft())
            gr.setColorAt(0.0, QColor(255, 255, 255, 34))
            gr.setColorAt(0.5, QColor(255, 255, 255, 0))
            p.setBrush(QBrush(gr))
            p.drawRoundedRect(r, radius, radius)
        ba = int(c.get("border_alpha", 0))
        if ba > 0:
            bc = QColor(255, 255, 255)
            bc.setAlphaF(ba / 100)
            pen = QPen(bc, 1.0)
            p.setPen(pen)
            p.setBrush(Qt.BrushStyle.NoBrush)
            p.drawRoundedRect(r.adjusted(0.5, 0.5, -0.5, -0.5), radius, radius)
        p.setPen(Qt.PenStyle.NoPen)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        # neredeyse görünmez zemin: boş alana da tıklanıp sürüklenebilsin
        p.fillRect(self.rect(), QColor(0, 0, 0, 1))
        op = self.cfg["global_opacity"] / 100
        if self.cfg["hide_hover"] and self._hovering and not self._dragging:
            op *= 0.12
        p.setOpacity(op)
        p.setPen(Qt.PenStyle.NoPen)
        self.paint_content(p)
        p.end()


# ======================================================================
# Saat widget'ı
# ======================================================================
class ClockWidget(BaseWidget):
    def __init__(self, mgr, cfg):
        super().__init__(mgr, cfg)
        self._glyph_cache = {}
        self.timer = QTimer(self, interval=500)
        self.timer.timeout.connect(self.update)
        self.timer.start()
        self.start()

    def content_size(self):
        c = self.cfg
        w = sum(i["w"] for i in c["items"]) + c["gap"] * 4 + 2 * c["pad"]
        h = max(i["h"] for i in c["items"]) + 2 * c["pad"] + 4
        return int(w), int(h)

    def make_dialog(self):
        return ClockDialog(self)

    def on_double_click(self):
        self.open_settings()

    def glyph(self, ch):
        key = (self.cfg["font"], ch)
        if key not in self._glyph_cache:
            f = QFont(self.cfg["font"])
            f.setPixelSize(200)
            f.setBold(True)
            path = QPainterPath()
            path.addText(0, 0, f, ch)
            self._glyph_cache[key] = path
        return self._glyph_cache[key]

    def draw_segments(self, p, ch, x0, y0, it):
        w, h = it["w"], it["h"]
        t = max(2, min(it["t"], w * 0.45, h * 0.22))
        g = 2
        hl = max(2, w - t - 2 * g)
        vl = max(2, (h / 2 - t / 2) - 2 * g)
        xl, xr, xm = x0 + t / 2, x0 + w - t / 2, x0 + w / 2
        ya, yg, yd = y0 + t / 2, y0 + h / 2, y0 + h - t / 2
        yu, yl = (ya + yg) / 2, (yg + yd) / 2
        shapes = {
            "a": hex_h(xm, ya, hl, t), "g": hex_h(xm, yg, hl, t),
            "d": hex_h(xm, yd, hl, t), "f": hex_v(xl, yu, vl, t),
            "b": hex_v(xr, yu, vl, t), "e": hex_v(xl, yl, vl, t),
            "c": hex_v(xr, yl, vl, t),
        }
        for s in SEGMENTS[ch]:
            p.drawPolygon(shapes[s])

    def draw_font_digit(self, p, ch, x0, y0, it):
        ref = self.glyph("0").boundingRect()
        if ref.width() <= 0 or ref.height() <= 0:
            return
        sx, sy = it["w"] / ref.width(), it["h"] / ref.height()
        path = self.glyph(ch)
        br = path.boundingRect()
        tx = x0 + (it["w"] - br.width() * sx) / 2 - br.left() * sx
        ty = y0 - ref.top() * sy
        tr = QTransform()
        tr.translate(tx, ty)
        tr.scale(sx, sy)
        p.drawPath(tr.map(path))

    def draw_colon(self, p, x0, y0, it):
        w, h = it["w"], it["h"]
        bw = min(it["t"], w)
        bh = h * 0.17
        cx = x0 + w / 2
        r = min(bw, bh) * 0.25
        for cy in (y0 + h * 0.30, y0 + h * 0.70):
            p.drawRoundedRect(QRectF(cx - bw / 2, cy - bh / 2, bw, bh), r, r)

    def draw_items(self, p, chars, blink_on, shadow):
        pad, gap = self.cfg["pad"], self.cfg["gap"]
        max_h = max(i["h"] for i in self.cfg["items"])
        x = pad
        for ch, it in zip(chars, self.cfg["items"]):
            y0 = pad + (max_h - it["h"]) / 2
            col = QColor(it["color"])
            if not col.isValid():
                col = QColor("#FFFFFF")
            a = max(0.0, min(1.0, it["alpha"] / 100))
            if shadow:
                col = QColor(0, 0, 0)
                a *= 0.35
                y0 += 3
            col.setAlphaF(a)
            p.setBrush(col)
            if ch == ":":
                if blink_on:
                    self.draw_colon(p, x, y0, it)
            elif self.cfg["mode"] == "font":
                self.draw_font_digit(p, ch, x, y0, it)
            else:
                self.draw_segments(p, ch, x, y0, it)
            x += it["w"] + gap

    def paint_content(self, p):
        self.paint_panel(p, QRectF(0, 0, self.width(), self.height()), self.cfg["radius"])
        now = datetime.now()
        hour = now.hour if self.cfg["use_24h"] else (now.hour % 12 or 12)
        chars = list(f"{hour:02d}") + [":"] + list(f"{now.minute:02d}")
        blink_on = (now.second % 2 == 0) or not self.cfg["blink"]
        if self.cfg["shadow"]:
            self.draw_items(p, chars, blink_on, True)
        self.draw_items(p, chars, blink_on, False)


# ======================================================================
# Uygulama çubuğu widget'ı
# ======================================================================
class AppBarWidget(BaseWidget):
    def __init__(self, mgr, cfg):
        super().__init__(mgr, cfg)
        self.hover = None
        self.setAcceptDrops(True)
        self.start()

    # ---- geometri
    def rows(self):
        n, cols = len(self.cfg["slots"]), max(1, int(self.cfg["cols"]))
        return (n + cols - 1) // cols

    def content_size(self):
        c = self.cfg
        cols = max(1, min(int(c["cols"]), len(c["slots"])))
        w = 2 * c["pad"] + cols * c["tile"] + (cols - 1) * c["gap"]
        h = 2 * c["pad"] + self.rows() * c["tile"] + (self.rows() - 1) * c["gap"]
        return int(w), int(h)

    def tile_rect(self, i):
        c = self.cfg
        cols = max(1, int(c["cols"]))
        col, row = i % cols, i // cols
        x = c["pad"] + col * (c["tile"] + c["gap"])
        y = c["pad"] + row * (c["tile"] + c["gap"])
        return QRectF(x, y, c["tile"], c["tile"])

    def hit(self, pt):
        pt = QPointF(pt)
        for i in range(len(self.cfg["slots"])):
            if self.tile_rect(i).contains(pt):
                return i
        return None

    def make_dialog(self):
        return BarDialog(self)

    def keep_on_reset(self):
        return {"slots": self.cfg["slots"], "n_slots": self.cfg["n_slots"]}

    # ---- slot işlemleri
    def set_slot_count(self, n):
        n = max(1, min(MAX_SLOTS, int(n)))
        slots = self.cfg["slots"][:n]
        slots += [None] * (n - len(slots))
        self.cfg["slots"] = slots
        self.cfg["n_slots"] = n
        self.changed()
        self.mgr.update_info()

    def clear_slot(self, i):
        self.cfg["slots"][i] = None
        self.changed()

    def clear_all(self):
        self.cfg["slots"] = [None] * len(self.cfg["slots"])
        self.changed()

    def assign_slots(self, start, new_slots):
        slots = self.cfg["slots"]
        n = len(slots)
        idx = start
        placed = 0
        for k, s in enumerate(new_slots):
            if k == 0:
                slots[idx] = s
                placed += 1
                continue
            for off in range(1, n + 1):  # sıradaki boş slotu bul
                j = (idx + off) % n
                if slots[j] is None:
                    slots[j] = s
                    idx = j
                    placed += 1
                    break
        if placed < len(new_slots):
            self.mgr.notify(f"Yeterli boş slot yok: {len(new_slots) - placed} öğe eklenemedi. "
                            "Ayarlardan slot sayısını artırabilir veya yeni çubuk ekleyebilirsin.")
        self.changed()

    def first_empty(self):
        for i, s in enumerate(self.cfg["slots"]):
            if s is None:
                return i
        return 0

    def pick_for(self, i):
        dlg = AppPicker()
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.result_slots:
            self.assign_slots(i, dlg.result_slots)

    def open_slot(self, i):
        s = self.cfg["slots"][i]
        if not s:
            return
        try:
            launch(s)
        except Exception as err:
            self.mgr.notify(f"Başlatılamadı: {s['name']}\n{err}")

    # ---- etkileşim
    def on_hover(self, pt):
        h = self.hit(pt)
        if h != self.hover:
            self.hover = h
            self.setCursor(Qt.CursorShape.PointingHandCursor if h is not None
                           else Qt.CursorShape.ArrowCursor)
            self.update()

    def on_leave(self):
        if self.hover is not None:
            self.hover = None
            self.update()

    def on_click(self, pt):
        i = self.hit(pt)
        if i is None:
            return
        if self.cfg["slots"][i]:
            self.open_slot(i)
        else:
            self.pick_for(i)

    def slot_menu(self, m, pt):
        i = self.hit(pt)
        if i is None:
            return
        if self.cfg["slots"][i]:
            add_act(m, "Aç", lambda i=i: self.open_slot(i))
            add_act(m, "Değiştir…", lambda i=i: self.pick_for(i))
            add_act(m, "Slotu temizle", lambda i=i: self.clear_slot(i))
        else:
            add_act(m, "Uygulama ekle…", lambda i=i: self.pick_for(i))
        m.addSeparator()

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        new = []
        for url in e.mimeData().urls():
            path = url.toLocalFile()
            if path:
                new.append({"name": os.path.splitext(os.path.basename(path.rstrip("/\\")))[0]
                            or path, "path": path, "kind": "file"})
        if not new:
            return
        i = self.hit(e.position())
        self.assign_slots(i if i is not None else self.first_empty(), new)
        e.acceptProposedAction()

    # ---- çizim
    def paint_content(self, p):
        c = self.cfg
        W, H = self.width(), self.height()
        self.paint_panel(p, QRectF(0, 0, W, H), c["radius"] + c["pad"] / 2)

        label_font = QFont()
        label_font.setPixelSize(int(c["label_size"] * 1.35))
        fm = QFontMetrics(label_font)
        label_h = fm.height() + 2 if c["show_labels"] else 0
        icon = min(int(c["icon"]), int(c["tile"]) - label_h - 6)
        icon = max(12, icon)

        for i, slot in enumerate(c["slots"]):
            rect = self.tile_rect(i)
            hovered = (i == self.hover)
            col = QColor(c["tile_color"])
            col.setAlphaF((c["hover_alpha"] if hovered else c["tile_alpha"]) / 100)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(col)
            p.drawRoundedRect(rect, c["radius"], c["radius"])

            if slot:
                pm = icon_for_slot(slot).pixmap(QSize(icon * 2, icon * 2))
                ix = rect.x() + (rect.width() - icon) / 2
                iy = rect.y() + (rect.height() - label_h - icon) / 2 + 2
                p.drawPixmap(QRectF(ix, iy, icon, icon).toRect(), pm)
                if c["show_labels"]:
                    p.setFont(label_font)
                    tc = QColor(c["label_color"])
                    p.setPen(tc)
                    text = fm.elidedText(slot["name"], Qt.TextElideMode.ElideRight,
                                         int(rect.width()) - 8)
                    p.drawText(QRectF(rect.x() + 4, rect.bottom() - label_h - 3,
                                      rect.width() - 8, label_h), ALIGN_CENTER, text)
            else:  # boş slot: + işareti
                pc = QColor(c["label_color"])
                pc.setAlphaF(0.75 if hovered else 0.35)
                pen = QPen(pc, 2.5)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                p.setPen(pen)
                cx, cy = rect.center().x(), rect.center().y()
                s = min(rect.width(), rect.height()) * 0.14
                p.drawLine(QPointF(cx - s, cy), QPointF(cx + s, cy))
                p.drawLine(QPointF(cx, cy - s), QPointF(cx, cy + s))
            p.setPen(Qt.PenStyle.NoPen)


# ======================================================================
# Ortak taban: tema panelli, ölçeklenebilir yeni widget'lar
# ======================================================================
AYLAR = ["Ocak", "Şubat", "Mart", "Nisan", "Mayıs", "Haziran", "Temmuz",
         "Ağustos", "Eylül", "Ekim", "Kasım", "Aralık"]
GUNLER = ["Pt", "Sa", "Ça", "Pe", "Cu", "Ct", "Pz"]
_CPU_STATE = {"prev": None}


def cpu_percent():
    try:
        import psutil  # varsa en doğrusu
        return float(psutil.cpu_percent(None))
    except Exception:
        pass
    try:
        if IS_WIN:
            import ctypes
            idle, ker, usr = ctypes.c_ulonglong(), ctypes.c_ulonglong(), ctypes.c_ulonglong()
            ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(ker),
                                                  ctypes.byref(usr))
            cur = (idle.value, ker.value, usr.value)
        elif sys.platform.startswith("linux"):
            with open("/proc/stat") as f:
                v = [int(x) for x in f.readline().split()[1:]]
            cur = (v[3] + (v[4] if len(v) > 4 else 0), sum(v), 0)
        else:
            return min(100.0, os.getloadavg()[0] * 100 / (os.cpu_count() or 1))
        prev, _CPU_STATE["prev"] = _CPU_STATE["prev"], cur
        if not prev:
            return 0.0
        if IS_WIN:
            di, dk, du = (cur[i] - prev[i] for i in range(3))
            tot = dk + du
            return max(0.0, min(100.0, 100.0 * (tot - di) / tot)) if tot > 0 else 0.0
        di, dt = cur[0] - prev[0], cur[1] - prev[1]
        return max(0.0, min(100.0, 100.0 * (dt - di) / dt)) if dt > 0 else 0.0
    except Exception:
        return 0.0


def ram_info():
    """(yüzde, kullanılan GB, toplam GB)"""
    try:
        import psutil
        m = psutil.virtual_memory()
        return m.percent, (m.total - m.available) / 2**30, m.total / 2**30
    except Exception:
        pass
    try:
        if IS_WIN:
            import ctypes

            class MS(ctypes.Structure):
                _fields_ = [("l", ctypes.c_ulong), ("load", ctypes.c_ulong),
                            ("tp", ctypes.c_ulonglong), ("ap", ctypes.c_ulonglong),
                            ("tpf", ctypes.c_ulonglong), ("apf", ctypes.c_ulonglong),
                            ("tv", ctypes.c_ulonglong), ("av", ctypes.c_ulonglong),
                            ("ae", ctypes.c_ulonglong)]
            m = MS()
            m.l = ctypes.sizeof(MS)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return float(m.load), (m.tp - m.ap) / 2**30, m.tp / 2**30
        if sys.platform.startswith("linux"):
            info = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    k, v = line.split(":", 1)
                    info[k] = int(v.split()[0]) * 1024
            tot, av = info["MemTotal"], info["MemAvailable"]
            return 100.0 * (tot - av) / tot, (tot - av) / 2**30, tot / 2**30
    except Exception:
        pass
    return 0.0, 0.0, 0.0


def disk_info():
    try:
        root = (os.path.splitdrive(sys.executable)[0] + "\\") if IS_WIN else "/"
        u = shutil.disk_usage(root or "/")
        return 100.0 * u.used / u.total, u.used / 2**30, u.total / 2**30
    except Exception:
        return 0.0, 0.0, 0.0


class PanelWidget(BaseWidget):
    """Temayla uyumlu, tek ayar (boyut %) ile ölçeklenen widget tabanı."""
    BASE = (300, 300)
    TICK = 1000
    TITLE = "Widget"
    SETTINGS = []   # ("int", key, etiket, min, max) / ("bool", key, etiket)

    def __init__(self, mgr, cfg):
        super().__init__(mgr, cfg)
        self.init_state()
        self.timer = None
        if self.TICK:
            self.timer = QTimer(self)
            self.timer.setInterval(self.TICK)
            self.timer.timeout.connect(self.tick)
            self.timer.start()
        self.tick()
        self.start()

    # ---- alt sınıflar
    def init_state(self):
        pass

    def tick(self):
        self.update()

    def draw(self, p, W, H):
        pass

    def base_size(self):
        return self.BASE

    # ---- ortak
    def k(self):
        return max(0.3, self.cfg["scale"] / 100)

    def content_size(self):
        bw, bh = self.base_size()
        return int(bw * self.k()), int(bh * self.k())

    def make_dialog(self):
        return PanelDialog(self)

    def on_double_click(self):
        self.open_settings()

    def lp(self, pt):
        k = self.k()
        return QPointF(pt.x() / k, pt.y() / k)

    def paint_content(self, p):
        k = self.k()
        bw, bh = self.base_size()
        self.paint_panel(p, QRectF(0, 0, self.width(), self.height()), self.cfg["radius"] * k)
        p.save()
        p.scale(k, k)
        self.draw(p, bw, bh)
        p.restore()

    def acc(self, a=1.0):
        c = QColor(self.cfg["accent"])
        c.setAlphaF(max(0.0, min(1.0, a)))
        return c

    def txt(self, a=1.0):
        c = QColor(self.cfg["text"])
        c.setAlphaF(max(0.0, min(1.0, a)))
        return c

    def T(self, p, x, y, w, h, s, px, col, bold=False, al=ALIGN_CENTER, fam=None):
        f = QFont(fam) if fam else QFont()
        f.setPixelSize(int(px))
        f.setBold(bold)
        p.setFont(f)
        p.setPen(col)
        p.drawText(QRectF(x, y, w, h), al, s)
        p.setPen(Qt.PenStyle.NoPen)

    def bar(self, p, x, y, w, h, frac, col=None):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.txt(0.16))
        p.drawRoundedRect(QRectF(x, y, w, h), h / 2, h / 2)
        fw = max(0.0, min(1.0, frac)) * w
        if fw > 0:
            p.setBrush(col or self.acc())
            p.drawRoundedRect(QRectF(x, y, max(fw, h), h), h / 2, h / 2)


# ---------------------------------------------------------------- Takvim
class CalendarWidget(PanelWidget):
    BASE, TICK, TITLE = (300, 322), 30000, "Takvim"
    SETTINGS = [("bool", "monday_first", "Hafta Pazartesi ile başlasın")]

    def init_state(self):
        self.off = 0

    def month(self):
        t = date.today()
        y, m = divmod(t.year * 12 + t.month - 1 + self.off, 12)
        return y, m + 1

    def draw(self, p, W, H):
        today = date.today()
        y, m = self.month()
        self.T(p, 50, 12, W - 100, 34, f"{AYLAR[m - 1]} {y}", 21, self.txt(), True)
        self.T(p, 10, 12, 40, 34, "‹", 26, self.txt(0.6))
        self.T(p, W - 50, 12, 40, 34, "›", 26, self.txt(0.6))
        mon = bool(self.cfg["monday_first"])
        names = GUNLER if mon else [GUNLER[6]] + GUNLER[:6]
        cw = (W - 32) / 7
        for i, n in enumerate(names):
            self.T(p, 16 + i * cw, 54, cw, 22, n, 12, self.acc(0.95), True)
        cal = calendar.Calendar(firstweekday=0 if mon else 6)
        weeks = cal.monthdatescalendar(y, m)
        while len(weeks) < 6:
            last = weeks[-1][-1]
            weeks.append([last + timedelta(days=i + 1) for i in range(7)])
        for r, wk in enumerate(weeks):
            for c, d in enumerate(wk):
                x, yy = 16 + c * cw, 80 + r * 38
                if d == today:
                    p.setPen(Qt.PenStyle.NoPen)
                    p.setBrush(self.acc())
                    p.drawEllipse(QPointF(x + cw / 2, yy + 19), 17, 17)
                    self.T(p, x, yy, cw, 38, str(d.day), 15, QColor("#FFFFFF"), True)
                else:
                    a = 0.95 if d.month == m else 0.25
                    self.T(p, x, yy, cw, 38, str(d.day), 15, self.txt(a))

    def on_click(self, pt):
        pt = self.lp(pt)
        if pt.y() < 52:
            self.off = self.off - 1 if pt.x() < 80 else self.off + 1 if pt.x() > 220 else 0
            self.update()

    def wheelEvent(self, e):
        self.off += -1 if e.angleDelta().y() > 0 else 1
        self.update()


# ---------------------------------------------------------------- Sistem monitörü
class SysMonWidget(PanelWidget):
    TICK, TITLE = 1000, "Sistem monitörü"
    SETTINGS = [("bool", "show_cpu", "İşlemci (CPU)"), ("bool", "show_ram", "Bellek (RAM)"),
                ("bool", "show_disk", "Disk")]

    def init_state(self):
        self.vals = {"cpu": (0.0, ""), "ram": (0.0, ""), "disk": (0.0, "")}
        self.n = 0

    def rows(self):
        return [k for k in ("cpu", "ram", "disk") if self.cfg["show_" + k]] or ["cpu"]

    def base_size(self):
        return 280, 40 + len(self.rows()) * 46

    def tick(self):
        c = self.cfg
        if c.get("show_cpu", True):
            self.vals["cpu"] = (cpu_percent(), "")
        if c.get("show_ram", True):
            pct, used, tot = ram_info()
            self.vals["ram"] = (pct, f"{used:.1f} / {tot:.1f} GB")
        if c.get("show_disk", True) and self.n % 15 == 0:
            pct, used, tot = disk_info()
            self.vals["disk"] = (pct, f"{used:.0f} / {tot:.0f} GB")
        self.n += 1
        self.update()

    def draw(self, p, W, H):
        self.T(p, 20, 12, 120, 18, "SİSTEM", 11, self.txt(0.5), True, ALIGN_L)
        names = {"cpu": "CPU", "ram": "RAM", "disk": "Disk"}
        for i, k in enumerate(self.rows()):
            y = 36 + i * 46
            pct, extra = self.vals[k]
            self.T(p, 20, y, 80, 20, names[k], 15, self.txt(), True, ALIGN_L)
            right = f"{extra}   {pct:.0f}%" if extra else f"{pct:.0f}%"
            self.T(p, 90, y, W - 110, 20, right, 14, self.acc(), True, ALIGN_R)
            hot = QColor("#FF5C5C") if pct >= 90 else None
            self.bar(p, 20, y + 26, W - 40, 8, pct / 100, hot)


# ---------------------------------------------------------------- Not defteri
class NotesWidget(PanelWidget):
    BASE, TICK, TITLE = (260, 200), 0, "Not defteri"
    SETTINGS = [("int", "font_px", "Yazı boyutu", 8, 48)]

    def init_state(self):
        self._ed = None

    def keep_on_reset(self):
        return {"text": self.cfg["text"]}

    def draw(self, p, W, H):
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.acc())
        p.drawRoundedRect(QRectF(18, 16, 30, 4), 2, 2)
        text = self.cfg["text"].strip()
        f = QFont()
        f.setPixelSize(int(self.cfg["font_px"]))
        p.setFont(f)
        p.setPen(self.txt(0.95 if text else 0.4))
        flags = (Qt.TextFlag.TextWordWrap.value | Qt.AlignmentFlag.AlignTop.value
                 | Qt.AlignmentFlag.AlignLeft.value)
        p.drawText(QRectF(18, 30, W - 36, H - 46), flags,
                   text or "Not yazmak için çift tıkla…")
        p.setPen(Qt.PenStyle.NoPen)

    def edit(self):
        if self._ed is not None:
            self._ed.raise_()
            return
        dlg = QDialog()
        dlg.setWindowTitle("Not")
        dlg.resize(360, 300)
        lay = QVBoxLayout(dlg)
        te = QPlainTextEdit()
        te.setPlainText(self.cfg["text"])
        lay.addWidget(te)

        def changed():
            self.cfg["text"] = te.toPlainText()
            self.update()
            self.mgr.schedule_save()
        te.textChanged.connect(changed)
        b = QPushButton("Kapat")
        b.clicked.connect(dlg.close)
        lay.addWidget(b)
        dlg.finished.connect(lambda _r: setattr(self, "_ed", None))
        self._ed = dlg
        dlg.show()

    def on_double_click(self):
        self.edit()

    def slot_menu(self, m, pt):
        add_act(m, "Notu düzenle…", self.edit)
        m.addSeparator()


# ---------------------------------------------------------------- Analog saat
class AnalogWidget(PanelWidget):
    BASE, TICK, TITLE = (260, 260), 60, "Analog saat"
    SETTINGS = [("bool", "show_seconds", "Akrep: saniye ibresi"),
                ("bool", "show_numbers", "Sayıları göster")]

    def tick(self):
        iv = 60 if self.cfg.get("show_seconds", True) else 1000
        if self.timer and self.timer.interval() != iv:
            self.timer.setInterval(iv)
        self.update()

    def hand(self, p, ang, ln, wd, col):
        p.save()
        p.translate(130, 130)
        p.rotate(ang)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(col)
        p.drawRoundedRect(QRectF(-wd / 2, -ln, wd, ln + 12), wd / 2, wd / 2)
        p.restore()

    def draw(self, p, W, H):
        now = datetime.now()
        p.setBrush(self.txt(0.06))
        p.setPen(QPen(self.acc(0.9), 5))
        p.drawEllipse(QPointF(130, 130), 104, 104)
        for i in range(60):
            long = i % 5 == 0
            p.save()
            p.translate(130, 130)
            p.rotate(i * 6)
            p.setPen(QPen(self.txt(0.9 if long else 0.3), 3 if long else 1.5,
                          Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
            p.drawLine(QPointF(0, -92), QPointF(0, -80 if long else -86))
            p.restore()
        if self.cfg["show_numbers"]:
            for h in range(1, 13):
                a = math.radians(h * 30)
                x, y = 130 + 64 * math.sin(a), 130 - 64 * math.cos(a)
                self.T(p, x - 15, y - 12, 30, 24, str(h), 18, self.txt(0.85), True)
        sec = now.second + now.microsecond / 1e6
        self.hand(p, ((now.hour % 12) + now.minute / 60) * 30, 50, 8, self.txt())
        self.hand(p, (now.minute + sec / 60) * 6, 76, 5, self.txt())
        if self.cfg["show_seconds"]:
            self.hand(p, sec * 6, 90, 2.4, self.acc())
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.acc())
        p.drawEllipse(QPointF(130, 130), 7, 7)


# ---------------------------------------------------------------- Zamanlayıcı (Pomodoro)
class TimerWidget(PanelWidget):
    BASE, TICK, TITLE = (280, 150), 200, "Zamanlayıcı"
    SETTINGS = [("int", "focus_min", "Odak süresi (dk)", 1, 180),
                ("int", "break_min", "Mola süresi (dk)", 1, 60),
                ("bool", "auto_next", "Süre bitince sonraki aşamayı otomatik başlat")]

    def init_state(self):
        self.mode = "focus"
        self.running = False
        self.touched = False
        self.end = 0.0
        self.remaining = self.cfg["focus_min"] * 60

    def total(self):
        return max(1, (self.cfg["focus_min"] if self.mode == "focus" else self.cfg["break_min"]) * 60)

    def tick(self):
        if self.running:
            rem = self.end - time.monotonic()
            if rem <= 0:
                self.finish_phase()
            else:
                self.remaining = rem
        elif not self.touched:
            self.remaining = self.total()
        self.update()

    def finish_phase(self):
        QApplication.beep()
        self.mgr.notify("Odak süresi bitti, mola zamanı!" if self.mode == "focus"
                        else "Mola bitti, odaklanma zamanı!")
        self.mode = "break" if self.mode == "focus" else "focus"
        self.remaining = self.total()
        if self.cfg["auto_next"]:
            self.end = time.monotonic() + self.remaining
        else:
            self.running = False
            self.touched = False

    def toggle(self):
        if self.running:
            self.running = False
            self.remaining = max(0.0, self.end - time.monotonic())
        else:
            self.running = self.touched = True
            self.end = time.monotonic() + self.remaining
        self.update()

    def reset(self, mode=None):
        if mode:
            self.mode = mode
        self.running = self.touched = False
        self.remaining = self.total()
        self.update()

    def on_click(self, pt):
        self.toggle()

    def slot_menu(self, m, pt):
        add_act(m, "Duraklat" if self.running else "Başlat", self.toggle)
        add_act(m, "Sıfırla", self.reset)
        add_act(m, "Odak moduna geç", lambda: self.reset("focus"))
        add_act(m, "Mola moduna geç", lambda: self.reset("break"))
        m.addSeparator()

    def draw(self, p, W, H):
        focus = self.mode == "focus"
        self.T(p, 20, 12, 120, 20, "ODAK" if focus else "MOLA", 13,
               self.acc() if focus else QColor("#4ADE80"), True, ALIGN_L)
        state = "ÇALIŞIYOR" if self.running else ("DURAKLATILDI" if self.touched else "BAŞLAMAK İÇİN TIKLA")
        self.T(p, 110, 12, W - 130, 20, state, 11, self.txt(0.5), True, ALIGN_R)
        m, s = divmod(int(math.ceil(self.remaining)), 60)
        self.T(p, 0, 34, W, 72, f"{m:02d}:{s:02d}", 62, self.acc() if focus else QColor("#4ADE80"),
               True, ALIGN_CENTER, "Consolas")
        done = 1 - self.remaining / self.total()
        self.bar(p, 20, H - 28, W - 40, 8, done, None if focus else QColor("#4ADE80"))


# ======================================================================
# Yeni widget'lar (2): Pil, Hızlı arama, Kronometre, Geri sayım, Tarih kartı
# ======================================================================
GUN_UZUN = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
ENGINES = [("Google", "https://www.google.com/search?q="),
           ("Bing", "https://www.bing.com/search?q="),
           ("YouTube", "https://www.youtube.com/results?search_query="),
           ("DuckDuckGo", "https://duckduckgo.com/?q=")]


def battery_info():
    """(yüzde, şarjda_mı) ya da pil yoksa None."""
    try:
        import psutil
        b = psutil.sensors_battery()
        return (float(b.percent), bool(b.power_plugged)) if b else None
    except Exception:
        pass
    try:
        if IS_WIN:
            import ctypes

            class SPS(ctypes.Structure):
                _fields_ = [("ac", ctypes.c_ubyte), ("flag", ctypes.c_ubyte),
                            ("pct", ctypes.c_ubyte), ("sf", ctypes.c_ubyte),
                            ("life", ctypes.c_ulong), ("full", ctypes.c_ulong)]
            st = SPS()
            ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(st))
            if st.pct == 255 or st.flag & 128:
                return None
            return float(st.pct), st.ac == 1
        base = "/sys/class/power_supply"
        for n in sorted(os.listdir(base)):
            if n.startswith("BAT"):
                with open(f"{base}/{n}/capacity") as f:
                    pct = float(f.read())
                with open(f"{base}/{n}/status") as f:
                    return pct, f.read().strip() in ("Charging", "Full")
    except Exception:
        pass
    return None


class BatteryWidget(PanelWidget):
    BASE, TICK, TITLE = (230, 110), 5000, "Pil durumu"
    SETTINGS = []

    def init_state(self):
        self.info = None

    def tick(self):
        self.info = battery_info()
        self.update()

    def draw(self, p, W, H):
        pct, chg = self.info if self.info else (0.0, False)
        col = QColor("#4ADE80") if chg else QColor("#FF5C5C") if pct < 20 else self.acc()
        p.setPen(QPen(self.txt(0.9), 4))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(20, 30, 84, 48), 9, 9)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.txt(0.9))
        p.drawRoundedRect(QRectF(106, 44, 7, 20), 3, 3)
        if self.info:
            p.setBrush(col)
            p.drawRoundedRect(QRectF(26, 36, max(6.0, 72 * pct / 100), 36), 5, 5)
        self.T(p, 120, 22, W - 130, 46, f"{pct:.0f}%" if self.info else "—", 38, col, True, ALIGN_R)
        txt = "Şarj oluyor ⚡" if (self.info and chg) else "Pilde" if self.info else "Pil yok (masaüstü)"
        self.T(p, 20, 84, W - 40, 20, txt, 13, self.txt(0.6), False, ALIGN_L)


class SearchWidget(PanelWidget):
    BASE, TICK, TITLE = (320, 64), 0, "Hızlı arama"
    SETTINGS = [("int", "engine", "Motor: 0 Google, 1 Bing, 2 YouTube, 3 DuckDuckGo", 0, 3)]

    def draw(self, p, W, H):
        p.setBrush(self.txt(0.12))
        p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(QRectF(14, 12, W - 28, H - 24), (H - 24) / 2, (H - 24) / 2)
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.setPen(QPen(self.acc(), 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
        p.drawEllipse(QPointF(40, 30), 8, 8)
        p.drawLine(QPointF(46, 36), QPointF(53, 43))
        name = ENGINES[max(0, min(3, int(self.cfg["engine"])))][0]
        self.T(p, 66, 12, W - 90, H - 24, f"{name} ile ara…", 16, self.txt(0.6), False, ALIGN_L)

    def on_click(self, pt):
        name, url = ENGINES[max(0, min(3, int(self.cfg["engine"])))]
        q, ok = QInputDialog.getText(None, "Hızlı arama", f"{name}:")
        if ok and q.strip():
            webbrowser.open(url + quote(q.strip()))


class StopwatchWidget(PanelWidget):
    BASE, TICK, TITLE = (280, 170), 50, "Kronometre"
    SETTINGS = []

    def init_state(self):
        self.running = False
        self.elapsed = 0.0
        self.t0 = 0.0
        self.laps = []

    def now_el(self):
        return self.elapsed + (time.monotonic() - self.t0 if self.running else 0.0)

    def fmt(self, t):
        h, r = divmod(int(t), 3600)
        m, s = divmod(r, 60)
        cs = int((t - int(t)) * 100)
        return f"{h}:{m:02d}:{s:02d}" if h else f"{m:02d}:{s:02d}.{cs:02d}"

    def toggle(self):
        if self.running:
            self.elapsed += time.monotonic() - self.t0
            self.running = False
        else:
            self.t0 = time.monotonic()
            self.running = True
        self.update()

    def reset(self):
        self.running = False
        self.elapsed = 0.0
        self.laps = []
        self.update()

    def lap(self):
        if self.running:
            self.laps.append(self.now_el())
        self.update()

    def on_click(self, pt):
        self.toggle()

    def slot_menu(self, m, pt):
        add_act(m, "Duraklat" if self.running else "Başlat", self.toggle)
        add_act(m, "Tur kaydet", self.lap)
        add_act(m, "Sıfırla", self.reset)
        m.addSeparator()

    def draw(self, p, W, H):
        self.T(p, 20, 12, 150, 20, "KRONOMETRE", 12, self.txt(0.5), True, ALIGN_L)
        self.T(p, 110, 12, W - 130, 20, "ÇALIŞIYOR" if self.running else "TIKLA: BAŞLAT",
               11, self.acc(0.9), True, ALIGN_R)
        self.T(p, 0, 32, W, 64, self.fmt(self.now_el()), 50, self.acc(), True, ALIGN_CENTER, "Consolas")
        for i, t in enumerate(self.laps[-3:][::-1]):
            n = len(self.laps) - i
            self.T(p, 20, 104 + i * 18, W - 40, 18, f"Tur {n}    {self.fmt(t)}", 13,
                   self.txt(0.7), False, ALIGN_L, "Consolas")


class CountdownWidget(PanelWidget):
    BASE, TICK, TITLE = (280, 160), 1000, "Geri sayım"
    SETTINGS = [("int", "year", "Yıl", 2024, 2100), ("int", "month", "Ay", 1, 12),
                ("int", "day", "Gün", 1, 31)]

    def target(self):
        c = self.cfg
        y, m = int(c["year"]), max(1, min(12, int(c["month"])))
        d = max(1, min(calendar.monthrange(y, m)[1], int(c["day"])))
        return datetime(y, m, d)

    def rename(self):
        t, ok = QInputDialog.getText(None, "Geri sayım", "Etiket:", text=self.cfg["label"])
        if ok:
            self.cfg["label"] = t
            self.changed()

    def slot_menu(self, m, pt):
        add_act(m, "Etiketi değiştir…", self.rename)
        m.addSeparator()

    def draw(self, p, W, H):
        diff = self.target() - datetime.now()
        past = diff.total_seconds() < 0
        diff = abs(diff)
        days, rem = diff.days, diff.seconds
        self.T(p, 20, 12, W - 40, 22, self.cfg["label"].upper(), 14, self.txt(0.7), True, ALIGN_L)
        self.T(p, 0, 36, W, 70, str(days), 64, QColor("#FF9F43") if past else self.acc(), True)
        self.T(p, 0, 104, W, 22, "gün önce" if past else "gün kaldı", 15, self.txt(0.85))
        self.T(p, 0, 128, W, 20, f"{rem // 3600} sa {(rem % 3600) // 60} dk {rem % 60} sn",
               13, self.txt(0.5), False, ALIGN_CENTER, "Consolas")


class DateCardWidget(PanelWidget):
    BASE, TICK, TITLE = (200, 210), 30000, "Tarih kartı"
    SETTINGS = [("bool", "show_year", "Yılı göster")]

    def draw(self, p, W, H):
        t = date.today()
        mon = AYLAR[t.month - 1].upper() + (f" {t.year}" if self.cfg["show_year"] else "")
        self.T(p, 0, 14, W, 30, mon, 18, self.acc(), True)
        self.T(p, 0, 40, W, 110, str(t.day), 96, self.txt(), True)
        self.T(p, 0, 156, W, 36, GUN_UZUN[t.weekday()], 22, self.txt(0.8))


# ======================================================================
# Medya oynatıcı (Spotify / tarayıcı / sistem medya oturumu)
# ======================================================================
MEDIA_VK = {"play": 0xB3, "next": 0xB0, "prev": 0xB1, "volup": 0xAF, "voldown": 0xAE, "mute": 0xAD}
MEDIA_LINUX = {"play": ["playerctl", "play-pause"], "next": ["playerctl", "next"],
               "prev": ["playerctl", "previous"],
               "volup": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"],
               "voldown": ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"],
               "mute": ["pactl", "set-sink-mute", "@DEFAULT_SINK@", "toggle"]}


def media_cmd(name):
    try:
        if IS_WIN:
            import ctypes
            vk = MEDIA_VK[name]
            ctypes.windll.user32.keybd_event(vk, 0, 1, 0)
            ctypes.windll.user32.keybd_event(vk, 0, 3, 0)
        elif sys.platform.startswith("linux"):
            subprocess.Popen(MEDIA_LINUX[name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _win_titles():
    """[(başlık, exe)] – yalnızca ' - ' içeren görünür pencereler."""
    import ctypes
    from ctypes import wintypes
    u, k = ctypes.windll.user32, ctypes.windll.kernel32
    u.IsWindowVisible.argtypes = [wintypes.HWND]
    u.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    u.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
    u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    k.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    k.OpenProcess.restype = wintypes.HANDLE
    k.CloseHandle.argtypes = [wintypes.HANDLE]
    k.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
                                             ctypes.POINTER(wintypes.DWORD)]
    out = []
    proc_t = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        n = u.GetWindowTextLengthW(hwnd)
        if n <= 0:
            return True
        buf = ctypes.create_unicode_buffer(n + 1)
        u.GetWindowTextW(hwnd, buf, n + 1)
        title = buf.value
        if " - " not in title:
            return True
        pid = wintypes.DWORD()
        u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        h = k.OpenProcess(0x1000, False, pid.value)
        exe = ""
        if h:
            sz = wintypes.DWORD(520)
            b2 = ctypes.create_unicode_buffer(520)
            if k.QueryFullProcessImageNameW(h, 0, b2, ctypes.byref(sz)):
                exe = os.path.basename(b2.value).lower()
            k.CloseHandle(h)
        out.append((title, exe))
        return True

    u.EnumWindows(proc_t(cb), 0)
    return out


class MediaPoller:
    """Arka planda çalan medyayı okur (winsdk varsa tam bilgi + kapak, yoksa pencere başlığı)."""

    def __init__(self):
        self.state = self.empty()
        self.api = None
        self._tk = None
        self._tb = None
        self.ev = threading.Event()
        threading.Thread(target=self.run, daemon=True).start()

    @staticmethod
    def empty():
        return {"title": "", "artist": "", "playing": False, "pos": 0.0, "dur": 0.0,
                "t": time.monotonic(), "thumb": None, "app": ""}

    def kick(self):
        self.ev.set()

    def run(self):
        import asyncio
        loop = asyncio.new_event_loop()
        while True:
            st = None
            try:
                if IS_WIN and self.api is not False:
                    st = loop.run_until_complete(self.win_api())
                    self.api = True
            except ImportError:
                self.api = False
            except Exception:
                st = None
            try:
                if st is None:
                    st = self.fallback()
            except Exception:
                st = None
            self.state = st or self.empty()
            self.ev.wait(1.5)
            self.ev.clear()

    async def win_api(self):
        import importlib
        mod = None
        for pre in ("winsdk", "winrt"):
            try:
                mod = importlib.import_module(pre + ".windows.media.control")
                st_mod = importlib.import_module(pre + ".windows.storage.streams")
                break
            except ImportError:
                continue
        if mod is None:
            raise ImportError("winsdk yok")
        mgr = await mod.GlobalSystemMediaTransportControlsSessionManager.request_async()
        ses = mgr.get_current_session()
        if not ses:
            return None
        props = await ses.try_get_media_properties_async()
        pb = ses.get_playback_info()
        tl = ses.get_timeline_properties()
        key = (props.title, props.artist)
        if key != self._tk:
            self._tk, self._tb = key, None
            try:
                ref = props.thumbnail
                if ref:
                    stream = await ref.open_read_async()
                    size = int(stream.size)
                    reader = st_mod.DataReader(stream.get_input_stream_at(0))
                    await reader.load_async(size)
                    buf = bytearray(size)
                    reader.read_bytes(buf)
                    self._tb = bytes(buf)
            except Exception:
                self._tb = None
        return {"title": props.title or "", "artist": props.artist or "",
                "playing": int(pb.playback_status) == 4,
                "pos": tl.position.total_seconds(),
                "dur": max(0.0, tl.end_time.total_seconds() - tl.start_time.total_seconds()),
                "t": time.monotonic(), "thumb": self._tb, "app": ses.source_app_user_model_id or ""}

    def fallback(self):
        st = self.empty()
        if IS_WIN:
            for title, exe in _win_titles():
                if exe == "spotify.exe" and title not in ("Spotify", "Spotify Free", "Spotify Premium"):
                    a, _s, t = title.partition(" - ")
                    st.update(title=t or title, artist=a, playing=True, app="Spotify")
                    return st
            for title, _exe in _win_titles():
                if " - YouTube" in title:
                    st.update(title=title.split(" - YouTube")[0], artist="YouTube",
                              playing=True, app="YouTube")
                    return st
            return None
        if sys.platform.startswith("linux"):
            r = subprocess.run(["playerctl", "metadata", "--format",
                                "{{status}}|{{artist}}|{{title}}|{{position}}|{{mpris:length}}"],
                               capture_output=True, text=True, timeout=2)
            if r.returncode == 0 and r.stdout.strip():
                s, a, t, pos, ln = (r.stdout.strip().split("|") + ["", "", "", "0", "0"])[:5]
                st.update(title=t, artist=a, playing=(s == "Playing"),
                          pos=int(pos or 0) / 1e6, dur=int(ln or 0) / 1e6)
                return st
        return None


_POLLER = None


def get_poller():
    global _POLLER
    if _POLLER is None:
        _POLLER = MediaPoller()
    return _POLLER


class MediaWidget(PanelWidget):
    BASE, TICK, TITLE = (360, 150), 250, "Medya oynatıcı"
    SETTINGS = [("bool", "show_art", "Albüm kapağını göster"),
                ("bool", "show_progress", "İlerleme çubuğunu göster")]

    def init_state(self):
        self.poller = get_poller()
        self.art = None
        self.art_key = None
        c = lambda x: QRectF(x - 16, 102, 32, 32)  # noqa: E731
        self.btns = {"voldown": c(150), "prev": c(192), "play": QRectF(222, 98, 40, 40),
                     "next": c(294), "volup": c(334)}

    def tick(self):
        st = self.poller.state
        key = (st["title"], st["artist"])
        if key != self.art_key:
            self.art_key = key
            self.art = None
            if st["thumb"]:
                pm = QPixmap()
                if pm.loadFromData(st["thumb"]):
                    self.art = pm
        self.update()

    def cmd(self, name):
        media_cmd(name)
        QTimer.singleShot(600, self.poller.kick)

    def on_click(self, pt):
        pt = self.lp(pt)
        for name, r in self.btns.items():
            if r.contains(pt):
                self.cmd(name)
                return

    def wheelEvent(self, e):
        self.cmd("volup" if e.angleDelta().y() > 0 else "voldown")

    def slot_menu(self, m, pt):
        add_act(m, "Oynat / Duraklat", lambda: self.cmd("play"))
        add_act(m, "Önceki", lambda: self.cmd("prev"))
        add_act(m, "Sonraki", lambda: self.cmd("next"))
        add_act(m, "Sesi kapat / aç", lambda: self.cmd("mute"))
        m.addSeparator()

    def elide(self, p, text, px, w, bold=False):
        f = QFont()
        f.setPixelSize(px)
        f.setBold(bold)
        return QFontMetrics(f).elidedText(text, Qt.TextElideMode.ElideRight, int(w))

    @staticmethod
    def mmss(t):
        t = max(0, int(t))
        return f"{t // 60}:{t % 60:02d}"

    def draw(self, p, W, H):
        st = self.poller.state
        playing = st["playing"]
        has = bool(st["title"])
        x0 = 140 if self.cfg["show_art"] else 20
        tw = W - x0 - 16
        if self.cfg["show_art"]:
            path = QPainterPath()
            path.addRoundedRect(QRectF(16, 20, 110, 110), 14, 14)
            p.save()
            p.setClipPath(path)
            if self.art:
                pm = self.art.scaled(220, 220, Qt.AspectRatioMode.KeepAspectRatioByExpanding,
                                     Qt.TransformationMode.SmoothTransformation)
                p.drawPixmap(QRectF(16, 20, 110, 110), pm,
                             QRectF((pm.width() - 220) / 2, (pm.height() - 220) / 2, 220, 220))
            else:
                g = QLinearGradient(16, 20, 126, 130)
                g.setColorAt(0, self.acc())
                g.setColorAt(1, self.acc(0.35))
                p.fillRect(QRectF(16, 20, 110, 110), QBrush(g))
                self.T(p, 16, 20, 110, 110, "♪", 54, QColor(255, 255, 255, 220), True)
            p.restore()
        title = st["title"] if has else "Çalan medya yok"
        artist = st["artist"] if has else "Spotify veya tarayıcıda bir şey çal"
        self.T(p, x0, 14, tw, 28, self.elide(p, title, 18, tw, True), 18, self.txt(), True, ALIGN_L)
        self.T(p, x0, 42, tw, 22, self.elide(p, artist, 14, tw), 14, self.txt(0.65), False, ALIGN_L)
        if self.cfg["show_progress"]:
            pos = st["pos"] + ((time.monotonic() - st["t"]) if playing else 0.0)
            dur = st["dur"]
            frac = min(1.0, pos / dur) if dur > 0 else 0.0
            self.bar(p, x0, 72, tw, 6, frac)
            if dur > 0:
                self.T(p, x0, 80, 60, 16, self.mmss(min(pos, dur)), 11, self.txt(0.55), False, ALIGN_L)
                self.T(p, x0 + tw - 60, 80, 60, 16, self.mmss(dur), 11, self.txt(0.55), False, ALIGN_R)
        # ---- düğmeler
        b = self.btns
        self.T(p, b["voldown"].x(), b["voldown"].y(), 32, 32, "−", 24, self.txt(0.75), True)
        self.T(p, b["volup"].x(), b["volup"].y(), 32, 32, "+", 24, self.txt(0.75), True)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.txt(0.9))
        r = b["prev"]
        cx, cy = r.center().x(), r.center().y()
        p.drawRect(QRectF(cx - 9, cy - 8, 3, 16))
        p.drawPolygon(poly([cx + 8, cy - 8, cx + 8, cy + 8, cx - 5, cy]))
        r = b["next"]
        cx, cy = r.center().x(), r.center().y()
        p.drawRect(QRectF(cx + 6, cy - 8, 3, 16))
        p.drawPolygon(poly([cx - 8, cy - 8, cx - 8, cy + 8, cx + 5, cy]))
        r = b["play"]
        cx, cy = r.center().x(), r.center().y()
        p.setBrush(self.acc())
        p.drawEllipse(r)
        p.setBrush(QColor("#FFFFFF"))
        if playing:
            p.drawRoundedRect(QRectF(cx - 7, cy - 8, 5, 16), 1.5, 1.5)
            p.drawRoundedRect(QRectF(cx + 2, cy - 8, 5, 16), 1.5, 1.5)
        else:
            p.drawPolygon(poly([cx - 5, cy - 9, cx - 5, cy + 9, cx + 9, cy]))


# ======================================================================
# Yeni widget'lar (3): Yapılacaklar, Ağ hızı, Çöp kutusu, Pano geçmişi,
#                      Ses görselleştirici, Sistem düğmeleri
# ======================================================================
def confirm_box(text):
    return QMessageBox.question(None, "Onay", text,
                                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes


def fmt_speed(b):
    for unit in ("B/s", "KB/s", "MB/s"):
        if b < 1024 or unit == "MB/s":
            return f"{b:.0f} {unit}" if unit == "B/s" else f"{b:.1f} {unit}"
        b /= 1024


# ---------------------------------------------------------------- Yapılacaklar
class TodoWidget(PanelWidget):
    BASE, TICK, TITLE = (300, 200), 0, "Yapılacaklar"
    SETTINGS = [("int", "max_rows", "Görünen satır sayısı", 3, 15),
                ("bool", "hide_done", "Tamamlananları gizle")]

    def tasks(self):
        if not isinstance(self.cfg.get("tasks"), list):
            self.cfg["tasks"] = []
        return self.cfg["tasks"]

    def rows(self):
        idx = [i for i, t in enumerate(self.tasks())
               if isinstance(t, dict) and not (self.cfg["hide_done"] and t.get("d"))]
        mr = int(self.cfg["max_rows"])
        return idx[:mr], max(0, len(idx) - mr)

    def base_size(self):
        rows, extra = self.rows()
        return 300, 44 + (max(len(rows), 1) + (1 if extra else 0)) * 30 + 40

    def keep_on_reset(self):
        return {"tasks": self.tasks()}

    def row_at(self, pt):
        rows, _e = self.rows()
        i = int((pt.y() - 40) // 30)
        return rows[i] if pt.y() >= 40 and 0 <= i < len(rows) else None

    def add_task(self):
        t, ok = QInputDialog.getText(None, "Yeni görev", "Görev:")
        if ok and t.strip():
            self.tasks().append({"t": t.strip(), "d": False})
            self.changed()

    def edit_task(self, i):
        t, ok = QInputDialog.getText(None, "Görevi düzenle", "Görev:", text=self.tasks()[i]["t"])
        if ok and t.strip():
            self.tasks()[i]["t"] = t.strip()
            self.changed()

    def del_task(self, i):
        del self.tasks()[i]
        self.changed()

    def clear_done(self):
        self.cfg["tasks"] = [t for t in self.tasks() if not (isinstance(t, dict) and t.get("d"))]
        self.changed()

    def on_click(self, pt):
        pt = self.lp(pt)
        i = self.row_at(pt)
        if i is not None:
            self.tasks()[i]["d"] = not self.tasks()[i].get("d")
            self.changed()
        else:
            rows, extra = self.rows()
            add_y = 40 + (max(len(rows), 1) + (1 if extra else 0)) * 30
            if pt.y() >= add_y:
                self.add_task()

    def slot_menu(self, m, pt):
        i = self.row_at(self.lp(pt))
        add_act(m, "Görev ekle…", self.add_task)
        if i is not None:
            add_act(m, "Görevi düzenle…", lambda: self.edit_task(i))
            add_act(m, "Görevi sil", lambda: self.del_task(i))
        add_act(m, "Tamamlananları temizle", self.clear_done)
        m.addSeparator()

    def draw(self, p, W, H):
        tasks = [t for t in self.tasks() if isinstance(t, dict)]
        done = sum(1 for t in tasks if t.get("d"))
        self.T(p, 20, 12, 180, 22, "YAPILACAKLAR", 12, self.txt(0.5), True, ALIGN_L)
        self.T(p, W - 90, 12, 70, 22, f"{done}/{len(tasks)}", 13, self.acc(), True, ALIGN_R)
        rows, extra = self.rows()
        if not rows:
            self.T(p, 20, 40, W - 40, 30, "Görev yok", 15, self.txt(0.4), False, ALIGN_L)
        for n, i in enumerate(rows):
            t = tasks[i] if i < len(tasks) else {"t": "", "d": False}
            t = self.tasks()[i]
            y = 40 + n * 30
            d = bool(t.get("d"))
            c = QPointF(30, y + 15)
            if d:
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(self.acc())
                p.drawEllipse(c, 9, 9)
                p.setPen(QPen(QColor("#FFFFFF"), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawPolyline(QPolygonF([QPointF(25.5, y + 15), QPointF(29, y + 18.5), QPointF(35, y + 11.5)]))
            else:
                p.setPen(QPen(self.txt(0.5), 2))
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.drawEllipse(c, 9, 9)
            f = QFont()
            f.setPixelSize(16)
            txt = QFontMetrics(f).elidedText(str(t.get("t", "")), Qt.TextElideMode.ElideRight, W - 80)
            self.T(p, 50, y, W - 70, 30, txt, 16, self.txt(0.4 if d else 0.95), False, ALIGN_L)
            if d:
                tw = QFontMetrics(f).horizontalAdvance(txt)
                p.setPen(QPen(self.txt(0.4), 1.5))
                p.drawLine(QPointF(50, y + 15), QPointF(50 + tw, y + 15))
        y = 40 + max(len(rows), 1) * 30
        if extra:
            self.T(p, 50, y, W - 70, 30, f"+{extra} görev daha", 13, self.txt(0.5), False, ALIGN_L)
            y += 30
        self.T(p, 20, y + 6, W - 40, 28, "+  Görev ekle", 15, self.acc(), True, ALIGN_L)


# ---------------------------------------------------------------- Ağ hızı
def net_counters():
    """{anahtar: (alınan_bayt, gönderilen_bayt, sayaç_bit)}"""
    try:
        import psutil
        c = psutil.net_io_counters()
        return {"all": (c.bytes_recv, c.bytes_sent, 64)}
    except Exception:
        pass
    try:
        if IS_WIN:
            import ctypes

            class IFROW(ctypes.Structure):
                _fields_ = ([("name", ctypes.c_wchar * 256)]
                            + [(n, ctypes.c_ulong) for n in ("index", "type", "mtu", "speed", "palen")]
                            + [("pa", ctypes.c_ubyte * 8)]
                            + [(n, ctypes.c_ulong) for n in (
                                "admin", "oper", "lastchange", "inoct", "inucast", "innucast",
                                "indisc", "inerr", "inunk", "outoct", "outucast", "outnucast",
                                "outdisc", "outerr", "outqlen", "descrlen")]
                            + [("descr", ctypes.c_ubyte * 256)])
            iph = ctypes.windll.iphlpapi
            size = ctypes.c_ulong(0)
            iph.GetIfTable(None, ctypes.byref(size), False)
            buf = ctypes.create_string_buffer(size.value)
            if iph.GetIfTable(buf, ctypes.byref(size), False) != 0:
                return {}
            n = ctypes.c_ulong.from_buffer(buf, 0).value
            rs = ctypes.sizeof(IFROW)
            out = {}
            for i in range(n):
                row = IFROW.from_buffer_copy(buf, 4 + i * rs)
                if row.type != 24 and row.oper >= 4:
                    out[row.index] = (row.inoct, row.outoct, 32)
            return out
        if sys.platform.startswith("linux"):
            rx = tx = 0
            with open("/proc/net/dev") as f:
                for line in list(f)[2:]:
                    name, data = line.split(":", 1)
                    if name.strip() != "lo":
                        v = data.split()
                        rx += int(v[0])
                        tx += int(v[8])
            return {"all": (rx, tx, 64)}
    except Exception:
        pass
    return {}


class NetSpeedWidget(PanelWidget):
    BASE, TICK, TITLE = (300, 175), 1000, "Ağ hızı"
    SETTINGS = [("int", "history", "Grafik süresi (sn)", 20, 120),
                ("bool", "show_graph", "Grafiği göster")]

    def init_state(self):
        self.prev = None
        self.prev_t = 0.0
        self.hist = []
        self.peak = (0.0, 0.0)

    def base_size(self):
        return (300, 175) if self.cfg["show_graph"] else (300, 90)

    def tick(self):
        cur, now = net_counters(), time.monotonic()
        if self.prev is not None and now > self.prev_t:
            dt = now - self.prev_t
            rx = tx = 0
            for k, (r, t, bits) in cur.items():
                if k in self.prev:
                    mask = (1 << bits) - 1
                    rx += (r - self.prev[k][0]) & mask
                    tx += (t - self.prev[k][1]) & mask
            self.hist.append((rx / dt, tx / dt))
            self.hist = self.hist[-int(self.cfg["history"]):]
            self.peak = (max(self.peak[0], rx / dt), max(self.peak[1], tx / dt))
        self.prev, self.prev_t = cur, now
        self.update()

    def draw(self, p, W, H):
        d, u = self.hist[-1] if self.hist else (0.0, 0.0)
        green = QColor("#4ADE80")
        self.T(p, 20, 10, 100, 18, "AĞ", 12, self.txt(0.5), True, ALIGN_L)
        self.T(p, 20, 30, 130, 36, "↓ " + fmt_speed(d), 20, self.acc(), True, ALIGN_L)
        self.T(p, 150, 30, 130, 36, "↑ " + fmt_speed(u), 20, green, True, ALIGN_R)
        if not self.cfg["show_graph"]:
            return
        gx, gy, gw, gh = 20, 76, W - 40, 72
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(self.txt(0.06))
        p.drawRoundedRect(QRectF(gx, gy, gw, gh), 8, 8)
        n = len(self.hist)
        if n >= 2:
            mx = max(10 * 1024.0, max(max(a, b) for a, b in self.hist))
            step = gw / (max(int(self.cfg["history"]), 2) - 1)
            for idx, col, fill in ((0, self.acc(), True), (1, green, False)):
                pts = [QPointF(gx + gw - (n - 1 - i) * step,
                               gy + gh - 4 - (gh - 8) * self.hist[i][idx] / mx) for i in range(n)]
                line = QPainterPath()
                line.moveTo(pts[0])
                for q in pts[1:]:
                    line.lineTo(q)
                if fill:
                    area = QPainterPath(line)
                    area.lineTo(pts[-1].x(), gy + gh)
                    area.lineTo(pts[0].x(), gy + gh)
                    area.closeSubpath()
                    c = QColor(col)
                    c.setAlphaF(0.28)
                    p.setBrush(c)
                    p.setPen(Qt.PenStyle.NoPen)
                    p.drawPath(area)
                p.setBrush(Qt.BrushStyle.NoBrush)
                p.setPen(QPen(col, 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
                p.drawPath(line)
            p.setPen(Qt.PenStyle.NoPen)
        self.T(p, gx, gy + gh + 2, gw, 18, f"zirve  ↓ {fmt_speed(self.peak[0])}   ↑ {fmt_speed(self.peak[1])}",
               11, self.txt(0.45), False, ALIGN_R)


# ---------------------------------------------------------------- Çöp kutusu
def recycle_info():
    """(bayt, öğe sayısı) ya da None"""
    if not IS_WIN:
        return None
    try:
        import ctypes

        class RBI(ctypes.Structure):
            _fields_ = [("cb", ctypes.c_ulong), ("size", ctypes.c_longlong), ("items", ctypes.c_longlong)]
        i = RBI()
        i.cb = ctypes.sizeof(RBI)
        if ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(i)) == 0:
            return i.size, i.items
    except Exception:
        pass
    return None


class RecycleWidget(PanelWidget):
    BASE, TICK, TITLE = (240, 130), 5000, "Çöp kutusu"
    SETTINGS = [("bool", "confirm", "Boşaltmadan önce sor")]

    def init_state(self):
        self.info = None
        self.btn = QRectF(110, 86, 112, 30)

    def tick(self):
        self.info = recycle_info()
        self.update()

    def empty(self):
        if not IS_WIN or not self.info or self.info[1] == 0:
            return
        if self.cfg["confirm"] and not confirm_box(f"Çöp kutusundaki {self.info[1]} öğe kalıcı olarak silinsin mi?"):
            return
        try:
            import ctypes
            ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
        except Exception:
            pass
        QTimer.singleShot(800, self.tick)

    def open_bin(self):
        try:
            subprocess.Popen(["explorer.exe", "shell:RecycleBinFolder"])
        except Exception:
            pass

    def on_click(self, pt):
        if self.btn.contains(self.lp(pt)):
            self.empty()

    def on_double_click(self):
        self.open_bin()

    def slot_menu(self, m, pt):
        add_act(m, "Çöp kutusunu aç", self.open_bin)
        add_act(m, "Çöp kutusunu boşalt", self.empty)
        m.addSeparator()

    def draw(self, p, W, H):
        n = self.info[1] if self.info else 0
        size = self.info[0] if self.info else 0
        p.setPen(QPen(self.acc(), 4, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
        p.setBrush(self.acc(0.3) if n else Qt.BrushStyle.NoBrush)
        p.drawPolygon(poly([32, 44, 80, 44, 74, 104, 38, 104]))
        p.setBrush(Qt.BrushStyle.NoBrush)
        p.drawRoundedRect(QRectF(24, 32, 64, 8), 3, 3)
        p.drawRoundedRect(QRectF(47, 22, 18, 10), 3, 3)
        for x in (46, 56, 66):
            p.drawLine(QPointF(x, 54), QPointF(x - (56 - x) * 0.0 - 1 if x < 56 else x + 0, 94))
        p.setPen(Qt.PenStyle.NoPen)
        if not IS_WIN:
            self.T(p, 100, 30, 130, 50, "Yalnızca Windows", 13, self.txt(0.6), False, ALIGN_L)
            return
        mb = size / 2**20
        sz = f"{mb / 1024:.1f} GB" if mb >= 1024 else f"{mb:.0f} MB"
        self.T(p, 100, 22, W - 110, 34, sz if n else "Boş", 26, self.acc(), True, ALIGN_L)
        self.T(p, 100, 56, W - 110, 22, f"{n} öğe" if n else "silinecek bir şey yok", 13, self.txt(0.65), False, ALIGN_L)
        p.setBrush(self.acc(0.9) if n else self.txt(0.12))
        p.drawRoundedRect(self.btn, 15, 15)
        self.T(p, self.btn.x(), self.btn.y(), self.btn.width(), self.btn.height(), "Boşalt", 14,
               QColor("#FFFFFF") if n else self.txt(0.4), True)


# ---------------------------------------------------------------- Pano geçmişi
class ClipHub:
    """Pano değişikliklerini toplar. Yalnızca bellekte tutulur, diske yazılmaz."""

    def __init__(self):
        self.items = []
        self.cb = QApplication.clipboard()
        self.cb.dataChanged.connect(self.on_change)
        self.on_change()

    def on_change(self):
        try:
            t = self.cb.text()
        except Exception:
            return
        if t and t.strip() and len(t) <= 5000:
            if t in self.items:
                self.items.remove(t)
            self.items.insert(0, t)
            del self.items[50:]


_CLIPHUB = None


def get_cliphub():
    global _CLIPHUB
    if _CLIPHUB is None:
        _CLIPHUB = ClipHub()
    return _CLIPHUB


class ClipboardWidget(PanelWidget):
    BASE, TICK, TITLE = (320, 200), 500, "Pano geçmişi"
    SETTINGS = [("int", "rows", "Görünen satır sayısı", 3, 10)]

    def init_state(self):
        self.hub = get_cliphub()
        self.flash = -1

    def base_size(self):
        return 320, 46 + int(self.cfg["rows"]) * 34 + 8

    def on_click(self, pt):
        pt = self.lp(pt)
        i = int((pt.y() - 42) // 34)
        if pt.y() >= 42 and 0 <= i < min(int(self.cfg["rows"]), len(self.hub.items)):
            QApplication.clipboard().setText(self.hub.items[i])
            self.flash = i
            QTimer.singleShot(600, lambda: setattr(self, "flash", -1))

    def slot_menu(self, m, pt):
        add_act(m, "Geçmişi temizle", lambda: self.hub.items.clear())
        m.addSeparator()

    def draw(self, p, W, H):
        self.T(p, 20, 12, 200, 22, "PANO GEÇMİŞİ", 12, self.txt(0.5), True, ALIGN_L)
        self.T(p, W - 120, 12, 100, 22, "tıkla: kopyala", 11, self.txt(0.4), False, ALIGN_R)
        items = self.hub.items
        if not items:
            self.T(p, 20, 42, W - 40, 30, "Henüz bir şey kopyalanmadı", 14, self.txt(0.4), False, ALIGN_L)
        f = QFont()
        f.setPixelSize(14)
        fm = QFontMetrics(f)
        for i, t in enumerate(items[:int(self.cfg["rows"])]):
            y = 42 + i * 34
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.acc(0.4) if i == self.flash else self.txt(0.08))
            p.drawRoundedRect(QRectF(16, y, W - 32, 30), 8, 8)
            line = " ".join(t.split())
            self.T(p, 26, y, W - 52, 30, fm.elidedText(line, Qt.TextElideMode.ElideRight, W - 52),
                   14, self.txt(0.95), False, ALIGN_L)


# ---------------------------------------------------------------- Ses görselleştirici
class AudioHub:
    """Sistem sesini (WASAPI loopback) dinleyip 64 bantlık spektrum üretir."""

    N = 64

    def __init__(self):
        self.levels = [0.0] * self.N
        self.error = ""
        self.started = False

    def start(self):
        if self.started:
            return
        self.started = True
        threading.Thread(target=self.run, daemon=True).start()

    def run(self):
        try:
            import numpy as np
            import pyaudiowpatch as pa
        except ImportError:
            self.error = "pip install numpy pyaudiowpatch"
            return
        try:
            p = pa.PyAudio()
            wasapi = p.get_host_api_info_by_type(pa.paWASAPI)
            dev = p.get_device_info_by_index(wasapi["defaultOutputDevice"])
            if not dev.get("isLoopbackDevice"):
                for lb in p.get_loopback_device_info_generator():
                    if dev["name"] in lb["name"]:
                        dev = lb
                        break
            ch = int(dev["maxInputChannels"])
            rate = int(dev["defaultSampleRate"])
            n = 2048
            win = np.hanning(n)
            freqs = np.fft.rfftfreq(n, 1.0 / rate)
            edges = np.geomspace(40, min(14000, rate / 2 - 1), self.N + 1)
            idx = [np.where((freqs >= edges[i]) & (freqs < edges[i + 1]))[0] for i in range(self.N)]
            buf = np.zeros(n)

            def cb(data, frames, ti, status):
                nonlocal buf
                x = np.frombuffer(data, dtype=np.int16).reshape(-1, ch).mean(axis=1)
                buf = np.concatenate([buf, x])[-n:]
                mag = np.abs(np.fft.rfft(buf * win))
                out = []
                for i in range(self.N):
                    sel = idx[i]
                    if len(sel) == 0:
                        out.append(out[-1] if out else 0.0)
                        continue
                    v = (np.log10(float(mag[sel].max()) + 1) - 3.0) / 3.6
                    out.append(float(min(1.0, max(0.0, v))))
                self.levels = out
                return (None, pa.paContinue)

            stream = p.open(format=pa.paInt16, channels=ch, rate=rate, input=True,
                            input_device_index=int(dev["index"]), frames_per_buffer=1024,
                            stream_callback=cb)
            stream.start_stream()
            while stream.is_active():
                time.sleep(0.5)
        except Exception as e:
            self.error = f"Ses yakalanamadı: {e}"


_AUDIOHUB = None


def get_audiohub():
    global _AUDIOHUB
    if _AUDIOHUB is None:
        _AUDIOHUB = AudioHub()
    _AUDIOHUB.start()
    return _AUDIOHUB


class AudioVizWidget(PanelWidget):
    BASE, TICK, TITLE = (320, 120), 33, "Ses görselleştirici"
    SETTINGS = [("int", "bars", "Çubuk sayısı", 8, 64), ("bool", "mirror", "Ortadan simetrik")]

    def init_state(self):
        self.hub = get_audiohub()
        self.lv = [0.0] * 64

    def tick(self):
        src = self.hub.levels
        for i in range(64):
            self.lv[i] = max(src[i], self.lv[i] * 0.86)
        self.update()

    def draw(self, p, W, H):
        if self.hub.error:
            self.T(p, 16, 10, W - 32, H - 20, self.hub.error, 13, self.txt(0.7))
            return
        n = int(self.cfg["bars"])
        per = 64 / n
        gap = 3.0
        bw = (W - 32 - gap * (n - 1)) / n
        base_y, top = (H / 2, 14) if self.cfg["mirror"] else (H - 14, 14)
        full = (H / 2 - top) if self.cfg["mirror"] else (base_y - top)
        p.setPen(Qt.PenStyle.NoPen)
        for i in range(n):
            a, b = int(i * per), max(int(i * per) + 1, int((i + 1) * per))
            v = max(self.lv[a:b])
            h = max(3.0, full * v)
            x = 16 + i * (bw + gap)
            c = self.acc(0.55 + 0.45 * v)
            p.setBrush(c)
            if self.cfg["mirror"]:
                p.drawRoundedRect(QRectF(x, base_y - h, bw, h * 2), bw / 2, bw / 2)
            else:
                p.drawRoundedRect(QRectF(x, base_y - h, bw, h), min(bw / 2, 4), min(bw / 2, 4))


# ---------------------------------------------------------------- Sistem düğmeleri
POWER_ACTIONS = {
    "lock": ("Kilitle", "Ekran kilitlensin mi?",
             {"win": ["rundll32.exe", "user32.dll,LockWorkStation"], "lin": ["loginctl", "lock-session"]}),
    "sleep": ("Uyku", "Bilgisayar uyku moduna alınsın mı?",
              {"win": ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"], "lin": ["systemctl", "suspend"]}),
    "logoff": ("Oturumu kapat", "Oturum kapatılsın mı? Kaydedilmemiş işler kaybolabilir.",
               {"win": ["shutdown", "/l"], "lin": ["loginctl", "terminate-user", os.environ.get("USER", "")]}),
    "restart": ("Yeniden başlat", "Bilgisayar yeniden başlatılsın mı? Kaydedilmemiş işler kaybolabilir.",
                {"win": ["shutdown", "/r", "/t", "0"], "lin": ["systemctl", "reboot"]}),
    "shutdown": ("Kapat", "Bilgisayar kapatılsın mı? Kaydedilmemiş işler kaybolabilir.",
                 {"win": ["shutdown", "/s", "/t", "0"], "lin": ["systemctl", "poweroff"]}),
}


class PowerWidget(PanelWidget):
    TICK, TITLE = 0, "Sistem düğmeleri"
    SETTINGS = [("bool", "show_lock", "Kilitle"), ("bool", "show_sleep", "Uyku"),
                ("bool", "show_logoff", "Oturumu kapat"), ("bool", "show_restart", "Yeniden başlat"),
                ("bool", "show_shutdown", "Kapat"),
                ("bool", "confirm", "Çalıştırmadan önce onay iste (önerilir)")]

    def init_state(self):
        self.hov = None

    def keys(self):
        return [k for k in POWER_ACTIONS if self.cfg["show_" + k]] or ["shutdown"]

    def base_size(self):
        n = len(self.keys())
        return 32 + n * 68 + (n - 1) * 8, 112

    def cell(self, i):
        return QRectF(16 + i * 76, 18, 68, 76)

    def hit(self, pt):
        for i, k in enumerate(self.keys()):
            if self.cell(i).contains(pt):
                return k
        return None

    def on_hover(self, pt):
        h = self.hit(self.lp(pt))
        if h != self.hov:
            self.hov = h
            self.update()

    def on_leave(self):
        self.hov = None
        self.update()

    def run(self, key):
        label, ask, cmds = POWER_ACTIONS[key]
        if self.cfg["confirm"] and not confirm_box(ask):
            return
        try:
            subprocess.Popen(cmds["win"] if IS_WIN else cmds["lin"])
        except Exception:
            pass

    def on_click(self, pt):
        k = self.hit(self.lp(pt))
        if k:
            self.run(k)

    def slot_menu(self, m, pt):
        for k in self.keys():
            add_act(m, POWER_ACTIONS[k][0], lambda k=k: self.run(k))
        m.addSeparator()

    def icon(self, p, key, cx, cy, col):
        pen = QPen(col, 3.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin)
        p.setPen(pen)
        p.setBrush(Qt.BrushStyle.NoBrush)
        if key == "lock":
            p.drawRoundedRect(QRectF(cx - 11, cy - 3, 22, 16), 4, 4)
            p.drawArc(QRectF(cx - 7, cy - 14, 14, 16), 0, 180 * 16)
        elif key == "sleep":
            moon = QPainterPath()
            moon.addEllipse(QRectF(cx - 12, cy - 12, 24, 24))
            cut = QPainterPath()
            cut.addEllipse(QRectF(cx - 4, cy - 16, 22, 22))
            p.setBrush(col)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPath(moon.subtracted(cut))
        elif key == "logoff":
            p.drawPolyline(QPolygonF([QPointF(cx + 2, cy - 12), QPointF(cx - 12, cy - 12),
                                      QPointF(cx - 12, cy + 12), QPointF(cx + 2, cy + 12)]))
            p.drawLine(QPointF(cx - 3, cy), QPointF(cx + 13, cy))
            p.drawPolyline(QPolygonF([QPointF(cx + 8, cy - 5), QPointF(cx + 13, cy), QPointF(cx + 8, cy + 5)]))
        elif key == "restart":
            p.drawArc(QRectF(cx - 12, cy - 12, 24, 24), 60 * 16, 290 * 16)
            p.setBrush(col)
            p.setPen(Qt.PenStyle.NoPen)
            p.drawPolygon(poly([cx + 12, cy - 14, cx + 13, cy - 2, cx + 2, cy - 7]))
        else:  # shutdown
            p.drawArc(QRectF(cx - 12, cy - 12, 24, 24), 120 * 16, -300 * 16)
            p.drawLine(QPointF(cx, cy - 15), QPointF(cx, cy - 1))

    def draw(self, p, W, H):
        colors = {"lock": self.acc(), "sleep": self.acc(), "logoff": QColor("#FBBF24"),
                  "restart": QColor("#FB923C"), "shutdown": QColor("#FF5C5C")}
        for i, k in enumerate(self.keys()):
            r = self.cell(i)
            col = colors[k]
            hot = self.hov == k
            p.setPen(Qt.PenStyle.NoPen)
            bg = QColor(col)
            bg.setAlphaF(0.30 if hot else 0.10)
            p.setBrush(bg)
            p.drawRoundedRect(r, 14, 14)
            self.icon(p, k, r.center().x(), r.y() + 30, col if not hot else QColor("#FFFFFF"))
            self.T(p, r.x(), r.y() + 52, r.width(), 20, POWER_ACTIONS[k][0], 11, self.txt(0.9 if hot else 0.7), hot)


# ======================================================================
# Kırpma aracı (el titremesi düzeltmeli)
# ======================================================================
def snip_correct(img, rect, o):
    """Elle çizilen seçimi düzeltir: kenarlara yapış, ekran kenarına yapış, oranı düzelt.
    img: RGB32 QImage, rect: QRect (görüntü pikseli). Döner: (QRect, ayrıntı)"""
    W, H = img.width(), img.height()
    x1, y1, x2, y2 = rect.left(), rect.top(), rect.left() + rect.width(), rect.top() + rect.height()
    N = int(o.get("snap_px", 12))
    snapped_y = False

    def diff(a, b):
        return (abs(((a >> 16) & 255) - ((b >> 16) & 255)) + abs(((a >> 8) & 255) - ((b >> 8) & 255))
                + abs((a & 255) - (b & 255)))

    def vedge(x, ya, yb):
        step = max(1, (yb - ya) // 50)
        s = n = 0
        for y in range(ya, yb, step):
            s += diff(img.pixel(x - 1, y), img.pixel(x, y))
            n += 1
        return s / max(n, 1)

    def hedge(y, xa, xb):
        step = max(1, (xb - xa) // 50)
        s = n = 0
        for x in range(xa, xb, step):
            s += diff(img.pixel(x, y - 1), img.pixel(x, y))
            n += 1
        return s / max(n, 1)

    def best(c, lo, hi, fn):
        top, sc = c, 0.0
        for cand in range(max(lo, c - N), min(hi, c + N + 1)):
            v = fn(cand)
            eff = v - 2.0 * abs(cand - c)
            if v > 45 and eff > sc:
                top, sc = cand, eff
        return top, sc > 0

    if N > 0 and x2 - x1 > 8 and y2 - y1 > 8:
        ya, yb = max(0, y1), min(H, y2)
        x1, _a = best(x1, 1, W - 1, lambda c: vedge(c, ya, yb))
        x2, _b = best(x2, 1, W - 1, lambda c: vedge(c, ya, yb))
        xa, xb = max(0, x1), min(W, x2)
        if xb - xa > 4:
            y1, _c = best(y1, 1, H - 1, lambda c: hedge(c, xa, xb))
            y2, snapped_y = best(y2, 1, H - 1, lambda c: hedge(c, xa, xb))
    if o.get("snap_screen", True):
        m = 14
        x1 = 0 if x1 <= m else x1
        y1 = 0 if y1 <= m else y1
        x2 = W if W - x2 <= m else x2
        y2 = H if H - y2 <= m else y2
    note = ""
    w, h = x2 - x1, y2 - y1
    if o.get("snap_ratio", True) and not snapped_y and w > 20 and h > 20:
        for rw, rh, name in ((1, 1, "1:1"), (4, 3, "4:3"), (3, 4, "3:4"), (16, 9, "16:9"),
                             (9, 16, "9:16"), (3, 2, "3:2"), (2, 3, "2:3")):
            if abs(w / h - rw / rh) / (rw / rh) < 0.03:
                nh = round(w * rh / rw)
                if y1 + nh <= H:
                    y2 = y1 + nh
                    note = name
                break
    x1, y1 = max(0, x1), max(0, y1)
    x2, y2 = min(W, max(x2, x1 + 4)), min(H, max(y2, y1 + 4))
    return QRect(x1, y1, x2 - x1, y2 - y1), note


class SnipOverlay(QWidget):
    def __init__(self, screen, pixmap, opts, done):
        super().__init__()
        self.pm, self.opts, self.done = pixmap, opts, done
        self.img = pixmap.toImage().convertToFormat(QImage.Format.Format_RGB32)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.Tool
                            | Qt.WindowType.WindowStaysOnTopHint)
        self.setGeometry(screen.geometry())
        self.setCursor(Qt.CursorShape.CrossCursor)
        self.setMouseTracking(True)
        self.a = self.b = None
        self.raw = None
        self.corr, self.note, self._t = None, "", 0.0

    def r(self):
        return self.img.width() / max(1, self.width())

    def raw_rect(self):
        r = self.r()
        x1, x2 = sorted((self.a.x(), self.b.x()))
        y1, y2 = sorted((self.a.y(), self.b.y()))
        return QRect(int(x1 * r), int(y1 * r), max(1, int((x2 - x1) * r)), max(1, int((y2 - y1) * r)))

    def recompute(self):
        self.raw = self.raw_rect()
        self.corr, self.note = snip_correct(self.img, self.raw, self.opts)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self.a = self.b = e.position().toPoint()
            self.corr = None
        else:
            self.done(None)

    def mouseMoveEvent(self, e):
        if self.a is None:
            return
        self.b = e.position().toPoint()
        now = time.monotonic()
        if now - self._t > 0.04:
            self._t = now
            self.recompute()
        self.update()

    def mouseReleaseEvent(self, e):
        if e.button() != Qt.MouseButton.LeftButton or self.a is None:
            return
        self.b = e.position().toPoint()
        if abs(self.b.x() - self.a.x()) < 6 or abs(self.b.y() - self.a.y()) < 6:
            self.a = self.b = None      # titreme / yanlışlıkla tıklama: yok say
            self.corr = None
            self.update()
            return
        self.recompute()
        self.done(self.pm.copy(self.corr))

    def keyPressEvent(self, e):
        if e.key() == Qt.Key.Key_Escape:
            self.done(None)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.drawPixmap(self.rect(), self.pm)
        p.fillRect(self.rect(), QColor(0, 0, 0, 120))
        f = QFont()
        f.setPixelSize(14)
        p.setFont(f)
        if self.a is None or self.corr is None:
            p.setPen(QColor("#FFFFFF"))
            p.drawText(QRectF(0, 20, self.width(), 30), int(Qt.AlignmentFlag.AlignCenter.value),
                       "Kırpılacak alanı sürükle  •  Esc: iptal  •  Titremeler otomatik düzeltilir")
            return
        r = self.r()
        c = QRectF(self.corr.x() / r, self.corr.y() / r, self.corr.width() / r, self.corr.height() / r)
        p.drawPixmap(c, self.pm, QRectF(self.corr))
        raw = QRectF(self.raw.x() / r, self.raw.y() / r, self.raw.width() / r, self.raw.height() / r)
        p.setBrush(Qt.BrushStyle.NoBrush)
        pen = QPen(QColor(255, 255, 255, 170), 1, Qt.PenStyle.DashLine)
        p.setPen(pen)
        p.drawRect(raw)
        p.setPen(QPen(QColor("#4ADE80"), 2))
        p.drawRect(c)
        p.setBrush(QColor("#4ADE80"))
        for pt in (c.topLeft(), c.topRight(), c.bottomLeft(), c.bottomRight()):
            p.drawEllipse(pt, 4, 4)
        d = (abs(self.corr.x() - self.raw.x()) + abs(self.corr.y() - self.raw.y())
             + abs(self.corr.right() - self.raw.right()) + abs(self.corr.bottom() - self.raw.bottom()))
        label = f"{self.corr.width()} × {self.corr.height()}" + (f"   {self.note}" if self.note else "") \
                + ("   ✓ düzeltildi" if d > 1 else "")
        ty = c.top() - 30 if c.top() > 36 else c.bottom() + 8
        box = QRectF(c.left(), ty, max(150, QFontMetrics(f).horizontalAdvance(label) + 20), 24)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor(20, 20, 20, 225))
        p.drawRoundedRect(box, 8, 8)
        p.setPen(QColor("#FFFFFF"))
        p.drawText(box, int(Qt.AlignmentFlag.AlignCenter.value), label)


class SnipWidget(PanelWidget):
    BASE, TICK, TITLE = (312, 118), 0, "Kırpma aracı"
    SETTINGS = [("int", "snap_px", "Düzeltme gücü (px) – kenara yapışma mesafesi", 0, 40),
                ("bool", "snap_ratio", "En-boy oranına yapış (1:1, 4:3, 16:9…)"),
                ("bool", "snap_screen", "Ekran kenarına yapış"),
                ("bool", "copy_clip", "Panoya kopyala"),
                ("bool", "save_file", "Resimler\\Kirpma klasörüne kaydet"),
                ("bool", "show_labels", "Düğme yazılarını göster (kapalı = yalnızca ikon)"),
                ("bool", "show_status", "Durum satırını göster")]
    MODES = [("region", "Kırp"), ("full", "Tam ekran"), ("delay", "3 sn sonra")]

    def init_state(self):
        self.hov = None
        self.status = "Hazır"
        self.busy = False
        self.overlays = []

    def base_size(self):
        n = len(self.MODES)
        lab = self.cfg["show_labels"]
        w = 32 + n * (88 if lab else 60) + (n - 1) * 8
        h = 28 + (76 if lab else 60) + (22 if self.cfg["show_status"] else 0)
        return w, h

    def cell(self, i):
        if self.cfg["show_labels"]:
            return QRectF(16 + i * 96, 14, 88, 76)
        return QRectF(16 + i * 68, 14, 60, 60)

    def hit(self, pt):
        for i, (k, _l) in enumerate(self.MODES):
            if self.cell(i).contains(pt):
                return k
        return None

    def on_hover(self, pt):
        h = self.hit(self.lp(pt))
        if h != self.hov:
            self.hov = h
            self.setToolTip(dict(self.MODES).get(h, ""))
            self.update()

    def on_leave(self):
        self.hov = None
        self.update()

    def on_click(self, pt):
        k = self.hit(self.lp(pt))
        if not k or self.busy:
            return
        if k == "delay":
            self.status = "3 saniye sonra…"
            self.update()
            QTimer.singleShot(3000, lambda: self.begin("region"))
        else:
            self.begin(k)

    def slot_menu(self, m, pt):
        add_act(m, "Alan kırp", lambda: self.begin("region"))
        add_act(m, "Tam ekran al", lambda: self.begin("full"))
        add_act(m, "Kayıt klasörünü aç", self.open_folder)
        m.addSeparator()

    def folder(self):
        return os.path.join(os.path.expanduser("~"), "Pictures", "Kirpma")

    def open_folder(self):
        os.makedirs(self.folder(), exist_ok=True)
        try:
            os.startfile(self.folder()) if IS_WIN else subprocess.Popen(["xdg-open", self.folder()])
        except Exception:
            pass

    def begin(self, mode):
        if self.busy:
            return
        self.busy = True
        hidden = [w for w in self.mgr.widgets if w.isVisible()]
        for w in hidden:
            w.hide()
        faded = []
        for t in QApplication.topLevelWidgets():
            if isinstance(t, QDialog) and t.isVisible():
                faded.append((t, t.windowOpacity()))
                t.setWindowOpacity(0.0)

        def restore():
            for o in self.overlays:
                o.hide()
                o.deleteLater()
            self.overlays = []
            for w in hidden:
                w.show()
                w.pin_tick()
            for t, op in faded:
                t.setWindowOpacity(op)
            self.busy = False

        def finish(pm):
            if self.overlays or mode == "full":
                restore()
            if pm is None or pm.isNull():
                self.status = "İptal edildi"
            else:
                msg = []
                if self.cfg["copy_clip"]:
                    QApplication.clipboard().setPixmap(pm)
                    msg.append("panoya kopyalandı")
                if self.cfg["save_file"]:
                    os.makedirs(self.folder(), exist_ok=True)
                    path = os.path.join(self.folder(), f"kirpma_{datetime.now():%Y%m%d_%H%M%S}.png")
                    if pm.save(path):
                        msg.append("kaydedildi")
                self.status = f"Son: {pm.width()}×{pm.height()} • " + (", ".join(msg) or "alındı")
                self.mgr.notify(f"Ekran görüntüsü {pm.width()}×{pm.height()} – " + (", ".join(msg) or "alındı"))
            self.update()

        def grab():
            opts = {k: self.cfg[k] for k in ("snap_px", "snap_ratio", "snap_screen")}
            shots = [(sc, sc.grabWindow(0)) for sc in QApplication.screens()]
            if mode == "full":
                scr = self.app.primaryScreen() if hasattr(self, "app") else QApplication.primaryScreen()
                pm = next((pm for sc, pm in shots if sc == scr), shots[0][1])
                restore()
                finish(pm)
                return
            done_flag = {"d": False}

            def once(pm):
                if not done_flag["d"]:
                    done_flag["d"] = True
                    finish(pm)
            for sc, pm in shots:
                ov = SnipOverlay(sc, pm, opts, once)
                self.overlays.append(ov)
                ov.show()
            self.overlays[0].activateWindow()
            self.overlays[0].setFocus()

        QTimer.singleShot(300, grab)

    def draw(self, p, W, H):
        for i, (k, label) in enumerate(self.MODES):
            r = self.cell(i)
            hot = self.hov == k
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(self.acc(0.30 if hot else 0.10))
            p.drawRoundedRect(r, 14, 14)
            cx = r.center().x()
            cy = r.y() + (28 if self.cfg['show_labels'] else 30)
            col = QColor("#FFFFFF") if hot else self.acc()
            p.setPen(QPen(col, 3, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.setBrush(Qt.BrushStyle.NoBrush)
            if k == "region":      # kırpma işareti
                p.drawPolyline(QPolygonF([QPointF(cx - 6, cy - 14), QPointF(cx - 6, cy + 6), QPointF(cx + 14, cy + 6)]))
                p.drawPolyline(QPolygonF([QPointF(cx + 6, cy + 14), QPointF(cx + 6, cy - 6), QPointF(cx - 14, cy - 6)]))
            elif k == "full":      # tam ekran köşe işaretleri
                for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    p.drawPolyline(QPolygonF([QPointF(cx + sx * 14, cy + sy * 6), QPointF(cx + sx * 14, cy + sy * 13),
                                              QPointF(cx + sx * 7, cy + sy * 13)]))
            else:                  # gecikmeli: saat
                p.drawEllipse(QPointF(cx, cy), 13, 13)
                p.drawLine(QPointF(cx, cy), QPointF(cx, cy - 8))
                p.drawLine(QPointF(cx, cy), QPointF(cx + 6, cy + 3))
            if self.cfg["show_labels"]:
                self.T(p, r.x(), r.y() + 50, r.width(), 20, label, 12, self.txt(0.95 if hot else 0.75), hot)
        if self.cfg["show_status"]:
            self.T(p, 16, H - 26, W - 32, 20, self.status, 12, self.txt(0.55), False, ALIGN_L)


# ======================================================================
# Duvar kağıdı efektleri (kar, yağmur, yıldız, ateşböceği, matrix, sakura,
# kutup ışığı) + renk filtresi, vinyet, gün döngüsü
# ======================================================================
FX_EFFECTS = [("none", "Yok (yalnızca renk filtresi / vinyet)"), ("snow", "Kar"), ("rain", "Yağmur"),
              ("stars", "Yıldızlı gece + kayan yıldız"), ("fireflies", "Ateşböcekleri"),
              ("matrix", "Matrix yağmuru"), ("petals", "Sakura yaprakları"), ("aurora", "Kutup ışığı")]
FX_PRESETS = {
    "Kış gecesi": {"effect": "snow", "color": "#FFFFFF", "amount": 140, "speed": 100,
                   "tint_color": "#0B1A3A", "tint_alpha": 28, "vignette": 40, "auto_tone": False},
    "Yağmurlu gün": {"effect": "rain", "color": "#BFD8FF", "amount": 220, "speed": 100,
                     "tint_color": "#203040", "tint_alpha": 22, "vignette": 35, "auto_tone": False},
    "Matrix": {"effect": "matrix", "color": "#39FF14", "amount": 45, "speed": 100,
               "tint_color": "#001A00", "tint_alpha": 35, "vignette": 55, "auto_tone": False},
    "Sakura": {"effect": "petals", "color": "#FFB7D5", "amount": 60, "speed": 90,
               "tint_color": "#FFC0DD", "tint_alpha": 8, "vignette": 20, "auto_tone": False},
    "Yıldızlı gece": {"effect": "stars", "color": "#FFFFFF", "amount": 180, "speed": 100,
                      "tint_color": "#050A24", "tint_alpha": 30, "vignette": 50, "auto_tone": False},
    "Ateşböcekleri": {"effect": "fireflies", "color": "#FFE066", "amount": 40, "speed": 100,
                      "tint_color": "#06140A", "tint_alpha": 30, "vignette": 45, "auto_tone": False},
    "Kutup ışığı": {"effect": "aurora", "color": "#3DFFB0", "amount": 75, "speed": 100,
                    "tint_color": "#050A1E", "tint_alpha": 35, "vignette": 40, "auto_tone": False},
    "Gün döngüsü": {"effect": "none", "tint_alpha": 0, "vignette": 25, "auto_tone": True},
}
MATRIX_CH = "アイウエオカキクケコサシスセソタチツテトナニヌネノ0123456789ABCDEFZ"
MATRIX_CS = 18
TONE_KEYS = [(0, (10, 20, 60), 34), (5, (10, 20, 60), 30), (7, (255, 150, 90), 14),
             (9, (255, 255, 255), 0), (16, (255, 255, 255), 0), (18, (255, 110, 60), 18),
             (20, (25, 25, 80), 28), (24, (10, 20, 60), 34)]


def tone_now():
    """Günün saatine göre (renk, opaklık%) — gece mavi, gün doğumu/batımı turuncu."""
    n = datetime.now()
    h = n.hour + n.minute / 60
    for i in range(len(TONE_KEYS) - 1):
        h0, c0, a0 = TONE_KEYS[i]
        h1, c1, a1 = TONE_KEYS[i + 1]
        if h0 <= h <= h1:
            f = (h - h0) / (h1 - h0)
            return tuple(int(c0[j] + (c1[j] - c0[j]) * f) for j in range(3)), a0 + (a1 - a0) * f
    return (255, 255, 255), 0


class FxWidget(BaseWidget):
    """Tüm ekranı kaplayan, tıklamayı geçiren efekt katmanı."""

    def make_dialog(self):
        return FxDialog(self)

    def __init__(self, mgr, cfg):
        super().__init__(mgr, cfg)
        self.parts, self.cols = [], []
        self.sig = None
        self.meteor = None
        self.next_meteor = 0.0
        self.t = 0.0
        self.last = time.monotonic()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.tick)
        self.timer.start(33)
        self.start()

    # ---- pencere davranışı
    def apply_flags(self):
        self.cfg["click_through"] = True      # asla tıklamayı engellemesin
        super().apply_flags()

    def pin_tick(self):
        super().pin_tick()
        try:
            self.lower()
        except Exception:
            pass

    def content_size(self):
        return max(1, self.width()), max(1, self.height())

    def relayout(self):
        scr = QApplication.screens()
        i = max(0, min(int(self.cfg["monitor"]), len(scr) - 1))
        g = scr[i].geometry()
        self.setGeometry(g)
        self.cfg["x"], self.cfg["y"] = g.x(), g.y()
        eff = self.cfg["effect"]
        iv = 1000 if eff == "none" else max(16, int(1000 / max(5, int(self.cfg["fps"]))))
        self.timer.setInterval(iv)
        self.build_if_needed()
        self.update()

    # ---- parçacıklar
    def build_if_needed(self):
        sig = (self.cfg["effect"], int(self.cfg["amount"]), int(self.cfg["monitor"]),
               self.width(), self.height())
        if sig == self.sig:
            return
        self.sig = sig
        self.parts, self.cols, self.meteor = [], [], None
        W, H = max(1, self.width()), max(1, self.height())
        n, rnd, eff = int(self.cfg["amount"]), random.random, self.cfg["effect"]
        if eff == "snow":
            for _ in range(n):
                r = random.uniform(1.4, 4.2)
                self.parts.append([rnd() * W, rnd() * H, 0, random.uniform(25, 60) * (0.6 + r / 4),
                                   r, rnd() * 6.28, random.uniform(10, 30)])
        elif eff == "petals":
            for _ in range(n):
                self.parts.append([rnd() * W, rnd() * H, rnd() * 360, random.uniform(30, 70),
                                   random.uniform(5, 10), rnd() * 6.28, random.uniform(25, 60)])
        elif eff == "rain":
            for _ in range(n):
                self.parts.append([rnd() * (W + 300), rnd() * H, -120, random.uniform(650, 950),
                                   random.uniform(10, 22), 0, 0])
        elif eff == "stars":
            for _ in range(n):
                self.parts.append([rnd() * W, rnd() * H, 0, 0, random.uniform(0.6, 2.0),
                                   rnd() * 6.28, random.uniform(0.8, 2.6)])
            self.next_meteor = self.t + random.uniform(2, 6)
        elif eff == "fireflies":
            for _ in range(n):
                self.parts.append([rnd() * W, rnd() * H, 0, random.uniform(18, 42),
                                   random.uniform(2, 4), rnd() * 6.28, rnd() * 6.28])
        elif eff == "matrix":
            for _ in range(max(5, n)):
                ln = random.randint(8, 22)
                self.cols.append([rnd() * W, -rnd() * H, random.uniform(140, 340), ln,
                                  [random.choice(MATRIX_CH) for _ in range(24)]])

    def mouse_local(self):
        if not self.cfg["mouse_react"]:
            return None
        lp = self.mapFromGlobal(QCursor.pos())
        return lp.x(), lp.y()

    def tick(self):
        if not self.isVisible():
            return
        now = time.monotonic()
        dt = min(0.1, now - self.last)
        self.last = now
        self.t += dt
        self.build_if_needed()
        self.step(dt)
        self.update()

    def step(self, dt):
        eff, sp = self.cfg["effect"], self.cfg["speed"] / 100
        W, H, t = self.width(), self.height(), self.t
        if eff in ("snow", "petals", "fireflies"):
            m = self.mouse_local()
            for pt in self.parts:
                if eff == "fireflies":
                    pt[6] += random.uniform(-3, 3) * dt
                    pt[0] += math.cos(pt[6]) * pt[3] * dt * sp
                    pt[1] += math.sin(pt[6]) * pt[3] * dt * sp
                else:
                    pt[1] += pt[3] * dt * sp
                    pt[0] += math.sin(t * 0.9 + pt[5]) * pt[6] * dt * sp
                if m:
                    dx, dy = pt[0] - m[0], pt[1] - m[1]
                    d2 = dx * dx + dy * dy
                    if d2 < 14400:
                        d = math.sqrt(d2) + 0.1
                        f = (120 - d) / 120 * 260 * dt
                        pt[0] += dx / d * f
                        pt[1] += dy / d * f
                if eff == "fireflies":
                    pt[0] = pt[0] % W
                    pt[1] = pt[1] % H
                else:
                    if pt[1] > H + 12:
                        pt[1], pt[0] = -12, random.random() * W
                    if pt[0] < -20:
                        pt[0] = W + 10
                    elif pt[0] > W + 20:
                        pt[0] = -10
        elif eff == "rain":
            for pt in self.parts:
                pt[0] += pt[2] * dt * sp
                pt[1] += pt[3] * dt * sp
                if pt[1] > H + 30:
                    pt[1] = -30 - random.random() * 100
                    pt[0] = random.random() * (W + 300)
        elif eff == "stars":
            if self.meteor:
                m = self.meteor
                m[0] += m[2] * dt
                m[1] += m[3] * dt
                m[4] -= dt
                if m[4] <= 0:
                    self.meteor = None
            elif t > self.next_meteor:
                ang = math.radians(random.uniform(20, 40))
                v = random.uniform(900, 1300)
                self.meteor = [random.uniform(0.2 * W, W), random.uniform(0, 0.4 * H),
                               -math.cos(ang) * v, math.sin(ang) * v, 0.8]
                self.next_meteor = t + random.uniform(5, 12)
        elif eff == "matrix":
            for c in self.cols:
                c[1] += c[2] * dt * sp
                if c[1] - c[3] * MATRIX_CS > H:
                    c[1] = -random.random() * H * 0.4
                    c[2] = random.uniform(140, 340)
                if random.random() < 0.25:
                    c[4][random.randrange(len(c[4]))] = random.choice(MATRIX_CH)

    # ---- çizim
    def paint_content(self, p):
        W, H, t = self.width(), self.height(), self.t
        rect = QRectF(0, 0, W, H)
        # 1) renk filtresi (isteğe bağlı gün döngüsü)
        if self.cfg["auto_tone"]:
            rgb, a = tone_now()
            tc, ta = QColor(*rgb), a / 100
        else:
            tc, ta = QColor(self.cfg["tint_color"]), self.cfg["tint_alpha"] / 100
        if ta > 0:
            tc.setAlphaF(min(1.0, ta))
            p.fillRect(rect, tc)
        # 2) efekt
        eff = self.cfg["effect"]
        col = QColor(self.cfg["color"])
        p.setPen(Qt.PenStyle.NoPen)
        if eff == "snow":
            for pt in self.parts:
                col.setAlphaF(min(0.95, 0.3 + pt[4] * 0.14))
                p.setBrush(col)
                p.drawEllipse(QPointF(pt[0], pt[1]), pt[4], pt[4])
        elif eff == "petals":
            col.setAlphaF(0.78)
            p.setBrush(col)
            for pt in self.parts:
                s = pt[4]
                p.save()
                p.translate(pt[0], pt[1])
                p.rotate(pt[2] + t * 45 * (0.5 + pt[5] % 1))
                p.drawEllipse(QRectF(-s, -s * 0.5, s * 2, s))
                p.restore()
        elif eff == "rain":
            col.setAlphaF(0.38)
            p.setPen(QPen(col, 1.3))
            for pt in self.parts:
                k = pt[4] / pt[3]
                p.drawLine(QPointF(pt[0], pt[1]), QPointF(pt[0] - pt[2] * k, pt[1] - pt[4]))
            p.setPen(Qt.PenStyle.NoPen)
        elif eff == "stars":
            for pt in self.parts:
                col.setAlphaF(0.2 + 0.8 * (0.5 + 0.5 * math.sin(t * pt[6] + pt[5])))
                p.setBrush(col)
                p.drawEllipse(QPointF(pt[0], pt[1]), pt[4], pt[4])
            if self.meteor:
                m = self.meteor
                nrm = math.hypot(m[2], m[3])
                tail = QPointF(m[0] - m[2] / nrm * 190, m[1] - m[3] / nrm * 190)
                g = QLinearGradient(QPointF(m[0], m[1]), tail)
                c1, c2 = QColor(col), QColor(col)
                c1.setAlphaF(min(1.0, m[4] * 1.5))
                c2.setAlphaF(0.0)
                g.setColorAt(0, c1)
                g.setColorAt(1, c2)
                p.setPen(QPen(QBrush(g), 2.2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
                p.drawLine(QPointF(m[0], m[1]), tail)
                p.setPen(Qt.PenStyle.NoPen)
        elif eff == "fireflies":
            for pt in self.parts:
                pulse = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.6 + pt[5]))
                rad = pt[4] * 7
                g = QRadialGradient(QPointF(pt[0], pt[1]), rad)
                c1, c2 = QColor(col), QColor(col)
                c1.setAlphaF(0.85 * pulse)
                c2.setAlphaF(0.0)
                g.setColorAt(0, c1)
                g.setColorAt(1, c2)
                p.setBrush(QBrush(g))
                p.drawEllipse(QPointF(pt[0], pt[1]), rad, rad)
        elif eff == "matrix":
            f = QFont("Consolas")
            f.setPixelSize(MATRIX_CS)
            p.setFont(f)
            c2 = QColor(col)
            for c in self.cols:
                for k in range(c[3]):
                    y = c[1] - k * MATRIX_CS
                    if y < -MATRIX_CS or y > H + MATRIX_CS:
                        continue
                    if k == 0:
                        p.setPen(QColor(235, 255, 235, 240))
                    else:
                        c2.setAlphaF(max(0.04, (1 - k / c[3]) ** 1.6 * 0.85))
                        p.setPen(c2)
                    p.drawText(QPointF(c[0], y), c[4][k % len(c[4])])
            p.setPen(Qt.PenStyle.NoPen)
        elif eff == "aurora":
            bands = int(max(2, min(6, self.cfg["amount"] / 25)))
            hue = col.hue() if col.hue() >= 0 else 150
            sp = self.cfg["speed"] / 100
            for i in range(bands):
                c = QColor.fromHsv((hue + i * 35) % 360, 170, 255)
                y0, amp, thick = H * (0.10 + 0.07 * i), H * 0.06, H * 0.22
                top, bot = [], []
                for x in range(0, W + 30, 30):
                    y = (y0 + amp * math.sin(x * 0.003 * (1 + i * 0.3) + t * 0.35 * sp + i * 1.7)
                         + amp * 0.5 * math.sin(x * 0.007 + t * 0.2 * sp + i))
                    top.append(QPointF(x, y))
                    bot.append(QPointF(x, y + thick * (0.8 + 0.2 * math.sin(x * 0.005 + t * 0.3 * sp + i))))
                path = QPainterPath()
                path.moveTo(top[0])
                for q in top[1:]:
                    path.lineTo(q)
                for q in reversed(bot):
                    path.lineTo(q)
                path.closeSubpath()
                g = QLinearGradient(0, y0 - amp, 0, y0 + thick + amp)
                c0, c1 = QColor(c), QColor(c)
                c0.setAlphaF(0.0)
                c1.setAlphaF(0.30)
                g.setColorAt(0.0, c0)
                g.setColorAt(0.3, c1)
                g.setColorAt(1.0, c0)
                p.setBrush(QBrush(g))
                p.drawPath(path)
        # 3) vinyet (kenar karartma)
        v = self.cfg["vignette"]
        if v > 0:
            g = QRadialGradient(QPointF(W / 2, H / 2), math.hypot(W, H) / 2)
            g.setColorAt(0.55, QColor(0, 0, 0, 0))
            g.setColorAt(1.0, QColor(0, 0, 0, int(255 * v / 100 * 0.9)))
            p.fillRect(rect, QBrush(g))


# ======================================================================
# Program seçici
# ======================================================================
class AppPicker(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Uygulama seç")
        self.resize(460, 580)
        self.result_slots = []
        self.thread = None

        lay = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Ara…")
        self.search.textChanged.connect(self.apply_filter)
        lay.addWidget(self.search)

        self.list = QListWidget()
        self.list.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.list.setIconSize(QSize(28, 28))
        self.list.itemDoubleClicked.connect(lambda _i: self.accept_selected())
        lay.addWidget(self.list, 1)

        self.info = QLabel("")
        self.info.setStyleSheet("color: gray")
        lay.addWidget(self.info)

        bl = QHBoxLayout()
        b_file = QPushButton("Dosya seç…")
        b_file.clicked.connect(self.pick_file)
        b_ref = QPushButton("Yenile")
        b_ref.clicked.connect(self.rescan)
        b_ok = QPushButton("Ekle")
        b_ok.setDefault(True)
        b_ok.clicked.connect(self.accept_selected)
        b_cancel = QPushButton("İptal")
        b_cancel.clicked.connect(self.reject)
        for b in (b_file, b_ref):
            bl.addWidget(b)
        bl.addStretch(1)
        bl.addWidget(b_ok)
        bl.addWidget(b_cancel)
        lay.addLayout(bl)

        if APP_CACHE is None:
            self.rescan()
        else:
            self.fill(APP_CACHE)

    def rescan(self):
        self.info.setText("Programlar taranıyor…")
        self.list.clear()
        t = ScanThread()
        _KEEP_THREADS.append(t)
        t.done.connect(_store_cache)
        t.done.connect(self.fill)
        t.finished.connect(lambda t=t: _KEEP_THREADS.remove(t) if t in _KEEP_THREADS else None)
        self.thread = t
        t.start()

    def fill(self, apps):
        self.list.clear()
        for a in apps:
            it = QListWidgetItem(icon_for_slot(a), a["name"])
            it.setData(Qt.ItemDataRole.UserRole, a)
            self.list.addItem(it)
        self.info.setText(f"{len(apps)} program bulundu (Başlat menüsü / shell:Programs). "
                          "Ctrl/Shift ile birden fazla seçebilirsin.")
        self.apply_filter(self.search.text())

    def apply_filter(self, text):
        t = text.casefold()
        for i in range(self.list.count()):
            it = self.list.item(i)
            it.setHidden(t not in it.text().casefold())

    def accept_selected(self):
        items = self.list.selectedItems()
        if not items:
            return
        self.result_slots = [dict(it.data(Qt.ItemDataRole.UserRole)) for it in items]
        self.accept()

    def pick_file(self):
        files, _ = QFileDialog.getOpenFileNames(self, "Dosya veya uygulama seç")
        if not files:
            return
        self.result_slots = [
            {"name": os.path.splitext(os.path.basename(f))[0] or f, "path": f, "kind": "file"}
            for f in files]
        self.accept()


# ======================================================================
# Ayar pencereleri
# ======================================================================
class CommonGroup(QWidget):
    """Tüm widget türleri için ortak: konum, katman, şeffaflık, kilit..."""

    def __init__(self, w):
        super().__init__()
        self.w = w
        self._upd = False
        f = QFormLayout(self)
        self.s_op = row_slider(f, "Genel şeffaflık (%)", 5, 100, self.on_opacity)

        pl = QHBoxLayout()
        self.sp_x, self.sp_y = QSpinBox(), QSpinBox()
        for sp in (self.sp_x, self.sp_y):
            sp.setRange(-10000, 20000)
            sp.valueChanged.connect(self.on_pos)
            pl.addWidget(sp)
        bc = QPushButton("Ortala")
        bc.clicked.connect(self.center)
        pl.addWidget(bc)
        f.addRow("Konum X / Y", pl)

        self.zpos = QComboBox()
        for _k, label in ZPOS:
            self.zpos.addItem(label)
        self.zpos.currentIndexChanged.connect(
            lambda i: None if self._upd else self.w.set_flag("zpos", ZPOS[i][0]))
        f.addRow("Katman", self.zpos)

        self.chk = {}
        for key, label in (("locked", "Konumu kilitle"),
                           ("click_through", "Tıklamayı geçir (sonra tepsiden kapat)"),
                           ("snap", "Ekran kenarlarına yapış")):
            c = QCheckBox(label)
            c.toggled.connect(lambda v, k=key: None if self._upd else self.w.set_flag(k, bool(v)))
            f.addRow(c)
            self.chk[key] = c

    def sync(self):
        self._upd = True
        c = self.w.cfg
        self.s_op.setValue(c["global_opacity"])
        self.sp_x.setValue(int(c["x"]))
        self.sp_y.setValue(int(c["y"]))
        keys = [k for k, _ in ZPOS]
        self.zpos.setCurrentIndex(keys.index(c["zpos"]) if c["zpos"] in keys else 0)
        for k, box in self.chk.items():
            box.setChecked(bool(c[k]))
        self._upd = False

    def sync_position(self):
        self._upd = True
        self.sp_x.setValue(int(self.w.cfg["x"]))
        self.sp_y.setValue(int(self.w.cfg["y"]))
        self._upd = False

    def on_opacity(self, v):
        if self._upd:
            return
        self.w.cfg["global_opacity"] = int(v)
        self.w.update()
        self.w.mgr.schedule_save()

    def on_pos(self, _v):
        if self._upd:
            return
        self.w.cfg["x"], self.w.cfg["y"] = self.sp_x.value(), self.sp_y.value()
        self.w.changed()

    def center(self):
        W, H = self.w.content_size()
        g = self.w.app.primaryScreen().availableGeometry()
        self.w.cfg["x"] = g.left() + (g.width() - W) // 2
        self.w.cfg["y"] = g.top() + (g.height() - H) // 2
        self.w.changed()
        self.sync_position()


class WidgetDialog(QDialog):
    def __init__(self, w, title):
        super().__init__()
        self.w = w
        self._upd = False
        self.swatches = {}
        self.setWindowTitle(title)
        self.root = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.root.addWidget(self.tabs)

    def add_tab(self, title):
        page = QWidget()
        form = QFormLayout(page)
        self.tabs.addTab(page, title)
        return form

    def finish(self):
        self.common = CommonGroup(self.w)
        self.tabs.addTab(self.common, "Konum ve davranış")
        bl = QHBoxLayout()
        b_save = QPushButton("Kaydet")
        b_save.clicked.connect(self.w.mgr.save_now)
        b_reset = QPushButton("Varsayılana dön")
        b_reset.clicked.connect(self.w.reset_defaults)
        b_del = QPushButton("Widget'ı kaldır")
        b_del.clicked.connect(lambda: self.w.mgr.remove_widget(self.w))
        b_close = QPushButton("Kapat")
        b_close.clicked.connect(self.close)
        bl.addWidget(b_save)
        bl.addWidget(b_reset)
        bl.addWidget(b_del)
        bl.addStretch(1)
        bl.addWidget(b_close)
        self.root.addLayout(bl)
        self.status = QLabel(STORE_PATH)
        self.status.setStyleSheet("color: gray")
        self.root.addWidget(self.status)
        self.sync()

    def color_row(self, form, label, key):
        sw = QLabel()
        sw.setFixedSize(46, 24)
        btn = QPushButton("Renk seç…")
        lay = QHBoxLayout()
        lay.addWidget(sw)
        lay.addWidget(btn)
        lay.addStretch(1)
        form.addRow(label, lay)
        btn.clicked.connect(lambda: self.pick_key_color(key))
        self.swatches[key] = sw

    def pick_key_color(self, key):
        col = choose_color(self, QColor(self.w.cfg[key]), "Renk seç")
        if col.isValid():
            self.w.cfg[key] = col.name()
            self.w.changed()
            self.sync()

    def sync(self, *_):
        self._upd = True
        self.sync_specific()
        for key, sw in self.swatches.items():
            sw.setStyleSheet(f"background:{self.w.cfg[key]}; border:1px solid #888")
        self._upd = False
        if hasattr(self, "common"):
            self.common.sync()

    def sync_specific(self):
        pass

    def closeEvent(self, e):
        self.w.dialog = None
        super().closeEvent(e)


class ClockDialog(WidgetDialog):
    def __init__(self, w):
        super().__init__(w, "Saat ayarları")
        f1 = self.add_tab("Rakamlar")
        self.target = QComboBox()
        self.target.addItems(["Tümü"] + ITEM_NAMES)
        self.target.currentIndexChanged.connect(self.sync)
        f1.addRow("Uygulanacak yer", self.target)
        self.s_w = row_slider(f1, "Genişlik", 10, 300, lambda v: self.on_item("w", v))
        self.s_h = row_slider(f1, "Yükseklik", 40, 900, lambda v: self.on_item("h", v))
        self.s_t = row_slider(f1, "Kalınlık", 2, 100, lambda v: self.on_item("t", v))
        self.s_a = row_slider(f1, "Opaklık (%)", 5, 100, lambda v: self.on_item("alpha", v))
        self.item_swatch = QLabel()
        self.item_swatch.setFixedSize(46, 24)
        b = QPushButton("Renk seç…")
        b.clicked.connect(self.pick_item_color)
        cl = QHBoxLayout()
        cl.addWidget(self.item_swatch)
        cl.addWidget(b)
        cl.addStretch(1)
        f1.addRow("Renk", cl)

        f2 = self.add_tab("Görünüm")
        self.mode = QComboBox()
        self.mode.addItems(["Segment (dikdörtgen)", "Yazı tipi"])
        self.mode.currentIndexChanged.connect(self.on_mode)
        f2.addRow("Rakam stili", self.mode)
        self.font = QFontComboBox()
        self.font.currentFontChanged.connect(self.on_font)
        f2.addRow("Yazı tipi", self.font)
        self.s_gap = row_slider(f2, "Rakam boşluğu", 0, 150, lambda v: self.on_glob("gap", v))
        self.s_pad = row_slider(f2, "Kenar boşluğu", 0, 150, lambda v: self.on_glob("pad", v))
        self.chk = {}
        for key, label in (("use_24h", "24 saat biçimi"),
                           ("blink", "İki nokta yanıp sönsün"),
                           ("shadow", "Gölge")):
            c = QCheckBox(label)
            c.toggled.connect(lambda v, k=key: self.on_bool(k, v))
            f2.addRow(c)
            self.chk[key] = c
        self.color_row(f2, "Panel rengi", "panel_color")
        self.s_pa = row_slider(f2, "Panel opaklığı (%)", 0, 100, lambda v: self.on_glob("panel_alpha", v))
        self.s_rad = row_slider(f2, "Köşe yuvarlaklığı", 0, 80, lambda v: self.on_glob("radius", v))
        self.s_bd = row_slider(f2, "Kenarlık opaklığı (%)", 0, 100, lambda v: self.on_glob("border_alpha", v))
        self.finish()

    def indices(self):
        i = self.target.currentIndex()
        return list(range(5)) if i <= 0 else [i - 1]

    def sync_specific(self):
        c = self.w.cfg
        first = c["items"][self.indices()[0]]
        self.s_w.setValue(first["w"])
        self.s_h.setValue(first["h"])
        self.s_t.setValue(first["t"])
        self.s_a.setValue(first["alpha"])
        self.item_swatch.setStyleSheet(f"background:{first['color']}; border:1px solid #888")
        self.mode.setCurrentIndex(1 if c["mode"] == "font" else 0)
        self.font.setCurrentFont(QFont(c["font"]))
        self.font.setEnabled(c["mode"] == "font")
        self.s_t.setEnabled(c["mode"] != "font")
        self.s_gap.setValue(c["gap"])
        self.s_pad.setValue(c["pad"])
        self.s_pa.setValue(c["panel_alpha"])
        self.s_rad.setValue(c["radius"])
        self.s_bd.setValue(c["border_alpha"])
        for k, box in self.chk.items():
            box.setChecked(bool(c[k]))

    def on_item(self, key, v):
        if self._upd:
            return
        all_mode = self.target.currentIndex() <= 0
        for i in self.indices():
            if all_mode and i == COLON_IDX and key in ("w", "t"):
                continue  # "Tümü": iki noktanın genişlik/kalınlığı değişmez
            self.w.cfg["items"][i][key] = int(v)
        self.w.changed()

    def on_glob(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = int(v)
        self.w.changed()

    def on_bool(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = bool(v)
        self.w.changed()

    def on_mode(self, i):
        if self._upd:
            return
        self.w.cfg["mode"] = "font" if i == 1 else "segment"
        self.font.setEnabled(i == 1)
        self.s_t.setEnabled(i != 1)
        self.w.changed()

    def on_font(self, f):
        if self._upd:
            return
        self.w.cfg["font"] = f.family()
        self.w._glyph_cache.clear()
        self.w.changed()

    def pick_item_color(self):
        cur = QColor(self.w.cfg["items"][self.indices()[0]]["color"])
        col = choose_color(self, cur, "Rakam rengi")
        if not col.isValid():
            return
        for i in self.indices():
            self.w.cfg["items"][i]["color"] = col.name()
        self.w.changed()
        self.sync()


class BarDialog(WidgetDialog):
    def __init__(self, w):
        super().__init__(w, "Uygulama çubuğu ayarları")
        f1 = self.add_tab("Düzen")
        self.info = QLabel("")
        f1.addRow(self.info)
        self.sp_n = QSpinBox()
        self.sp_n.setRange(1, MAX_SLOTS)
        self.sp_n.valueChanged.connect(self.on_slots)
        f1.addRow("Slot sayısı", self.sp_n)
        self.sp_cols = QSpinBox()
        self.sp_cols.setRange(1, 12)
        self.sp_cols.valueChanged.connect(lambda v: self.on_int("cols", v))
        f1.addRow("Sütun sayısı", self.sp_cols)
        self.s_tile = row_slider(f1, "Kutu boyutu", 40, 220, lambda v: self.on_int("tile", v))
        self.s_icon = row_slider(f1, "İkon boyutu", 16, 160, lambda v: self.on_int("icon", v))
        self.s_gap = row_slider(f1, "Kutu boşluğu", 0, 60, lambda v: self.on_int("gap", v))
        self.s_pad = row_slider(f1, "Kenar boşluğu", 0, 80, lambda v: self.on_int("pad", v))
        self.c_lab = QCheckBox("İsimleri göster")
        self.c_lab.toggled.connect(lambda v: self.on_bool("show_labels", v))
        f1.addRow(self.c_lab)
        self.s_lsize = row_slider(f1, "Yazı boyutu", 6, 20, lambda v: self.on_int("label_size", v))
        b = QPushButton("Tüm slotları temizle")
        b.clicked.connect(self.w.clear_all)
        f1.addRow(b)

        f2 = self.add_tab("Renkler")
        self.color_row(f2, "Kutu rengi", "tile_color")
        self.s_ta = row_slider(f2, "Kutu opaklığı (%)", 0, 100, lambda v: self.on_int("tile_alpha", v))
        self.s_ha = row_slider(f2, "Üzerine gelince (%)", 0, 100, lambda v: self.on_int("hover_alpha", v))
        self.s_rad = row_slider(f2, "Köşe yuvarlaklığı", 0, 70, lambda v: self.on_int("radius", v))
        self.color_row(f2, "Panel rengi", "panel_color")
        self.s_pa = row_slider(f2, "Panel opaklığı (%)", 0, 100, lambda v: self.on_int("panel_alpha", v))
        self.color_row(f2, "Yazı / + rengi", "label_color")
        self.s_bd = row_slider(f2, "Kenarlık opaklığı (%)", 0, 100, lambda v: self.on_int("border_alpha", v))
        self.finish()

    def sync_specific(self):
        c = self.w.cfg
        self.info.setText(f"Bu çubukta {len(c['slots'])} slot var. "
                          f"Tüm çubuklarda toplam: {self.w.mgr.total_slots()} slot.")
        self.sp_n.setValue(c["n_slots"])
        self.sp_cols.setValue(c["cols"])
        self.s_tile.setValue(c["tile"])
        self.s_icon.setValue(c["icon"])
        self.s_gap.setValue(c["gap"])
        self.s_pad.setValue(c["pad"])
        self.c_lab.setChecked(bool(c["show_labels"]))
        self.s_lsize.setValue(c["label_size"])
        self.s_ta.setValue(c["tile_alpha"])
        self.s_ha.setValue(c["hover_alpha"])
        self.s_rad.setValue(c["radius"])
        self.s_pa.setValue(c["panel_alpha"])
        self.s_bd.setValue(c["border_alpha"])

    def on_int(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = int(v)
        self.w.changed()

    def on_bool(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = bool(v)
        self.w.changed()

    def on_slots(self, v):
        if self._upd:
            return
        self.w.set_slot_count(v)
        self.sync()


class FxDialog(WidgetDialog):
    def __init__(self, w):
        super().__init__(w, "Duvar kağıdı efekti ayarları")
        f = self.add_tab("Efekt")
        self.cb_preset = QComboBox()
        self.cb_preset.addItems(["Hazır ortam seç…"] + list(FX_PRESETS))
        self.cb_preset.activated.connect(self.apply_preset)
        f.addRow("Hazır ortam", self.cb_preset)
        self.cb_fx = QComboBox()
        for key, label in FX_EFFECTS:
            self.cb_fx.addItem(label, key)
        self.cb_fx.currentIndexChanged.connect(self.on_fx)
        f.addRow("Efekt", self.cb_fx)
        self.color_row(f, "Efekt rengi (damlalıkla duvar kağıdından al)", "color")
        self.s_amount = row_slider(f, "Miktar", 5, 400, lambda v: self.on_int("amount", v))
        self.s_speed = row_slider(f, "Hız (%)", 20, 300, lambda v: self.on_int("speed", v))
        self.s_fps = row_slider(f, "Kare hızı (düşük = daha az işlemci)", 10, 60, lambda v: self.on_int("fps", v))
        f2 = self.add_tab("Atmosfer")
        self.color_row(f2, "Renk filtresi rengi", "tint_color")
        self.s_tint = row_slider(f2, "Renk filtresi gücü (%)", 0, 70, lambda v: self.on_int("tint_alpha", v))
        self.s_vig = row_slider(f2, "Kenar karartma / vinyet (%)", 0, 90, lambda v: self.on_int("vignette", v))
        self.c_auto = QCheckBox("Gün döngüsü: gece mavi, gün doğumu/batımı turuncu (filtreyi otomatik değiştirir)")
        self.c_auto.toggled.connect(lambda v: self.on_bool("auto_tone", v))
        f2.addRow(self.c_auto)
        self.c_mouse = QCheckBox("Fare yaklaşınca parçacıklar kaçsın (kar, yaprak, ateşböceği)")
        self.c_mouse.toggled.connect(lambda v: self.on_bool("mouse_react", v))
        f2.addRow(self.c_mouse)
        self.s_mon = row_slider(f2, "Monitör (0 = ana ekran)", 0, 5, lambda v: self.on_int("monitor", v))
        self.finish()

    def sync_specific(self):
        c = self.w.cfg
        self.cb_fx.setCurrentIndex(max(0, self.cb_fx.findData(c["effect"])))
        self.s_amount.setValue(int(c["amount"]))
        self.s_speed.setValue(int(c["speed"]))
        self.s_fps.setValue(int(c["fps"]))
        self.s_tint.setValue(int(c["tint_alpha"]))
        self.s_vig.setValue(int(c["vignette"]))
        self.c_auto.setChecked(bool(c["auto_tone"]))
        self.c_mouse.setChecked(bool(c["mouse_react"]))
        self.s_mon.setValue(int(c["monitor"]))

    def on_fx(self, _i):
        if self._upd:
            return
        self.w.cfg["effect"] = self.cb_fx.currentData()
        self.w.changed()

    def on_int(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = int(v)
        self.w.changed()

    def on_bool(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = bool(v)
        self.w.changed()

    def apply_preset(self, i):
        if i <= 0:
            return
        self.w.cfg.update(FX_PRESETS[self.cb_preset.itemText(i)])
        self.w.changed()
        self.sync()
        self.cb_preset.setCurrentIndex(0)


class PanelDialog(WidgetDialog):
    def __init__(self, w):
        super().__init__(w, w.TITLE + " ayarları")
        f = self.add_tab("Görünüm")
        self.s_scale = row_slider(f, "Boyut (%)", 40, 400, lambda v: self.on_int("scale", v))
        self.color_row(f, "Vurgu rengi", "accent")
        self.color_row(f, "Yazı rengi", "text")
        self.color_row(f, "Panel rengi", "panel_color")
        self.s_pa = row_slider(f, "Panel opaklığı (%)", 0, 100, lambda v: self.on_int("panel_alpha", v))
        self.s_rad = row_slider(f, "Köşe yuvarlaklığı", 0, 60, lambda v: self.on_int("radius", v))
        self.s_bd = row_slider(f, "Kenarlık opaklığı (%)", 0, 100, lambda v: self.on_int("border_alpha", v))
        self.ctrl = {}
        if w.SETTINGS:
            f2 = self.add_tab("İçerik")
            for spec in w.SETTINGS:
                if spec[0] == "int":
                    _k, key, label, lo, hi = spec
                    self.ctrl[key] = row_slider(f2, label, lo, hi,
                                                lambda v, key=key: self.on_int(key, v))
                else:
                    _k, key, label = spec
                    c = QCheckBox(label)
                    c.toggled.connect(lambda v, key=key: self.on_bool(key, v))
                    f2.addRow(c)
                    self.ctrl[key] = c
        self.finish()

    def sync_specific(self):
        c = self.w.cfg
        self.s_scale.setValue(c["scale"])
        self.s_pa.setValue(c["panel_alpha"])
        self.s_rad.setValue(c["radius"])
        self.s_bd.setValue(c["border_alpha"])
        for key, wd in self.ctrl.items():
            if isinstance(wd, QCheckBox):
                wd.setChecked(bool(c[key]))
            else:
                wd.setValue(int(c[key]))

    def on_int(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = int(v)
        self.w.changed()

    def on_bool(self, key, v):
        if self._upd:
            return
        self.w.cfg[key] = bool(v)
        self.w.changed()


class ThemeDialog(QDialog):
    """Tüm widget'lara tek yerden ortak görünüm uygular (canlı)."""

    def __init__(self, mgr):
        super().__init__()
        self.mgr = mgr
        self._upd = False
        self.setWindowTitle("Ortak tema")
        lay = QVBoxLayout(self)
        form = QFormLayout()
        lay.addLayout(form)
        pl = QHBoxLayout()
        for name in PRESETS:
            b = QPushButton(name)
            b.clicked.connect(lambda _c=False, n=name: self.preset(n))
            pl.addWidget(b)
        form.addRow("Hazır temalar", pl)
        self.sw = {}
        for key, label in (("accent", "Vurgu (rakam) rengi"),
                           ("text", "Yazı / kutu rengi"),
                           ("glass", "Cam panel rengi")):
            sw = QLabel()
            sw.setFixedSize(46, 24)
            btn = QPushButton("Renk seç…")
            btn.clicked.connect(lambda _c=False, k=key: self.pick(k))
            hl = QHBoxLayout()
            hl.addWidget(sw)
            hl.addWidget(btn)
            hl.addStretch(1)
            form.addRow(label, hl)
            self.sw[key] = sw
        self.sl = {}
        for key, label, lo, hi in (("glass_alpha", "Panel opaklığı (%)", 0, 100),
                                   ("border_alpha", "Kenarlık opaklığı (%)", 0, 100),
                                   ("radius", "Köşe yuvarlaklığı", 0, 60),
                                   ("gap", "Widget arası boşluk (yapışma)", 0, 40)):
            self.sl[key] = row_slider(form, label, lo, hi, lambda v, k=key: self.on_val(k, v))
        bl = QHBoxLayout()
        bl.addStretch(1)
        bc = QPushButton("Kapat")
        bc.clicked.connect(self.close)
        bl.addWidget(bc)
        lay.addLayout(bl)
        self.sync()

    def sync(self):
        self._upd = True
        th = self.mgr.theme
        for k, sw in self.sw.items():
            sw.setStyleSheet(f"background:{th[k]}; border:1px solid #888")
        for k, sl in self.sl.items():
            sl.setValue(int(th[k]))
        self._upd = False

    def on_val(self, k, v):
        if self._upd:
            return
        self.mgr.theme[k] = int(v)
        self.mgr.apply_theme()

    def pick(self, k):
        col = choose_color(self, QColor(self.mgr.theme[k]), "Renk seç")
        if col.isValid():
            self.mgr.theme[k] = col.name()
            self.sync()
            self.mgr.apply_theme()

    def preset(self, name):
        self.mgr.theme.update(PRESETS[name])
        self.sync()
        self.mgr.apply_theme()

    def closeEvent(self, e):
        self.mgr.theme_dlg = None
        super().closeEvent(e)


# ======================================================================
# Yönetici (tepsi, kaydetme, ekleme/silme)
# ======================================================================
WIDGET_CLASSES = {"clock": ClockWidget, "appbar": AppBarWidget,
                  "calendar": CalendarWidget, "sysmon": SysMonWidget,
                  "notes": NotesWidget, "analog": AnalogWidget, "timer": TimerWidget,
                  "battery": BatteryWidget, "search": SearchWidget,
                  "stopwatch": StopwatchWidget, "countdown": CountdownWidget,
                  "datecard": DateCardWidget, "media": MediaWidget,
                  "todo": TodoWidget, "netspeed": NetSpeedWidget, "recycle": RecycleWidget,
                  "clipboard": ClipboardWidget, "audioviz": AudioVizWidget, "power": PowerWidget,
                  "snip": SnipWidget, "wallfx": FxWidget}


class Manager:
    def __init__(self, app):
        self.app = app
        self.widgets = []
        self.pinner = None
        if IS_WIN:
            try:
                self.pinner = WinDesktopPinner()
            except Exception:
                self.pinner = None
        self._mtime = self.file_mtime()
        self.theme = load_theme()
        self.theme_dlg = None
        global MANAGER
        MANAGER = self

        self.save_timer = QTimer(singleShot=True, interval=400)
        self.save_timer.timeout.connect(self.save_now)
        self.pin_timer = QTimer(interval=1000)
        self.pin_timer.timeout.connect(self.pin_tick)
        self.pin_timer.start()
        self.reload_timer = QTimer(interval=1500)
        self.reload_timer.timeout.connect(self.check_reload)
        self.reload_timer.start()

        self.tray = None
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray = QSystemTrayIcon(make_tray_icon())
            self.tray.setToolTip("Widget Studio")
            self.tray_menu = QMenu()
            self.tray_menu.aboutToShow.connect(lambda: self.fill_menu(self.tray_menu))
            self.tray.setContextMenu(self.tray_menu)
            self.tray.show()

        for cfg in load_store():
            self.create(cfg)
        if not self.widgets:
            self.add_widget("clock")

    # ---- widget yaşam döngüsü
    def create(self, cfg):
        w = WIDGET_CLASSES[cfg["type"]](self, cfg)
        self.widgets.append(w)
        return w

    def add_widget(self, typ, near=None):
        cfg = DEFAULTS[typ]()
        style_cfg(cfg, self.theme)
        g = self.app.primaryScreen().availableGeometry()
        if near is not None:
            cfg["x"], cfg["y"] = near.x(), near.y() + near.height() + 20
            if cfg["y"] > g.bottom() - 120:  # altına sığmıyorsa yanına koy
                cfg["x"], cfg["y"] = near.x() + near.width() + 20, near.y()
        else:
            n = len(self.widgets)
            cfg["x"], cfg["y"] = g.left() + 120 + 30 * n, g.top() + 120 + 30 * n
        w = self.create(cfg)
        self.schedule_save()
        self.update_info()
        if typ == "appbar":
            self.notify("Yeni uygulama çubuğu eklendi: boş (+) slota tıklayarak program ekle. "
                        f"Toplam slot: {self.total_slots()}")
        return w

    def remove_widget(self, w, save=True):
        if w not in self.widgets:
            return
        self.widgets.remove(w)
        if w.dialog:
            w.dialog.close()
        w.hide()
        w.deleteLater()
        if save:
            self.schedule_save()
        if not self.widgets and not QSystemTrayIcon.isSystemTrayAvailable():
            self.add_widget("clock")  # tepsi yoksa en az bir widget kalsın
        self.update_info()

    def total_slots(self):
        return sum(len(w.cfg["slots"]) for w in self.widgets if w.cfg["type"] == "appbar")

    def update_info(self):
        for w in self.widgets:
            if w.dialog and hasattr(w.dialog, "info"):
                w.dialog.sync()

    def notify(self, text):
        if self.tray:
            self.tray.showMessage("Widget Studio", text)
        else:
            print(text)

    # ---- kaydet / yeniden yükle
    def file_mtime(self):
        try:
            return os.path.getmtime(STORE_PATH)
        except OSError:
            return 0

    def schedule_save(self):
        self.save_timer.start()

    def save_now(self):
        try:
            tmp = STORE_PATH + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump({"version": 4, "theme": self.theme,
                           "widgets": [w.cfg for w in self.widgets]},
                          f, indent=2, ensure_ascii=False)
            os.replace(tmp, STORE_PATH)
            self._mtime = self.file_mtime()
            for w in self.widgets:
                if w.dialog:
                    w.dialog.status.setText("Kaydedildi ✓")
        except OSError as err:
            for w in self.widgets:
                if w.dialog:
                    w.dialog.status.setText(f"Kaydedilemedi: {err}")

    def check_reload(self):
        m = self.file_mtime()
        if m and m != self._mtime:
            self.reload()

    def apply_theme(self):
        for w in self.widgets:
            style_cfg(w.cfg, self.theme)
            w.relayout()
            if w.dialog:
                w.dialog.sync()
        self.schedule_save()

    def open_theme(self):
        if self.theme_dlg is None:
            self.theme_dlg = ThemeDialog(self)
        self.theme_dlg.sync()
        self.theme_dlg.show()
        self.theme_dlg.raise_()
        self.theme_dlg.activateWindow()

    def toggle_all(self):
        show = not any(w.isVisible() for w in self.widgets)
        for w in self.widgets:
            w.setVisible(show)
            if show:
                w.pin_tick()

    def reload(self):
        self._mtime = self.file_mtime()
        self.theme = load_theme()
        by_id = {c["id"]: c for c in load_store()}
        for w in list(self.widgets):
            c = by_id.pop(w.cfg["id"], None)
            if c is None or c["type"] != w.cfg["type"]:
                self.remove_widget(w, save=False)
            else:
                w.cfg = c
                w.cfg_replaced()
        for c in by_id.values():
            self.create(c)
        self.update_info()

    def pin_tick(self):
        for w in self.widgets:
            w.pin_tick()

    # ---- tepsi menüsü
    def fill_menu(self, m):
        m.clear()
        sub = m.addMenu("Widget ekle")
        for typ, label in TYPE_LABELS.items():
            add_act(sub, label, lambda t=typ: self.add_widget(t))
        wm = m.addMenu(f"Widget'lar ({len(self.widgets)})")
        counters = {}
        for w in self.widgets:
            t = w.cfg["type"]
            counters[t] = counters.get(t, 0) + 1
            label = TYPE_LABELS[t].split(" (")[0] + f" #{counters[t]}"
            ws = wm.addMenu(label)
            add_act(ws, "Ayarlar…", w.open_settings)
            add_act(ws, "Kaldır", lambda w=w: self.remove_widget(w))
        add_act(m, "Ortak tema…", self.open_theme)
        add_act(m, "Tümünü gizle / göster", self.toggle_all)
        info = m.addAction(f"Toplam uygulama slotu: {self.total_slots()}")
        info.setEnabled(False)
        m.addSeparator()
        add_act(m, "Yenile (ayar dosyasını yeniden oku)", self.reload)
        if IS_WIN:
            add_act(m, "Windows ile başlat", set_autostart, checked=autostart_enabled())
        m.addSeparator()
        add_act(m, "Çıkış", self.quit)

    def quit(self):
        self.save_now()
        if self.tray:
            self.tray.hide()
        self.app.quit()


def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("Widget Studio")
    mgr = Manager(app)  # noqa: F841  (referansı tut)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
