#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Module that contains utils functions used by libraries
"""

from __future__ import print_function, division, absolute_import

import os
import json
import shutil
from collections import OrderedDict, Mapping

import tpPyUtils
from tpPyUtils.externals import six
from tpPyUtils import path as path_utils

from tpQtLib.widgets.library import exceptions


def absolute_path(data, start):
    """
    Returns an absolute version of all the paths in data using the start path
    :param data: str
    :param start: str
    :return: str
    """

    rel_path1 = path_utils.normalize_path(os.path.dirname(start))
    rel_path2 = path_utils.normalize_path(os.path.dirname(rel_path1))
    rel_path3 = path_utils.normalize_path(os.path.dirname(rel_path2))

    if not rel_path1.endswith("/"):
        rel_path1 += "/"

    if not rel_path2.endswith("/"):
        rel_path2 += "/"

    if not rel_path3.endswith("/"):
        rel_path3 += "/"

    data = data.replace('../../../', rel_path3)
    data = data.replace('../../', rel_path2)
    data = data.replace('../', rel_path1)

    return data


def update(data, other):
    """
    Update teh value of a nested dictionary of varying depth
    :param data: dict
    :param other: dict
    :return: dict
    """

    for key, value in other.items():
        if isinstance(value, Mapping):
            data[key] = update(data.get(key, {}), value)
        else:
            data[key] = value

    return data


def read(path):
    """
    Returns the contents of the given file
    :param path: str
    :return: str
    """

    data = ''
    path = path_utils.normalize_path(path)
    if os.path.isfile(path):
        with open(path) as f:
            data = f.read() or data
    data = absolute_path(data, path)

    return data


def write(path, data):
    """
    Writes the given data to the given file on disk
    :param path: str
    :param data: str
    """

    path = path_utils.normalize_path(path)
    data = path_utils.get_relative_path(data, path)

    tmp = path + '.tmp'
    bak = path + '.bak'

    dirname = os.path.dirname(path)
    if not os.path.exists(dirname):
        os.makedirs(dirname)

    if os.path.exists(tmp):
        msg = 'The path is locked for writing and cannot be accessed {}'.format(tmp)
        raise IOError(msg)

    try:
        with open(tmp, 'w') as f:
            f.write(data)
            f.flush()

        if os.path.exists(bak):
            os.remove(bak)
        if os.path.exists(path):
            os.rename(path, bak)
        if os.path.exists(tmp):
            os.rename(tmp, path)
        if os.path.exists(path) and os.path.exists(bak):
            os.remove(bak)
    except Exception:
        if os.path.exists(tmp):
            os.remove(tmp)
        if not os.path.exists(path) and os.path.exists(bak):
            os.rename(bak, path)

        raise


def update_json(path, data):
    """
    Update a JSON file with the given data
    :param path: str
    :param data: dict
    """

    data_ = read_json(path)
    data_ = update(data_, data)
    save_json(path, data_)


def read_json(path):
    """
    Reads the given JSON file and deserialize it to a Python object
    :param path: str
    :return: dict
    """

    path = path_utils.normalize_path(path)
    data = read(path) or '{}'
    data = json.loads(data)

    return data


def save_json(path, data):
    """
    Serialize given tdata to a JSON string and write it to the given path
    :param path: str
    :param data: dict
    """

    path = path_utils.normalize_path(path)
    data = OrderedDict(sorted(data.items(), key=lambda t: t[0]))
    data = json.dumps(data, indent=4)
    write(path, data)


def replace_json(path, old, new, count=-1):
    """
    Repalces the old value with the new value in the given JSON file
    :param path: str
    :param old: str
    :param new: str
    :param count: int
    :return: dict
    """

    old = old.encode("unicode_escape")
    new = new.encode("unicode_escape")

    data = read(path) or "{}"
    data = data.replace(old, new, count)
    data = json.loads(data)

    save_json(path, data)

    return data


def generate_unique_path(path, max_attempts=1000):
    """
    Generates a unique path on disk
    :param path: str
    :param max_attempts: int
    :return: str
    """

    attempt = 1
    dirname, name, extension = path_utils.split_path(path)
    path_ = '{dirname}/{name} ({number}){extension}'

    while os.path.exists(path):
        attempt += 1
        path = path_.format(name=name, number=attempt, dirname=dirname, extension=extension)
        if attempt >= max_attempts:
            raise ValueError('Cannot generate unique name for path {}'.format(path))

    return path


def rename_path_in_file(path, source, target):
    """
    Renames the given source path to the given target path
    :param path: str
    :param source: str
    :param target: str
    """

    source = path_utils.normalize_path(source)
    target = path_utils.normalize_path(target)

    source1 = '"' + source + '"'
    target1 = '"' + target + '"'

    replace_json(path, source1, target1)

    source2 = '"' + source
    target2 = '"' + target

    if not source2.endswith("/"):
        source2 += "/"

    if not target2.endswith("/"):
        target2 += "/"

    replace_json(path, source2, target2)


def rename_path(source, target, extension=None, force=False):
    """
    Renames the given source path to the given destination path
    :param source: str
    :param target: str
    :param extension: str
    :param force: bool
    :return: str
    """

    dirname = os.path.dirname(source)

    if '/' not in target:
        target = os.path.join(dir(dirname, target))

    if extension and extension not in target:
        target += extension

    source = path_utils.normalize_path(source)
    target = path_utils.normalize_path(target)
    tpPyUtils.logger.debug('Renaming: {} > {}'.format(source, target))

    if source == target and not force:
        raise exceptions.RenamePathError('The source path and destination path are the same: {}'.format(source))
    if os.path.exists(target) and not force:
        raise exceptions.RenamePathError('Cannot save over an existing path: "{}"'.format(target))
    if not os.path.exists(dirname):
        raise exceptions.RenamePathError('The system cannot find the specified path: "{}"'.format(dirname))
    if not os.path.exists(os.path.dirname(target)) and force:
        os.mkdir(os.path.dirname(target))
    if not os.path.exists(source):
        raise exceptions.RenamePathError('The system cannot find the specified path: "{}"'.format(source))

    os.rename(source, target)
    tpPyUtils.logger.debug('Renamed: {} > {}'.format(source, target))

    return target


def copy_path(source, target):
    """
    Makes a copy of the given source path to the given destination path
    :param source: str
    :param target: str
    :return: str
    """

    dirname = os.path.dirname(source)
    if '/' not in target:
        target = os.path.join(dirname, target)

    source = path_utils.normalize_path(source)
    target = path_utils.normalize_path(target)

    if source == target:
        raise IOError('The source path and destination path are the same: {}'.format(source))
    if os.path.exists(target):
        raise IOError('Cannot copy over an existing path: {}'.format(target))
    if os.path.isfile(source):
        shutil.copy(source, target)
    else:
        shutil.copytree(source, target)

    return target


def move_path(source, target):
    """
    Moves the given source path to the given destination path
    :param source: str
    :param target: str
    :return: str
    """

    source = six.u(source)
    dirname, name, extension = path_utils.split_path(source)
    if not os.path.exists(source):
        raise exceptions.MovePathError('No such file or directory: {}'.format(source))
    if os.path.isdir(source):
        target = '{}/{}{}'.format(target, name, extension)
        target = generate_unique_path(target)
    shutil.move(source, target)

    return target


def move_paths(source_paths, target):
    """
    Moves the given paths to the given destination paths
    :param source_paths: list(str)
    :param target: str
    :return: list(str)
    """

    if not os.path.exists(target):
        os.makedirs(target)

    for source in source_paths or list():
        if not source:
            continue
        basename = os.path.basename(source)
        target_ = path_utils.normalize_path(os.path.join(target, basename))
        tpPyUtils.logger.debug('Moving Content: {} > {}'.format(source, target_))
        shutil.move(source, target_)


def remove_path(path):
    """
    Removes the given path from disk
    :param path: str
    """

    if os.path.isfile(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)