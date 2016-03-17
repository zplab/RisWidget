# The MIT License (MIT)
#
# Copyright (c) 2016 WUSTL ZPLAB
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
from .. import om

class _BaseField(Qt.QWidget):
    widget_value_changed = Qt.pyqtSignal(object)

    def __init__(self, field_tuple, parent):
        super().__init__(parent)
        self.name = field_tuple[0]
        self.type = field_tuple[1]
        self.default = self.type(field_tuple[2])
        self.field_tuple = field_tuple
        self.setLayout(Qt.QHBoxLayout())
        self._init_label()
        self._init_widget()

    def _init_label(self):
        self.label = Qt.QLabel(self.name, self)
        self.layout().addWidget(self.label)
        self.layout().addStretch()

    def _init_widget(self):
        pass

    def _on_widget_change(self):
        self.widget_value_changed.emit(self)

    def refresh(self, value):
        self.widget.setValue(value)

    def value(self):
        return self.widget.value()

class _StringField(_BaseField):
    def _init_widget(self):
        self.widget = Qt.QLineEdit(self)
        self.layout().addWidget(self.widget)
        self.widget.textEdited.connect(self._on_widget_change)

    def refresh(self, value):
        self.widget.setText(value)

    def value(self):
        return self.widget.text()

class _IntField(_BaseField):
    def _init_widget(self):
        self.min = self.field_tuple[3] if len(self.field_tuple) >= 4 else None
        self.max = self.field_tuple[4] if len(self.field_tuple) >= 5 else None
        self.widget = Qt.QSpinBox(self)
        if self.min is not None:
            self.widget.setMinimum(self.min)
            if self.max is not None:
                self.widget.setMaximum(self.max)
        self.widget.valueChanged.connect(self._on_widget_change)
        l = self.layout()
        l.addWidget(self.widget)
        self.setLayout(l)

class _FloatField(_BaseField):
    def _init_widget(self):
        self.widget = Qt.QLineEdit(self)
        self.min = self.field_tuple[3] if len(self.field_tuple) >= 4 else None
        self.max = self.field_tuple[4] if len(self.field_tuple) >= 5 else None
        self.widget.textEdited.connect(self._on_widget_change)
        self.widget.editingFinished.connect(self._on_editing_finished)
        self.layout().addWidget(self.widget)

    def _on_editing_finished(self):
        v = self.value()
        self.refresh(v)

    def refresh(self, value):
        self.widget.setText(str(value))

    def value(self):
        try:
            v = float(self.widget.text())
        except ValueError:
            return self.default
        if self.min is not None and v < self.min:
            return self.min
        elif self.max is not None and v > self.max:
            return self.max
        else:
            return v

class FlipbookPageAnnotator(Qt.QWidget):
    """Field widgets are grayed out when no flipbook entry is focused."""
    TYPE_FIELD_CLASSES = {
        str: _StringField,
        int: _IntField,
        float : _FloatField,
        #tuple : _ChoiceField
    }
    def __init__(self, flipbook, page_metadata_attribute_name, field_descrs, parent=None):
        super().__init__(parent)
        self.flipbook = flipbook
        flipbook.page_focus_changed.connect(self._on_page_focus_changed)
        self.page_metadata_attribute_name = page_metadata_attribute_name
        layout = Qt.QVBoxLayout()
        self.setLayout(layout)
        self.fields = {}
        for field_descr in field_descrs:
            assert field_descr[0] not in self.fields
            field = self._make_field(field_descr)
            field.refresh(field_descr[2])
            field.widget_value_changed.connect(self._on_gui_change)
            layout.addWidget(field)
            self.fields[field_descr[0]] = field
        layout.addStretch()
        self.refresh_gui()

    @property
    def data(self):
        data = []
        for page in self.flipbook.pages:
            if hasattr(page, self.page_metadata_attribute_name):
                page_data = getattr(page, self.page_metadata_attribute_name)
            else:
                page_data = {}
                setattr(page, self.page_metadata_attribute_name, page_data)
            for field in self.fields.values():
                if field.name not in page_data:
                    page_data[field.name] = field.default
            data.append(page_data)
        return data

    @data.setter
    def data(self, v):
        # Replace relevant values in annotations of corresponding pages.  In the situation where an incomplete
        # dict is supplied for a page also missing the omitted values, defaults are assigned.
        m_n = self.page_metadata_attribute_name
        for page_v, page in zip(v, self.flipbook.pages):
            old_page_data = getattr(page, m_n, {})
            updated_page_data = {}
            for field in self.fields.values():
                n = field.name
                if n in page_v:
                    updated_page_data[n] = page_v[n]
                elif n in old_page_data:
                    updated_page_data[n] = old_page_data[n]
                else:
                    updated_page_data[n] = field.default
            setattr(page, m_n, updated_page_data)
        self.refresh_gui()

    def _make_field(self, field_descr):
        return self.TYPE_FIELD_CLASSES[field_descr[1]](field_descr, None)

    def _on_page_focus_changed(self):
        self.refresh_gui()

    def _on_gui_change(self, field):
        page = self.flipbook.focused_page
        if page is not None:
            data = getattr(page, self.page_metadata_attribute_name)
            data[field.name] = field.value()

    def refresh_gui(self):
        """Ensures that the currently focused flipbook page's annotation dict contains at least default values, and
        updates the annotator GUI with data from the annotation dict."""
        page = self.flipbook.focused_page
        if page is None:
            for field in self.fields.values():
                field.setEnabled(False)
        else:
            if hasattr(page, self.page_metadata_attribute_name):
                data = getattr(page, self.page_metadata_attribute_name)
            else:
                data = {}
                setattr(page, self.page_metadata_attribute_name, data)

            for field in self.fields.values():
                if field.name in data:
                    v = data[field.name]
                else:
                    v = data[field.name] = field.default
                field.refresh(v)
                field.setEnabled(True)