#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains library list view implementation
"""

from __future__ import print_function, division, absolute_import

import traceback

from Qt.QtCore import *
from Qt.QtWidgets import *
from Qt.QtGui import *

import tpQtLib
from tpQtLib.widgets.library import consts, mixin


class LibraryListView(mixin.LibraryViewWidgetMixin, QListView):
    """
    Class that implemented library list view widget
    This class is used by LibraryViewer class
    """

    DEFAULT_DRAG_THRESHOLD = consts.LIST_DEFAULT_DRAG_THRESHOLD

    itemMoved = Signal(object)
    itemDropped = Signal(object)
    itemClicked = Signal(object)
    itemDoubleClicked = Signal(object)

    def __init__(self, *args):
        QListView.__init__(self, *args)
        mixin.LibraryViewWidgetMixin.__init__(self)

        self.setSpacing(5)
        self.setMouseTracking(True)
        self.setSelectionRectVisible(True)
        self.setViewMode(QListView.IconMode)
        self.setResizeMode(QListView.Adjust)
        self.setSelectionMode(QListView.ExtendedSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDrop)

        self._tree_widget = None
        self._rubber_band = None
        self._rubber_band_start_pos = None
        self._rubber_band_color = QColor(Qt.white)
        self._custom_sort_order = list()

        self._drag = None
        self._drag_start_pos = None
        self._drag_start_index = None
        self._drop_enabled = True

        self.clicked.connect(self._on_index_clicked)
        self.doubleClicked.connect(self._on_index_double_clicked)

    """
    ##########################################################################################
    OVERRIDES
    ##########################################################################################
    """

    def mousePressEvent(self, event):
        """
        Overrides base QListView mousePressEvent function
        :param event: QMouseEvent
        """

        item = self.item_at(event.pos())
        if not item:
            self.clearSelection()

        mixin.LibraryViewWidgetMixin.mousePressEvent(self, event)
        if event.isAccepted():
            QListView.mousePressEvent(self, event)
            self.viewer().tree_widget().setItemSelected(item, True)

        self.endDrag()
        self._drag_start_pos = event.pos()

        is_left_button = self.mouse_press_button() == Qt.LeftButton
        is_item_draggable = item and item.drag_enabled()
        is_selection_empty = not self.selected_items()

        if is_left_button and (is_selection_empty or not is_item_draggable):
            self.rubber_band_start_event(event)

    def mouseMoveEvent(self, event):
        """
        Overrides base QListView mouseMoveEvent function
        :param event: QMouseEvent
        """

        if not self.is_dragging_items():
            is_left_button = self.mouse_press_button() == Qt.LeftButton
            if is_left_button and self.rubber_band().isHidden() and self.selected_items():
                self.startDrag(event)
            else:
                mixin.LibraryViewWidgetMixin.mouseMoveEvent(self, event)
                QListView.mouseMoveEvent(self, event)
            if is_left_button:
                self.rubber_band_move_event(event)

    def mouseReleaseEvent(self, event):
        """
        Override base QListView mouseReleaseEvent function
        :param event: QMouseEvent
        """

        item = self.item_at(event.pos())
        items = self.selected_items()
        mixin.LibraryViewWidgetMixin.mouseReleaseEvent(self, event)
        if item not in items:
            if event.button() != Qt.MidButton:
                QListView.mouseReleaseEvent(self, event)
        elif not items:
            QListView.mouseReleaseEvent(self, event)

        self.endDrag()
        self.rubber_band().hide()

    def startDrag(self, event):
        """
        Overrides bae QListView startDrag function
        :param event: QEvent
        """

        if not self.dragEnabled():
            return

        if self._drag_start_pos and hasattr(event, 'pos'):
            item = self.item_at(event.pos())
            if item and item.drag_enabled():
                self._drag_start_index = self.indexAt(event.pos())
                point = self._drag_start_pos - event.pos()
                dt = self.drag_threshold()
                if point.x() > dt or point.y() > dt or point.x() < -dt or point.y() < -dt:
                    items = self.selected_items()
                    mime_data = self.mime_data(items)
                    pixmap = self._drag_pixmap(item, items)
                    hotspot = QPoint(pixmap.width() * 0.5, pixmap.height() * 0.5)
                    self._drag = QDrag(self)
                    self._drag.setPixmap(pixmap)
                    self._drag.setHotSpot(hotspot)
                    self._drag.setMimeData(mime_data)
                    self._drag.start(Qt.MoveAction)

    def endDrag(self):
        """
        Function that ends current drag
        """

        self._drag_start_pos = None
        self._drag_start_index = None
        if self._drag:
            del self._drag
            self._drag = None

    def dragEnterEvent(self, event):
        """
        Overrides bae QListView dragEnterEvent function
        :param event: QDragEvent
        """

        mimedata = event.mimeData()
        if (mimedata.hasText() or mimedata.hasUrls()) and self.drop_enabled():
            event.accept()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """
        Overrides bae QListView dragMoveEvent function
        :param event: QDragEvent
        """

        mimedata = event.mimeData()
        if (mimedata.hasText() or mimedata.hasUrls()) and self.drop_enabled():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        """
        Overrides bae QListView dropEvent function
        :param event: QDropEvent
        """

        item = self.item_at(event.pos())
        selected_items = self.selected_item()
        if selected_items and item:
            if self.tree_widget().is_sort_by_custom_order():
                self.move_items(selected_items, item)
            else:
                tpQtLib.logger.info('You can only re-order items when sorting by custom order')

        if item:
            item.drop_event(event)

        self.itemDropped.emit(event)

    """
    ##########################################################################################
    BASE
    ##########################################################################################
    """

    def scroll_to_item(self, item, pos=None):
        """
        Ensures that the item is visible
        :param item: LibraryItem
        :param pos: QPoint or None
        """

        index = self.index_from_item(item)
        pos = pos or QAbstractItemView.PositionAtCenter

        self.scrollTo(index, pos)

    """
    ##########################################################################################
    EVENTS
    ##########################################################################################
    """

    def validate_drag_event(self, event):
        """
        Validates the drag event
        :param event: QMouseEvent
        """

        return Qt.LeftButton == event.mouseButtons()

    def rubber_band_start_event(self, event):
        """
        Function called when the user presses an empty area
        :param event: QMouseEvent
        """

        self._rubber_band_start_pos = event.pos()
        rect = QRect(self._rubber_band_start_pos, QSize())
        rubber_band = self.rubber_band()
        rubber_band.setGeometry(rect)
        rubber_band.show()

    def rubber_band_move_event(self, event):
        """
        Function called when the user moves the mouse over the current viewport
        :param event: QMouseEvent
        """

        if self.rubber_band() and self._rubber_band_start_pos:
            rect = QRect(self._rubber_band_start_pos, event.pos())
            rect = rect.normalized()
            self.rubber_band().setGeometry(rect)

    """
    ##########################################################################################
    DRAG & DROP
    ##########################################################################################
    """

    def drop_enabled(self):
        """
        Returns whether drop functionality is enabled or not
        :return: bool
        """

        return self._drop_enabled

    def set_drop_enabled(self, flag):
        """
        Sets whether drop functionality is enabled or not
        :param flag: bool
        """

        self._drop_enabled = flag

    def drag_threshold(self):
        """
        Returns current drag threshold
        :return: float
        """

        return self.DEFAULT_DRAG_THRESHOLD

    def is_dragging_items(self):
        """
        Returns whether the user is currently dragging items or not
        :return: bool
        """

        return bool(self._drag)

    def mime_data(self, items):
        """
        Returns drag mime data
        :param items: list(LibraryItem)
        :return: QMimeData
        """

        mimedata = QMimeData()
        urls = [item.url() for item in items]
        text = '\n'.join([item.mime_text() for item in items])
        mimedata.setUrls(urls)
        mimedata.setText(text)

        return mimedata

    def _drag_pixmap(self, item, items):
        """
        Internal function that shows the pixmap for the given item during drag operation
        :param item: LibraryItem
        :param items: list(LibraryItem)
        :return: QPixmap
        """

        rect = self.visualRect(self.index_from_item(item))
        pixmap = QPixmap()
        pixmap = pixmap.grabWidget(self, rect)
        if len(items) > 1:
            custom_width = 35
            custom_padding = 5
            custom_text = str(len(items))
            custom_x = pixmap.rect().center().x() - float(custom_width * 0.5)
            custom_y = pixmap.rect().top() + custom_padding
            custom_rect = QRect(custom_x, custom_y, custom_width, custom_width)
            painter = QPainter(pixmap)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setPen(Qt.NoPen)
            painter.setBrush(self.viewer().background_selected_color())
            painter.drawEllipse(custom_rect.center(), float(custom_width * 0.5), float(custom_width * 0.5))
            font = QFont('Serif', 12, QFont.Light)
            painter.setFont(font)
            painter.setPen(self.viewer().text_selected_color())
            painter.drawText(custom_rect, Qt.AlignCenter, str(custom_text))

        return pixmap

    """
    ##########################################################################################
    TREE WIDGET
    ##########################################################################################
    """

    def tree_widget(self):
        """
        Return the tree widget that contains the items
        :return: LibraryTreeWidget
        """

        return self._tree_widget

    def set_tree_widget(self, tree_widget):
        """
        Set the tree widget that contains the items
        :param tree_widget: LibraryTreeWidget
        """

        self._tree_widget = tree_widget
        self.setModel(tree_widget.model())
        self.setSelectionModel(tree_widget.selectionModel())

    def items(self):
        """
        Return all the items
        :return: list(LibraryItem)
        """

        return self.tree_widget().items()

    def item_at(self, pos):
        """
        Returns a pointer to the item at the coordinates p
        The coordinates are relative to the tree widget's viewport
        :param pos: QPoint
        :return: LibraryItem
        """

        index = self.indexAt(pos)
        return self.item_from_index(index)

    def selected_item(self):
        """
        Returns the last selected non-hidden item
        :return: QTreeWidgetItem
        """

        return self.tree_widget().selected_item()

    def selected_items(self):
        """
        Returns a list of all selected non-hidden items
        :return: list(QTreeWidgetItem)
        """

        return self.tree_widget().selectedItems()

    def insert_item(self, row, item):
        """
        Inserts the item at row in the top level in the view
        :param row: int
        :param item: QTreeWidgetItem
        """

        self.tree_widget().insertTopLevelItem(row, item)

    def take_items(self, items):
        """
        Removes and returns the items from the view
        :param items: list(QTreeWidgetItem)
        :return: list(QTreeWidgetItem)
        """

        for item in items:
            row = self.tree_widget().indexOfTopLevelItem(item)
            self.tree_widget().takeTopLevelItem(row)

        return items

    def set_indexes_selected(self, indexes, value):
        """
        Set the selected state for the given indexes
        :param indexes: list(QModelIndex)
        :param value: bool
        """

        items = self.items_from_indexes(indexes)
        self.set_items_selected(items, value)

    def set_items_selected(self, items, value):
        """
        Sets the selected state for the given items
        :param items: list(LibraryItem)
        :param value: bool
        """

        self.tree_widget().blockSignals(True)
        try:
            for item in items:
                self.tree_widget().setItemSelected(item, value)
        except Exception as e:
            tpQtLib.logger.error('{} | {}'.format(e, traceback.format_exc()))
        finally:
            self.tree_widget().blockSignals(False)

    def move_items(self, items, item_at):
        """
        Moves the given items to the position at the given row
        :param items: list(LibraryItem)
        :param item_at: LibraryItem
        """

        scroll_value = self.verticalScrollBar().value()
        self.tree_widget().move_items(items, item_at)
        self.itemMoved.emit(items[-1])
        self.verticalScrollBar().setValue(scroll_value)

    def index_from_item(self, item):
        """
        Returns QModelIndex associated with the given item
        :param item: LibraryItem
        :return: QModelIndex
        """

        return self.tree_widget().indexFromItem(item)

    def item_from_index(self, index):
        """
        Return a pointer to the LibraryItem associated with the given model index
        :param index: QModelIndex
        :return: LibraryItem
        """

        return self.tree_widget().itemFromIndex(index)

    """
    ##########################################################################################
    RUBBER BAND
    ##########################################################################################
    """

    def create_rubber_band(self):
        """
        Creates a new instance of the selection rubber band
        :return: QRubberBand
        """

        rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        palette = QPalette()
        color = self.rubber_band_color()
        palette.setBrush(QPalette.Highlight, QBrush(color))
        rubber_band.setPalette(palette)

        return rubber_band

    def rubber_band(self):
        """
        Retursn the selection rubber band for this widget
        :return: QRubberBand
        """

        if not self._rubber_band:
            self.setSelectionRectVisible(False)
            self._rubber_band = self.create_rubber_band()

        return self._rubber_band

    def rubber_band_color(self):
        """
        Returns the rubber band color for this widget
        :return: QColor
        """

        return self._rubber_band_color

    def set_rubber_band_color(self, color):
        """
        Sets the color for the rubber band
        :param color: QColor
        """

        self._rubber_band = None
        self._rubber_band_color = color

    """
    ##########################################################################################
    CALLBACKS
    ##########################################################################################
    """

    def _on_index_clicked(self, index):
        """
        Callback function that is called when the user clicks on an item
        :param index: QModelIndex
        """

        item = self.item_from_index(index)
        item.clicked()
        self.set_items_selected([item], True)
        self.itemClicked.emit(item)

    def _on_index_double_clicked(self, index):
        """
        Callback function that is called when the user double clicks on an item
        :param index: QModelIndex
        """

        item = self.item_from_index(index)
        self.set_items_selected([item], True)
        item.double_clicked()
        self.itemDoubleClicked.emit(item)
