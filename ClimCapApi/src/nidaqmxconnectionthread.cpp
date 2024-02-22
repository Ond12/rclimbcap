#include "nidaqmxconnectionthread.h"
#include <NIDAQmx.h>
#include <stdio.h>
#include <QDebug>
#include <string>
#include "sensor.h"

#define DAQmxErrChk(functionCall) if( DAQmxFailed(error=(functionCall)) ) goto Error; else

float NidaqmxConnectionThread::m_acqRate = 0;
float NidaqmxConnectionThread::m_callBackRate = 0;
uint NidaqmxConnectionThread::m_numberOfChannels = 0;
uint NidaqmxConnectionThread::m_bufferSize = 0;
bool NidaqmxConnectionThread::m_enableStartTrigger = 0;
uint NidaqmxConnectionThread::m_numberOfSample = 0;

#pragma region CONSTRUCTOR

void parseDevices(char* str)
{
	size_t init_size = strlen(str);
	const char delim[] = ",";

	char* context = nullptr;
	char* token = strtok_s(str, delim, &context);

	while (token != NULL)
	{
		qDebug("%s\n", token);
		token = strtok_s(NULL, delim, &context);
	}

}

NidaqmxConnectionThread* NidaqmxConnectionThread::GetInstance()
{
	return getInstanceImpl(0, 0, 0, 0, 0);
}

NidaqmxConnectionThread* NidaqmxConnectionThread::getInstanceImpl(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample)
{
	static NidaqmxConnectionThread instance{ acquisitionRate, callBackRate, nOfChannels, triggerEnable , numberOfSample };
	return &instance;
}

bool NidaqmxConnectionThread::init(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample)
{
	int32 status;
	int32 stringLength;

	/* get number of characters */
	stringLength = DAQmxGetSysDevNames(NULL, 0);

	if (stringLength < 0)
	{
		/* handle error */
	}
	else
	{
		char* deviceNames = (char*)calloc(stringLength, sizeof(char));
		if (!deviceNames) { /* handle allocation failure */ }

		status = DAQmxGetSysDevNames(deviceNames, stringLength);

		parseDevices(deviceNames);

		if (status < 0) {}

		qDebug("Devices: %s\n", deviceNames);

		free(deviceNames);
	}

	getInstanceImpl(0, 0, 0, 0, 0);
	return true;
}

NidaqmxConnectionThread::~NidaqmxConnectionThread()
{
	delete m_acquisitionTask;
	delete m_calibrationTask;
	delete m_platformAcquisitionTask;
	delete m_platformCalibrationTask;
}

NidaqmxConnectionThread::NidaqmxConnectionThread(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample)
{
	int32       error = 0;
	char        errBuff[2048] = { '\0' };

	this->cardName = globals::SENSOR_ACQ_CARD_NAME;
	this->platformCardName = globals::PLATFORM_ACQ_CARD_NAME;

	DAQmxErrChk(DAQmxResetDevice(this->cardName.toStdString().c_str()));
	DAQmxErrChk(DAQmxResetDevice(this->platformCardName.toStdString().c_str()));

Error:
	if (DAQmxFailed(error)) 
	{
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		qDebug("DAQmx Error: %s\n", errBuff);
		this->errorFlag = true;
	}
}

#pragma endregion

#pragma region SENSOR CARD

