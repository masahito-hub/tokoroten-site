#!/usr/bin/env python3
"""Build an Auto-blog-compatible input ZIP from a golden content package.

Converts a `content-samples/<article>/` package (post.md + metadata.json +
images/) into `article.zip` shaped for Auto-blog's input contract:

    article.zip
    ├── post.md       # YAML frontmatter + Markdown body
    └── images/
        └── ...

Uses only the Python 3 standard library — no external dependencies.

Usage:
    python3 tools/build_autoblog_package.py content-samples/golden-article-001 \
        --output dist/

The source package must pass `validate_content_package.py` before it is
converted; conversion never proceeds on a package that fails validation.
`status` in the generated frontmatter is always "draft", regardless of the
input value, so this tool can never produce a publish-ready ZIP.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import validate_content_package as vcp  # noqa: E402

OUTPUT_STATUS = "draft"
FIXED_ZIP_DATE_TIME = (1980, 1, 1, 0, 0, 0)
H1_RE = re.compile(r"\A#[ \t]+\S.*(?:\r?\n)?")


class BuildError(Exception):
    """Raised for any input/validation problem that prevents building a ZIP."""


def load_metadata(package_dir):
    path = os.path.join(package_dir, "metadata.json")
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    return json.loads(raw)


def strip_leading_h1(text):
    """Remove the leading H1 heading (and following blank lines) from text.

    The WordPress post title already carries this text, so leaving the H1
    in the body would duplicate it there.
    """
    match = H1_RE.match(text)
    if not match:
        raise BuildError("post.md does not start with an H1 heading")
    rest = text[match.end():]
    return rest.lstrip("\n")


def yaml_scalar(value):
    text = str(value)
    text = text.replace("\\", "\\\\").replace('"', '\\"')
    text = text.replace("\n", "\\n").replace("\r", "")
    return f'"{text}"'


def build_frontmatter_text(metadata, featured_image_arcname):
    """Render YAML frontmatter for the given metadata.

    `status` is hard-coded to "draft" regardless of metadata['status'] —
    this adapter must never emit a publish-ready output.
    """
    lines = ["---"]
    lines.append(f"title: {yaml_scalar(metadata['title'])}")
    lines.append(f"slug: {yaml_scalar(metadata['slug'])}")
    lines.append(f"description: {yaml_scalar(metadata['description'])}")
    lines.append(f'status: "{OUTPUT_STATUS}"')
    lines.append("categories:")
    for category in metadata["categories"]:
        lines.append(f"  - {yaml_scalar(category)}")
    if featured_image_arcname:
        lines.append(f"featured_image: {yaml_scalar(featured_image_arcname)}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def resolve_package_image(package_dir, rel_path, field_name):
    resolved = vcp.resolve_safe_path(package_dir, rel_path)
    if resolved is None:
        raise BuildError(
            f"{field_name} '{rel_path}' is not a safe path within the package "
            "(absolute path, '..', or symlink escape)"
        )
    if not os.path.isfile(resolved):
        raise BuildError(f"{field_name} '{rel_path}' does not exist")
    return resolved


def collect_image_entries(package_dir, metadata):
    """Return a list of (arcname, absolute_path) pairs for images to bundle.

    The featured image is required; the comparison image is bundled when
    present but is not referenced from frontmatter or the post body — its
    use is out of scope for this gate.
    """
    entries = []
    seen_arcnames = {}

    def add(rel_path, field_name):
        resolved = resolve_package_image(package_dir, rel_path, field_name)
        arcname = f"images/{os.path.basename(resolved)}"
        if arcname in seen_arcnames and seen_arcnames[arcname] != resolved:
            raise BuildError(
                f"{field_name}: filename collision for '{arcname}' between "
                "distinct source files"
            )
        seen_arcnames[arcname] = resolved
        entries.append((arcname, resolved))
        return arcname

    featured_arcname = add(metadata["featured_image"], "featured_image")

    if metadata.get("comparison_image"):
        add(metadata["comparison_image"], "comparison_image")

    return featured_arcname, entries


def render_post_md(package_dir, metadata):
    post_path = os.path.join(package_dir, "post.md")
    with open(post_path, "r", encoding="utf-8") as f:
        original = f.read()

    body = strip_leading_h1(original)

    marker_count = body.count(vcp.AD_MARKER)
    if marker_count != 1:
        raise BuildError(
            f"post.md: '{vcp.AD_MARKER}' must appear exactly once in the "
            f"converted body, found {marker_count}"
        )

    featured_arcname, image_entries = collect_image_entries(package_dir, metadata)
    frontmatter = build_frontmatter_text(metadata, featured_arcname)
    return frontmatter + "\n" + body, image_entries


def _zip_info(arcname):
    info = zipfile.ZipInfo(arcname, date_time=FIXED_ZIP_DATE_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    info.create_system = 0
    return info


def build_autoblog_package(package_dir, output_dir, force=False):
    """Validate and convert package_dir into an Auto-blog input ZIP.

    Returns the path to the generated ZIP. Raises BuildError on any
    validation or conversion failure; never leaves a partial ZIP behind.
    """
    result = vcp.validate_package(package_dir)
    if not result.ok:
        raise BuildError(
            "input package failed validate_content_package.py:\n"
            + "\n".join(f"  - {e}" for e in result.errors)
        )

    metadata = load_metadata(package_dir)
    post_md_text, image_entries = render_post_md(package_dir, metadata)

    output_path = os.path.join(output_dir, f"{metadata['slug']}.zip")
    if os.path.exists(output_path) and not force:
        raise BuildError(
            f"output already exists: {output_path} (pass --force to overwrite)"
        )

    os.makedirs(output_dir, exist_ok=True)
    fd, tmp_path = tempfile.mkstemp(
        dir=output_dir, prefix=".build_autoblog_package-", suffix=".zip.tmp"
    )
    os.close(fd)
    try:
        with zipfile.ZipFile(tmp_path, "w") as zf:
            zf.writestr(_zip_info("post.md"), post_md_text.encode("utf-8"))
            for arcname, path in sorted(image_entries, key=lambda e: e[0]):
                with open(path, "rb") as imgf:
                    data = imgf.read()
                zf.writestr(_zip_info(arcname), data)
        os.replace(tmp_path, output_path)
    except BaseException:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise

    return output_path


def main(argv):
    parser = argparse.ArgumentParser(
        description="Build an Auto-blog-compatible input ZIP from a content package."
    )
    parser.add_argument("package_dir", help="Path to a content-samples package directory")
    parser.add_argument(
        "--output", default="dist", help="Output directory for the generated ZIP (default: dist)"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing output ZIP instead of failing",
    )
    args = parser.parse_args(argv)

    if not os.path.isdir(args.package_dir):
        print(f"ERROR: {args.package_dir} is not a directory")
        return 1

    try:
        output_path = build_autoblog_package(args.package_dir, args.output, force=args.force)
    except BuildError as e:
        print(f"ERROR: {e}")
        return 1

    print(f"OK: wrote {output_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
