"""Reusable UI widgets for the NipoVPN GUI."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .theme import COLORS


class Card(QFrame):
    """A rounded surface container with an optional title."""

    def __init__(self, title: str | None = None, parent: QWidget | None = None):
        super().__init__(parent)
        self.setObjectName("card")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(12)
        if title:
            label = QLabel(title)
            label.setObjectName("cardTitle")
            self._layout.addWidget(label)

    def body(self) -> QVBoxLayout:
        return self._layout

    def add(self, widget: QWidget) -> None:
        self._layout.addWidget(widget)


class StatCard(Card):
    """A card showing a big value with a small caption (e.g. data sent)."""

    def __init__(
        self,
        caption: str,
        value: str = "0 B",
        accent: str | None = None,
        parent: QWidget | None = None,
    ):
        super().__init__(parent=parent)
        self.value_label = QLabel(value)
        self.value_label.setObjectName("statValue")
        if accent:
            self.value_label.setStyleSheet(f"color: {accent};")
        caption_label = QLabel(caption)
        caption_label.setObjectName("statLabel")
        self.sub_label = QLabel("")
        self.sub_label.setObjectName("statLabel")

        self.add(self.value_label)
        self.add(caption_label)
        self.add(self.sub_label)

    def set_value(self, value: str) -> None:
        self.value_label.setText(value)

    def set_sub(self, text: str) -> None:
        self.sub_label.setText(text)


class StatusPill(QLabel):
    """A small colored status indicator."""

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.set_status("Disconnected", COLORS["text_muted"])

    def set_status(self, text: str, color: str) -> None:
        self.setText(f"  ●  {text}")
        self.setStyleSheet(
            f"color: {color}; font-weight: 700; font-size: 13px;"
        )


def field_row(label_text: str, widget: QWidget) -> QWidget:
    """A labeled form row laid out vertically (label above widget)."""
    container = QWidget()
    layout = QVBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(5)
    label = QLabel(label_text)
    label.setObjectName("statLabel")
    layout.addWidget(label)
    layout.addWidget(widget)
    return container


def hline() -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.HLine)
    line.setStyleSheet(f"color: {COLORS['border']};")
    line.setFixedHeight(1)
    return line


def hspace() -> QWidget:
    spacer = QWidget()
    spacer.setLayout(QHBoxLayout())
    spacer.setAttribute(Qt.WA_TransparentForMouseEvents)
    return spacer