int32 CVICALLBACK NidaqmxConnectionThread::EveryNCallback(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData)
{
	DataPacket DP(m_numberOfChannels);

	int32       error = 0;
	char        errBuff[2048] = { '\0' };

	static int  totalRead = 0;
	static int  frameNumber = 0;
	int32       read = 0;
	double* data = new double[m_numberOfChannels];

	DAQmxErrChk(DAQmxReadAnalogF64(taskHandle, NidaqmxConnectionThread::m_callBackRate,
		10, DAQmx_Val_GroupByScanNumber, data, NidaqmxConnectionThread::m_bufferSize, &read, NULL));

	//qDebug() << "Read " << read << "buff size " << NidaqmxConnectionThread::m_bufferSize;
	//if (read > 0) {
		//qDebug("Acquisition de %d echantillons. Total %d\r", (int)read, (int)(totalRead += read));
	//}

	if (globals::DEBUG_MOD_SENSOR)
	{
		double* dummydata = new double[m_numberOfChannels];
		for (uint i = 0; i < ((m_numberOfChannels - 1) / 6); i++)
		{
			dummydata[i * 6] = 1;
			dummydata[i * 6 + 1] = 2;
			dummydata[i * 6 + 2] = 3;
			dummydata[i * 6 + 3] = -10;
			dummydata[i * 6 + 4] = -20;
			dummydata[i * 6 + 5] = -30;
		}
		dummydata[m_numberOfChannels - 1] = 5;

		DataPacket DP2(m_numberOfChannels);

		std::copy(dummydata, dummydata + m_numberOfChannels, std::begin(DP2.dataValues));
		delete[] dummydata;
		//DP2.printDebug();
		emit NidaqmxConnectionThread::GetInstance()->newDataPacketNi(DP2);
	}
	else
	{
		std::copy(data, data + m_numberOfChannels, std::begin(DP.dataValues));
		delete[] data;

		emit NidaqmxConnectionThread::GetInstance()->newDataPacketNi(DP);
	}

Error:
	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		DAQmxStopTask(taskHandle);
		DAQmxClearTask(taskHandle);
		qDebug("DAQmx Error: %s\n", errBuff);
	}

	return 0;
}

int32 CVICALLBACK NidaqmxConnectionThread::EveryNCallbackCalibration(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData)
{
	DataPacket DP(m_numberOfChannels);

	int32       error = 0;
	char        errBuff[2048] = { '\0' };

	static int  totalRead = 0;
	static int  frameNumber = 0;
	int32       read = 0;
	double* data = new double[m_numberOfChannels];

	DAQmxErrChk(DAQmxReadAnalogF64(taskHandle, NidaqmxConnectionThread::m_callBackRate,
		10, DAQmx_Val_GroupByScanNumber, data, NidaqmxConnectionThread::m_bufferSize, &read, NULL));

	if (globals::DEBUG_MOD_SENSOR)
	{
		double* dummydata = new double[m_numberOfChannels];
		for (uint i = 0; i < ((m_numberOfChannels - 1) / 6); i++)
		{
			dummydata[i * 6] = 1;
			dummydata[i * 6 + 1] = 2;
			dummydata[i * 6 + 2] = 3;
			dummydata[i * 6 + 3] = -10;
			dummydata[i * 6 + 4] = -20;
			dummydata[i * 6 + 5] = -30;
		}
		dummydata[m_numberOfChannels - 1] = 5;

		DataPacket DP2(m_numberOfChannels);

		std::copy(dummydata, dummydata + m_numberOfChannels, std::begin(DP2.dataValues));
		delete[] dummydata;
		//DP2.printDebug();
		emit NidaqmxConnectionThread::GetInstance()->newDataPacketNiCalibration(DP2);
	}
	else
	{
		std::copy(data, data + m_numberOfChannels, std::begin(DP.dataValues));
		delete[] data;

		emit NidaqmxConnectionThread::GetInstance()->newDataPacketNiCalibration(DP);
	}

Error:
	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		DAQmxStopTask(taskHandle);
		DAQmxClearTask(taskHandle);
		qDebug("DAQmx Error: %s\n", errBuff);
	}

	return 0;
}

