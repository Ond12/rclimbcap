#ifndef SETTINGSWIDGET_H
#define SETTINGSWIDGET_H

#include <QWidget>
#include <QMap>
#include <QJsonObject>
#include <QJsonDocument>
#include <QVariantMap>
#include <QFile>
#include <QJsonArray>
#include <QDialog>

namespace Ui {
class SettingsWidget;
}

class SettingsWidget : public QDialog
{
    Q_OBJECT

public:
    explicit SettingsWidget(QWidget *parent = nullptr);
    ~SettingsWidget();

private slots:
    void on_resestButton_clicked();
    void on_addPushButton_clicked();
    void on_applyButton_clicked();
    void on_loadpushButton_clicked();
    void onCheckboxStateChanged(int state);

private:
    Ui::SettingsWidget *ui;
    QMap<int,int> sensorIDtoAnaloEntry;

    void setUpComboBox();
    void writeJson(QJsonDocument &json) const;
    bool loadJson();
    QString m_saveFilePath;

    void addNewSensorToTable(uint sensorid, QString sensorname, uint sensorChannel, double sensorAngle, double sensorZRotation, bool isFlip);

    bool loadConfing();

signals:
    void newConfigFile();
};

#endif // SETTINGSWIDGET_H
