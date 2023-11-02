#include "dataProcessing.h"
#include "dataPacket.h"

#include <QApplication>
#include <QDebug>
#include <QGenericMatrix>
#include <QFile>
#include <QDir>
#include <iterator>
#include <algorithm>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>

DataController::DataController(QObject* parent)
    : QObject{ parent }
{
    this->applyRotMatrix = true;
    this->applyOffset = true;
    this->applyWallRotation = true;

    m_calibrationFilesPath = "../data/calibration_matrices";

    m_configFilePath = "../data/save.json";

    m_sensorCalibrationFiles = {
        "G_202109A1-1_o2.txt",
        "G_202109A1-2_o2.txt",
        "G_202109A1-3_o2.txt",
        "G_202109A1-4_o2.txt",
        "G_202109A1-5_o2.txt",
        "G_202109A1-6_o2.txt",
        "G_202109A1-7_o2.txt",
        "G_202109A1-8_o2.txt",
        "G_202109A1-9_o2.txt",
        "G_202109A1-10_o2.txt",
        "G_202109A1-11_o2.txt",
    };

    m_plaformCalibrationFiles = {
        "dummy1.txt",
        "dummy2.txt"
    };

}


#pragma region CONFIG LOADING

void DataController::clearSensorConfiguration()
{
    this->sensors.clear();
}

QGenericMatrix<3, 3, double> calculateWallRotMatrix(double wallAngle)
{
    constexpr int N = 3;
    double theta = wallAngle * M_PI / 180.0;

    // Calcul de la matrice de rotation
    double cos_theta = cos(theta);
    double sin_theta = sin(theta);

    double rot_matrix[N * N] =
    {
        1,0,0,
        0, cos_theta, -sin_theta,
        0, sin_theta, cos_theta
    };

    QGenericMatrix<3, 3, double> tprotationMatrice(rot_matrix);

    return tprotationMatrice;
}

uint DataController::loadPlatformToAnalogConfig()
{
    this->plaforms.clear();

    Sensor platformL(40, 0, 0);
    Sensor platformR(41, 8, 0);

    QGenericMatrix<12, 6, double> calibrationMatrixO2container;

    loadCalibrationMatriceOrdre2PLATFORM(platformL.getSensorId(), calibrationMatrixO2container);
    platformL.setCalibrationMatriceO2PLATFORM(calibrationMatrixO2container);
    this->plaforms.push_back(platformL);

    loadCalibrationMatriceOrdre2PLATFORM(platformR.getSensorId(), calibrationMatrixO2container);
    platformL.setCalibrationMatriceO2PLATFORM(calibrationMatrixO2container);
    this->plaforms.push_back(platformR);

    return true;
}

bool DataController::loadCalibrationMatriceOrdre2PLATFORM(uint sensorNumber, QGenericMatrix<12, 6, double>& matrice)
{
  
    QString path;
    path.append(m_calibrationFilesPath);
    
    //NOT IDEAL TO DO 
    path.append("/" + m_plaformCalibrationFiles[sensorNumber - 40]);

    //qDebug() << "Ouverture matrice de calibration" << path;

    QFile inputFile(path);

    QStringList splitList;
    double matriceData[12 * 6];

    if (inputFile.open(QIODevice::ReadOnly)) {
        QTextStream in(&inputFile);
        uint mcpt = 0;
        while (!in.atEnd())
        {
            QString line = in.readLine();
            splitList = line.split("\t");

            for (uint i = 0; i < splitList.size(); ++i, ++mcpt)
            {
                matriceData[mcpt] = splitList.at(i).toDouble();
            }

        }
        QGenericMatrix<12, 6, double> calibrationMatrixO2(matriceData);
        matrice = calibrationMatrixO2;
        inputFile.close();
    }
    else
    {
        qCritical() << "Impossible d'ouvrir le fichier matrice de calibration " << path;
        return false;
    }

    return true;
}

