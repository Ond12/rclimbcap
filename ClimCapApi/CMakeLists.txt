cmake_minimum_required(VERSION 3.14)

if (WIN32)
    project(MY_PROJECT LANGUAGES CXX)
elseif(UNIX)
    project(MY_PROJECT)
endif()

set(CMAKE_CONFIGURATION_TYPES "Release;RelWithDebInfo" CACHE STRING "" FORCE)

# ###########################################################################

#======================= INCLUSION OF Qt =======================#
set(CMAKE_INCLUDE_CURRENT_DIR ON)
set(CMAKE_AUTOMOC ON)
set(CMAKE_AUTOUIC ON)
set(CMAKE_AUTORCC ON)
set(CMAKE_PREFIX_PATH $ENV{QTDIR})

find_package(Qt6Core REQUIRED)
find_package(Qt6Widgets REQUIRED)
find_package(Qt6Network REQUIRED)
find_package(Qt6PrintSupport REQUIRED)
find_package(Qt6SerialPort REQUIRED) 

#====================== INCLUSION OF NIDAQMX ======================#
find_library(NIDAQMX_LIBRARY
	NAMES
	NIDAQmx
	PATHS
	"C:/Program Files (x86)/National Instruments/Shared/ExternalCompilerSupport/C/lib64/msvc")

find_path(NIDAQMX_INCLUDE_DIR
	  NAMES
	  NIDAQmx.h
	  PATHS
	  "C:/Program Files (x86)/National Instruments/Shared/ExternalCompilerSupport/C/include")

include(FindPackageHandleStandardArgs)
find_package_handle_standard_args(NIDAQmx
	DEFAULT_MSG
	NIDAQMX_LIBRARY
	NIDAQMX_INCLUDE_DIR)

if(NIDAQMX_FOUND)
	set(NIDAQMX_LIBRARIES "${NIDAQMX_LIBRARY}")

	set(NIDAQMX_INCLUDE_DIRS "${NIDAQMX_INCLUDE_DIR}")
endif()


mark_as_advanced(NIDAQMX_INCLUDE_DIR NIDAQMX_LIBRARY)
include_directories(${NIDAQMX_INCLUDE_DIRS})


#=================== INCLUSION OF Project Files ====================#

set(FORMS_DIR "${CMAKE_SOURCE_DIR}/forms")
set(INCLUDE_DIR "${CMAKE_SOURCE_DIR}/include")
set(SOURCE_DIR "${CMAKE_SOURCE_DIR}/src")

include_directories(${INCLUDE_DIR})
include_directories(${SOURCE_DIR})

file(GLOB_RECURSE SOURCES

    "${FORMS_DIR}/*.ui"
    "${FORMS_DIR}/*.qrc"
    "${INCLUDE_DIR}/*.h"
    "${SOURCE_DIR}/*.cpp"
)

#=================== SETUP EXECTUABLE ====================#
# Enable debug logging on RELWITHDEBINFO configuration
set_property(DIRECTORY APPEND PROPERTY COMPILE_DEFINITIONS
    $<$<CONFIG:RELWITHDEBINFO>:QT_MESSAGELOGCONTEXT>
)

# Add the forms directory to the AUTOUIC search paths
set(CMAKE_AUTOUIC_SEARCH_PATHS ${CMAKE_AUTOUIC_SEARCH_PATHS} ${FORMS_DIR})

# Add the executable
if (WIN32) 
    add_executable(MY_PROJECT WIN32 ${SOURCES})
elseif(UNIX)
    add_executable(MY_PROJECT ${SOURCES})
endif()

# Add the target includes for MY_PROJECT 
target_include_directories(MY_PROJECT PRIVATE ${FORMS_DIR})
target_include_directories(MY_PROJECT PRIVATE ${INCLUDE_DIR})
target_include_directories(MY_PROJECT PRIVATE ${SOURCE_DIR})

target_include_directories(MY_PROJECT PRIVATE ${NIDAQMX_INCLUDE_DIRS})
target_include_directories(MY_PROJECT PRIVATE ${NIDAQMX_LIBRARY})

#===================== LINKING LIBRARIES =======================#
target_link_libraries(MY_PROJECT Qt6::Core)
target_link_libraries(MY_PROJECT Qt6::Widgets)
target_link_libraries(MY_PROJECT Qt6::Network)
target_link_libraries(MY_PROJECT Qt6::PrintSupport)
target_link_libraries(MY_PROJECT Qt6::SerialPort)

target_link_libraries(MY_PROJECT ${NIDAQMX_LIBRARY})




