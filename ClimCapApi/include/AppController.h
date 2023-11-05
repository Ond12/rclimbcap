#pragma once

#include "myudp.h"
#include "dataProcessing.h"
#include "nidaqmxconnectionthread.h"
#include "globals.h"
#include <QSettings>


class AppController
{

public:

	MyUDP* MyUdpClient;
	DataController* MyDataController;
	NidaqmxConnectionThread* MyNidaqmxConnectionThread;

	uint m_sampleRate;
	int m_totalAcqTimeS;
	bool m_triggerEnable;
	uint m_sampleCalibrationNumber;

	uint m_callbackrate;  //callback every one sample
	uint m_calibrationRate; // in hz
	uint m_calibrationTime; //in seconds
	uint m_calibrationNumberSample;

	AppController()
	{
		this->resetSettings();
		this->readSettings();

		//TO DO SETTINGS SEEMS WRONG

		m_callbackrate = 1;
		m_calibrationRate = 1000;
		m_calibrationTime = 1;
		m_calibrationNumberSample = m_calibrationRate * m_calibrationTime;
	}

	~AppController()
	{
		delete MyUdpClient;
		delete MyDataController;
	}

#pragma region SETTINGS

	void resetSettings()
	{
		QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");
		settings.setValue("acquisition_time", globals::DEFAULT_ACQ_TIME);
		settings.setValue("sample_rate", globals::DEFAULT_SAMPLE_RATE);
		settings.setValue("trigger_enable", globals::DEFAULT_TRIGGER_SETTING);
		settings.setValue("sample_calibration_number", globals::DEFAULT_SAMPLE_CALIBRATION_NUMBER);
	}

	void readSettings()
	{
		QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");

		const auto acquisition_time = settings.value("acquisition_time");

		if (acquisition_time.isNull())
		{
			settings.setValue("acquisition_time", globals::DEFAULT_ACQ_TIME);
			m_totalAcqTimeS = globals::DEFAULT_ACQ_TIME;
		}
		else
			m_totalAcqTimeS = acquisition_time.toInt();

		const auto sample_rate = settings.value("sample_rate");

		if (sample_rate.isNull())
		{
			settings.setValue("sample_rate", globals::DEFAULT_SAMPLE_RATE);
			m_sampleRate = globals::DEFAULT_SAMPLE_RATE;
		}
		else
			m_sampleRate = sample_rate.toInt();

		const auto trigger_enable = settings.value("trigger_enable");
		if (trigger_enable.isNull())
		{
			settings.setValue("trigger_enable", globals::DEFAULT_TRIGGER_SETTING);
			m_triggerEnable = globals::DEFAULT_TRIGGER_SETTING;
		}
		else
			m_triggerEnable = trigger_enable.toBool();


		const auto sample_Calibration_Number = settings.value("sample_calibration_number");
		if (sample_Calibration_Number.isNull())
		{
			settings.setValue("sample_calibration_number", globals::DEFAULT_SAMPLE_CALIBRATION_NUMBER);
			m_sampleCalibrationNumber = globals::DEFAULT_SAMPLE_CALIBRATION_NUMBER;
		}
		else
			m_sampleCalibrationNumber = sample_Calibration_Number.toDouble();

		//qDebug() << "S:trig " << this->triggerEnable << " S:SampleRate " << this->sampleRate  << " S:acQTime " << this->totalAcqTimeS;

	}


#pragma endregion

#pragma region START UP

	bool reloadSensorConfiguration()
	{
		if (MyNidaqmxConnectionThread != nullptr)
		{
			if (MyDataController != nullptr)
			{
				this->readSettings();
				MyNidaqmxConnectionThread->clearTask();

				if (globals::ENABLE_PLATFORM)
				{
					uint NplatformLoaded = MyDataController->loadPlatformToAnalogConfig();
					if (NplatformLoaded == 0) { qCritical() << "Echec dans le chargement de la configuration platformes, vide"; return 0; };

					int totalNumberOfChannels = NplatformLoaded * 8;

					int numberOfSample = m_totalAcqTimeS * m_sampleRate; //used if acquisition have a define time else its infinity

					MyNidaqmxConnectionThread->setUPPlatformTask(m_sampleRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, numberOfSample);
					MyNidaqmxConnectionThread->setUpPlatformCalibrationTask(m_calibrationRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, m_calibrationNumberSample);
				}
				else {
					qDebug() << "Acquisition Plateformes désactivees";
				}

				/////////////////////////////////////////////////////////////////

				if (globals::ENABLE_SENSOR)
				{
					uint NsensorLoaded = MyDataController->loadSensorToAnalogConfig();
					if (NsensorLoaded == 0) { qCritical() << "Echec dans le chargement de la configuration capteur, vide"; return 0; };

					int totalNumberOfChannels = NsensorLoaded * 6;
					int numberOfSample = m_totalAcqTimeS * m_sampleRate;

					MyNidaqmxConnectionThread->setUPTask(m_sampleRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, numberOfSample);
					MyNidaqmxConnectionThread->setUpCalibrationTask(m_calibrationRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, m_calibrationNumberSample);

				}
				else {
					qDebug() << "Acquisition Capteurs désactivees";
				}

			}
			else {
				qCritical() << "DataController nullptr";
				return false;
			}
		}
		else
		{
			qCritical() << "Echec NidaqmxConnectionThread ";
			return false;
		}

		return true;
	}

	bool startUp()
	{
		bool errorFlag = false;

		MyDataController = new DataController();
		MyUdpClient = new MyUDP();

		MyDataController->connectToUdpSteam(MyUdpClient);

		NidaqmxConnectionThread::init(0, 0, 0, 0, 0);
		MyNidaqmxConnectionThread = NidaqmxConnectionThread::GetInstance();

		if (!MyNidaqmxConnectionThread->HasError()) {
			errorFlag = this->reloadSensorConfiguration();
		}
		else {
			qDebug() << "Erreur programme en pause";
			return false;
		}

		if (MyNidaqmxConnectionThread != nullptr)
		{

			QObject::connect(MyNidaqmxConnectionThread, SIGNAL(newDataPacketNi(const DataPacket&)),
				MyDataController, SLOT(processNewDataPacketFromNi(const DataPacket&)));

			QObject::connect(MyNidaqmxConnectionThread, SIGNAL(newDataPacketPlatform(const DataPacket&)),
				MyDataController, SLOT(processNewDataPacketPlatformFromNi(const DataPacket&)));

		}

		return errorFlag;
	};

#pragma endregion

#pragma region TOOLS
	void startAcquisition() const
	{
		if(globals::ENABLE_SENSOR) MyNidaqmxConnectionThread->startSensorAcquisition();
		if(globals::ENABLE_PLATFORM) MyNidaqmxConnectionThread->startPlaformAcquisition();
	};

	void stopAcquisition() const
	{
		if(globals::ENABLE_SENSOR) MyNidaqmxConnectionThread->stopSensorAcquisition();
		if(globals::ENABLE_PLATFORM) MyNidaqmxConnectionThread->stopPlaformAcquisition();
	};

	void startCalibrationTask() const
	{
		if (globals::ENABLE_SENSOR)
		{
			MyNidaqmxConnectionThread->startSensorCalibration();
			MyDataController->calibrate_sensors(m_sampleCalibrationNumber, 1);
		}

		if (globals::ENABLE_PLATFORM)
		{
			MyNidaqmxConnectionThread->startPlaformCalibration();
			MyDataController->calibrate_sensors(m_sampleCalibrationNumber, 2);
		}
	}
#pragma endregion

};

