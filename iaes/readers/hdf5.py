"""
@author:
Eraldo Pomponi

@copyright:
2012 - Eraldo Pomponi
eraldo.pomponi@gmail.com

@license:
All rights reserved

Created on Jun 12, 2012
"""
from tables import openFile

import sip
sip.setapi('QString', 2)
sip.setapi('QVariant', 2)

from os import urandom

def __dependencies_for_freezing():
    from PyQt4 import QtGui, QtCore, QtOpenGL, QtNetwork
    import pyface.ui.qt4.resource_manager
    import pyface.ui.qt4.tasks.task_window_backend
    import scipy.io.matlab.streams
    import random


#print urandom.__repr__()

# ETS imports
import os
os.environ['QT_API'] = 'pyqt'
os.environ['ETS_TOOLKIT'] = 'qt4'

from traits.api import \
    HasTraits, Str, List, Dict, Any, Property, cached_property, Instance, \
    adapts, File, Button, on_trait_change

from traitsui.api import \
    TreeEditor, TreeNode, ITreeNode, View, Item, \
    ITreeNodeAdapter, VGroup, HGroup, Controller

from traitsui.tabular_adapter import TabularAdapter
from pyface.api import FileDialog, MessageDialog

from datablock_table import DataBlockTable, DataBlockTablePlot
from parameters_table import ParametersTable, ParametersTablePlot


class Board(HasTraits):
    """ This class represents a 'board' node in the hdf5 tree structure. """

    h5file_board_ptr = Any
    board_id = Str('<unknown>')
    path = Str('<unknown>')
    parent_path = Str('<unknown>')
    chnls = List
    meta = Property(Dict, depends_on='h5file_board_ptr')
    cview = Property(depends_on='h5file_board_ptr')

    @cached_property
    def _get_cview(self):
        for label in self.meta.keys():
            print label, self.meta[label]
            self.add_trait(label, self.meta[label])
        items = [Item(name, style='readonly') \
                 for name in sorted(self.meta.keys())]
        return View(*items)

    @cached_property
    def _get_meta(self):
        labels = self.h5file_board_ptr._v_attrs._f_list("user")
        meta = {}
        for label in labels:
            meta[label] = self.h5file_board_ptr._v_attrs[label]
        return meta


class Channel(HasTraits):
    """ This class represents a 'channel' node in the hdf5 tree structure. """

    h5file_channel_ptr = Any
    channel_id = Str('<unknown>')
    path = Str('<unknown>')
    parent_path = Str('<unknown>')
    meta = Property(Dict, depends_on='h5file_channel_ptr')
    cview = Property(depends_on='h5file_channel_ptr')

    @cached_property
    def _get_cview(self):
        for label in self.meta.keys():
            print label, self.meta[label]
            self.add_trait(label, self.meta[label])
        items = [Item(name, style='readonly') \
                 for name in sorted(self.meta.keys())]
        return View(*items)

    @cached_property
    def _get_meta(self):
        labels = self.h5file_channel_ptr._v_attrs._f_list("user")
        meta = {}
        for label in labels:
            meta[label] = self.h5file_channel_ptr._v_attrs[label]
        return meta


class DataBlockAdapter(TabularAdapter):

    columns = [('Block_ID', 'block_id'), ('Time Stamp', 'time_stamp'), \
               ('Raw Data', 'raw_data')]


class ParametersAdapter(TabularAdapter):

    columns = [('Block_ID', 'block_id'), ('Time Stamp', 'time_stamp'), \
               ('RMS', 'rms'), ('Peak Amp', 'peak'), ('Count', 'count')]


class BoardObjectAdapter(ITreeNodeAdapter):
    adapts(Board, ITreeNode)

    def allows_children(self):
        return True

    def has_children(self):
        return len(self.adaptee.chnls) > 0

    def get_children(self):
        return self.adaptee.chnls

    def get_view(self):
        return self.adaptee.cview

    def get_label(self):
        return self.adaptee.board_id


