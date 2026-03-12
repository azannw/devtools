"""
ToolKit — Background Remover tool.
Remove image backgrounds, optionally replace with solid colour or custom image.
"""

import threading
from pathlib import Path
from tkinter import filedialog, colorchooser

import customtkinter as ctk
from PIL import Image, ImageTk

from utils import theme


class BackgroundRemoverTool(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG_DARK)

        self._input_path = None
        self._result_image = None   # PIL Image (processed)
        self._original_image = None # PIL Image (original)
        self._bg_mode = "Transparent"
        self._bg_color = (255, 255, 255)
        self._bg_image_path = None
        self._session = None
        self._model_name = "u2net"

        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # header
        header = theme.create_tool_header(
            self, "Background Remover",
            "Remove backgrounds and replace with custom colours or images",
        )
        header.grid(row=0, column=0, sticky="ew", padx=theme.PAD_LARGE, pady=(theme.PAD_LARGE, theme.PAD_MEDIUM))

        # main workspace
        workspace = ctk.CTkFrame(self, fg_color="transparent")
        workspace.grid(row=1, column=0, sticky="nsew", padx=theme.PAD_LARGE)
        workspace.grid_columnconfigure(0, weight=1)
        workspace.grid_columnconfigure(1, weight=0)
        workspace.grid_rowconfigure(0, weight=1)

        # ── left: preview ──
        preview_card = theme.create_card_frame(workspace)
        preview_card.grid(row=0, column=0, sticky="nsew", padx=(0, theme.PAD_MEDIUM))
        preview_card.grid_rowconfigure(0, weight=1)
        preview_card.grid_columnconfigure(0, weight=1)

        self._preview_label = ctk.CTkLabel(
            preview_card, text="Select an image to get started",
            font=theme.FONT_BODY, text_color=theme.TEXT_DISABLED,
        )
        self._preview_label.grid(row=0, column=0, sticky="nsew", padx=theme.PAD_MEDIUM, pady=theme.PAD_MEDIUM)
        # keep a reference so CTkImage isn't garbage-collected
        self._preview_ctk_image = None

        # ── right: controls ──
        ctrl = theme.create_card_frame(workspace, width=280)
        ctrl.grid(row=0, column=1, sticky="ns")
        ctrl.grid_propagate(False)
        ctrl.configure(width=280)

        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=theme.PAD_MEDIUM, pady=theme.PAD_MEDIUM)

        # select image
        theme.create_action_button(inner, "Select Image", self._select_image, width=248).pack(fill="x")
        self._file_label = ctk.CTkLabel(inner, text="No file selected", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY)
        self._file_label.pack(anchor="w", pady=(4, theme.PAD_MEDIUM))

        # model
        ctk.CTkLabel(inner, text="Model", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self._model_menu = ctk.CTkOptionMenu(
            inner, values=["u2net", "u2netp", "u2net_human_seg", "isnet-general-use"],
            command=self._on_model_change,
            fg_color=theme.BG_INPUT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, text_color=theme.TEXT_PRIMARY,
            dropdown_fg_color=theme.BG_CARD, dropdown_hover_color=theme.ACCENT_MUTED,
            dropdown_text_color=theme.TEXT_PRIMARY, width=248,
        )
        self._model_menu.set("u2net")
        self._model_menu.pack(fill="x", pady=(4, theme.PAD_MEDIUM))

        # background mode
        ctk.CTkLabel(inner, text="Background", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self._bg_seg = ctk.CTkSegmentedButton(
            inner, values=["Transparent", "Solid Color", "Image"],
            command=self._on_bg_mode,
            font=theme.FONT_SMALL,
            fg_color=theme.BG_INPUT, selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BG_INPUT, unselected_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
        )
        self._bg_seg.set("Transparent")
        self._bg_seg.pack(fill="x", pady=(4, theme.PAD_SMALL))

        # container for bg options (swapped by mode)
        self._bg_options_frame = ctk.CTkFrame(inner, fg_color="transparent")
        self._bg_options_frame.pack(fill="x", pady=(0, theme.PAD_MEDIUM))
        self._build_bg_options()

        # action buttons
        self._remove_btn = theme.create_action_button(inner, "Remove Background", self._start_remove, width=248)
        self._remove_btn.pack(fill="x", pady=(theme.PAD_SMALL, theme.PAD_SMALL))

        self._export_btn = theme.create_secondary_button(inner, "Export Result", self._export, width=248)
        self._export_btn.pack(fill="x")
        self._export_btn.configure(state="disabled")

        # status bar
        status_frame, self._status_label, self._progress_bar = theme.create_status_bar(self)
        status_frame.grid(row=2, column=0, sticky="ew", padx=theme.PAD_LARGE, pady=(theme.PAD_MEDIUM, theme.PAD_LARGE))

    # ── bg-options sub-panel ──────────────────────────────────────────

    def _build_bg_options(self):
        for w in self._bg_options_frame.winfo_children():
            w.destroy()

        if self._bg_mode == "Solid Color":
            row = ctk.CTkFrame(self._bg_options_frame, fg_color="transparent")
            row.pack(fill="x", pady=(4, 0))

            colors = [
                ("#ffffff", "W"), ("#000000", "B"), ("#e85454", "R"),
                ("#4caf50", "G"), ("#e8913a", "O"),
            ]
            for hex_c, _label in colors:
                btn = ctk.CTkButton(
                    row, text="", width=32, height=32,
                    fg_color=hex_c, hover_color=hex_c,
                    corner_radius=6, border_width=2,
                    border_color=theme.BORDER,
                    command=lambda c=hex_c: self._pick_preset_color(c),
                )
                btn.pack(side="left", padx=2)

            ctk.CTkButton(
                row, text="...", width=32, height=32,
                fg_color=theme.BG_INPUT, hover_color=theme.BG_CARD_HOVER,
                corner_radius=6, border_width=1, border_color=theme.BORDER,
                text_color=theme.TEXT_PRIMARY,
                command=self._pick_custom_color,
            ).pack(side="left", padx=2)

            self._color_preview = ctk.CTkFrame(
                self._bg_options_frame, width=248, height=24,
                fg_color=self._rgb_to_hex(self._bg_color), corner_radius=4,
            )
            self._color_preview.pack(fill="x", pady=(4, 0))

        elif self._bg_mode == "Image":
            theme.create_secondary_button(
                self._bg_options_frame, "Choose Background", self._select_bg_image, width=248,
            ).pack(fill="x", pady=(4, 0))
            self._bg_img_label = ctk.CTkLabel(
                self._bg_options_frame, text="No background selected",
                font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY,
            )
            self._bg_img_label.pack(anchor="w", pady=(2, 0))

    # ── callbacks ─────────────────────────────────────────────────────

    def _on_model_change(self, value):
        self._model_name = value
        self._session = None  # force re-create

    def _on_bg_mode(self, value):
        self._bg_mode = value
        self._build_bg_options()

    def _pick_preset_color(self, hex_color):
        r = int(hex_color[1:3], 16)
        g = int(hex_color[3:5], 16)
        b = int(hex_color[5:7], 16)
        self._bg_color = (r, g, b)
        if hasattr(self, "_color_preview"):
            self._color_preview.configure(fg_color=hex_color)

    def _pick_custom_color(self):
        color = colorchooser.askcolor(title="Pick background colour")
        if color and color[0]:
            self._bg_color = tuple(int(c) for c in color[0])
            if hasattr(self, "_color_preview"):
                self._color_preview.configure(fg_color=color[1])

    def _select_image(self):
        path = filedialog.askopenfilename(
            title="Select Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp *.tiff")],
        )
        if not path:
            return
        self._input_path = path
        self._file_label.configure(text=Path(path).name)
        self._original_image = Image.open(path).convert("RGBA")
        self._result_image = None
        self._export_btn.configure(state="disabled")
        self._show_preview(self._original_image)
        self._status_label.configure(text="Image loaded", text_color=theme.TEXT_SECONDARY)

    def _select_bg_image(self):
        path = filedialog.askopenfilename(
            title="Select Background Image",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.webp *.bmp")],
        )
        if path:
            self._bg_image_path = path
            if hasattr(self, "_bg_img_label"):
                self._bg_img_label.configure(text=Path(path).name)

    # ── preview ───────────────────────────────────────────────────────

    def _show_preview(self, pil_image: Image.Image):
        self._preview_label.update_idletasks()
        max_w = max(self._preview_label.winfo_width() - 20, 200)
        max_h = max(self._preview_label.winfo_height() - 20, 200)

        img = pil_image.copy()
        img.thumbnail((max_w, max_h), Image.LANCZOS)
        self._preview_ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)
        self._preview_label.configure(image=self._preview_ctk_image, text="")

    # ── processing ────────────────────────────────────────────────────

    def _start_remove(self):
        if not self._input_path:
            self._status_label.configure(text="Please select an image first", text_color=theme.WARNING)
            return
        self._remove_btn.configure(state="disabled")
        self._status_label.configure(text="Removing background…", text_color=theme.TEXT_SECONDARY)
        self._progress_bar.set(0)
        threading.Thread(target=self._do_remove, daemon=True).start()

    def _do_remove(self):
        try:
            from rembg import remove, new_session

            self.after(0, lambda: self._progress_bar.set(0.1))
            if self._session is None or self._session_model != self._model_name:
                self.after(0, lambda: self._status_label.configure(text="Loading model (first time may download)…"))
                self._session = new_session(self._model_name)
                self._session_model = self._model_name
            self.after(0, lambda: self._progress_bar.set(0.3))

            input_img = Image.open(self._input_path)
            self.after(0, lambda: self._status_label.configure(text="Processing…"))

            if self._bg_mode == "Solid Color":
                r, g, b = self._bg_color
                result = remove(input_img, session=self._session, bgcolor=(r, g, b, 255))
            else:
                result = remove(input_img, session=self._session)

            self.after(0, lambda: self._progress_bar.set(0.8))

            if self._bg_mode == "Image" and self._bg_image_path:
                bg = Image.open(self._bg_image_path).convert("RGBA")
                bg = bg.resize(result.size, Image.LANCZOS)
                result_rgba = result.convert("RGBA")
                bg.paste(result_rgba, mask=result_rgba.split()[3])
                result = bg

            self._result_image = result
            self.after(0, lambda: self._progress_bar.set(1.0))
            self.after(0, lambda: self._show_preview(result))
            self.after(0, lambda: self._export_btn.configure(state="normal"))
            self.after(0, lambda: self._status_label.configure(text="Background removed!", text_color=theme.SUCCESS))
        except Exception as e:
            self.after(0, lambda: self._status_label.configure(text=f"Error: {e}", text_color=theme.ERROR))
        finally:
            self.after(0, lambda: self._remove_btn.configure(state="normal"))

    # ── export ────────────────────────────────────────────────────────

    def _export(self):
        if self._result_image is None:
            return
        path = filedialog.asksaveasfilename(
            title="Export Image",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("WebP", "*.webp")],
        )
        if not path:
            return
        try:
            ext = Path(path).suffix.lower()
            img = self._result_image
            if ext in (".jpg", ".jpeg"):
                if img.mode == "RGBA":
                    bg = Image.new("RGB", img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                img.save(path, "JPEG", quality=95)
            else:
                img.save(path)
            self._status_label.configure(text=f"Saved to {Path(path).name}", text_color=theme.SUCCESS)
        except Exception as e:
            self._status_label.configure(text=f"Export failed: {e}", text_color=theme.ERROR)

    # ── helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _rgb_to_hex(rgb):
        return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
