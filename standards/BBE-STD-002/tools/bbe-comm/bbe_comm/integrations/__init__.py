"""Integration modules — outbound contracts for other tools.

Each integration module exposes pure conversion functions: Result → external
shape. They never run side effects (no network, no file write outside the
tool's data dirs, no subprocess to live systems).
"""
