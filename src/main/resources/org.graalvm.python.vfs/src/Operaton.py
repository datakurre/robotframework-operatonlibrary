from robot.api.deco import keyword
from pathlib import Path
from typing import Any

import os
import uuid

from robotlibcore import DynamicCore

from keywords.base import Variables, except_interop_exception
from keywords.process_assertions import ProcessAssertions
from keywords.event_keywords import EventKeywords
from keywords.history_keywords import HistoryKeywords
from keywords.dmn_keywords import DmnKeywords
from keywords.typed_variables import TypedVariables
from keywords.timer_keywords import TimerKeywords
from keywords.external_task_keywords import ExternalTaskKeywords
from keywords.bpmn_keywords import BpmnKeywords
from keywords.form_keywords import FormKeywords

try:
    import java  # pyright: ignore
except ImportError:
    # Fix typechecks outside graalpy
    class java:
        @staticmethod
        def type(klass: str) -> Any:
            pass


ProcessEngineConfiguration = (
    java.type("org.operaton.bpm.engine.ProcessEngineConfiguration"))
assertThat: Any = (
    getattr(java.type("org.operaton.bpm.engine.test.assertions.bpmn.BpmnAwareTests"), "assertThat", None))

try:
    _SpinPlugin = java.type("org.operaton.spin.plugin.impl.SpinProcessEnginePlugin")
except Exception:
    _SpinPlugin = None

try:
    _VasaraPlugin = java.type("fi.jyu.vasara.VasaraPlugin")
except Exception:
    _VasaraPlugin = None


