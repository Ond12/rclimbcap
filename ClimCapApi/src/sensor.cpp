#include "sensor.h"
#include "QTime"
#include "dataPacket.h"
#include <cmath>

Sensor::Sensor(uint id, uint firstChannelId, double angle)
{
    this->setRotationAngle(angle, 'y');
    this->Zangle = 0;
    this->firstChannelId = firstChannelId;
    this->sensorId = id;
    this->m_datax = std::vector<DataPoint>();
    this->m_datay = std::vector<DataPoint>();
    this->m_dataz = std::vector<DataPoint>();
    this->resetCalibrationValues();
}

#pragma region matrice

void Sensor::setRotationAngle(double angle, char axis)
{
    constexpr int N = 3;

    this->m_channelNumber = 6;

    double theta = (180 - angle) * M_PI / 180.0;

    // Calcul de la matrice de rotation
    double cos_theta = cos(theta);
    double sin_theta = sin(theta);

    double rot_matrix_z[N * N] =
    {
     cos_theta , -sin_theta, 0,
     sin_theta , cos_theta, 0,
     0 , 0, 1
    };

    double rot_matrix_y[N * N] =
    {
     cos_theta , 0, sin_theta,
     0,1,0,
     -sin_theta, 0, cos_theta
    };

    QGenericMatrix<3, 3, double> tprotationMatrice;

    if (axis == 'z')
    {
        // rotation autour du vecteur unitaire (z)
        QGenericMatrix<3, 3, double> tprotationMatrice(rot_matrix_z);
        this->Zangle = angle;
        this->rotationMatrice = this->rotationMatrice * tprotationMatrice;
    }
    else
    {
        // rotation autour du vecteur unitaire (y)
        QGenericMatrix<3, 3, double> tprotationMatrice(rot_matrix_y);
        this->angle = angle;
        this->rotationMatrice = this->rotationMatrice * tprotationMatrice;
    }
}

void Sensor::setFlip(bool isFlip)
{
    m_isFlip = isFlip;
}


#pragma endregion

#pragma region getter

uint Sensor::getSensorId() const
{
    return this->sensorId;
}

uint Sensor::getNumberOfChan() const
{
    return m_channelNumber;
}

const QGenericMatrix<12, 6, double>& Sensor::getCalibrationMatriceO2PLATFORM() const
{
    return platformCalibrationMatriceOrdre2;
}

const QGenericMatrix<12, 6, double>& Sensor::getCalibrationMatriceO2() const
{
    return this->calibrationMatriceOrdre2;
}

const QGenericMatrix<3, 3, double>& Sensor::getRotationMatrix() const
{
    return this->rotationMatrice;
}

uint Sensor::getfirstChannel() const
{
    return this->firstChannelId;
}


const double* Sensor::getChannelCalibrationValuesArr() const
{
    return this->m_channelCalibrationValues;
}


#pragma endregion

#pragma region data

void Sensor::pushDataForceMoment(const DataPacket& forceMomentData)
{
    double key = forceMomentData.timeKey;

    m_datax.push_back(DataPoint{ key, forceMomentData.dataValues.at(0) });
    m_datay.push_back(DataPoint{ key, forceMomentData.dataValues.at(1) });
    m_dataz.push_back(DataPoint{ key, forceMomentData.dataValues.at(2) });
}

void Sensor::addData(double key, double val, char axis)
{
    switch (axis)
    {
    case 'x':
        this->m_datax.push_back(DataPoint{ key, val });
        break;
    case 'y':
        this->m_datay.push_back(DataPoint{ key, val });
        break;
    case 'z':
        this->m_dataz.push_back(DataPoint{ key, val });
        break;
    default:
        break;
    }
}

#pragma endregion


const QGenericMatrix<1, 6, double> Sensor::ChannelanalogToForce3axisForce(double rawAnalogChannelValues[6])
{
    double*  analogDataSquared = new double [m_channelNumber * 2];

    //array is first all analog data then following all analog data squared
    // ex nchan = 3   rawdata = [1,2,3]   analogDataSquare = [1,2,3,1,4,9]

    for (uint i = 0; i < m_channelNumber; i++) analogDataSquared[i] = rawAnalogChannelValues[i];
    for (uint i = 0; i < m_channelNumber; i++) analogDataSquared[i + m_channelNumber] = rawAnalogChannelValues[i] * rawAnalogChannelValues[i];

    QGenericMatrix<1, 12, double> analogValuesSquare(analogDataSquared);
    QGenericMatrix<1, 6, double> result = this->getCalibrationMatriceO2() * analogValuesSquare;


    delete[] analogDataSquared;

    return result;
}

void Sensor::resetCalibrationValues()
{
    for (uint i = 0; i < this->m_channelNumber; ++i)
    {
        this->m_channelCalibrationValues[i] = .0f;
    }
}

void Sensor::setChannelCalibrationValues(double* calibrationValues)
{
    for (uint i = 0; i < this->m_channelNumber; ++i)
    {
        this->m_channelCalibrationValues[i] = calibrationValues[i];
    }
}

void Sensor::setCalibrationMatriceO2(QGenericMatrix<12, 6, double>& calibrationMatriceOrdre2)
{
    this->calibrationMatriceOrdre2 = calibrationMatriceOrdre2;
}

void Sensor::setCalibrationMatriceO2PLATFORM(QGenericMatrix<12, 6, double>& calibrationMatriceOrdre2)
{
    this->platformCalibrationMatriceOrdre2 = calibrationMatriceOrdre2;
}


void Sensor::toString(bool showCalMat) const
{
    qDebug() << "___";
    qDebug() << "Sensor :" << this->sensorId << " adr :" << this;

    if (showCalMat)
    {
        qDebug() << "Cal mat " << this->calibrationMatriceOrdre1;
        qDebug() << "Angle: " << this->angle << " deg";
        qDebug() << "Zrotation: " << this->Zangle << " deg";
        qDebug() << this->rotationMatrice;
    }

    qDebug() << "___";
}

bool Sensor::getFlip() const
{
    return m_isFlip;
}
