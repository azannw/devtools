"""
ToolKit — YouTube Downloader tool.
Download videos & audio from YouTube using yt-dlp.
Based on azannw/yt-dl.
"""

import glob
import os
import re
import shutil
import threading
from tkinter import filedialog, messagebox

import customtkinter as ctk

from utils import theme

_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


# ── ffmpeg detection ──────────────────────────────────────────────────────

def _find_ffmpeg():
    """Return the directory containing ffmpeg, or None if already on PATH."""
    if shutil.which("ffmpeg"):
        return None
    base = os.path.join(
        os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages"
    )
    pattern = os.path.join(base, "Gyan.FFmpeg*", "ffmpeg-*", "bin", "ffmpeg.exe")
    matches = glob.glob(pattern)
    if matches:
        return os.path.dirname(matches[0])
    return None


FFMPEG_DIR = _find_ffmpeg()


def _ffmpeg_available():
    if shutil.which("ffmpeg"):
        return True
    if FFMPEG_DIR:
        return os.path.isfile(os.path.join(FFMPEG_DIR, "ffmpeg.exe"))
    return False


# ── Tool frame ────────────────────────────────────────────────────────────

class YTDownloaderTool(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG_DARK)

        self._downloading = False
        self._formats = []
        self._cancel_event = threading.Event()
        self._current_filename = None

        self._build_ui()

        if not _ffmpeg_available():
            self._status_label.configure(
                text="ffmpeg not found — video+audio merge won't work. Install ffmpeg and restart.",
                text_color=theme.WARNING,
            )

    # ── UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # header
        header = theme.create_tool_header(
            self, "YouTube Downloader",
            "Download videos and audio from YouTube",
        )
        header.grid(row=0, column=0, sticky="ew",
                    padx=theme.PAD_LARGE, pady=(theme.PAD_LARGE, theme.PAD_MEDIUM))

        # scrollable content area
        content = ctk.CTkScrollableFrame(
            self, fg_color="transparent",
            scrollbar_button_color=theme.SCROLLBAR,
            scrollbar_button_hover_color=theme.ACCENT_MUTED,
        )
        content.grid(row=1, column=0, sticky="nsew", padx=theme.PAD_LARGE)
        content.grid_columnconfigure(0, weight=1)

        # ── URL card ──
        url_card = theme.create_card_frame(content)
        url_card.grid(row=0, column=0, sticky="ew", pady=(0, theme.PAD_MEDIUM))
        url_inner = ctk.CTkFrame(url_card, fg_color="transparent")
        url_inner.pack(fill="x", padx=theme.PAD_MEDIUM, pady=theme.PAD_MEDIUM)

        ctk.CTkLabel(url_inner, text="Video URL", font=theme.FONT_SUBHEADING,
                     text_color=theme.TEXT_PRIMARY).pack(anchor="w")

        self._url_entry = ctk.CTkEntry(
            url_inner, placeholder_text="https://youtube.com/watch?v=...",
            font=theme.FONT_BODY, height=38, corner_radius=8,
            fg_color=theme.BG_INPUT, border_color=theme.BORDER,
            text_color=theme.TEXT_PRIMARY,
        )
        self._url_entry.pack(fill="x", pady=(theme.PAD_SMALL, theme.PAD_SMALL))

        self._fetch_btn = theme.create_action_button(url_inner, "Fetch Info", self._on_fetch, width=140)
        self._fetch_btn.pack(anchor="w")

        # ── Options card ──
        opts_card = theme.create_card_frame(content)
        opts_card.grid(row=1, column=0, sticky="ew", pady=(0, theme.PAD_MEDIUM))
        opts_inner = ctk.CTkFrame(opts_card, fg_color="transparent")
        opts_inner.pack(fill="x", padx=theme.PAD_MEDIUM, pady=theme.PAD_MEDIUM)

        ctk.CTkLabel(opts_inner, text="Download Type", font=theme.FONT_SUBHEADING,
                     text_color=theme.TEXT_PRIMARY).pack(anchor="w")

        self._seg_var = ctk.StringVar(value="Video + Audio")
        self._seg_button = ctk.CTkSegmentedButton(
            opts_inner, values=["Video + Audio", "Audio Only"],
            variable=self._seg_var, command=self._on_type_change,
            font=theme.FONT_BODY,
            fg_color=theme.BG_INPUT, selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BG_INPUT, unselected_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
        )
        self._seg_button.pack(fill="x", pady=(theme.PAD_SMALL, theme.PAD_MEDIUM))

        ctk.CTkLabel(opts_inner, text="Quality", font=theme.FONT_SMALL,
                     text_color=theme.TEXT_SECONDARY).pack(anchor="w")

        self._quality_menu = ctk.CTkOptionMenu(
            opts_inner, values=["Fetch info first"],
            fg_color=theme.BG_INPUT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, text_color=theme.TEXT_PRIMARY,
            dropdown_fg_color=theme.BG_CARD, dropdown_hover_color=theme.ACCENT_MUTED,
            dropdown_text_color=theme.TEXT_PRIMARY,
        )
        self._quality_menu.pack(fill="x", pady=(4, theme.PAD_MEDIUM))

        ctk.CTkLabel(opts_inner, text="Save to", font=theme.FONT_SMALL,
                     text_color=theme.TEXT_SECONDARY).pack(anchor="w")

        loc_frame = ctk.CTkFrame(opts_inner, fg_color="transparent")
        loc_frame.pack(fill="x", pady=(4, 0))

        self._loc_entry = ctk.CTkEntry(
            loc_frame, placeholder_text="Choose folder…",
            font=theme.FONT_BODY, height=36, corner_radius=8,
            fg_color=theme.BG_INPUT, border_color=theme.BORDER,
            text_color=theme.TEXT_PRIMARY,
        )
        self._loc_entry.pack(side="left", fill="x", expand=True, padx=(0, theme.PAD_SMALL))

        theme.create_secondary_button(loc_frame, "Browse", self._browse, width=90).pack(side="right")

        # ── Download card ──
        dl_card = theme.create_card_frame(content)
        dl_card.grid(row=2, column=0, sticky="ew", pady=(0, theme.PAD_SMALL))
        dl_inner = ctk.CTkFrame(dl_card, fg_color="transparent")
        dl_inner.pack(fill="x", padx=theme.PAD_MEDIUM, pady=theme.PAD_MEDIUM)

        self._dl_btn = ctk.CTkButton(
            dl_inner, text="Download",
            font=theme.FONT_BUTTON, height=42, corner_radius=8,
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            text_color="#ffffff",
            command=self._on_download,
        )
        self._dl_btn.pack(fill="x")

        self._progress = ctk.CTkProgressBar(
            dl_inner, height=6, corner_radius=3,
            fg_color=theme.SCROLLBAR, progress_color=theme.ACCENT,
        )
        self._progress.pack(fill="x", pady=(theme.PAD_SMALL, 0))
        self._progress.set(0)

        # status bar
        sf, self._status_label, self._status_progress = theme.create_status_bar(self)
        sf.grid(row=2, column=0, sticky="ew",
                padx=theme.PAD_LARGE, pady=(theme.PAD_MEDIUM, theme.PAD_LARGE))
        self._status_label.configure(text="Paste a URL and click Fetch Info")

    # ── helpers ───────────────────────────────────────────────────────

    @property
    def _dl_type(self):
        return "audio" if self._seg_var.get() == "Audio Only" else "video"

    def _browse(self):
        folder = filedialog.askdirectory(title="Choose download folder")
        if folder:
            self._loc_entry.delete(0, "end")
            self._loc_entry.insert(0, folder)

    def _get_url(self):
        url = self._url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a YouTube URL.")
            return None
        return url

    def _reset_download_button(self):
        self._dl_btn.configure(
            text="Download",
            fg_color=theme.ACCENT, hover_color=theme.ACCENT_HOVER,
            state="normal",
        )

    # ── fetch ─────────────────────────────────────────────────────────

    def _on_fetch(self):
        url = self._get_url()
        if not url:
            return
        self._fetch_btn.configure(state="disabled")
        self._status_label.configure(text="Fetching video info…", text_color=theme.TEXT_SECONDARY)
        self._progress.set(0)
        threading.Thread(target=self._fetch_worker, args=(url,), daemon=True).start()

    def _fetch_worker(self, url):
        try:
            import yt_dlp
            ydl_opts = {"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": False}
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

            if info.get("_type") == "playlist":
                entries = list(info.get("entries", []))
                entry_count = info.get("playlist_count") or len(entries)
                first = next((e for e in entries if e is not None), None)
                if first is None:
                    self.after(0, self._fetch_error, "Could not read playlist entries.")
                    return
                formats = first.get("formats") or []
                title = f"Playlist: {info.get('title', 'Unknown')} ({entry_count} videos)"
            else:
                formats = info.get("formats") or []
                title = info.get("title", "Unknown")

            self._formats = formats
            self.after(0, self._fetch_done, title)
        except Exception as e:
            self.after(0, self._fetch_error, str(e))

    def _fetch_done(self, title):
        self._fetch_btn.configure(state="normal")
        self._status_label.configure(text=f"Ready — {title}", text_color=theme.SUCCESS)
        self._populate_quality()

    def _fetch_error(self, err):
        self._fetch_btn.configure(state="normal")
        self._status_label.configure(text=f"Error: {_ANSI_RE.sub('', err)}", text_color=theme.ERROR)

    # ── quality ───────────────────────────────────────────────────────

    def _on_type_change(self, *_):
        self._populate_quality()

    def _populate_quality(self):
        if not self._formats:
            self._quality_menu.configure(values=["Fetch info first"])
            self._quality_menu.set("Fetch info first")
            return

        if self._dl_type == "audio":
            choices = ["Best audio (mp3)", "Best audio (m4a)", "Best audio (opus)"]
        else:
            seen = set()
            resolutions = []
            for f in self._formats:
                h = f.get("height")
                if h and h not in seen:
                    seen.add(h)
                    resolutions.append(h)
            resolutions.sort(reverse=True)

            choices = ["Best quality"]
            for r in resolutions:
                label = f"{r}p"
                if r >= 2160:
                    label += " (4K)"
                elif r >= 1440:
                    label += " (2K)"
                choices.append(label)

        self._quality_menu.configure(values=choices)
        self._quality_menu.set(choices[0])

    # ── download ──────────────────────────────────────────────────────

    def _on_download(self):
        if self._downloading:
            self._cancel_event.set()
            self._dl_btn.configure(text="Cancelling…", state="disabled")
            self._status_label.configure(text="Cancelling download…", text_color=theme.WARNING)
            return

        url = self._get_url()
        if not url:
            return
        save_dir = self._loc_entry.get().strip()
        if not save_dir or not os.path.isdir(save_dir):
            messagebox.showwarning("No folder", "Please choose a valid download folder.")
            return

        quality = self._quality_menu.get()
        dl_type = self._dl_type

        self._downloading = True
        self._cancel_event.clear()
        self._current_filename = None

        self._dl_btn.configure(
            text="Cancel", fg_color=theme.ERROR, hover_color="#c0392b",
        )
        self._progress.set(0)
        self._status_label.configure(text="Starting download…", text_color=theme.TEXT_SECONDARY)

        threading.Thread(
            target=self._download_worker,
            args=(url, save_dir, dl_type, quality),
            daemon=True,
        ).start()

    def _download_worker(self, url, save_dir, dl_type, quality):
        try:
            import yt_dlp
            ydl_opts = self._build_opts(save_dir, dl_type, quality)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            if self._cancel_event.is_set():
                self._cleanup_partial(save_dir)
                self.after(0, self._download_cancelled)
                return
            self.after(0, self._download_done)
        except Exception as e:
            if self._cancel_event.is_set():
                self._cleanup_partial(save_dir)
                self.after(0, self._download_cancelled)
            else:
                self.after(0, self._download_error, str(e))

    def _build_opts(self, save_dir, dl_type, quality):
        import yt_dlp
        outtmpl = os.path.join(save_dir, "%(title)s.%(ext)s")
        opts = {
            "outtmpl": outtmpl,
            "noplaylist": False,
            "progress_hooks": [self._progress_hook],
            "postprocessor_hooks": [self._pp_hook],
            "quiet": True,
            "no_warnings": True,
            "retries": 10,
            "fragment_retries": 10,
            "file_access_retries": 3,
        }
        if FFMPEG_DIR:
            opts["ffmpeg_location"] = FFMPEG_DIR

        if dl_type == "audio":
            audio_ext = "mp3"
            if "m4a" in quality.lower():
                audio_ext = "m4a"
            elif "opus" in quality.lower():
                audio_ext = "opus"
            opts["format"] = "bestaudio/best"
            opts["postprocessors"] = [{
                "key": "FFmpegExtractAudio",
                "preferredcodec": audio_ext,
                "preferredquality": "0",
            }]
        else:
            height = self._parse_height(quality)
            if height:
                opts["format"] = (
                    f"bestvideo*[height<={height}]+bestaudio"
                    f"/best[height<={height}]/best"
                )
            else:
                opts["format"] = "bestvideo*+bestaudio/best"
            opts["merge_output_format"] = "mp4/mkv"

        return opts

    @staticmethod
    def _parse_height(quality):
        m = re.search(r"(\d+)p", quality)
        return int(m.group(1)) if m else None

    def _progress_hook(self, d):
        import yt_dlp
        if self._cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Cancelled by user")

        if d["status"] == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            downloaded = d.get("downloaded_bytes", 0)
            pct = downloaded / total if total else 0
            speed = d.get("_speed_str", "")
            eta = d.get("_eta_str", "")
            filename = os.path.basename(d.get("filename", ""))
            self._current_filename = d.get("filename")
            self.after(0, self._update_progress, pct, f"Downloading {filename}  {speed}  ETA {eta}")
        elif d["status"] == "finished":
            self._current_filename = d.get("filename", self._current_filename)
            self.after(0, self._update_progress, 1.0, "Processing…")

    def _pp_hook(self, d):
        import yt_dlp
        if self._cancel_event.is_set():
            raise yt_dlp.utils.DownloadCancelled("Cancelled by user")

    def _update_progress(self, pct, text):
        self._progress.set(pct)
        self._status_label.configure(text=text, text_color=theme.TEXT_SECONDARY)

    def _cleanup_partial(self, save_dir):
        for pat in ("*.part", "*.ytdl"):
            for f in glob.glob(os.path.join(save_dir, pat)):
                try:
                    os.remove(f)
                except OSError:
                    pass

    def _download_cancelled(self):
        self._downloading = False
        self._reset_download_button()
        self._progress.set(0)
        self._status_label.configure(text="Download cancelled.", text_color=theme.WARNING)

    def _download_done(self):
        self._downloading = False
        self._reset_download_button()
        self._progress.set(1.0)
        self._status_label.configure(text="Download complete!", text_color=theme.SUCCESS)

    def _download_error(self, err):
        self._downloading = False
        self._reset_download_button()
        self._progress.set(0)
        self._status_label.configure(text=f"Error: {_ANSI_RE.sub('', err)}", text_color=theme.ERROR)
