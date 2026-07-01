#!/usr/bin/env python3
"""Validate content-samples article packages.

Checks a single package directory (containing metadata.json) or a parent
directory holding multiple package directories (e.g. content-samples/).

Uses only the Python 3 standard library — no external dependencies.

Usage:
    python3 tools/validate_content_package.py content-samples/golden-article-001
    python3 tools/validate_content_package.py content-samples
"""
import argparse
import json
import os
import re
import struct
import sys

REQUIRED_FILES = ["post.md", "metadata.json", "source-notes.md", "README.md"]
REQUIRED_METADATA_KEYS = [
    "title",
    "slug",
    "status",
    "categories",
    "description",
    "featured_image",
    "middle_ad_marker",
]
AD_MARKER = "<!-- acourt-ad-middle -->"
SLUG_RE = re.compile(r"^[a-z0-9-]+$")
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
FEATURED_SIZE = (1200, 630)
COMPARISON_SIZE = (1200, 800)


class Result:
    def __init__(self):
        self.errors = []
        self.warnings = []

    def error(self, message):
        self.errors.append(message)

    def warning(self, message):
        self.warnings.append(message)

    @property
    def ok(self):
        return not self.errors


def resolve_safe_path(package_dir, rel_path):
    """Resolve rel_path relative to package_dir, rejecting escapes.

    Returns the resolved absolute path, or None if rel_path is absolute,
    contains '..', or resolves (following symlinks) outside package_dir.
    """
    if not rel_path:
        return None
    normalized = rel_path.replace("\\", "/")
    if normalized.startswith("/") or os.path.isabs(rel_path):
        return None
    if ".." in normalized.split("/"):
        return None
    package_real = os.path.realpath(package_dir)
    candidate_real = os.path.realpath(os.path.join(package_dir, rel_path))
    if os.path.commonpath([package_real, candidate_real]) != package_real:
        return None
    return candidate_real


def read_png_dimensions(path):
    """Return (width, height) for a valid PNG file, or None if invalid."""
    try:
        with open(path, "rb") as f:
            header = f.read(33)
    except OSError:
        return None
    if len(header) < 33 or header[:8] != PNG_SIGNATURE:
        return None
    width, height = struct.unpack(">II", header[16:24])
    return width, height


def check_required_files(package_dir, result):
    present = {}
    for name in REQUIRED_FILES:
        path = os.path.join(package_dir, name)
        exists = os.path.isfile(path)
        present[name] = exists
        if not exists:
            result.error(f"{name}: required file is missing")
    return present


def check_image(package_dir, result, rel_path, field_name, expected_size):
    if not isinstance(rel_path, str):
        result.error(f"metadata.json: {field_name} must be a string path")
        return
    resolved = resolve_safe_path(package_dir, rel_path)
    if resolved is None:
        result.error(
            f"metadata.json: {field_name} '{rel_path}' is not a safe path "
            "within the package (absolute path, '..', or symlink escape)"
        )
        return
    if not os.path.isfile(resolved):
        result.error(f"metadata.json: {field_name} '{rel_path}' does not exist")
        return
    if os.path.getsize(resolved) == 0:
        result.error(f"{rel_path}: file is empty")
        return
    dimensions = read_png_dimensions(resolved)
    if dimensions is None:
        result.error(f"{rel_path}: not a valid PNG file")
        return
    if dimensions != expected_size:
        result.error(
            f"{rel_path}: expected size {expected_size[0]}x{expected_size[1]}, "
            f"got {dimensions[0]}x{dimensions[1]}"
        )


