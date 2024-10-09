import json
import unittest
from pathlib import Path

from nixos_render_docs.manual import HTMLConverter, HTMLParameters
from nixos_render_docs.redirects import Redirects


class TestRedirects(unittest.TestCase):
    def setUp(self):
        with open(Path(__file__).parent / 'index.md', 'w') as infile:
            infile.write("""
# title {#title}

## subtitle {#subtitle}
            """)

    def parse_and_test(self, regex: str, redirects: dict[str, list[str]]):
        md = HTMLConverter("1.0.0", HTMLParameters("", [], [], 2, 2, 2, Path("")), {}, Redirects(redirects, ''))
        with self.assertRaisesRegex(RuntimeError, regex):
            md.convert(Path(__file__).parent / 'index.md', Path(__file__).parent / 'index.html')

    def test_parsing_passes(self):
        md = HTMLConverter("1.0.0", HTMLParameters("", [], [], 2, 2, 2, Path("")), {}, Redirects({'title': ['index.html'], 'subtitle': ['index.html']}, ''))
        try:
            md.convert(
                Path(__file__).parent / 'index.md',
                Path(__file__).parent / 'index.html',
            )
        except Exception as error:
            self.fail(f"redirect parsing failed raised an unexpected exception: {error}")

    def test_missing_redirect_for_identifier(self):
        self.parse_and_test(
            "^following identifiers don't have a redirect: {'title', 'subtitle'}$",
            {}
        )

    def test_orphan_identifier_in_redirects(self):
        self.parse_and_test(
            "^following identifiers missing in source: {'foo'}$",
            {'foo': ['index.html', 'index.html#title']}
        )

    def test_missing_current_output_path(self):
        self.parse_and_test(
            "^the first location of 'subtitle' must be its current output path$",
            {'title': ['index.html'], 'subtitle': ['foo.html']}
        )

    def test_divergent_redirects(self):
        self.parse_and_test(
            "^following paths redirect to different locations: {'index.html#foo'}$",
            {'title': ['index.html', 'index.html#foo'], 'subtitle': ['index.html', 'index.html#foo']}
        )

    def test_conflicting_anchors(self):
        self.parse_and_test(
            "^following anchors found that conflict with identifiers: {'title'}$",
            {'title': ['index.html'], 'subtitle': ['index.html', 'index.html#title']}
        )

    def test_transitive_redirects(self):
        self.parse_and_test(
            "^following paths have server-side redirects, please modify them to represent their final paths:\n\tfoo.html#bar -> index.html#bar$",
            {'title': ['index.html', 'foo.html'], 'subtitle': ['index.html', 'foo.html#bar']}
        )
