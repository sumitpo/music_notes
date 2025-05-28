"""
abc_to_kalimba_music21.py

A script to convert an ABC notation file into a visual Kalimba tablature using music21.
Supports kalimba size and octave policy.

Usage:
    python abc_to_kalimba_music21.py -i input.abc [--kalimba-size 17] [--octave-policy ignore|shift_down]
"""

import argparse
from pathlib import Path
from music21 import converter, note
import svgwrite
from weasyprint import HTML
from rich import print


# 默认映射表（最多到 E5）
# fmt: off
NOTE_TO_KALIMBA = {
    'C2': 1, 'D2': 2, 'E2': 3, 'F2': 4,
    'G2': 5, 'A2': 6, 'B2': 7,

    'C3': 8, 'D3': 9, 'E3': 10, 'F3': 11,
    'G3': 12, 'A3': 13, 'B3': 14,

    'C4': 15, 'D4': 16, 'E4': 17, 'F4': 18,
    'G4': 19, 'A4': 20, 'B4': 21,

    'C5': 22, 'D5': 23, 'E5': 24
}
# fmt: on


def build_kalimba_map(max_tines=17):
    """
    根据 kalimba 的音片数构建映射表。
    例如 max_tines=17 → 只保留到 E4
    """
    return {k: v for k, v in NOTE_TO_KALIMBA.items() if v <= max_tines}


def map_note_to_kalimba(note_name, kalimba_notes):
    """
    将音名转换为 kalimba 音片编号
    """
    if note_name in kalimba_notes:
        return kalimba_notes[note_name]

    # 分割音名和八度（如 C#4 -> ('C#', 4)）
    base = "".join(filter(str.isalpha, note_name))
    num = "".join(filter(str.isdigit, note_name))

    if not num:
        return None

    octave = int(num)
    new_note = f"{base}{octave - 1}"  # 降八度尝试
    if new_note in kalimba_notes:
        print(f"[+] Auto-shifted down: {note_name} → {new_note}")
        return kalimba_notes[new_note]

    return None


def generate_svg(notes, output_svg="kalimba_tab.svg"):
    """Generate SVG file representing the kalimba tab."""
    dwg = svgwrite.Drawing(output_svg, profile="tiny", size=("210mm", "297mm"))
    x, y = 20, 50
    spacing = 30

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


def parse_abc_file(file_path, kalimba_notes, policy="shift_down"):
    """
    Parse .abc file and extract notes with Kalimba mapping.
    """
    try:
        score = converter.parse(file_path)

        kalimba_notes_list = []

        for element in score.recurse():
            if not isinstance(element, note.Note):
                continue
            raw_note = element.pitch.nameWithOctave

            # 获取音符名称中的基础音和八度
            base = "".join(filter(str.isalpha, raw_note))
            num_part = "".join(filter(str.isdigit, raw_note))
            if not num_part:
                continue
            octave = int(num_part)

            mapped_note = map_note_to_kalimba(raw_note, kalimba_notes)

            if mapped_note is None and policy == "shift_down":
                # 尝试降八度
                new_note = f"{base}{octave - 1}"
                mapped_note = map_note_to_kalimba(new_note, kalimba_notes)

                if mapped_note:
                    print(
                        f"[+] Shifted down from {raw_note} → {new_note}: {mapped_note}"
                    )

            if mapped_note:
                direction = "▲" if mapped_note % 2 == 0 else "▼"
                kalimba_notes_list.append((mapped_note, direction))

        return kalimba_notes_list

    except Exception as e:
        print(f"[!] Error parsing ABC file: {e}")
        return []


def main(input_abc, output_pdf=None, kalimba_size=17, octave_policy="shift_down"):
    print(f"[*] Parsing ABC file: {input_abc}")
    print(f"[+] Using kalimba size: {kalimba_size}, Octave Policy: {octave_policy}")

    kalimba_notes = build_kalimba_map(kalimba_size)

    notes = parse_abc_file(input_abc, kalimba_notes, octave_policy)

    if not notes:
        print("[-] No valid notes found or error occurred.")
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


def parse():
    des = "Convert ABC notation to Kalimba tablature using music21."
    try:
        from rich_argparse import RichHelpFormatter

        parser = argparse.ArgumentParser(
            description=des, formatter_class=RichHelpFormatter
        )
    except ImportError:
        parser = argparse.ArgumentParser(description=des)

    parser.add_argument("-i", "--input", required=True, help="Path to input .abc file")
    parser.add_argument("-o", "--output", help="Optional path to output PDF file")
    parser.add_argument(
        "--kalimba-size",
        type=int,
        default=17,
        help="Number of tines on your kalimba (default: 17)",
    )
    parser.add_argument(
        "--octave-policy",
        choices=["ignore", "shift_down"],
        default="shift_down",
        help="How to handle notes out of range",
    )

    args = parser.parse_args()
    return args


if __name__ == "__main__":
    args = parse()
    main(args.input, args.output, args.kalimba_size, args.octave_policy)
