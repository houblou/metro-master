from hashlib import sha256
from pathlib import Path
import unittest

from metro_master.pdf_library import GovernedPdfLibrary, PdfManifestRecord


class FakePage:
    def __init__(self, number):
        self.number = number

    def extract_text(self):
        return f"content of page {self.number}"


class FakeReader:
    def __init__(self, path):
        self.pages = [FakePage(index) for index in range(1, 26)]


class GovernedPdfLibraryTests(unittest.TestCase):
    def setUp(self):
        self.root = Path(__file__).parent.resolve()
        fixture = self.root / "fixtures" / "not-a-real.pdf"
        digest = sha256(fixture.read_bytes()).hexdigest()
        self.record = PdfManifestRecord(
            id="DOC-1",
            reference="REF-1",
            title="Fixture",
            relative_path="fixtures/not-a-real.pdf",
            source_url="",
            resolved_url="",
            status="Downloaded",
            sha256=digest,
            rights="private",
            message="",
            verified_at="2026-11-05",
        )
        self.library = GovernedPdfLibrary(
            self.root,
            [self.record],
            reader_factory=FakeReader,
        )

    def test_search_and_verified_chunking(self):
        self.assertEqual(self.library.search("fixture")[0].id, "DOC-1")
        chunks = tuple(self.library.iter_chunks("DOC-1"))
        self.assertEqual(len(chunks), 2)
        self.assertEqual((chunks[0].start_page, chunks[0].end_page), (1, 20))
        self.assertEqual((chunks[1].start_page, chunks[1].end_page), (21, 25))
        self.assertEqual(chunks[1].pages[-1].page_number, 25)

    def test_more_than_twenty_pages_per_chunk_is_rejected(self):
        with self.assertRaises(ValueError):
            tuple(self.library.iter_chunks("DOC-1", chunk_size=21))

    def test_hash_mismatch_is_rejected(self):
        invalid = PdfManifestRecord(
            id="BAD",
            reference="REF",
            title="Bad hash",
            relative_path="fixtures/not-a-real.pdf",
            source_url="",
            resolved_url="",
            status="Downloaded",
            sha256="0" * 64,
            rights="private",
            message="",
            verified_at="2026-11-05",
        )
        library = GovernedPdfLibrary(
            self.root,
            [invalid],
            reader_factory=FakeReader,
        )
        with self.assertRaises(ValueError):
            tuple(library.iter_chunks("BAD"))

    def test_manifest_path_cannot_escape_root(self):
        escaping = PdfManifestRecord(
            id="ESCAPE",
            reference="REF",
            title="Escape",
            relative_path="../outside.pdf",
            source_url="",
            resolved_url="",
            status="Downloaded",
            sha256="0" * 64,
            rights="private",
            message="",
            verified_at="2026-11-05",
        )
        library = GovernedPdfLibrary(self.root, [escaping], reader_factory=FakeReader)
        with self.assertRaises(ValueError):
            library.resolve_file(escaping)


if __name__ == "__main__":
    unittest.main()
