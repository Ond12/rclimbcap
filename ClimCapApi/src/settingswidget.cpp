#include "settingswidget.h"
#include "ui_settingswidget.h"
#include <QStandardItemModel>
#include <QSettings>

SettingsWidget::SettingsWidget(QWidget *parent) :
    QDialog(parent),
    ui(new Ui::SettingsWidget)
{
    m_saveFilePath = "../data/save.json";
    ui->setupUi(this);
    this->ui->loadpushButton->hide();
    this->setUpComboBox();
    this->loadJson();
    this->setWindowTitle(tr("Parametres"));
    this->setGeometry(QRect(0,0,800, 600));
    this->ui->sensorListWidget->hide();

    connect(this->ui->checkBox, &QCheckBox::stateChanged, this, &SettingsWidget::onCheckboxStateChanged);

    this->ui->addPushButton->setIcon(QIcon::fromTheme("add", QIcon(":/images/plus.png")));
    this->ui->applyButton->setIcon(QIcon::fromTheme("apply", QIcon(":/images/applys.png")));
    this->ui->resestButton->setIcon(QIcon::fromTheme("reset", QIcon(":/images/resets.png")));

    QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");
   
    const auto sample_rate_setting = settings.value("sample_rate").toInt();
    this->ui->FACQSpinBox->setValue(sample_rate_setting);

    const auto acquisition_time = settings.value("acquisition_time").toInt();
    this->ui->acqTimespinBox->setValue(acquisition_time);

    const auto trigger_enable = settings.value("trigger_enable").toBool();
    this->ui->checkBox->setChecked(trigger_enable);

    const auto sample_Calibration_Number = settings.value("sample_calibration_number").toInt();
    this->ui->CalibrationSampleSpinBox->setValue(sample_Calibration_Number);

}

void SettingsWidget::setUpComboBox()
{
    uint sensorNumber = 11;
    uint lowAnalogRange = 0;
    uint numberOfChannelPerSensor = 6;
    uint highAnalogRange = lowAnalogRange + (numberOfChannelPerSensor - 1);

    for(uint i = 0; i < sensorNumber; ++i)
    {
        this->ui->nbSensorComboBox->addItem(QString::number(i+1), i+1);

        QString analogRangeItemTxt = QString::number(lowAnalogRange) + "..." + QString::number(highAnalogRange);

        this->ui->analogRangeComboBox->addItem(analogRangeItemTxt, lowAnalogRange);

        lowAnalogRange = lowAnalogRange + numberOfChannelPerSensor;
        highAnalogRange = lowAnalogRange + (numberOfChannelPerSensor - 1);
    }
}

SettingsWidget::~SettingsWidget()
{
    delete ui;
}

void SettingsWidget::on_resestButton_clicked()
{
    this->ui->sensorListWidget->clear();

    this->ui->nbSensorComboBox->clear();
    this->ui->tableWidget->clearContents();
    this->ui->tableWidget->setRowCount(0);
    this->ui->analogRangeComboBox->clear();
    this->sensorIDtoAnaloEntry.clear();

    this->setUpComboBox();
}

void SettingsWidget::on_addPushButton_clicked()
{
    if(this->ui->nbSensorComboBox->count() != 0 )
    {
        uint currentSensorId = this->ui->nbSensorComboBox->currentData().toInt();
        uint currentAnalogRange = this->ui->analogRangeComboBox->currentData().toInt();
        double currentSensorAngle = this->ui->angleDoubleSpinBox->value();
        double Zrotation = this->ui->doubleSpinBox->value();

        this->ui->nbSensorComboBox->removeItem( this->ui->nbSensorComboBox->currentIndex() );
        this->ui->analogRangeComboBox->removeItem( this->ui->analogRangeComboBox->currentIndex() );

        addNewSensorToTable(currentSensorId, "testname", currentAnalogRange, currentSensorAngle, Zrotation, false);

        this->sensorIDtoAnaloEntry.insert(currentSensorId, currentAnalogRange);
        this->ui->sensorListWidget->addItem( "Capteur " + QString::number(currentSensorId) + " -> " + QString::number(currentAnalogRange) + "-" + QString::number(currentAnalogRange+5) );
    
    }
}

void SettingsWidget::writeJson(QJsonDocument& json) const
{
    QVariantMap vmap;
    QMapIterator<int, int> i(this->sensorIDtoAnaloEntry);
    QJsonObject doc;
    QJsonArray array;

    doc["wallangle"] = this->ui->wallAngledoubleSpinBox->value();

    if (this->sensorIDtoAnaloEntry.count() != 0)
    {
        for (int row = 0; row < this->ui->tableWidget->rowCount(); ++row) {
            QJsonObject sensorItem;
              
            sensorItem["id"]    =  this->ui->tableWidget->item(row, 0)->text().toInt();
            sensorItem["name"]  =  this->ui->tableWidget->item(row, 1)->text();
            sensorItem["chan"]  =  this->ui->tableWidget->item(row, 2)->text().toInt();
            sensorItem["angle"] =  this->ui->tableWidget->item(row, 3)->text().toDouble();
            sensorItem["zRotation"] = this->ui->tableWidget->item(row, 4)->text().toDouble();
            sensorItem["isFlip"] = this->ui->tableWidget->item(row, 5)->text().toInt();
            array.append(sensorItem);
        }

        doc["sensors"] = array;
        json = QJsonDocument(doc);
    }
}

