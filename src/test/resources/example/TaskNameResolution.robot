*** Settings ***

Library    Operaton

*** Test Cases ***

Should Have Task By Task Name
    [Documentation]    Should Have Task accepts a human-readable task name instead of a definition key.
    [Setup]    Setup Process Engine
    [Teardown]    Teardown Process Engine
    Deploy Resources    ${CURDIR}${/}current-instance-process.bpmn
    ${instance}=    Start Instance    current-instance-process
    Should Have Task    ${instance}    Review Request

Complete Task By Task Name
    [Documentation]    Complete Task accepts a human-readable task name instead of a definition key.
    [Setup]    Setup Process Engine
    [Teardown]    Teardown Process Engine
    Deploy Resources    ${CURDIR}${/}current-instance-process.bpmn
    ${instance}=    Start Instance    current-instance-process
    Complete Task    ${instance}    Review Request
    Should Be Ended    ${instance}

Definition Key Still Works For Backward Compat
    [Documentation]    Passing the task definition key directly still works (backward compatibility).
    [Setup]    Setup Process Engine
    [Teardown]    Teardown Process Engine
    Deploy Resources    ${CURDIR}${/}current-instance-process.bpmn
    ${instance}=    Start Instance    current-instance-process
    Complete Task    ${instance}    review-request
    Should Be Ended    ${instance}

Task Name Resolution Without Explicit Instance
    [Documentation]    Task name resolution works together with current-instance state.
    [Setup]    Setup Process Engine
    [Teardown]    Teardown Process Engine
    Deploy Resources    ${CURDIR}${/}current-instance-process.bpmn
    Start Instance    current-instance-process
    Should Have Task    task_defintion_key=Review Request
    Complete Task    task_definition_key=Review Request
    Should Be Ended
