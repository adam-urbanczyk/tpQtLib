#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains extended Qt dialog classes
"""

from __future__ import print_function, division, absolute_import

import os
import string
import getpass
from functools import partial

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpQtLib
import tpDccLib as tp
from tpQtLib.core import qtutils, color, animation, theme, dragger
from tpQtLib.widgets import splitters


class Dialog(QDialog, object):
    """
    Class to create basic Maya docked windows
    """

    dialogClosed = Signal()

    def __init__(self, parent=None, **kwargs):

        title = kwargs.get('title', '')
        name = title or self.__class__.__name__

        # Remove previous dialogs
        main_window = tp.Dcc.get_main_window()
        if main_window:
            wins = tp.Dcc.get_main_window().findChildren(QWidget, name) or list()
            for w in wins:
                w.close()
                w.deleteLater()

        if parent is None:
            parent = main_window
        super(Dialog, self).__init__(parent=parent)

        self._theme = None
        self._dpi = kwargs.get('dpi', 1.0)
        self._show_dragger = kwargs.get('show_dragger', True)
        self._fixed_size = kwargs.get('fixed_size', False)
        self._has_title = kwargs.pop('has_title', False)
        self._size = kwargs.pop('size', (200, 125))
        self._title_pixmap = kwargs.pop('title_pixmap', None)
        show_on_initialize = kwargs.get('show_on_initialize', False)
        width = kwargs.pop('width', 600)
        height = kwargs.pop('height', 800)

        self.setObjectName(name)
        self.setFocusPolicy(Qt.StrongFocus)

        if self._show_dragger:
            self.setAttribute(Qt.WA_TranslucentBackground)
            if qtutils.is_pyside2():
                self.setWindowFlags(self.windowFlags() | Qt.FramelessWindowHint)
            else:
                self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)

        self.ui()
        self.setup_signals()

        self.setWindowTitle(title)

        auto_load = kwargs.get('auto_load', True)
        if auto_load:
            self.load_theme()

        if show_on_initialize:
            self.center()
            self.show()
            
        self.resize(width, height)

    def default_settings(self):
        """
        Returns default settings values
        :return: dict
        """

        return {
            "theme": {
            "accentColor": "rgb(80, 80, 80, 255)",
            "backgroundColor": "rgb(45, 45, 45, 255)",
            }
        }

    def load_theme(self):
        def_settings = self.default_settings()
        def_theme_settings = def_settings.get('theme')
        theme_settings = {
            "accentColor": def_theme_settings['accentColor'],
            "backgroundColor": def_theme_settings['backgroundColor']
        }
        self.set_theme_settings(theme_settings)

    def set_width_height(self, width, height):
        """
        Sets the width and height of the dialog
        :param width: int
        :param height: int
        """

        x = self.geometry().x()
        y = self.geometry().y()
        self.setGeometry(x, y, width, height)

    def center(self, to_cursor=False):
        """
        Move the dialog to the center of the current window
        """

        frame_geo = self.frameGeometry()
        if to_cursor:
            pos = QApplication.desktop().cursor().pos()
            screen = QApplication.desktop().screenNumber(pos)
            center_point = QApplication.desktop().screenGeometry(screen).center()
        else:
            center_point = QDesktopWidget().availableGeometry().center()
        frame_geo.moveCenter(center_point)
        self.move(frame_geo.topLeft())

    def fade_close(self):
        animation.fade_window(start=1, end=0, duration=400, object=self, on_finished=self.close)

    def get_main_layout(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        return main_layout

    def ui(self):

        dlg_layout = QVBoxLayout()
        dlg_layout.setContentsMargins(0, 0, 0, 0)
        dlg_layout.setSpacing(0)
        self.setLayout(dlg_layout)

        self._base_layout = QVBoxLayout()
        self._base_layout.setContentsMargins(0, 0, 0, 0)
        self._base_layout.setSpacing(0)
        self._base_layout.setAlignment(Qt.AlignTop)
        base_widget = QFrame()
        base_widget.setObjectName('mainFrame')
        base_widget.setFrameStyle(QFrame.NoFrame)
        base_widget.setFrameShadow(QFrame.Plain)
        base_widget.setStyleSheet("""
        QFrame#mainFrame
        {
        background-color: rgb(35, 35, 35);
        border-radius: 10px;
        }""")
        base_widget.setLayout(self._base_layout)
        dlg_layout.addWidget(base_widget)

        self._dragger = dragger.DialogDragger(parent=self)
        self._dragger.setVisible(self._show_dragger)
        self._base_layout.addWidget(self._dragger)

        self.main_layout = self.get_main_layout()
        self._base_layout.addLayout(self.main_layout)

        title_layout = QHBoxLayout()
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(0)
        title_layout.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        self.main_layout.addLayout(title_layout)

        self.logo_view = QGraphicsView()
        self.logo_view.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.logo_view.setMaximumHeight(100)
        self._logo_scene = QGraphicsScene()
        self._logo_scene.setSceneRect(QRectF(0, 0, 2000, 100))
        self.logo_view.setScene(self._logo_scene)
        self.logo_view.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logo_view.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.logo_view.setFocusPolicy(Qt.NoFocus)

        if self._has_title and self._title_pixmap:
            self._logo_scene.addPixmap(self._title_pixmap)
            title_layout.addWidget(self.logo_view)

        # title_background_pixmap = self._get_title_pixmap()
        # if self._has_title and title_background_pixmap:
        #     self._logo_scene.addPixmap(title_background_pixmap)
        #     title_layout.addWidget(self.logo_view)
        # else:
        #     self.logo_view.setVisible(False)

        if self._size:
            self.resize(self._size[0], self._size[1])

        self._status_bar = QStatusBar(self)
        dlg_layout.addWidget(self._status_bar)
        if self._fixed_size:
            self._status_bar.hide()

    def statusBar(self):
        """
        Returns status bar of the dialog
        :return: QStatusBar
        """

        return self._status_bar

    def dpi(self):
        """
        Return the current dpi for the window
        :return: float
        """

        return float(self._dpi)

    def set_dpi(self, dpi):
        """
        Sets current dpi for the window
        :param dpi: float
        """

        self._dpi = dpi

    def theme(self):
        """
        Returns the current theme
        :return: Theme
        """

        if not self._theme:
            self._theme = theme.Theme()

        return self._theme

    def set_theme(self, theme):
        """
        Sets current window theme
        :param theme: Theme
        """

        self._theme = theme
        self._theme.updated.connect(self.reload_stylesheet)
        self.reload_stylesheet()

    def set_theme_settings(self, settings):
        """
        Sets the theme settings from the given settings
        :param settings: dict
        """

        new_theme = theme.Theme()
        new_theme.set_settings(settings)
        self.set_theme(new_theme)

    def reload_stylesheet(self):
        """
        Reloads the stylesheet to the current theme
        """

        current_theme = self.theme()
        current_theme.set_dpi(self.dpi())
        options = current_theme.options()
        stylesheet = current_theme.stylesheet()

        all_widgets = self.main_layout.findChildren(QObject)

        text_color = color.Color.from_string(options["ITEM_TEXT_COLOR"])
        text_selected_color = color.Color.from_string(options["ITEM_TEXT_SELECTED_COLOR"])
        background_color = color.Color.from_string(options["ITEM_BACKGROUND_COLOR"])
        background_hover_color = color.Color.from_string(options["ITEM_BACKGROUND_HOVER_COLOR"])
        background_selected_color = color.Color.from_string(options["ITEM_BACKGROUND_SELECTED_COLOR"])

        self.setStyleSheet(stylesheet)

        for w in all_widgets:
            found = False
            if hasattr(w, 'set_text_color'):
                w.set_text_color(text_color)
                found = True
            if hasattr(w, 'set_text_selected_color'):
                w.set_text_selected_color(text_selected_color)
                found = True
            if hasattr(w, 'set_background_color'):
                w.set_background_color(background_color)
                found = True
            if hasattr(w, 'set_background_hover_color'):
                w.set_background_hover_color(background_hover_color)
                found = True
            if hasattr(w, 'set_background_selected_color'):
                w.set_background_selected_color(background_selected_color)
                found = True

            if found:
                w.update()
    
    def setup_signals(self):
        pass

    def set_logo(self, logo, offset=(930, 0)):
        logo = self._logo_scene.addPixmap(logo)
        logo.setOffset(offset[0], offset[1])

    def resizeEvent(self, event):
        # TODO: Take the width from the QGraphicsView not hardcoded :)
        self.logo_view.centerOn(1000, 0)
        return super(Dialog, self).resizeEvent(event)

    def closeEvent(self, event):
        self.dialogClosed.emit()
        event.accept()

    def setWindowIcon(self, icon):
        if self._show_dragger:
            self._dragger.set_icon(icon)
        super(Dialog, self).setWindowIcon(icon)

    def setWindowTitle(self, title):
        if self._show_dragger:
            self._dragger.set_title(title)
        super(Dialog, self).setWindowTitle(title)

    def _get_title_pixmap(self):
        """
        Internal function that sets the pixmap used for the title
        """

        return None


class ColorDialog(Dialog, object):

    def_title = 'Select Color'

    maya_colors = [(.467, .467, .467),(.000, .000, .000),(.247, .247, .247),(.498, .498, .498),(0.608, 0, 0.157),(0, 0.016, 0.373),(0, 0, 1),(0, 0.275, 0.094),(0.145, 0, 0.263),(0.78, 0, 0.78),(0.537, 0.278, 0.2),(0.243, 0.133, 0.122),(0.6, 0.145, 0),(1, 0, 0),(0, 1, 0),(0, 0.255, 0.6),(1, 1, 1),(1, 1, 0),(0.388, 0.863, 1),(0.263, 1, 0.635),(1, 0.686, 0.686),(0.89, 0.675, 0.475),(1, 1, 0.384),(0, 0.6, 0.325),(0.627, 0.412, 0.188),(0.62, 0.627, 0.188),(0.408, 0.627, 0.188),(0.188, 0.627, 0.365),(0.188, 0.627, 0.627),(0.188, 0.404, 0.627),(0.435, 0.188, 0.627),(0.627, 0.188, 0.404)]

    def __init__(self, name='MayaColorDialog', parent=None, **kwargs):
        if parent is None:
            parent = tp.Dcc.get_main_window()

        super(ColorDialog, self).__init__(name=name, parent=parent, **kwargs)

        self._color = None

    # region Properties
    def get_color(self):
        return self._color

    color = property(get_color)
    # endregion

    # region Override Functions
    def ui(self):

        self.color_buttons = list()

        super(ColorDialog, self).ui()

        if tp.Dcc.get_name() == tp.Dccs.Maya and tp.Dcc.get_version() <= 2016:
            self.color_dialog = QColorDialog(parent=self)
            self.color_dialog.setWindowFlags(Qt.Widget)
            self.color_dialog.setOptions(QColorDialog.DontUseNativeDialog | QColorDialog.NoButtons)
            self.main_layout.addWidget(self.color_dialog)
        else:
            grid_layout = QGridLayout()
            grid_layout.setAlignment(Qt.AlignTop)
            self.main_layout.addLayout(grid_layout)
            color_index = 0
            for i in range(0, 4):
                for j in range(0, 8):
                    color_btn = QPushButton()
                    color_btn.setMinimumHeight(35)
                    color_btn.setMinimumWidth(35)
                    self.color_buttons.append(color_btn)
                    color_btn.setStyleSheet('background-color:rgb(%s,%s,%s);' % (
                        self.maya_colors[color_index][0] * 255,
                        self.maya_colors[color_index][1] * 255,
                        self.maya_colors[color_index][2] * 255
                    ))
                    grid_layout.addWidget(color_btn, i, j)
                    color_index += 1
            selected_color_layout = QHBoxLayout()
            self.main_layout.addLayout(selected_color_layout)
            self.color_slider = QSlider(Qt.Horizontal)
            self.color_slider.setMinimum(0)
            self.color_slider.setMaximum(31)
            self.color_slider.setValue(2)
            self.color_slider.setStyleSheet("QSlider::groove:horizontal {border: 1px solid #999999;height: 25px; /* the groove expands to the size of the slider by default. by giving it a height, it has a fixed size */background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #B1B1B1, stop:1 #c4c4c4);margin: 2px 0;}QSlider::handle:horizontal {background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #b4b4b4, stop:1 #8f8f8f);border: 1px solid #5c5c5c;width: 10px;margin: -2px 0; /* handle is placed by default on the contents rect of the groove. Expand outside the groove */border-radius: 1px;}")
            selected_color_layout.addWidget(self.color_slider)

            color_label_layout = QHBoxLayout()
            color_label_layout.setContentsMargins(10, 10, 10, 0)
            self.main_layout.addLayout(color_label_layout)

            self.color_lbl = QLabel()
            self.color_lbl.setStyleSheet("border: 1px solid black; background-color:rgb(0, 0, 0);")
            self.color_lbl.setMinimumWidth(45)
            self.color_lbl.setMaximumWidth(80)
            self.color_lbl.setMinimumHeight(80)
            self.color_lbl.setAlignment(Qt.AlignCenter)
            color_label_layout.addWidget(self.color_lbl)

        bottom_layout = QHBoxLayout()
        bottom_layout.setAlignment(Qt.AlignRight)
        self.main_layout.addLayout(bottom_layout)

        self.ok_btn = QPushButton('Ok')
        self.cancel_btn = QPushButton('Cancel')
        bottom_layout.addLayout(splitters.SplitterLayout())
        bottom_layout.addWidget(self.ok_btn)
        bottom_layout.addWidget(self.cancel_btn)

    def setup_signals(self):

        if tp.Dcc.get_name() == tp.Dccs.Maya and tp.Dcc.get_version() <= 2016:
            pass
        else:
            for i, btn in enumerate(self.color_buttons):
                btn.clicked.connect(partial(self._on_set_color, i))
            self.color_slider.valueChanged.connect(self._on_set_color)

        self.ok_btn.clicked.connect(self._on_ok_btn)
        self.cancel_btn.clicked.connect(self._on_cancel_btn)
    # endregion

    # region Private Functions
    def _on_set_color(self, color_index):

        if tp.Dcc.get_name() == tp.Dccs.Maya and tp.Dcc.get_version() <= 2016:
            self.color_dialog.setCurrentColor(QColor.fromRgb(
                self.maya_colors[color_index][0] * 255,
                self.maya_colors[color_index][1] * 255,
                self.maya_colors[color_index][2] * 255
            ))
        else:
            self.color_lbl.setStyleSheet('background-color:rgb(%s,%s,%s);' % (
                self.maya_colors[color_index][0] * 255,
                self.maya_colors[color_index][1] * 255,
                self.maya_colors[color_index][2] * 255
            ))
            self.color_slider.setValue(color_index)

    def _on_set_slider(self, color_index):
        self._set_color(color_index=color_index)

    def _on_ok_btn(self):

        if tp.Dcc.get_name() == tp.Dccs.Maya and tp.Dcc.get_version() <= 2016:
            pass
        else:
            self._color = self.color_slider.value()

        self.close()

    def _on_cancel_btn(self):
        self._color = None
        self.close()


class BaseFileFolderDialog(Dialog, object):
    """
    Base dialog classes for folders and files
    """

    def_title = 'Select File'
    def_size = (200, 125)
    def_use_app_browser = False

    def __init__(self,
                 name='BaseFileFolder', parent=None, **kwargs):
        super(BaseFileFolderDialog, self).__init__(name=name, parent=parent)

        self.directory = None
        self.filters = None
        self._use_app_browser = kwargs.pop('use_app_browser', self.def_use_app_browser)

        self.set_filters('All Files (*.*)')

        # By default, we set the directory to the user folder
        self.set_directory(os.path.expanduser('~'))
        self.center()

    # region To Override Functions
    def open_app_browser(self):
        return
    # endregion

    # region Override Functions
    def ui(self):
        super(BaseFileFolderDialog, self).ui()

        from tpQtLib.widgets import directory

        self.places = dict()

        self.grid = QGridLayout()
        sub_grid = QGridLayout()
        self.grid.addWidget(QLabel('Path:'), 0, 0, Qt.AlignRight)

        self.path_edit = QLineEdit(self)
        self.path_edit.setReadOnly(True)
        self.filter_box = QComboBox(self)
        self.file_edit = QLineEdit(self)

        self.view = directory.FileListWidget(self)
        self.view.setWrapping(True)
        self.view.setFocusPolicy(Qt.StrongFocus)

        self.open_button = QPushButton('Select', self)
        self.cancel_button = QPushButton('Cancel', self)

        size = QSize(32, 24)
        self.up_button = QPushButton('Up')
        self.up_button.setToolTip('Go up')
        self.up_button.setMinimumSize(size)
        self.up_button.setMaximumSize(size)

        size = QSize(56, 24)
        self.refresh_button = QPushButton('Reload')
        self.refresh_button.setToolTip('Reload file list')
        self.refresh_button.setMinimumSize(size)
        self.refresh_button.setMaximumSize(size)

        self.show_hidden = QCheckBox('Hidden')
        self.show_hidden.setChecked(False)
        self.show_hidden.setToolTip('Toggle show hidden files')

        sub_grid.addWidget(self.up_button, 0, 1)
        sub_grid.addWidget(self.path_edit, 0, 2)
        sub_grid.addWidget(self.refresh_button, 0, 3)
        sub_grid.addWidget(self.show_hidden, 0, 4)
        self.grid.addLayout(sub_grid, 0, 1)
        self.grid.addWidget(self.get_drives_widget(), 1, 0)
        self.grid.addWidget(self.view, 1, 1)
        self.grid.addWidget(QLabel('File name:'), 7, 0, Qt.AlignRight)
        self.grid.addWidget(self.file_edit, 7, 1)
        self.filter_label = QLabel('Filter:')
        self.grid.addWidget(self.filter_label, 8, 0, Qt.AlignRight)
        self.grid.addWidget(self.filter_box, 8, 1)
        hbox = QGridLayout()
        hbox.addWidget(self.open_button, 0, 0, Qt.AlignRight)
        hbox.addWidget(self.cancel_button, 0, 1, Qt.AlignRight)
        self.grid.addLayout(hbox, 9, 1, Qt.AlignRight)
        self.main_layout.addLayout(self.grid)
        self.setGeometry(200, 100, 600, 400)

        self.open_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)
        self.up_button.clicked.connect(self.go_up)
        self.refresh_button.clicked.connect(self.update_view)
        self.show_hidden.stateChanged.connect(self.update_view)
        self.view.directory_activated.connect(self.activate_directory_from_view)
        self.view.file_activated.connect(self.activate_file_from_view)
        self.view.file_selected.connect(self.select_file_item)
        self.view.folder_selected.connect(self.select_folder_item)
        self.view.up_requested.connect(self.go_up)
        self.view.update_requested.connect(self.update_view)

    def exec_(self, *args, **kwargs):
        if self._use_app_browser:
            return self.open_app_browser()
        else:
            self.update_view()
            self.filter_box.currentIndexChanged.connect(self.update_view)
            accepted = super(BaseFileFolderDialog, self).exec_()
            self.filter_box.currentIndexChanged.disconnect(self.update_view)
            return self.get_result() if accepted == 1 else None
    # endregion

    # region Public Functions
    def set_filters(self, filters, selected = 0):
        self.filter_box.clear()
        filter_types = filters.split(';;')
        for ft in filter_types:
            extensions = string.extract(ft, '(', ')')
            filter_name = string.rstrips(ft, '({})'.format(extensions))
            extensions = extensions.split(' ')
            self.filter_box.addItem('{} ({})'.format(filter_name, ','.join(extensions)), extensions)
        if 0 <= selected < self.filter_box.count():
            self.filter_box.setCurrentIndex(selected)
        self.filters = filters

    def get_drives_widget(self):
        """
        Returns a QGroupBox widget that contains all disk drivers of the PC in a vertical layout
        :return: QGroupBox
        """

        w = QGroupBox('')
        w.setParent(self)
        box = QVBoxLayout()
        box.setAlignment(Qt.AlignTop)
        places = [(getpass.getuser(), os.path.realpath(os.path.expanduser('~')))]
        places += [(q, q) for q in [os.path.realpath(x.absolutePath()) for x in QDir().drives()]]
        for label, loc in places:
            icon = QFileIconProvider().icon(QFileInfo(loc))
            drive_btn = QRadioButton(label)
            drive_btn.setIcon(icon)
            drive_btn.setToolTip(loc)
            drive_btn.setProperty('path', loc)
            drive_btn.clicked.connect(self.go_to_drive)
            self.places[loc] = drive_btn
            box.addWidget(drive_btn)
        w.setLayout(box)
        return w

    def go_to_drive(self):
        """
        Updates widget to show the content of the selected disk drive
        """

        sender = self.sender()
        self.set_directory(sender.property('path'), False)

    def get_result(self):
        tf = self.file_edit.text()
        sf = self.get_file_path(tf)
        return sf, os.path.dirname(sf), tf.split(os.pathsep)

    def get_filter_patterns(self):
        """
        Get list of filter patterns that are being used by the widget
        :return: list<str>
        """

        idx = self.filter_box.currentIndex()
        if idx >= 0:
            return self.filter_box.itemData(idx)
        else:
            return []

    def get_file_path(self, file_name):
        """
        Returns file path of the given file name taking account the selected directory
        :param file_name: str, name of the file without path
        :return: str
        """

        sname = file_name.split(os.pathsep)[0]
        return os.path.realpath(os.path.join(os.path.abspath(self.directory), sname))
#     def accept(self):
#         self._overlay.close()
#         super(BaseFileFolderDialog, self).accept()
#
#
#     def reject(self):
#         self._overlay.close()
#         super(BaseFileFolderDialog, self).reject()

    def update_view(self):
        """
        Updates file/folder view
        :return:
        """

        self.view.clear()
        qdir = QDir(self.directory)
        qdir.setNameFilters(self.get_filter_patterns())
        filters = QDir.Dirs | QDir.AllDirs | QDir.Files | QDir.NoDot | QDir.NoDotDot
        if self.show_hidden.isChecked():
            filters = filters | QDir.Hidden
        entries = qdir.entryInfoList(filters=filters, sort=QDir.DirsFirst | QDir.Name)
        file_path = self.get_file_path('..')
        if os.path.exists(file_path) and file_path != self.directory:
            icon = QFileIconProvider().icon(QFileInfo(self.directory))
            QListWidgetItem(icon, '..', self.view, 0)
        for info in entries:
            icon = QFileIconProvider().icon(info)
            suf = info.completeSuffix()
            name, tp = (info.fileName(), 0) if info.isDir() else (
            '%s%s' % (info.baseName(), '.%s' % suf if suf else ''), 1)
            QListWidgetItem(icon, name, self.view, tp)
        self.view.setFocus()

    def set_directory(self, path, check_drive=True):
        """
        Sets the directory that you want to explore
        :param path: str, valid path
        :param check_drive: bool,
        :return:
        """

        self.directory = os.path.realpath(path)
        self.path_edit.setText(self.directory)
        self.file_edit.setText('')

        # If necessary, update selected disk driver
        if check_drive:
            for loc in self.places:
                rb = self.places[loc]
                rb.setAutoExclusive(False)
                rb.setChecked(loc.lower() == self.directory.lower())
                rb.setAutoExclusive(True)

        self.update_view()
        self.up_button.setEnabled(not self.cant_go_up())

    def go_up(self):
        """
        Updates the current directory to go to its parent directory
        """

        self.set_directory(os.path.dirname(self.directory))

    def cant_go_up(self):
        """
        Checks whether we can naviage to current selected parent directory or not
        :return: bool
        """

        return os.path.dirname(self.directory) == self.directory

    def activate_directory_from_view(self, name):
        """
        Updates selected directory
        :param name: str, name of the directory
        """

        self.set_directory(os.path.join(self.directory, name))

    def activate_file_from_view(self, name):
        """
        Updates selected file text and returns its info by accepting it
        :param name: str, name of the file
        """

        self.select_file_item(name=name)
        self.accept()

    def select_file_item(self, name):
        """
        Updates selected file text and returns its info by accepting it
        :param name: str, name of the file
        """

        self.file_edit.setText(name)

    def select_folder_item(self, name):
        """
        Updates selected folder text and returns its info by accepting it
        :param name: str, name of the folder
        """

        self.file_edit.setText(name)


class OpenFileDialog(BaseFileFolderDialog, object):
    """
    Open file dialog
    """

    def __init__(
            self,
            name='OpenFile',
            multi=False,
            title='Open File',
            size=(200, 125),
            fixed_size=False,
            frame_less=True,
            hide_title=False,
            parent=None,
            use_app_browser=False):

        if parent is None:
            parent = tp.Dcc.get_main_window()

        super(OpenFileDialog, self).__init__(
            name=name, title=title, size=size, fixed_size=fixed_size, frame_less=frame_less, hide_title=hide_title, use_app_browser=use_app_browser, parent=parent
        )

        self._multi = multi
        if multi:
            self.setExtendedSelection()

    def accept(self, *args, **kwargs):
        selected_file, selected_dir, selected_file_name = self.get_result()
        if not os.path.isdir(selected_file):
            if os.path.exists(selected_file):
                super(OpenFileDialog, self).accept()
            else:
                message_box = QMessageBox()
                message_box.setWindowTitle('Confirme file selection')
                message_box.setText('File "{0}" does not exists!'.format(selected_file))
                message_box.exec_()

    def open_app_browser(self):
        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            sel_file = cmds.fileDialog2(
                caption=self.windowTitle(),
                fileMode=1,
                fileFilter=self.filters,
                dialogStyle=2
            )
        else:
            raise NotImplementedError('Open App Browser is not implemented for your current DCC: {}'.format(tp.Dcc.get_name()))

        if sel_file:
            sel_file = sel_file[0]
            return [sel_file, os.path.dirname(sel_file), [os.path.basename(sel_file)]]

        return None

    def select_file_item(self, names):
        if self._multi:
            self.file_edit.setText(os.pathsep.join(names))
        else:
            super(OpenFileDialog, self).select_file_item(names)


class SaveFileDialog(BaseFileFolderDialog, object):
    def __init__(self,
                 name='SaveFile',
                 title='Save File',
                 size=(200, 125),
                 fixed_size=False,
                 frame_less=True,
                 hide_title=False,
                 parent=None,
                 use_app_browser=False):

        if parent is None:
            parent = tp.Dcc.get_main_window()

        super(SaveFileDialog, self).__init__(
            name=name, title=title, size=size, fixed_size=fixed_size, frame_less=frame_less, hide_title=hide_title, use_app_browser=use_app_browser, parent=parent)

        self._open_button.setText('Save')
        size = QSize(42, 24)
        self.new_directory_button = QPushButton('New')
        self.new_directory_button.setToolTip('Create new directory')
        self.new_directory_button.setMinimumSize(size)
        self.new_directory_button.setMaximumWidth(size)
        self.new_directory_button.clicked.connect(self.create_new_directory)
        self.grid.itemAtPosition(0, 1).addWidget(self.new_directory_button, 0, 5)

    def accept(self, *args, **kwargs):
        selected_file, selected_dir, selected_filename = self.get_result()
        if not os.path.isdir(selected_file):
            if os.path.exists(selected_file):
                message_box = QMessageBox()
                message_box.setWindowTitle('Confirm File Selection')
                message_box.setText('File "%s" exists.\nDo you want to overwrite it?' % selected_file)
                message_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
                message_box.setDefaultButton(QMessageBox.No)
                rv = message_box.exec_()
                if rv == QMessageBox.Yes and not os.path.isdir(selected_file):
                    super(SaveFileDialog, self).accept()
        else:
            super(SaveFileDialog, self).accept()

    def open_app_browser(self):

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            sel_file = cmds.fileDialog2(
                caption=self.windowTitle(),
                fileMode=0,
                fileFilter=self.filters,
                dialogStyle=2
            )
        else:
            raise NotImplementedError('Open App Browser is not implemented for your current DCC: {}'.format(tp.Dcc.get_name()))
            
        if sel_file:
            sel_file = sel_file[0]

        return [sel_file, os.path.dirname(sel_file), [os.path.basename(sel_file)]]

    def create_new_directory(self):
        name, ok = QInputDialog.getText(self, 'New directory name', 'Name:', QLineEdit.Normal, 'New Directory')
        if ok and name:
            path = os.path.join(self.directory, name)
            if os.path.exists(path):
                msg_box = QMessageBox(self)
                msg_box.setWindowTitle('Error')
                msg_box.setText('Directory already exists')
                msg_box.exec_()
            else:
                try:
                    os.makedirs(path)
                    self.update_view()
                except os.error as e:
                    msg_box = QMessageBox(self)
                    msg_box.setWindowTitle('Error')
                    msg_box.setText('Cannot create directory')
                    msg_box.exec_()


class SelectFolderDialog(BaseFileFolderDialog, object):
    def __init__(self,
                 name='SelectFolder',
                 title='Select Folder',
                 size=(200, 125),
                 fixed_size=False,
                 frame_less=True,
                 hide_title=False,
                 use_app_browser=False,
                 parent=None,
                 **kwargs):

        if parent is None:
            parent = tp.Dcc.get_main_window()

        super(SelectFolderDialog, self).__init__(
            name=name, title=title, size=size, fixed_size=fixed_size, frame_less=frame_less, hide_title=hide_title, use_app_browser=use_app_browser, parent=parent, **kwargs
        )

    def accept(self, *args, **kwargs):
        selected_file, selected_dir, selected_filename = self.get_result()
        super(SelectFolderDialog, self).accept()

    def open_app_browser(self):

        if tp.Dcc.get_name() == tp.Dccs.Maya:
            import maya.cmds as cmds
            sel_folder = cmds.fileDialog2(
                caption=self.windowTitle(),
                fileMode=3,
                fileFilter=self.filters,
                dialogStyle=2
            )
        else:
            raise NotImplementedError('Open App Browser is not implemented for your current DCC: {}'.format(tp.Dcc.get_name()))

        if sel_folder:
            sel_folder = sel_folder[0]

            result = [sel_folder, os.path.dirname(sel_folder), [os.path.basename(sel_folder)]]
            return result[0]

        return None

    def exec_(self, *args, **kwargs):
        self.set_filters('')
        return super(SelectFolderDialog, self).exec_()


class NativeDialog(object):
    """
    Dialog that opens DCC native dialogs
    """

    @staticmethod
    def open_file(title='Open File', start_directory=None, filters=None):
        """
        Function that shows open file DCC native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        raise NotImplementedError('open_file() function is not implemented')

    @staticmethod
    def save_file(title='Save File', start_directory=None, filters=None):
        """
        Function that shows save file DCC native dialog
        :param title: str
        :param start_directory: str
        :param filters: str
        :return: str
        """

        raise NotImplementedError('save_file() function is not implemented')

    @staticmethod
    def select_folder(title='Select Folder', start_directory=None):
        """
        Function that shows select folder DCC native dialog
        :param title: str
        :param start_directory: str
        :return: str
        """

        raise NotImplementedError('select_folder() function is not implemented')


tpQtLib.register_class('Dialog', Dialog)
tpQtLib.register_class('OpenFileDialog', OpenFileDialog)
tpQtLib.register_class('SaveFileDialog', SaveFileDialog)
tpQtLib.register_class('SelectFolderDialog', SelectFolderDialog)
tpQtLib.register_class('NativeDialog', NativeDialog)
