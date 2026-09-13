"""Generate multi-resolution application icons for File Juggler."""
import os
import struct
import sys
from pathlib import Path

# Ensure offscreen Qt
os.environ["QT_QPA_PLATFORM"] = "offscreen"

from PySide6.QtCore import Qt, QRectF, QPointF
from PySide6.QtGui import (
    QGuiApplication, QImage, QPainter, QPainterPath,
    QColor, QLinearGradient, QBrush, QPen, QRadialGradient
)


def create_icon_image(size: int) -> QImage:
    """Render a modern, sleek File Juggler icon at the specified size."""
    image = QImage(size, size, QImage.Format_ARGB32_Premultiplied)
    image.fill(Qt.transparent)

    painter = QPainter(image)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    scale = size / 256.0

    # Draw rounded squircle background base
    bg_rect = QRectF(12 * scale, 12 * scale, 232 * scale, 232 * scale)
    bg_path = QPainterPath()
    bg_path.addRoundedRect(bg_rect, 48 * scale, 48 * scale)

    bg_grad = QLinearGradient(0, 0, size, size)
    bg_grad.setColorAt(0.0, QColor("#0f172a"))  # Deep Slate 900
    bg_grad.setColorAt(1.0, QColor("#1e293b"))  # Slate 800
    painter.fillPath(bg_path, bg_grad)

    # Squircle border stroke
    border_pen = QPen(QColor(255, 255, 255, 25), 2.0 * scale)
    painter.strokePath(bg_path, border_pen)

    # 1. Folder Back / Tab
    tab_path = QPainterPath()
    tab_path.moveTo(42 * scale, 95 * scale)
    tab_path.lineTo(95 * scale, 95 * scale)
    tab_path.lineTo(115 * scale, 115 * scale)
    tab_path.lineTo(214 * scale, 115 * scale)
    tab_path.lineTo(214 * scale, 195 * scale)
    tab_path.lineTo(42 * scale, 195 * scale)
    tab_path.closeSubpath()
    painter.fillPath(tab_path, QColor("#1d4ed8"))  # Deep Blue

    # 2. Folder Front Body
    body_rect = QRectF(42 * scale, 115 * scale, 172 * scale, 90 * scale)
    body_path = QPainterPath()
    body_path.addRoundedRect(body_rect, 14 * scale, 14 * scale)

    body_grad = QLinearGradient(0, 115 * scale, 0, 205 * scale)
    body_grad.setColorAt(0.0, QColor("#3b82f6"))  # Blue 500
    body_grad.setColorAt(1.0, QColor("#1d4ed8"))  # Blue 700
    painter.fillPath(body_path, body_grad)

    body_pen = QPen(QColor(255, 255, 255, 50), 1.5 * scale)
    painter.strokePath(body_path, body_pen)

    # 3. Juggling Orbs in an arc above the folder
    orbs = [
        {"x": 68 * scale, "y": 72 * scale, "r": 18 * scale, "c1": "#34d399", "c2": "#059669"}, # Emerald (media/doc)
        {"x": 128 * scale, "y": 48 * scale, "r": 22 * scale, "c1": "#60a5fa", "c2": "#2563eb"}, # Blue Center (main)
        {"x": 188 * scale, "y": 72 * scale, "r": 18 * scale, "c1": "#fbbf24", "c2": "#d97706"}, # Amber (archive/data)
    ]

    for orb in orbs:
        cx, cy, r = orb["x"], orb["y"], orb["r"]
        orb_grad = QRadialGradient(cx - r * 0.3, cy - r * 0.3, r * 1.3)
        orb_grad.setColorAt(0.0, QColor(orb["c1"]))
        orb_grad.setColorAt(1.0, QColor(orb["c2"]))

        painter.setBrush(QBrush(orb_grad))
        painter.setPen(QPen(QColor(255, 255, 255, 120), 1.2 * scale))
        painter.drawEllipse(QPointF(cx, cy), r, r)

    # 4. Subtle swoosh / juggle motion curve
    arc_path = QPainterPath()
    arc_path.moveTo(68 * scale, 86 * scale)
    arc_path.quadTo(128 * scale, 26 * scale, 188 * scale, 86 * scale)
    arc_pen = QPen(QColor(255, 255, 255, 70), 2.5 * scale, Qt.DashLine)
    painter.strokePath(arc_path, arc_pen)

    painter.end()
    return image


def save_multi_res_ico(png_data_dict: dict, output_ico_path: Path):
    """
    Pack multiple PNG buffers into a valid Windows .ico container.
    png_data_dict: {size: bytes_of_png}
    """
    num_images = len(png_data_dict)
    header = struct.pack("<HHH", 0, 1, num_images)
    
    entries = bytearray()
    image_data_block = bytearray()
    
    # Calculate offset where image raw data starts:
    # 6 bytes header + (16 bytes * num_images)
    current_offset = 6 + (16 * num_images)
    
    for size, png_bytes in sorted(png_data_dict.items()):
        width = 0 if size >= 256 else size
        height = 0 if size >= 256 else size
        color_count = 0
        reserved = 0
        planes = 1
        bpp = 32
        bytes_in_res = len(png_bytes)
        
        entry = struct.pack(
            "<BBBBHHII",
            width,
            height,
            color_count,
            reserved,
            planes,
            bpp,
            bytes_in_res,
            current_offset
        )
        entries.extend(entry)
        image_data_block.extend(png_bytes)
        current_offset += bytes_in_res
        
    with open(output_ico_path, "wb") as f:
        f.write(header)
        f.write(entries)
        f.write(image_data_block)


def main():
    app = QGuiApplication.instance() or QGuiApplication(sys.argv)

    project_root = Path(__file__).resolve().parent.parent
    assets_dir = project_root / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    sizes = [16, 32, 48, 64, 128, 256]
    png_dict = {}

    for size in sizes:
        img = create_icon_image(size)
        temp_png = assets_dir / f"icon_{size}.png"
        img.save(str(temp_png), "PNG")
        with open(temp_png, "rb") as f:
            png_dict[size] = f.read()
        
        # Keep 256 as the primary icon.png
        if size == 256:
            primary_png = assets_dir / "icon.png"
            img.save(str(primary_png), "PNG")

        # Clean temp individual size files
        temp_png.unlink()

    ico_path = assets_dir / "icon.ico"
    save_multi_res_ico(png_dict, ico_path)
    print(f"Generated multi-resolution ICO at: {ico_path} ({ico_path.stat().st_size} bytes)")
    print(f"Generated primary PNG at: {assets_dir / 'icon.png'}")


if __name__ == "__main__":
    main()
