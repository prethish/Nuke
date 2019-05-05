"""This was written for the artist to replace the normal ascii export
so that they export the retime curves with more control over the column order.
I also modified the default tcl script to take in extra arguments.
"""
from PySide2 import QtWidgets, QtCore
import nuke


class QtCustomLineEdit(QtWidgets.QWidget):
    def __init__(self, text, display_text, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.setLayout(QtWidgets.QHBoxLayout())
        self.qtext = QtWidgets.QLineEdit(text)
        self.qdisplay_text = QtWidgets.QLabel(display_text)
        self.layout().addWidget(self.qdisplay_text)
        self.layout().addWidget(self.qtext)

    def set_text(self, str):
        self.qtext.setText(str)

    def set_display_text(self, str):
        self.qdisplay_text.setText(str)

    def get_display_text(self):
        return self.qdisplay_text.text()

    def get_text(self):
        return self.qtext.text()


class ExportAsciiPanel(QtWidgets.QWidget):
    def __init__(self, nuke_node, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self._node = nuke_node
        self._columns = []
        self.setLayout(QtWidgets.QVBoxLayout())
        self.curves_list = QtWidgets.QListWidget()
        self.curves_list.setSelectionMode(
            QtWidgets.QAbstractItemView.MultiSelection)
        self.start_frame = QtCustomLineEdit(text='', display_text='Start at')
        self.end_frame = QtCustomLineEdit(text='', display_text='End at')
        self.column_zone = QtWidgets.QVBoxLayout()
        self.execute_export_btn = QtWidgets.QPushButton('Export Curves')
        self.layout().addWidget(self.curves_list)
        self.layout().addWidget(self.start_frame)
        self.layout().addWidget(self.end_frame)
        self.layout().addLayout(self.column_zone)
        self.layout().addWidget(self.execute_export_btn)
        self.connect_slots()
        self.update_curves_list()
        self.create_column_options()

    def connect_slots(self):
        self.curves_list.itemSelectionChanged.connect(
            self.create_column_options)
        self.execute_export_btn.clicked.connect(self.export_curves)

    def update_curves_list(self):
        self.curves_list.clear()
        for knob_name, knob in self._node.knobs().iteritems():
            if knob.isAnimated():
                for curve in knob.animations():
                    txt = curve.knobAndFieldName()
                    if txt.endswith('.'):
                        txt = txt[:-1]
                    self.curves_list.addItem(txt)
        self.select_all()

    def select_all(self):
        for i in range(self.curves_list.count()):
            self.curves_list.item(i).setSelected(True)

    def create_column_options(self):
        for col in self._columns:
            col.setParent(None)
        self._columns = []
        for index, item in enumerate(self.curves_list.selectedItems()):
            column = QtCustomLineEdit(text=str(index),
                                      display_text='Column for :{}'.format(item.text()))
            self._columns.append(column)
            self.column_zone.addWidget(column)

    def getCurveAt(self, position):
        for column in self._columns:
            if position == column.get_text():
                return column.get_display_text().split(':')[1]

    def export_curves(self):
        file_name = ''
        start = self.start_frame.get_text()
        end = self.end_frame.get_text()
        curve_list = []
        for i in range(len(self._columns)):
            curve_list.append(
                '%s.%s' % (self._node.name(), self.getCurveAt(i))
            )

        nuke.tcl('set curves {{clist}};'
                 'export_ascii_curves '
                 '{file} {s} {e} $curves'.format(
                     clist=' '.join(curve_list),
                     file=file_name,
                     s=start,
                     e=end)
                 )


panel = ExportAsciiPanel(nuke.selectedNode())
panel.show()
