#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QSerialPort>
#include <QUdpSocket>
#include "AppController.h"

QT_BEGIN_NAMESPACE

class QLabel;

namespace Ui {
class MainWindow;
}

QT_END_NAMESPACE

class Console;
class SettingsWidget;

namespace Mainwindow_ {

    class Emitter : public QObject
    {
        Q_OBJECT
    public:
        Emitter() {};
        ~Emitter() {};
    signals:
        void append_log(QString msg);
    };
}

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    static Console* m_console;
    static Mainwindow_::Emitter s_emitter;

    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();
   
private slots:
    void openUdpPort();
    void startCalibration();
    void closeUdpPort();
    void writeData(const QByteArray &data);
    void readData();

    void handleError(QSerialPort::SerialPortError error);

private:
    void initActionsConnections();
    void updatePlotSettings() const;
    void showSettingsWindow();

private:
    void showStatusMessage(const QString &message);

    Ui::MainWindow *m_ui = nullptr;
    QLabel *m_status = nullptr;

    SettingsWidget *m_settings = nullptr;
    QUdpSocket *m_udp = nullptr;

    AppController* MyApc = nullptr;

private slots:
    void appSettingsChanged();
};

#endif // MAINWINDOW_H
