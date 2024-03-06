#include "connectionstatemachine.h"

ConnectionStateMachine::ConnectionStateMachine(QString acquisitionDeviceName, QObject* parent)
    : QObject{parent}
{
    this->m_acquisitionDeviceName = acquisitionDeviceName;
}

void ConnectionStateMachine::setState(ConnectionStateMachine::state newState)
{
    this->m_state = newState;
    emit stateChanged(newState);
}

const QString& ConnectionStateMachine::getAcquistionDeviceName() const
{
    return this->m_acquisitionDeviceName;
}
