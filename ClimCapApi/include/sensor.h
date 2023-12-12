#pragma once

#include <QDebug>
#include <QGenericMatrix>
#include "dataPacket.h"
#include <cmath>

struct DataPoint
{
	double val;
	double key;
};

template <int channelNumber>
class SensorG
{
private:
    uint sensorId;
    uint firstChannelId;

    uint m_channelNumber;

    double angle;
    double wallAngle;
    double Zangle;

    bool m_isFlip;

    QGenericMatrix<channelNumber * 2, 6, double> calibrationMatriceOrdre2;

    QGenericMatrix<3, 3, double> rotationMatrice;
    QGenericMatrix<3, 3, double> wallRotMatrix;

    double m_channelCalibrationValues[channelNumber];

public:

    SensorG(uint id, uint firstChannelId, double angle)
    {
        this->setRotationAngle(angle, 'y');
        this->Zangle = 0;
        this->firstChannelId = firstChannelId;
        this->m_channelNumber = channelNumber;
        this->sensorId = id;
        this->resetCalibrationValues();
    }

    #pragma region matrice

    void setRotationAngle(double angle, char axis)
    {
        constexpr int N = 3;

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

    void setFlip(bool isFlip)
    {
        m_isFlip = isFlip;
    }

    #pragma endregion

    #pragma region getter

    uint getSensorId() const
    {
        return this->sensorId;
    }

    uint getNumberOfChan() const
    {
        return this->m_channelNumber;
    }
 
    const QGenericMatrix<channelNumber*2, 6, double>& getCalibrationMatriceO2() const
    {
        return this->calibrationMatriceOrdre2;
    }

    const QGenericMatrix<3, 3, double>& getRotationMatrix() const
    {
        return this->rotationMatrice;
    }

    uint getfirstChannel() const
    {
        return this->firstChannelId;
    }

    bool getFlip() const
    {
        return m_isFlip;
    }

    const double* getChannelCalibrationValuesArr() const
    {
        return this->m_channelCalibrationValues;
    }

    #pragma endregion

    const QGenericMatrix<1, 6, double> ChannelanalogToForce3axisForce(double rawAnalogChannelValues[ channelNumber ])
    {
        double* analogDataSquared = new double[m_channelNumber * 2];

        //array is first all analog data then following all analog data squared
        // ex nchan = 3   rawdata = [1,2,3]   analogDataSquare = [1,2,3,1,4,9]

        for (uint i = 0; i < m_channelNumber; i++) analogDataSquared[i] = rawAnalogChannelValues[i];
        for (uint i = 0; i < m_channelNumber; i++) analogDataSquared[i + m_channelNumber] = rawAnalogChannelValues[i] * rawAnalogChannelValues[i];

        QGenericMatrix<1, channelNumber * 2, double> analogValuesSquare(analogDataSquared);
        QGenericMatrix<1, 6, double> result = this->getCalibrationMatriceO2() * analogValuesSquare;


        delete[] analogDataSquared;

        return result;
    }

    void resetCalibrationValues()
    {
        for (uint i = 0; i < this->m_channelNumber; ++i)
        {
            this->m_channelCalibrationValues[i] = .0f;
        }
    }

    void setChannelCalibrationValues(double* calibrationValues)
    {
        for (uint i = 0; i < this->m_channelNumber; ++i)
        {
            this->m_channelCalibrationValues[i] = calibrationValues[i];
        }
    }

    void setCalibrationMatriceO2(QGenericMatrix<channelNumber * 2, 6, double>& calibrationMatriceOrdre2)
    {
        this->calibrationMatriceOrdre2 = calibrationMatriceOrdre2;
    }

    void toString(bool showCalMat) const
    {
        qDebug() << "___";
        qDebug() << "Sensor :" << this->sensorId << " adr :" << this << "number of chan :" << this->m_channelNumber;

        if (showCalMat)
        {
            qDebug() << "Cal mat " << this->calibrationMatriceOrdre2;
            qDebug() << "Angle: " << this->angle << " deg";
            qDebug() << "Zrotation: " << this->Zangle << " deg";
            qDebug() << this->rotationMatrice;
        }

        qDebug() << "___";
    }

};

typedef SensorG<6> Sensor;
typedef SensorG<8> Platform;

typedef QGenericMatrix<16, 6, double> PlaformMatrice;
typedef QGenericMatrix<12, 6, double> SensorMatrice; 