class Operaton(DynamicCore):
    ROBOT_LIBRARY_SCOPE = "GLOBAL"

    engine: Any = None
    _current_instance_id: str = ""
    _current_business_key: str = ""

    def __init__(self):
        components = [
            ProcessAssertions(self),
            EventKeywords(self),
            HistoryKeywords(self),
            DmnKeywords(self),
            TypedVariables(self),
            TimerKeywords(self),
            ExternalTaskKeywords(self),
            BpmnKeywords(self),
            FormKeywords(self),
        ]
        DynamicCore.__init__(self, components)

    @keyword
    @except_interop_exception
    def setup_process_engine(self) -> Any:
        if self.engine is None:
            config = (
                ProcessEngineConfiguration.createStandaloneInMemProcessEngineConfiguration()
                .setHistory(ProcessEngineConfiguration.HISTORY_FULL)
                .setHostname("localhost")
            )
            # Always register the Spin plugin so JSON/XML serialization is available.
            if _SpinPlugin is not None:
                config.getProcessEnginePlugins().add(_SpinPlugin())
            # When running from the vasara fat JAR, activate Vasara form customizations
            # automatically by classpath-presence of fi.jyu.vasara.VasaraPlugin.
            if _VasaraPlugin is not None:
                config.getProcessEnginePlugins().add(_VasaraPlugin())
            self.engine = config.buildProcessEngine()
        return self.engine

    def _resolve_instance_id(self, process_instance_id: str = "") -> str:
        """Return the effective process instance ID.

        Resolution order:
        1. Explicit ``process_instance_id`` argument (if non-empty).
        2. The current instance stored in ``_current_instance_id``.
        3. Query all active/historic instances with ``_current_business_key``
           (exactly 1 must match).
        """
        if process_instance_id:
            return process_instance_id
        if self._current_instance_id:
            return self._current_instance_id
        if self._current_business_key:
            assert self.engine, "No engine"
            # Try runtime (active) first
            runtime = self.engine.getRuntimeService()
            results = (runtime.createProcessInstanceQuery()
                       .processInstanceBusinessKey(self._current_business_key)
                       .list())
            count = int(results.size())
            if count == 1:
                return str(results.get(0).getId())
            if count > 1:
                raise AssertionError(
                    f"Multiple active instances share business key "
                    f"'{self._current_business_key}' — please pass process_instance_id explicitly"
                )
            # Fall back to history (ended instances)
            history = self.engine.getHistoryService()
            hist_results = (history.createHistoricProcessInstanceQuery()
                            .processInstanceBusinessKey(self._current_business_key)
                            .list())
            hist_count = int(hist_results.size())
            if hist_count == 1:
                return str(hist_results.get(0).getId())
            if hist_count > 1:
                raise AssertionError(
                    f"Multiple historic instances share business key "
                    f"'{self._current_business_key}' — please pass process_instance_id explicitly"
                )
        raise AssertionError(
            "No process_instance_id given and no current instance in scope. "
            "Call 'Start Instance' first, or pass process_instance_id explicitly."
        )

    def _resolve_task_key(self, instance_id: str, key_or_name: str) -> str:
        """Return the task definition key for *key_or_name* within *instance_id*.

        If *key_or_name* matches a task by definition key, it is returned unchanged.
        Otherwise it is treated as a task **name**: exactly one task must have that
        name, and its definition key is returned. If multiple tasks share the name,
        an error is raised.
        """
        if not key_or_name:
            return ""
        assert self.engine, "No engine"
        task_service = self.engine.getTaskService()
        by_key = (task_service.createTaskQuery()
                  .processInstanceId(instance_id)
                  .taskDefinitionKey(key_or_name)
                  .list())
        if int(by_key.size()) > 0:
            # It's already a definition key
            return key_or_name
        # Try matching by name
        by_name = (task_service.createTaskQuery()
                   .processInstanceId(instance_id)
                   .taskName(key_or_name)
                   .list())
        name_count = int(by_name.size())
        assert name_count > 0, (
            f"No task with definition key or name '{key_or_name}' "
            f"found for instance '{instance_id}'"
        )
        assert name_count == 1, (
            f"Ambiguous task name '{key_or_name}': {name_count} tasks match "
            f"for instance '{instance_id}' — use the definition key instead"
        )
        return str(by_name.get(0).getTaskDefinitionKey())

    @keyword
    @except_interop_exception
    def teardown_process_engine(self):
        self.engine.close()
        self.engine = None
        self._current_instance_id = ""
        self._current_business_key = ""

    @keyword
    @except_interop_exception
    def deploy_resources(self, *paths: str, name: str = "Test Deployment") -> str:
        """Deploys BPMN/DMN resources to the engine.

        Returns the deployment ID.
        """
        assert self.engine, "No engine"
        repository = self.engine.getRepositoryService()
        deployment = repository.createDeployment()
        for path in paths:
            deployment.addString(
                os.path.basename(path),
                Path(path).read_text(),
            )
        deployment.name(name)
        result = deployment.deploy()
        return str(result.getId())

    @keyword
    @except_interop_exception
    def get_current_instance(self) -> str:
        """Returns the ID of the current process instance set by the last Start Instance call."""
        return self._current_instance_id

    @keyword
    @except_interop_exception
    def get_current_business_key(self) -> str:
        """Returns the business key of the current process instance."""
        return self._current_business_key

    @keyword
    @except_interop_exception
    def start_instance(self, process_definition_key: str, business_key: str = "") -> str:
        """Starts a process instance and stores it as the current instance.

        If *business_key* is not provided, a UUID4 is generated automatically.
        The instance ID and business key are stored in test scope state and used
        automatically by subsequent keywords that accept ``process_instance_id``.
        """
        assert self.engine, "No engine"
        if not business_key:
            business_key = str(uuid.uuid4())
        runtime = self.engine.getRuntimeService()
        instance = runtime.startProcessInstanceByKey(process_definition_key, business_key)
        assertThat(instance).isStarted()
        self._current_instance_id = str(instance.getId())
        self._current_business_key = business_key
        return self._current_instance_id

    @keyword
    @except_interop_exception
    def should_have_task(self, process_instance_id: str = "", task_defintion_key: str = ""):
        """Asserts that the process instance has an active task with the given definition key or name.

        Both ``process_instance_id`` and ``task_defintion_key`` can be omitted when a
        current instance is in scope (set by ``Start Instance``).
        The task may be identified by its definition key *or* by its human-readable name.
        """
        assert self.engine, "No engine"
        instance_id = self._resolve_instance_id(process_instance_id)
        resolved_key = self._resolve_task_key(instance_id, task_defintion_key)
        runtime = self.engine.getRuntimeService()
        query = runtime.createProcessInstanceQuery()
        query.processInstanceId(instance_id)
        instance = query.singleResult()
        assertThat(instance).task().hasDefinitionKey(resolved_key)

    @keyword
    @except_interop_exception
    def complete_task(self, process_instance_id: str = "", task_definition_key: str = "", variables: Any = None):
        """Completes the active user task for the process instance.

        ``process_instance_id`` defaults to the current instance in scope.
        ``task_definition_key`` may be a definition key *or* a human-readable task name.
        When omitted (and only one task is active), that task is completed.
        """
        assert self.engine, "No engine"
        instance_id = self._resolve_instance_id(process_instance_id)
        resolved_key = self._resolve_task_key(instance_id, task_definition_key)
        task_service = self.engine.getTaskService()
        query = task_service.createTaskQuery().processInstanceId(instance_id)
        if resolved_key:
            query = query.taskDefinitionKey(resolved_key)
        task = query.singleResult()
        assert task, f"No task found for instance {instance_id}"
        if variables:
            task_service.complete(task.getId(), variables)
        else:
            task_service.complete(task.getId())

    @keyword
    @except_interop_exception
    def get_variable(self, process_instance_id: str = "", variable_name: str = "") -> Any:
        """Returns the value of a process variable. Defaults to the current instance."""
        assert self.engine, "No engine"
        instance_id = self._resolve_instance_id(process_instance_id)
        runtime = self.engine.getRuntimeService()
        return runtime.getVariable(instance_id, variable_name)

    @keyword
    @except_interop_exception
    def set_variable(self, process_instance_id: str = "", variable_name: str = "", variable_value: Any = None):
        """Sets a process variable. Defaults to the current instance."""
        assert self.engine, "No engine"
        instance_id = self._resolve_instance_id(process_instance_id)
        runtime = self.engine.getRuntimeService()
        runtime.setVariable(instance_id, variable_name, variable_value)

    @keyword
    @except_interop_exception
    def get_tasks(self, process_instance_id: str = "") -> list:
        """Returns all active tasks for the process instance as a list of dicts.

        Each dict has: id, name, taskDefinitionKey, assignee.
        Defaults to the current instance in scope.
        """
        assert self.engine, "No engine"
        instance_id = self._resolve_instance_id(process_instance_id)
        task_service = self.engine.getTaskService()
        tasks = task_service.createTaskQuery().processInstanceId(instance_id).list()
        result = []
        for i in range(int(tasks.size())):
            task = tasks.get(i)
            result.append({
                "id": str(task.getId()),
                "name": str(task.getName()) if task.getName() else None,
                "taskDefinitionKey": str(task.getTaskDefinitionKey()),
                "assignee": str(task.getAssignee()) if task.getAssignee() else None,
            })
        return result

    @keyword
    @except_interop_exception
    def start_instance_with_variables(self, process_definition_key: str, business_key: str = "", **variables: Any) -> str:
        """Starts a process instance with the given variables and stores it as the current instance.

        If *business_key* is not provided, a UUID4 is generated automatically.
        """
        assert self.engine, "No engine"
        if not business_key:
            business_key = str(uuid.uuid4())
        runtime = self.engine.getRuntimeService()
        if variables:
            var_map = Variables.createVariables()
            for name, value in variables.items():
                var_map.putValue(name, value)
            instance = runtime.startProcessInstanceByKey(process_definition_key, business_key, var_map)
        else:
            instance = runtime.startProcessInstanceByKey(process_definition_key, business_key)
        assertThat(instance).isStarted()
        self._current_instance_id = str(instance.getId())
        self._current_business_key = business_key
        return self._current_instance_id
