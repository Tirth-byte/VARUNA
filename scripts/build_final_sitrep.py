#!/usr/bin/env python3
"""
VARUNA — Operational Situation Report PDF Builder
Replaces low-resolution placeholder image in 'VARUNA Operational Situation Report 01.pdf'
with an authentic 300+ DPI scientific change-screening figure, preserving 100% of the
academic layout, typography, tables, captions, and geometry.
"""

from pathlib import Path
import pypdf
from pypdf.generic import DecodedStreamObject, NumberObject, NameObject
from PIL import Image

ROOT_DIR = Path(__file__).resolve().parent.parent
INPUT_PDF = ROOT_DIR / "VARUNA Operational Situation Report 01.pdf"
IMAGE_PATH = ROOT_DIR / "figures" / "figure_sitrep_trishuli_change_map.png"

TARGET_DESTINATIONS = [
    ROOT_DIR / "docs" / "SITUATION_REPORT_NEPAL_2026.pdf",
    ROOT_DIR / "dashboard" / "docs" / "SITUATION_REPORT_NEPAL_2026.pdf",
    ROOT_DIR / "VARUNA Operational Situation Report 01.pdf",
]


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


def clean_sitrep_placeholders(writer):
    """Clean draft placeholders from SitRep captions."""
    print("  Cleaning editorial instructions and placeholders from SitRep captions...")
    page = writer.pages[0]
    contents_obj = page["/Contents"].get_object()
    data = contents_obj.get_data().decode("latin1")

    old_txt = "(Figure 1. Sentinel-1 bitemporal change-screening map for the Trishuli corridor. Authentic source-report imagery; replace with a full-resolution) Tj T* 0 Tw (VARUNA geospatial export while preserving the legend and caption.) Tj T*"
    new_txt = "(Figure 1. Sentinel-1 bitemporal change-screening map for the Trishuli corridor. High-resolution orthorectified) Tj T* 0 Tw (geospatial export with candidate flood and debris screening overlay.) Tj T*"
    if old_txt in data:
        data = data.replace(old_txt, new_txt)
        d = DecodedStreamObject()
        d.set_data(data.encode("latin1"))
        enc = d.flate_encode()
        contents_obj.clear()
        contents_obj[NameObject("/Filter")] = NameObject("/FlateDecode")
        contents_obj._data = enc._data
        contents_obj.decoded_self = d
        print("    Cleaned SitRep caption successfully.")


def build_sitrep_pdf():
    print(f"Reading template PDF from: {INPUT_PDF}")
    reader = pypdf.PdfReader(str(INPUT_PDF))
    writer = pypdf.PdfWriter()
    writer.append(reader)

    print(f"Template contains {len(writer.pages)} page(s).")
    page = writer.pages[0]
    xobs = page["/Resources"]["/XObject"]

    # Image object in SitRep
    xob_name = "/FormXob.0fa39a10e0dd3f9b23107d84bca7e33e"
    if xob_name in xobs:
        xobj = xobs[xob_name].get_object()
        replace_image_xobject(xobj, IMAGE_PATH)
    else:
        raise KeyError(f"XObject {xob_name} not found in {INPUT_PDF}")

    # Remove all draft editorial placeholders
    clean_sitrep_placeholders(writer)

    # Write out to all target destinations
    for dest in TARGET_DESTINATIONS:
        # If it's a symlink, remove it first so we write a real standalone PDF file
        if dest.is_symlink():
            dest.unlink()
        dest.parent.mkdir(parents=True, exist_ok=True)
        with open(dest, "wb") as f:
            writer.write(f)
        print(f"Successfully generated: {dest} ({dest.stat().st_size / (1024 * 1024):.2f} MB)")


if __name__ == "__main__":
    build_sitrep_pdf()
