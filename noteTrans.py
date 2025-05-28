"""
abc_to_kalimba.py

A Python script to convert an ABC notation file into a visual Kalimba tablature.
The output is generated as SVG, and optionally converted to PDF.

Usage:
    python abc_to_kalimba.py -i input.abc [-o output.pdf]
"""

import argparse
from abctools import abc_parser
import svgwrite
from weasyprint import HTML


# Mapping of musical notes to kalimba tines (for 17-note kalimba)
NOTE_TO_KALIMBA = {
    "c2": 1,
    "d2": 2,
    "e2": 3,
    "f2": 4,
    "g2": 5,
    "a2": 6,
    "b2": 7,
    "c3": 8,
    "d3": 9,
    "e3": 10,
    "f3": 11,
    "g3": 12,
    "a3": 13,
    "b3": 14,
    "c4": 15,
    "d4": 16,
    "e4": 17,
}


def map_note_to_kalimba(note):
    """Converts a note name to its corresponding kalimba tine number."""
    return NOTE_TO_KALIMBA.get(str(note).lower(), None)


def parse_abc_file(file_path):
    """Parse the ABC file and extract notes."""
    try:
        with open(file_path, "r") as f:
            content = f.read()
        parsed = abc_parser.parse(content)
        notes = []
        for tune in parsed:
            for n in tune.notes:
                note_number = map_note_to_kalimba(n.pitch)
                if note_number:
                    direction = "▲" if note_number % 2 == 0 else "▼"
                    notes.append((note_number, direction))
        return notes
    except Exception as e:
        print(f"[!] Failed to parse ABC file: {e}")
        return []


def generate_svg(notes, output_svg="kalimba_tab.svg"):
    """Generate an SVG file representing the kalimba tab."""
    dwg = svgwrite.Drawing(output_svg, profile="tiny", size=("210mm", "297mm"))
    x, y = 20, 50
    spacing = 30

    # Add title
    dwg.add(dwg.text("Kalimba Tablature", insert=(20, 30), font_size=24))

    for i, (num, direction) in enumerate(notes):
        text = f"{num}{direction}"
        dwg.add(dwg.text(text, insert=(x, y), font_size=20))
        x += spacing

        if (i + 1) % 16 == 0:
            x = 20
            y += 40

    dwg.save()
    print(f"[+] SVG file saved: {output_svg}")


def convert_svg_to_pdf(svg_path, pdf_path):
    """Convert SVG to PDF using WeasyPrint."""
    try:
        html_content = open(svg_path, "r").read()
        HTML(string=html_content).write_pdf(pdf_path)
        print(f"[+] PDF file saved: {pdf_path}")
    except Exception as e:
        print(f"[!] Failed to convert SVG to PDF: {e}")


def main(input_abc, output_pdf=None):
    print("[*] Parsing ABC file...")
    notes = parse_abc_file(input_abc)

    if not notes:
        print("[-] No valid notes found in ABC file.")
        return

    svg_file = "kalimba_tab.svg"
    print(f"[+] Generating SVG file: {svg_file}")
    generate_svg(notes, svg_file)

    if output_pdf:
        print(f"[+] Converting to PDF: {output_pdf}")
        convert_svg_to_pdf(svg_file, output_pdf)
    else:
        default_pdf = "kalimba_tab.pdf"
        print(f"[+] Converting to default PDF: {default_pdf}")
        convert_svg_to_pdf(svg_file, default_pdf)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Convert ABC notation to Kalimba tablature."
    )
    parser.add_argument("-i", "--input", required=True, help="Path to input .abc file")
    parser.add_argument("-o", "--output", help="Optional path to output PDF file")

    args = parser.parse_args()

    main(args.input, args.output)
