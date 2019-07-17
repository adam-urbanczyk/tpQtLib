#! /usr/bin/env python
# -*- coding: utf-8 -*-

"""
Initialization module for tpQtLib
"""

from __future__ import print_function, division, absolute_import

import os
import inspect

from tpPyUtils import importer
from tpQtLib.core import resource as resource_utils
from tpQtLib.core import dialog, window
from tpQtLib.resources import res

main = __import__('__main__')

# =================================================================================

logger = None
resource = None
MainWindow = window.MainWindow
DockWindow = window.DockWindow
SubWindow = window.SubWindow
Dialog = dialog.Dialog

# =================================================================================


class tpQtLibResource(resource_utils.Resource, object):
    RESOURCES_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'resources')


class tpQtLib(importer.Importer, object):
    def __init__(self):
        super(tpQtLib, self).__init__(module_name='tpQtLib')

    def get_module_path(self):
        """
        Returns path where tpQtLib module is stored
        :return: str
        """

        try:
            mod_dir = os.path.dirname(inspect.getframeinfo(inspect.currentframe()).filename)
        except Exception:
            try:
                mod_dir = os.path.dirname(__file__)
            except Exception:
                try:
                    import tpQtLib
                    mod_dir = tpQtLib.__path__[0]
                except Exception:
                    return None

        return mod_dir


def init(do_reload=False):
    """
    Initializes module
    :param do_reload: bool, Whether to reload modules or not
    """

    tpqtlib_importer = importer.init_importer(importer_class=tpQtLib, do_reload=do_reload)

    global logger
    global resource
    logger = tpqtlib_importer.logger
    resource = tpQtLibResource

    tpqtlib_importer.import_modules()
    tpqtlib_importer.import_packages(only_packages=True)

    init_dcc(do_reload=do_reload)


def init_dcc(do_reload=False):
    """
    Checks DCC we are working on an initializes proper variables
    """

    if 'cmds' in main.__dict__:
        import tpMayaLib
        tpMayaLib.init(do_reload=do_reload)
    elif 'MaxPlus' in main.__dict__:
        import tpMaxLib
        tpMaxLib.init(do_reload=do_reload)
    elif 'hou' in main.__dict__:
        raise NotImplementedError('Houdini is not a supported DCC yet!')
    elif 'nuke' in main.__dict__:
        raise NotImplementedError('Nuke is not a supported DCC yet!')
    else:
        logger.warning('No DCC found, using abstracto one!')
