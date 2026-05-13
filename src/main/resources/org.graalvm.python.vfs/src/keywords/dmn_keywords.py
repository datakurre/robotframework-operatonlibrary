from robot.api.deco import keyword
from typing import Any

from keywords.base import Variables, except_interop_exception


class DmnKeywords:

    def __init__(self, ctx: Any):
        self.ctx = ctx

    @keyword
    @except_interop_exception
    def evaluate_decision(self, decision_key: str, **variables: Any) -> Any:
        """Evaluates a deployed DMN decision by key with the given input variables.

        Returns the full decision result as a list of dictionaries.
        Each entry in the list represents a matched rule's output values.

        Example usage in Robot::

            Deploy Resources    ${CURDIR}${/}discount.dmn
            ${result}=    Evaluate Decision    discount    customerType=gold    orderTotal=1500
        """
        assert self.ctx.engine, "No engine"
        decision_service = self.ctx.engine.getDecisionService()
        builder = decision_service.evaluateDecisionByKey(decision_key)
        if variables:
            var_map = Variables.createVariables()
            for name, value in variables.items():
                var_map.putValue(name, value)
            builder = builder.variables(var_map)
        dmn_result = builder.evaluate()
        result = []
        for i in range(dmn_result.size()):
            entry = dmn_result.get(i)
            row = {}
            entry_map = entry.getEntryMap()
            for key in entry_map.keySet():
                row[str(key)] = entry_map.get(key)
            result.append(row)
        return result

    @keyword
    @except_interop_exception
    def evaluate_decision_table(self, decision_key: str, **variables: Any) -> Any:
        """Evaluates a deployed DMN decision table by key with the given input variables.

        Returns the decision table result as a list of dictionaries.
        Use this when you specifically want to evaluate a decision table
        (as opposed to a literal expression or DRG).

        Example usage in Robot::

            Deploy Resources    ${CURDIR}${/}discount.dmn
            ${result}=    Evaluate Decision Table    discount    customerType=gold
        """
        assert self.ctx.engine, "No engine"
        decision_service = self.ctx.engine.getDecisionService()
        builder = decision_service.evaluateDecisionTableByKey(decision_key)
        if variables:
            var_map = Variables.createVariables()
            for name, value in variables.items():
                var_map.putValue(name, value)
            builder = builder.variables(var_map)
        dmn_result = builder.evaluate()
        result = []
        for i in range(dmn_result.size()):
            entry = dmn_result.get(i)
            row = {}
            entry_map = entry.getEntryMap()
            for key in entry_map.keySet():
                row[str(key)] = entry_map.get(key)
            result.append(row)
        return result

    @keyword
    @except_interop_exception
    def decision_result_should_contain(self, result: Any, output_name: str, expected_value: Any):
        """Asserts that at least one row in the decision result contains
        the expected value for the given output name.

        Example usage in Robot::

            ${result}=    Evaluate Decision    discount    customerType=gold
            Decision Result Should Contain    ${result}    discountPercent    15
        """
        values = [row.get(output_name) for row in result if output_name in row]
        matched = False
        for v in values:
            if str(v) == str(expected_value):
                matched = True
                break
        assert matched, (
            f"Expected output '{output_name}' to contain '{expected_value}', "
            f"but got values: {values}"
        )

    @keyword
    @except_interop_exception
    def decision_single_result(self, result: Any) -> Any:
        """Returns the single result row from a decision result.

        Asserts that exactly one rule matched.

        Example usage in Robot::

            ${result}=    Evaluate Decision    discount    customerType=gold
            ${row}=    Decision Single Result    ${result}
        """
        assert len(result) == 1, (
            f"Expected exactly 1 matched rule, but got {len(result)}: {result}"
        )
        return result[0]

    @keyword
    @except_interop_exception
    def decision_single_entry(self, result: Any) -> Any:
        """Returns the single output value from a decision result with exactly
        one matched rule and one output column.

        Example usage in Robot::

            ${result}=    Evaluate Decision    discount    customerType=gold
            ${discount}=    Decision Single Entry    ${result}
            Should Be Equal As Numbers    ${discount}    15
        """
        assert len(result) == 1, (
            f"Expected exactly 1 matched rule, but got {len(result)}: {result}"
        )
        row = result[0]
        assert len(row) == 1, (
            f"Expected exactly 1 output column, but got {len(row)}: {row}"
        )
        return next(iter(row.values()))

    @keyword
    @except_interop_exception
    def collect_entries(self, result: Any, output_name: str) -> Any:
        """Returns all values of a specific output column from a decision result.

        Extracts the value of the given output column from each matched rule.

        Example usage in Robot::

            ${result}=    Evaluate Decision    benefits    customerType=gold    orderTotal=${total}
            ${benefits}=    Collect Entries    ${result}    benefit
        """
        return [row[output_name] for row in result if output_name in row]

    @keyword
    @except_interop_exception
    def should_have_decision_definition(self, decision_key: str) -> str:
        """Asserts that a decision definition with the given key is deployed.

        Returns the decision definition ID.

        Example usage in Robot::

            Deploy Resources    ${CURDIR}${/}discount.dmn
            Should Have Decision Definition    discount
        """
        assert self.ctx.engine, "No engine"
        repository = self.ctx.engine.getRepositoryService()
        query = repository.createDecisionDefinitionQuery() \
            .decisionDefinitionKey(decision_key)
        result = query.singleResult()
        assert result is not None, (
            f"Decision definition '{decision_key}' not found"
        )
        return str(result.getId())
