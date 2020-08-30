
from typing import TYPE_CHECKING

from .expressionevaluator import ExpressionEvaluator

if TYPE_CHECKING:
    from typing import Any, Dict

class Expression:

    def __init__(self, expression: str, default_value: 'Any' = None) -> None:
        self.__expr = ExpressionEvaluator.parse(expression)
        self.__evaluator = ExpressionEvaluator()
        self.__default_value = default_value

    @property
    def context(self) -> 'Dict[str, Any]':
        return self.__evaluator.names

    def evaluate(self, **kwargs: 'Any') -> 'Any':

        self.__evaluator.names = kwargs

        try:
            return self.__evaluator.eval(self.__expr, parsed_expr=True)
        except Exception:
            return self.__default_value

class Condition(Expression):

    def __init__(self, expression: str, default_value: bool = False) -> None:
        super().__init__(expression, default_value=default_value)

    def evaluate(self, **kwargs: 'Any') -> 'Any':
        return bool(super().evaluate(**kwargs))
