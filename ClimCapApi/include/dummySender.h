#pragma once
#include <QCoreApplication>
#include <QTimer>
#include <QObject>

class DummySender : public QThread {
    Q_OBJECT
private:
	QTimer* timer;
	uint  m_numberOfChannels;
	uint m_frequency;

signals:
	void newDataPacketNi(const DataPacket&);

public:
	DummySender()
	{
        timer = new QTimer(this);
		m_numberOfChannels = 12;
		m_frequency = 200;
        connect(timer, &QTimer::timeout, this, &DummySender::onTimeout);
        //timer->start(1000); 
    }

	void setNbchan(uint nbchan)
	{
		this->m_numberOfChannels = nbchan;
	}

	void start()
	{
		uint time_ms = 1 / m_frequency * 1000;
		timer->start(5);
	}

	void stop() 
	{
		timer->stop();
	}

public slots:
    void onTimeout() {

			double* dummydata = new double[m_numberOfChannels];
			for (uint i = 0; i < ((m_numberOfChannels) / 8); i++)
			{
				dummydata[i * 8] = 1;
				dummydata[i * 8 + 1] = 2;
				dummydata[i * 8 + 2] = 3;
				dummydata[i * 8 + 3] = 4;
				dummydata[i * 8 + 4] = 5;
				dummydata[i * 8 + 5] = 6;
				dummydata[i * 8 + 6] = 7;
				dummydata[i * 8 + 7] = 8;
			}
			//dummydata[m_numberOfChannels - 1] = 5;

			DataPacket DP2(m_numberOfChannels);

			std::copy(dummydata, dummydata + m_numberOfChannels, std::begin(DP2.dataValues));
			delete[] dummydata;
			emit newDataPacketNi(DP2);
    }


};
