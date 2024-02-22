#ifndef NIDAQMXCONNECTIONTHREAD_H
#define NIDAQMXCONNECTIONTHREAD_H

#include <QThread>
#include <QObject>
#include <QTimer>

#include <NIDAQmx.h>
#include "globals.h"
#include "sensor.h"
#include "dataPacket.h"

namespace NIDAQmx
{
    class DAQException : public std::exception
    {
        const int32 m_code;

        DAQException& operator=(const DAQException&);
    public:
        DAQException(int32 errorCode)
            : exception("exception in NI-DAQmx library")
            , m_code(errorCode)
        {
        }

        int code() const { return m_code; }
        std::string description() const
        {
            std::string buffer;
            int32 neededSize = DAQmxGetErrorString(m_code, NULL, 0);
            if (neededSize > 0) {
                buffer.resize(neededSize);
                DAQmxGetErrorString(m_code, &buffer[0], neededSize);
            }
            return buffer;
        }
    };

    class Task
    {
        typedef TaskHandle TaskHandle;

        Task(TaskHandle handle)
            : m_handle(handle)
        {
        }

        TaskHandle CreateNamedTask(std::string name)
        {
            TaskHandle retval;
            int32 error = DAQmxCreateTask(name.c_str(), &retval);
            if (error < 0)
                qDebug() << DAQException(error).description();

            return retval;
        }

        Task& operator=(const Task&);   // not provided

    public:
        const TaskHandle m_handle;

        Task(std::string name)
            : m_handle(CreateNamedTask(name))
        {
        }

        ~Task()
        {
            DAQmxClearTask(m_handle);
        }

        void AddChannel(std::string physicalName, int terminalConfig, double minVal, double maxVal, std::string customScale = std::string())
        {
            int32 error = DAQmxCreateAIVoltageChan(m_handle, physicalName.c_str(), NULL, terminalConfig, minVal, maxVal, customScale.empty() ? DAQmx_Val_Volts : DAQmx_Val_Custom, customScale.empty() ? NULL : customScale.c_str());
            if (error < 0)
                qDebug() << DAQException(error).description();
        }

        size_t GetChannelCount(void) const
        {
            uInt32 chanCount;
            int32 error = DAQmxGetTaskNumChans(m_handle, &chanCount);
            if (error < 0)
                qDebug() << DAQException(error).description();
            return chanCount;
        }

        void SetupContinuousAcquisition(double samplesPerSecond, unsigned int bufferSize)
        {
            int32 error = DAQmxCfgSampClkTiming(m_handle, NULL, samplesPerSecond, DAQmx_Val_Rising, DAQmx_Val_ContSamps, bufferSize);
            if (error < 0)
                qDebug() << DAQException(error).description();
        }

        void Start()
        {
            int32 error = DAQmxStartTask(m_handle);
            if (error < 0)
                qDebug() << DAQException(error).description();
        }

        void Stop()
        {
            int32 error = DAQmxStopTask(m_handle);
            if (error < 0)
                qDebug() << DAQException(error).description();
        }

        size_t TryRead(double buffer[], size_t bufferSize, bool32 fillMode = DAQmx_Val_GroupByScanNumber)
        {
            int32 truncatedBufferSize = (int32)bufferSize;
            if (truncatedBufferSize < 0 || bufferSize != (size_t)truncatedBufferSize)
                qDebug("invalid bufferSize");
            int32 samplesRead;
            int32 error = DAQmxReadAnalogF64(m_handle, DAQmx_Val_Auto, 0, fillMode, buffer, truncatedBufferSize, &samplesRead, NULL);
            if (error < 0)
                qDebug() << DAQException(error).description();
            return samplesRead;
        }

        void SyncReadNonInterleaved(double buffer[], size_t bufferSize, size_t samplesToRead)
        {
            int32 truncatedBufferSize = (int32)bufferSize;
            if (truncatedBufferSize < 0 || bufferSize != (size_t)truncatedBufferSize)
                qDebug("invalid bufferSize");
            int32 truncatedSamplesToRead = (int32)samplesToRead;
            if (truncatedSamplesToRead < 0 || samplesToRead != (size_t)truncatedSamplesToRead)
                qDebug("invalid samplesToRead");
            int32 samplesRead;
            int32 error = DAQmxReadAnalogF64(m_handle, truncatedSamplesToRead, -1, DAQmx_Val_GroupByChannel, buffer, truncatedBufferSize, &samplesRead, NULL);
            if (error < 0)
                qDebug() << DAQException(error).description();
            if (samplesRead != truncatedSamplesToRead)
                qDebug("DAQmxReadAnalogF64 misbehaved?");
        }

        template<size_t N>
        size_t TryRead(double(&buffer)[N])
        {
            return TryRead(buffer, N, DAQmx_Val_GroupByScanNumber);
        }

        template<size_t N>
        size_t TryReadNonInterleaved(double(&buffer)[N])
        {
            return TryRead(buffer, N, DAQmx_Val_GroupByChannel);
        }

        template<size_t N>
        void SyncReadNonInterleaved(double(&buffer)[N], size_t samplesToRead)
        {
            SyncReadNonInterleaved(buffer, N, samplesToRead);
        }

