#ifndef MYUDP_H
#define MYUDP_H

#include <QObject>
#include <QUdpSocket>
#include "dataPacket.h"

class MyUDP : public QObject
{
    Q_OBJECT
public:
    explicit MyUDP(QObject *parent = nullptr);
    void streamData(const DataPacket& data, uint sensorId);

public slots:
    void readyRead();

private:
    QUdpSocket *socket;

signals:

};

#endif // MYUDP_H
