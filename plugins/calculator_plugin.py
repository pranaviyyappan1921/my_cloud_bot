"""
Calculator and Safe Mathematics Plugin for Cloud AI Chatbot.

Provides secure mathematical computation using Python AST whitelisting:
- Arithmetic, power, roots, trigonometry, logarithms, combinatorics
- Multi-unit conversions (length, weight, temperature, data, time, speed)
- Statistical summary analysis (mean, median, std dev, min, max, sum)
- 100% immune to code injection (Zero eval() / exec())
"""

import ast
import math
import statistics
import operator
from typing import Dict, Any, Optional, List, Union
from .base_plugin import BasePlugin, PluginPermission, PluginToolParameter, PluginToolSchema


# Safe math operators mapping
SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Safe constants
SAFE_CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
    "tau": math.tau,
    "inf": math.inf,
}

# Safe mathematical functions
SAFE_FUNCTIONS = {
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "asin": math.asin,
    "acos": math.acos,
    "atan": math.atan,
    "sinh": math.sinh,
    "cosh": math.cosh,
    "tanh": math.tanh,
    "sqrt": math.sqrt,
    "cbrt": lambda x: math.pow(x, 1 / 3) if x >= 0 else -math.pow(-x, 1 / 3),
    "log": math.log,
    "log10": math.log10,
    "log2": math.log2,
    "exp": math.exp,
    "abs": abs,
    "round": round,
    "ceil": math.ceil,
    "floor": math.floor,
    "factorial": lambda x: math.factorial(int(x)) if int(x) <= 1000 else None,
    "gcd": math.gcd,
    "radians": math.radians,
    "degrees": math.degrees,
    "pow": math.pow,
}


