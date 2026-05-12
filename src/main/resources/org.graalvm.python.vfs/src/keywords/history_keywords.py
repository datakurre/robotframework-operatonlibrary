from robot.api.deco import keyword
from typing import Any

from keywords.base import except_interop_exception


class HistoryKeywords:

    def __init__(self, ctx: Any):
        self.ctx = ctx

    @keyword
    @except_interop_exception
    def get_completed_instances(self, process_definition_key: str = "") -> Any:
        """Returns a list of completed historic process instances."""
        assert self.ctx.engine, "No engine"
        history = self.ctx.engine.getHistoryService()
        query = history.createHistoricProcessInstanceQuery().finished()
        if process_definition_key:
            query = query.processDefinitionKey(process_definition_key)
        return query.list()

    @keyword
    @except_interop_exception
    def get_historic_variables(self, process_instance_id: str) -> Any:
        """Returns historic variable instances as a dict."""
        assert self.ctx.engine, "No engine"
        history = self.ctx.engine.getHistoryService()
        variables = history.createHistoricVariableInstanceQuery() \
            .processInstanceId(process_instance_id).list()
        result = {}
        for i in range(int(variables.size())):
            var = variables.get(i)
            result[str(var.getName())] = var.getValue()
        return result
