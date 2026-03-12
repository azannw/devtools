"""
ToolKit — Shared theme constants and widget factories.
All colors, fonts, spacing, and reusable styled-widget helpers live here
so the entire app stays visually consistent.
"""

import customtkinter as ctk

# ── Colour palette (warm-neutral dark — no blue) ──────────────────────────

BG_DARK        = "#1a1a1a"
BG_CARD        = "#252525"
BG_CARD_HOVER  = "#2e2e2e"
BG_SIDEBAR     = "#1e1e1e"
BG_INPUT       = "#2a2a2a"

ACCENT         = "#e8913a"
ACCENT_HOVER   = "#d4802e"
ACCENT_MUTED   = "#3d2e1a"

TEXT_PRIMARY    = "#e8e8e8"
TEXT_SECONDARY  = "#9a9a9a"
TEXT_DISABLED   = "#555555"

BORDER         = "#333333"
SUCCESS        = "#4caf50"
ERROR          = "#e85454"
WARNING        = "#e8c84a"
SCROLLBAR      = "#3a3a3a"

# ── Fonts (Segoe UI ships with every Windows install) ─────────────────────

FONT_HEADING    = ("Segoe UI", 20, "bold")
FONT_SUBHEADING = ("Segoe UI", 14, "bold")
FONT_BODY       = ("Segoe UI", 13)
FONT_SMALL      = ("Segoe UI", 11)
FONT_BUTTON     = ("Segoe UI", 13, "bold")

# ── Spacing / geometry ────────────────────────────────────────────────────

PAD_LARGE      = 24
PAD_MEDIUM     = 16
PAD_SMALL      = 8
CORNER_RADIUS  = 10


# ── Widget factories ─────────────────────────────────────────────────────

def create_tool_header(parent, title: str, subtitle: str):
    """Return a styled header frame with title + subtitle labels."""
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    ctk.CTkLabel(
        frame, text=title, font=FONT_HEADING,
        text_color=TEXT_PRIMARY, anchor="w",
    ).pack(anchor="w")
    ctk.CTkLabel(
        frame, text=subtitle, font=FONT_SMALL,
        text_color=TEXT_SECONDARY, anchor="w",
    ).pack(anchor="w", pady=(2, 0))
    return frame


def create_action_button(parent, text: str, command, width=180):
    """Primary call-to-action button (accent colour)."""
    return ctk.CTkButton(
        parent, text=text, command=command, width=width,
        font=FONT_BUTTON, height=38,
        fg_color=ACCENT, hover_color=ACCENT_HOVER,
        text_color="#ffffff", corner_radius=8,
    )


def create_secondary_button(parent, text: str, command, width=140):
    """Secondary / outline button."""
    return ctk.CTkButton(
        parent, text=text, command=command, width=width,
        font=FONT_BODY, height=36,
        fg_color=BG_CARD, hover_color=BG_CARD_HOVER,
        border_width=1, border_color=BORDER,
        text_color=TEXT_PRIMARY, corner_radius=8,
    )


def create_card_frame(parent, **kwargs):
    """A rounded card surface."""
    kw = dict(fg_color=BG_CARD, corner_radius=CORNER_RADIUS)
    kw.update(kwargs)
    return ctk.CTkFrame(parent, **kw)


def create_label(parent, text, font=None, color=None):
    return ctk.CTkLabel(
        parent, text=text,
        font=font or FONT_BODY,
        text_color=color or TEXT_PRIMARY,
    )


def create_slider_with_label(parent, label_text, from_, to, default, command=None, is_int=True):
    """
    Returns (frame, slider, value_label).
    The value_label auto-updates when the slider moves.
    """
    frame = ctk.CTkFrame(parent, fg_color="transparent")

    top = ctk.CTkFrame(frame, fg_color="transparent")
    top.pack(fill="x")
    ctk.CTkLabel(
        top, text=label_text, font=FONT_SMALL, text_color=TEXT_SECONDARY,
    ).pack(side="left")

    val_text = str(int(default)) if is_int else f"{default:.1f}"
    value_label = ctk.CTkLabel(
        top, text=val_text, font=FONT_SMALL, text_color=ACCENT, width=50,
    )
    value_label.pack(side="right")

    def _on_change(v):
        display = str(int(float(v))) if is_int else f"{float(v):.1f}"
        value_label.configure(text=display)
        if command:
            command(v)

    slider = ctk.CTkSlider(
        frame, from_=from_, to=to, number_of_steps=(to - from_) if is_int else 100,
        command=_on_change,
        fg_color=SCROLLBAR, progress_color=ACCENT,
        button_color=ACCENT, button_hover_color=ACCENT_HOVER,
    )
    slider.set(default)
    slider.pack(fill="x", pady=(4, 0))

    return frame, slider, value_label


def create_status_bar(parent):
    """Returns (frame, status_label, progress_bar)."""
    frame = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=8, height=44)
    frame.pack_propagate(False)

    status_label = ctk.CTkLabel(
        frame, text="Ready", font=FONT_SMALL,
        text_color=TEXT_SECONDARY, anchor="w",
    )
    status_label.pack(side="left", padx=PAD_MEDIUM, fill="x", expand=True)

    progress_bar = ctk.CTkProgressBar(
        frame, width=160, height=6,
        fg_color=SCROLLBAR, progress_color=ACCENT,
        corner_radius=3,
    )
    progress_bar.set(0)
    progress_bar.pack(side="right", padx=PAD_MEDIUM)

    return frame, status_label, progress_bar
