# Import PyQt5 widgets
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QComboBox,
                             QFileDialog, QMessageBox, QSizePolicy, QSlider,
                             QSpinBox)
from PyQt5.QtGui import QPixmap, QImage, QFont
from PyQt5.QtCore import Qt
import sys
from PIL import Image

# ── Retro QSS stylesheet ──────────────────────────────────────────────────
RETRO_QSS = """
QMainWindow {
    background-color: #0a0a0a;
    color: #33ff33;
    font-family: 'monospace', monospace;
}
QPushButton {
    background-color: #1a1a2e;
    color: #33ff33;
    border: 2px solid #33ff33;
    border-radius: 0px;
    padding: 8px 16px;
    font-size: 14px;
}
QPushButton:hover {
    background-color: #0f3460;
    border-color: #00ffff;
    color: #00ffff;
}
QPushButton:pressed {
    background-color: #16213e;
    border-color: #ff00ff;
    color: #ff00ff;
}
QLabel {
    color: #33ff33;
    font-size: 13px;
}
QComboBox {
    background-color: #1a1a2e;
    color: #33ff33;
    border: 2px solid #33ff33;
    border-radius: 0px;
    padding: 4px 8px;
}
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QComboBox QAbstractItemView {
    background-color: #1a1a2e;
    color: #33ff33;
    selection-background-color: #0f3460;
}
QSlider::groove:horizontal {
    background: #1a1a2e;
    height: 6px;
    border: 1px solid #33ff33;
}
QSlider::handle:horizontal {
    background: #33ff33;
    width: 14px;
    height: 14px;
    margin: -4px 0;
    border-radius: 0px;
}
QSlider::handle:horizontal:hover {
    background: #00ffff;
}
QSpinBox {
    background-color: #1a1a2e;
    color: #33ff33;
    border: 2px solid #33ff33;
    border-radius: 0px;
    padding: 4px 8px;
}
QSpinBox::up-button, QSpinBox::down-button {
    background: #1a1a2e;
    border: 1px solid #33ff33;
    width: 16px;
}
"""


class DitherWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("DitherPy")
        self.setMinimumSize(700, 520)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # ── Title ──────────────────────────────────────────────────────
        title = QLabel("═══ DITHERPY ENGINE ═══")
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont("monospace", 18, QFont.Bold))
        layout.addWidget(title)

        # ── Controls row 1: buttons ────────────────────────────────────
        controls1 = QHBoxLayout()

        self.load_btn = QPushButton("[ LOAD ]")
        self.load_btn.clicked.connect(self.load_image)
        controls1.addWidget(self.load_btn)

        self.dither_btn = QPushButton("[ DITHER ]")
        self.dither_btn.clicked.connect(self.apply_dithering)
        controls1.addWidget(self.dither_btn)

        self.save_btn = QPushButton("[ SAVE ]")
        self.save_btn.clicked.connect(self.save_image)
        controls1.addWidget(self.save_btn)

        layout.addLayout(controls1)

        # ── Controls row 2: method + color depth ───────────────────────
        controls2 = QHBoxLayout()

        controls2.addWidget(QLabel("METHOD:"))
        self.method_combo = QComboBox()
        self.method_combo.addItems(["FLOYD STEINBERG", "NONE"])
        self.method_combo.setCurrentIndex(0)
        controls2.addWidget(self.method_combo)

        controls2.addWidget(QLabel("COLORS:"))
        self.depth_combo = QComboBox()
        self.depth_combo.addItems(["2", "4", "8", "16", "32", "64", "128", "256"])
        self.depth_combo.setCurrentIndex(2)  # default: 8 colors
        controls2.addWidget(self.depth_combo)

        layout.addLayout(controls2)

        # ── Controls row 3: blend slider ───────────────────────────────
        controls3 = QHBoxLayout()

        controls3.addWidget(QLabel("BLEND:"))
        self.blend_slider = QSlider(Qt.Horizontal)
        self.blend_slider.setRange(0, 100)
        self.blend_slider.setValue(100)
        self.blend_slider.setSingleStep(5)
        self.blend_slider.valueChanged.connect(self.update_blend_label)
        controls3.addWidget(self.blend_slider)

        self.blend_label = QLabel("100%")
        self.blend_label.setFixedWidth(48)
        controls3.addWidget(self.blend_label)

        layout.addLayout(controls3)

        # ── Image display ──────────────────────────────────────────────
        self.image_label = QLabel("NO IMAGE LOADED")
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.image_label.setMinimumHeight(300)
        self.image_label.setStyleSheet(
            "border: 2px solid #1a1a2e; background-color: #050505;"
        )
        layout.addWidget(self.image_label)

        # ── Status bar ─────────────────────────────────────────────────
        self.status = QLabel("READY_")
        self.status.setStyleSheet("color: #555;")
        layout.addWidget(self.status)

        # Internal state
        self.original_image = None
        self.dithered_image = None

    def update_blend_label(self, value):
        """Update the percentage label when the slider moves."""
        self.blend_label.setText(f"{value}%")
        # If we already have a dithered image, re-apply with new blend
        if self.original_image is not None and self.dithered_image is not None:
            self.apply_dithering()

    def load_image(self):
        """Open a file dialog and load an image."""
        path, _ = QFileDialog.getOpenFileName(
            self, "Load Image", "",
            "Images (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if not path:
            return

        self.original_image = Image.open(path)
        self.dithered_image = None
        self.display_image(self.original_image)
        self.status.setText(f"LOADED: {path.split('/')[-1]}_")

    def apply_dithering(self):
        """Apply dithering with selected method, color depth, and blend."""
        if self.original_image is None:
            QMessageBox.warning(self, "ERROR", "LOAD AN IMAGE FIRST_")
            return

        method = self.method_combo.currentText()
        colors = int(self.depth_combo.currentText())
        blend_pct = self.blend_slider.value()  # 0-100

        # Map method string to Pillow constant
        dither_map = {
            "FLOYD STEINBERG": Image.Dither.FLOYDSTEINBERG,
            "NONE":            Image.Dither.NONE,
        }
        dither_const = dither_map.get(method, Image.Dither.FLOYDSTEINBERG)

        # Convert to palette mode with chosen color count
        # Fewer colors = more aggressive dithering
        dithered = self.original_image.convert(
            "P", palette=Image.ADAPTIVE, colors=colors, dither=dither_const
        )

        # Blend: 0% = original, 100% = fully dithered
        # Image.blend(img1, img2, alpha) → alpha=0 gives img1, alpha=1 gives img2
        if blend_pct < 100:
            # Both must be same mode and size for blending
            orig_rgb = self.original_image.convert("RGB")
            dithered_rgb = dithered.convert("RGB")
            # Make sure sizes match (they should, but be safe)
            if orig_rgb.size != dithered_rgb.size:
                dithered_rgb = dithered_rgb.resize(orig_rgb.size, Image.NEAREST)
            alpha = blend_pct / 100.0
            result = Image.blend(orig_rgb, dithered_rgb, alpha)
        else:
            result = dithered

        self.dithered_image = result
        self.display_image(result)
        self.status.setText(
            f"DITHERED [{method}] {colors}C {blend_pct}%_"
        )

    def save_image(self):
        """Save the dithered image to disk."""
        if self.dithered_image is None:
            QMessageBox.warning(self, "ERROR", "NOTHING TO SAVE_")
            return

        path, _ = QFileDialog.getSaveFileName(
            self, "Save Image", "", "PNG (*.png);;JPEG (*.jpg)"
        )
        if not path:
            return

        self.dithered_image.save(path)
        self.status.setText(f"SAVED: {path.split('/')[-1]}_")

    def display_image(self, pil_img):
        """Convert PIL Image → QPixmap and show it."""
        img = pil_img.copy()
        img.thumbnail((500, 400), Image.NEAREST)
        img_rgb = img.convert("RGB")
        data = img_rgb.tobytes()
        width, height = img_rgb.size
        qimg = QImage(data, width, height, 3 * width, QImage.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        self.image_label.setScaledContents(True)
        self.image_label.setPixmap(pixmap)


# ── Entry point ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet(RETRO_QSS)
    window = DitherWindow()
    window.show()
    sys.exit(app.exec_())   
