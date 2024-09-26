import unittest
from pathlib import Path

from nixos_render_docs.manual import HTMLConverter, HTMLParameters


class TestRedirects(unittest.TestCase):
    def setUp(self):
        self.md = HTMLConverter("1.0.0", HTMLParameters("", [], [], 2, 2, 2, Path("")), {})

        with open(Path(__file__).parent / 'index.md', 'w') as infile:
            infile.write("""
# title {#title}

## subtitle {#subtitle}
            """)
        self.md.convert(Path(__file__).parent / 'index.md', Path(__file__).parent / 'index.html')


    def test_parsing_passes(self):
        try:
            self.md.parse_redirects({'title': ['index.html'], 'subtitle': ['index.html']}, Path(__file__).parent)
        except Exception as error:
            self.fail(f"redirect parsing failed raised an unexpected exception: {error}")


    def test_missing_redirect_for_identifier(self):
        with self.assertRaisesRegex(RuntimeError, "^following identifiers don't have a redirect: {'title', 'subtitle'}$"):
            self.md.parse_redirects({}, Path(__file__).parent)


    def test_orphan_identifier_in_redirects(self):
        with self.assertRaisesRegex(RuntimeError, "^following identifiers missing in source: {'foo'}$"):
            self.md.parse_redirects({'foo': ['index.html', 'index.html#title']}, Path(__file__).parent)


    def test_divergent_redirects(self):
        with self.assertRaisesRegex(RuntimeError, "^following paths redirect to different locations: {'index.html#foo'}$"):
            self.md.parse_redirects({'title': ['index.html', 'index.html#foo'], 'subtitle': ['index.html', 'index.html#foo']}, Path(__file__).parent)


    def test_conflicting_anchors(self):
        with self.assertRaisesRegex(RuntimeError, "^following anchors found that conflict with identifiers: {'title'}$"):
            self.md.parse_redirects({'title': ['index.html'], 'subtitle': ['index.html', 'index.html#title']}, Path(__file__).parent)


    def test_transitive_redirects(self):
        with self.assertRaisesRegex(RuntimeError, "^following paths have server-side redirects, please modify them to represent their final paths:\n\tfoo.html#bar -> index.html#bar$"):
            self.md.parse_redirects({'title': ['index.html', 'foo.html'], 'subtitle': ['index.html', 'foo.html#bar']}, Path(__file__).parent)
