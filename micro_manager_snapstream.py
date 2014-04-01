# The MIT License (MIT)
#
# Copyright (c) 2014 Erik Hvatum
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

import threading

from ris_widget.ris import Ris

class MicroManagerSnapStream(Ris):
    def __init__(self, mmc):
        super().__init__()
        self.mmc = mmc
        self.stopLock = threading.Lock()
        with self.stopLock:
            self.stop = True

    def _doStart(self):
        self.prevShape = None
        with self.stopLock:
            self.stop = False
        self.acquire()

    def _doStop(self):
        with self.stopLock:
            self.stop = True

    def _doAcquire(self):
        stop = None
        with self.stopLock:
            stop = self.stop
        if not stop:
            self.mmc.snapImage()

        with self.stopLock:
            stop = self.stop
        if not stop:
            image = self.mmc.getImage()

        self._signalImageAcquired(image)

    def _imageAcquired(self, image):
        sameShape = image.shape == self.prevShape
        self.prevShape = image.shape
        for sink in self._sinks:
            sink.showImage(image, sameShape)
        self.acquire()
