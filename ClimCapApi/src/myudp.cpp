#include "myudp.h"
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

QJsonArray serialize(const QVector<double>* ar, int ar_size)
{
    QJsonArray result;

    for (int i = 0; i < ar_size; i++)
        result.append(ar->at(i));

    return result;
}

void deserialize(const QByteArray& byteArray)
{
    QDataStream stream(byteArray);
    int ar_size = 0;
    stream >> ar_size;
    int* ar = new int[ar_size];

    for (int i = 0; i < ar_size; i++)
        stream >> ar[i];
}

//------------------------------------------------------------------

MyUDP::MyUDP(QObject *parent) :
    QObject(parent)
{
    socket = new QUdpSocket(this);

    socket->bind(QHostAddress::LocalHost, 20001);

    //connect(socket, SIGNAL(readyRead()), this, SLOT(readyRead()));
}

void MyUDP::streamData(const DataPacket& data, const DataPacket& analogData, uint sensorId) const
{
    int sid = sensorId;
    QJsonObject jsdata;

    jsdata.insert("sid", sid);
    const auto jsArr = serialize(&data.dataValues, data.m_channelNumber);
    jsdata.insert("data", jsArr);
    const auto jsArrtwo = serialize(&analogData.dataValues, analogData.m_channelNumber);
    jsdata.insert("analog", jsArrtwo);

    QJsonDocument jsonDoc;
    jsonDoc.setObject(jsdata);

    QString jsString = QString::fromLatin1(jsonDoc.toJson());
    QByteArray datagrudp;
    datagrudp.append(jsString.toUtf8());

    socket->writeDatagram(datagrudp, QHostAddress::LocalHost, 20001);
}



void MyUDP::readyRead()
{
    QByteArray buffer;
    buffer.resize(socket->pendingDatagramSize());

    QHostAddress sender;
    quint16 senderPort;

    socket->readDatagram(buffer.data(), buffer.size(),
                         &sender, &senderPort);

    qDebug() << "Message from: " << sender.toString();
    qDebug() << "Message port: " << senderPort;
    qDebug() << "Message: " << buffer;
}
