#pragma once
#include <QDebug>
#include <QGenericMatrix>

template <class T>
class DataPacketG {

public:
	uint m_channelNumber;
	QVector<T> dataValues;  
	uint frameNumber;
	double timeKey;

	DataPacketG(uint channelNumber)
	{
		frameNumber = 0;
		m_channelNumber = channelNumber;
		dataValues.reserve(channelNumber);
	}

	~DataPacketG()
	{

	}

	void printDebug() const
	{
		qDebug() << "fn : " << frameNumber;
		for (uint i = 0; i < m_channelNumber; i++)
			qDebug() << "channel " << i << " = " << dataValues.at(i) << " ";
	}
};

typedef DataPacketG<double> DataPacket;
Q_DECLARE_METATYPE(DataPacket);