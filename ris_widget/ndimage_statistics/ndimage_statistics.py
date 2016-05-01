# The MIT License (MIT)
#
# Copyright (c) 2014-2016 WUSTL ZPLAB
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
# Authors: Erik Hvatum <ice.rikh@gmail.com>, Zach Pincus

import numpy
import numpy.ma
from collections import namedtuple
import concurrent.futures as futures
import multiprocessing

pool = futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() + 1)
inner_pool = futures.ThreadPoolExecutor(max_workers=multiprocessing.cpu_count() + 1)

NDImageStatistics = namedtuple('NDImageStatistics', ('histogram', 'max_bin', 'min_max_intensity'))

try:
    from . import _ndimage_statistics

    def _min_max(im, mask=None):
        min_max = numpy.zeros((2,), dtype=im.dtype)
        if mask is None:
            _ndimage_statistics.min_max(im, min_max)
        else:
            _ndimage_statistics.masked_min_max(im, mask, min_max)
        return min_max

    def _histogram(im, bin_count, range_, mask=None, with_overflow_bins=False):
        hist = numpy.zeros((bin_count,), dtype=numpy.uint32)
        if mask is None:
            _ndimage_statistics.ranged_hist(im, range_, hist, with_overflow_bins)
        else:
            _ndimage_statistics.masked_ranged_hist(im, mask, range_, hist, with_overflow_bins)
        return hist

    def _statistics(im, is_twelve_bit, hist, min_max, mask=None):
        if mask is None:
            _ndimage_statistics.hist_min_max(im, hist, min_max, is_twelve_bit)
        else:
            _ndimage_statistics.masked_hist_min_max(im, mask, hist, min_max, is_twelve_bit)

except ImportError:
    import warnings
    warnings.warn('warning: Failed to load _ndimage_statistics binary module; using slow histogram and extrema computation methods.')

    def _stretch_mask(im, mask):
        if im.shape != mask.shape:
            x_lut = numpy.linspace(0, im.shape[0]-1, im.shape[0], dtype=numpy.uint32)
            y_lut = numpy.linspace(0, im.shape[1]-1, im.shape[1], dtype=numpy.uint32)
            xx_lut, yy_lut = numpy.meshgrid(x_lut, y_lut, indexing='ij')
            mask = mask[xx_lut, yy_lut]
        return mask

    def _min_max(im, mask=None):
        if mask is not None:
            mask = _stretch_mask(im, mask)
            im = numpy.ma.array(im, dtype=im.dtype, copy=False, mask=~mask)
        return numpy.array((im.min(), im.max()), dtype=im.dtype)

    def _histogram(im, bin_count, range_, mask=None, with_overflow_bins=False):
        if mask is not None:
            mask = _stretch_mask(im, mask)
        if with_overflow_bins:
            assert bin_count >= 3
            hist = numpy.zeros((bin_count,), dtype=numpy.uint32)
            hist[1:-1] = numpy.histogram(im, bins=bin_count-2, range=range_, density=False, weights=mask)[0].astype(numpy.uint32)
            if mask is not None:
                im = numpy.ma.array(im, dtype=im.dtype, copy=False, mask=~mask)
            hist[0] = (im < range_[0]).sum()
            hist[-1] = (im > range_[1]).sum()
            return hist
        else:
            assert bin_count >= 1
            return numpy.histogram(im, bins=bin_count, range=range_, density=False, weights=mask)[0].astype(numpy.uint32)

    def _statistics(im, twelve_bit, mask=None):
        if im.dtype == numpy.uint8:
            min_max = numpy.zeros((2,), dtype=numpy.uint8)
            bin_count = 256
            range_ = (0,255)
        elif im.dtype == numpy.uint16:
            min_max = numpy.zeros((2,), dtype=numpy.uint16)
            bin_count = 1024
            range_ = (0,4095) if twelve_bit else (0,65535)
        else:
            raise NotImplementedError('Support for dtype of supplied im argument not implemented.')
        if mask is not None:
            mask = _stretch_mask(im, mask)
        hist = numpy.histogram(im, bins=bin_count, range=range_, density=False, weights=mask)[0].astype(numpy.uint32)
        if mask is not None:
            im = numpy.ma.array(im, dtype=im.dtype, copy=False, mask=~mask)
        min_max[0] = im.min()
        min_max[1] = im.max()
        return NDImageStatistics(hist, hist.argmax(), min_max)

