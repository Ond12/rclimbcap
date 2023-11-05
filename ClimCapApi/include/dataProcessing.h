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

	QVector<QVector<double>* > m_data;

	uint m_currentSampleNumber;
	uint m_maxSampleNumber;
	uint m_sensorID;
	uint m_sensorStartChannel;

	uint m_channelsNumbers;

public:
	CalibrationWork(uint sensorID, uint sensorStartChannel, uint maxSampleNumber, uint channelsNumbers)
	{
		this->steps = 0;
		this->m_hasEmitResult = false;
		this->m_currentSampleNumber = 0;
		this->m_sensorID = sensorID;
		this->m_sensorStartChannel = sensorStartChannel;
		this->m_maxSampleNumber = maxSampleNumber;
		this->m_channelsNumbers = channelsNumbers;

		timer = new QTimer(this);
		//connect(timer, &QTimer::timeout, this, &CalibrationWork::doHeavyCaclulations);
		//timer->start(500);

		for (int i = 0; i < m_channelsNumbers; ++i) {
			QVector<double>* row = new QVector<double>;
			m_data.push_back(row);
		}
	};

	virtual ~CalibrationWork() 
	{
		qDebug("deleting calibration work");
		for (QVector<double>* row : m_data) {
			delete row;
		}
		delete timer;
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

		for (int i = 0; i < m_channelsNumbers; ++i) {
			m_data[i]->append(d.dataValues[channelIdx + i]);
		}

		steps++;
		emit progress(steps);
		
		if (steps == this->m_maxSampleNumber)
		{
			DataPacket dataPacket(m_channelsNumbers);

			double* analogZeroCorrection = new double[m_channelsNumbers];

			for (int i = 0; i < m_channelsNumbers; ++i) {
				auto curcol = m_data[i];
				analogZeroCorrection[i] = std::accumulate(curcol->begin(), curcol->end(), .0) / curcol->size();
			}

			std::copy(analogZeroCorrection, analogZeroCorrection + m_channelsNumbers, std::begin(dataPacket.dataValues));

			delete[] analogZeroCorrection;

			emit resultReady(m_sensorID, dataPacket);
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
	QVector<Sensor> m_sensorsList;
	QVector<Sensor> m_plaformsList;

	QString m_configFilePath;
	QString m_calibrationFilesPath;

	QStringList m_sensorCalibrationFiles;
	QStringList m_plaformCalibrationFiles;

	QThread workerThread;

	QGenericMatrix<3, 3, double> wallRotMatrix;

	bool applyRotMatrix;
	bool applyOffset;
	bool applyWallRotation;

	void handleResultsAvgZeroPlatform(uint sensorid, const DataPacket& analogZeroCorrection);

	const QGenericMatrix<1, 6, double> ChannelanalogToForce3axisForce(double rawAnalogChannelValues[6], Sensor& sensor, uint matrixOrder);
	
	void clearSensorConfiguration();

public:

	explicit DataController(QObject* parent = nullptr);

	void displaySensor() const;

	Sensor& getPlatform(uint id);
	
	Sensor& getSensor(uint id);

	void calibrate_sensors(uint nbSamples, int mode);
	void createThreadAvgZero(uint sensorID, uint stratChannel, uint nbSamples);

	uint loadPlatformToAnalogConfig();

	bool loadCalibrationMatriceOrdre2PLATFORM(uint sensorNumber, QGenericMatrix<12, 6, double>& matrice);

	uint loadSensorToAnalogConfig();
	void connectToUdpSteam(MyUDP* udps);

	bool loadCalibrationMatriceOrdre2(uint sensorNumber, QGenericMatrix<12, 6, double>& matrice);

	const QGenericMatrix<1, 6, double> PLATFORMChannelanalogToForce3axisForce(double rawAnalogChannelValues[6], Sensor& sensor);

public slots:

	void handleResultsAvgZero(uint, const DataPacket& data);

	void processNewDataPacketFromNi(const DataPacket& data);

	void processNewDataPacketPlatformFromNi(const DataPacket& d);

signals:
	void gotNewDataPacket(const DataPacket& data);
};

