
from .expressionevaluator import ExpressionEvaluator

class Expression:

    def __init__(self, expression: str, default_value=None) -> None:
        self.__expr = ExpressionEvaluator.parse(expression)
        self.__evaluator = ExpressionEvaluator()
        self.__default_value = default_value

    @property
    def context(self):
        return self.__evaluator.names

    def evaluate(self, **kwargs: 'Any') -> 'Any':

        self.__evaluator.names = kwargs

        try:
            return self.__evaluator.eval(self.__expr, parsed_expr=True)
        except Exception:
            return self.__default_value

class Condition(Expression):

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs, default_value=False)

    def evaluate(self, *args, **kwargs) -> 'Any':
        return bool(super().evaluate(*args, **kwargs))
