#!/usr/bin/env python3
"""Tests for build_autoblog_package.py.

Tests the Golden Article to Auto-blog ZIP conversion adapter.
"""
import json
import os
import re
import shutil
import sys
import tempfile
import unittest
import zipfile

# Add tools directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tools"))

from build_autoblog_package import (
    build_autoblog_zip,
    build_frontmatter,
    collect_images,
    escape_yaml_string,
    remove_h1_from_body,
    resolve_safe_path,
    validate_ad_marker,
)

# Path to golden article for integration tests
GOLDEN_ARTICLE_DIR = os.path.join(
    os.path.dirname(__file__), "..", "content-samples", "golden-article-001"
)

AD_MARKER = "<!-- acourt-ad-middle -->"


class TestEscapeYamlString(unittest.TestCase):
    """Test YAML string escaping."""
    
    def test_plain_string(self):
        self.assertEqual(escape_yaml_string("hello"), "hello")
    
    def test_string_with_colon(self):
        result = escape_yaml_string("foo: bar")
        self.assertTrue(result.startswith('"'))
        self.assertTrue(result.endswith('"'))
    
    def test_string_with_quotes(self):
        result = escape_yaml_string('say "hello"')
        self.assertIn('\\"', result)
    
    def test_string_with_leading_dash(self):
        result = escape_yaml_string("- list item")
        self.assertTrue(result.startswith('"'))


class TestRemoveH1(unittest.TestCase):
    """Test H1 removal from body."""
    
    def test_removes_h1_at_start(self):
        body = "# Title Here\n\nSome content"
        result = remove_h1_from_body(body)
        self.assertNotIn("# Title Here", result)
        self.assertIn("Some content", result)
    
    def test_preserves_h2(self):
        body = "# Title\n\n## Section\n\nContent"
        result = remove_h1_from_body(body)
        self.assertIn("## Section", result)
    
    def test_only_removes_first_h1(self):
        body = "# First\n\n# Second\n\nContent"
        result = remove_h1_from_body(body)
        self.assertNotIn("# First", result)
        self.assertIn("# Second", result)
    
    def test_handles_whitespace(self):
        body = "\n\n# Title\n\nContent"
        result = remove_h1_from_body(body)
        self.assertNotIn("# Title", result)


class TestValidateAdMarker(unittest.TestCase):
    """Test ad marker validation."""
    
    def test_exactly_one_marker(self):
        body = f"Content before\n{AD_MARKER}\nContent after"
        self.assertTrue(validate_ad_marker(body))
    
    def test_no_marker_raises(self):
        body = "Content without marker"
        with self.assertRaises(ValueError):
            validate_ad_marker(body)
    
    def test_multiple_markers_raises(self):
        body = f"{AD_MARKER}\n{AD_MARKER}"
        with self.assertRaises(ValueError):
            validate_ad_marker(body)


