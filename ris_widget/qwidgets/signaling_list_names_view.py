# The MIT License (MIT)
#
# Copyright (c) 2015 WUSTL ZPLAB
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# Authors: Erik Hvatum <ice.rikh@gmail.com>

from PyQt5 import Qt
from ..signaling_list import SignalingList

class SignalingListNamesView(Qt.QListView):
    """SignalingListNamesView: a QListView subclass that shows the value of the element.name property
    for each element in SignalingListNamesView_instance.signaling_list, in order, with .signaling_list[0]
    at the top.

    Signals:
    current_row_changed(index of new current/focused row in signaling_list, the element from signalist_list)"""
    current_row_changed = Qt.pyqtSignal(int, object)

    def __init__(self, parent=None, signaling_list=None, item_flags_callback=None, supported_drop_actions=0, SignalingListNamesModelClass=None):
        super().__init__(parent)
        self._item_flags_callback = item_flags_callback
        self._supported_drop_actions = supported_drop_actions
        self.SignalingListNamesModelClass = SignalingListNamesModel if SignalingListNamesModelClass is None else SignalingListNamesModelClass
        self._signaling_list = None
        self.signaling_list = signaling_list

    def _default_item_flags_callback(self, midx):
        return Qt.Qt.ItemIsEnabled | Qt.Qt.ItemIsSelectable | Qt.Qt.ItemNeverHasChildren

    @property
    def signaling_list(self):
        return self._signaling_list

    @signaling_list.setter
    def signaling_list(self, sl):
        if sl is not self._signaling_list:
            old_models = self.model(), self.selectionModel()
            if sl is None:
                self.setModel(None)
            else:
                self.setModel(self.SignalingListNamesModelClass(self, sl, self._item_flags_callback, self._supported_drop_actions))
                self.selectionModel().currentRowChanged.connect(self._on_model_current_row_changed)
            self._signaling_list = sl
            for old_model in old_models:
                if old_model is not None:
                    old_model.deleteLater()

    @property
    def item_flags_callback(self):
        return self._default_item_flags_callback if self._item_flags_callback is None else self._item_flags_callback

    @item_flags_callback.setter
    def item_flags_callback(self, v):
        self._item_flags_callback = v
        model = self.model()
        if model is not None:
            model.item_flags_callback = v

    @item_flags_callback.deleter
    def item_flags_callback(self):
        self.item_flags_callback = None

    @property
    def supported_drop_actions(self):
        return self._supported_drop_actions

    @supported_drop_actions.setter
    def supported_drop_actions(self, v):
        self._supported_drop_actions = v
        model = self.model()
        if model is not None:
            model.supported_drop_actions = v

    def _on_model_current_row_changed(self, old_midx, midx):
        row = midx.row()
        if 0 <= row < len(self._signaling_list):
            self.current_row_changed.emit(row, self._signaling_list[row])

class SignalingListNamesModel(Qt.QAbstractListModel):
    def __init__(self, parent, signaling_list, item_flags_callback, supported_drop_actions):
        assert isinstance(signaling_list, SignalingList)
        super().__init__(parent)
        self.item_flags_callback = item_flags_callback
        self.supported_drop_actions = supported_drop_actions
        signaling_list.inserting.connect(self._on_inserting)
        signaling_list.inserted.connect(self._on_inserted)
        signaling_list.removing.connect(self._on_removing)
        signaling_list.removed.connect(self._on_removed)
        self._element_name_changed_signal_mapper = Qt.QSignalMapper(self)
        self._element_name_changed_signal_mapper.mapped[Qt.QObject].connect(self._on_element_name_changed)
        for element in signaling_list:
            self._element_name_changed_signal_mapper.setMapping(element, element)
            element.name_changed.connect(self._element_name_changed_signal_mapper.map)
        self.signaling_list = signaling_list

    def rowCount(self, _=None):
        return len(self.signaling_list)

    def data(self, midx, role=Qt.Qt.DisplayRole):
        if role == Qt.Qt.DisplayRole and midx.column() == 0:
            return Qt.QVariant(self.signaling_list[midx.row()].name)
        return Qt.QVariant()

    def flags(self, midx):
        return self.item_flags_callback(midx)

    def supportedDropActions(self):
        return self.supported_drop_actions

    def removeRow(self, row, pmidx=Qt.QModelIndex()):
        if 0 <= row < len(self.signaling_list):
            del self.signaling_list[row]
            return True
        else:
            return False

    def removeRows(self, row, row_count, pmidx=Qt.QModelIndex()):
        end_row = row+row_count
        if 0 <= row < len(self.signaling_list) and 0 <= end_row < len(self.signaling_list):
            del self.signaling_list[row:end_row]
            return True
        else:
            return False

    def _on_inserting(self, idx, element):

        self.beginInsertRows(Qt.QModelIndex(), idx, idx)

    def _on_inserted(self, idx, element):
        self.endInsertRows()
        self._element_name_changed_signal_mapper.setMapping(element, element)
        element.name_changed.connect(self._element_name_changed_signal_mapper.map)

    def _on_removing(self, idx, element):
        self.beginRemoveRows(Qt.QModelIndex(), idx, idx)

    def _on_removed(self, idx, element):
        self.endRemoveRows()
        element.name_changed.disconnect(self._element_name_changed_signal_mapper.map)
        self._element_name_changed_signal_mapper.removeMappings(element)

    def _on_element_name_changed(self, element):
        idx = self.signaling_list.index(element)
        self.dataChanged.emit(self.createIndex(idx), self.createIndex(idx), (Qt.Qt.DisplayRole,))
