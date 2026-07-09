"""Local contract test for Auto-blog's post.md input format.

This repository does not check out the Auto-blog repository during CI (an
external-repo checkout in this CI was judged too unstable — see
docs/AUTOBLOG_PACKAGE.md), so this test re-implements a minimal,
independent reading of Auto-blog's *documented* input contract instead of
importing Auto-blog's own parse_post_md():

  - post.md must start with a "---" delimited YAML frontmatter block
  - "title" and "slug" are required and non-empty
  - "slug" must be a valid URL slug (lowercase letters/digits/hyphens)
  - the file must be valid UTF-8
  - "featured_image", when present, must resolve to a file inside the ZIP

This parser is deliberately independent of tools/build_autoblog_package.py's
own frontmatter generator so this test cannot pass merely by mirroring a bug
in the generator. If Auto-blog's actual contract changes, update this parser
and docs/AUTOBLOG_PACKAGE.md together.

Uses only the Python 3 standard library — no external dependencies.
"""
import os
import re
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

FRONTMATTER_RE = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n(.*)\Z", re.DOTALL)
SLUG_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


class ContractViolation(Exception):
    pass


def parse_post_md_contract(raw_bytes):
    """Parse post.md bytes the way Auto-blog's documented contract requires.

    Raises ContractViolation on any breach of the documented contract.
    Returns (frontmatter_dict, body_text) on success.
    """
    try:
        text = raw_bytes.decode("utf-8")
    except UnicodeDecodeError as e:
        raise ContractViolation(f"post.md is not valid UTF-8: {e}")

    match = FRONTMATTER_RE.match(text)
    if not match:
        raise ContractViolation("post.md must start with '---' delimited YAML frontmatter")
    raw_fm, body = match.group(1), match.group(2)

    frontmatter = {}
    lines = raw_fm.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        m = re.match(r"^([A-Za-z_][A-Za-z0-9_]*):\s*(.*)$", line)
        if not m:
            raise ContractViolation(f"unparseable frontmatter line: {line!r}")
        key, value = m.group(1), m.group(2)
        if value == "":
            items = []
            j = i + 1
            while j < len(lines) and lines[j].startswith("  - "):
                items.append(_unquote(lines[j][4:]))
                j += 1
            frontmatter[key] = items
            i = j
            continue
        frontmatter[key] = _unquote(value)
        i += 1

    if not frontmatter.get("title"):
        raise ContractViolation("frontmatter is missing required non-empty 'title'")
    if not frontmatter.get("slug"):
        raise ContractViolation("frontmatter is missing required non-empty 'slug'")
    if not SLUG_RE.match(frontmatter["slug"]):
        raise ContractViolation(f"'slug' is not a valid slug: {frontmatter['slug']!r}")

    return frontmatter, body


def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        inner = value[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return value


class AutoblogContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.pkg_dir = os.path.join(self.tmp.name, "pkg")
        tvcp.build_valid_package(self.pkg_dir)
        self.output_dir = os.path.join(self.tmp.name, "dist")

    def _build_and_parse(self, pkg_dir=None):
        output_path = bap.build_autoblog_package(pkg_dir or self.pkg_dir, self.output_dir)
        with zipfile.ZipFile(output_path) as zf:
            names = set(zf.namelist())
            post_bytes = zf.read("post.md")
        frontmatter, body = parse_post_md_contract(post_bytes)
        return frontmatter, body, names

    def test_generated_post_md_satisfies_autoblog_contract(self):
        frontmatter, _, names = self._build_and_parse()
        self.assertTrue(frontmatter["title"])
        self.assertTrue(frontmatter["slug"])
        self.assertRegex(frontmatter["slug"], SLUG_RE)
        self.assertEqual(frontmatter["status"], "draft")

    def test_featured_image_path_exists_inside_zip(self):
        frontmatter, _, names = self._build_and_parse()
        featured_image = frontmatter.get("featured_image")
        self.assertIsNotNone(featured_image)
        self.assertIn(featured_image, names)

    def test_golden_article_001_satisfies_autoblog_contract(self):
        golden_dir = os.path.join(REPO_ROOT, "content-samples", "golden-article-001")
        frontmatter, _, names = self._build_and_parse(pkg_dir=golden_dir)
        self.assertEqual(frontmatter["slug"], "tokoroten-vs-kanten")
        self.assertEqual(frontmatter["status"], "draft")
        self.assertIn(frontmatter["featured_image"], names)


if __name__ == "__main__":
    unittest.main()
