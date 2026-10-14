#!/usr/bin/env python3
"""
VARUNA — Final Academic Research Paper Builder
Replaces low-resolution placeholder images in VARUNA_Research_Paper_REFINED.pdf
with authentic 300+ DPI scientific figures, preserving 100% of the academic layout,
typography, tables, citations, and geometry.
"""

from pathlib import Path
import pypdf
from pypdf.generic import DecodedStreamObject, NumberObject, NameObject
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PDF = Path("/Users/macbookair/Library/Mobile Documents/com~apple~CloudDocs/VARUNA_Research_Paper_REFINED.pdf")
OUTPUT_PDF = ROOT_DIR / "VARUNA_Research_Paper_FINAL.pdf"
DOCS_PDF = ROOT_DIR / "docs" / "VARUNA_Research_Paper_FINAL.pdf"
DASHBOARD_PDF = ROOT_DIR / "dashboard" / "docs" / "VARUNA_Research_Paper_FINAL.pdf"

FIGURES = {
    # Page 1: Figure 1 Study Area
    (0, "/FormXob.e712a5f9546488d0c3d113825b3644d8"): ROOT_DIR / "figures" / "figure1_study_area_context.png",
    # Page 2: Figure 2 Sentinel-1 Comparison
    (1, "/FormXob.397a0e28d9537f07e8b17361c59df759"): ROOT_DIR / "figures" / "figure2_s1_pre_post_comparison.png",
    # Page 3 Top: Figure 3 SAR Surface Change Classification
    (2, "/FormXob.21ef92fb53f5e1254f99430bf6795962"): ROOT_DIR / "figures" / "figure3_sar_surface_change_classification.png",
    # Page 3 Bottom: Figure 4 EMSR927 Validation (Bidur)
    (2, "/FormXob.22bb07c67e1b3be6fe592a82a04d0c16"): ROOT_DIR / "figures" / "figure4_emsr927_validation_bidur.png",
}


def replace_image_xobject(xobj, img_path: Path):
    """Replace image stream in-place with high-res PNG pixel data compressed via FlateDecode."""
    print(f"  Replacing XObject with {img_path.name}...")
    im = Image.open(img_path).convert("RGB")
    w, h = im.size
    raw_bytes = im.tobytes()

    d = DecodedStreamObject()
    d.set_data(raw_bytes)
    enc = d.flate_encode()

    xobj.clear()
    xobj[NameObject("/Type")] = NameObject("/XObject")
    xobj[NameObject("/Subtype")] = NameObject("/Image")
    xobj[NameObject("/Width")] = NumberObject(w)
    xobj[NameObject("/Height")] = NumberObject(h)
    xobj[NameObject("/ColorSpace")] = NameObject("/DeviceRGB")
    xobj[NameObject("/BitsPerComponent")] = NumberObject(8)
    xobj[NameObject("/Filter")] = NameObject("/FlateDecode")
    xobj._data = enc._data
    xobj.decoded_self = d
    print(f"    Dimensions: {w}x{h} px | Stream size: {len(xobj._data) / 1024:.1f} KB")


def build_final_pdf():
    print(f"Reading template PDF from: {INPUT_PDF}")
    reader = pypdf.PdfReader(str(INPUT_PDF))
    writer = pypdf.PdfWriter()
    writer.append(reader)

    print(f"Template contains {len(writer.pages)} pages.")

    for (page_idx, xob_name), img_path in FIGURES.items():
        page = writer.pages[page_idx]
        xobs = page["/Resources"]["/XObject"]
        if xob_name in xobs:
            xobj = xobs[xob_name].get_object()
            replace_image_xobject(xobj, img_path)
        else:
            raise KeyError(f"XObject {xob_name} not found on page {page_idx + 1}")

    # Save to destination paths
    for dest in [OUTPUT_PDF, DOCS_PDF, DASHBOARD_PDF]:
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            writer.write(f)
        print(f"Successfully generated: {dest} ({dest.stat().st_size / (1024 * 1024):.2f} MB)")


if __name__ == "__main__":
    build_final_pdf()