def extremae(im, mask=None, per_channel_thread_count=2, return_future=False):
    """im: The 2D or 3D ndarray for which min and max values are found.
    mask: None or a 2D bool or uint8 ndarray with neither dimension smaller than the corresponding dimension of im.  If mask is not None, only image
    pixels with non-zero mask counterparts contribute to min_max.  Pixels of mask outside of im have no impact.  If mask is None, all image pixels are
    included.
    return_future: If not False, a concurrent.futures.Future is returned.

    Returns a channel_count x 2 numpy array containing the min and max element values over the masked region or entirety of im."""
    assert im.ndim in (2, 3)
    if mask is not None:
        assert mask.ndim == 2
        assert mask.dtype in (numpy.uint8, numpy.bool)
    if im.ndim == 2:
        def proc():
            return _min_max(im, mask)
    else:
        def channel_proc(channel):
            return _min_max(im[..., channel], mask)
        def proc():
            futes = [pool.submit(channel_proc, channel) for channel in range(im.shape[2])]
            ret = numpy.vstack(fute.result() for fute in futes)
            if ret.dtype != im.dtype:
                ret = ret.astype(im.dtype)
            return ret
    return pool.submit(proc) if return_future else proc()

# In the unlikely scenario where float32 histogram performance proves critically important on a scope system, it would be useful to look at
# http://cuda-programming.blogspot.com/2013/03/optimization-in-histogram-cuda-code.html  The various approaches taken here are generally the same
# as those we tried in opencl, with the wrinkle that in part 4, the author goes one step further than we did, using nvidia's absurdly good cuda profiler
# to identify memory bank contention, which he resolves for a huge throughput improvement.
def histogram(im, bin_count, range_, mask=None, with_overflow_bins=False, per_channel_thread_count=2, return_future=False):
    """im: The 2D or 3D ndarray for which histogram is computed.
    range_: An indexable sequence of at least two elements, castable to float32, representing the closed interval which is divided into bin_count number
    of bins comprising the histogram.
    mask: None or a 2D bool or uint8 ndarray with neither dimension smaller than the corresponding dimension of im.  If mask is not None, only image
    pixels with non-zero mask counterparts contribute to the histogram.  Mask pixels outside of im have no impact.  If mask is None, all image pixels
    are included.
    with_overfloat_bins: If true, the first and last histogram bins represent the number of image pixels falling below and above range_, respectively.
    return_future: If not False, a concurrent.futures.Future is returned.

    Returns a channel_count x bin_count numpy array uint32 values."""
    assert im.ndim in (2, 3)
    assert range_[0] < range_[1]
    if mask is not None:
        assert mask.ndim == 2
        assert mask.dtype in (numpy.uint8, numpy.bool)
    if with_overflow_bins:
        assert bin_count >= 4
    else:
        assert bin_count >= 2
    if im.ndim == 2:
        def proc():
            return _histogram(im, bin_count, range_, mask, with_overflow_bins)
    else:
        def channel_proc(axis):
            return _histogram(im[..., axis], bin_count, range_, mask, with_overflow_bins)
        def proc():
            futes = [pool.submit(channel_proc, axis) for axis in range(im.shape[2])]
            return numpy.vstack(fute.result() for fute in futes)
    return pool.submit(proc) if return_future else proc()

def statistics(im, is_twelve_bit=False, mask=None, per_channel_thread_count=2, return_future=False):
    assert im.ndim in (2, 3)
    if im.ndim == 2:
        # NB: we very much want to avoid
        thread_hists = numpy.array()
        def proc():

            return _statistics(im, is_twelve_bit, mask)
    else:
        def channel_proc(channel):
            return _statistics(im[..., channel], twelve_bit, mask)
        def proc():
            results = [channel_proc(channel) for channel in range(im.shape[2])]
            return NDImageStatistics(
                numpy.vstack((result.histogram for result in results)),
                numpy.hstack((result.max_bin for result in results)),
                numpy.vstack((result.min_max_intensity for result in results)))
    return pool.submit(proc) if return_future else proc()

def bundle_float_stats_into_future(histogram, extremae):
    def proc():
        return NDImageStatistics(
            histogram,
            histogram.argmax() if histogram.ndim == 1 else numpy.array([ch.argmax() for ch in histogram]),
            extremae)
    return pool.submit(proc)