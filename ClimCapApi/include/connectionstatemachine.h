#ifndef CONNECTIONSTATEMACHINE_H
#define CONNECTIONSTATEMACHINE_H

#include <QObject>

class ConnectionStateMachine : public QObject
{
    Q_OBJECT

public:
    typedef enum class state { notconnected, acquisition, calibration, stop, waitingTrigger };
    
    explicit ConnectionStateMachine(QString acquisitionDeviceName, QObject* parent = nullptr);

    void setState(ConnectionStateMachine::state newState);
    const QString& getAcquistionDeviceName() const;
    ConnectionStateMachine::state m_state;
signals:
    void stateChanged(ConnectionStateMachine::state newState);

private:

    QString m_acquisitionDeviceName;


};

#endif // CONNECTIONSTATEMACHINE_H
