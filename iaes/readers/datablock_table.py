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
import numpy as np

# ETS imports
import os
os.environ['QT_API'] = 'pyqt'
os.environ['ETS_TOOLKIT'] = 'qt4'

from traits.api import HasTraits, Array, Instance, Any, Str, \
    Property, on_trait_change, cached_property
from traitsui.api import View, Item, TabularEditor, VGroup, \
    InstanceEditor
from traitsui.tabular_adapter import TabularAdapter

from enable.api import ComponentEditor

from chaco.api import ArrayPlotData, Plot
from chaco.tools.api import PanTool, ZoomTool, DragZoom

data_block_dtype = np.dtype(([('block_id', '<u8'), \
                             ('time_stamp', '<f8'), \
                             ('raw_data', '<f8', (4096,))]))


class DataBlockAdapter(TabularAdapter):

    columns = [('Block_ID', 'block_id'), ('Time Stamp', 'time_stamp'), \
               ('Raw Data', 'raw_data')]

    def get_text(self, object, trait, row, column):
        return str(getattr(object, trait)[row][column])


class DataBlockTable(HasTraits):
    name = Str('<Unknown>')
    table = Property(Array(dtype=data_block_dtype), depends_on='table_ptr')
    _table = Array(dtype=data_block_dtype)
    table_ptr = Any  # PyTables iterator to access the rown

    selected = Any

    view = View(
                Item('table',
                     show_label=False,
                     style='readonly',
                     editor=TabularEditor(adapter=DataBlockAdapter(),
                                          selected='selected',
                                          editable=False)
                     ),
                title='Parameters Table',
                height=0.50,
                width=0.30,
                resizable=True
            )

    def _get_table(self):
        if self._table is None or len(self._table) == 0:
            if self.table_ptr is not None:
                self._table = np.array(self.table_ptr, self.table_ptr.dtype)
            else:
                self._table = np.array([])
        return self._table

    def _set_table(self, np_arr_struct):
        self._table = np_arr_struct


class DataBlockTablePlot(HasTraits):

    # the ParametersTable holding the actual array
    dataset = Instance(DataBlockTable)

    # a local reference to the data array in the dataset, for convenience
    selected = Property(Any, depends_on='dataset.selected')

    # ArrayPlotData for plot
    plot_data = Instance(ArrayPlotData, ())

    # Chaco Plot instance
    plot = Instance(Plot)

    traits_view = View(
                       VGroup(
                              Item('dataset', show_label=False, style='custom',
                                   editor=InstanceEditor()),
                              Item('plot',
                                   show_label=False,
                                   editor=ComponentEditor(),
                                   width=0.25, height=0.35
                                   ),
                              ),
                       width=0.60, height=0.60,
                       resizable=True,
                       title='Parameters Plot',
                       )

    def cview(self):
        return View(
                    VGroup(
                           Item('dataset', show_label=False, style='custom',
                                editor=InstanceEditor()),
                           Item('plot',
                                show_label=False,
                                editor=ComponentEditor(),
                                width=0.25, height=0.35
                                ),
                           ),
                    width=0.60, height=0.60,
                    resizable=True,
                    title='Raw Data Plot',
                    )

    @cached_property
    def _get_selected(self):
        return self.dataset.selected

    @on_trait_change('selected')
    def _data_source_change(self):
        """Handler for changes of ther selected table row
        """
        if self.selected is None:
            return

        x = np.linspace(0, \
                        len(self.selected['raw_data']), \
                        len(self.selected['raw_data']))

        self.plot_data.set_data('x', x)
        self.plot_data.set_data('y', self.selected['raw_data'])

    def _plot_data_default(self):
        """ This creates a list of ArrayPlotData instances,
        one for each species.
        """
        plot_data = ArrayPlotData()

        plot_data.set_data('x', [])
        plot_data.set_data('y', [])

        return plot_data

    def _plot_default(self):
        """ This creates the default value for the plot.
        """
        # create the main plot object
        plot = Plot(self.plot_data)

        plot.plot(('x', 'y'), type='line', name='raw data', color='lightgreen')

        # add the additional information
        plot.title = 'Row Data'
        plot.x_axis.title = 'Samples'
        plot.y_axis.title = 'Amplitude'

        # tools for basic interactivity
        plot.tools.append(PanTool(plot))
        plot.tools.append(ZoomTool(plot))
        plot.tools.append(DragZoom(plot, drag_button="right"))

        return plot


if __name__ == '__main__':

    db_table = DataBlockTable()

    dbt = np.zeros((100,), \
                   dtype=([('block_id', '<u8'), \
                             ('time_stamp', '<f8'), \
                             ('raw_data', '<f8', (4096,))]))

    for i in xrange(100):
        dbt['block_id'][i] = long(i)
        dbt['time_stamp'][i] = float(i + 20)
        dbt['raw_data'][i] = np.random.normal(size=(4096,))

    db_table.table = dbt

    db_plot = DataBlockTablePlot(dataset=db_table)
    db_plot.configure_traits()
