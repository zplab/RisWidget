# This code is licensed under the MIT License (see LICENSE file for details)

from contextlib import ExitStack
import math
import numpy
from OpenGL import GL
from PyQt5 import Qt

from . import shader_item
from .. import shared_resources
from .. import internal_util

class HistogramItem(shader_item.ShaderItem):
    QGRAPHICSITEM_TYPE = shared_resources.generate_unique_qgraphicsitem_type()

    def __init__(self, layer_stack, graphics_item_parent=None):
        super().__init__(graphics_item_parent)
        self.setAcceptHoverEvents(True)
        self.contextual_info_pos = None
        self.layer_stack = layer_stack
        self._hist_tex_needs_upload = True
        self._bounding_rect = Qt.QRectF(0, 0, 1, 1)
        self._tex = None
        self._gl_widget = None
        self.min_item = MinMaxItem(self, 'min')
        self.max_item = MinMaxItem(self, 'max')
        self.gamma_item = GammaItem(self, self.min_item, self.max_item)
        self.gamma_gamma = 1.0
        self.hide()
        layer_stack.layer_focus_changed.connect(self._on_layer_focus_changed)
        self._connect_layer(layer_stack.layers[0])

    def _on_layer_focus_changed(self, layer_stack, old_layer, new_layer):
        assert layer_stack is self.layer_stack
        assert self.layer is old_layer
        if old_layer is not None:
            old_layer.image_changed.disconnect(self._on_layer_histogram_change)
            old_layer.min_changed.disconnect(self.min_item.arrow_item._on_value_changed)
            old_layer.max_changed.disconnect(self.max_item.arrow_item._on_value_changed)
            old_layer.histogram_min_changed.disconnect(self._on_layer_histogram_change)
            old_layer.histogram_max_changed.disconnect(self._on_layer_histogram_change)
            old_layer.gamma_changed.disconnect(self.gamma_item._on_value_changed)
        self._connect_layer(new_layer)

    def _connect_layer(self, layer):
        self.layer = layer
        if layer is not None:
            layer.image_changed.connect(self._on_layer_histogram_change)
            layer.min_changed.connect(self.min_item.arrow_item._on_value_changed)
            layer.max_changed.connect(self.max_item.arrow_item._on_value_changed)
            layer.histogram_min_changed.connect(self._on_layer_histogram_change)
            layer.histogram_max_changed.connect(self._on_layer_histogram_change)
            layer.gamma_changed.connect(self.gamma_item._on_value_changed)
        self._on_layer_histogram_change()


    def boundingRect(self):
        return self._bounding_rect

    def paint(self, qpainter, option, widget):
        assert widget is not None, 'histogram_scene.HistogramItem.paint called with widget=None.  Ensure that view caching is disabled.'
        if self._gl_widget is None:
            self._gl_widget = widget
        else:
            assert self._gl_widget is widget
        layer = self.layer
        if layer is None or layer.image is None:
            if self._tex is not None:
                self._tex.destroy()
                self._tex = None
        else:
            widget_size = widget.size()
            histogram = self.layer.histogram
            with ExitStack() as estack:
                qpainter.beginNativePainting()
                estack.callback(qpainter.endNativePainting)
                QGL = shared_resources.QGL()
                desired_shader_type = 'G'
                if desired_shader_type in self.progs:
                    prog = self.progs[desired_shader_type]
                    if not QGL.glIsProgram(prog.programId()):
                        # The current GL context is in a state of flux, likely because a histogram view is in a dock widget that is in
                        # the process of being floated or docked.
                        return
                else:
                    prog = self.build_shader_prog(
                        desired_shader_type,
                        'planar_quad_vertex_shader',
                        'histogram_item_fragment_shader')
                desired_tex_width = len(histogram)
                tex = self._tex
                if tex is not None:
                    if tex.width() != desired_tex_width:
                        tex.destroy()
                        tex = None
                if tex is None:
                    tex = Qt.QOpenGLTexture(Qt.QOpenGLTexture.Target1D)
                    tex.setFormat(Qt.QOpenGLTexture.R32F)
                    tex.setWrapMode(Qt.QOpenGLTexture.ClampToEdge)
                    tex.setMipLevels(1)
                    tex.setAutoMipMapGenerationEnabled(False)
                    tex.setSize(desired_tex_width)
                    tex.allocateStorage()
                    # tex stores histogram bin counts - values that are intended to be addressed by element without
                    # interpolation.  Thus, nearest neighbor for texture filtering.
                    tex.setMinMagFilters(Qt.QOpenGLTexture.Nearest, Qt.QOpenGLTexture.Nearest)
                    tex.bind()
                    estack.callback(tex.release)
                    self._hist_tex_needs_upload = True
                else:
                    tex.bind()
                    estack.callback(tex.release)
                max_bin_val = histogram.max()
                if self._hist_tex_needs_upload:
                    GL.glTexSubImage1D(
                        GL.GL_TEXTURE_1D, 0, 0, desired_tex_width, GL.GL_RED,
                        GL.GL_UNSIGNED_INT,
                        memoryview(histogram)
                    )
                    self._hist_tex_needs_upload = False
                    self._tex = tex
                glQuad = shared_resources.GL_QUAD()
                if not glQuad.buffer.bind():
                    Qt.qDebug('shared_resources.GL_QUAD.buffer.bind() failed')
                    return
                estack.callback(glQuad.buffer.release)
                glQuad.vao.bind()
                estack.callback(glQuad.vao.release)
                if not prog.bind():
                    Qt.qDebug('prog.bind() failed')
                    return
                estack.callback(prog.release)
                vert_coord_loc = prog.attributeLocation('vert_coord')
                if vert_coord_loc < 0:
                    Qt.qDebug('vert_coord_loc < 0')
                    return
                prog.enableAttributeArray(vert_coord_loc)
                prog.setAttributeBuffer(vert_coord_loc, QGL.GL_FLOAT, 0, 2, 0)
                prog.setUniformValue('tex', 0)
                dpi_ratio = widget.devicePixelRatio()
                prog.setUniformValue('inv_view_size', 1/(dpi_ratio * widget_size.width()), 1/(dpi_ratio * widget_size.height()))
                inv_max_transformed_bin_val = max_bin_val**-self.gamma_gamma
                prog.setUniformValue('inv_max_transformed_bin_val', inv_max_transformed_bin_val)
                prog.setUniformValue('gamma_gamma', self.gamma_gamma)
                prog.setUniformValue('opacity', self.opacity())
                self.set_blend(estack)
                QGL.glEnableClientState(QGL.GL_VERTEX_ARRAY)
                QGL.glDrawArrays(QGL.GL_TRIANGLE_FAN, 0, 4)

    def hoverMoveEvent(self, event):
        self.contextual_info_pos = event.pos()
        self._update_contextual_info()

    def hoverLeaveEvent(self, event):
        self.contextual_info_pos = None
        self.scene().contextual_info_item.set_info_text(None)

    def _update_contextual_info(self):
        text = ''
        if self.contextual_info_pos is not None:
            layer = self.layer
            if layer is not None:
                image = layer.image
                if image is not None:
                    histogram = layer.histogram
                    hist_min = layer.histogram_min
                    hist_width = layer.histogram_max - hist_min
                    n_bins = len(histogram)
                    bin_width = hist_width / n_bins
                    bin = int(self.contextual_info_pos.x() * n_bins)
                    l, r = hist_min + bin * bin_width, hist_min + (bin + 1) * bin_width
                    if image.data.dtype == numpy.float32:
                        bin_text = '[{:.8g},{:.8g}{}'.format(l, r, ']' if bin == n_bins - 1 else ')')
                    else:
                        l, r = int(math.ceil(l)), int(math.floor(r))
                        bin_text = '{}'.format(l) if image.data.dtype == numpy.uint8 else '[{},{}]'.format(l, r)
                    text = bin_text + ': {}'.format(histogram[bin])
        self.scene().contextual_info_item.set_info_text(text)

    def _on_layer_histogram_change(self):
        if self.layer is None or self.layer.image is None:
            self.hide()
        else:
            self.show()
            self._hist_tex_needs_upload = True
            self.min_item.arrow_item._on_value_changed()
            self.max_item.arrow_item._on_value_changed()
            self.gamma_item._on_value_changed()
        if self.scene() is not None:
            self._update_contextual_info()
        self.update()

