import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pymupdf
from pptx import Presentation


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from build_pdf import build_pdf
from prepare_sources import tree_sha256
from project_manager import init, outline_digest


class TalkWorkflowTest(unittest.TestCase):
    def setUp(self):
        work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.root = init(work / "talk")
        self.slides = self.root / "slides"
        self.main = self.slides / "main.tex"
        self.main.write_text("test source", encoding="utf-8")
        self.outline = self.root / "outline.md"
        self.outline.write_text("### S01 Method\n", encoding="utf-8")
        self.pdf = work / "slides.pdf"
        with pymupdf.open() as pdf:
            for text in ("First", "Second"):
                pdf.new_page(width=320, height=180).insert_text((50, 50), text)
            pdf.save(self.pdf)

    def cli(self, script, *args, success=True):
        result = subprocess.run([sys.executable, str(SCRIPTS / script), *map(str, args)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        self.assertEqual(result.returncode, 0 if success else 1, result.stderr + result.stdout)
        return result

    def approve(self):
        self.cli("project_manager.py", "approve-outline", self.root, "--yes")

    def test_failed_build_preserves_previous_outputs(self):
        self.approve()
        build = self.root / "build"
        build.mkdir()
        previous = {"main.pdf": self.pdf.read_bytes(), "main.pptx": b"previous export", "check.json": b"previous report"}
        for name, data in previous.items():
            (build / name).write_bytes(data)
        with patch("build_pdf.shutil.which", return_value=None):
            self.assertFalse(build_pdf(self.root, self.slides))
        for name, data in previous.items():
            self.assertEqual((build / name).read_bytes(), data)
        report = json.loads((self.root / "build-failed" / "check.json").read_text(encoding="utf-8"))
        self.assertEqual(report["issues"][0]["kind"], "missing_compiler")

    def test_current_export_roundtrips_notes_and_rejects_changed_inputs(self):
        self.approve()
        build = self.root / "build"
        build.mkdir()
        (build / "main.pdf").write_bytes(self.pdf.read_bytes())
        (build / "slides.sha256").write_text(tree_sha256(self.slides), encoding="utf-8")
        (build / "outline.sha256").write_text(outline_digest(self.root), encoding="utf-8")
        (build / "check.json").write_text('{"automated_checks_passed": true}', encoding="utf-8")
        (self.root / "speaker-notes.md").write_text("## 1\nOpening remarks\n\n## 2\nClosing remarks\n", encoding="utf-8")
        args = ("export_pptx.py", self.root, "--format", "png", "--png-long-edge", 320)
        self.cli(*args)
        output = build / "main.pptx"
        self.assertEqual([s.notes_slide.notes_text_frame.text for s in Presentation(output).slides],
                         ["Opening remarks", "Closing remarks"])
        previous = output.read_bytes()
        self.outline.write_text("### S01 Revised method\n", encoding="utf-8")
        self.assertIn("not approved", self.cli(*args, success=False).stderr)
        self.approve()
        self.assertIn("stale", self.cli(*args, success=False).stderr)
        (build / "outline.sha256").write_text(outline_digest(self.root), encoding="utf-8")
        self.main.write_text("changed source", encoding="utf-8")
        self.assertIn("stale", self.cli(*args, success=False).stderr)
        self.assertEqual(output.read_bytes(), previous)

    def test_source_import_and_slide_evidence_coverage(self):
        self.cli("project_manager.py", "import-sources", self.root, "--manuscript", self.pdf)
        content = ("### S00 Cover\nEvidence-exempt: cover — Title only\n"
                   "### S01 Method\n[Method](sources/manuscript/original/slides.pdf#page=1)\n"
                   "### S02 Results\nResults without a locator\n")
        args = ("check_evidence.py", self.root)
        self.outline.write_text(content, encoding="utf-8")
        self.assertIn("S02: missing", self.cli(*args, success=False).stderr)
        self.outline.write_text(content + "[Result](sources/manuscript/original/slides.pdf#page=2)\n", encoding="utf-8")
        self.cli(*args)
