import io
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.oxml.xmlchemy import OxmlElement
from pptx.oxml.ns import qn
from pptx.util import Inches


SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from generate_beamer_template import generate
from inspect_pptx import archive_reference, extract_images
from project_manager import init


def png(color):
    stream = io.BytesIO()
    Image.new("RGB", (64, 36), color).save(stream, format="PNG")
    return stream.getvalue()


class PptxTemplateTest(unittest.TestCase):
    def setUp(self):
        work = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.root = init(work / "template project")
        source = work / "reference.pptx"
        deck = Presentation()
        slide = deck.slides.add_slide(deck.slide_layouts[0])
        slide.shapes.title.text = "Unapproved title from source"
        self.logo = png("blue")
        logo = slide.shapes.add_picture(io.BytesIO(self.logo), Inches(1), Inches(1))
        logo.crop_left = 0.2
        self.logo_id = f"p1:{logo.shape_id}"
        hidden = deck.slides.add_slide(deck.slide_layouts[6])
        hidden._element.set("show", "0")
        self.background = png("white")
        hidden.shapes.add_picture(io.BytesIO(png("red")), Inches(1), Inches(1))
        _, rel_id = deck.slide_masters[0].part.get_or_add_image_part(io.BytesIO(self.background))
        bg = deck.slide_masters[0]._element.xpath("./p:cSld/p:bg")[0]
        bg.clear()
        for tag in ("p:bgPr", "a:blipFill", "a:blip"):
            node = OxmlElement(tag)
            bg.append(node)
            bg = node
        bg.set(qn("r:embed"), rel_id)
        deck.save(source)
        self.report = json.loads(archive_reference(self.root, source).read_text(encoding="utf-8"))
        self.spec = {
            "source_sha256": self.report["sha256"],
            "overall": {"canvas": "source", "density": "standard", "header": "band", "footer": "number",
                        "colors": {"accent": "315C88", "text": "182231", "background": "FFFFFF", "on_accent": "FFFFFF"}},
            "labels": {"author": "报告人", "date": "日期", "body": "填写符号说明", "point": "要点",
                       "evidence": "证据", "figure": "图表占位", "caption": "图注", "summary": "结论与下一步"},
            "frames": [{"stage": "封面", "layout": "cover", "title": "新标题 & 50%", "reference_pages": [1]}],
        }
        (self.root / "outline.md").write_text("Confirmed template design", encoding="utf-8")

    def test_inventory_and_exact_extraction(self):
        self.assertTrue(self.report["slides"][1]["hidden"])
        self.assertEqual(self.report["slides"][0]["layout"], "l1")
        self.assertEqual(self.report["layouts"][0]["master"], "m1")
        shape = next(shape for shape in self.report["slides"][0]["shapes"] if shape["id"] == self.logo_id)
        self.assertEqual(shape["image"]["source_rect"]["l"], "20000")
        self.assertTrue(self.report["masters"][0]["background"]["image"]["extractable"])
        folder = self.root / "slides" / "figures" / "pptx"
        self.assertFalse(folder.exists())
        with self.assertRaisesRegex(ValueError, "Not an extractable"):
            extract_images(self.root, [self.logo_id, "p2:999"])
        self.assertFalse(folder.exists())

        manifest = extract_images(self.root, [self.logo_id, "m1:bg"])
        self.assertEqual({p.name for p in folder.iterdir()}, {manifest.name, self.logo_id.replace(":", "-") + ".png", "m1-bg.png"})
        self.assertEqual((folder / "m1-bg.png").read_bytes(), self.background)
        with self.assertRaisesRegex(ValueError, "Extract exactly"):
            generate(self.root, self.spec)

    def test_placeholder_template_omits_original_content(self):
        main = generate(self.root, self.spec)
        text = main.read_text(encoding="utf-8")
        self.assertNotIn("Unapproved title", text)
        self.assertNotIn("includegraphics", text)
        self.assertIn(r"新标题 \& 50\%", text)
        self.assertIn("papersize={120.000mm,90.000mm}", main.with_name("pptx-theme.sty").read_text(encoding="utf-8"))

    @unittest.skipUnless(shutil.which("latexmk") and shutil.which("xelatex"), "requires latexmk and XeLaTeX")
    def test_compile_all_layouts_without_original_pptx(self):
        import pymupdf

        self.spec["overall"].update(canvas="16:9", latin_font="Nonexistent Test Font")
        self.spec["frames"][0]["logo"] = self.logo_id
        for layout in ("divider", "bullets", "two-column", "figure", "formula", "summary"):
            self.spec["frames"].append({"layout": layout, "stage": "阶段示例", "reference_pages": [1]})
        self.spec["frames"][3]["image"] = self.logo_id
        self.spec["frames"][4]["background"] = "m1:bg"
        self.spec["frames"].append({"layout": "cover", "stage": "备用封面", "reference_pages": []})
        extract_images(self.root, [self.logo_id, "m1:bg"])
        generate(self.root, self.spec)
        (self.root / "template-source" / "original.pptx").unlink()
        result = subprocess.run([sys.executable, str(SCRIPTS / "build_pdf.py"), "build", str(self.root)],
                                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
        report = json.loads((self.root / "build" / "check.json").read_text(encoding="utf-8"))
        self.assertEqual(result.returncode, 0, f"{result.stderr}\n{report}")
        self.assertEqual(report["page_count"], 8)
        with pymupdf.open(self.root / "build" / "main.pdf") as pdf:
            self.assertAlmostEqual(pdf[0].rect.width / pdf[0].rect.height, 16 / 9, places=3)
            self.assertIn("50%", pdf[0].get_text())
            self.assertEqual([page.number for page in pdf if page.get_image_info()], [0, 3, 4])


if __name__ == "__main__":
    unittest.main()