class MinMaxItem(Qt.QGraphicsObject):
    QGRAPHICSITEM_TYPE = shared_resources.generate_unique_qgraphicsitem_type()

    def __init__(self, histogram_item, name):
        super().__init__(histogram_item)
        self._bounding_rect = Qt.QRectF(-0.1, 0, .2, 1)
        self.arrow_item = MinMaxArrowItem(self, histogram_item, name)
        self.setFlag(Qt.QGraphicsItem.ItemIgnoresParentOpacity)

    def type(self):
        return self.QGRAPHICSITEM_TYPE

    def boundingRect(self):
        return self._bounding_rect

    def paint(self, qpainter, option, widget):
        pen = Qt.QPen(Qt.QColor(255,0,0,128))
        pen.setWidth(0)
        qpainter.setPen(pen)
        br = self.boundingRect()
        x = (br.left() + br.right()) / 2
        qpainter.drawLine(x, br.top(), x, br.bottom())

class MinMaxArrowItem(Qt.QGraphicsObject):
    QGRAPHICSITEM_TYPE = shared_resources.generate_unique_qgraphicsitem_type()

    def __init__(self, min_max_item, histogram_item, name):
        super().__init__(histogram_item)
        self.name = name
        self._path = Qt.QPainterPath()
        self._min_max_item = min_max_item
        if self.name.startswith('min'):
            polygonf = Qt.QPolygonF((Qt.QPointF(0.5, -12), Qt.QPointF(8, 0), Qt.QPointF(0.5, 12)))
        else:
            polygonf = Qt.QPolygonF((Qt.QPointF(-0.5, -12), Qt.QPointF(-8, 0), Qt.QPointF(-0.5, 12)))
        self._path.addPolygon(polygonf)
        self._path.closeSubpath()
        self._bounding_rect = self._path.boundingRect()
        self.setFlag(Qt.QGraphicsItem.ItemIgnoresParentOpacity)
        self.setFlag(Qt.QGraphicsItem.ItemIgnoresTransformations)
        self.setFlag(Qt.QGraphicsItem.ItemIsMovable)
        self._ignore_x_change = internal_util.Condition()
        self.setY(0.5)
        self.xChanged.connect(self._on_x_changed)
        self.yChanged.connect(self._on_y_changed)

    def type(self):
        return self.QGRAPHICSITEM_TYPE

    def boundingRect(self):
        return self._bounding_rect

    def shape(self):
        return self._path

    def paint(self, qpainter, option, widget):
        c = Qt.QColor(255,0,0,128)
        qpainter.setPen(Qt.QPen(c))
        qpainter.setBrush(Qt.QBrush(c))
        qpainter.drawPath(self._path)

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        self.scene().contextual_info_item.set_info_text('{}: {}'.format(self.name, getattr(self.parentItem().layer, self.name)))

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.scene().contextual_info_item.set_info_text('{}: {}'.format(self.name, getattr(self.parentItem().layer, self.name)))

    def _on_x_changed(self):
        x = self.x()
        if not self._ignore_x_change:
            if x < 0:
                self.setX(0)
                x = 0
            elif x > 1:
                self.setX(1)
                x = 1
            layer = self.parentItem().layer
            mn, mx = layer.histogram_min, layer.histogram_max
            setattr(layer, self.name, mn + x * float(mx - mn))
        self._min_max_item.setX(x)

    def _on_y_changed(self):
        if self.y() != 0.5:
            self.setY(0.5)

    def _on_value_changed(self):
        with self._ignore_x_change:
            layer = self.parentItem().layer
            mn, mx = layer.histogram_min, layer.histogram_max
            if mx == mn:
                x = mn
            else:
                x = (getattr(layer, self.name) - mn) / (mx - mn)
            self.setX(x)

