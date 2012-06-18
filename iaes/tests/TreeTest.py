"""
@author:
Eraldo Pomponi

@copyright:
2012 - Eraldo Pomponi 
eraldo.pomponi@gmail.com

@license:
All rights reserved

Created on Jun 13, 2012
"""

# -*- coding: utf-8 -*-
# <nbformat>3</nbformat>

# <codecell>

from traits.api import HasTraits, Str, List, Instance, Any
from traitsui.api import View, Item, TreeEditor, TreeNode


class Foo(HasTraits):

    view = View()

    def __init__(self):
        super(HasTraits, self).__init__()
        self.create_trait_view()

    def create_trait_view(self):
        self.add_trait('n1', 10)
        self.add_trait('n2', 20)
        trait_dict = self._instance_traits()
        items = [Item(name) for name in sorted(trait_dict)]
        self.view = View(*items)


class ListFoo(HasTraits):
    name = Str('List of Foo')
    foos = List(Foo)


class MyTreeNode(TreeNode):

    def get_view(self, object):
        return object.create_trait_view()


no_view = View()


tr = TreeEditor(
            nodes=[
                    TreeNode(
                             node_for=[ListFoo],
                             auto_open=True,
                             children='foos',
                             label='=Foo class',
                             view=no_view,
                             ),
                    MyTreeNode(
                             node_for=[Foo],
                             auto_open=True,
                             children='',
                             label='=Foo class',
                             view='object.trait_view',
                             )
                    ],
                    editable=False
               )


class TreeTest(HasTraits):
    """ Defines a business partner."""

    name = Str('<unknown>')
    lfoo = Instance(ListFoo)

    view = View(
        Item(name='lfoo',
             editor=tr,
             show_label=False
        ),
        title='Tree Test',
        buttons=['OK'],
        resizable=True,
        style='custom',
        width=.3,
        height=.5
    )

# <codecell>

if __name__ == '__main__':

    a = Foo()
    b = Foo()

    lf = ListFoo(name='lf', foos=[a, b])

    # <codecell>

    tt = TreeTest(name='Instance Tree', lfoo=lf)

    # <codecell>

    tt.configure_traits()