uint DataController::loadSensorToAnalogConfig()
{
    QFile file(m_configFilePath);
    clearSensorConfiguration();

    if (!file.open(QIODevice::ReadOnly))
    {
        qWarning() << "Impossible d'ouvrir le fichier de configuration " << m_configFilePath;
        return 0;
    }

    QTextStream stream(&file);
    QString content = stream.readAll();
    file.close();

    QJsonParseError parseError;
    QJsonDocument doc = QJsonDocument::fromJson(content.toUtf8(), &parseError);

    if (parseError.error != QJsonParseError::NoError)
    {
        qWarning() << "Erreur de parsing " << parseError.offset << ":" << parseError.errorString();
        return 1;
    }

    if (!doc.isEmpty())
    {
        QJsonObject jsonObj = doc.object();
        double angle = jsonObj.value("wallangle").toDouble();
        qDebug() << "Angle du mur : " << angle;

        //TO DO STORE FOR EACH sensor instead
        this->wallRotMatrix = calculateWallRotMatrix(angle);

        QJsonArray array = jsonObj["sensors"].toArray();

        QGenericMatrix<12, 6, double> calibrationMatrixO2container;

        for (const auto& item : array) {
            QJsonObject obj = item.toObject();

            QString sensorname = obj["name"].toString();
            uint sensorId = obj["id"].toInt();
            uint sensorChannel = obj["chan"].toInt();
            double sensorAngle = obj["angle"].toDouble();
            double sensorZRotation = obj["zRotation"].toDouble();

            Sensor tms(sensorId, sensorChannel, sensorAngle);

            if (sensorZRotation != 0)
                tms.setRotationAngle(sensorZRotation, 'z');

            if (!this->loadCalibrationMatriceOrdre2(tms.getSensorId(), calibrationMatrixO2container))
            {
                qCritical("Matrice de calibration ordre2 non initialisee");
                return 0;
            }

            tms.setCalibrationMatriceO2(calibrationMatrixO2container);
            this->sensors.push_back(tms);

            qDebug() << "Chargement du capteur" << tms.getSensorId() << " OK ";
            //tms.toString(true);
        }
    }

    return this->sensors.count();
}


bool DataController::loadCalibrationMatriceOrdre2(uint sensorNumber, QGenericMatrix<12, 6, double>& matrice)
{
    if (sensorNumber == 0) sensorNumber = 1;

    QString path;
    path.append(m_calibrationFilesPath);
    path.append("/" + m_sensorCalibrationFiles[sensorNumber - 1]);

    //qDebug() << "Ouverture matrice de calibration" << path;

    QFile inputFile(path);

    QStringList splitList;
    double matriceData[12 * 6];

    if (inputFile.open(QIODevice::ReadOnly)) {
        QTextStream in(&inputFile);
        uint mcpt = 0;
        while (!in.atEnd())
        {
            QString line = in.readLine();
            splitList = line.split("\t");

            for (uint i = 0; i < splitList.size(); ++i, ++mcpt)
            {
                matriceData[mcpt] = splitList.at(i).toDouble();
            }

        }
        QGenericMatrix<12, 6, double> calibrationMatrixO2(matriceData);
        matrice = calibrationMatrixO2;
        inputFile.close();
    }
    else
    {
        qCritical() << "Impossible d'ouvrir le fichier matrice de calibration " << path;
        return false;
    }

    return true;
}


#pragma endregion

#pragma region OFFSET THREAD

void DataController::Calibrate_Sensors(uint nbSamples)
{
    for (uint i = 0; i < this->sensors.count(); ++i)
    {
        auto curSensor = this->sensors.at(i);

        //createThreadAvgZero(curSensor.getSensorId(), curSensor.getfirstChannel(), nbSamples);
    }

    //to do 

    for (uint i = 0; i < this->plaforms.count(); ++i)
    {
        auto curSensor = this->sensors.at(i);

        //createThreadAvgZero(curSensor.getSensorId(), curSensor.getfirstChannel(), nbSamples);
    }
}

// OFFSET THREAD
void DataController::createThreadAvgZero(uint sensorID, uint sensorStartChannel, uint nbSamples)
{
    qDebug() << "Creating worker thread for zero correction value of sensors " << sensorID
        << "start channel: " << sensorStartChannel;

    //uint sensorFirstAnalogChannel = this->sensorIDtoAnalogEntry.value(sensorID);

    QProgressDialog* progressDialog = new QProgressDialog("Calibration du capteur", "Stop", 0, nbSamples);
    progressDialog->setWindowModality(Qt::WindowModal);
    progressDialog->setMinimumDuration(0);
    progressDialog->setValue(0);
    progressDialog->show();

    QThread* thread = new QThread();
    //redoot stch var
    CalibrationWork* worker = new CalibrationWork(sensorID, sensorStartChannel, nbSamples);
    worker->moveToThread(thread);

    //connect(worker, &CalibrationWork::error, this, &MyClass::errorString);

    connect(thread, &QThread::started, worker, &CalibrationWork::starting);

    connect(worker, &CalibrationWork::finished, thread, &QThread::quit);
    connect(worker, &CalibrationWork::finished, worker, &CalibrationWork::deleteLater);
    connect(thread, &QThread::finished, thread, &QThread::deleteLater);

    connect(this, SIGNAL(gotNewDataPacket(DataPacket)), worker, SLOT(getNewAnalogData(DataPacket)));
    connect(worker, SIGNAL(resultReady(uint, DataPacket)), this, SLOT(handleResultsAvgZero(uint, DataPacket)));
    connect(worker, SIGNAL(progress(int)), progressDialog, SLOT(setValue(int)));

    connect(progressDialog, &QProgressDialog::canceled, worker, &CalibrationWork::finished);

    thread->start();
}