void NidaqmxConnectionThread::setUPTask(float acquisitionRate, float callBackRate, const QVector<Sensor>& sensorList, bool triggerEnable, uint numberOfSample)
{
	int32       error = 0;
	char        errBuff[2048] = { '\0' };

	NidaqmxConnectionThread::m_acqRate = acquisitionRate;
	NidaqmxConnectionThread::m_callBackRate = callBackRate;
	NidaqmxConnectionThread::m_numberOfChannels = 0; // +1 for chrono pulse channel

	NidaqmxConnectionThread::m_enableStartTrigger = triggerEnable;
	NidaqmxConnectionThread::m_numberOfSample = numberOfSample;

	std::string taskname = cardName.toStdString() + "forceAcq";
	m_acquisitionTask = new NIDAQmx::Task(taskname);

	QString channelNamePrefix = this->cardName + "/ai";

	QDebug chd = qDebug();
	chd << "- Initialisation des voies d'acquisition \n";

	for (auto sensor : sensorList)
	{
		uint sensorFisrtChan = sensor.getfirstChannel();
		uint nOfChannels = sensor.getNumberOfChan();
		chd << "Sensor :" << sensor.getSensorId();
		for (uint i = 0; i < nOfChannels; ++i)
		{
			uint currentChanNumber = sensorFisrtChan + i;
			QString channelName = channelNamePrefix + QString::number(currentChanNumber);
			std::string str = channelName.toStdString();
			m_acquisitionTask->AddChannel(str, DAQmx_Val_RSE, -10.0, 10.0);

			NidaqmxConnectionThread::m_numberOfChannels++;
			chd << channelName << " | ";
		}
		chd << "\n";
	}

	//Ajout voie chrono
	QString channelName = channelNamePrefix + QString::number(globals::CHRONO_PULSE_PIN);
	std::string str = channelName.toStdString();
	m_acquisitionTask->AddChannel(str, DAQmx_Val_RSE, -10.0, 10.0);
	chd << "|chrono: " << channelName << " | ";
	NidaqmxConnectionThread::m_numberOfChannels++;

	NidaqmxConnectionThread::m_bufferSize = callBackRate * m_numberOfChannels;

	if (m_enableStartTrigger)
	{
		QString str = '/' + this->cardName + '/' + globals::IMPORT_START_TRIGGER_PIN;
		std::string sstrChannelName = str.toStdString();

		qDebug("Import Trigger enable");

		DAQmxErrChk(DAQmxCfgSampClkTiming(m_acquisitionTask->m_handle, "", acquisitionRate, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, m_numberOfSample));
		DAQmxErrChk(DAQmxCfgDigEdgeStartTrig(m_acquisitionTask->m_handle, sstrChannelName.c_str(), DAQmx_Val_Rising));
	}
	else
	{
		m_acquisitionTask->SetupContinuousAcquisition(acquisitionRate, 1000);
	}

	DAQmxErrChk(DAQmxRegisterEveryNSamplesEvent(m_acquisitionTask->m_handle, DAQmx_Val_Acquired_Into_Buffer, callBackRate, 0, &NidaqmxConnectionThread::EveryNCallback, NULL));
	DAQmxErrChk(DAQmxRegisterDoneEvent(m_acquisitionTask->m_handle, 0, DoneCallback, NULL));

	qDebug() << "Tache d'acquisition initialisee :"
		<< taskname.c_str()
		<< " - Frequence: " << acquisitionRate << " hz"
		<< " - Taille de trame " << callBackRate << " ech "
		<< " - Nb voies: " << NidaqmxConnectionThread::m_numberOfChannels
		<< " - Taille buffer: " << m_bufferSize
		<< " - Trigger: " << m_enableStartTrigger;

Error:

	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		qDebug("DAQmx Error: %s\n", errBuff);
	}

}

void NidaqmxConnectionThread::setUpCalibrationTask(float acquisitionRate, float callBackRate, const QVector<Sensor>& sensorList, bool triggerEnable, uint numberOfSample)
{
	int32       error = 0;
	char        errBuff[2048] = { '\0' };

	std::string taskname = cardName.toStdString() + "calibration";
	m_calibrationTask = new NIDAQmx::Task(taskname);
	QString channelNamePrefix = this->cardName + "/ai";

	uint chancpt = 0;

	for (auto sensor : sensorList)
	{
		uint sensorFisrtChan = sensor.getfirstChannel();
		uint nOfChannels = sensor.getNumberOfChan();

		for (uint i = 0; i < nOfChannels; ++i)
		{
			uint currentChanNumber = sensorFisrtChan + i;
			QString channelName = channelNamePrefix + QString::number(currentChanNumber);
			std::string str = channelName.toStdString();
			m_acquisitionTask->AddChannel(str, DAQmx_Val_RSE, -10.0, 10.0);

			chancpt++;
		}
	}

	DAQmxErrChk(DAQmxCfgSampClkTiming(m_calibrationTask->m_handle, "", acquisitionRate, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, numberOfSample));
	DAQmxErrChk(DAQmxRegisterEveryNSamplesEvent(m_calibrationTask->m_handle, DAQmx_Val_Acquired_Into_Buffer, callBackRate, 0, &NidaqmxConnectionThread::EveryNCallbackCalibration, NULL));
	DAQmxErrChk(DAQmxRegisterDoneEvent(m_calibrationTask->m_handle, 0, DoneCallback, NULL));

	qDebug() << "Tache calibration initialisee :"
		<< taskname.c_str()
		<< " - Frequence: " << acquisitionRate << " hz"
		<< " - Taille de trame " << callBackRate << " ech "
		<< " - Nb voies: " << chancpt;

Error:

	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		qDebug("DAQmx Error: %s\n", errBuff);
	}
}

