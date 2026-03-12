"""
ToolKit — Images to PDF converter.
Select multiple images, reorder them, and combine into a single PDF.
"""

import threading
from pathlib import Path
from tkinter import filedialog

import customtkinter as ctk
from PIL import Image
from fpdf import FPDF

from utils import theme


class ImagesToPdfTool(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color=theme.BG_DARK)
        self._images = []  # list of dicts: {"path": str, "name": str, "size": (w,h)}
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────────────────

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0)
        self.grid_rowconfigure(1, weight=1)

        # header (spans both columns)
        header = theme.create_tool_header(
            self, "Images to PDF",
            "Combine multiple images into a single PDF document",
        )
        header.grid(row=0, column=0, columnspan=2, sticky="ew",
                    padx=theme.PAD_LARGE, pady=(theme.PAD_LARGE, theme.PAD_MEDIUM))

        # ── left: image list ──
        list_card = theme.create_card_frame(self)
        list_card.grid(row=1, column=0, sticky="nsew", padx=(theme.PAD_LARGE, theme.PAD_MEDIUM))
        list_card.grid_rowconfigure(0, weight=1)
        list_card.grid_columnconfigure(0, weight=1)

        self._scroll_frame = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent",
            scrollbar_button_color=theme.SCROLLBAR,
            scrollbar_button_hover_color=theme.ACCENT_MUTED,
        )
        self._scroll_frame.grid(row=0, column=0, sticky="nsew", padx=4, pady=4)
        self._scroll_frame.grid_columnconfigure(0, weight=1)

        self._placeholder = ctk.CTkLabel(
            self._scroll_frame, text="Add images to get started",
            font=theme.FONT_BODY, text_color=theme.TEXT_DISABLED,
        )
        self._placeholder.grid(row=0, column=0, pady=40)

        # ── right: controls ──
        ctrl = theme.create_card_frame(self, width=260)
        ctrl.grid(row=1, column=1, sticky="ns", padx=(0, theme.PAD_LARGE))
        ctrl.grid_propagate(False)
        ctrl.configure(width=260)

        inner = ctk.CTkFrame(ctrl, fg_color="transparent")
        inner.pack(fill="both", expand=True, padx=theme.PAD_MEDIUM, pady=theme.PAD_MEDIUM)

        theme.create_action_button(inner, "Add Images", self._add_images, width=228).pack(fill="x")
        theme.create_secondary_button(inner, "Clear All", self._clear_all, width=228).pack(fill="x", pady=(theme.PAD_SMALL, theme.PAD_MEDIUM))

        self._count_label = ctk.CTkLabel(inner, text="0 images", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY)
        self._count_label.pack(anchor="w")

        sep = ctk.CTkFrame(inner, height=1, fg_color=theme.BORDER)
        sep.pack(fill="x", pady=theme.PAD_MEDIUM)

        # page size
        ctk.CTkLabel(inner, text="Page size", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self._page_menu = ctk.CTkOptionMenu(
            inner, values=["A4", "Letter", "Fit to Image"],
            fg_color=theme.BG_INPUT, button_color=theme.ACCENT,
            button_hover_color=theme.ACCENT_HOVER, text_color=theme.TEXT_PRIMARY,
            dropdown_fg_color=theme.BG_CARD, dropdown_hover_color=theme.ACCENT_MUTED,
            dropdown_text_color=theme.TEXT_PRIMARY, width=228,
        )
        self._page_menu.set("A4")
        self._page_menu.pack(fill="x", pady=(4, theme.PAD_MEDIUM))

        # orientation
        ctk.CTkLabel(inner, text="Orientation", font=theme.FONT_SMALL, text_color=theme.TEXT_SECONDARY).pack(anchor="w")
        self._orient_seg = ctk.CTkSegmentedButton(
            inner, values=["Portrait", "Landscape", "Auto"],
            font=theme.FONT_SMALL,
            fg_color=theme.BG_INPUT, selected_color=theme.ACCENT,
            selected_hover_color=theme.ACCENT_HOVER,
            unselected_color=theme.BG_INPUT, unselected_hover_color=theme.BG_CARD_HOVER,
            text_color=theme.TEXT_PRIMARY,
        )
        self._orient_seg.set("Auto")
        self._orient_seg.pack(fill="x", pady=(4, theme.PAD_MEDIUM))

        # margin
        mf, self._margin_slider, _ = theme.create_slider_with_label(inner, "Margin (mm)", 0, 30, 10)
        mf.pack(fill="x", pady=(0, theme.PAD_MEDIUM))

        # quality
        qf, self._quality_slider, _ = theme.create_slider_with_label(inner, "JPEG quality", 30, 100, 85)
        qf.pack(fill="x", pady=(0, theme.PAD_MEDIUM))

        # generate
        self._gen_btn = theme.create_action_button(inner, "Generate PDF", self._start_generate, width=228)
        self._gen_btn.pack(fill="x", pady=(theme.PAD_SMALL, 0))

        # status bar (spans both columns)
        sf, self._status_label, self._progress_bar = theme.create_status_bar(self)
        sf.grid(row=2, column=0, columnspan=2, sticky="ew",
                padx=theme.PAD_LARGE, pady=(theme.PAD_MEDIUM, theme.PAD_LARGE))

    # ── image list management ─────────────────────────────────────────

    def _add_images(self):
        paths = filedialog.askopenfilenames(
            title="Select Images",
            filetypes=[("Images", "*.png *.jpg *.jpeg *.bmp *.tiff *.webp *.gif")],
        )
        if not paths:
            return
        for p in paths:
            try:
                img = Image.open(p)
                self._images.append({"path": p, "name": Path(p).name, "size": img.size})
            except Exception:
                pass
        self._rebuild_list()

    def _clear_all(self):
        self._images.clear()
        self._rebuild_list()

    def _move_up(self, idx):
        if idx <= 0:
            return
        self._images[idx], self._images[idx - 1] = self._images[idx - 1], self._images[idx]
        self._rebuild_list()

    def _move_down(self, idx):
        if idx >= len(self._images) - 1:
            return
        self._images[idx], self._images[idx + 1] = self._images[idx + 1], self._images[idx]
        self._rebuild_list()

    def _remove_item(self, idx):
        self._images.pop(idx)
        self._rebuild_list()

    def _rebuild_list(self):
        for w in self._scroll_frame.winfo_children():
            w.destroy()

        self._count_label.configure(text=f"{len(self._images)} image(s)")

        if not self._images:
            self._placeholder = ctk.CTkLabel(
                self._scroll_frame, text="Add images to get started",
                font=theme.FONT_BODY, text_color=theme.TEXT_DISABLED,
            )
            self._placeholder.grid(row=0, column=0, pady=40)
            return

        # keep thumbnail references alive
        self._thumb_refs = []

        for i, item in enumerate(self._images):
            row = ctk.CTkFrame(self._scroll_frame, fg_color=theme.BG_CARD_HOVER, corner_radius=6, height=56)
            row.grid(row=i, column=0, sticky="ew", pady=2, padx=2)
            row.grid_columnconfigure(2, weight=1)
            row.grid_propagate(False)
            row.configure(height=56)

            # index number
            ctk.CTkLabel(
                row, text=f"{i + 1}", font=theme.FONT_SMALL,
                text_color=theme.TEXT_DISABLED, width=28,
            ).grid(row=0, column=0, padx=(8, 2), pady=8)

            # thumbnail
            try:
                thumb = Image.open(item["path"])
                thumb.thumbnail((40, 40), Image.LANCZOS)
                ctk_thumb = ctk.CTkImage(light_image=thumb, dark_image=thumb, size=thumb.size)
                self._thumb_refs.append(ctk_thumb)
                ctk.CTkLabel(row, image=ctk_thumb, text="").grid(row=0, column=1, padx=4, pady=4)
            except Exception:
                ctk.CTkLabel(row, text="?", width=40).grid(row=0, column=1, padx=4, pady=4)

            # info
            info_frame = ctk.CTkFrame(row, fg_color="transparent")
            info_frame.grid(row=0, column=2, sticky="ew", padx=4)
            ctk.CTkLabel(info_frame, text=item["name"], font=theme.FONT_SMALL, text_color=theme.TEXT_PRIMARY, anchor="w").pack(anchor="w")
            ctk.CTkLabel(info_frame, text=f"{item['size'][0]}×{item['size'][1]}", font=("Segoe UI", 10), text_color=theme.TEXT_DISABLED, anchor="w").pack(anchor="w")

            # buttons
            btn_frame = ctk.CTkFrame(row, fg_color="transparent")
            btn_frame.grid(row=0, column=3, padx=4, pady=4)

            ctk.CTkButton(
                btn_frame, text="\u25b2", width=28, height=24,
                fg_color=theme.BG_INPUT, hover_color=theme.ACCENT_MUTED,
                text_color=theme.TEXT_SECONDARY, corner_radius=4,
                font=("Segoe UI", 10),
                command=lambda idx=i: self._move_up(idx),
            ).pack(side="left", padx=1)
            ctk.CTkButton(
                btn_frame, text="\u25bc", width=28, height=24,
                fg_color=theme.BG_INPUT, hover_color=theme.ACCENT_MUTED,
                text_color=theme.TEXT_SECONDARY, corner_radius=4,
                font=("Segoe UI", 10),
                command=lambda idx=i: self._move_down(idx),
            ).pack(side="left", padx=1)
            ctk.CTkButton(
                btn_frame, text="\u2715", width=28, height=24,
                fg_color=theme.BG_INPUT, hover_color=theme.ERROR,
                text_color=theme.TEXT_SECONDARY, corner_radius=4,
                font=("Segoe UI", 10),
                command=lambda idx=i: self._remove_item(idx),
            ).pack(side="left", padx=1)

    # ── PDF generation ────────────────────────────────────────────────

    def _start_generate(self):
        if not self._images:
            self._status_label.configure(text="Add images first", text_color=theme.WARNING)
            return
        out = filedialog.asksaveasfilename(
            title="Save PDF",
            defaultextension=".pdf",
            filetypes=[("PDF", "*.pdf")],
        )
        if not out:
            return
        self._output_path = out
        self._gen_btn.configure(state="disabled")
        self._status_label.configure(text="Generating PDF…", text_color=theme.TEXT_SECONDARY)
        self._progress_bar.set(0)
        threading.Thread(target=self._do_generate, daemon=True).start()

    def _do_generate(self):
        try:
            page_size = self._page_menu.get()
            orientation = self._orient_seg.get()
            margin = int(self._margin_slider.get())
            quality = int(self._quality_slider.get())
            total = len(self._images)

            page_dims = {"A4": (210, 297), "Letter": (215.9, 279.4)}

            pdf = FPDF()

            for i, item in enumerate(self._images):
                img = Image.open(item["path"])
                w_px, h_px = img.size

                if page_size == "Fit to Image":
                    w_mm = w_px * 25.4 / 96
                    h_mm = h_px * 25.4 / 96
                    orient = "L" if w_mm > h_mm else "P"
                    pdf.add_page(orientation=orient, format=(min(w_mm, h_mm), max(w_mm, h_mm)))
                    pw = max(w_mm, h_mm) if orient == "L" else min(w_mm, h_mm)
                    ph = min(w_mm, h_mm) if orient == "L" else max(w_mm, h_mm)
                    pdf.image(item["path"], x=0, y=0, w=pw, h=ph)
                else:
                    pw, ph = page_dims[page_size]
                    if orientation == "Auto":
                        orient = "L" if w_px > h_px else "P"
                    elif orientation == "Landscape":
                        orient = "L"
                    else:
                        orient = "P"

                    pdf.add_page(orientation=orient)
                    eff_w = (ph if orient == "L" else pw) - 2 * margin
                    eff_h = (pw if orient == "L" else ph) - 2 * margin

                    img_w_mm = w_px * 25.4 / 96
                    img_h_mm = h_px * 25.4 / 96
                    scale = min(eff_w / img_w_mm, eff_h / img_h_mm, 1.0)
                    iw = img_w_mm * scale
                    ih = img_h_mm * scale
                    x = margin + (eff_w - iw) / 2
                    y = margin + (eff_h - ih) / 2
                    pdf.image(item["path"], x=x, y=y, w=iw, h=ih)

                prog = (i + 1) / total
                self.after(0, lambda p=prog: self._progress_bar.set(p))
                self.after(0, lambda ii=i + 1: self._status_label.configure(text=f"Processing image {ii}/{total}…"))

            pdf.output(self._output_path)
            self.after(0, lambda: self._status_label.configure(
                text=f"PDF saved! ({total} pages)", text_color=theme.SUCCESS,
            ))
            self.after(0, lambda: self._progress_bar.set(1))
        except Exception as e:
            self.after(0, lambda: self._status_label.configure(text=f"Error: {e}", text_color=theme.ERROR))
        finally:
            self.after(0, lambda: self._gen_btn.configure(state="normal"))