def check_metadata(package_dir, result, present):
    if not present.get("metadata.json"):
        return None

    path = os.path.join(package_dir, "metadata.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        metadata = json.loads(raw)
    except json.JSONDecodeError as e:
        result.error(f"metadata.json: invalid JSON ({e})")
        return None

    if not isinstance(metadata, dict):
        result.error("metadata.json: top-level value must be a JSON object")
        return None

    for key in REQUIRED_METADATA_KEYS:
        if key not in metadata:
            result.error(f"metadata.json: missing required key '{key}'")

    if "status" in metadata and metadata["status"] != "draft":
        result.error(
            f"metadata.json: status must be 'draft', got '{metadata['status']}'"
        )

    if "categories" in metadata:
        categories = metadata["categories"]
        if not isinstance(categories, list) or len(categories) == 0:
            result.error("metadata.json: categories must be a non-empty array")

    if "slug" in metadata:
        slug = metadata["slug"]
        if not isinstance(slug, str) or not SLUG_RE.match(slug):
            result.error(
                "metadata.json: slug must contain only lowercase letters, "
                "digits, and hyphens"
            )

    if "description" in metadata:
        description = metadata["description"]
        if not isinstance(description, str) or not description.strip():
            result.error("metadata.json: description must not be empty")

    if "middle_ad_marker" in metadata and metadata["middle_ad_marker"] != AD_MARKER:
        result.error(
            f"metadata.json: middle_ad_marker must be exactly '{AD_MARKER}', "
            f"got '{metadata['middle_ad_marker']}'"
        )

    if "featured_image" in metadata:
        check_image(
            package_dir, result, metadata["featured_image"], "featured_image", FEATURED_SIZE
        )

    if metadata.get("comparison_image"):
        check_image(
            package_dir,
            result,
            metadata["comparison_image"],
            "comparison_image",
            COMPARISON_SIZE,
        )

    return metadata


def check_post(package_dir, result, present, metadata):
    if not present.get("post.md"):
        return

    path = os.path.join(package_dir, "post.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    h1_matches = re.findall(r"^#\s+(.+?)\s*$", text, re.MULTILINE)
    if not h1_matches:
        result.error("post.md: no H1 heading found")
    h1_title = h1_matches[0] if h1_matches else None

    h2_matches = re.findall(r"^##(?!#)\s+.+$", text, re.MULTILINE)
    if not h2_matches:
        result.error("post.md: no H2 heading found")

    stripped_len = len(re.sub(r"\s", "", text))
    if stripped_len < 2000:
        result.error(
            f"post.md: body is too short ({stripped_len} characters, minimum 2000)"
        )

    marker_count = text.count(AD_MARKER)
    if marker_count != 1:
        result.error(
            f"post.md: '{AD_MARKER}' must appear exactly once, found {marker_count}"
        )

    if metadata is not None and h1_title is not None:
        metadata_title = metadata.get("title")
        if metadata_title is not None and metadata_title != h1_title:
            result.error(
                f"post.md: H1 title '{h1_title}' does not match "
                f"metadata.json title '{metadata_title}'"
            )


def check_source_notes(package_dir, result, present):
    if not present.get("source-notes.md"):
        return

    path = os.path.join(package_dir, "source-notes.md")
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    if not re.search(r"https?://", text):
        result.error("source-notes.md: no http:// or https:// URL found")

    if "参照日" not in text:
        result.error("source-notes.md: no '参照日' entry found")

    for marker in ("未確認", "URL未確定"):
        if marker in text:
            result.warning(f"source-notes.md: contains '{marker}'")


def validate_package(package_dir):
    result = Result()
    present = check_required_files(package_dir, result)
    metadata = check_metadata(package_dir, result, present)
    check_post(package_dir, result, present, metadata)
    check_source_notes(package_dir, result, present)
    return result


def find_packages(path):
    """Return a list of package directories to validate for the given path."""
    if os.path.isfile(os.path.join(path, "metadata.json")):
        return [path]

    packages = []
    if os.path.isdir(path):
        for entry in sorted(os.listdir(path)):
            sub = os.path.join(path, entry)
            if os.path.isdir(sub) and os.path.isfile(os.path.join(sub, "metadata.json")):
                packages.append(sub)
    return packages


def main(argv):
    parser = argparse.ArgumentParser(
        description="Validate content-samples article packages."
    )
    parser.add_argument(
        "path", help="A single package directory or a parent directory of packages"
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.path):
        print(f"ERROR: {args.path} is not a directory")
        return 1

    packages = find_packages(args.path)
    if not packages:
        print(f"ERROR: no content package found under {args.path}")
        return 1

    overall_ok = True
    for package_dir in packages:
        name = os.path.basename(os.path.normpath(package_dir))
        result = validate_package(package_dir)
        if result.ok:
            print(f"PASS: {name}")
        else:
            overall_ok = False
            print(f"FAIL: {name}")
            for error in result.errors:
                print(f"  ERROR: {error}")
        for warning in result.warnings:
            print(f"  WARNING: {warning}")

    return 0 if overall_ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
