from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "BGV_WORKFLOW_VISUAL.png"


def main() -> None:
    width, height = 1400, 760
    image = Image.new("RGB", (width, height), "#f8fafc")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    steps = [
        ("Offer Released", "HR sends offer email"),
        ("Candidate Accepts", "Microsoft Form response"),
        ("BGV Form", "Candidate submits details"),
        ("Vendor Check", "Verification outcome"),
        ("AI Assist", "Risk summary and draft"),
        ("HR Review", "Approve or request edits"),
        ("Correction", "Candidate responds"),
        ("Final Decision", "Complete, proceed, hold, reject"),
    ]

    box_w, box_h = 245, 92
    gap_x, gap_y = 70, 110
    start_x, start_y = 70, 120

    draw.text((70, 42), "Agentic AI BGV Workflow", fill="#111827", font=font)
    draw.text((70, 68), "Demo-safe background verification flow for HR teams", fill="#4b5563", font=font)

    positions = []
    for idx, step in enumerate(steps):
        row = idx // 4
        col = idx % 4
        x = start_x + col * (box_w + gap_x)
        y = start_y + row * (box_h + gap_y)
        positions.append((x, y))
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=8, fill="#ffffff", outline="#2563eb", width=3)
        draw.text((x + 18, y + 20), step[0], fill="#1d4ed8", font=font)
        draw.text((x + 18, y + 52), step[1], fill="#374151", font=font)

    for i in range(len(positions) - 1):
        x1, y1 = positions[i]
        x2, y2 = positions[i + 1]
        if i == 3:
            draw.line((x1 + box_w / 2, y1 + box_h, x1 + box_w / 2, y2 - 24), fill="#64748b", width=3)
            draw.line((x1 + box_w / 2, y2 - 24, x2 + box_w / 2, y2 - 24), fill="#64748b", width=3)
            draw.line((x2 + box_w / 2, y2 - 24, x2 + box_w / 2, y2), fill="#64748b", width=3)
        else:
            draw.line((x1 + box_w, y1 + box_h / 2, x2, y2 + box_h / 2), fill="#64748b", width=3)

    draw.rounded_rectangle((70, 610, 1320, 700), radius=8, fill="#eff6ff", outline="#bfdbfe")
    draw.text((95, 638), "HR remains in control: AI output is reviewed before candidate-facing communication is sent.", fill="#1e3a8a", font=font)
    draw.text((95, 666), "The app runs locally with deterministic fallback logic, so it is demoable without live AI or email credentials.", fill="#1e3a8a", font=font)

    image.save(OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
