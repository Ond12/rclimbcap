#pragma once
namespace globals
{
	constexpr auto  MATRICES_FILES_PATH = "../data/calibration_matrices";
	constexpr auto  CONFIG_FILE_PATH = "../data/save.json";

	constexpr auto  DEFAULT_SAMPLE_RATE = 200;

	constexpr auto  DEFAULT_ACQ_TIME = 200;

	constexpr auto  DEFAULT_TRIGGER_SETTING = 0;
	constexpr auto  DEFAULT_SAMPLE_CALIBRATION_NUMBER = 1000;

	constexpr auto  ENABLE_PLATFORM = true;
	constexpr auto  ENABLE_SENSOR = false;

	//NIDAQmx globals
	constexpr auto IMPORT_SAMPLE_CLOCK_PIN = "PFI0";
	constexpr auto IMPORT_START_TRIGGER_PIN = "PFI1";
	constexpr auto EXPORT_SAMPLE_CLOCK_PIN = "PFI4";
	constexpr auto EXPORT_START_TRIGGER_PIN = "PFI5";
	constexpr auto CHRONO_PULSE_PIN = 72;

	constexpr auto SENSOR_ACQ_CARD_NAME = "Dev2";
	constexpr auto PLATFORM_ACQ_CARD_NAME = "Dev2";//"Dev3";

	//Debug globals

	constexpr auto DEBUG_MOD_PLATFORM = true;
	constexpr auto DEBUG_MOD_SENSOR = false;

	constexpr auto DUMMY_SENDER = false;
}