"""Run processors.

    python -m pipeline.process                  # every module in pipeline/process/
    python -m pipeline.process buildings_gwr    # just one
"""
import importlib
import pkgutil
import sys

import pipeline.process as package


def main(names: list[str]) -> None:
    if not names:
        names = [m.name for m in pkgutil.iter_modules(package.__path__) if not m.name.startswith("_")]
    for name in names:
        print(f"[{name}]")
        importlib.import_module(f"pipeline.process.{name}").run()


if __name__ == "__main__":
    main(sys.argv[1:])