class TestResolveSafePath(unittest.TestCase):
    """Test path safety validation."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "images"))
        # Create a test file
        with open(os.path.join(self.temp_dir, "images", "test.png"), "w") as f:
            f.write("test")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_valid_relative_path(self):
        result = resolve_safe_path(self.temp_dir, "images/test.png")
        self.assertIsNotNone(result)
    
    def test_rejects_absolute_path(self):
        result = resolve_safe_path(self.temp_dir, "/etc/passwd")
        self.assertIsNone(result)
    
    def test_rejects_parent_traversal(self):
        result = resolve_safe_path(self.temp_dir, "../../../etc/passwd")
        self.assertIsNone(result)
    
    def test_rejects_empty_path(self):
        result = resolve_safe_path(self.temp_dir, "")
        self.assertIsNone(result)


class TestBuildFrontmatter(unittest.TestCase):
    """Test frontmatter generation."""
    
    def test_includes_required_fields(self):
        metadata = {
            "title": "Test Title",
            "slug": "test-slug",
            "status": "draft",
            "categories": ["基礎知識"],
            "description": "Test description",
            "featured_image": "images/test.png",
        }
        result = build_frontmatter(metadata)
        self.assertIn("title:", result)
        self.assertIn("slug: test-slug", result)
        self.assertIn("status: draft", result)
    
    def test_forces_draft_status(self):
        metadata = {
            "title": "Test",
            "slug": "test",
            "status": "publish",  # Should be overridden
            "categories": ["Test"],
        }
        result = build_frontmatter(metadata)
        self.assertIn("status: draft", result)
        self.assertNotIn("status: publish", result)
    
    def test_categories_as_array(self):
        metadata = {
            "title": "Test",
            "slug": "test",
            "categories": ["Cat1", "Cat2"],
        }
        result = build_frontmatter(metadata)
        self.assertIn("categories:", result)
        self.assertIn("  - Cat1", result)
        self.assertIn("  - Cat2", result)
    
    def test_starts_and_ends_with_dashes(self):
        metadata = {"title": "Test", "slug": "test", "categories": []}
        result = build_frontmatter(metadata)
        self.assertTrue(result.startswith("---"))
        self.assertTrue(result.endswith("---"))


class TestCollectImages(unittest.TestCase):
    """Test image collection."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "images"))
        # Create test images
        for name in ["featured.png", "comparison.png"]:
            with open(os.path.join(self.temp_dir, "images", name), "wb") as f:
                f.write(b"fake image data")
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
    
    def test_collects_featured_image(self):
        metadata = {"featured_image": "images/featured.png"}
        result = collect_images(self.temp_dir, metadata)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], "images/featured.png")
    
    def test_collects_both_images(self):
        metadata = {
            "featured_image": "images/featured.png",
            "comparison_image": "images/comparison.png",
        }
        result = collect_images(self.temp_dir, metadata)
        self.assertEqual(len(result), 2)
    
    def test_missing_image_raises(self):
        metadata = {"featured_image": "images/nonexistent.png"}
        with self.assertRaises(FileNotFoundError):
            collect_images(self.temp_dir, metadata)
    
    def test_unsafe_path_raises(self):
        metadata = {"featured_image": "../../../etc/passwd"}
        with self.assertRaises(ValueError):
            collect_images(self.temp_dir, metadata)