class GammaItem(Qt.QGraphicsObject):
    QGRAPHICSITEM_TYPE = shared_resources.generate_unique_qgraphicsitem_type()
    CURVE_VERTEX_Y_INCREMENT = 1 / 100

    def __init__(self, histogram_item, min_item, max_item):
        super().__init__(histogram_item)
        self._bounding_rect = Qt.QRectF(0, 0, 1, 1)
        self.min_item = min_item
        self.min_item.xChanged.connect(self._on_min_or_max_x_changed)
        self.max_item = max_item
        self.max_item.xChanged.connect(self._on_min_or_max_x_changed)
        self._path = Qt.QPainterPath()
        self.setFlag(Qt.QGraphicsItem.ItemIgnoresParentOpacity)
        self.setFlag(Qt.QGraphicsItem.ItemIsMovable)
        self.setZValue(-1)
        # This is a convenient way to ensure that only primary mouse button clicks cause
        # invocation of mouseMoveEvent(..).  Without this, it would be necessary to
        # override mousePressEvent(..) and check which buttons are down, in addition to
        # checking which buttons remain down in mouseMoveEvent(..).
        self.setAcceptedMouseButtons(Qt.Qt.LeftButton)

    def type(self):
        return self.QGRAPHICSITEM_TYPE

    def boundingRect(self):
        return self._bounding_rect

    def shape(self):
        pen = Qt.QPen()
        pen.setWidthF(0)
        stroker = Qt.QPainterPathStroker(pen)
        stroker.setWidth(0.2)
        return stroker.createStroke(self._path)

    def paint(self, qpainter, option, widget):
        if not self._path.isEmpty():
            pen = Qt.QPen(Qt.QColor(255,255,0,128))
            pen.setWidth(2)
            pen.setCosmetic(True)
            qpainter.setPen(pen)
            qpainter.setBrush(Qt.Qt.NoBrush)
            qpainter.drawPath(self._path)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        self.scene().contextual_info_item.set_info_text('gamma: {}'.format(self.parentItem().layer.gamma))

    def mouseMoveEvent(self, event):
        current_x, current_y = map(
            lambda v: min(max(v, 0.001), 0.999),
            (event.pos().x(), event.pos().y()))
        current_y = 1-current_y
        layer = self.parentItem().layer
        layer.gamma = gamma = min(max(math.log(current_y, current_x), layer.GAMMA_RANGE[0]), layer.GAMMA_RANGE[1])
        self.scene().contextual_info_item.set_info_text('gamma: {}'.format(gamma))

    def _on_min_or_max_x_changed(self):
        min_x = self.min_item.x()
        max_x = self.max_item.x()
        t = Qt.QTransform()
        t.translate(min_x, 0)
        t.scale(max_x - min_x, 1)
        self.setTransform(t)

    def _on_value_changed(self):
        self.prepareGeometryChange()
        self._path = Qt.QPainterPath(Qt.QPointF(0, 1))
        gamma = self.parentItem().layer.gamma
        # Compute sample point x locations such that the y increment from one sample point to the next is approximately
        # the constant, resulting in a fairly smooth gamma plot.  This is not particularly fast, but it only happens when
        # gamma value changes, and it's fast enough that there is no noticable choppiness when dragging the gamma curve
        # up and down on a mac mini.
        xs = []
        x = 0
        while x < 1:
            xs.append(x)
            x += (GammaItem.CURVE_VERTEX_Y_INCREMENT + x**gamma)**(1/gamma) - x
        del xs[0]
        for x, y in zip(xs, (x**gamma for x in xs)):
            self._path.lineTo(x, 1.0-y)
        self._path.lineTo(1, 0)
        self.update()