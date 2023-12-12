#pragma once

#include <QDebug>
#include <QGenericMatrix>
#include "dataPacket.h"

struct DataPoint
{
	double val;
	double key;
};

class Sensor
{
private:
	uint sensorId;
	uint firstChannelId;

	uint m_channelNumber;

	double angle;
	double wallAngle;
	double Zangle;  

	bool m_isFlip;

	QGenericMatrix<6, 6, double> calibrationMatriceOrdre1;
	QGenericMatrix<12, 6, double> calibrationMatriceOrdre2;

	QGenericMatrix<12, 6, double> platformCalibrationMatriceOrdre2;

	QGenericMatrix<3, 3, double> rotationMatrice;
	QGenericMatrix<3, 3, double> wallRotMatrix;

	//to do convert this
	double m_channelCalibrationValues[6];

	std::vector<DataPoint> m_datax;
	std::vector<DataPoint> m_datay;
	std::vector<DataPoint> m_dataz;

public:
	Sensor(uint id, uint firstChannelId, double angle);

	void setCalibrationMatriceO2(QGenericMatrix<12, 6, double>& calibrationMatriceOrdre2);

	void addData(double key, double val, char axis);
	void pushDataForceMoment(const DataPacket& forceMomentData);

	const QGenericMatrix<12, 6, double>& getCalibrationMatriceO2() const;
	const QGenericMatrix<3, 3, double>& getRotationMatrix() const;
	
	uint getfirstChannel() const;
	void setChannelCalibrationValues(double* calibrationValues);
	void setRotationAngle(double angle, char axis);
	void setFlip(bool isFlip);

	const double* getChannelCalibrationValuesArr() const;
	const QGenericMatrix<1, 6, double> ChannelanalogToForce3axisForce(double rawAnalogChannelValues[6]);
	void resetCalibrationValues();

	uint getSensorId() const;
	uint getNumberOfChan() const;
	bool getFlip() const;
	void toString(bool showCalMat) const;

	const QGenericMatrix<12, 6, double>& getCalibrationMatriceO2PLATFORM() const;
	void setCalibrationMatriceO2PLATFORM(QGenericMatrix<12, 6, double>& calibrationMatriceOrdre2);
};