#pragma endregion

#pragma region PLATFORM CARD
void NidaqmxConnectionThread::setUPPlatformTask(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample)
{
	int32	error = 0;

	QString current_card_name = this->platformCardName;
	auto* current_task = this->m_platformAcquisitionTask;

	std::string taskname = current_card_name.toStdString() + "forceAcq";
	current_task = new NIDAQmx::Task(taskname);
	this->m_platformAcquisitionTask = current_task;

	QString channelNamePrefix = current_card_name + "/ai";

	QDebug chd = qDebug();
	chd << "Initialisation des voies d'acquisition boitier Platformes";
	for (uint i = 0; i < nOfChannels; ++i)
	{
		QString channelName = channelNamePrefix + QString::number(i);
		std::string str = channelName.toStdString();
		current_task->AddChannel(str, DAQmx_Val_RSE, -10.0, 10.0);
		chd << channelName << " | ";
	}

	if (m_enableStartTrigger)
	{
		QString str = '/' + current_card_name + '/' + globals::IMPORT_START_TRIGGER_PIN;
		std::string sstrChannelName = str.toStdString();

		qDebug("Import Trigger enable for platform task");

		DAQmxErrChk(DAQmxCfgSampClkTiming(current_task->m_handle, "", acquisitionRate, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, m_numberOfSample));
		DAQmxErrChk(DAQmxCfgDigEdgeStartTrig(current_task->m_handle, sstrChannelName.c_str(), DAQmx_Val_Rising));
	}
	else
	{
		current_task->SetupContinuousAcquisition(acquisitionRate, 1000);
	}

	DAQmxErrChk(DAQmxRegisterEveryNSamplesEvent(current_task->m_handle, DAQmx_Val_Acquired_Into_Buffer, callBackRate, 0, &NidaqmxConnectionThread::EveryNCallbackPlatform, NULL));
	DAQmxErrChk(DAQmxRegisterDoneEvent(current_task->m_handle, 0, DoneCallback, NULL));

	qDebug() << "Tache d'acquisition PLATFORM initialisee :"
		<< " - Frequence: " << acquisitionRate << " hz"
		<< " - Taille de trame " << callBackRate << " ech "
		<< " - Nb voies: " << nOfChannels
		<< " - Taille buffer: " << m_bufferSize
		<< " - Trigger: " << triggerEnable;

Error:
	if (DAQmxFailed(error)) {

		char        errBuff[2048] = { '\0' };
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		qDebug("DAQmx Error: %s\n", errBuff);
	}
}

void NidaqmxConnectionThread::setUpPlatformCalibrationTask(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample)
{
	int32       error = 0;
	char        errBuff[2048] = { '\0' };

	std::string taskname = this->platformCardName.toStdString() + "calibrationPlatform";
	this->m_platformCalibrationTask = new NIDAQmx::Task(taskname);
	QString channelNamePrefix = this->platformCardName + "/ai";

	for (uint i = 0; i < nOfChannels; ++i)
	{
		QString channelName = channelNamePrefix + QString::number(i);
		std::string str = channelName.toStdString();
		this->m_platformCalibrationTask->AddChannel(str, DAQmx_Val_RSE, -10.0, 10.0);
	}

	DAQmxErrChk(DAQmxCfgSampClkTiming(this->m_platformCalibrationTask->m_handle, "", acquisitionRate, DAQmx_Val_Rising, DAQmx_Val_FiniteSamps, numberOfSample));
	DAQmxErrChk(DAQmxRegisterEveryNSamplesEvent(this->m_platformCalibrationTask->m_handle, DAQmx_Val_Acquired_Into_Buffer, callBackRate, 0, &NidaqmxConnectionThread::EveryNCallbackPlatformCalibration, NULL));
	DAQmxErrChk(DAQmxRegisterDoneEvent(this->m_platformCalibrationTask->m_handle, 0, DoneCallback, NULL));


	qDebug() << "Tache calibration platformes initialisee :"
		<< taskname.c_str()
		<< " - Frequence: " << acquisitionRate << " hz"
		<< " - Taille de trame " << callBackRate << " ech "
		<< " - Nb voies: " << nOfChannels
		<< " - Nb sample: " << numberOfSample;

Error:

	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		qDebug("DAQmx Error: %s\n", errBuff);
	}
}

