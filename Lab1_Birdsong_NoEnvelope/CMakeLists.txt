# == DO NOT EDIT THE FOLLOWING LINES for the Raspberry Pi Pico VS Code Extension to work ==
if(WIN32)
    set(USERHOME $ENV{USERPROFILE})
else()
    set(USERHOME $ENV{HOME})
endif()
set(sdkVersion 2.3.0)
set(toolchainVersion 15_2_Rel1)
set(picotoolVersion 2.3.0)
set(picoVscode ${USERHOME}/.pico-sdk/cmake/pico-vscode.cmake)
if (EXISTS ${picoVscode})
    include(${picoVscode})
endif()
# ====================================================================================
set(PICO_BOARD pico2 CACHE STRING "Board type")

# cmake version
cmake_minimum_required(VERSION 3.13)

# include the sdk.cmake file
include(pico_sdk_import.cmake)

# give the project a name (anything you want)
project(birdsong_no_envelope C CXX ASM)

# initialize the sdk
pico_sdk_init()

add_executable(birdsong_no_envelope birdsong_no_envelope.c ../Lab1_Birdsong_Cardinal/northern_cardinal.c)

target_sources(birdsong_no_envelope PRIVATE birdsong_no_envelope.c ../Lab1_Birdsong_Cardinal/northern_cardinal.c)

# The cardinal presets are shared with the main build, not copied.
target_include_directories(birdsong_no_envelope PRIVATE ../Lab1_Birdsong_Cardinal)

target_link_libraries(birdsong_no_envelope 
    pico_stdlib 
    pico_bootsel_via_double_reset 
    hardware_spi 
    hardware_timer 
    hardware_irq pico_bootsel_via_double_reset 
    pico_sync
    hardware_sync
    hardware_vreg
    hardware_clocks
    hardware_adc
    pico_multicore
    hardware_pio
    hardware_dma
)

pico_add_extra_outputs(birdsong_no_envelope)