void SettingsWidget::addNewSensorToTable(uint sensorid, QString sensorname, uint sensorChannel, double sensorAngle, double sensorZRotation, bool isFlip)
{
    uint rowcount = ui->tableWidget->rowCount();

    ui->tableWidget->insertRow(rowcount);

    QTableWidgetItem* iditem = new QTableWidgetItem(QString::number(sensorid));
    iditem->setFlags(iditem->flags() & ~Qt::ItemIsEditable);
    ui->tableWidget->setItem(rowcount, 0, iditem);

    ui->tableWidget->setItem(rowcount, 1, new QTableWidgetItem(sensorname));

    QTableWidgetItem* chanitem = new QTableWidgetItem(QString::number(sensorChannel));
    chanitem->setFlags(chanitem->flags() & ~Qt::ItemIsEditable);
    ui->tableWidget->setItem(rowcount, 2, chanitem);

    ui->tableWidget->setItem(rowcount, 3, new QTableWidgetItem(QString::number(sensorAngle)));
    ui->tableWidget->setItem(rowcount, 4, new QTableWidgetItem(QString::number(sensorZRotation)));

    QTableWidgetItem* flipitem = new QTableWidgetItem(QString::number(isFlip));
    ui->tableWidget->setItem(rowcount, 5, flipitem);

}

bool SettingsWidget::loadJson()
{
    QFile file(m_saveFilePath);

    if (!file.open(QIODevice::ReadOnly | QIODevice::Text))
    {
        qWarning("Impossible d'ouvrir le fichier de configuration capteur");
        return false;
    }

    QTextStream stream(&file);
    QString content = stream.readAll();
    file.close();

    QJsonParseError parseError;
    QJsonDocument doc = QJsonDocument::fromJson(content.toUtf8(), &parseError);

    if (parseError.error != QJsonParseError::NoError) {
        qWarning() << "Parse error at " << parseError.offset << ":" << parseError.errorString();
        return 1;
    }
    
    QJsonObject jsonObj = doc.object();
    double angle = jsonObj.value("wallangle").toDouble();
    this->ui->wallAngledoubleSpinBox->setValue(angle);

    QJsonArray array = jsonObj["sensors"].toArray();

    uint row = 0;
    uint column = 6;

    this->ui->tableWidget->setRowCount(row);
    this->ui->tableWidget->setColumnCount(column);

    QStringList horzHeaders;
    horzHeaders << "Numero" << "Nom" << "Entree" << "Angle" << "Rotation" << "Flip";
    ui->tableWidget->setHorizontalHeaderLabels(horzHeaders);

    if( !doc.isEmpty() )
    {
        this->sensorIDtoAnaloEntry.clear();
        for (const auto& item : array) {
            QJsonObject obj = item.toObject();

            QString sensorname = obj["name"].toString();
            uint sensorId      = obj["id"].toInt();
            uint sensorChannel = obj["chan"].toInt();
            double sensorAngle = obj["angle"].toDouble();
            double sensorZRotation = obj["zRotation"].toDouble();
            bool isFlip = obj["isFlip"].toInt();

            this->addNewSensorToTable(sensorId, sensorname, sensorChannel, sensorAngle, sensorZRotation, isFlip);

            this->ui->sensorListWidget->addItem("Capteur " + sensorname + " -> " + QString::number(sensorChannel) + "-" + QString::number(sensorChannel + 5));

            this->sensorIDtoAnaloEntry.insert(sensorId, sensorChannel);

            int idx = this->ui->analogRangeComboBox->findData(sensorChannel);
            int idxc = this->ui->nbSensorComboBox->findData(sensorId);

            this->ui->analogRangeComboBox->removeItem(idx);
            this->ui->nbSensorComboBox->removeItem(idxc);
        }
    }
    return true;
}

void SettingsWidget::onCheckboxStateChanged(int state)
{
    if (state == Qt::Checked)
    {
        this->ui->acqTimespinBox->setEnabled(true);
    }
    else
    {
        this->ui->acqTimespinBox->setEnabled(false);
    }
}

void SettingsWidget::on_applyButton_clicked()
{
    if (this->sensorIDtoAnaloEntry.count() != 0) {

        QJsonDocument json;
        this->writeJson(json);

        QFile saveFile(m_saveFilePath);

        if (!saveFile.open(QIODevice::WriteOnly))
        {
            qWarning("Couldn't open save.json file.");
        }

        saveFile.write(json.toJson());
        saveFile.close();
        this->close();

        QSettings settings(QSettings::IniFormat, QSettings::UserScope, "GIPSA-LAB", "ClimbCap");

        const auto acqtime = this->ui->acqTimespinBox->value();
        settings.setValue("acquisition_time", acqtime);

        const auto triggerEnable = this->ui->checkBox->isChecked();
        settings.setValue("trigger_enable", triggerEnable);

        const auto sampleRate = this->ui->FACQSpinBox->value();
        settings.setValue("sample_rate", sampleRate);

        const auto sample_Calibration_Number = this->ui->CalibrationSampleSpinBox->value();
        settings.setValue("sample_calibration_number", sample_Calibration_Number);
       
        settings.sync();

        emit this->newConfigFile();
    }
}

void SettingsWidget::on_loadpushButton_clicked()
{
    this->loadJson();
}
