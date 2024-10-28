import json
import unittest
from pathlib import Path

from nixos_render_docs.manual import HTMLConverter, HTMLParameters
from nixos_render_docs.manual_structure import XrefTarget
from nixos_render_docs.redirects import Redirects


class TestRedirects(unittest.TestCase):
    def setup_boilerplate(self, source, redirects):
        with open(Path(__file__).parent / 'index.md', 'w') as infile:
            infile.write("""
# Redirects test suite {#redirects-test-suite}
## Setup steps

```{=include=} chapters
foo.md
```
            """)

        with open(Path(__file__).parent / 'foo.md', 'w') as infile:
            infile.write(source)
        md = HTMLConverter("1.0.0", HTMLParameters("", [], [], 2, 2, 2, Path("")), {}, Redirects({"redirects-test-suite": ["index.html"]} | redirects, ''))
        md.convert(Path(__file__).parent / 'index.md', Path(__file__).parent / 'index.html')

        return md._redirects

    def test_identifier_added(self):
        """Test adding a new identifier to the source."""
        # Before
        redirects = self.setup_boilerplate("""
# Foo {#foo}
            """,
            {
                "foo": ["index.html"],
            },
        )
        self.assertEqual(redirects.report_validity(), '')

        # After
        redirects = self.setup_boilerplate(
            """
# Foo {#foo}

## Bar {#bar}
            """,
            {
                "foo": ["index.html"],
                "bar": ["index.html"],
            },
        )
        self.assertEqual(redirects.report_validity(), '')

    def test_identifier_removed(self):
        """Test removing an identifier from the source."""
        # Before
        redirects = self.setup_boilerplate("""
# Foo {#foo}

## Bar {#bar}
            """,
            {
                "foo": ["index.html"],
                "bar": ["index.html"],
            },
        )
        self.assertEqual(redirects.report_validity(), '')

        # After
        redirects = self.setup_boilerplate("""
# Foo {#foo}
            """,
            {
                "foo": ["index.html"],
            },
        )
        self.assertEqual(redirects.report_validity(), '')

    def test_identifier_renamed(self):
        """Test renaming an identifier in the source."""
        # Before
        redirects = self.setup_boilerplate("""
# Foo {#foo}

## Bar {#bar}
            """,
            {
                "foo": ["index.html"],
                "bar": ["index.html"],
            },
        )
        self.assertEqual(redirects.report_validity(), '')

        # After
        redirects = self.setup_boilerplate("""
# Foo Prime {#foo-prime}

## Bar {#bar}
            """,
            {
                "foo-prime": ["index.html", "index.html#foo"],
                "bar": ["index.html"],
            },
        )
        self.assertEqual(redirects.report_validity(), '')
