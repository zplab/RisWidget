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

#version 430 core

struct GammaTransformParams
{
    float minVal;
    float maxVal;
    float gammaVal;
};

uniform GammaTransformParams gtp = GammaTransformParams(0.0, 65535.0, 1.0);
uniform usampler2D tex;

// From vertex shader
in vec2 vsTexCoord;

layout (location = 0) out vec4 fsColor;

subroutine void PanelColorer();

subroutine (PanelColorer) void imagePanelGammaTransformColorer()
{
    float intensity = texture(tex, vsTexCoord).r;
    if(intensity <= gtp.minVal)
    {
        fsColor = vec4(0, 0, 1, 1);
    }
    else if(intensity >= gtp.maxVal)
    {
        fsColor = vec4(1, 0, 0, 1);
    }
    else
    {
        float scaled = pow(clamp((intensity - gtp.minVal) / (gtp.maxVal - gtp.minVal), 0.0, 1.0), gtp.gammaVal);
        fsColor = vec4(scaled, scaled, scaled, 1.0);
    }
}

subroutine (PanelColorer) void imagePanelPassthroughColorer()
{
    fsColor = vec4(vec3(texture(tex, vsTexCoord).rrr) / 65535.0, 1);
}

subroutine (PanelColorer) void histogramPanelColorer()
{
    fsColor = vec4(0, 0, 0, 1);
}

subroutine uniform PanelColorer panelColorer;

void main()
{
    panelColorer();
}
