"""Processors: one module per source, each exposing `run()` that writes tidy CSVs via `write_tidy()`.

Modules whose name starts with `_` are skipped by `python -m pipeline.process`.
"""
