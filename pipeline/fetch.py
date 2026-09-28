"""Download raw source files listed under `downloads:` in catalog/sources.yml.

    python -m pipeline.fetch                 # all sources
    python -m pipeline.fetch --source bfs_gwr
    python -m pipeline.fetch --force         # re-download existing files

A download may carry a `post:` JSON body, sent as a POST instead of a GET.
Each download is recorded (url, retrieved, Last-Modified, sha256, bytes) in
data/raw/<source>/_manifest.json, which processors turn into provenance.
"""
import argparse
import hashlib

import requests

from .common import RAW_DIR, load_catalog, now_utc, read_manifest, write_manifest


def download(url: str, dest, post: dict | None = None) -> dict:
    """GET `url` (or POST the JSON body `post`, for query APIs such as PXWeb) into `dest`."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    h = hashlib.sha256()
    size = 0
    request = requests.post(url, json=post, stream=True, timeout=300) if post else requests.get(url, stream=True, timeout=60)
    with request as r:
        r.raise_for_status()
        with open(tmp, "wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 20):
                f.write(chunk)
                h.update(chunk)
                size += len(chunk)
        last_modified = r.headers.get("Last-Modified")
    tmp.replace(dest)
    record = {"url": url, "retrieved": now_utc(), "last_modified": last_modified, "sha256": h.hexdigest(), "bytes": size}
    if post:
        record["post"] = post
    return record


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--source", action="append", help="source id (repeatable); default: all")
    parser.add_argument("--force", action="store_true", help="re-download files that already exist")
    args = parser.parse_args()

    sources, _, _ = load_catalog()
    for sid in args.source or list(sources):
        downloads = sources[sid].get("downloads") or []
        if not downloads:
            print(f"[{sid}] no automatic downloads configured, skipping")
            continue
        source_dir = RAW_DIR / sid
        manifest = read_manifest(source_dir)
        for item in downloads:
            dest = source_dir / item["filename"]
            if dest.exists() and item["filename"] in manifest and not args.force:
                print(f"[{sid}] {item['filename']} exists, skipping (use --force)")
                continue
            print(f"[{sid}] downloading {item['url']}")
            manifest[item["filename"]] = download(item["url"], dest, item.get("post"))
            write_manifest(source_dir, manifest)


if __name__ == "__main__":
    main()
