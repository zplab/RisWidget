#!/usr/bin/env python

# import sys
# import numpy
# from ris_widget.ndimage_statistics.test_and_benchmark import test
# test()
#

# im = numpy.array(list(range(65536)), dtype=numpy.uint8).reshape((256,256),order='F')

# from ris_widget.ndimage_statistics.test_and_benchmark import test
# test()

# sys.exit(0)

import numpy
import os.path
from pathlib import Path
from PyQt5 import Qt
from ris_widget.ris_widget import RisWidget
import freeimage
import sys

argv = sys.argv
#Qt.QCoreApplication.setAttribute(Qt.Qt.AA_ShareOpenGLContexts)
app = Qt.QApplication(argv)

rw = RisWidget()

# rw.main_view.zoom_preset_idx = 27

# rw.flipbook.pages.append(numpy.array(list(range(10000)),numpy.uint16).reshape((100,100)))
# rw.flipbook.pages[0][0].name = 'image'
# rw.flipbook.pages[0].append(numpy.zeros((100,10), numpy.bool))
# rw.flipbook.pages[0][1].name = 'mask'

# rw.image = numpy.zeros((100,100), dtype=numpy.uint8)

# im = freeimage.read('/Volumes/MrSpinny/14/2015-11-18t0948 focus-03_ffc.png')
rw_dpath = Path(os.path.expanduser('~')) / 'zplrepo' / 'ris_widget'
# rw.flipbook_pages.append(im)
# mask = im > 0
# rw.qt_object.layer_stack.imposed_image_mask = mask[:781,:1000]
# rw.flipbook_pages.append(rw.qt_object.layer_stack.imposed_image_mask)
#
rw.add_image_files_to_flipbook([
    [rw_dpath / 'Opteron_6300_die_shot_16_core_mod.jpg', rw_dpath / 'top_left_g.png'],
    ['/Volumes/MrSpinny/14/2015-11-18t0948 focus-03_ffc.png']
])

#rw.histogram_view.gl_widget.start_logging()

app.exec_()