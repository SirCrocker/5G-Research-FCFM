check_include_file_cxx(stdint.h HAVE_STDINT_H)
if(HAVE_STDINT_H)
    add_definitions(-DHAVE_STDINT_H)
endif()

find_package(Boost REQUIRED COMPONENTS program_options serialization)
include_directories(${Boost_INCLUDE_DIRS})
find_package(Python REQUIRED COMPONENTS Interpreter Development)
find_package(pybind11 CONFIG REQUIRED)
include_directories(${pybind11_INCLUDE_DIRS})

find_package(PythonLibs REQUIRED)
find_package(Protobuf CONFIG)
if(NOT Protobuf_FOUND)
    find_package(Protobuf REQUIRED)
endif()
include_directories(${Protobuf_INCLUDE_DIRS})

build_exec(
      EXECNAME ns3ai_apb_msg_vec
      EXECNAME_PREFIX scratch_
      SOURCE_FILES apb.cc
      LIBRARIES_TO_LINK "${libai}"
      EXECUTABLE_DIRECTORY_PATH /home/diego/ns-3-dev/build/scratch
  )

pybind11_add_module(ns3ai_apb_py_vec apb_py.cc)
set_target_properties(ns3ai_apb_py_vec PROPERTIES
        LIBRARY_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
target_link_libraries(ns3ai_apb_py_vec PRIVATE Boost::serialization pybind11::module ${PYTHON_LIBRARIES} ${libai})