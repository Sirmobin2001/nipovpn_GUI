#!/usr/bin/env python3
"""Launcher for the NipoVPN GUI client.

Run with::

    python gui/main.py
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from nipovpn_gui.app import main  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(main())