class ChannelObjectAdapter(ITreeNodeAdapter):
    adapts(Channel, ITreeNode)

    def allows_children(self):
        return True

    def has_children(self):
        return len(self.adaptee.tables) > 0

    def get_children(self):
        return self.adaptee.tables

    def get_view(self):
        return self.adaptee.cview

    def get_label(self):
        return self.adaptee.channel_id


class DataBlockTablePlotObjectAdapter(ITreeNodeAdapter):

    adapts(DataBlockTablePlot, ITreeNode)

    def allows_children(self):
        return False

    def has_children(self):
        return False

    def get_view(self):
        return self.adaptee.cview()

    def get_label(self):
        return "Raw Data"


class ParametersTablePlotObjectAdapter(ITreeNodeAdapter):
    adapts(ParametersTablePlot, ITreeNode)

    def allows_children(self):
        return False

    def has_children(self):
        return False

    def get_view(self):
        return self.adaptee.cview()

    def get_label(self):
        return "Parameters"


# HDF5 Nodes in the tree
class Hdf5TableNode(HasTraits):
    name = Str('<unknown>')
    path = Str('<unknown>')
    parent_path = Str('<unknown>')


class Hdf5FileNode(HasTraits):
    name = Str('<unknown>')
    path = Str('/')
    boards = List(Board)
    channels = List(Channel)
    tables = List(Hdf5TableNode)
    boards_channels_tables = List


def _get_tables(group, h5file):
    """Return a list of all tables immediately below a group
    in an HDF5 file."""
    l = []

    for table in h5file.iterNodes(group, classname='Table'):
        if table._v_name == 'rowdata':
            db = DataBlockTable(name=table._v_name,
                                table_ptr=table)

            a = DataBlockTablePlot(dataset=db)
            l.append(a)
        elif table._v_name == 'parameters':
            param = ParametersTable(name=table._v_name,
                                    table_ptr=table)
            a = ParametersTablePlot(dataset=param)
            l.append(a)
    return l


def _get_channels(board, h5file):
    """Return a list of all groups and arrays immediately below a group
    in an HDF5 file."""
    l = []

    for subgroup in h5file.iterNodes(board, classname='Group'):
        if subgroup._v_name.lower().strip().find('ch') != -1:
            g = Channel(
                    channel_id=subgroup._v_name,
                    path=subgroup._v_pathname,
                    parent_path=subgroup._v_parent._v_pathname,
                    h5file_channel_ptr=subgroup
                    )
            g.tables = _get_tables(subgroup, h5file)

            l.append(g)

    return l


def _get_boards(h5file):
    """Return a list of all groups and arrays immediately below a group
    in an HDF5 file."""
    l = []

    for subgroup in h5file.iterNodes(h5file.root, classname='Group'):
        if subgroup._v_name.lower().strip().find('board') != -1:
            g = Board(
                    board_id=subgroup._v_name,
                    path=subgroup._v_pathname,
                    parent_path=subgroup._v_parent._v_pathname,
                    h5file_board_ptr=subgroup
                    )
            g.chnls = _get_channels(subgroup, h5file)

            l.append(g)

    return l


def _hdf5_tree(h5file):
    """Return a list of all groups and arrays below the root group
    of an HDF5 file."""

    file_tree = Hdf5FileNode(
            name='IAES',
            boards=_get_boards(h5file)
            )

    return file_tree

# View for objects that aren't edited
no_view = View()


#def _hdf5_tree_editor(selected=''):
#    """Return a TreeEditor specifically for HDF5 file trees."""
#    return TreeEditor(
#        nodes=[
#            TreeNode(
#                node_for=[Hdf5FileNode],
#                auto_open=True,
#                children='boards',
#                label='name',
#                view=no_view,
#                ),
#            TreeNode(
#                node_for=[Hdf5TableNode],
#                auto_open=False,
#                children='',
#                label='name',
#                view=no_view,
#                ),
#            ],
#        selected=selected,
#        )


