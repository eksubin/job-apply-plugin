import unittest
from html.parser import HTMLParser
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SITE_ORIGIN = "https://eksubin.github.io/job-apply-plugin/"


class MetadataParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.canonical = None
        self.open_graph_url = None

    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        if tag == "link" and values.get("rel") == "canonical":
            self.canonical = values.get("href")
        if tag == "meta" and values.get("property") == "og:url":
            self.open_graph_url = values.get("content")


class SiteMetadataTests(unittest.TestCase):
    def test_custom_domain_is_consistent_across_pages_configuration_and_metadata(self):
        parser = MetadataParser()
        parser.feed((REPO_ROOT / "site" / "index.html").read_text())

        self.assertFalse(
            (REPO_ROOT / "site" / "CNAME").exists(),
            "site is served from the GitHub Pages default domain, so no CNAME is expected",
        )
        self.assertEqual(parser.canonical, SITE_ORIGIN)
        self.assertEqual(parser.open_graph_url, SITE_ORIGIN)


if __name__ == "__main__":
    unittest.main()
