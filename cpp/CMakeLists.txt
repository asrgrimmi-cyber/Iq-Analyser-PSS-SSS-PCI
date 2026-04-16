cmake_minimum_required(VERSION 3.10)
project(LteIqAnalyzer CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Source files
set(KISS_FFT_SRCS deps/kissfft/kiss_fft.c)
set(ENGINE_SRCS LteEngine.cpp)

# Header include paths
include_directories(.)
include_directories(deps/kissfft)

# Create a shared library for the Python bridge
add_library(lte_engine SHARED ${ENGINE_SRCS} ${KISS_FFT_SRCS} bridge.cpp)

# Create a standalone CLI tool
add_executable(iq_analyzer main.cpp ${ENGINE_SRCS} ${KISS_FFT_SRCS})

# Compiler flags for speed
if(MSVC)
    add_compile_options(/O2 /Oi /Ot)
else()
    add_compile_options(-O3 -march=native)
endif()
