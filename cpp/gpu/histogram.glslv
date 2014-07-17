#version 410 core
#line 3
// The MIT License (MIT)
//
// Copyright (c) 2014 Erik Hvatum
//
// Permission is hereby granted, free of charge, to any person obtaining a copy
// of this software and associated documentation files (the "Software"), to deal
// in the Software without restriction, including without limitation the rights
// to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
// copies of the Software, and to permit persons to whom the Software is
// furnished to do so, subject to the following conditions:
//
// The above copyright notice and this permission notice shall be included in all
// copies or substantial portions of the Software.
//
// THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
// IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
// FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
// AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
// LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
// OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
// SOFTWARE.

uniform mat4 projectionModelViewMatrix;
uniform uint binCount;
uniform float binScale;
uniform float gammaGammaVal = 1.0;
uniform usamplerBuffer histogram;

layout (location = 0) in float binIndex;

void main()
{
    uint binValue = texelFetch(histogram, int(binIndex)).r;
    gl_Position = projectionModelViewMatrix * vec4((float(binIndex) / float(binCount) - 0.5) * 2.0,
//                                                 (log(float(binValue)) / binScale - 0.5) * 2.0,
//                                                 (float(binValue) / binScale - 0.5) * 2.0,
                                                   (pow(float(binValue) / binScale, gammaGammaVal) - 0.5) * 2.0,
                                                   0.4,
                                                   1.0);
}