int32 CVICALLBACK NidaqmxConnectionThread::EveryNCallbackPlatform(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData)
{
	uint numberOfChannels = 16;
	uint bufferSize = NidaqmxConnectionThread::m_callBackRate * numberOfChannels;

	DataPacket DP(numberOfChannels);

	int32       error = 0;
	char        errBuff[2048] = { '\0' };
	static int  totalRead = 0;
	static int  frameNumber = 0;
	int32       read = 0;
	double* data = new double[numberOfChannels];

	DAQmxErrChk(DAQmxReadAnalogF64(taskHandle, NidaqmxConnectionThread::m_callBackRate,
		10, DAQmx_Val_GroupByScanNumber, data, bufferSize, &read, NULL));

	//qDebug() << "Read " << read << "buff size " << NidaqmxConnectionThread::m_bufferSize;
	//if (read > 0) {
		//qDebug("Acquisition de %d echantillons. Total %d\r", (int)read, (int)(totalRead += read));
	//}

	if (globals::DEBUG_MOD_PLATFORM)
	{
		double* dummydata = new double[numberOfChannels];
		
		for (uint i = 0; i < (numberOfChannels / 8); i++)
		{
			dummydata[i * 8] = 10;
			dummydata[i * 8 + 1] = 20;
			dummydata[i * 8 + 2] = 30;
			dummydata[i * 8 + 3] = -40;
			dummydata[i * 8 + 4] = -50;
			dummydata[i * 8 + 5] = -60;
			dummydata[i * 8 + 6] = -70;
			dummydata[i * 8 + 7] = -80;
		}

		DataPacket DP2(numberOfChannels);
		std::copy(dummydata, dummydata + numberOfChannels, std::begin(DP2.dataValues));
		delete[] dummydata;
		//DP2.printDebug();
		emit NidaqmxConnectionThread::GetInstance()->newDataPacketPlatform(DP2);
	}
	else
	{
		std::copy(data, data + numberOfChannels, std::begin(DP.dataValues));
		delete[] data;
		emit NidaqmxConnectionThread::GetInstance()->newDataPacketPlatform(DP);
	}

Error:
	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);

		DAQmxStopTask(taskHandle);
		DAQmxClearTask(taskHandle);
		qDebug("DAQmx Error: %s\n", errBuff);
	}
	return 0;
}

int32 CVICALLBACK NidaqmxConnectionThread::EveryNCallbackPlatformCalibration(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData)
{
	uint numberOfChannels = 16;
	uint bufferSize = NidaqmxConnectionThread::m_callBackRate * numberOfChannels;

	DataPacket DP(numberOfChannels);

	int32       error = 0;
	char        errBuff[2048] = { '\0' };
	static int  totalRead = 0;
	static int  frameNumber = 0;
	int32       read = 0;
	double* data = new double[numberOfChannels];

	DAQmxErrChk(DAQmxReadAnalogF64(taskHandle, NidaqmxConnectionThread::m_callBackRate,
		10, DAQmx_Val_GroupByScanNumber, data, bufferSize, &read, NULL));

	if (globals::DEBUG_MOD_PLATFORM)
	{
		double* dummydata = new double[numberOfChannels];

		for (uint i = 0; i < (numberOfChannels / 8); i++)
		{
			dummydata[i * 8] = 10;
			dummydata[i * 8 + 1] = 20;
			dummydata[i * 8 + 2] = 30;
			dummydata[i * 8 + 3] = -40;
			dummydata[i * 8 + 4] = -50;
			dummydata[i * 8 + 5] = -60;
			dummydata[i * 8 + 6] = -70;
			dummydata[i * 8 + 7] = -80;
		}

		DataPacket DP2(numberOfChannels);
		std::copy(dummydata, dummydata + numberOfChannels, std::begin(DP2.dataValues));
		delete[] dummydata;
		//DP2.printDebug();
		emit NidaqmxConnectionThread::GetInstance()->newDataPacketPlatformCalibration(DP2);
	}
	else
	{
		std::copy(data, data + numberOfChannels, std::begin(DP.dataValues));
		delete[] data;
		emit NidaqmxConnectionThread::GetInstance()->newDataPacketPlatformCalibration(DP);
	}

Error:
	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		DAQmxStopTask(taskHandle);
		DAQmxClearTask(taskHandle);
		qDebug("DAQmx Error: %s\n", errBuff);
	}
	return 0;
}
#pragma endregion

