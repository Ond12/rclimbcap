#include <QApplication>
#include <QtCore>
#include <Qdir>
#include "dataProcessing.h"
#include "nidaqmxconnectionthread.h"

#include "mainwindow.h"
#include "console.h"

static QPointer<QFile> log_file = nullptr;
QPointer<QSettings> global_settings = nullptr;

void myMessageOutput(QtMsgType type, const QMessageLogContext& context, const QString& msg)
{
    if (MainWindow::m_console == 0)
    {
        QByteArray localMsg = msg.toLocal8Bit();
        switch (type) {
        case QtDebugMsg:
            fprintf(stderr, "Debug: %s (%s:%u, %s)\n", localMsg.constData(), context.file, context.line, context.function);
            break;
        case QtWarningMsg:
            fprintf(stderr, "Warning: %s (%s:%u, %s)\n", localMsg.constData(), context.file, context.line, context.function);
            break;
        case QtCriticalMsg:
            fprintf(stderr, "Critical: %s (%s:%u, %s)\n", localMsg.constData(), context.file, context.line, context.function);
            break;
        case QtFatalMsg:
            fprintf(stderr, "Fatal: %s (%s:%u, %s)\n", localMsg.constData(), context.file, context.line, context.function);
            abort();
        }
    }
    else
    {
        switch (type) {
        case QtDebugMsg:
        case QtWarningMsg:
        case QtCriticalMsg:

            if (log_file)
            {
                log_file->write(msg.toLatin1());
                log_file->write("\n");
                log_file->flush();
            }

            if (MainWindow::m_console != 0)
            {
                emit MainWindow::s_emitter.append_log(msg);
            }

            break;
        case QtFatalMsg:
            abort();
        }
    }
}

int main(int argc, char** argv)
{
    qInstallMessageHandler(myMessageOutput);

    //QDir::setCurrent("..");
    qDebug() << "Dossier courant :" << QDir::currentPath();
   
    if (!QDir("../data/").exists())
    {
        if (!QDir().mkdir("../data/"))
        {
            qDebug("Le dossier 'data' est manquant");
            return 0;
        }
    }

    QFile file("../data/log.txt");

    log_file = &file;

    if (!log_file->open(QFile::WriteOnly | QFile::Text | QFile::Truncate))
    {
        qInstallMessageHandler(nullptr);
        qDebug() << "Erreur fichier log";
    }

    QApplication a(argc, argv);

    QCoreApplication::setOrganizationName("GIPSA-LAB");
    QCoreApplication::setOrganizationDomain("https://www.gipsa-lab.grenoble-inp.fr/");
    QCoreApplication::setApplicationName("ClimbCap");

    MainWindow w;
    w.show();

    return a.exec();
}
