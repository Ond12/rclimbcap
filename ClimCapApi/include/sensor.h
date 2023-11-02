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

	uint channelNumber;

	double angle;
	double wallAngle;
	double Zangle;  

	QGenericMatrix<6, 6, double> calibrationMatriceOrdre1;
	QGenericMatrix<12, 6, double> calibrationMatriceOrdre2;

	QGenericMatrix<12, 6, double> platformCalibrationMatriceOrdre2;

	QGenericMatrix<3, 3, double> rotationMatrice;

	//to do convert this
	double channelCalibrationValues[6];

	std::vector<DataPoint> m_datax;
	std::vector<DataPoint> m_datay;
	std::vector<DataPoint> m_dataz;

public:
	Sensor(uint id, uint firstChannelId, double angle);

	void setCalibrationMatriceO1(QGenericMatrix<6, 6, double>& calibrationMatriceOrdre1);
	void setCalibrationMatriceO2(QGenericMatrix<12, 6, double>& calibrationMatriceOrdre2);

	void addData(double key, double val, char axis);
	void pushDataForceMoment(const DataPacket& forceMomentData);

	QGenericMatrix<6, 6,  double> getCalibrationMatriceO1() const;
	const QGenericMatrix<12, 6, double>& getCalibrationMatriceO2() const;
	const QGenericMatrix<3, 3, double>& getRotationMatrix() const;
	
	uint getfirstChannel() const;
	void setRotationAngle(double angle, char axis);

	void setChannelCalibrationValues(double calibrationValues[6]);

	const double* getChannelCalibrationValuesArr() const;
	void resetCalibrationValues();


	uint getSensorId() const;
	void toString(bool showCalMat) const;


	const QGenericMatrix<12, 6, double>& getCalibrationMatriceO2PLATFORM() const;
	void setCalibrationMatriceO2PLATFORM(QGenericMatrix<12, 6, double>& calibrationMatriceOrdre2);
};