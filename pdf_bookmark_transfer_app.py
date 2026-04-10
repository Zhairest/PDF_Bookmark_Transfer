#!/usr/bin/env python3
"""Qt desktop app for copying PDF bookmarks onto another PDF."""

from __future__ import annotations

import sys
from pathlib import Path

from merge_pdf_bookmarks import (
    build_output_path,
    default_output_filename,
    merge_bookmarks,
    normalize_output_filename,
    validate_paths,
)

PYSIDE6_IMPORT_ERROR: ImportError | None = None

try:
    from PySide6.QtCore import QObject, QThread, QTimer, Qt, Signal, Slot
    from PySide6.QtGui import QFont
    from PySide6.QtWidgets import (
        QApplication,
        QFileDialog,
        QGridLayout,
        QGroupBox,
        QHBoxLayout,
        QLabel,
        QLineEdit,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSizePolicy,
        QVBoxLayout,
        QWidget,
    )
except ImportError as exc:  # pragma: no cover - depends on local environment
    PYSIDE6_IMPORT_ERROR = exc


MISSING_PYSIDE6_MESSAGE = (
    "PySide6 / Qt is not installed.\n\n"
    "Install the GUI dependency with:\n"
    "  python3 -m pip install PySide6-Essentials shiboken6\n"
)


