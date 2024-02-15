#pragma once

#include "myudp.h"
#include "dataProcessing.h"
#include "nidaqmxconnectionthread.h"
#include "globals.h"
#include <QSettings>
#include "dummySender.h"


class AppController
{

public:

	MyUDP* MyUdpClient;
	DataController* MyDataController;
	NidaqmxConnectionThread* MyNidaqmxConnectionThread;

	DummySender* dummySender;

	uint m_sampleRate;
	int m_totalAcqTimeS;
	bool m_triggerEnable;
	uint m_sampleCalibrationNumber;

	bool m_ENABLE_PLATFORM;
	bool m_ENABLE_SENSOR;

	QString m_sensor_card_name;
	QString m_platform_card_name;

	uint m_callbackrate;  //callback every one sample
	uint m_calibrationRate; // in hz
	uint m_calibrationTime; //in seconds
	uint m_calibrationNumberSample;

	AppController()
	{
		MyUdpClient = nullptr;
		MyDataController = nullptr;
		MyNidaqmxConnectionThread = nullptr;

		//this->resetSettings();
		this->readSettings();

		//TO DO SETTINGS SEEMS WRONG

		m_callbackrate = 1;
		m_calibrationRate = 1000;
		m_calibrationTime = 1;
		m_calibrationNumberSample = 1000;

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
		settings.setValue("sensor_card_name", globals::SENSOR_ACQ_CARD_NAME);
		settings.setValue("plat_card_name", globals::PLATFORM_ACQ_CARD_NAME);

		settings.setValue("ENABLE_PLATFORM", globals::ENABLE_PLATFORM);
		settings.setValue("ENABLE_SENSOR", globals::ENABLE_SENSOR);
	}

	void readSettings()
	{
		QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");


		const auto ENABLE_PLATFORM = settings.value("ENABLE_PLATFORM");

		if (ENABLE_PLATFORM.isNull())
		{
			settings.setValue("ENABLE_PLATFORM", globals::ENABLE_PLATFORM);
			m_ENABLE_PLATFORM = globals::ENABLE_PLATFORM;
		}
		else
			m_ENABLE_PLATFORM = ENABLE_PLATFORM.toBool();

		const auto ENABLE_SENSOR = settings.value("ENABLE_SENSOR");

		if (ENABLE_SENSOR.isNull())
		{
			settings.setValue("ENABLE_SENSOR", globals::ENABLE_SENSOR);
			m_ENABLE_SENSOR = globals::ENABLE_SENSOR;
		}
		else
			m_ENABLE_SENSOR = ENABLE_SENSOR.toBool();


		const auto sensor_card_name = settings.value("sensor_card_name");

		if (sensor_card_name.isNull())
		{
			settings.setValue("sensor_card_name", globals::SENSOR_ACQ_CARD_NAME);
			m_sensor_card_name = globals::SENSOR_ACQ_CARD_NAME;
		}
		else
			m_sensor_card_name = sensor_card_name.toString();

		const auto plat_card_name = settings.value("plat_card_name");

		if (plat_card_name.isNull())
		{
			settings.setValue("plat_card_name", globals::PLATFORM_ACQ_CARD_NAME);
			m_platform_card_name = globals::PLATFORM_ACQ_CARD_NAME;
		}
		else
			m_platform_card_name = plat_card_name.toString();

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
		if (MyDataController != nullptr)
		{
			this->readSettings();
			if (MyNidaqmxConnectionThread != nullptr)
			{
				MyNidaqmxConnectionThread->clearTask();

				if (m_ENABLE_PLATFORM)
				{
					uint NplatformLoaded = MyDataController->loadPlatformToAnalogConfig();
					if (NplatformLoaded == 0) { qCritical() << "Echec dans le chargement de la configuration platformes, vide"; return 0; };

					int totalNumberOfChannels = NplatformLoaded * 8;

					int numberOfSample = m_totalAcqTimeS * m_sampleRate; //used if acquisition have a define time else its infinity

					MyNidaqmxConnectionThread->setUPPlatformTask(m_sampleRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, numberOfSample);
					MyNidaqmxConnectionThread->setUpPlatformCalibrationTask(m_calibrationRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, m_calibrationNumberSample);

				}
				else 
				{
					qDebug() << "Acquisition Plateformes désactivees";
				}

				/////////////////////////////////////////////////////////////////

				if (m_ENABLE_SENSOR)
				{
					uint NsensorLoaded = MyDataController->loadSensorToAnalogConfig();
					if (NsensorLoaded == 0) { qCritical() << "Echec dans le chargement de la configuration capteur, vide"; return 0; };

					int totalNumberOfChannels = NsensorLoaded * 6;
					int numberOfSample = m_totalAcqTimeS * m_sampleRate;

					MyNidaqmxConnectionThread->setUPTask(m_sampleRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, numberOfSample);
					MyNidaqmxConnectionThread->setUpCalibrationTask(m_calibrationRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, m_calibrationNumberSample);

				}
				else
				{
					qDebug() << "Acquisition Capteurs désactivees";
				}

				////////////////////////////////////////////////////////////////
			}
			else if (globals::DUMMY_SENDER)
			{
				uint NsensorLoaded = MyDataController->loadSensorToAnalogConfig();
				if (NsensorLoaded == 0) { qCritical() << "Echec dans le chargement de la configuration capteur, vide"; return 0; };

				int totalNumberOfChannelssensor = NsensorLoaded * 6;

				uint NplatformLoaded = MyDataController->loadPlatformToAnalogConfig();

				int totalNumberOfChannelsplat = NplatformLoaded * 8;

				if (dummySender != nullptr)
				{
					dummySender->setNbchan(totalNumberOfChannelssensor);
				}

				qDebug() << "set up dummy sender mode nbchan plat " << totalNumberOfChannelssensor;
			}
			else
			{
				qCritical() << "Echec NidaqmxConnectionThread ";
				return false;
			}
		}
		else
		{
			qCritical() << "DataController nullptr";
			return false;
		}

		return false;
	}