void DataController::handleResultsAvgZero(uint sensorid, const DataPacket& analogZeroCorrection)
{
    qDebug() << "Handle new calibration avg result for sensor" << sensorid << "sn array " << getSensor(sensorid).getSensorId();

    double darr[6];

    getSensor(sensorid).toString(false);

    //why don't work
    //std::copy(std::begin(analogZeroCorrection.dataValues),
    //          std::end(analogZeroCorrection.dataValues), darr);

    for (uint i = 0; i < 6; ++i) {
        darr[i] = analogZeroCorrection.dataValues[i];
        qDebug() << "dari : " << darr[i] << " ::" << analogZeroCorrection.dataValues[i];
    }
    getSensor(sensorid).setChannelCalibrationValues(darr);
    for (uint i = 0; i < 6; ++i) qDebug() << getSensor(sensorid).getChannelCalibrationValuesArr()[i];
}

#pragma endregion

#pragma region DATA PROCESSING
//_____________________
//Data Processing______
const QGenericMatrix<1, 6, double> DataController::ChannelanalogToForce3axisForce(double rawAnalogChannelValues[6], Sensor& sensor, uint matrixOrder)
{
    QGenericMatrix<1, 6, double> result;
    if (matrixOrder == 1)
    {
        QGenericMatrix<1, 6, double> analogValuesMatrix(rawAnalogChannelValues);
        result = sensor.getCalibrationMatriceO1() * analogValuesMatrix;
    }
    else if (matrixOrder == 2)
    {
        double analogDataSquared[12];
        for (uint i = 0; i < 6; i++) analogDataSquared[i] = rawAnalogChannelValues[i];
        for (uint i = 0; i < 6; i++) analogDataSquared[i + 6] = rawAnalogChannelValues[i] * rawAnalogChannelValues[i];

        QGenericMatrix<1, 12, double> analogValuesSquare(analogDataSquared);
        result = sensor.getCalibrationMatriceO2() * analogValuesSquare;
    }
    return result;
}

void DataController::processNewDataPacketFromNi(const DataPacket& d)
{
    this->processNewDataPacket(d);
}


void DataController::processNewDataPacket(const DataPacket& d)
{
    double dataBySensor[6] = { 0,0,0,0,0,0 };
    //d.printDebug();
    emit this->gotNewDataPacket(d);

    for (auto gp = sensors.begin(); gp != sensors.end(); gp++)
    {
        uint currentSensorID = (*gp).getSensorId();

        const double* sensorCalibrationValues = (*gp).getChannelCalibrationValuesArr();
        uint sensorFirstAnalogChannel = (*gp).getfirstChannel();

        auto rotationMatrix = (*gp).getRotationMatrix();

        //nombre de channels par capteurs (6)
        for (uint i = 0; i < 6; ++i)
        {
            uint idx = ((sensorFirstAnalogChannel)+i);

            if (idx > d.m_channelNumber)
            {
                qDebug() << "Erreur pas assez de voies d'acquisition disponibles";
                qDebug() << "Capteur " << currentSensorID << " est associe a la voie " <<
                    sensorFirstAnalogChannel << " mais il y a seulement " << d.dataValues.count() << "de data de disponible";
                break;
            }

            //apply 0 offset to raw values
            if (this->applyOffset)
            {
                dataBySensor[i] = d.dataValues[idx] - sensorCalibrationValues[i];
            }

        }

        //calculate forces
        QGenericMatrix<1, 6, double> result = this->ChannelanalogToForce3axisForce(dataBySensor, (*gp), 2);

        DataPacket finalForce(6);

        if (this->applyRotMatrix)
        {
            double forcet[3] = { result(0,0), result(1,0) , result(2,0) };

            QGenericMatrix<1, 3, double> force(forcet);

            //apply rotation matrix to force vector
            QGenericMatrix<1, 3, double> forceVecRot = rotationMatrix * force;

            //apply wall rotation matrix
            if (this->applyWallRotation)
                forceVecRot = this->wallRotMatrix * forceVecRot;

            finalForce.dataValues[0] = forceVecRot(0, 0);
            finalForce.dataValues[1] = forceVecRot(1, 0);
            finalForce.dataValues[2] = forceVecRot(2, 0);

        }
        else // force without angle
        {
            //generic vector for debuging
            finalForce.dataValues[0] = result(0, 0);
            finalForce.dataValues[1] = result(1, 0);
            finalForce.dataValues[2] = result(2, 0);
        }

        //moment value
        finalForce.dataValues[3] = result(3, 0);
        finalForce.dataValues[4] = result(4, 0);
        finalForce.dataValues[5] = result(5, 0);

        bool debug = false;
        if (debug)
        {
            finalForce.dataValues[0] = dataBySensor[0];
            finalForce.dataValues[1] = dataBySensor[1];
            finalForce.dataValues[2] = dataBySensor[2];
            finalForce.dataValues[3] = dataBySensor[3];
            finalForce.dataValues[4] = dataBySensor[4];
            finalForce.dataValues[5] = dataBySensor[5];
        }

        //finalForce.printDebug();

        //(*gp).pushDataForceMoment(finalForce);

        udpClient->streamData(finalForce, currentSensorID);
    }

    //send_chrono_pulse
    DataPacket chrono_pulse(1);
    double lastDataCol = d.dataValues[d.m_channelNumber - 1];
    chrono_pulse.dataValues[0] = lastDataCol;

    udpClient->streamData(chrono_pulse, 0);

}


