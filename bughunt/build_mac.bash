#!/usr/bin/env bash

/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/clang++ -shared -pipe -O2 -fPIC -isysroot /Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.8.sdk -std=c++11 -stdlib=libc++ -mmacosx-version-min=10.7 -Wall -W -DQT_NO_DEBUG -DQT_WIDGETS_LIB -DQT_GUI_LIB -DQT_CORE_LIB -I/usr/local/qt/5.3/clang_64/mkspecs/macx-clang -I. -I/Library/Frameworks/Python.framework/Versions/3.4/include/python3.4m -I/usr/local/qt/5.3/clang_64/lib/QtWidgets.framework/Versions/5/Headers -I/usr/local/qt/5.3/clang_64/lib/QtGui.framework/Versions/5/Headers -I/usr/local/qt/5.3/clang_64/lib/QtCore.framework/Versions/5/Headers -I. -I/usr/local/boost/include/boost-1_55 -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.8.sdk/System/Library/Frameworks/OpenGL.framework/Versions/A/Headers -I/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX10.8.sdk/System/Library/Frameworks/AGL.framework/Headers -F/usr/local/qt/5.3/clang_64/lib -framework QtWidgets -framework QtGui -framework QtCore -framework OpenGL -framework AGL sipbughuntBugHunt.cpp sipbughuntcmodule.cpp -lbughunt -L./ -o bughunt.so -L/Library/Frameworks/Python.framework/Versions/3.4/lib/python3.4/config-3.4m -ldl -framework CoreFoundation -lpython3.4m -L/usr/local/boost/lib -lboost_python-clang-darwin42-mt-1_55 -lpthread