	bool startUp()
	{
		bool errorFlag = false;

		MyDataController = new DataController();
		MyUdpClient = new MyUDP();

		MyDataController->connectToUdpSteam(MyUdpClient);

		if (m_ENABLE_SENSOR || m_ENABLE_PLATFORM)
		{
			NidaqmxConnectionThread::init(0, 0, 0, 0, 0);
			MyNidaqmxConnectionThread = NidaqmxConnectionThread::GetInstance();

			if (!MyNidaqmxConnectionThread->HasError())
			{
				errorFlag = this->reloadSensorConfiguration();
			}

			if (MyNidaqmxConnectionThread != nullptr)
			{
				//sensor card signal
				QObject::connect(MyNidaqmxConnectionThread, SIGNAL(newDataPacketNi(const DataPacket&)),
					MyDataController, SLOT(processNewDataPacketFromNi(const DataPacket&)));

				//platform card signal
				QObject::connect(MyNidaqmxConnectionThread, SIGNAL(newDataPacketPlatform(const DataPacket&)),
					MyDataController, SLOT(processNewDataPacketPlatformFromNi(const DataPacket&)));		

				//calibration signal

				//sensor card calibration signal
				QObject::connect(MyNidaqmxConnectionThread, SIGNAL(newDataPacketNiCalibration(const DataPacket&)),
					MyDataController, SIGNAL(gotNewDataPacket(const DataPacket&)));

				//platform card calibration signal
				QObject::connect(MyNidaqmxConnectionThread, SIGNAL(newDataPacketPlatformCalibration(const DataPacket&)),
					MyDataController, SIGNAL(gotNewDataPacketPlatform(const DataPacket&)));
				
			}
			else 
			{
				qDebug() << "Erreur MyNidaqmxConnectionThread est null programme en pause";
				return false;
			}
		}

		if(globals::DUMMY_SENDER)
		{
			dummySender = new DummySender();
			errorFlag = this->reloadSensorConfiguration();
			qDebug("init dummy senser");
			QObject::connect(dummySender, SIGNAL(newDataPacketNi(const DataPacket&)),
				MyDataController, SLOT(processNewDataPacketFromNi(const DataPacket&)));
			
			//QObject::connect(dummySender, SIGNAL(newDataPacketNi(const DataPacket&)),
			//	MyDataController, SLOT(processNewDataPacketPlatformFromNi(const DataPacket&)));

			
		}

		return errorFlag;
	};

#pragma endregion

#pragma region TOOLS
	void startAcquisition() const
	{
		if(m_ENABLE_SENSOR) MyNidaqmxConnectionThread->startSensorAcquisition();
		if(m_ENABLE_PLATFORM) MyNidaqmxConnectionThread->startPlaformAcquisition();
		if(globals::DUMMY_SENDER) dummySender->start();
		globals::nbpacketsend = 0;
	};

	void stopAcquisition() const
	{
		if(m_ENABLE_SENSOR) MyNidaqmxConnectionThread->stopSensorAcquisition();
		if(m_ENABLE_PLATFORM) MyNidaqmxConnectionThread->stopPlaformAcquisition();
		if(globals::DUMMY_SENDER) dummySender->stop();
		qDebug() << "Paquets : " << globals::nbpacketsend;
	};

	void startCalibrationTask() const
	{
		if (m_ENABLE_SENSOR)
		{
			MyNidaqmxConnectionThread->startSensorCalibration();
			MyDataController->calibrate_sensors(m_sampleCalibrationNumber, 1);
		}

		if (m_ENABLE_PLATFORM)
		{
			MyNidaqmxConnectionThread->startPlaformCalibration();
			MyDataController->calibrate_sensors(m_sampleCalibrationNumber, 2);
		}

		if (globals::DUMMY_SENDER)
		{
			dummySender->start();
			//MyDataController->calibrate_sensors(m_sampleCalibrationNumber, 1);
			MyDataController->calibrate_sensors(m_sampleCalibrationNumber, 2);
		}
	}
#pragma endregion

};

