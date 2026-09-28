"""Download raw source files listed under `downloads:` in catalog/sources.yml.

    python -m pipeline.fetch                 # all sources
    python -m pipeline.fetch --source bfs_gwr
    python -m pipeline.fetch --force         # re-download existing files
"""
import argparse

import requests

from .common import RAW_DIR, load_catalog


def download(url: str, dest) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with requests.get(url, stream=True, timeout=60) as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
    tmp.replace(dest)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", action="append", help="source id (repeatable); default: all")
    parser.add_argument("--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()

    sources, _ = load_catalog()
    selected = args.source or list(sources)
    for sid in selected:
        downloads = sources[sid].get("downloads") or []
        if not downloads:
            print(f"[{sid}] no automatic downloads configured, skipping")
            continue
        for item in downloads:
            dest = RAW_DIR / sid / item["filename"]
            if dest.exists() and not args.force:
                print(f"[{sid}] {item['filename']} exists, skipping (use --force)")
                continue
            print(f"[{sid}] downloading {item['url']}")
            download(item["url"], dest)


if __name__ == "__main__":
    main()
