#pragma once

#include <Qvector>
#include <QGenericMatrix>
#include <QObject>
#include <QDebug>
#include <QByteArray>
#include <QThread>
#include <algorithm>
#include <QMap>
#include <QProgressDialog>
#include <QTimer>
#include <iostream>

#include "dataPacket.h"
#include "sensor.h"
#include "myudp.h"

class CalibrationWork : public QObject
{
	Q_OBJECT
	QTimer* timer;
	uint steps;
	bool m_hasEmitResult;

	QVector<double> vch1;
	QVector<double> vch2;
	QVector<double> vch3;
	QVector<double> vch4;
	QVector<double> vch5;
	QVector<double> vch6;

	uint m_currentSampleNumber;
	uint m_maxSampleNumber;
	uint m_sensorID;
	uint m_sensorStartChannel;

public:
	CalibrationWork(uint sensorID, uint sensorStartChannel, uint maxSampleNumber)
	{
		this->steps = 0;
		this->m_hasEmitResult = false;
		this->m_currentSampleNumber = 0;
		this->m_sensorID = sensorID;
		this->m_sensorStartChannel = sensorStartChannel;
		this->m_maxSampleNumber = maxSampleNumber;

		timer = new QTimer(this);
		//connect(timer, &QTimer::timeout, this, &CalibrationWork::doHeavyCaclulations);
		timer->start(500);
	};

	virtual ~CalibrationWork() 
	{
		qDebug("deleting calibration work");
	};

public slots:

	void starting()
	{
		qDebug() << "Start Calibration";
	}

	void getNewAnalogData(const DataPacket& d)
	{ 
		qDebug() << "work s:"<< m_sensorID << " at " << this->steps << "/" << this->m_maxSampleNumber;

		uint channelIdx = (this->m_sensorStartChannel);

		this->vch1.append(d.dataValues[ channelIdx ] );
		this->vch2.append(d.dataValues[ channelIdx + 1] );
		this->vch3.append(d.dataValues[ channelIdx + 2] );
		this->vch4.append(d.dataValues[ channelIdx + 3] );
		this->vch5.append(d.dataValues[ channelIdx + 4] );
		this->vch6.append(d.dataValues[ channelIdx + 5] );

		steps++;
		emit progress(steps);
		
		if (steps == this->m_maxSampleNumber)
		{
			DataPacket dataPacket(6);

			float analogZeroCorrection[6] = { 0, 0, 0, 0, 0, 0 };

			analogZeroCorrection[0] = std::accumulate(vch1.begin(), vch1.end(), .0) / vch1.size();
			analogZeroCorrection[1] = std::accumulate(vch2.begin(), vch2.end(), .0) / vch2.size();
			analogZeroCorrection[2] = std::accumulate(vch3.begin(), vch3.end(), .0) / vch3.size();
			analogZeroCorrection[3] = std::accumulate(vch4.begin(), vch4.end(), .0) / vch4.size();
			analogZeroCorrection[4] = std::accumulate(vch5.begin(), vch5.end(), .0) / vch5.size();
			analogZeroCorrection[5] = std::accumulate(vch6.begin(), vch6.end(), .0) / vch6.size();

			std::copy(analogZeroCorrection, analogZeroCorrection + 6, std::begin(dataPacket.dataValues));

			emit resultReady(this->m_sensorID, dataPacket);
			m_hasEmitResult = true;
		}
		
		if (m_hasEmitResult) {
			emit finished();
		}

	};

signals:

	void progress(int);
	void finished();
	void resultReady(uint, const DataPacket& data);
	void error(QString err);
};

class DataController : public QObject
{
	Q_OBJECT

private:

	MyUDP* udpClient;
	QVector<Sensor> sensors;
	QVector<Sensor> plaforms;

	QThread workerThread;

	QGenericMatrix<3, 3, double> wallRotMatrix;


	bool applyRotMatrix;
	bool applyOffset;
	bool applyWallRotation;

	const QGenericMatrix<1, 6, double> ChannelanalogToForce3axisForce(double rawAnalogChannelValues[6], Sensor& sensor, uint matrixOrder);
	
	void clearSensorConfiguration();

public:

	explicit DataController(QObject* parent = nullptr);

	void displaySensor();
	void Calibrate_Sensors(uint nbSamples);
	
	Sensor& getSensor(uint id);
	void createThreadAvgZero(uint sensorID, uint stratChannel, uint nbSamples);

	uint loadSensorToAnalogConfig();
	void connectToUdpSteam(MyUDP* udps);

	bool loadCalibrationMatriceOrdre2(uint sensorNumber, QGenericMatrix<12, 6, double>& matrice);
	bool loadCalibrationMatriceOrdre1(uint sensorNumber, QGenericMatrix<6,  6, double>& matrice);

	const QGenericMatrix<1, 6, double> PLATFORMChannelanalogToForce3axisForce(double rawAnalogChannelValues[6], Sensor& sensor);

public slots:

	void handleResultsAvgZero(uint, const DataPacket& data);

	void processNewDataPacket(const DataPacket& data);
	void processNewDataPacketFromNi(const DataPacket& data);
	void processNewDataPacketPlatformFromNi(const DataPacket& d);

signals:
	void gotNewDataPacket(const DataPacket& data);
};

