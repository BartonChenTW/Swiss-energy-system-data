"""Parse CHANGELOG.md and describe the build, for the site footer and Changelog page."""
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CHANGELOG = ROOT / "CHANGELOG.md"

VERSION_RE = re.compile(r"^## \[([^\]]+)\](?:\s+-\s+(\d{4}-\d{2}-\d{2}))?\s*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def parse(text: str) -> list[dict]:
    """Versions, newest first: {version, date, sections: [{title, items}]}."""
    versions, section = [], None
    for line in text.splitlines():
        if m := VERSION_RE.match(line):
            versions.append({"version": m[1], "date": m[2], "sections": []})
            section = None
        elif not versions:
            continue  # preamble
        elif line.startswith("### "):
            section = {"title": line[4:].strip(), "items": []}
            versions[-1]["sections"].append(section)
        elif line.startswith("- ") and section is not None:
            section["items"].append(line[2:].strip())
        elif line.startswith("  ") and line.strip() and section and section["items"]:
            section["items"][-1] += " " + line.strip()  # wrapped bullet
    for v in versions:
        if v["version"] != "Unreleased" and not (SEMVER_RE.match(v["version"]) and v["date"]):
            raise ValueError(f"CHANGELOG.md: '{v['version']}' needs to look like '## [1.2.3] - YYYY-MM-DD'")
    return versions


def commit() -> str | None:
    """Commit the site is built from: GitHub Actions sets GITHUB_SHA, locally ask git."""
    if sha := os.environ.get("GITHUB_SHA"):
        return sha
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True,
                              text=True, check=True).stdout.strip() or None
    except (OSError, subprocess.CalledProcessError):
        return None


def site_version(built: str) -> dict:
    versions = parse(CHANGELOG.read_text(encoding="utf-8"))
    released = [v for v in versions if v["version"] != "Unreleased"]
    unreleased = next((v for v in versions if v["version"] == "Unreleased"), None)
    return {
        "version": released[0]["version"] if released else None,
        "released": released[0]["date"] if released else None,
        "built": built,
        "commit": commit(),
        # Changes merged since the last release, so the page can say "plus unreleased changes".
        "unreleased": bool(unreleased and any(s["items"] for s in unreleased["sections"])),
        "changelog": [v for v in versions if v["version"] != "Unreleased" or any(s["items"] for s in v["sections"])],
    }
