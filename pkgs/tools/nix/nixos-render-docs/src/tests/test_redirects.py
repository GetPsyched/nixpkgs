import json
import unittest
from pathlib import Path

from nixos_render_docs.manual import HTMLConverter, HTMLParameters
from nixos_render_docs.manual_structure import XrefTarget
from nixos_render_docs.redirects import Redirects


class TestRedirects(unittest.TestCase):
    def test_identifier_added(self):
        """
        Test adding a new identifier to the source.

        Expected behaviour:
        - The redirects JSON should be updated to include the new identifier
        - The identifier must correspond to a list of which the first element is its current location

        Before:
        Markdown:
        # Foo
        Content for Foo.

        Redirects JSON:
        {
            "foo": ["path/to/index.html"]
        }

        After:
        Markdown:
        # Foo
        Content for Foo.

        # Bar
        Content for Bar.

        Redirects JSON:
        {
            "foo": ["path/to/index.html"],
            "bar": ["path/to/index.html"]
        }
        """
        xref_targets = {
            "foo": XrefTarget(id="foo", title_html="Foo", toc_html="Foo", title="Foo", path="path/to/index.html"),
            "bar": XrefTarget(id="bar", title_html="Bar", toc_html="Bar", title="Bar", path="path/to/index.html"),
        }

        # Case 1: Violated expected behaviour
        raw_redirects = { "foo": ["path/to/index.html"] }
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertIn("bar", redirects.identifiers_without_redirects)

        # Case 2: Conformed to expected behaviour
        raw_redirects["bar"] = ["path/to/index.html"]
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertNotIn("bar", redirects.identifiers_without_redirects)

    def test_identifier_removed(self):
        """
        Test removing an identifier from the source.

        Expected behaviour:
        - The "bar" identifier should be removed from the redirects mapping along with its location(s)

        Before:
        Markdown:
        # Foo
        Content for Foo.

        # Bar
        Content for Bar.

        Redirects JSON:
        {
            "foo": ["path/to/index.html"],
            "bar": ["path/to/index.html"]
        }

        After:
        Markdown:
        # Foo
        Content for Foo.

        Redirects JSON:
        {
            "foo": ["path/to/index.html"]
        }
        """
        xref_targets = {
            "foo": XrefTarget("foo", "Foo", "Foo", "Foo", "path/to/index.html"),
        }

        # Case 1: Violated expected behaviour
        raw_redirects = {
            "foo": ["path/to/index.html"],
            "bar": ["path/to/index.html"],
        }
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertIn("bar", redirects.orphan_identifiers)

        # Case 2: Conformed to expected behaviour
        del raw_redirects["bar"]
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertNotIn("bar", redirects.orphan_identifiers)

    def test_identifier_renamed(self):
        """
        Test renaming an identifier in the source.

        Expected behaviour:
        - The old "foo" identifier should be removed from the redirect identifiers
        - A new "foo-prime" identifier should be added to the redirect mapping and have "foo" in its historical locations
        - If "foo" had any historical locations, those should also be appended to this new identifier's list

        Before:
        Markdown:
        # Foo
        Content for Foo.

        # Bar
        Content for Bar.

        Redirects JSON:
        {
            "foo": ["path/to/index.html"],
            "bar": ["path/to/index.html"]
        }

        After:
        Markdown:
        # Foo Prime
        Content for Foo.

        # Bar
        Content for Bar.

        Redirects JSON:
        {
            "foo-prime": ["path/to/index.html", "path/to/index.html#foo"],
            "bar": ["path/to/bar.html"]
        }
        """
        xref_targets = {
            "foo-prime": XrefTarget("foo-prime", "Foo Prime", "Foo Prime", "Foo Prime", "path/to/index.html"),
            "bar": XrefTarget("bar", "Bar", "Bar", "Bar", "path/to/index.html"),
        }

        # Case 1: Violated expected behaviour
        raw_redirects = {
            "foo": ["path/to/index.html"],
            "bar": ["path/to/index.html"],
        }
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertIn("foo-prime", redirects.identifiers_without_redirects)
        self.assertIn("foo", redirects.orphan_identifiers)

        # Case 2: Conformed to expected behaviour
        raw_redirects["foo-prime"] = raw_redirects.pop("foo")
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertNotIn("foo-prime", redirects.identifiers_without_redirects)
        self.assertNotIn("foo", redirects.orphan_identifiers)

    def test_child_identifier_moved_to_different_file(self):
        """
        Test moving an identifier without children to a different source file.

        Expected behavior:
        - The "bar" identifier should be updated in xref_targets with its new path
        - The redirects JSON should be updated to include the new location for "bar"

        Before:
        Markdown (foo.md):
        # Foo
        Content for Foo.

        # Bar
        Content for Bar.

        Redirects JSON:
        {
            "foo": ["path/to/foo.html"],
            "bar": ["path/to/foo.html", "path/to/foo.html#baz"]
        }

        After:
        Markdown (bar.md):
        # Bar
        Content for Bar.

        Redirects JSON:
        {
            "foo": ["path/to/foo.html"],
            "bar": ["path/to/bar.html", "path/to/foo.html#bar", "path/to/foo.html#baz"]
        }
        """
        xref_targets = {
            "foo": XrefTarget("foo", "Foo", "Foo", "Foo", "path/to/foo.html"),
            "bar": XrefTarget("bar", "Bar", "Bar", "Bar", "path/to/bar.html"),
        }

        # Case 1: Violated expected behaviour
        raw_redirects = {
            "foo": ["path/to/foo.html"],
            "bar": ["path/to/foo.html", "path/to/foo.html#baz"],
        }
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertIn("bar", redirects.identifiers_missing_current_outpath)

        # Case 2: Conformed to expected behaviour
        raw_redirects = {
            "foo": ["path/to/foo.html"],
            "bar": ["path/to/bar.html", "path/to/foo.html#bar", "path/to/foo.html#baz"]
        }
        redirects = Redirects(raw_redirects, '')
        redirects.validate(xref_targets)
        self.assertNotIn("bar", redirects.identifiers_missing_current_outpath)
