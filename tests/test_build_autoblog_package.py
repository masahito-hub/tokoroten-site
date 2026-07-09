"""Tests for tools/build_autoblog_package.py.

Uses only the Python 3 standard library — no external dependencies.
Run with:
    python3 -m unittest discover -s tests
"""
import glob
import hashlib
import os
import sys
import tempfile
import unittest
import zipfile

TESTS_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(TESTS_DIR)
TOOLS_DIR = os.path.join(REPO_ROOT, "tools")
sys.path.insert(0, TOOLS_DIR)
sys.path.insert(0, TESTS_DIR)

import build_autoblog_package as bap  # noqa: E402
import test_validate_content_package as tvcp  # noqa: E402


def parse_generated_frontmatter(post_md_text):
    """Minimal parser for the frontmatter this adapter itself generates.

    Not a stand-in for Auto-blog's own parser — see
    tests/test_autoblog_contract.py for the independent contract check.
    """
    assert post_md_text.startswith("---\n")
    end = post_md_text.index("\n---\n", 4)
    raw_fm = post_md_text[4:end]
    body = post_md_text[end + len("\n---\n"):]

    data = {}
    lines = raw_fm.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if ":" not in line:
            i += 1
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        if value == "":
            items = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                items.append(_unquote(lines[j][4:]))
                j += 1
            data[key] = items
            i = j
            continue
        data[key] = _unquote(value)
        i += 1
    return data, body


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        inner = value[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return value


class BuildAutoblogPackageTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pkg_dir = os.path.join(self.tmp.name, "pkg")
        tvcp.build_valid_package(self.pkg_dir)
        self.output_dir = os.path.join(self.tmp.name, "dist")

    def test_build_succeeds_and_zip_root_has_post_md(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        self.assertTrue(os.path.isfile(output_path))
        with zipfile.ZipFile(output_path) as zf:
            self.assertIn("post.md", zf.namelist())

    def test_frontmatter_matches_metadata(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        metadata = tvcp.default_metadata()
        with zipfile.ZipFile(output_path) as zf:
            post_text = zf.read("post.md").decode("utf-8")
        data, _ = parse_generated_frontmatter(post_text)
        self.assertEqual(data["title"], metadata["title"])
        self.assertEqual(data["slug"], metadata["slug"])
        self.assertEqual(data["description"], metadata["description"])
        self.assertEqual(data["categories"], metadata["categories"])
        self.assertEqual(data["featured_image"], "images/featured.png")

    def test_status_always_draft_in_generated_output(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with zipfile.ZipFile(output_path) as zf:
            post_text = zf.read("post.md").decode("utf-8")
        data, _ = parse_generated_frontmatter(post_text)
        self.assertEqual(data["status"], "draft")

    def test_status_forced_draft_even_if_metadata_tampered(self):
        # Defense-in-depth: build_frontmatter_text() itself must never trust
        # metadata['status'], independent of validate_content_package's own
        # (also enforced) rejection of non-draft status.
        metadata = tvcp.default_metadata()
        metadata["status"] = "publish"
        text = bap.build_frontmatter_text(metadata, "images/featured.png")
        self.assertIn('status: "draft"', text)
        self.assertNotIn("publish", text)

    def test_h1_removed_from_output_body(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with zipfile.ZipFile(output_path) as zf:
            post_text = zf.read("post.md").decode("utf-8")
        _, body = parse_generated_frontmatter(post_text)
        self.assertNotIn(f"# {tvcp.VALID_TITLE}", body)

    def test_ad_marker_exactly_once_in_output(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with zipfile.ZipFile(output_path) as zf:
            post_text = zf.read("post.md").decode("utf-8")
        self.assertEqual(post_text.count(bap.vcp.AD_MARKER), 1)

    def test_featured_and_comparison_images_bundled(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with zipfile.ZipFile(output_path) as zf:
            names = zf.namelist()
        self.assertIn("images/featured.png", names)
        self.assertIn("images/comparison.png", names)

    def test_extra_package_files_not_included(self):
        output_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with zipfile.ZipFile(output_path) as zf:
            names = zf.namelist()
        self.assertNotIn("metadata.json", names)
        self.assertNotIn("source-notes.md", names)
        self.assertNotIn("README.md", names)

    def test_missing_required_metadata_fails(self):
        metadata = tvcp.default_metadata()
        del metadata["title"]
        tvcp.write_metadata(self.pkg_dir, metadata)
        with self.assertRaises(bap.BuildError):
            bap.build_autoblog_package(self.pkg_dir, self.output_dir)

    def test_missing_referenced_image_fails(self):
        os.remove(os.path.join(self.pkg_dir, "images", "featured.png"))
        with self.assertRaises(bap.BuildError):
            bap.build_autoblog_package(self.pkg_dir, self.output_dir)

    def test_unsafe_path_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as other_tmp:
            with self.assertRaises(bap.BuildError):
                bap.resolve_package_image(other_tmp, "../outside.png", "featured_image")

    def test_unsafe_absolute_path_rejected(self):
        with tempfile.TemporaryDirectory() as other_tmp:
            with self.assertRaises(bap.BuildError):
                bap.resolve_package_image(other_tmp, "/etc/hostname", "featured_image")

    def test_invalid_status_produces_no_output(self):
        metadata = tvcp.default_metadata()
        metadata["status"] = "publish"
        tvcp.write_metadata(self.pkg_dir, metadata)
        with self.assertRaises(bap.BuildError):
            bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        self.assertFalse(os.path.isdir(self.output_dir) and os.listdir(self.output_dir))

    def test_existing_output_fails_closed_without_force(self):
        first_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with open(first_path, "rb") as f:
            original_bytes = f.read()
        with self.assertRaises(bap.BuildError):
            bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        with open(first_path, "rb") as f:
            self.assertEqual(f.read(), original_bytes)

    def test_existing_output_overwritable_with_force(self):
        first_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        second_path = bap.build_autoblog_package(self.pkg_dir, self.output_dir, force=True)
        self.assertEqual(first_path, second_path)

    def test_build_is_deterministic(self):
        output_dir_a = os.path.join(self.tmp.name, "dist-a")
        output_dir_b = os.path.join(self.tmp.name, "dist-b")
        path_a = bap.build_autoblog_package(self.pkg_dir, output_dir_a)
        path_b = bap.build_autoblog_package(self.pkg_dir, output_dir_b)
        with open(path_a, "rb") as f:
            digest_a = hashlib.sha256(f.read()).hexdigest()
        with open(path_b, "rb") as f:
            digest_b = hashlib.sha256(f.read()).hexdigest()
        self.assertEqual(digest_a, digest_b)

    def test_failed_build_leaves_no_temp_files(self):
        os.remove(os.path.join(self.pkg_dir, "images", "featured.png"))
        with self.assertRaises(bap.BuildError):
            bap.build_autoblog_package(self.pkg_dir, self.output_dir)
        leftovers = glob.glob(os.path.join(self.output_dir, ".build_autoblog_package-*"))
        self.assertEqual(leftovers, [])
        self.assertFalse(os.path.exists(os.path.join(self.output_dir, "test-article.zip")))


class GoldenArticleAutoblogPackageTests(unittest.TestCase):
    """Integration check: the real golden-article-001 sample must convert."""

    def test_golden_article_001_builds(self):
        golden_dir = os.path.join(REPO_ROOT, "content-samples", "golden-article-001")
        self.assertTrue(os.path.isdir(golden_dir), f"{golden_dir} does not exist")
        with tempfile.TemporaryDirectory() as output_dir:
            output_path = bap.build_autoblog_package(golden_dir, output_dir)
            self.assertTrue(os.path.isfile(output_path))
            with zipfile.ZipFile(output_path) as zf:
                names = zf.namelist()
                self.assertIn("post.md", names)
                self.assertIn("images/tokoroten_golden_featured.png", names)
                self.assertIn("images/tokoroten_golden_comparison.png", names)
                post_text = zf.read("post.md").decode("utf-8")
            self.assertEqual(post_text.count(bap.vcp.AD_MARKER), 1)
            self.assertNotIn("# ところてんと寒天は何が違う？", post_text)


if __name__ == "__main__":
    unittest.main()
