"""Tests for tools/validate_content_package.py.

Uses only the Python 3 standard library — no external dependencies.
Run with:
    python3 -m unittest discover -s tests
"""
import contextlib
import io
import json
import os
import struct
import sys
import tempfile
import unittest
import zlib

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)

import validate_content_package as vcp  # noqa: E402

VALID_TITLE = "テスト記事のタイトル"
VALID_SLUG = "test-article"
LONG_BODY = "これはテスト用の本文です。" * 170  # well over 2000 chars once whitespace-stripped


def png_bytes(width, height):
    """Build a minimal PNG (signature + IHDR only) with the given dimensions."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + crc
    return signature + chunk


def png_bytes_bad_chunk_type(width, height):
    """PNG signature followed by a first chunk that is not IHDR, but whose
    payload still holds width/height at the same byte offsets."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    crc = struct.pack(">I", zlib.crc32(b"IDAT" + ihdr_data) & 0xFFFFFFFF)
    chunk = struct.pack(">I", len(ihdr_data)) + b"IDAT" + ihdr_data + crc
    return signature + chunk


def png_bytes_bad_chunk_length(width, height):
    """PNG signature followed by an IHDR chunk whose declared length is
    wrong, while width/height still sit at the expected byte offsets."""
    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    crc = struct.pack(">I", zlib.crc32(b"IHDR" + ihdr_data) & 0xFFFFFFFF)
    chunk = struct.pack(">I", 20) + b"IHDR" + ihdr_data + crc
    return signature + chunk


def default_metadata():
    return {
        "title": VALID_TITLE,
        "slug": VALID_SLUG,
        "status": "draft",
        "categories": ["カテゴリー"],
        "description": "テスト用の説明文です。",
        "featured_image": "images/featured.png",
        "comparison_image": "images/comparison.png",
        "middle_ad_marker": vcp.AD_MARKER,
    }


def write_metadata(pkg_dir, metadata=None, raw_text=None):
    with open(os.path.join(pkg_dir, "metadata.json"), "w", encoding="utf-8") as f:
        if raw_text is not None:
            f.write(raw_text)
        else:
            json.dump(metadata, f, ensure_ascii=False)


def write_post(pkg_dir, title=VALID_TITLE, marker_count=1, body=LONG_BODY):
    marker_block = "\n\n".join([vcp.AD_MARKER] * marker_count)
    text = (
        f"# {title}\n\n{body}\n\n"
        f"## 見出し1\n\n{body}\n\n"
        f"{marker_block}\n\n"
        f"## 見出し2\n\nまとめです。\n"
    )
    with open(os.path.join(pkg_dir, "post.md"), "w", encoding="utf-8") as f:
        f.write(text)


def write_source_notes(pkg_dir, text=None):
    if text is None:
        text = "## 出典\n\nhttps://example.com/reference\n\n参照日: 2026-06-28\n"
    with open(os.path.join(pkg_dir, "source-notes.md"), "w", encoding="utf-8") as f:
        f.write(text)


def write_readme(pkg_dir):
    with open(os.path.join(pkg_dir, "README.md"), "w", encoding="utf-8") as f:
        f.write("# テストパッケージ\n")


