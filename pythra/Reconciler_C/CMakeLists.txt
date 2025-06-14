cmake_minimum_required(VERSION 3.16)
project(PyThraCpp)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Framework library
add_library(framework
    framework/reconciler.cpp
)

target_include_directories(framework
    PUBLIC ${CMAKE_CURRENT_SOURCE_DIR}/framework
)

# Executable
add_executable(app main.cpp)
target_link_libraries(app PRIVATE framework)

# Optional: organize output
set_target_properties(app PROPERTIES
    RUNTIME_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/bin
)
set_target_properties(framework PROPERTIES
    ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR}/lib
)