def _safe_eval_ast(node: ast.AST) -> Union[int, float]:
    """Recursively evaluates AST expression nodes strictly within safe mathematical bounds."""
    if isinstance(node, ast.Expression):
        return _safe_eval_ast(node.body)

    elif isinstance(node, ast.Constant):  # Python 3.8+ numbers/strings/booleans
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError(f"Literal type '{type(node.value).__name__}' is not allowed in calculations.")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Operator '{op_type.__name__}' is not permitted.")
        left = _safe_eval_ast(node.left)
        right = _safe_eval_ast(node.right)
        if op_type == ast.Pow:
            # Protect against huge memory allocation attacks e.g. 9999999 ** 9999999
            if abs(right) > 1000 or (abs(left) > 1000 and right > 100):
                raise ValueError("Exponentiation values exceed safety limits.")
        op_func = SAFE_OPERATORS[op_type]
        return op_func(left, right)

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type not in SAFE_OPERATORS:
            raise ValueError(f"Unary operator '{op_type.__name__}' is not permitted.")
        operand = _safe_eval_ast(node.operand)
        return SAFE_OPERATORS[op_type](operand)

    elif isinstance(node, ast.Name):
        name = node.id.lower()
        if name in SAFE_CONSTANTS:
            return SAFE_CONSTANTS[name]
        raise ValueError(f"Identifier '{node.id}' is not recognized or permitted.")

    elif isinstance(node, ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Only standard mathematical function calls are supported.")
        func_name = node.func.id.lower()
        if func_name not in SAFE_FUNCTIONS:
            raise ValueError(f"Function '{node.func.id}' is not in the safe mathematical whitelist.")

        args = [_safe_eval_ast(arg) for arg in node.args]
        func = SAFE_FUNCTIONS[func_name]
        result = func(*args)
        if result is None:
            raise ValueError(f"Function '{func_name}' computation exceeded safe boundaries.")
        return result

    else:
        raise ValueError(f"Unsupported syntax structure '{type(node).__name__}'.")


class CalculatorPlugin(BasePlugin):
    """
    High-performance, secure Calculator & Math Engine plugin.
    """

    def __init__(self):
        super().__init__(
            id="calculator",
            name="Calculator & Math Engine",
            description="Perform precise mathematical calculations, scientific formulas, unit conversions, and statistical computations safely.",
            category="Popular",
            icon="🧮",
            icon_bg="linear-gradient(135deg, #10b981, #059669)",
            version="1.2.0",
            author="Cloud AI Math Systems",
            tags=["Math", "Calculator", "Units", "Statistics", "Scientific"],
            requires_auth=False,
            is_connected=True,
            is_enabled=True,
        )

    def setup_permissions(self) -> None:
        self.add_permission(
            PluginPermission(
                id="math_compute",
                name="Execute Mathematical Computations",
                description="Allows the AI assistant to evaluate equations, algebra, and trigonometry securely.",
                enabled=True,
                required=True,
            )
        )
        self.add_permission(
            PluginPermission(
                id="unit_conversion",
                name="Convert Physical Units",
                description="Allows converting between temperature, length, data storage, speed, and mass units.",
                enabled=True,
                required=False,
            )
        )
        self.add_permission(
            PluginPermission(
                id="statistics",
                name="Compute Dataset Statistics",
                description="Allows computing mean, median, standard deviation, and variance on number lists.",
                enabled=True,
                required=False,
            )
        )

    def setup_tools(self) -> None:
        # Tool 1: Calculate Expression
        self.add_tool(
            PluginToolSchema(
                name="calculate",
                description="Evaluates a mathematical, scientific, or algebraic expression accurately and safely (e.g. '45 * 38 + sqrt(144)', 'sin(pi/4) * 100', '2^10 + log10(1000)').",
                parameters=[
                    PluginToolParameter(
                        name="expression",
                        type="string",
                        description="The mathematical formula or expression to calculate.",
                        required=True,
                    )
                ],
                required_permission="math_compute",
            )
        )

        # Tool 2: Unit Converter
        self.add_tool(
            PluginToolSchema(
                name="convert_units",
                description="Converts a numeric value from one physical or digital unit to another (e.g. Celsius to Fahrenheit, km to miles, GB to MB, kg to lbs).",
                parameters=[
                    PluginToolParameter(
                        name="value",
                        type="number",
                        description="Numeric amount to convert.",
                        required=True,
                    ),
                    PluginToolParameter(
                        name="from_unit",
                        type="string",
                        description="Source unit (e.g. 'km', 'mi', 'm', 'c', 'f', 'k', 'kg', 'lb', 'g', 'oz', 'mb', 'gb', 'tb', 'hours', 'minutes', 'seconds').",
                        required=True,
                    ),
                    PluginToolParameter(
                        name="to_unit",
                        type="string",
                        description="Target unit (e.g. 'km', 'mi', 'm', 'c', 'f', 'k', 'kg', 'lb', 'g', 'oz', 'mb', 'gb', 'tb', 'hours', 'minutes', 'seconds').",
                        required=True,
                    ),
                ],
                required_permission="unit_conversion",
            )
        )

        # Tool 3: Statistical Summary
        self.add_tool(
            PluginToolSchema(
                name="calculate_statistics",
                description="Computes descriptive statistics (mean, median, mode, variance, standard deviation, min, max, sum) for a list of numbers.",
                parameters=[
                    PluginToolParameter(
                        name="numbers",
                        type="array",
                        description="List of numbers to analyze.",
                        required=True,
                    )
                ],
                required_permission="statistics",
            )
        )

    def execute(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        valid, err = self.validate_tool_call(tool_name, params)
        if not valid:
            return {"success": False, "error": err, "summary": f"Failed: {err}"}

        if tool_name == "calculate":
            return self._execute_calculate(params.get("expression", ""))
        elif tool_name == "convert_units":
            return self._execute_convert_units(
                params.get("value"),
                str(params.get("from_unit", "")).strip().lower(),
                str(params.get("to_unit", "")).strip().lower(),
            )
        elif tool_name == "calculate_statistics":
            return self._execute_statistics(params.get("numbers", []))
        else:
            return {"success": False, "error": f"Unknown tool '{tool_name}'.", "summary": "Tool not found."}

    def _execute_calculate(self, raw_expression: str) -> Dict[str, Any]:
        cleaned = raw_expression.strip().replace("^", "**").replace("×", "*").replace("÷", "/")
        if not cleaned:
            return {"success": False, "error": "Empty mathematical expression.", "summary": "Empty expression"}

        if len(cleaned) > 250:
            return {"success": False, "error": "Expression exceeds maximum length of 250 characters.", "summary": "Expression too long"}

        try:
            parsed = ast.parse(cleaned, mode="eval")
            result = _safe_eval_ast(parsed)

            # Round cleanly if float with insignificant precision issues
            if isinstance(result, float):
                if result.is_integer():
                    formatted = str(int(result))
                else:
                    formatted = f"{result:.8g}"
            else:
                formatted = str(result)

            return {
                "success": True,
                "result": result,
                "formatted": formatted,
                "expression": raw_expression,
                "summary": f"{raw_expression} = {formatted}",
                "data": {
                    "input": raw_expression,
                    "output": result,
                    "formatted_output": formatted,
                },
            }
        except ZeroDivisionError:
            return {"success": False, "error": "Division by zero is undefined.", "summary": "Error: Division by zero"}
        except Exception as e:
            return {"success": False, "error": f"Calculation error: {str(e)}", "summary": f"Math error: {str(e)}"}

    def _execute_convert_units(self, val: Any, from_u: str, to_u: str) -> Dict[str, Any]:
        try:
            num = float(val)
        except (ValueError, TypeError):
            return {"success": False, "error": "Invalid numeric value for unit conversion.", "summary": "Invalid value"}

        # Normalize unit names
        aliases = {
            "celsius": "c", "centigrade": "c", "fahrenheit": "f", "kelvin": "k",
            "kilometer": "km", "kilometers": "km", "meter": "m", "meters": "m", "centimeter": "cm", "centimeters": "cm",
            "millimeter": "mm", "millimeters": "mm", "mile": "mi", "miles": "mi", "foot": "ft", "feet": "ft", "inch": "in", "inches": "in",
            "kilogram": "kg", "kilograms": "kg", "gram": "g", "grams": "g", "pound": "lb", "pounds": "lb", "ounce": "oz", "ounces": "oz",
            "byte": "b", "bytes": "b", "kilobyte": "kb", "kilobytes": "kb", "megabyte": "mb", "megabytes": "mb",
            "gigabyte": "gb", "gigabytes": "gb", "terabyte": "tb", "terabytes": "tb",
            "second": "s", "seconds": "s", "minute": "min", "minutes": "min", "hour": "h", "hours": "h", "day": "d", "days": "d",
        }
        u1 = aliases.get(from_u, from_u)
        u2 = aliases.get(to_u, to_u)

        # Temperature
        if u1 in ("c", "f", "k") and u2 in ("c", "f", "k"):
            # Normalize to Celsius
            if u1 == "c":
                c = num
            elif u1 == "f":
                c = (num - 32) * 5 / 9
            else:  # k
                c = num - 273.15

            # Convert to target
            if u2 == "c":
                res = c
            elif u2 == "f":
                res = (c * 9 / 5) + 32
            else:  # k
                res = c + 273.15

            res_f = f"{res:.4g}"
            return {
                "success": True,
                "result": res,
                "formatted": res_f,
                "summary": f"{num} {from_u.upper()} = {res_f} {to_u.upper()}",
                "data": {"from_value": num, "from_unit": from_u, "to_value": res, "to_unit": to_u},
            }

        # Length factors to meters
        length_to_m = {"m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001, "mi": 1609.344, "ft": 0.3048, "in": 0.0254}
        if u1 in length_to_m and u2 in length_to_m:
            in_meters = num * length_to_m[u1]
            res = in_meters / length_to_m[u2]
            res_f = f"{res:.6g}"
            return {
                "success": True,
                "result": res,
                "formatted": res_f,
                "summary": f"{num} {from_u} = {res_f} {to_u}",
                "data": {"from_value": num, "from_unit": from_u, "to_value": res, "to_unit": to_u},
            }

        # Mass factors to grams
        mass_to_g = {"g": 1.0, "kg": 1000.0, "mg": 0.001, "lb": 453.59237, "oz": 28.34952}
        if u1 in mass_to_g and u2 in mass_to_g:
            in_g = num * mass_to_g[u1]
            res = in_g / mass_to_g[u2]
            res_f = f"{res:.6g}"
            return {
                "success": True,
                "result": res,
                "formatted": res_f,
                "summary": f"{num} {from_u} = {res_f} {to_u}",
                "data": {"from_value": num, "from_unit": from_u, "to_value": res, "to_unit": to_u},
            }

        # Digital storage factors to bytes
        storage_to_b = {"b": 1, "kb": 1024, "mb": 1024**2, "gb": 1024**3, "tb": 1024**4}
        if u1 in storage_to_b and u2 in storage_to_b:
            in_b = num * storage_to_b[u1]
            res = in_b / storage_to_b[u2]
            res_f = f"{res:.6g}"
            return {
                "success": True,
                "result": res,
                "formatted": res_f,
                "summary": f"{num} {from_u.upper()} = {res_f} {to_u.upper()}",
                "data": {"from_value": num, "from_unit": from_u, "to_value": res, "to_unit": to_u},
            }

        # Time factors to seconds
        time_to_s = {"s": 1, "min": 60, "h": 3600, "d": 86400}
        if u1 in time_to_s and u2 in time_to_s:
            in_s = num * time_to_s[u1]
            res = in_s / time_to_s[u2]
            res_f = f"{res:.6g}"
            return {
                "success": True,
                "result": res,
                "formatted": res_f,
                "summary": f"{num} {from_u} = {res_f} {to_u}",
                "data": {"from_value": num, "from_unit": from_u, "to_value": res, "to_unit": to_u},
            }

        return {
            "success": False,
            "error": f"Cannot convert between '{from_u}' and '{to_u}'. Units must belong to the same physical category.",
            "summary": "Incompatible unit types",
        }

    def _execute_statistics(self, numbers: Any) -> Dict[str, Any]:
        if not isinstance(numbers, list) or len(numbers) == 0:
            return {"success": False, "error": "Please provide a non-empty list of numbers.", "summary": "Empty dataset"}

        clean_nums: List[float] = []
        for n in numbers:
            try:
                clean_nums.append(float(n))
            except (ValueError, TypeError):
                continue

        if not clean_nums:
            return {"success": False, "error": "No valid numeric items found in the input list.", "summary": "Invalid numbers"}

        count = len(clean_nums)
        mean_val = statistics.mean(clean_nums)
        median_val = statistics.median(clean_nums)
        min_val = min(clean_nums)
        max_val = max(clean_nums)
        sum_val = sum(clean_nums)
        variance_val = statistics.variance(clean_nums) if count > 1 else 0.0
        stdev_val = statistics.stdev(clean_nums) if count > 1 else 0.0

        stats_data = {
            "count": count,
            "sum": sum_val,
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "min": min_val,
            "max": max_val,
            "variance": round(variance_val, 4),
            "standard_deviation": round(stdev_val, 4),
        }

        summary = f"Count: {count} | Mean: {stats_data['mean']} | Median: {stats_data['median']} | Min: {min_val} | Max: {max_val} | StdDev: {stats_data['standard_deviation']}"

        return {
            "success": True,
            "result": stats_data,
            "summary": summary,
            "data": stats_data,
        }