        template<size_t N>
        void SyncReadTimeout(double(&buffer)[N], size_t samplesToRead, double secondsTimeout)
        {
            int32 truncatedBufferSize = (int32)N;
            if (truncatedBufferSize < 0 || N != (size_t)truncatedBufferSize)
                qDebug("invalid bufferSize");
            int32 truncatedSamplesToRead = (int32)samplesToRead;
            if (truncatedSamplesToRead < 0 || samplesToRead != (size_t)truncatedSamplesToRead)
                qDebug("invalid samplesToRead");
            int32 samplesRead;
            int32 error = DAQmxReadAnalogF64(m_handle, truncatedSamplesToRead, secondsTimeout, DAQmx_Val_GroupByScanNumber, buffer, truncatedBufferSize, &samplesRead, NULL);
            if (error < 0)
                qDebug() << DAQException(error).description();
            if (samplesRead != truncatedSamplesToRead)
                qDebug("DAQmxReadAnalogF64 misbehaved?");
        }

        template<typename TFunctor>
        void* SubscribeSamplesRead(unsigned int blockSize, TFunctor* callbackFunctor)
        {
            struct ReadSamplesRegistration
            {
                Task* const m_pTask;
                TFunctor* const m_functor;
                static int32 CVICALLBACK Callback(TaskHandle taskHandle, int32, uInt32 /*nSamples*/, void* pCallbackData)
                {
                    ReadSamplesRegistration* that = static_cast<ReadSamplesRegistration*>(pCallbackData);
                    if (that->m_pTask->m_handle != taskHandle)
                        return -1;

                    return (*that->m_functor)(that->m_pTask);

                }

                ReadSamplesRegistration(Task* pTask, TFunctor* callbackFunctor)
                    : m_pTask(pTask)
                    , m_functor(callbackFunctor)
                {
                }

            private:
                ReadSamplesRegistration& operator=(const ReadSamplesRegistration&) { __assume(false); }
            }*pRegistration = new ReadSamplesRegistration(this, callbackFunctor);

            int32 error = DAQmxRegisterEveryNSamplesEvent(m_handle, DAQmx_Val_Acquired_Into_Buffer, blockSize, 0, &ReadSamplesRegistration::Callback, pRegistration);
            if (error < 0)
                qDebug() << DAQException(error).description();

            return pRegistration;
        }


    };
}

class NidaqmxConnectionThread : public QThread
{
    Q_OBJECT

public:

    bool HasError() const;

    static int32 CVICALLBACK EveryNCallback(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData);
    static int32 CVICALLBACK EveryNCallbackCalibration(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData);

    static int32 CVICALLBACK EveryNCallbackPlatform(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData);
    static int32 CVICALLBACK EveryNCallbackPlatformCalibration(TaskHandle taskHandle, int32 everyNsamplesEventType, uInt32 nSamples, void* callbackData);

    static int32 CVICALLBACK DoneCallback(TaskHandle taskHandle, int32 status, void* callbackData);

    QString cardName;
    QString platformCardName;

    static float m_acqRate;
    static float m_callBackRate;
    static uint m_numberOfChannels;
    static uint m_bufferSize;
    static bool m_enableStartTrigger;
    static uint m_numberOfSample;

    static NidaqmxConnectionThread* GetInstance();
    static bool init(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample);

    void startSensorAcquisition() const;
    void stopSensorAcquisition() const;

    void startSensorCalibration() const;
    void stopSensorCalibration() const;

    void setUPTask(float acquisitionRate, float callBackRate, const QVector<Sensor>& sensorList, bool triggerEnable, uint numberOfSample);
    void setUpCalibrationTask(float acquisitionRate, float callBackRate, const QVector<Sensor>& sensorList, bool triggerEnable, uint numberOfSample);

    void startPlaformAcquisition() const;
    void stopPlaformAcquisition() const;

    void startPlaformCalibration() const;
    void stopPlaformCalibration() const;

    void setUPPlatformTask(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample);
    void setUpPlatformCalibrationTask(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample);

    void clearTask();

    NidaqmxConnectionThread(NidaqmxConnectionThread const&) = delete;
    void operator=(NidaqmxConnectionThread const&) = delete;

    ~NidaqmxConnectionThread();

private:

    NidaqmxConnectionThread(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample);
    static NidaqmxConnectionThread* getInstanceImpl(float acquisitionRate, float callBackRate, uint nOfChannels, bool triggerEnable, uint numberOfSample);

    NIDAQmx::Task* m_acquisitionTask;
    NIDAQmx::Task* m_calibrationTask;

    NIDAQmx::Task* m_platformAcquisitionTask;
    NIDAQmx::Task* m_platformCalibrationTask;

    bool errorFlag;

signals:
    void newDataPacketNi(const DataPacket&);
    void newDataPacketPlatform(const DataPacket&);

    void newDataPacketNiCalibration(const DataPacket&);
    void newDataPacketPlatformCalibration(const DataPacket&);




};

#endif // NIDAQMXCONNECTIONTHREAD_H
