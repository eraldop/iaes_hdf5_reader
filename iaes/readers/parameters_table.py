"""
@author:
Eraldo Pomponi

@copyright:
2012 - Eraldo Pomponi
eraldo.pomponi@gmail.com

@license:
All rights reserved

Created on Jun 14, 2012
"""
import numpy as np

# ETS imports
import os
os.environ['QT_API'] = 'pyqt'
os.environ['ETS_TOOLKIT'] = 'qt4'

from traits.api import HasTraits, Array, List, Instance, Any, Str, \
    Property, Int, Enum, on_trait_change, cached_property
from traitsui.api import View, Item, TabularEditor, HGroup, VGroup, \
    InstanceEditor
from traitsui.tabular_adapter import TabularAdapter

from enable.api import ComponentEditor

from chaco.api import ArrayPlotData, Plot, ScatterInspectorOverlay, jet
from chaco.tools.api import PanTool, ZoomTool, DragZoom


param_dtype = np.dtype([('block_id', '<u8'), \
                           ('time_stamp', '<f8'), \
                           ('rms', '<f8'), \
                           ('peak', '<f8'), \
                           ('count', '<i2')])


class ParametersAdapter(TabularAdapter):

    columns = [('Block_ID', 'block_id'), ('Time Stamp', 'time_stamp'), \
               ('RMS', 'rms'), ('Peak Amp', 'peak'), ('Count', 'count')]

    def get_text(self, object, trait, row, column):
        return str(getattr(object, trait)[row][column])


class ParametersTable(HasTraits):
    name = Str('<Unknown>')
    table = Property(Array(dtype=param_dtype), depends_on='table_ptr')
    _table = Array(dtype=param_dtype)
    table_ptr = Any  # PyTables iterator to access the rown

    selection = List(Int)

    view = View(
                Item('table_ptr',
                     show_label=True,
                     style='readonly',
                     editor=TabularEditor(adapter=ParametersAdapter(),
                                          multi_select=True,
                                          selected_row='selection',
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


class ParametersTablePlot(HasTraits):

    # the ParametersTable holding the actual array
    dataset = Instance(ParametersTable)

    # a local reference to the data array in the dataset, for convenience
    data = Property(Array(dtype=param_dtype), depends_on='dataset.table')

    selection = List(Int)

    # traits for selecting axes and colours
    x_axis = Enum(['rms', 'peak', 'count'])
    y_axis = Enum('peak', ['rms', 'peak', 'count'])
    color = Enum(['rms', 'peak', 'count'])

    parameters = List(Str, ['rms', 'peak', 'count'])

    # a corresponding list of markers to use for each species
    markers = Enum(['square', 'circle', 'triangle'])

    # ArrayPlotData for plot
    plot_data = Instance(ArrayPlotData, ())

    # Chaco Plot instance
    plot = Instance(Plot)

    traits_view = View(
           HGroup(
               Item('dataset', show_label=False, style='custom',
                   editor=InstanceEditor()),
               VGroup(
                       VGroup(
                           Item('x_axis'),
                           Item('y_axis'),
                           Item('color')
                           ),
                       Item('plot',
                            show_label=False,
                            editor=ComponentEditor(),
                            width=0.25, height=0.35
                            ),
               ),
           ),
           width=0.60, height=0.60,
           resizable=True,
           title='Parameters Plot',
           )

    def cview(self):
        return View(
                    HGroup(
                           Item('dataset', show_label=False, style='custom',
                                editor=InstanceEditor()),
                           VGroup(
                                  VGroup(
                                         Item('x_axis'),
                                         Item('y_axis'),
                                         Item('color')
                                         ),
                                  Item('plot',
                                       show_label=False,
                                       editor=ComponentEditor(),
                                       width=0.25, height=0.35
                                       ),
                                  ),
                           ),
                    width=0.60, height=0.60,
                    resizable=True,
                    title='Parameters Plot',
                    )

    @cached_property
    def _get_data(self):
        return self.dataset.table

    @on_trait_change('x_axis,y_axis,color,data,plot')
    def _data_source_change(self):
        """Handler for changes to the data source selectors
        """
        self.plot_data.set_data('index', self.data[self.x_axis])
        self.plot_data.set_data('value', self.data[self.y_axis])
        self.plot_data.set_data('color', self.data[self.color])

        # set axis titles appropriately
        self.plot.x_axis.title = self.x_axis.title()
        self.plot.y_axis.title = self.y_axis.title()

    @on_trait_change('dataset.selection')
    def user_selection_changed(self, new):
        """ We extract the selection from the dataset, and filter by
        species.
        """
        # ensure the plot exists
        self.plot

        # turn the selection list of indices into a mask
        selection = np.zeros(shape=len(self.data), dtype=bool)
        selection[new] = True

        # now get the indices
        indx = list(np.arange(len(self.data))[selection])
        # set the metadata on the renderer
        self.renderer.index.metadata['selections'] = indx

    def _plot_data_default(self):
        """ This creates a, ArrayPlotData instances.
        """
        plot_data = ArrayPlotData()

        plot_data.set_data('index', [])
        plot_data.set_data('value', [])
        plot_data.set_data('color', [])

        return plot_data

    def _plot_default(self):
        """ This creates the default value for the plot.
        """
        # create the main plot object
        plot = Plot(self.plot_data)

        renderer = plot.plot(('index', 'value', 'color'), \
                             type="cmap_scatter", \
                             color_mapper=jet, \
                             marker='triangle'
                             )[0]

        self.renderer = renderer

        # inspector tool for showing data about points
        #renderer.tools.append(ScatterInspector(renderer))

        # overlay for highlighting selected points
        overlay = ScatterInspectorOverlay(renderer,
            hover_color="red",
            hover_marker_size=6,
            selection_marker_size=6,
            selection_color="yellow",
            selection_outline_color="black",
            selection_line_width=3)
        renderer.overlays.append(overlay)

        # add the additional information
        plot.title = 'Parameters Data'
        plot.x_axis.title = ''
        plot.y_axis.title = ''

        # tools for basic interactivity
        plot.tools.append(PanTool(plot))
        plot.tools.append(ZoomTool(plot))
        plot.tools.append(DragZoom(plot, drag_button="right"))

        return plot


if __name__ == '__main__':

    param_table = ParametersTable()

    pt = np.zeros((100,), dtype=param_dtype)

    for i in xrange(100):
        pt['block_id'][i] = long(i)
        pt['time_stamp'][i] = float(i + 20)
        pt['rms'][i] = 100.0 * np.random.normal()
        pt['peak'][i] = 110.21 * np.random.normal()
        pt['count'][i] = int(23 * np.random.normal())

    param_table.table = pt

    parameters_plot = ParametersTablePlot(dataset=param_table)
    parameters_plot.configure_traits(view='trait_view')

#EOF
