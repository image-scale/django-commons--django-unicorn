import ast
from functools import lru_cache
from types import MappingProxyType
from typing import Any, Mapping

from dk_unicorn.typer import CASTERS


class InvalidKwargError(Exception):
    pass


def _get_expr_string(expr):
    if isinstance(expr, ast.Name):
        return expr.id
    elif isinstance(expr, ast.Attribute):
        return f"{_get_expr_string(expr.value)}.{expr.attr}"
    return ""


def _cast_value(value):
    for caster in CASTERS.values():
        try:
            result = caster(value)
            if result is not None:
                return result
        except (ValueError, TypeError):
            continue
    return value


@lru_cache(maxsize=128)
def eval_value(value):
    if not isinstance(value, str):
        return value

    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return _cast_value(value)


@lru_cache(maxsize=128)
def parse_kwarg(kwarg, *, raise_if_unparseable=False):
    try:
        tree = ast.parse(kwarg, mode="exec")
    except SyntaxError:
        if raise_if_unparseable:
            raise InvalidKwargError(f"Cannot parse kwarg: {kwarg}")
        return {}

    if not tree.body:
        return {}

    stmt = tree.body[0]

    if isinstance(stmt, ast.Assign) and len(stmt.targets) == 1:
        target = stmt.targets[0]
        if isinstance(target, ast.Name):
            key = target.id
            try:
                val = ast.literal_eval(stmt.value)
            except (ValueError, SyntaxError):
                if isinstance(stmt.value, (ast.Name, ast.Attribute)):
                    val = _get_expr_string(stmt.value)
                else:
                    val = ast.dump(stmt.value)
            return {key: val}

    if raise_if_unparseable:
        raise InvalidKwargError(f"Cannot parse kwarg: {kwarg}")
    return {}


@lru_cache(maxsize=128)
def parse_call_method_name(call_method_name):
    is_special = call_method_name.startswith("$")
    if is_special:
        call_method_name = call_method_name[1:]

    try:
        tree = ast.parse(call_method_name, mode="eval")
    except SyntaxError:
        method_name = call_method_name
        if is_special:
            method_name = f"${method_name}"
        return (method_name, (), MappingProxyType({}))

    expr = tree.body

    if isinstance(expr, ast.Call):
        method_name = _get_expr_string(expr.func)

        args = []
        for arg in expr.args:
            try:
                args.append(ast.literal_eval(arg))
            except (ValueError, SyntaxError):
                if isinstance(arg, (ast.Name, ast.Attribute)):
                    args.append(_get_expr_string(arg))
                else:
                    args.append(ast.dump(arg))

        kwargs = {}
        for keyword in expr.keywords:
            key = keyword.arg
            try:
                val = ast.literal_eval(keyword.value)
            except (ValueError, SyntaxError):
                if isinstance(keyword.value, (ast.Name, ast.Attribute)):
                    val = _get_expr_string(keyword.value)
                else:
                    val = ast.dump(keyword.value)
            kwargs[key] = val

        if is_special:
            method_name = f"${method_name}"

        return (method_name, tuple(args), MappingProxyType(kwargs))

    elif isinstance(expr, (ast.Name, ast.Attribute)):
        method_name = _get_expr_string(expr)
        if is_special:
            method_name = f"${method_name}"
        return (method_name, (), MappingProxyType({}))

    method_name = call_method_name
    if is_special:
        method_name = f"${method_name}"
    return (method_name, (), MappingProxyType({}))
