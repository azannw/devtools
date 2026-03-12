"""
ToolKit — A personal developer toolkit.
Main entry point: app shell with sidebar navigation.
"""

import customtkinter as ctk

from utils import theme
from tools.compressor import CompressorTool
from tools.img_to_pdf import ImagesToPdfTool
from tools.file_converter import FileConverterTool
from tools.yt_downloader import YTDownloaderTool


class ToolKitApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # ── window ────────────────────────────────────────────────────
        self.title("ToolKit")
        self.geometry("1200x750")
        self.minsize(960, 600)
        self.configure(fg_color=theme.BG_DARK)

        ctk.set_appearance_mode("dark")

        # ── layout: sidebar | content ─────────────────────────────────
        self.grid_columnconfigure(0, weight=0, minsize=220)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_content_area()
        self._register_tools()

        # show first tool
        self._show_tool("compressor")

    # ── sidebar ───────────────────────────────────────────────────────

    def _build_sidebar(self):
        sidebar = ctk.CTkFrame(self, fg_color=theme.BG_SIDEBAR, corner_radius=0, width=220)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)

        # logo / title
        title_frame = ctk.CTkFrame(sidebar, fg_color="transparent")
        title_frame.pack(fill="x", padx=16, pady=(20, 0))

        ctk.CTkLabel(
            title_frame, text="ToolKit", font=("Segoe UI", 22, "bold"),
            text_color=theme.ACCENT,
        ).pack(anchor="w")
        ctk.CTkLabel(
            title_frame, text="Personal Dev Tools", font=theme.FONT_SMALL,
            text_color=theme.TEXT_DISABLED,
        ).pack(anchor="w", pady=(0, 4))

        # divider
        ctk.CTkFrame(sidebar, height=1, fg_color=theme.BORDER).pack(fill="x", padx=16, pady=(12, 16))

        # nav buttons
        self._nav_buttons = {}
        nav_items = [
            ("compressor",     "\u2699  Compressor"),
            ("img_to_pdf",     "\u2630  Images to PDF"),
            ("file_converter", "\u21c4  File Converter"),
            ("yt_downloader",  "\u25b6  YouTube Downloader"),
        ]
        for key, label in nav_items:
            btn = ctk.CTkButton(
                sidebar, text=f"  {label}", anchor="w",
                font=theme.FONT_BODY, height=42,
                fg_color="transparent", hover_color=theme.ACCENT_MUTED,
                text_color=theme.TEXT_SECONDARY, corner_radius=8,
                command=lambda k=key: self._show_tool(k),
            )
            btn.pack(fill="x", padx=12, pady=3)
            self._nav_buttons[key] = btn

        # push version label to bottom
        ctk.CTkFrame(sidebar, fg_color="transparent").pack(expand=True)
        ctk.CTkLabel(
            sidebar, text="v1.0.0", font=theme.FONT_SMALL,
            text_color=theme.TEXT_DISABLED,
        ).pack(pady=(0, 16))

    # ── content area ──────────────────────────────────────────────────

    def _build_content_area(self):
        self._content = ctk.CTkFrame(self, fg_color=theme.BG_DARK, corner_radius=0)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)

    # ── tools ─────────────────────────────────────────────────────────

    def _register_tools(self):
        self._tools = {
            "compressor":     CompressorTool(self._content),
            "img_to_pdf":     ImagesToPdfTool(self._content),
            "file_converter": FileConverterTool(self._content),
            "yt_downloader":  YTDownloaderTool(self._content),
        }
        self._active_tool = None

    def _show_tool(self, name):
        if self._active_tool == name:
            return

        # hide current
        if self._active_tool and self._active_tool in self._tools:
            self._tools[self._active_tool].grid_forget()
            self._nav_buttons[self._active_tool].configure(
                fg_color="transparent", text_color=theme.TEXT_SECONDARY,
            )

        # show new
        self._tools[name].grid(row=0, column=0, sticky="nsew")
        self._nav_buttons[name].configure(
            fg_color=theme.ACCENT_MUTED, text_color=theme.ACCENT,
        )
        self._active_tool = name


if __name__ == "__main__":
    app = ToolKitApp()
    app.mainloop()
