#!/usr/bin/env python3
"""Convenience entry point; run geo_data.py for --root support."""
import sys
from geo_data import main

if __name__ == "__main__":
    raise SystemExit(main(["diff", *sys.argv[1:]]))