class TestGoldenArticleIntegration(unittest.TestCase):
    """Integration tests using the actual golden article."""
    
    @classmethod
    def setUpClass(cls):
        """Check if golden article exists."""
        if not os.path.isdir(GOLDEN_ARTICLE_DIR):
            raise unittest.SkipTest(
                f"Golden article not found: {GOLDEN_ARTICLE_DIR}"
            )
    
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.output_dir)
    
    def test_1_creates_zip_successfully(self):
        """Test 1: Golden ArticleからZIP生成成功"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        self.assertTrue(os.path.isfile(output_path))
        self.assertTrue(output_path.endswith(".zip"))
    
    def test_2_zip_contains_post_md_at_root(self):
        """Test 2: ZIPルートにpost.mdが存在"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        with zipfile.ZipFile(output_path, "r") as zf:
            self.assertIn("post.md", zf.namelist())
    
    def test_3_frontmatter_matches_metadata(self):
        """Test 3: frontmatterのtitle/slug/description/categories/featured_imageがmetadataと一致"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        
        # Load original metadata
        with open(os.path.join(GOLDEN_ARTICLE_DIR, "metadata.json")) as f:
            metadata = json.load(f)
        
        # Extract frontmatter from generated post.md
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
        
        # Check each field
        self.assertIn(f"title: {metadata['title']}", content)
        self.assertIn(f"slug: {metadata['slug']}", content)
        self.assertIn(metadata["description"], content)
        for cat in metadata["categories"]:
            self.assertIn(cat, content)
        self.assertIn(metadata["featured_image"], content)
    
    def test_4_status_is_always_draft(self):
        """Test 4: statusが必ずdraft"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
        
        self.assertIn("status: draft", content)
        self.assertNotIn("status: publish", content)
    
    def test_5_h1_removed_from_body(self):
        """Test 5: 元H1が本文から除去される"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
        
        # Split into frontmatter and body
        parts = content.split("---")
        body = "---".join(parts[2:])  # Everything after second ---
        
        # Body should not start with H1
        h1_pattern = r"^\s*#\s+[^\n]+"
        self.assertIsNone(re.match(h1_pattern, body.strip()))
        
        # But H2 should still be present
        self.assertIn("## ", body)
    
    def test_6_ad_marker_appears_exactly_once(self):
        """Test 6: 広告マーカーがちょうど1回"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
        
        self.assertEqual(content.count(AD_MARKER), 1)
    
    def test_7_images_included(self):
        """Test 7: featured imageとcomparison imageが同梱される"""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        
        with open(os.path.join(GOLDEN_ARTICLE_DIR, "metadata.json")) as f:
            metadata = json.load(f)
        
        with zipfile.ZipFile(output_path, "r") as zf:
            names = zf.namelist()
            self.assertIn(metadata["featured_image"], names)
            if metadata.get("comparison_image"):
                self.assertIn(metadata["comparison_image"], names)
    
    def test_12_overwrite_fails_without_force(self):
        """Test 12: 既存出力への上書きをfail-closed"""
        # Create first
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        self.assertTrue(os.path.exists(output_path))
        
        # Try to create again without force
        with self.assertRaises(FileExistsError):
            build_autoblog_zip(GOLDEN_ARTICLE_DIR, self.output_dir)
    
    def test_13_deterministic_output(self):
        """Test 13: 同一入力からの出力内容が決定的"""
        # Create twice
        dir1 = tempfile.mkdtemp()
        dir2 = tempfile.mkdtemp()
        try:
            path1 = build_autoblog_zip(GOLDEN_ARTICLE_DIR, dir1)
            path2 = build_autoblog_zip(GOLDEN_ARTICLE_DIR, dir2)
            
            # Compare contents
            with open(path1, "rb") as f1, open(path2, "rb") as f2:
                self.assertEqual(f1.read(), f2.read())
        finally:
            shutil.rmtree(dir1)
            shutil.rmtree(dir2)


class TestMissingMetadataErrors(unittest.TestCase):
    """Test error handling for missing/invalid metadata."""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_dir = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_dir, "images"))
    
    def tearDown(self):
        shutil.rmtree(self.temp_dir)
        shutil.rmtree(self.output_dir)
    
    def _create_package(self, metadata, post_content=None):
        """Helper to create a test package."""
        # metadata.json
        with open(os.path.join(self.temp_dir, "metadata.json"), "w") as f:
            json.dump(metadata, f)
        
        # post.md
        if post_content is None:
            post_content = f"# Test Title\n\nContent here.\n\n{AD_MARKER}\n\nMore content." + "x" * 2000
        with open(os.path.join(self.temp_dir, "post.md"), "w") as f:
            f.write(post_content)
        
        # source-notes.md
        with open(os.path.join(self.temp_dir, "source-notes.md"), "w") as f:
            f.write("Source: https://example.com\n参照日: 2025-01-01")
        
        # README.md
        with open(os.path.join(self.temp_dir, "README.md"), "w") as f:
            f.write("# README")
    
    def test_8_missing_required_metadata_fails(self):
        """Test 8: 必須metadata欠損時に失敗"""
        # Missing title
        metadata = {
            "slug": "test",
            "status": "draft",
            "categories": ["Test"],
            "description": "Test",
            "featured_image": "images/test.png",
            "middle_ad_marker": AD_MARKER,
        }
        self._create_package(metadata)
        
        with self.assertRaises(ValueError) as ctx:
            build_autoblog_zip(self.temp_dir, self.output_dir)
        self.assertIn("validation failed", str(ctx.exception).lower())
    
    def test_9_missing_image_fails(self):
        """Test 9: 参照画像欠損時に失敗"""
        metadata = {
            "title": "Test",
            "slug": "test",
            "status": "draft",
            "categories": ["Test"],
            "description": "Test",
            "featured_image": "images/nonexistent.png",
            "middle_ad_marker": AD_MARKER,
        }
        self._create_package(metadata)
        
        with self.assertRaises((ValueError, FileNotFoundError)):
            build_autoblog_zip(self.temp_dir, self.output_dir)
    
    def test_10_unsafe_path_rejected(self):
        """Test 10: unsafe pathを拒否"""
        metadata = {
            "title": "Test",
            "slug": "test",
            "status": "draft",
            "categories": ["Test"],
            "description": "Test",
            "featured_image": "../../../etc/passwd",
            "middle_ad_marker": AD_MARKER,
        }
        self._create_package(metadata)
        
        with self.assertRaises(ValueError):
            build_autoblog_zip(self.temp_dir, self.output_dir)
    
    def test_11_publish_status_forced_to_draft(self):
        """Test 11: 不正statusを渡しても公開用出力を作らない"""
        # This is already tested in test_4, but we verify explicitly
        # that even if metadata has publish, output is draft
        metadata = {
            "title": "Test",
            "slug": "test",
            "status": "publish",  # Invalid - should be forced to draft
            "categories": ["Test"],
            "description": "Test",
            "featured_image": "images/test.png",
            "middle_ad_marker": AD_MARKER,
        }
        self._create_package(metadata)
        
        # Create a valid image
        # Note: validation will fail due to status != draft
        with self.assertRaises(ValueError) as ctx:
            build_autoblog_zip(self.temp_dir, self.output_dir)
        # The validation script should catch status != draft
        self.assertIn("validation failed", str(ctx.exception).lower())