def write_png(pkg_dir, rel_path, width, height):
    path = os.path.join(pkg_dir, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(png_bytes(width, height))


def write_png_bytes(pkg_dir, rel_path, data):
    path = os.path.join(pkg_dir, rel_path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(data)


def build_valid_package(pkg_dir):
    os.makedirs(pkg_dir, exist_ok=True)
    write_metadata(pkg_dir, default_metadata())
    write_post(pkg_dir)
    write_source_notes(pkg_dir)
    write_readme(pkg_dir)
    write_png(pkg_dir, "images/featured.png", 1200, 630)
    write_png(pkg_dir, "images/comparison.png", 1200, 800)


class ValidateContentPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pkg_dir = os.path.join(self.tmp.name, "pkg")
        build_valid_package(self.pkg_dir)

    def test_valid_package_passes(self):
        result = vcp.validate_package(self.pkg_dir)
        self.assertEqual(result.errors, [])

    def test_missing_required_file_fails(self):
        os.remove(os.path.join(self.pkg_dir, "README.md"))
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("README.md" in e for e in result.errors))

    def test_invalid_json_fails(self):
        write_metadata(self.pkg_dir, raw_text="{ this is not valid json")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("invalid JSON" in e for e in result.errors))

    def test_ad_marker_missing_fails(self):
        write_post(self.pkg_dir, marker_count=0)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any(vcp.AD_MARKER in e for e in result.errors))

    def test_ad_marker_duplicated_fails(self):
        write_post(self.pkg_dir, marker_count=2)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any(vcp.AD_MARKER in e for e in result.errors))

    def test_title_mismatch_fails(self):
        write_post(self.pkg_dir, title="別のタイトル")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("does not match" in e for e in result.errors))

    def test_status_not_draft_fails(self):
        metadata = default_metadata()
        metadata["status"] = "publish"
        write_metadata(self.pkg_dir, metadata)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("status" in e for e in result.errors))

    def test_missing_image_reference_fails(self):
        os.remove(os.path.join(self.pkg_dir, "images", "featured.png"))
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("featured_image" in e for e in result.errors))

    def test_png_dimension_mismatch_fails(self):
        write_png(self.pkg_dir, "images/featured.png", 800, 600)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("expected size" in e for e in result.errors))

    def test_path_traversal_fails(self):
        metadata = default_metadata()
        metadata["featured_image"] = "../outside.png"
        write_metadata(self.pkg_dir, metadata)
        outside_path = os.path.join(self.tmp.name, "outside.png")
        with open(outside_path, "wb") as f:
            f.write(png_bytes(1200, 630))
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("safe path" in e for e in result.errors))

    def test_absolute_path_image_fails(self):
        metadata = default_metadata()
        metadata["featured_image"] = "/etc/hostname"
        write_metadata(self.pkg_dir, metadata)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("safe path" in e for e in result.errors))

    def test_slug_with_uppercase_fails(self):
        metadata = default_metadata()
        metadata["slug"] = "Invalid_Slug"
        write_metadata(self.pkg_dir, metadata)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("slug" in e for e in result.errors))

    def test_empty_categories_fails(self):
        metadata = default_metadata()
        metadata["categories"] = []
        write_metadata(self.pkg_dir, metadata)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("categories" in e for e in result.errors))

    def test_short_body_fails(self):
        write_post(self.pkg_dir, body="短い本文です。")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("too short" in e for e in result.errors))

    def test_missing_h1_fails(self):
        with open(os.path.join(self.pkg_dir, "post.md"), "w", encoding="utf-8") as f:
            f.write(f"## 見出しのみ\n\n{LONG_BODY}\n\n{vcp.AD_MARKER}\n")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("H1" in e for e in result.errors))

    def test_missing_h2_fails(self):
        with open(os.path.join(self.pkg_dir, "post.md"), "w", encoding="utf-8") as f:
            f.write(f"# {VALID_TITLE}\n\n{LONG_BODY}\n\n{vcp.AD_MARKER}\n")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("H2" in e for e in result.errors))

    def test_missing_source_url_fails(self):
        write_source_notes(self.pkg_dir, text="参照日: 2026-06-28\nURLはありません。\n")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("URL" in e for e in result.errors))

    def test_missing_reference_date_fails(self):
        write_source_notes(self.pkg_dir, text="https://example.com/reference\n")
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("参照日" in e for e in result.errors))

    def test_unconfirmed_marker_produces_warning_not_failure(self):
        write_source_notes(
            self.pkg_dir,
            text="https://example.com/reference\n参照日: 2026-06-28\n未確認の情報あり。\n",
        )
        result = vcp.validate_package(self.pkg_dir)
        self.assertTrue(result.ok)
        self.assertTrue(any("未確認" in w for w in result.warnings))

    def test_comparison_image_dimension_mismatch_fails(self):
        write_png(self.pkg_dir, "images/comparison.png", 1200, 630)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("expected size" in e for e in result.errors))

    def test_comparison_image_optional(self):
        metadata = default_metadata()
        del metadata["comparison_image"]
        write_metadata(self.pkg_dir, metadata)
        os.remove(os.path.join(self.pkg_dir, "images", "comparison.png"))
        result = vcp.validate_package(self.pkg_dir)
        self.assertTrue(result.ok)

    def test_empty_image_file_fails(self):
        open(os.path.join(self.pkg_dir, "images", "featured.png"), "wb").close()
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("empty" in e for e in result.errors))

    def test_png_wrong_chunk_type_fails(self):
        write_png_bytes(
            self.pkg_dir,
            "images/featured.png",
            png_bytes_bad_chunk_type(1200, 630),
        )
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("not a valid PNG file" in e for e in result.errors))

    def test_png_wrong_chunk_length_fails(self):
        write_png_bytes(
            self.pkg_dir,
            "images/featured.png",
            png_bytes_bad_chunk_length(1200, 630),
        )
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("not a valid PNG file" in e for e in result.errors))

    def test_png_non_positive_dimensions_fails(self):
        write_png(self.pkg_dir, "images/featured.png", 0, 630)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("not a valid PNG file" in e for e in result.errors))

    def test_symlink_escape_fails(self):
        outside_path = os.path.join(self.tmp.name, "outside.png")
        with open(outside_path, "wb") as f:
            f.write(png_bytes(1200, 630))
        link_path = os.path.join(self.pkg_dir, "images", "featured_link.png")
        try:
            os.symlink(outside_path, link_path)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks are not supported on this platform")
        metadata = default_metadata()
        metadata["featured_image"] = "images/featured_link.png"
        write_metadata(self.pkg_dir, metadata)
        result = vcp.validate_package(self.pkg_dir)
        self.assertFalse(result.ok)
        self.assertTrue(any("safe path" in e for e in result.errors))


class CliTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def test_main_exits_zero_on_pass(self):
        pkg_dir = os.path.join(self.tmp.name, "pkg")
        build_valid_package(pkg_dir)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = vcp.main([pkg_dir])
        self.assertEqual(exit_code, 0)
        self.assertIn("PASS", stdout.getvalue())

    def test_main_exits_one_on_fail(self):
        pkg_dir = os.path.join(self.tmp.name, "pkg")
        build_valid_package(pkg_dir)
        os.remove(os.path.join(pkg_dir, "README.md"))
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = vcp.main([pkg_dir])
        self.assertEqual(exit_code, 1)
        self.assertIn("FAIL", stdout.getvalue())

    def test_main_validates_all_packages_under_parent_directory(self):
        parent_dir = os.path.join(self.tmp.name, "content-samples")
        build_valid_package(os.path.join(parent_dir, "article-a"))
        build_valid_package(os.path.join(parent_dir, "article-b"))
        os.remove(os.path.join(parent_dir, "article-b", "README.md"))
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = vcp.main([parent_dir])
        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("PASS: article-a", output)
        self.assertIn("FAIL: article-b", output)

    def test_main_flags_package_missing_metadata_under_parent_directory(self):
        parent_dir = os.path.join(self.tmp.name, "content-samples")
        build_valid_package(os.path.join(parent_dir, "article-a"))
        no_metadata_dir = os.path.join(parent_dir, "article-no-metadata")
        os.makedirs(no_metadata_dir)
        write_post(no_metadata_dir)
        write_source_notes(no_metadata_dir)
        write_readme(no_metadata_dir)
        # metadata.json is intentionally missing.
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = vcp.main([parent_dir])
        output = stdout.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("PASS: article-a", output)
        self.assertIn("FAIL: article-no-metadata", output)
        self.assertIn("metadata.json: required file is missing", output)

    def test_main_reports_error_when_no_package_found(self):
        empty_dir = os.path.join(self.tmp.name, "empty")
        os.makedirs(empty_dir)
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            exit_code = vcp.main([empty_dir])
        self.assertEqual(exit_code, 1)
        self.assertIn("no content package found", stdout.getvalue())


class GoldenArticlePackageTests(unittest.TestCase):
    """Integration check: the real golden-article-001 sample must pass."""

    def test_golden_article_001_passes(self):
        golden_dir = os.path.join(REPO_ROOT, "content-samples", "golden-article-001")
        self.assertTrue(os.path.isdir(golden_dir), f"{golden_dir} does not exist")
        result = vcp.validate_package(golden_dir)
        self.assertEqual(result.errors, [], f"golden-article-001 failed: {result.errors}")


if __name__ == "__main__":
    unittest.main()
