import json
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

    def parse_and_test(self, regex: str, redirects: dict[str, list[str]]):
        with open(Path(__file__).parent / 'redirects.json', 'w') as infile:
            json.dump(redirects, infile)
        with self.assertRaisesRegex(RuntimeError, regex):
            self.md.convert(Path(__file__).parent / 'index.md', Path(__file__).parent / 'index.html')

    def test_parsing_passes(self):
        with open(Path(__file__).parent / 'redirects.json', 'w') as infile:
            json.dump({'title': ['index.html'], 'subtitle': ['index.html']}, infile)
        try:
            self.md.convert(
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