class TestAutoBlogContractCompliance(unittest.TestCase):
    """Test that output meets Auto-blog input contract."""
    
    def setUp(self):
        self.output_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.output_dir)
    
    @unittest.skipIf(
        not os.path.isdir(GOLDEN_ARTICLE_DIR),
        "Golden article not found"
    )
    def test_yaml_frontmatter_parseable(self):
        """Output post.md has valid YAML frontmatter."""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
        
        # Check frontmatter structure
        self.assertTrue(content.startswith("---"))
        parts = content.split("---")
        self.assertGreaterEqual(len(parts), 3)
        
        # Frontmatter should be parseable (basic check)
        frontmatter = parts[1]
        self.assertIn("title:", frontmatter)
        self.assertIn("slug:", frontmatter)
    
    @unittest.skipIf(
        not os.path.isdir(GOLDEN_ARTICLE_DIR),
        "Golden article not found"
    )
    def test_slug_format_valid(self):
        """Slug contains only lowercase letters, digits, and hyphens."""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
        
        # Extract slug from frontmatter
        match = re.search(r"slug:\s*(\S+)", content)
        self.assertIsNotNone(match)
        slug = match.group(1)
        self.assertRegex(slug, r"^[a-z0-9-]+$")
    
    @unittest.skipIf(
        not os.path.isdir(GOLDEN_ARTICLE_DIR),
        "Golden article not found"
    )
    def test_utf8_encoding(self):
        """Output is valid UTF-8."""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        
        with zipfile.ZipFile(output_path, "r") as zf:
            content_bytes = zf.read("post.md")
        
        # Should not raise
        content_bytes.decode("utf-8")
    
    @unittest.skipIf(
        not os.path.isdir(GOLDEN_ARTICLE_DIR),
        "Golden article not found"
    )
    def test_featured_image_exists_in_zip(self):
        """Featured image path in frontmatter exists in ZIP."""
        output_path = build_autoblog_zip(
            GOLDEN_ARTICLE_DIR, self.output_dir
        )
        
        with zipfile.ZipFile(output_path, "r") as zf:
            content = zf.read("post.md").decode("utf-8")
            names = zf.namelist()
        
        # Extract featured_image from frontmatter
        match = re.search(r"featured_image:\s*(\S+)", content)
        self.assertIsNotNone(match)
        featured_image = match.group(1)
        self.assertIn(featured_image, names)


if __name__ == "__main__":
    unittest.main()
