#pragma once
#include "myudp.h"
#include "dataProcessing.h"
#include "nidaqmxconnectionthread.h"
#include <QSettings>

#define DEFAULT_SAMPLE_RATE 200
#define DEFAULT_ACQ_TIME 200
#define NB_CHAN_PER_SENSOR 6
#define DEFAULT_TRIGGER_SETTING 0
#define DEFAULT_SAMPLE_CALIBRATION_NUMBER 1000

#define ENABLE_PLATFORM true
#define ENABLE_SENSOR true

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

	uint m_callbackrate = 1;  //callback every one sample
	uint m_calibrationRate = 1000; // in hz
	uint m_calibrationTime = 1; //in seconds
	uint m_calibrationNumberSample;
	
	AppController() 
	{
		this->resetSettings();
		this->readSettings();

		m_callbackrate = 1; 
		m_calibrationRate = 1000; 
		m_calibrationTime = 1; 
		m_calibrationNumberSample = m_calibrationRate * m_calibrationTime;
	}

	void resetSettings()
	{
		QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");
		settings.setValue("acquisition_time", DEFAULT_ACQ_TIME);
		settings.setValue("sample_rate", DEFAULT_SAMPLE_RATE);
		settings.setValue("trigger_enable", DEFAULT_TRIGGER_SETTING);
		settings.setValue("sample_calibration_number", DEFAULT_SAMPLE_CALIBRATION_NUMBER);
	}

	void readSettings()
	{
		QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");

		const auto acquisition_time = settings.value("acquisition_time");

		if (acquisition_time.isNull())
		{
			settings.setValue("acquisition_time", DEFAULT_ACQ_TIME);
			m_totalAcqTimeS = DEFAULT_ACQ_TIME;
		}
		else
			m_totalAcqTimeS = acquisition_time.toInt();

		const auto sample_rate = settings.value("sample_rate");

		if (sample_rate.isNull())
		{
			settings.setValue("sample_rate", DEFAULT_SAMPLE_RATE);
			m_sampleRate = DEFAULT_SAMPLE_RATE;
		}
		else
			m_sampleRate = sample_rate.toInt();
		
		const auto trigger_enable = settings.value("trigger_enable");
		if (trigger_enable.isNull())
		{
			settings.setValue("trigger_enable", DEFAULT_TRIGGER_SETTING);
			m_triggerEnable = DEFAULT_TRIGGER_SETTING;
		}
		else
			m_triggerEnable = trigger_enable.toBool();


		const auto sample_Calibration_Number = settings.value("sample_calibration_number");
		if (sample_Calibration_Number.isNull())
		{
			settings.setValue("sample_calibration_number", DEFAULT_SAMPLE_CALIBRATION_NUMBER);
			m_sampleCalibrationNumber = DEFAULT_SAMPLE_CALIBRATION_NUMBER;
		}
		else
			m_sampleCalibrationNumber = sample_Calibration_Number.toDouble();

		//qDebug() << "S:trig " << this->triggerEnable << " S:SampleRate " << this->sampleRate  << " S:acQTime " << this->totalAcqTimeS;

	}

	bool reloadSensorConfiguration()
	{
		if (MyNidaqmxConnectionThread != nullptr)
		{
			if (MyDataController != nullptr)
			{
				this->readSettings();
				MyNidaqmxConnectionThread->clearTask();



				if (ENABLE_PLATFORM)
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


				if (ENABLE_SENSOR)
				{
					uint NsensorLoaded = MyDataController->loadSensorToAnalogConfig();
					if (NsensorLoaded == 0) { qCritical() << "Echec dans le chargement de la configuration capteur, vide"; return 0; };

					int totalNumberOfChannels = NsensorLoaded * NB_CHAN_PER_SENSOR;
					int numberOfSample = m_totalAcqTimeS * m_sampleRate;

					MyNidaqmxConnectionThread->setUPTask(m_sampleRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, numberOfSample);
					MyNidaqmxConnectionThread->setUpCalibrationTask(m_calibrationRate, m_callbackrate, totalNumberOfChannels, m_triggerEnable, m_calibrationNumberSample);

				}
				else {
					qDebug() << "Acquisition Capteurs désactivees";
				}

			}
			else {

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
		MyDataController = new DataController();
		uint NsensorLoaded = MyDataController->loadSensorToAnalogConfig();
		if ( NsensorLoaded == 0 ) { qCritical() << "Echec dans le chargement de la configuration capteur"; return 0; };

		int totalNumberOfChannels = NsensorLoaded * NB_CHAN_PER_SENSOR;
		int numberOfSample = m_totalAcqTimeS * m_sampleRate;

		NidaqmxConnectionThread::init(m_sampleRate, 1, totalNumberOfChannels, m_triggerEnable, numberOfSample);
	    this->MyNidaqmxConnectionThread = NidaqmxConnectionThread::GetInstance();

		QObject::connect(this->MyNidaqmxConnectionThread, SIGNAL(newDataPacketNi(const DataPacket&)),
			this->MyDataController, SLOT(processNewDataPacketFromNi(const DataPacket&)));

		QObject::connect(this->MyNidaqmxConnectionThread, SIGNAL(newDataPacketPlatform(const DataPacket&)),
			this->MyDataController, SLOT(processNewDataPacketPlatformFromNi(const DataPacket&)));


		MyUdpClient = new MyUDP();

		MyDataController->connectToUdpSteam(MyUdpClient);

		return true;
	};

	void startAcquisition() const 
	{
		MyNidaqmxConnectionThread->startAcquisition();
	};

	void stopAcquisition() const 
	{
		MyNidaqmxConnectionThread->stopAcquisition();
	};

};

