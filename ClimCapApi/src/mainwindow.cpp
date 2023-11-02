#include "mainwindow.h"
#include "ui_mainwindow.h"
#include "console.h"

#include "settingswidget.h"

#include <QLabel>
#include <QMessageBox>
#include <QProgressDialog>

Console* MainWindow::m_console = nullptr;
Mainwindow_::Emitter MainWindow::s_emitter;

MainWindow::MainWindow(QWidget *parent) :
    QMainWindow(parent),
    m_ui(new Ui::MainWindow),
    m_status(new QLabel),
    m_settings(new SettingsWidget),
    m_udp(new QUdpSocket(this))
{
    m_console = new Console();
    connect(&s_emitter, SIGNAL(append_log(QString)), m_console, SLOT(putData(QString)));

    connect(m_settings, SIGNAL(newConfigFile()), this, SLOT(appSettingsChanged()));

    MyApc = new AppController(); 
    MyApc->startUp();

    m_ui->setupUi(this);
    m_console->setEnabled(false);
    setCentralWidget(m_console);

    m_ui->actionConnect->setEnabled(true);
    m_ui->actionDisconnect->setEnabled(false);
    m_ui->actionQuit->setEnabled(true);
    m_ui->actionConfigure->setEnabled(true);

    m_ui->statusBar->addWidget(m_status);

    initActionsConnections();

    connect(m_console, &Console::getData, this, &MainWindow::writeData);

}

MainWindow::~MainWindow()
{
    delete m_settings;
    delete m_ui;
}

void MainWindow::openUdpPort()
{
    this->MyApc->startAcquisition();

    if (m_udp->open(QIODevice::ReadWrite)) 
    {
        m_console->setEnabled(true);
        m_console->setLocalEchoEnabled(true);
        m_ui->actionConnect->setEnabled(false);
        m_ui->actionDisconnect->setEnabled(true);
        m_ui->actionConfigure->setEnabled(false);
        //m_ui->actionCalibration->setEnabled(false);
        showStatusMessage(tr("Debut acquisition"));
    } 
    else
    {
        QMessageBox::critical(this, tr("Erreur"), m_udp->errorString());
        showStatusMessage(tr("Erreur d'ouverture"));
    }
}

void MainWindow::appSettingsChanged()
{
    if (MyApc != nullptr)
    {
        qDebug("app settgings change");
        MyApc->reloadSensorConfiguration();
    }
}

void MainWindow::startCalibration()
{
    qDebug("Lancement calibration");
    this->MyApc->MyDataController->Calibrate_Sensors( this->MyApc->m_sampleCalibrationNumber );
    
   // m_ui->actionConnect->setEnabled(false);
    //m_ui->actionConfigure->setEnabled(false);
    //m_ui->actionCalibration->setEnabled(false);
}

void MainWindow::closeUdpPort()
{
    if (m_udp->isOpen())
        m_udp->close();

    this->MyApc->stopAcquisition();

    m_console->setEnabled(false);
    m_ui->actionConnect->setEnabled(true);
    m_ui->actionDisconnect->setEnabled(false);
    m_ui->actionConfigure->setEnabled(true);
    m_ui->actionCalibration->setEnabled(true);

    showStatusMessage(tr("Stop de l'acquisition"));
}

void MainWindow::writeData(const QByteArray &data)
{
    m_udp->write(data);
}

void MainWindow::readData()
{
    const QByteArray data = m_udp->readAll();
    m_console->putData(data);
}

void MainWindow::handleError(QSerialPort::SerialPortError error)
{
    if (error == QSerialPort::ResourceError) {
        QMessageBox::critical(this, tr("Critical Error"), m_udp->errorString());
        closeUdpPort();
    }
}

void MainWindow::initActionsConnections()
{
    connect(m_ui->actionConnect, &QAction::triggered, this, &MainWindow::openUdpPort);
    connect(m_ui->actionDisconnect, &QAction::triggered, this, &MainWindow::closeUdpPort);
    connect(m_ui->actionQuit, &QAction::triggered, this, &MainWindow::close);
    connect(m_ui->actionConfigure, &QAction::triggered, this, &MainWindow::showSettingsWindow);
    connect(m_ui->actionClear, &QAction::triggered, m_console, &Console::clear);
    connect(m_ui->actionCalibration, &QAction::triggered, this, &MainWindow::startCalibration);
}

void MainWindow::showStatusMessage(const QString &message)
{
    m_status->setText(message);
}

void MainWindow::showSettingsWindow()
{
    m_settings->exec();
}

void MainWindow::updatePlotSettings() const
{
    //this->GraphPlotWidgetList.at(i)->setAvailableSensorList(this->dataController->getLoadedSensorID());
}
