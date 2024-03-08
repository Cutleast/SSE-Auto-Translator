cmake_minimum_required(VERSION 3.21)
project(merger VERSION 1.0.0 LANGUAGES CXX)

# Set your project version and specify C++ standard
set(CMAKE_CXX_STANDARD 23)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set_property(GLOBAL PROPERTY USE_FOLDERS ON)

# Enable interprocedural optimization
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION ON)
set(CMAKE_INTERPROCEDURAL_OPTIMIZATION_DEBUG OFF)

# Set Boost options
set(Boost_USE_STATIC_LIBS ON)
set(Boost_USE_STATIC_RUNTIME ON)

#pdb
set(CMAKE_CXX_FLAGS_RELEASE "${CMAKE_CXX_FLAGS_RELEASE} /Zi")
set(CMAKE_SHARED_LINKER_FLAGS_RELEASE "${CMAKE_SHARED_LINKER_FLAGS_RELEASE} /DEBUG /OPT:REF /OPT:ICF")

# MSVC-specific settings
if (CMAKE_GENERATOR MATCHES "Visual Studio")
    add_compile_definitions(_UNICODE)

    # Set compiler definitions for debug and release builds
    target_compile_definitions("${PROJECT_NAME}" PRIVATE "$<$<CONFIG:DEBUG>:DEBUG>")
    
    # Compiler and linker options
    set(SC_RELEASE_OPTS "/Zi;/fp:fast;/GL;/Gy-;/Gm-;/Gw;/sdl-;/GS-;/guard:cf-;/O2;/Ob2;/Oi;/Ot;/Oy;/fp:except-")
    
    target_compile_options("${PROJECT_NAME}" PRIVATE
        /MP /await /W4 /WX /permissive- /Zc:alignedNew /Zc:auto /Zc:__cplusplus /Zc:externC /Zc:externConstexpr
        /Zc:forScope /Zc:hiddenFriend /Zc:implicitNoexcept /Zc:lambda /Zc:noexceptTypes /Zc:preprocessor /Zc:referenceBinding
        /Zc:rvalueCast /Zc:sizedDealloc /Zc:strictStrings /Zc:ternary /Zc:threadSafeInit /Zc:trigraphs /Zc:wchar_t
        /wd4200 # nonstandard extension used: zero-sized array in struct/union
    )
    
    target_compile_options("${PROJECT_NAME}" PUBLIC "$<$<CONFIG:DEBUG>:/fp:strict>")
    target_compile_options("${PROJECT_NAME}" PUBLIC "$<$<CONFIG:DEBUG>:/ZI>")
    target_compile_options("${PROJECT_NAME}" PUBLIC "$<$<CONFIG:DEBUG>:/Od>")
    target_compile_options("${PROJECT_NAME}" PUBLIC "$<$<CONFIG:DEBUG>:/Gy>")
    target_compile_options("${PROJECT_NAME}" PUBLIC "$<$<CONFIG:RELEASE>:${SC_RELEASE_OPTS}>")
    
    target_link_options("${PROJECT_NAME}" PRIVATE
        /WX
        "$<$<CONFIG:DEBUG>:/INCREMENTAL;/OPT:NOREF;/OPT:NOICF>"
        "$<$<CONFIG:RELEASE>:/LTCG;/INCREMENTAL:NO;/OPT:REF;/OPT:ICF;/DEBUG:FULL>"
    )
endif()


# Find required packages (adjust as needed)
find_package(nlohmann_json CONFIG REQUIRED)
find_package(unordered_dense CONFIG REQUIRED)

set(SRC "${CMAKE_SOURCE_DIR}/src")
file(GLOB sources ${SRC}/*.cpp)
add_executable(merger ${sources})

# Link libraries
target_link_libraries(merger PRIVATE nlohmann_json::nlohmann_json unordered_dense::unordered_dense)


# Add generated files to the target
configure_file("${CMAKE_CURRENT_SOURCE_DIR}/cmake/version.rc.in" "${CMAKE_CURRENT_BINARY_DIR}/cmake/version.rc" @ONLY)
target_sources(merger PRIVATE ${CMAKE_CURRENT_BINARY_DIR}/cmake/version.rc)

# Configure MSVC-specific settings for C++23
if(MSVC_VERSION GREATER_EQUAL 1936 AND MSVC_IDE) # 17.6+
    file(CONFIGURE OUTPUT "${CMAKE_BINARY_DIR}/Directory.Build.props" CONTENT [==[
    <Project>
      <ItemDefinitionGroup>
        <ClCompile>
          <BuildStlModules>false</BuildStlModules>
        </ClCompile>
      </ItemDefinitionGroup>
    </Project>
    ]==] @ONLY)
endif()