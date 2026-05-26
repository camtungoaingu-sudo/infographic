from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
    QMessageBox,
)

from pixel_to_vector.core.exporter import export_svg_from_rgba
from pixel_to_vector.utils.image_utils import load_rgba


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pixel to Vector")
        self.resize(1100, 700)

        self.image_path: str | None = None

        central = QWidget()
        layout = QHBoxLayout(central)

        self.preview = QLabel("Mở ảnh để bắt đầu")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(700, 600)
        layout.addWidget(self.preview, 3)

        right = QVBoxLayout()
        self.k_slider = QSlider(Qt.Horizontal)
        self.k_slider.setRange(2, 32)
        self.k_slider.setValue(10)
        self.k_label = QLabel("Số màu (K): 10")
        self.k_slider.valueChanged.connect(lambda v: self.k_label.setText(f"Số màu (K): {v}"))

        btn_open = QPushButton("Mở ảnh")
        btn_open.clicked.connect(self.open_image)
        btn_export = QPushButton("Xuất SVG")
        btn_export.clicked.connect(self.export_svg)

        right.addWidget(self.k_label)
        right.addWidget(self.k_slider)
        right.addWidget(btn_open)
        right.addWidget(btn_export)
        right.addStretch(1)

        layout.addLayout(right, 1)
        self.setCentralWidget(central)

        file_menu = self.menuBar().addMenu("File")
        act_open = QAction("Open", self)
        act_open.triggered.connect(self.open_image)
        file_menu.addAction(act_open)

    def open_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Chọn ảnh", "", "Images (*.png *.jpg *.jpeg *.webp)")
        if not path:
            return
        self.image_path = path
        pix = QPixmap(path)
        self.preview.setPixmap(pix.scaled(self.preview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def export_svg(self):
        if not self.image_path:
            QMessageBox.warning(self, "Thiếu ảnh", "Vui lòng mở ảnh trước.")
            return
        out_path, _ = QFileDialog.getSaveFileName(self, "Lưu SVG", str(Path(self.image_path).with_suffix('.svg')), "SVG (*.svg)")
        if not out_path:
            return
        rgba = load_rgba(self.image_path)
        export_svg_from_rgba(rgba, out_path, k=self.k_slider.value())
        QMessageBox.information(self, "Hoàn tất", f"Đã xuất: {out_path}")


def main():
    app = QApplication(sys.argv)
    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
