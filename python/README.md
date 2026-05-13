# robotframework-operaton

A CPython proxy package for the [Operaton Robot Framework library](https://github.com/operaton/robotframework-operaton).

This package auto-spawns the GraalPy/JVM backend as a Robot Framework Remote
Server and delegates all keyword calls over XML-RPC. It allows you to use the
Operaton library with standard CPython tools like RobotCode (VS Code extension),
`robotcode` CLI, and any other Robot Framework runner.

## Installation

```bash
pip install robotframework-operaton
```

## Prerequisites

- **Java 21+** on `PATH` (or `JAVA_HOME` set)
- The fat JAR: `operaton-bpm-extension-robot-*-fat.jar`
  - Build with: `mvn -Pshade package -DskipTests` in the main repo
  - Or download from releases

## Configuration

Set the `OPERATON_JAR` environment variable to point at the fat JAR:

```bash
export OPERATON_JAR=/path/to/operaton-bpm-extension-robot-1.0-SNAPSHOT-fat.jar
```

Or pass it as a library argument in your Robot suite:

```robot
*** Settings ***
Library    Operaton    jar=/path/to/fat.jar
```

## Usage

```robot
*** Settings ***
Library    Operaton

*** Test Cases ***
Deploy And Run
    [Setup]       Setup Process Engine
    [Teardown]    Teardown Process Engine
    Deploy Resources    ${CURDIR}${/}process.bpmn
    ${instance}=    Start Instance    my-process
    Should Have Task    ${instance}    user-task
```

## RobotCode / VS Code Integration

See the main repository's README for `robot.toml` configuration that provides
keyword discovery via `.libspec` and test execution via this proxy.