int32 CVICALLBACK NidaqmxConnectionThread::DoneCallback(TaskHandle taskHandle, int32 status, void* callbackData)
{
	int32   error = 0;
	char    errBuff[2048] = { '\0' };
	
	DAQmxErrChk(status);
	DAQmxErrChk(DAQmxStopTask(taskHandle));

Error:
	if (DAQmxFailed(error)) {
		DAQmxGetExtendedErrorInfo(errBuff, 2048);
		DAQmxClearTask(taskHandle);
		qDebug("DAQmx Error: %s\n", errBuff);
	}
	return 0;
}

//______________________________________________________________________________________________
#pragma region TOOLS

bool NidaqmxConnectionThread::HasError() const {
	return this->errorFlag;
}

void NidaqmxConnectionThread::clearTask()
{
	if (m_acquisitionTask != nullptr)
	{
		m_acquisitionTask->Stop();
	}

	if (m_calibrationTask != nullptr)
	{
		m_calibrationTask->Stop();
	}

	if (m_platformAcquisitionTask != nullptr)
	{
		m_platformAcquisitionTask->Stop();
	}

	if (m_platformCalibrationTask != nullptr)
	{
		m_platformCalibrationTask->Stop();
	}

	delete m_acquisitionTask;
	delete m_calibrationTask;

	delete m_platformAcquisitionTask;
	delete m_platformCalibrationTask;
}

void NidaqmxConnectionThread::startSensorAcquisition() const
{
	{
		if (m_acquisitionTask != nullptr) m_acquisitionTask->Start();
		if (m_enableStartTrigger)
		{
			qDebug("En attente de declenchement capteur");
		}
		else
		{
			qDebug("Debut de l'acquisition capteur");
		}
	}
};

void NidaqmxConnectionThread::stopSensorAcquisition() const
{
	if (m_acquisitionTask != nullptr)
	{
		m_acquisitionTask->Stop();
		qDebug("Fin de l'acquisition");
	}
};

void NidaqmxConnectionThread::startSensorCalibration() const
{
	if (m_calibrationTask != nullptr) m_calibrationTask->Start();
}

void NidaqmxConnectionThread::stopSensorCalibration() const
{
	if (m_calibrationTask != nullptr) m_calibrationTask->Stop();
}

//__PLATFORM___________________________________________________________________________

void NidaqmxConnectionThread::startPlaformAcquisition() const
{
	if (m_platformAcquisitionTask != nullptr)
	{
		m_platformAcquisitionTask->Start();
	}	
	if (m_enableStartTrigger)
	{
		qDebug("En attente de declenchement platformes");
	}
	else
	{
		qDebug("Debut de l'acquisition capteur platformes");
	}
}

void NidaqmxConnectionThread::stopPlaformAcquisition() const
{
	if (m_platformAcquisitionTask != nullptr) m_platformAcquisitionTask->Stop();
}

void NidaqmxConnectionThread::startPlaformCalibration() const
{
	if (m_platformCalibrationTask != nullptr) {
		qDebug("Debut de calibration platformes");
		m_platformCalibrationTask->Start();
	}
}

void NidaqmxConnectionThread::stopPlaformCalibration() const
{
	if (m_platformCalibrationTask != nullptr) m_platformCalibrationTask->Stop();
}

#pragma endregion