def _hdf5_tree_editor_item(selected=''):
    """Return a TreeEditor specifically for HDF5 file trees."""
    return TreeEditor(
        nodes=[
            TreeNode(
                node_for=[Hdf5FileNode],
                auto_open=True,
                children='boards',
                label='name',
                view=no_view,
                ),
            TreeNode(
                node_for=[Hdf5TableNode],
                auto_open=False,
                children='',
                label='name',
                view=no_view,
                ),
            ],
        selected=selected,
        shared_editor=True
        )


def _hdf5_tree_editor_tree(selected='', item_editor=''):
    """Return a TreeEditor specifically for HDF5 file trees."""
    return TreeEditor(
        nodes=[
            TreeNode(
                node_for=[Hdf5FileNode],
                auto_open=True,
                children='boards',
                label='name',
                view=no_view,
                ),
            TreeNode(
                node_for=[Hdf5TableNode],
                auto_open=False,
                children='',
                label='name',
                view=no_view,
                ),
            ],
        selected=selected,
        shared_editor=True,
        editor=item_editor
        )


class AtreeC(Controller):

    open_file = Button('Open')

    item_editor = _hdf5_tree_editor_item(selected='node')
    tree_editor = _hdf5_tree_editor_tree(selected='node', \
                                         item_editor=item_editor)

#    view = View(VGroup(
#                       HGroup(
#                              Item('handler.open_file'),
#                              Item('filename', style='readonly',springy=True),
#                              #Item('update'),
#                              show_labels=False,
#                              ),
#                       Item('h5_tree',
#                            editor=_hdf5_tree_editor(selected='node'),
#                            resizable=True,
#                            show_label=False
#                            ),
#                       ),
#                title='IAES HDF5 File Browser',
#                #buttons=['Undo', 'OK', 'Cancel'],
#                style='custom',
#                resizable=True,
#                width=.7,
#                height=.8
#                )

    view = View(VGroup(
                       HGroup(
                              Item('handler.open_file'),
                              Item('filename', style='readonly', springy=True),
                              #Item('update'),
                              show_labels=False,
                              ),
                       Item('h5_tree',
                            editor=tree_editor,
                            resizable=True,
                            show_label=False
                            ),
                       Item('h5_tree',
                            editor=item_editor,
                            resizable=True,
                            show_label=False
                            ),
                       ),
                title='IAES HDF5 File Browser',
                #buttons=['Undo', 'OK', 'Cancel'],
                #style='custom',
                resizable=True,
                width=.7,
                height=.8
                )

    @on_trait_change('open_file')
    def _open_file_changed(self):
        dlg = FileDialog()
        if dlg.open():
            if dlg.path != '':
                if self.model.h5file is not None:
                    self.model.h5file.close()
                self.model.filename = dlg.path
            else:
                self.model.h5file = None

    @on_trait_change('node')
    def _node_changed(self, new):
        try:
            print new.path
        except:
            pass

    def close(self, info, is_ok):
        self.model.h5file.close()
        return True


class ATree(HasTraits):

    filename = File
    h5File = Any

    h5_tree = Property(Instance(Hdf5FileNode), depends_on='filename')

    node = Any

    @cached_property
    def _get_h5_tree(self):

        if self.filename is None:
            return None
        try:
            self.h5file = openFile(self.filename, "a")
            return _hdf5_tree(self.h5file)
        except Exception, exc:
            dlg = MessageDialog(title='Could not open file %s' % self.filename,
                message=str(exc))
            dlg.open()
            return None

if __name__ == '__main__':

    fname = '../tests/Data/hd5_test.h5'
    a_tree = ATree()
    a_tree.filename = fname
    try:
        ac = AtreeC(model=a_tree)
        ac.configure_traits()
    except:
        pass

#EOF
