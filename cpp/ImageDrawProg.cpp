#include "Common.h"
#include "ImageDrawProg.h"

ImageDrawProg::ImageDrawProg(QObject* parent)
  : GlslProg(parent),
    m_quadVao(new QOpenGLVertexArrayObject(this)),
    m_quadVaoBuff(QOpenGLBuffer::VertexBuffer),
    m_pmvLoc(std::numeric_limits<int>::min()),
    m_fragToTexLoc(std::numeric_limits<int>::min())
{
    // Note Qt interprets a path beginning with a colon as a Qt resource bundle identifier.  Such a path refers to an
    // object integrated into this application's binary.
    addShader(":/gpu/image.glslv", QOpenGLShader::Vertex);
    addShader(":/gpu/image.glslf", QOpenGLShader::Fragment);
}

ImageDrawProg::~ImageDrawProg()
{
}

void ImageDrawProg::init(QOpenGLFunctions_4_1_Core* glfs)
{
    if(!m_quadVao->create())
    {
        throw RisWidgetException("ImageDrawProg::ImageDrawProg(..): Failed to create m_quadVao.");
    }
    QOpenGLVertexArrayObject::Binder quadVaoBinder(m_quadVao);

    float quad[] = {
        // Vertex positions
        1.1f, -1.1f,
        -1.1f, -1.1f,
        -1.1f, 1.1f,
        1.1f, 1.1f
    };

    m_quadVaoBuff.create();
    m_quadVaoBuff.bind();
    m_quadVaoBuff.setUsagePattern(QOpenGLBuffer::StaticDraw);
    m_quadVaoBuff.allocate(reinterpret_cast<void*>(quad), sizeof(quad));

    glfs->glEnableVertexAttribArray(VertCoordLoc);
    glfs->glVertexAttribPointer(VertCoordLoc, 2, GL_FLOAT, false, 0, nullptr);

    const_cast<int&>(m_pmvLoc) = uniformLocation("projectionModelViewMatrix");
    const_cast<int&>(m_fragToTexLoc) = uniformLocation("fragToTex");
}
