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
	QTimer* m_timer;

	uint m_steps;
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
		this->m_steps = 0;
		this->m_hasEmitResult = false;
		this->m_currentSampleNumber = 0;
		this->m_sensorID = sensorID;
		this->m_sensorStartChannel = sensorStartChannel;
		this->m_maxSampleNumber = maxSampleNumber;
		this->m_channelsNumbers = channelsNumbers;

		m_timer = new QTimer(this);
		//connect(m_timer, &QTimer::timeout, this, &CalibrationWork::doHeavyCaclulations);
		//m_timer->start(500);

		for (uint i = 0; i < m_channelsNumbers; ++i) {
			QVector<double>* row = new QVector<double>;
			m_data.push_back(row);
		}
	};

	virtual ~CalibrationWork() 
	{
		//qDebug("deleting calibration work");
		for (QVector<double>* row : m_data) {
			delete row;
		}
		delete m_timer;
	};

public slots:

	void starting()
	{
		qDebug() << "Start Calibration";
		qDebug() << "work s:" << m_sensorID << " / nbchannel " << m_channelsNumbers;
	}

	void getNewAnalogData(const DataPacket& d)
	{ 
		qDebug() << "work s:"<< m_sensorID << " at " << this->m_steps << "/" << this->m_maxSampleNumber << " / nbchannel " << m_channelsNumbers;

		uint channelIdx = (this->m_sensorStartChannel);

		for (uint i = 0; i < m_channelsNumbers; ++i) {
			m_data[i]->append(d.dataValues[ channelIdx + i ]);
		}

		m_steps++;
		emit progress(m_steps);
		
		if (m_steps == this->m_maxSampleNumber)
		{
			DataPacket dataPacket(m_channelsNumbers);

			double* analogZeroCorrection = new double[m_channelsNumbers];

			for (uint i = 0; i < m_channelsNumbers; ++i) {
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

	const MyUDP* udpClient;

	QVector<Sensor> m_sensorsList;
	QVector<Platform> m_plaformsList;

	QString m_configFilePath;
	QString m_calibrationFilesPath;

	QStringList m_sensorCalibrationFiles;
	QStringList m_plaformCalibrationFiles;

	QGenericMatrix<3, 3, double> wallRotMatrix;

	bool applyRotMatrix;
	bool applyOffset;
	bool applyWallRotation;
	
	void clearSensorConfiguration();

public:

	explicit DataController(QObject* parent = nullptr);

	void displaySensor() const;

	Platform& getPlatform(uint id);
	Sensor& getSensor(uint id);

	void calibrate_sensors(uint nbSamples, int mode);
	void createThreadAvgZero(uint sensorID, uint sensorStartChannel, uint nbSamples, uint channelsNumber);

	uint loadPlatformToAnalogConfig();
	uint loadSensorToAnalogConfig();

	bool loadCalibrationMatriceOrdre2(uint sensorNumber, SensorMatrice& matrice);

	bool loadCalibrationMatriceOrdre2PLATFORM(uint sensorNumber, PlaformMatrice& matrice);

	void connectToUdpSteam(const MyUDP* udps);

public slots:

	void handleResultsAvgZero(uint, const DataPacket& data);
	void handleResultsAvgZeroPlatform(uint sensorid, const DataPacket& analogZeroCorrection);

	void processNewDataPacketFromNi(const DataPacket& data);
	void processNewDataPacketPlatformFromNi(const DataPacket& d);

signals:
	void gotNewDataPacket(const DataPacket& data);
	void gotNewDataPacketPlatform(const DataPacket& data);
};