// Data processing platform
const QGenericMatrix<1, 6, double> DataController::PLATFORMChannelanalogToForce3axisForce(double rawAnalogChannelValues[8], Sensor& sensor)
{

    // to do 
    QGenericMatrix<1, 6, double> result;

    double analogDataSquared[12];


    for (uint i = 0; i < 6; i++) analogDataSquared[i] = rawAnalogChannelValues[i];
    for (uint i = 0; i < 6; i++) analogDataSquared[i + 6] = rawAnalogChannelValues[i] * rawAnalogChannelValues[i];

    QGenericMatrix<1, 12, double> analogValuesSquare(analogDataSquared);
    result = sensor.getCalibrationMatriceO2PLATFORM() * analogValuesSquare;

    return result;
}


void DataController::processNewDataPacketPlatformFromNi(const DataPacket& d)
{
    double dataBySensor[8] = { 0,0,0,0,0,0,0,0 };
    //d.printDebug();
    //emit this->gotNewDataPacket(d);

    for (auto gp = plaforms.begin(); gp != sensors.end(); gp++)
    {
        uint currentSensorID = (*gp).getSensorId();

        const double* sensorCalibrationValues = (*gp).getChannelCalibrationValuesArr();
        uint sensorFirstAnalogChannel = (*gp).getfirstChannel();

        auto rotationMatrix = (*gp).getRotationMatrix();

        //nombre de channels par capteurs (8) (platforme)
        for (uint i = 0; i < 8; ++i)
        {
            uint idx = ((sensorFirstAnalogChannel)+i);

            if (idx > d.m_channelNumber)
            {
                qDebug() << "Erreur pas assez de voies d'acquisition disponibles";
                qDebug() << "Capteur " << currentSensorID << " est associe a la voie " <<
                    sensorFirstAnalogChannel << " mais il y a seulement " << d.dataValues.count() << "de data de disponible";
                break;
            }

            //apply 0 offset to raw values
            if (this->applyOffset)
            {
                dataBySensor[i] = d.dataValues[idx] - sensorCalibrationValues[i];
            }

        }

        //calculate forces
        QGenericMatrix<1, 6, double> result = this->ChannelanalogToForce3axisForce(dataBySensor, (*gp), 2);

        DataPacket finalForce(6);

        //moment value
        finalForce.dataValues[3] = result(3, 0);
        finalForce.dataValues[4] = result(4, 0);
        finalForce.dataValues[5] = result(5, 0);


        //finalForce.printDebug();

        udpClient->streamData(finalForce, currentSensorID);
    }

}

#pragma endregion


////_____ TOOLS


void DataController::displaySensor()
{
    qDebug() << "N sensors" << this->sensors.count();
    for (uint i = 0; i < this->sensors.count(); ++i)
    {
        this->sensors.at(i).toString(false);
    }

    qDebug() << "N platform" << this->plaforms.count();
    for (uint i = 0; i < this->plaforms.count(); ++i)
    {
        this->plaforms.at(i).toString(false);
    }
}

Sensor& DataController::getSensor(uint id)
{
    for (Sensor& s : this->sensors) {
        if (id == s.getSensorId()) {
            return s;
        }
    }

    throw std::runtime_error("Object not found in vector.");
}

void DataController::connectToUdpSteam(MyUDP* udps)
{
    this->udpClient = udps;
}




///////////////////////////////////////////////////////////////////////////////////////