import os
import tempfile
from pathlib import Path

import pytest

# Isolate tests from the real database, uploads and API keys before the app is imported.
_TMP = Path(tempfile.mkdtemp(prefix="noteful-test-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["UPLOAD_DIR"] = str(_TMP / "uploads")
os.environ["PINECONE_API_KEY"] = ""
os.environ["ANTHROPIC_API_KEY"] = ""

FIXTURES = Path(__file__).parent / "fixtures"


def _make_pdf(path: Path) -> None:
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas

    c = canvas.Canvas(str(path), pagesize=letter)
    c.drawString(72, 720, "Photosynthesis converts light energy into chemical energy.")
    c.showPage()
    c.drawString(72, 720, "The Calvin cycle fixes carbon dioxide into sugars.")
    c.showPage()
    c.save()


def _make_pptx(path: Path) -> None:
    from pptx import Presentation

    prs = Presentation()
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Newton's Laws"
    slide.placeholders[1].text = "An object at rest stays at rest."
    slide.notes_slide.notes_text_frame.text = "Mention inertia here."
    slide = prs.slides.add_slide(prs.slide_layouts[1])
    slide.shapes.title.text = "Second Law"
    slide.placeholders[1].text = "F = ma"
    prs.save(str(path))


def _make_docx(path: Path) -> None:
    from docx import Document

    doc = Document()
    doc.add_heading("Cell Biology", 1)
    doc.add_paragraph("Mitochondria are the site of cellular respiration.")
    doc.save(str(path))


@pytest.fixture(scope="session")
def sample_files() -> dict[str, Path]:
    FIXTURES.mkdir(exist_ok=True)
    files = {
        "pdf": FIXTURES / "sample.pdf",
        "pptx": FIXTURES / "sample.pptx",
        "docx": FIXTURES / "sample.docx",
        "md": FIXTURES / "sample.md",
    }
    _make_pdf(files["pdf"])
    _make_pptx(files["pptx"])
    _make_docx(files["docx"])
    files["md"].write_text("# Thermodynamics\n\nEnergy cannot be created or destroyed.\n", encoding="utf-8")
    return files
