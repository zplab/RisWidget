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

LANGUAGE = C++
QT += core gui widgets opengl
CONFIG += c++11 precompile_header exceptions rtti stl thread debug largefile
CONFIG -= app_bundle
TARGET = RisWidget
unix {
    CFLAGS += -fno-omit-frame-pointer
    INCLUDEPATH += /usr/local/include /usr/local/glm /usr/include/python3.4 /usr/lib64/python3.4/site-packages/numpy/core/include
    LIBS += -lpython3.4 -lboost_python-3.4 -L/usr/local/lib -lboost_numpy
} else:macx {
    CFLAGS += -fno-omit-frame-pointer
    INCLUDEPATH += -I/Library/Frameworks/Python.framework/Versions/3.4/include/python3.4m -I/Library/Frameworks/Python.framework/Versions/3.4/include/python3.4m
    LIBS += -ldl -framework CoreFoundation -lpython3.4m
}
DEFINES += ENABLE_GL_DEBUG_LOGGING STAND_ALONE_EXECUTABLE

RESOURCES = RisWidget.qrc

PRECOMPILED_HEADER = Common.h

HEADERS += Common.h \
           GilStateScopeOperators.h \
           HistogramWidget.h \
           HistogramView.h \
           ImageWidget.h \
           ImageWidgetViewScroller.h \
           ImageView.h \
           LockedRef.h \
           Renderer.h \
           RisWidget.h \
           RisWidgetException.h \
           ShowCheckerDialog.h \
           View.h \
           ViewWidget.h

FORMS +=   RisWidget.ui \
           HistogramWidget.ui \
           ImageWidget.ui \
           ShowCheckerDialog.ui

SOURCES += RisWidget.cpp \
           GilStateScopeOperators.cpp \
           HistogramWidget.cpp \
           HistogramView.cpp \
           ImageWidget.cpp \
           ImageWidgetViewScroller.cpp \
           ImageView.cpp \
           Renderer.cpp \
           RisWidgetException.cpp \
           ShowCheckerDialog.cpp \
           View.cpp \
           ViewWidget.cpp