#!/usr/bin/env python3
"""Build Auto-blog compatible ZIP from tokoroten-site content package.

Converts a validated content-samples article package into a ZIP file
that Auto-blog can ingest via its existing pipeline.

Uses only the Python 3 standard library — no external dependencies.

Usage:
    python3 tools/build_autoblog_package.py content-samples/golden-article-001
    python3 tools/build_autoblog_package.py content-samples/golden-article-001 --output dist/
    python3 tools/build_autoblog_package.py content-samples/golden-article-001 --force
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from datetime import datetime

# Validation script path (relative to this script)
VALIDATE_SCRIPT = os.path.join(os.path.dirname(__file__), "validate_content_package.py")

# YAML-unsafe characters that need escaping
YAML_SPECIAL_CHARS = re.compile(r"[:\#\[\]\{\}\&\*\!\|\>\'\"\%\@\`]")


def escape_yaml_string(value):
    """Escape a string value for safe YAML output.
    
    Returns a double-quoted string if the value contains special characters,
    otherwise returns the plain value.
    """
    if not isinstance(value, str):
        return str(value)
    
    # Always quote if contains special chars, newlines, or leading/trailing whitespace
    if (YAML_SPECIAL_CHARS.search(value) or 
        "\n" in value or 
        value != value.strip() or
        value.startswith("-") or
        value.startswith("?")):
        # Escape backslashes and double quotes
        escaped = value.replace("\\", "\\\\").replace('"', '\\"')
        return f'"{escaped}"'
    return value


def build_frontmatter(metadata):
    """Build YAML frontmatter from metadata.json contents.
    
    Always sets status to 'draft' regardless of input value.
    """
    lines = ["---"]
    
    # Required fields
    lines.append(f"title: {escape_yaml_string(metadata['title'])}")
    lines.append(f"slug: {escape_yaml_string(metadata['slug'])}")
    
    # Always force draft status
    lines.append("status: draft")
    
    # Description (optional but expected)
    if metadata.get("description"):
        lines.append(f"description: {escape_yaml_string(metadata['description'])}")
    
    # Categories as YAML array
    if metadata.get("categories"):
        lines.append("categories:")
        for cat in metadata["categories"]:
            lines.append(f"  - {escape_yaml_string(cat)}")
    
    # Featured image (relative path within ZIP)
    if metadata.get("featured_image"):
        lines.append(f"featured_image: {escape_yaml_string(metadata['featured_image'])}")
    
    lines.append("---")
    return "\n".join(lines)


def remove_h1_from_body(body_text):
    """Remove the first H1 heading from markdown body.
    
    The H1 duplicates the WordPress post title, so we remove it
    from the body content.
    """
    # Match H1 at the start (with optional leading whitespace/newlines)
    pattern = r"^\s*#\s+[^\n]+\n*"
    return re.sub(pattern, "", body_text, count=1)


def validate_ad_marker(body_text, marker="<!-- acourt-ad-middle -->"):
    """Verify the ad marker appears exactly once in the body."""
    count = body_text.count(marker)
    if count != 1:
        raise ValueError(
            f"Ad marker '{marker}' must appear exactly once, found {count}"
        )
    return True


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


def collect_images(package_dir, metadata):
    """Collect image paths to include in the ZIP.
    
    Returns a list of (relative_path, absolute_path) tuples.
    Validates that all paths are safe and files exist.
    """
    images = []
    
    for field in ["featured_image", "comparison_image"]:
        rel_path = metadata.get(field)
        if not rel_path:
            continue
        
        abs_path = resolve_safe_path(package_dir, rel_path)
        if abs_path is None:
            raise ValueError(
                f"Unsafe path in {field}: '{rel_path}' "
                "(absolute path, '..', or symlink escape)"
            )
        
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"{field} not found: '{rel_path}'")
        
        images.append((rel_path, abs_path))
    
    return images


def run_validation(package_dir):
    """Run the content package validation script.
    
    Returns True if validation passes, raises an exception otherwise.
    """
    if not os.path.isfile(VALIDATE_SCRIPT):
        raise FileNotFoundError(f"Validation script not found: {VALIDATE_SCRIPT}")
    
    result = subprocess.run(
        [sys.executable, VALIDATE_SCRIPT, package_dir],
        capture_output=True,
        text=True
    )
    
    if result.returncode != 0:
        raise ValueError(
            f"Content package validation failed:\n{result.stdout}\n{result.stderr}"
        )
    
    return True


def build_autoblog_zip(package_dir, output_dir, force=False):
    """Build an Auto-blog compatible ZIP from a content package.
    
    Args:
        package_dir: Path to the content package directory
        output_dir: Directory to write the output ZIP
        force: If True, overwrite existing output file
        
    Returns:
        Path to the created ZIP file
    """
    # Validate input package first
    run_validation(package_dir)
    
    # Load metadata
    metadata_path = os.path.join(package_dir, "metadata.json")
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    # Load original post.md
    post_path = os.path.join(package_dir, "post.md")
    with open(post_path, "r", encoding="utf-8") as f:
        original_body = f.read()
    
    # Validate ad marker
    validate_ad_marker(original_body)
    
    # Build new post.md content
    frontmatter = build_frontmatter(metadata)
    body_without_h1 = remove_h1_from_body(original_body)
    new_post_content = frontmatter + "\n\n" + body_without_h1.lstrip()
    
    # Collect images
    images = collect_images(package_dir, metadata)
    
    # Determine output path
    slug = metadata["slug"]
    output_filename = f"{slug}.zip"
    output_path = os.path.join(output_dir, output_filename)
    
    # Check for existing file
    if os.path.exists(output_path) and not force:
        raise FileExistsError(
            f"Output file already exists: {output_path}\n"
            "Use --force to overwrite"
        )
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Create ZIP atomically (write to temp, then rename)
    temp_fd, temp_path = tempfile.mkstemp(suffix=".zip", dir=output_dir)
    try:
        os.close(temp_fd)
        
        # Use fixed timestamp for deterministic output
        # Using a fixed date to ensure reproducible builds
        fixed_time = (2025, 1, 1, 0, 0, 0)
        
        with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as zf:
            # Add post.md first
            info = zipfile.ZipInfo("post.md", date_time=fixed_time)
            info.compress_type = zipfile.ZIP_DEFLATED
            zf.writestr(info, new_post_content.encode("utf-8"))
            
            # Add images in sorted order for determinism
            for rel_path, abs_path in sorted(images):
                info = zipfile.ZipInfo(rel_path, date_time=fixed_time)
                info.compress_type = zipfile.ZIP_DEFLATED
                with open(abs_path, "rb") as img_f:
                    zf.writestr(info, img_f.read())
        
        # Atomic rename
        shutil.move(temp_path, output_path)
        
    except Exception:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
    
    return output_path


def list_zip_contents(zip_path):
    """Return a list of files in the ZIP for verification."""
    with zipfile.ZipFile(zip_path, "r") as zf:
        return sorted(zf.namelist())


def main(argv):
    parser = argparse.ArgumentParser(
        description="Build Auto-blog compatible ZIP from content package."
    )
    parser.add_argument(
        "package_dir",
        help="Path to the content package directory"
    )
    parser.add_argument(
        "--output", "-o",
        default="dist",
        help="Output directory for the ZIP file (default: dist)"
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing output file"
    )
    args = parser.parse_args(argv)
    
    if not os.path.isdir(args.package_dir):
        print(f"ERROR: {args.package_dir} is not a directory", file=sys.stderr)
        return 1
    
    try:
        output_path = build_autoblog_zip(
            args.package_dir,
            args.output,
            force=args.force
        )
        
        print(f"SUCCESS: Created {output_path}")
        print("Contents:")
        for name in list_zip_contents(output_path):
            print(f"  {name}")
        
        return 0
        
    except FileExistsError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except (ValueError, FileNotFoundError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
