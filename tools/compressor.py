"""
ToolKit — Image / Video Compressor tool.
Compress images (Pillow) and videos (ffmpeg) with user-controlled quality.
"""

import os
import shutil
import subprocess
import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image

from utils import theme


class CompressorTool(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG_DARK)
        self._image_paths = []
        self._video_path = None
        self._mode = "Image"
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        # header
        header = theme.create_tool_header(
            self, "Compressor",
            "Compress images and videos while controlling quality and size",
        )
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD_LARGE, pady=(theme.PAD_LARGE, theme.PAD_MEDIUM))

        # mode selector
        self._mode_seg = ctk.CTkSegmentedButton(
            self, values=["Image", "Video"], command=self._switch_mode,
            font=theme.FONT_BODY,
            fg_color=theme.BG_INPUT, selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BG_INPUT, unselected_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
        )
        self._mode_seg.set("Image")
        self._mode_seg.grid(row=1, column=0, sticky="w", padx=theme.PAD_LARGE, pady=(0, theme.PAD_MEDIUM))

        # panels container
        self._panels = ctk.CTkFrame(self, fg_color="transparent")
        self._panels.grid(row=2, column=0, sticky="nsew", padx=theme.PAD_LARGE)
        self._panels.grid_columnconfigure(0, weight=1)
        self._panels.grid_rowconfigure(0, weight=1)

        self._image_panel = self._build_image_panel(self._panels)
        self._video_panel = self._build_video_panel(self._panels)
        self._image_panel.grid(row=0, column=0, sticky="nsew")

        # status bar
        sf, self._status_label, self._progress_bar = theme.create_status_bar(self)
        sf.grid(row=3, column=0, sticky="ew", padx=theme.PAD_LARGE, pady=(theme.PAD_MEDIUM, theme.PAD_LARGE))

    def _switch_mode(self, value):
        self._mode = value
        if value == "Image":
            self._video_panel.grid_forget()
            self._image_panel.grid(row=0, column=0, sticky="nsew")
        else:
            self._image_panel.grid_forget()
            self._video_panel.grid(row=0, column=0, sticky="nsew")

    # ── image panel ───────────────────────────────────────────────────

    def _build_image_panel(self, parent):
        card = theme.create_card_frame(parent)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=theme.PAD_LARGE, pady=theme.PAD_LARGE)

        # select images
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        theme.create_action_button(top, "Select Images", self._select_images, width=180).pack(side="left")
        self._img_count_label = ctk.CTkLabel(top, text="No files selected", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY)
        self._img_count_label.pack(side="left", padx=theme.PAD_MEDIUM)

        # quality
        qf, self._img_quality_slider, _ = theme.create_slider_with_label(inner, "Quality (%)", 1, 100, 75)
        qf.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))

        # max dimension
        df, self._img_dim_slider, _ = theme.create_slider_with_label(inner, "Max dimension (px)", 100, 4000, 1920)
        df.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))
        ctk.CTkLabel(inner, text="Images larger than this are proportionally resized", font=theme.FONT_SMALL, text_color=theme.TEXT_DISABLED).pack(anchor="w")

        # output format
        fmt_row = ctk.CTkFrame(inner, fg_color="transparent")
        fmt_row.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))
        ctk.CTkLabel(fmt_row, text="Output format", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(side="left")
        self._img_fmt_menu = ctk.CTkOptionMenu(
            fmt_row, values=["Same as input", "JPEG", "PNG", "WebP"],
            fg_color=theme.BG_INPUT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, text_color=theme.TEXT_PRIMARY,
            dropdown_fg_color=theme.BG_CARD, dropdown_hover_color=theme.ACCENT_MUTED,
            dropdown_text_color=theme.TEXT_PRIMARY, width=160,
        )
        self._img_fmt_menu.set("Same as input")
        self._img_fmt_menu.pack(side="right")

        # output folder
        out_row = ctk.CTkFrame(inner, fg_color="transparent")
        out_row.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))
        theme.create_secondary_button(out_row, "Output Folder", self._select_img_output, width=140).pack(side="left")
        self._img_out_label = ctk.CTkLabel(out_row, text="Same as input", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY)
        self._img_out_label.pack(side="left", padx=theme.PAD_SMALL)
        self._img_output_dir = None

        # compress
        theme.create_action_button(inner, "Compress Images", self._start_image_compress, width=200).pack(anchor="w", pady=(theme.PAD_LARGE, 0))

        return card

    # ── video panel ───────────────────────────────────────────────────

    def _build_video_panel(self, parent):
        card = theme.create_card_frame(parent)
        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=theme.PAD_LARGE, pady=theme.PAD_LARGE)

        # select video
        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        theme.create_action_button(top, "Select Video", self._select_video, width=180).pack(side="left")
        self._vid_label = ctk.CTkLabel(top, text="No file selected", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY)
        self._vid_label.pack(side="left", padx=theme.PAD_MEDIUM)

        # CRF
        cf, self._crf_slider, _ = theme.create_slider_with_label(inner, "Quality (CRF — lower = better)", 0, 51, 23)
        cf.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))

        # preset
        preset_row = ctk.CTkFrame(inner, fg_color="transparent")
        preset_row.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))
        ctk.CTkLabel(preset_row, text="Encoding speed", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(side="left")
        self._preset_menu = ctk.CTkOptionMenu(
            preset_row, values=["ultrafast", "veryfast", "fast", "medium", "slow", "veryslow"],
            fg_color=theme.BG_INPUT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, text_color=theme.TEXT_PRIMARY,
            dropdown_fg_color=theme.BG_CARD, dropdown_hover_color=theme.ACCENT_MUTED,
            dropdown_text_color=theme.TEXT_PRIMARY, width=160,
        )
        self._preset_menu.set("medium")
        self._preset_menu.pack(side="right")

        # resolution
        res_row = ctk.CTkFrame(inner, fg_color="transparent")
        res_row.pack(fill="x", pady=(theme.PAD_MEDIUM, 0))
        ctk.CTkLabel(res_row, text="Resolution", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(side="left")
        self._res_menu = ctk.CTkOptionMenu(
            res_row, values=["Original", "1080p", "720p", "480p"],
            fg_color=theme.BG_INPUT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, text_color=theme.TEXT_PRIMARY,
            dropdown_fg_color=theme.BG_CARD, dropdown_hover_color=theme.ACCENT_MUTED,
            dropdown_text_color=theme.TEXT_PRIMARY, width=160,
        )
        self._res_menu.set("Original")
        self._res_menu.pack(side="right")

        # compress
        self._vid_compress_btn = theme.create_action_button(inner, "Compress Video", self._start_video_compress, width=200)
        self._vid_compress_btn.pack(anchor="w", pady=(theme.PAD_LARGE, 0))

        # ffmpeg check
        if not shutil.which("ffmpeg"):
            ctk.CTkLabel(
                inner, text="ffmpeg not found on PATH — video compression unavailable",
                font=theme.FONT_SMALL, text_color=theme.ERROR,
            ).pack(anchor="w", pady=(theme.PAD_SMALL, 0))
            self._vid_compress_btn.configure(state="disabled")

        return card

    # ── file selection ────────────────────────────────────────────────

    def _select_images(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff")],
        )
        if paths:
            self._image_paths = list(paths)
            self._img_count_label.configure(text=f"{len(paths)} file(s) selected")

    def _select_img_output(self):
        d = filedialog.askdirectory(title="Select output folder")
        if d:
            self._img_output_dir = d
            self._img_out_label.configure(text=d)

    def _select_video(self):
        path = filedialog.askopenfilename(
            title="Select Video",
            filetypes=[("Videos", "*.mp4 *.avi *.mkv *.mov *.wmv *.flv *.webm")],
        )
        if path:
            self._video_path = path
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self._vid_label.configure(text=f"{Path(path).name}  ({size_mb:.1f} MB)")

    # ── image compression ─────────────────────────────────────────────

    def _start_image_compress(self):
        if not self._image_paths:
            self._status_label.configure(text="Please select images first", text_color=theme.WARNING)
            return
        self._status_label.configure(text="Compressing…", text_color=theme.TEXT_SECONDARY)
        self._progress_bar.set(0)
        threading.Thread(target=self._do_image_compress, daemon=True).start()

    def _do_image_compress(self):
        try:
            quality = int(self._img_quality_slider.get())
            max_dim = int(self._img_dim_slider.get())
            fmt_choice = self._img_fmt_menu.get()
            total = len(self._image_paths)
            total_before = 0
            total_after = 0

            for i, path in enumerate(self._image_paths):
                total_before += os.path.getsize(path)
                img = Image.open(path)
                img.thumbnail((max_dim, max_dim), Image.LANCZOS)

                if fmt_choice == "Same as input":
                    fmt = img.format or Path(path).suffix.lstrip(".").upper()
                else:
                    fmt = fmt_choice

                # normalise
                if fmt in ("JPG", "JPEG"):
                    fmt = "JPEG"
                elif fmt == "WEBP":
                    fmt = "WebP"

                if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.convert("RGBA").split()[3] if img.mode == "RGBA" else None)
                    img = bg
                elif fmt == "JPEG" and img.mode != "RGB":
                    img = img.convert("RGB")

                out_dir = self._img_output_dir or str(Path(path).parent)
                stem = Path(path).stem
                ext_map = {"JPEG": ".jpg", "PNG": ".png", "WebP": ".webp", "BMP": ".bmp", "TIFF": ".tiff"}
                ext = ext_map.get(fmt, Path(path).suffix)
                out_path = os.path.join(out_dir, f"{stem}_compressed{ext}")

                save_kwargs = {"optimize": True}
                if fmt in ("JPEG", "WebP"):
                    save_kwargs["quality"] = quality
                img.save(out_path, fmt, **save_kwargs)
                total_after += os.path.getsize(out_path)

                self.after(0, lambda p=(i + 1) / total: self._progress_bar.set(p))
                self.after(0, lambda ii=i + 1: self._status_label.configure(text=f"Compressing {ii}/{total}…"))

            reduction = (1 - total_after / total_before) * 100 if total_before else 0
            before_mb = total_before / (1024 * 1024)
            after_mb = total_after / (1024 * 1024)
            self.after(0, lambda: self._status_label.configure(
                text=f"Done! {before_mb:.1f} MB → {after_mb:.1f} MB ({reduction:.0f}% smaller)",
                text_color=theme.SUCCESS,
            ))
        except Exception as e:
            self.after(0, lambda: self._status_label.configure(text=f"Error: {e}", text_color=theme.ERROR))

    # ── video compression ─────────────────────────────────────────────

    def _start_video_compress(self):
        if not self._video_path:
            self._status_label.configure(text="Please select a video first", text_color=theme.WARNING)
            return
        out = filedialog.asksaveasfilename(
            title="Save compressed video",
            defaultextension=".mp4",
            filetypes=[("MP4", "*.mp4"), ("MKV", "*.mkv"), ("AVI", "*.avi")],
        )
        if not out:
            return
        self._vid_output_path = out
        self._vid_compress_btn.configure(state="disabled")
        self._status_label.configure(text="Compressing video…", text_color=theme.TEXT_SECONDARY)
        self._progress_bar.set(0)
        threading.Thread(target=self._do_video_compress, daemon=True).start()

    def _do_video_compress(self):
        try:
            crf = str(int(self._crf_slider.get()))
            preset = self._preset_menu.get()
            resolution = self._res_menu.get()

            cmd = [
                "ffmpeg", "-y", "-i", self._video_path,
                "-c:v", "libx264", "-crf", crf,
                "-preset", preset,
                "-c:a", "aac", "-b:a", "128k",
            ]
            scale_map = {"1080p": "1920:-2", "720p": "1280:-2", "480p": "854:-2"}
            if resolution in scale_map:
                cmd += ["-vf", f"scale={scale_map[resolution]}"]
            cmd.append(self._vid_output_path)

            # show indeterminate-style progress
            self.after(0, lambda: self._progress_bar.configure(mode="indeterminate"))
            self.after(0, lambda: self._progress_bar.start())

            process = subprocess.run(
                cmd, capture_output=True, text=True,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )

            self.after(0, lambda: self._progress_bar.stop())
            self.after(0, lambda: self._progress_bar.configure(mode="determinate"))

            if process.returncode != 0:
                err = process.stderr.split("\n")[-2] if process.stderr else "Unknown error"
                self.after(0, lambda: self._status_label.configure(text=f"ffmpeg error: {err}", text_color=theme.ERROR))
                return

            orig = os.path.getsize(self._video_path) / (1024 * 1024)
            comp = os.path.getsize(self._vid_output_path) / (1024 * 1024)
            reduction = (1 - comp / orig) * 100 if orig else 0
            self.after(0, lambda: self._progress_bar.set(1))
            self.after(0, lambda: self._status_label.configure(
                text=f"Done! {orig:.1f} MB → {comp:.1f} MB ({reduction:.0f}% smaller)",
                text_color=theme.SUCCESS,
            ))
        except Exception as e:
            self.after(0, lambda: self._progress_bar.stop())
            self.after(0, lambda: self._progress_bar.configure(mode="determinate"))
            self.after(0, lambda: self._status_label.configure(text=f"Error: {e}", text_color=theme.ERROR))
        finally:
            self.after(0, lambda: self._vid_compress_btn.configure(state="normal"))
