#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains different classes to handle Qt settings
"""

from __future__ import print_function, division, absolute_import

import os
import sys

from Qt.QtCore import *
from Qt.QtWidgets import *

from tpPyUtils import settings


class QtSettings(QSettings, object):
    def __init__(self, filename, window, max_files=10,):
        super(QtSettings, self).__init__(filename, QSettings.IniFormat, window)

        self._max_files = max_files
        self._window = window
        self._groups = [window.objectName(), 'RecentFiles']
        self._initialize()

    # region Properties
    def has_setting(self, setting_name):
        return self.get(setting_name)

    def get(self, setting_name, default_value=None):
        """
        Returns the setting stored with the given name
        :param setting_name: str
        :param default_value: variant
        :return:
        """

        val = self.value(setting_name)
        if not val:
            return default_value

        return val

    def getw(self, setting_name, default_value=None):
        """
        Returns the setting stored with the given name
        :param setting_name: str
        :param default_value: variant
        :return:
        """

        val = self.value(self._window.objectName().upper() + '/' + setting_name)
        if not val:
            return default_value

        return val


    def set(self, setting_name, setting_value):
        """
        Stores a new settings with the given name and the given value
        If the given setting already exists, it will be overwrite
        :param setting_name: str, setting name we want store
        :param setting_value: variant, setting value we want to store
        """

        self.setValue(setting_name, setting_value)

    def setw(self, setting_name, setting_value):
        """
        Stores a new window setting with the given name and the given value
        :param setting_name: str, setting name we want to store
        :param setting_value: variant, setting value we want to store
        """

        self.setValue(self._window.objectName().upper() + '/' + setting_name, setting_value)

    def get_groups(self):
        """
        Returns the current preferences groups
        :return: list
        """

        return self._groups

    groups = property(get_groups)
    # endregion

    # region Public Functions
    def add_group(self, group):
        """
        Add a group to the current preferences groups
        :param group: str, name of group to add
        :return: bool, True if the group was successfully added
        """

        if group not in self._groups:
            self._groups.append(group)
            return True

        return False

    def remove_group(self, group):
        """
        Remove a group from the preferences group
        :param group: str, name of group to remove
        :return: bool, True if the group was successfully removed
        """

        if group in self._groups:
            self._groups.remove(group)
            return True

        return False

    def window_keys(self):
        """
        Returns a list of all window keys to save for layouts or rebuilding last layout on launch
        :return: list
        """

        if self._window is None:
            return []

        result = [self._window.objectName()]
        for dock in self._window.findChildren(QDockWidget):
            dock_name = dock.objectName()
            result.append(str(dock_name))

        return result

    def prefs_keys(self):
        """
        Returns a list of preferences keys
        :return: list<str>, list of user prefs keys
        """

        results = list()
        self.beginGroup('Preferences')
        results = self.childKeys()
        self.endGroup()
        return results

    def get_layouts(self):
        """
        Returns a list of window layout names
        :return: list
        """

        layout_names = list()
        layout_keys = ['%s/geometry' % x for x in self.window_keys()]

        for k in self.allKeys():
            if 'geometry' in k:
                attrs = k.split('/geometry/')
                if len(attrs) > 1:
                    layout_names.append(str(attrs[-1]))

        return sorted(list(set(layout_names)))

    def save_layout(self, layout):
        """
        Save a named layout
        :param layout: str, layout name to save
        """

        sys.utils.logger.info('Saving Layout: "{}"'.format(layout))
        self.setValue(self._window.objectName()+'/geometry/%s' % layout, self._window.saveGeoemtry())
        self.setValue(self._window.objectName()+'/windowState/%s' % layout, self._window.saveState())

        for dock in self._window.findChildren(QDockWidget):
            dock_name = dock.objectName()
            self.setValue('%s/geometry/%s' % (dock_name, layout), dock.saveGeometry())

    def restore_layout(self, layout):
        """
        Restore a named layout
        :param layout: str, layout name to restores
        """

        sys.utils.logger.info('Restoring layout: "{}"'.format(layout))
        window_keys = self.window_keys()

        for widget_name in window_keys:
            key_name = '%s/geometry/%s' % (widget_name, layout)
            if widget_name != self._window.objectName():
                dock = self._window.findChildren(QDockWidget, widget_name)
                if dock:
                    if key_name in self.allKeys():
                        value = self.value(key_name)
                        dock[0].restoreGeometry(value)
            else:
                if key_name in self.allKeys():
                    value = self.value(key_name)
                    self._window.restoreGeometry(value)

                window_state = '%s/windowState/%s' % (widget_name, layout)
                if window_state in self.allKeys():
                    self._window.restoreState(self.value(window_state))

    def delete_layout(self, layout):
        """
        Delete a named layout
        :param layout: str, layout name to restore
        """

        sys.utils.logger.info('Deleting layout: "{}"'.format(layout))
        window_keys = self.window_keys()

        for widget_name in window_keys:
            key_name = '%s/geometry/%s' % (widget_name, layout)
            if key_name in self.allKeys():
                self.remove(key_name)

            if widget_name == self._window.objectName():
                window_state = '%s/windowState/%s' % (widget_name, layout)
                if window_state in self.allKeys():
                    self.remoev(window_state)

    def get_default_value(self, key, *groups):
        """
        Returns the default values for a group
        :param key: str, key to search for
        :return: variant, default value of key (None if not found)
        """

        if self.group():
            try:
                self.endGroup()
            except:
                pass

        result = None

        if not groups:
            return None

        group_name = groups[0]
        for group in groups[1:]:
            group_name += '/%s' % group

        group_name += '/%s' % key
        group_name += '/%s' % 'default'

        if group_name in self.allKeys():
            result = self.value(group_name)

        return result

    def delete_file(self):
        """
        Delete the preferences file on disk
        """

        sys.utils.logger.info('Deleting Settings: "{}"'.format(self.fileName()))
        return os.remove(self.fileName())

    def get_recent_files(self):
        """
        Get a tuple of the most recent files
        """

        recent_files = list()
        cnt = self.beginReadArray('RecentFiles')
        for i in range(cnt):
            self.setArrayIndex(i)
            fn = self.value('file')
            recent_files.append(fn)
        self.endArray()

        return tuple(recent_files)

    def add_recent_file(self, filename):
        """
        Adds a recent file to the stack
        :param filename: str, file name to add
        """

        recent_files = self.get_recent_files()
        if filename in recent_files:
            recent_files = tuple(x for x in recent_files if x != filename)

        recent_files = recent_files + (filename,)
        self.beginWriteArray('RecentFiles')
        for i in range(len(recent_files)):
            self.setArrayIndex(i)
            self.setValue('file', recent_files[i])
        self.endArray()

    def clear_recent_files(self):
        self.remove('RecentFiles')
    # endregion

    # region Private Functions
    def _initialize(self):
        window_name = self._window.objectName().upper()
        if window_name not in self.childGroups():
            if self._window is not None:
                self.setValue(window_name+'/geometry/default', self._window.saveGeometry())

                if isinstance(self._window, QMainWindow):
                    self.setValue(window_name+'/windowState/default', self._window.saveState())

        if 'RecentFiles' not in self.childGroups():
            self.beginWriteArray('RecentFiles', 0)
            self.endArray()

        while self.group():
            self.endGroup()


class QtIniSettings(settings.INISettings, object):
    def __init__(self, filename):
        super(QtIniSettings, self).__init__(filename)

    def export_widget(self, option, widget):
        """
        Serializes a widget's state to an option, value pair Sets the value with an associated key in the section at the top of the section stack.

        :param str option:   The key to use in storing the value.
        :param str widget:   The QWidget to extractvalue to store.
        """

        if isinstance(widget, QComboBox):
            self.export_option(option, widget.currentIndex())
        elif isinstance(widget, QCheckBox):
            self.export_option(option, widget.isChecked())
        elif isinstance(widget, QToolButton):
            if widget.isCheckable():
                self.export_option(option, widget.isChecked())
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            self.export_option(option, widget.value())
        elif isinstance(widget, QLineEdit):
            self.export_option(option, widget.text())
        elif isinstance(widget, (QSize, QPoint)):
            self.export_option(option, widget.toTuple())
        else:
            assert False, "Unknown control type"

    def import_widget(self, option, widget):
        """
        Serializes a widget's state to an option, value pair Sets the value with an associated key in the section at the top of the section stack.

        :param str option:   The key to use in storing the value.
        :param str widget:   The QWidget to extractvalue to store.
        """

        if isinstance(widget, QComboBox):
            d = 0 if (widget.currentIndex() < 0) else widget.currentIndex()
            v = self.import_option(option, d)
            widget.setCurrentIndex(v)
        elif isinstance(widget, QCheckBox):
            d = widget.isChecked()
            v = self.import_option(option, d)
            widget.setChecked(v)
        elif isinstance(widget, QToolButton):
            if widget.isCheckable():
                d = widget.isChecked()
                v = self.import_option(option, d)
                widget.setChecked(v)
        elif isinstance(widget, (QSpinBox, QDoubleSpinBox)):
            d = widget.value()
            v = self.import_option(option, d)
            widget.setValue(v)
        elif isinstance(widget, QLineEdit):
            d = widget.text()
            v = self.import_option(option, d)
            widget.setText(v)
        elif isinstance(widget, QSize):
            d = widget.toTuple()
            v = self.import_option(option, d, True)
            widget.setWidth(v[0])
            widget.setHeight(v[1])
        elif isinstance(widget, QPoint):
            d = widget.toTuple()
            v = self.import_option(option, d, True)
            widget.setX(v[0])
            widget.setY(v[1])
        else:
            assert False, "Unknown control type"