if PYSIDE6_IMPORT_ERROR is None:

    class MergeWorker(QObject):
        finished = Signal(str, int)
        failed = Signal(str)

        def __init__(
            self,
            content_path: Path,
            bookmarks_path: Path,
            output_path: Path,
        ) -> None:
            super().__init__()
            self.content_path = content_path
            self.bookmarks_path = bookmarks_path
            self.output_path = output_path

        @Slot()
        def run(self) -> None:
            try:
                copied_count = merge_bookmarks(
                    self.content_path,
                    self.bookmarks_path,
                    self.output_path,
                )
            except Exception as exc:
                self.failed.emit(str(exc))
                return

            self.finished.emit(str(self.output_path), copied_count)


    class PdfBookmarkTransferWindow(QMainWindow):
        def __init__(self) -> None:
            super().__init__()
            self.worker_thread: QThread | None = None
            self.worker: MergeWorker | None = None
            self._interactive_widgets: list[QWidget] = []

            self.setWindowTitle("PDF 目录转移")
            self.resize(900, 560)
            self.setMinimumSize(800, 500)

            self._build_ui()
            self._connect_signals()
            self.refresh_output_preview()
            QTimer.singleShot(120, self.present_window)

        def _build_ui(self) -> None:
            central_widget = QWidget(self)
            self.setCentralWidget(central_widget)

            root_layout = QVBoxLayout(central_widget)
            root_layout.setContentsMargins(22, 20, 22, 20)
            root_layout.setSpacing(16)

            title_label = QLabel("PDF 目录转移")
            title_font = QFont()
            title_font.setPointSize(18)
            title_font.setBold(True)
            title_label.setFont(title_font)
            root_layout.addWidget(title_label)

            intro_label = QLabel(
                "保留高清内容 PDF 的页面内容，同时把目录来源 PDF 的侧边目录复制过去。"
                "保存位置默认与高清内容 PDF 相同，输出文件名可自行修改。"
            )
            intro_label.setWordWrap(True)
            intro_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root_layout.addWidget(intro_label)

            file_group = QGroupBox("文件设置")
            file_layout = QGridLayout(file_group)
            file_layout.setHorizontalSpacing(12)
            file_layout.setVerticalSpacing(12)
            file_layout.setColumnStretch(1, 1)
            root_layout.addWidget(file_group)

            self.content_input = self._create_line_edit(
                "选择要保留页面内容的高清 PDF"
            )
            self.bookmarks_input = self._create_line_edit(
                "选择带侧边目录的 PDF"
            )
            self.output_dir_input = self._create_line_edit("默认与高清内容 PDF 相同")
            self.output_name_input = self._create_line_edit("例如：文档_with_bookmarks.pdf")
            self.output_preview_label = QLabel("输出路径会显示在这里")
            self.output_preview_label.setWordWrap(True)
            self.output_preview_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.output_preview_label.setFrameShape(QLabel.Shape.StyledPanel)
            self.output_preview_label.setMargin(10)
            self.output_preview_label.setSizePolicy(
                QSizePolicy.Policy.Expanding,
                QSizePolicy.Policy.MinimumExpanding,
            )

            self.choose_content_button = self._create_button("选择文件")
            self.choose_bookmarks_button = self._create_button("选择文件")
            self.choose_output_dir_button = self._create_button("选择位置")
            self.reset_defaults_button = self._create_button("恢复默认")
            self.convert_button = self._create_button("开始转换", primary=True)

            self._add_form_row(
                file_layout,
                0,
                "高清内容 PDF",
                self.content_input,
                self.choose_content_button,
            )
            self._add_form_row(
                file_layout,
                1,
                "目录来源 PDF",
                self.bookmarks_input,
                self.choose_bookmarks_button,
            )
            self._add_form_row(
                file_layout,
                2,
                "保存位置",
                self.output_dir_input,
                self.choose_output_dir_button,
            )
            self._add_form_row(
                file_layout,
                3,
                "输出文件名",
                self.output_name_input,
                self.reset_defaults_button,
            )

            preview_title = QLabel("输出路径预览")
            preview_title.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
            file_layout.addWidget(preview_title, 4, 0)
            file_layout.addWidget(self.output_preview_label, 4, 1, 1, 2)

            note_label = QLabel(
                "默认保存到高清内容 PDF 所在文件夹；若目标文件已存在，转换前会提示是否覆盖。"
            )
            note_label.setWordWrap(True)
            note_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            file_layout.addWidget(note_label, 5, 0, 1, 3)

            action_layout = QHBoxLayout()
            action_layout.addStretch(1)
            action_layout.addWidget(self.convert_button)
            root_layout.addLayout(action_layout)

            self.status_label = QLabel("请选择两份 PDF 后开始转换。")
            self.status_label.setWordWrap(True)
            self.status_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
            root_layout.addWidget(self.status_label)

        def _connect_signals(self) -> None:
            self.choose_content_button.clicked.connect(self.choose_content_pdf)
            self.choose_bookmarks_button.clicked.connect(self.choose_bookmarks_pdf)
            self.choose_output_dir_button.clicked.connect(self.choose_output_dir)
            self.reset_defaults_button.clicked.connect(self.reset_output_defaults)
            self.convert_button.clicked.connect(self.start_conversion)

            self.content_input.textChanged.connect(self.refresh_output_preview)
            self.output_dir_input.textChanged.connect(self.refresh_output_preview)
            self.output_name_input.textChanged.connect(self.refresh_output_preview)

        def _create_line_edit(self, placeholder: str) -> QLineEdit:
            line_edit = QLineEdit()
            line_edit.setPlaceholderText(placeholder)
            line_edit.setMinimumHeight(38)
            line_edit.setClearButtonEnabled(True)
            self._interactive_widgets.append(line_edit)
            return line_edit

        def _create_button(self, text: str, *, primary: bool = False) -> QPushButton:
            button = QPushButton(text)
            button.setMinimumHeight(40)
            button.setMinimumWidth(128 if primary else 118)
            self._interactive_widgets.append(button)
            return button

        def _add_form_row(
            self,
            layout: QGridLayout,
            row: int,
            label_text: str,
            field: QWidget,
            button: QPushButton,
        ) -> None:
            label = QLabel(label_text)
            layout.addWidget(label, row, 0)
            layout.addWidget(field, row, 1)
            layout.addWidget(button, row, 2)

        def present_window(self) -> None:
            self.showNormal()
            self.raise_()
            self.activateWindow()

        def refresh_output_preview(self) -> None:
            content_text = self.content_input.text().strip()
            output_dir_text = self.output_dir_input.text().strip()
            output_name_text = self.output_name_input.text().strip()

            if not content_text:
                self.output_preview_label.setText("输出路径会显示在这里")
                return

            try:
                content_path = Path(content_text).expanduser().resolve()
                output_dir = (
                    Path(output_dir_text).expanduser().resolve() if output_dir_text else None
                )
                output_path = build_output_path(
                    content_path,
                    output_dir=output_dir,
                    output_name=output_name_text or None,
                )
            except Exception:
                self.output_preview_label.setText("当前输出文件名或保存位置无效，请检查。")
                return

            self.output_preview_label.setText(str(output_path))

        def choose_content_pdf(self) -> None:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "选择高清内容 PDF",
                str(Path.home()),
                "PDF Files (*.pdf);;All Files (*)",
            )
            self.present_window()
            if not selected:
                return

            content_path = Path(selected).expanduser().resolve()
            self.content_input.setText(str(content_path))
            self.output_dir_input.setText(str(content_path.parent))
            self.output_name_input.setText(default_output_filename(content_path))
            self.status_label.setText("已选择高清内容 PDF，请继续选择目录来源 PDF。")

        def choose_bookmarks_pdf(self) -> None:
            selected, _ = QFileDialog.getOpenFileName(
                self,
                "选择目录来源 PDF",
                self.content_input.text().strip() or str(Path.home()),
                "PDF Files (*.pdf);;All Files (*)",
            )
            self.present_window()
            if not selected:
                return

            self.bookmarks_input.setText(str(Path(selected).expanduser().resolve()))
            self.status_label.setText("已选择目录来源 PDF，可以开始转换了。")

        def choose_output_dir(self) -> None:
            initial_dir = self.output_dir_input.text().strip()
            if not initial_dir and self.content_input.text().strip():
                initial_dir = str(
                    Path(self.content_input.text().strip()).expanduser().resolve().parent
                )

            selected = QFileDialog.getExistingDirectory(
                self,
                "选择保存位置",
                initial_dir or str(Path.home()),
            )
            self.present_window()
            if not selected:
                return

            self.output_dir_input.setText(str(Path(selected).expanduser().resolve()))
            self.status_label.setText("已更新保存位置。")

        def reset_output_defaults(self) -> None:
            content_text = self.content_input.text().strip()
            if not content_text:
                QMessageBox.information(self, "需要先选文件", "请先选择高清内容 PDF。")
                self.present_window()
                return

            content_path = Path(content_text).expanduser().resolve()
            self.output_dir_input.setText(str(content_path.parent))
            self.output_name_input.setText(default_output_filename(content_path))
            self.status_label.setText("已恢复默认输出名称和保存位置。")

        def start_conversion(self) -> None:
            try:
                content_path, bookmarks_path, output_path = self._collect_paths()
                validate_paths(
                    content_path,
                    bookmarks_path,
                    output_path,
                    allow_overwrite=False,
                )
            except FileExistsError:
                answer = QMessageBox.question(
                    self,
                    "确认覆盖",
                    f"输出文件已存在，是否覆盖？\n\n{output_path}",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                    QMessageBox.StandardButton.No,
                )
                self.present_window()
                if answer != QMessageBox.StandardButton.Yes:
                    self.status_label.setText("已取消转换。")
                    return
            except Exception as exc:
                QMessageBox.critical(self, "无法开始转换", str(exc))
                self.status_label.setText("参数检查未通过，请调整后重试。")
                self.present_window()
                return

            self._set_busy(True, "正在转换，请稍候...")

            self.worker_thread = QThread(self)
            self.worker = MergeWorker(content_path, bookmarks_path, output_path)
            self.worker.moveToThread(self.worker_thread)

            self.worker_thread.started.connect(self.worker.run)
            self.worker.finished.connect(self._handle_conversion_success)
            self.worker.failed.connect(self._handle_conversion_failure)

            self.worker.finished.connect(self.worker_thread.quit)
            self.worker.failed.connect(self.worker_thread.quit)
            self.worker_thread.finished.connect(self._cleanup_worker)

            self.worker_thread.start()

        def _collect_paths(self) -> tuple[Path, Path, Path]:
            content_text = self.content_input.text().strip()
            bookmarks_text = self.bookmarks_input.text().strip()
            output_dir_text = self.output_dir_input.text().strip()
            output_name_text = self.output_name_input.text().strip()

            if not content_text:
                raise ValueError("请先选择高清内容 PDF。")
            if not bookmarks_text:
                raise ValueError("请先选择目录来源 PDF。")

            content_path = Path(content_text).expanduser().resolve()
            bookmarks_path = Path(bookmarks_text).expanduser().resolve()
            output_dir = (
                Path(output_dir_text).expanduser().resolve()
                if output_dir_text
                else content_path.parent
            )
            output_name = normalize_output_filename(output_name_text)
            output_path = build_output_path(
                content_path,
                output_dir=output_dir,
                output_name=output_name,
            )
            return content_path, bookmarks_path, output_path

        @Slot(str, int)
        def _handle_conversion_success(self, output_path: str, copied_count: int) -> None:
            self._set_busy(False, f"转换完成，共复制 {copied_count} 个目录项。")
            QMessageBox.information(
                self,
                "转换完成",
                f"新的 PDF 已生成：\n\n{output_path}\n\n复制的目录项数量：{copied_count}",
            )
            self.present_window()

        @Slot(str)
        def _handle_conversion_failure(self, error_message: str) -> None:
            self._set_busy(False, "转换失败，请检查文件后重试。")
            QMessageBox.critical(self, "转换失败", error_message)
            self.present_window()

        @Slot()
        def _cleanup_worker(self) -> None:
            if self.worker is not None:
                self.worker.deleteLater()
                self.worker = None
            if self.worker_thread is not None:
                self.worker_thread.deleteLater()
                self.worker_thread = None

        def _set_busy(self, busy: bool, status: str) -> None:
            for widget in self._interactive_widgets:
                widget.setEnabled(not busy)
            self.status_label.setText(status)


def main() -> int:
    if PYSIDE6_IMPORT_ERROR is not None:
        print(MISSING_PYSIDE6_MESSAGE, file=sys.stderr)
        return 1

    app = QApplication(sys.argv)
    app.setApplicationName("PDF 目录转移")

    window = PdfBookmarkTransferWindow()
    window.show()
    window.present_window()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
