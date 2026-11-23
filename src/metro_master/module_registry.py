"""Registre gouverné de capacités de calcul natives et déclaratives."""

from __future__ import annotations

import ast
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from hashlib import sha256
import inspect
import json
from math import cos, e, exp, isfinite, log, log10, pi, sin, sqrt, tan
from pathlib import Path
import re
from typing import Any, Callable, Iterable, Mapping, Protocol

from .quantities import parse_unit
from .validation import require_finite, require_text


MODULE_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")
VERSION_PATTERN = re.compile(r"^\d+\.\d+\.\d+(?:-[a-z0-9.-]+)?$")
INPUT_NAME_PATTERN = re.compile(r"^[A-Za-z][A-Za-z0-9_]{0,63}$")
VALID_STATUSES = {"candidate", "validated", "deprecated"}
CORE_RESERVED_MODULE_IDS = frozenset({"budget", "compare", "paired", "separate"})
MAX_EXPRESSION_LENGTH = 2_000
MAX_AST_NODES = 256
UnitSignature = dict[str, int]


def parse_unit_expression(unit: str) -> UnitSignature:
    return dict(parse_unit(unit).dimensions)


def _combine_units(
    left: UnitSignature, right: UnitSignature, *, right_sign: int
) -> UnitSignature:
    result = dict(left)
    for name, power in right.items():
        result[name] = result.get(name, 0) + right_sign * power
        if result[name] == 0:
            del result[name]
    return result


def _unit_label(signature: UnitSignature) -> str:
    if not signature:
        return "dimensionless"
    return " * ".join(
        name if power == 1 else f"{name}^{power}"
        for name, power in sorted(signature.items())
    )


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _strict_object(
    value: object,
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    label: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise TypeError(f"{label} must be an object")
    missing = required - set(value)
    unknown = set(value) - required - optional
    if missing:
        raise ValueError(f"{label} is missing fields: {', '.join(sorted(missing))}")
    if unknown:
        raise ValueError(f"{label} has unknown fields: {', '.join(sorted(unknown))}")
    return value


def validate_module_id(value: object) -> str:
    text = require_text("module id", value)
    if not MODULE_ID_PATTERN.fullmatch(text):
        raise ValueError(
            "module id must start with a lowercase letter and contain only "
            "lowercase letters, digits, underscores or hyphens"
        )
    return text


def _version(value: object) -> str:
    text = require_text("module version", value)
    if not VERSION_PATTERN.fullmatch(text):
        raise ValueError("module version must use semantic versioning, for example 1.0.0")
    return text


@dataclass(frozen=True, slots=True)
class FormulaInput:
    name: str
    unit: str
    description: str
    minimum: float | None = None
    maximum: float | None = None

    @classmethod
    def from_dict(cls, value: object) -> "FormulaInput":
        data = _strict_object(
            value,
            required={"name", "unit", "description"},
            optional={"minimum", "maximum"},
            label="formula input",
        )
        name = require_text("input name", data["name"])
        if not INPUT_NAME_PATTERN.fullmatch(name):
            raise ValueError(f"invalid formula input name: {name}")
        unit = require_text(f"unit for {name}", data["unit"], allow_empty=True)
        description = require_text(f"description for {name}", data["description"])
        minimum = data.get("minimum")
        maximum = data.get("maximum")
        if minimum is not None:
            minimum = require_finite(f"minimum for {name}", minimum)
        if maximum is not None:
            maximum = require_finite(f"maximum for {name}", maximum)
        if minimum is not None and maximum is not None and minimum > maximum:
            raise ValueError(f"minimum exceeds maximum for {name}")
        return cls(name, unit, description, minimum, maximum)


@dataclass(frozen=True, slots=True)
class FormulaOutput:
    name: str
    unit: str
    description: str

    @classmethod
    def from_dict(cls, value: object) -> "FormulaOutput":
        data = _strict_object(
            value,
            required={"name", "unit", "description"},
            label="formula output",
        )
        return cls(
            require_text("output name", data["name"]),
            require_text("output unit", data["unit"], allow_empty=True),
            require_text("output description", data["description"]),
        )


@dataclass(frozen=True, slots=True)
class ModuleReference:
    reference: str
    content_status: str
    locator: str
    notes: str = ""

    @classmethod
    def from_dict(cls, value: object) -> "ModuleReference":
        data = _strict_object(
            value,
            required={"reference", "content_status", "locator"},
            optional={"notes"},
            label="module reference",
        )
        content_status = require_text("reference content_status", data["content_status"])
        if content_status not in {
            "metadata_only",
            "excerpt_provided",
            "full_text_provided",
            "internal_validated_method",
        }:
            raise ValueError(f"invalid reference content_status: {content_status}")
        return cls(
            require_text("reference", data["reference"]),
            content_status,
            require_text("reference locator", data["locator"], allow_empty=True),
            require_text("reference notes", data.get("notes", ""), allow_empty=True),
        )


@dataclass(frozen=True, slots=True)
class FormulaValidationCase:
    name: str
    source: str
    inputs: dict[str, dict[str, object]]
    expected_value: float
    expected_unit: str
    absolute_tolerance: float

    @classmethod
    def from_dict(cls, value: object) -> "FormulaValidationCase":
        data = _strict_object(
            value,
            required={
                "name",
                "source",
                "inputs",
                "expected_value",
                "expected_unit",
                "absolute_tolerance",
            },
            label="validation case",
        )
        if not isinstance(data["inputs"], dict):
            raise TypeError("validation case inputs must be an object")
        tolerance = require_finite("absolute_tolerance", data["absolute_tolerance"])
        if tolerance < 0:
            raise ValueError("absolute_tolerance must be non-negative")
        return cls(
            require_text("validation case name", data["name"]),
            require_text("validation case source", data["source"]),
            data["inputs"],
            require_finite("expected_value", data["expected_value"]),
            require_text("expected_unit", data["expected_unit"], allow_empty=True),
            tolerance,
        )


@dataclass(frozen=True, slots=True)
class FormulaModuleDefinition:
    schema_version: int
    id: str
    version: str
    title: str
    description: str
    kind: str
    inputs: tuple[FormulaInput, ...]
    expression: str
    output: FormulaOutput
    references: tuple[ModuleReference, ...]
    validation_cases: tuple[FormulaValidationCase, ...]

    @classmethod
    def from_dict(cls, value: object) -> "FormulaModuleDefinition":
        data = _strict_object(
            value,
            required={
                "schema_version",
                "id",
                "version",
                "title",
                "description",
                "kind",
                "inputs",
                "expression",
                "output",
                "references",
                "validation_cases",
            },
            label="module definition",
        )
        if data["schema_version"] != 1:
            raise ValueError("only module schema_version 1 is supported")
        if data["kind"] != "formula":
            raise ValueError("only declarative formula modules are supported")
        if not isinstance(data["inputs"], list) or not data["inputs"]:
            raise ValueError("module inputs must be a non-empty array")
        if not isinstance(data["references"], list):
            raise TypeError("module references must be an array")
        if not isinstance(data["validation_cases"], list):
            raise TypeError("module validation_cases must be an array")
        inputs = tuple(FormulaInput.from_dict(item) for item in data["inputs"])
        names = [item.name for item in inputs]
        if len(names) != len(set(names)):
            raise ValueError("formula input names must be unique")
        expression = require_text("formula expression", data["expression"])
        formula = SafeFormula(expression, set(names))
        output = FormulaOutput.from_dict(data["output"])
        inferred_unit = formula.infer_unit(
            {item.name: parse_unit_expression(item.unit) for item in inputs}
        )
        declared_unit = parse_unit_expression(output.unit)
        if inferred_unit != declared_unit:
            raise ValueError(
                "formula output unit does not match dimensional analysis: "
                f"inferred {_unit_label(inferred_unit)}, declared {_unit_label(declared_unit)}"
            )
        return cls(
            1,
            validate_module_id(data["id"]),
            _version(data["version"]),
            require_text("module title", data["title"]),
            require_text("module description", data["description"]),
            "formula",
            inputs,
            expression,
            output,
            tuple(ModuleReference.from_dict(item) for item in data["references"]),
            tuple(
                FormulaValidationCase.from_dict(item)
                for item in data["validation_cases"]
            ),
        )

    def to_dict(self) -> dict[str, object]:
        return asdict(self)

    def integrity_sha256(self) -> str:
        canonical = json.dumps(
            self.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return sha256(canonical).hexdigest()


@dataclass(frozen=True, slots=True)
class ModuleEvent:
    action: str
    actor: str
    at: str
    reason: str = ""


@dataclass(frozen=True, slots=True)
class StoredModuleRecord:
    definition: FormulaModuleDefinition
    integrity_sha256: str
    status: str
    events: tuple[ModuleEvent, ...]

    @classmethod
    def from_dict(cls, value: object) -> "StoredModuleRecord":
        data = _strict_object(
            value,
            required={"definition", "integrity_sha256", "status", "events"},
            label="stored module record",
        )
        definition = FormulaModuleDefinition.from_dict(data["definition"])
        integrity = require_text("integrity_sha256", data["integrity_sha256"])
        if integrity != definition.integrity_sha256():
            raise ValueError(
                f"{definition.id}@{definition.version}: module definition integrity mismatch"
            )
        status = require_text("module status", data["status"])
        if status not in VALID_STATUSES:
            raise ValueError(f"invalid module status: {status}")
        if not isinstance(data["events"], list) or not data["events"]:
            raise ValueError("module events must be a non-empty array")
        events = []
        for item in data["events"]:
            event = _strict_object(
                item,
                required={"action", "actor", "at", "reason"},
                label="module event",
            )
            events.append(
                ModuleEvent(
                    require_text("event action", event["action"]),
                    require_text("event actor", event["actor"]),
                    require_text("event timestamp", event["at"]),
                    require_text("event reason", event["reason"], allow_empty=True),
                )
            )
        return cls(definition, integrity, status, tuple(events))

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class ValidationCaseResult:
    name: str
    passed: bool
    actual_value: float | None
    expected_value: float
    absolute_error: float | None
    tolerance: float
    error: str = ""


@dataclass(frozen=True, slots=True)
class ModuleValidationReport:
    module_id: str
    version: str
    passed: bool
    cases: tuple[ValidationCaseResult, ...]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class CalculationModule(Protocol):
    id: str
    version: str
    title: str
    kind: str

    def calculate(self, payload: dict[str, Any]) -> dict[str, object]: ...


@dataclass(frozen=True, slots=True)
class NativeCalculationModule:
    id: str
    version: str
    title: str
    handler: Callable[[dict[str, Any]], dict[str, object]]
    kind: str = "native"

    def calculate(self, payload: dict[str, Any]) -> dict[str, object]:
        return self.handler(payload)

    def descriptor(self) -> dict[str, object]:
        try:
            implementation = inspect.getsource(self.handler)
        except (OSError, TypeError):
            implementation = f"{self.handler.__module__}:{self.handler.__qualname__}"
        implementation_hash = sha256(implementation.encode("utf-8")).hexdigest()
        validation_contract = (
            f"native:{self.id}:{self.version}:unit+validation+orchestrator-regression"
        )
        return {
            "id": self.id,
            "version": self.version,
            "title": self.title,
            "kind": self.kind,
            "algorithm_id": f"metrology-lab-ai/{self.id}/{self.version}",
            "implementation_sha256": implementation_hash,
            "validation_suite_sha256": sha256(
                validation_contract.encode("utf-8")
            ).hexdigest(),
        }


class SafeFormula:
    _functions: Mapping[str, Callable[..., float]] = {
        "abs": abs,
        "min": min,
        "max": max,
        "sqrt": sqrt,
        "log": log,
        "log10": log10,
        "exp": exp,
        "sin": sin,
        "cos": cos,
        "tan": tan,
    }
    _constants = {"pi": pi, "e": e}

    def __init__(self, expression: str, input_names: set[str]) -> None:
        if len(expression) > MAX_EXPRESSION_LENGTH:
            raise ValueError("formula expression is too long")
        self.expression = expression
        self.input_names = input_names
        try:
            self.tree = ast.parse(expression, mode="eval")
        except SyntaxError as error:
            raise ValueError(f"invalid formula syntax: {error.msg}") from error
        if sum(1 for _ in ast.walk(self.tree)) > MAX_AST_NODES:
            raise ValueError("formula expression is too complex")
        self._validate_node(self.tree)

    def _validate_node(self, node: ast.AST) -> None:
        if isinstance(node, ast.Expression):
            self._validate_node(node.body)
            return
        if isinstance(node, ast.Constant):
            if isinstance(node.value, bool) or not isinstance(node.value, (int, float)):
                raise ValueError("formula constants must be numeric")
            try:
                finite = isfinite(node.value)
            except OverflowError as error:
                raise ValueError("formula constant is outside the supported range") from error
            if not finite or abs(node.value) > 1e100:
                raise ValueError("formula constant is outside the supported range")
            return
        if isinstance(node, ast.Name):
            if node.id not in self.input_names and node.id not in self._constants:
                raise ValueError(f"formula uses unknown name: {node.id}")
            return
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            self._validate_node(node.operand)
            return
        if isinstance(node, ast.BinOp) and isinstance(
            node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow)
        ):
            self._validate_node(node.left)
            self._validate_node(node.right)
            return
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in self._functions:
                raise ValueError("formula calls an unauthorized function")
            if node.keywords:
                raise ValueError("formula function calls cannot use keyword arguments")
            for argument in node.args:
                self._validate_node(argument)
            return
        raise ValueError(f"formula contains unauthorized syntax: {type(node).__name__}")

    def evaluate(self, values: Mapping[str, float]) -> float:
        missing = self.input_names - set(values)
        unknown = set(values) - self.input_names
        if missing:
            raise ValueError(f"formula values are missing: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"formula values are unknown: {', '.join(sorted(unknown))}")
        result = self._evaluate_node(self.tree.body, values)
        return require_finite("formula result", result)

    def infer_unit(
        self, input_units: Mapping[str, UnitSignature]
    ) -> UnitSignature:
        return self._infer_unit_node(self.tree.body, input_units)

    def _infer_unit_node(
        self, node: ast.AST, input_units: Mapping[str, UnitSignature]
    ) -> UnitSignature:
        if isinstance(node, ast.Constant):
            return {}
        if isinstance(node, ast.Name):
            return {} if node.id in self._constants else dict(input_units[node.id])
        if isinstance(node, ast.UnaryOp):
            return self._infer_unit_node(node.operand, input_units)
        if isinstance(node, ast.BinOp):
            left = self._infer_unit_node(node.left, input_units)
            right = self._infer_unit_node(node.right, input_units)
            if isinstance(node.op, (ast.Add, ast.Sub)):
                if left != right:
                    raise ValueError(
                        "addition or subtraction requires identical units: "
                        f"{_unit_label(left)} versus {_unit_label(right)}"
                    )
                return left
            if isinstance(node.op, ast.Mult):
                return _combine_units(left, right, right_sign=1)
            if isinstance(node.op, ast.Div):
                return _combine_units(left, right, right_sign=-1)
            if right:
                raise ValueError("a formula exponent must be dimensionless")
            if not isinstance(node.right, ast.Constant):
                if left:
                    raise ValueError(
                        "a dimensional base requires a constant integer exponent"
                    )
                return {}
            exponent = node.right.value
            if isinstance(exponent, bool) or not isinstance(exponent, (int, float)):
                raise ValueError("formula exponent must be numeric")
            if int(exponent) != exponent:
                if left:
                    raise ValueError(
                        "fractional powers of dimensional quantities are not supported"
                    )
                return {}
            return {name: power * int(exponent) for name, power in left.items()}
        if isinstance(node, ast.Call):
            units = [self._infer_unit_node(item, input_units) for item in node.args]
            function = node.func.id
            if function == "abs":
                if len(units) != 1:
                    raise ValueError("abs requires exactly one argument")
                return units[0]
            if function in {"min", "max"}:
                if not units or any(item != units[0] for item in units[1:]):
                    raise ValueError(f"{function} requires arguments with identical units")
                return units[0]
            if function == "sqrt":
                if len(units) != 1:
                    raise ValueError("sqrt requires exactly one argument")
                if any(power % 2 for power in units[0].values()):
                    raise ValueError(
                        "sqrt requires even dimensional exponents in the declarative engine"
                    )
                return {name: power // 2 for name, power in units[0].items()}
            if any(units):
                raise ValueError(f"{function} requires dimensionless arguments")
            return {}
        raise ValueError(f"unsupported formula node: {type(node).__name__}")

    def _evaluate_node(self, node: ast.AST, values: Mapping[str, float]) -> float:
        if isinstance(node, ast.Constant):
            return float(node.value)
        if isinstance(node, ast.Name):
            if node.id in self._constants:
                return self._constants[node.id]
            return require_finite(node.id, values[node.id])
        if isinstance(node, ast.UnaryOp):
            value = self._evaluate_node(node.operand, values)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left = self._evaluate_node(node.left, values)
            right = self._evaluate_node(node.right, values)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if abs(right) > 1_000:
                raise ValueError("formula exponent exceeds the supported range")
            return left**right
        if isinstance(node, ast.Call):
            function = self._functions[node.func.id]
            arguments = [self._evaluate_node(item, values) for item in node.args]
            return float(function(*arguments))
        raise ValueError(f"unsupported formula node: {type(node).__name__}")


class FormulaCalculationModule:
    kind = "formula"

    def __init__(self, definition: FormulaModuleDefinition) -> None:
        self.definition = definition
        self.id = definition.id
        self.version = definition.version
        self.title = definition.title
        self.formula = SafeFormula(
            definition.expression, {item.name for item in definition.inputs}
        )

    def calculate(self, payload: dict[str, Any]) -> dict[str, object]:
        data = _strict_object(
            payload,
            required={"inputs"},
            label=f"payload for {self.id}",
        )
        provided = data["inputs"]
        if not isinstance(provided, dict):
            raise TypeError("formula module inputs must be an object")
        expected_names = {item.name for item in self.definition.inputs}
        missing = expected_names - set(provided)
        unknown = set(provided) - expected_names
        if missing:
            raise ValueError(f"module inputs are missing: {', '.join(sorted(missing))}")
        if unknown:
            raise ValueError(f"module inputs are unknown: {', '.join(sorted(unknown))}")
        values = {}
        serialized_inputs = {}
        for specification in self.definition.inputs:
            item = _strict_object(
                provided[specification.name],
                required={"value", "unit"},
                label=f"input {specification.name}",
            )
            value = require_finite(specification.name, item["value"])
            unit = require_text(
                f"unit for {specification.name}", item["unit"], allow_empty=True
            )
            if unit != specification.unit:
                raise ValueError(
                    f"{specification.name} requires unit {specification.unit!r}, got {unit!r}"
                )
            if specification.minimum is not None and value < specification.minimum:
                raise ValueError(f"{specification.name} is below the validated domain")
            if specification.maximum is not None and value > specification.maximum:
                raise ValueError(f"{specification.name} is above the validated domain")
            values[specification.name] = value
            serialized_inputs[specification.name] = {"value": value, "unit": unit}
        result = self.formula.evaluate(values)
        return {
            "module_id": self.id,
            "module_version": self.version,
            "kind": self.kind,
            "inputs": serialized_inputs,
            "expression": self.definition.expression,
            "output": {
                "name": self.definition.output.name,
                "value": result,
                "unit": self.definition.output.unit,
            },
            "definition_sha256": self.definition.integrity_sha256(),
        }

    def descriptor(self) -> dict[str, object]:
        validation_payload = [asdict(item) for item in self.definition.validation_cases]
        return {
            "id": self.id,
            "version": self.version,
            "title": self.title,
            "kind": self.kind,
            "algorithm_id": f"governed-formula/{self.id}/{self.version}",
            "implementation_sha256": self.definition.integrity_sha256(),
            "validation_suite_sha256": sha256(
                json.dumps(
                    validation_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ).hexdigest(),
        }

    def validate(self) -> ModuleValidationReport:
        results = []
        for case in self.definition.validation_cases:
            try:
                output = self.calculate({"inputs": case.inputs})
                actual = output["output"]["value"]
                if case.expected_unit != output["output"]["unit"]:
                    raise ValueError(
                        f"expected unit {case.expected_unit!r}, got {output['output']['unit']!r}"
                    )
                error = abs(actual - case.expected_value)
                results.append(
                    ValidationCaseResult(
                        case.name,
                        error <= case.absolute_tolerance,
                        actual,
                        case.expected_value,
                        error,
                        case.absolute_tolerance,
                    )
                )
            except (ArithmeticError, KeyError, TypeError, ValueError) as error:
                results.append(
                    ValidationCaseResult(
                        case.name,
                        False,
                        None,
                        case.expected_value,
                        None,
                        case.absolute_tolerance,
                        str(error),
                    )
                )
        return ModuleValidationReport(
            self.id,
            self.version,
            bool(results) and all(item.passed for item in results),
            tuple(results),
        )


class ModuleRegistry:
    def __init__(self, modules: Iterable[CalculationModule] = ()) -> None:
        self._modules: dict[str, CalculationModule] = {}
        for module in modules:
            self.register(module)

    def register(self, module: CalculationModule) -> None:
        validate_module_id(module.id)
        if module.id in self._modules:
            raise ValueError(f"calculation module is already registered: {module.id}")
        self._modules[module.id] = module

    def get(self, module_id: str) -> CalculationModule:
        if module_id not in self._modules:
            available = ", ".join(sorted(self._modules))
            raise ValueError(
                f"unknown calculation module: {module_id}; available modules: {available}"
            )
        return self._modules[module_id]

    def remove_kind(self, kind: str) -> None:
        self._modules = {
            module_id: module
            for module_id, module in self._modules.items()
            if module.kind != kind
        }

    def calculate(self, module_id: str, payload: dict[str, Any]) -> dict[str, object]:
        return self.get(module_id).calculate(payload)

    def descriptor(self, module_id: str) -> dict[str, object]:
        module = self.get(module_id)
        descriptor = getattr(module, "descriptor", None)
        if callable(descriptor):
            return descriptor()
        return {
            "id": module.id,
            "version": module.version,
            "title": module.title,
            "kind": module.kind,
            "algorithm_id": f"unknown/{module.id}/{module.version}",
            "implementation_sha256": "",
            "validation_suite_sha256": "",
        }

    def describe(self) -> tuple[dict[str, object], ...]:
        return tuple(
            self.descriptor(module.id)
            for module in sorted(self._modules.values(), key=lambda item: item.id)
        )


class ModuleStore:
    def __init__(
        self,
        root: str | Path,
        *,
        reserved_ids: Iterable[str] = CORE_RESERVED_MODULE_IDS,
    ) -> None:
        self.root = Path(root)
        self.records_root = self.root / "records"
        self.active_path = self.root / "active.json"
        self.reserved_ids = set(reserved_ids)

    def submit(
        self, definition_value: object, *, created_by: str
    ) -> StoredModuleRecord:
        definition = FormulaModuleDefinition.from_dict(definition_value)
        if definition.id in self.reserved_ids:
            raise ValueError(f"module id is reserved by the core: {definition.id}")
        actor = require_text("created_by", created_by)
        path = self._record_path(definition.id, definition.version)
        if path.exists():
            raise FileExistsError(
                f"module version already exists: {definition.id}@{definition.version}"
            )
        record = StoredModuleRecord(
            definition,
            definition.integrity_sha256(),
            "candidate",
            (ModuleEvent("submitted", actor, _now()),),
        )
        self._write_json(path, record.to_dict(), overwrite=False)
        return record

    def load(self, module_id: str, version: str) -> StoredModuleRecord:
        path = self._record_path(validate_module_id(module_id), _version(version))
        with path.open("r", encoding="utf-8") as handle:
            return StoredModuleRecord.from_dict(json.load(handle))

    def list_records(self) -> tuple[StoredModuleRecord, ...]:
        if not self.records_root.exists():
            return ()
        records = []
        for path in sorted(self.records_root.glob("*/*.json")):
            with path.open("r", encoding="utf-8") as handle:
                records.append(StoredModuleRecord.from_dict(json.load(handle)))
        return tuple(records)

    def test(self, module_id: str, version: str) -> ModuleValidationReport:
        record = self.load(module_id, version)
        return FormulaCalculationModule(record.definition).validate()

    def promote(
        self, module_id: str, version: str, *, approved_by: str
    ) -> StoredModuleRecord:
        actor = require_text("approved_by", approved_by)
        record = self.load(module_id, version)
        if record.status != "candidate":
            raise ValueError("only candidate modules can be promoted")
        if len(record.definition.validation_cases) < 2:
            raise ValueError("promotion requires at least two reference validation cases")
        if not record.definition.references or not any(
            reference.content_status != "metadata_only"
            for reference in record.definition.references
        ):
            raise ValueError(
                "promotion requires at least one provided reference or validated internal method"
            )
        report = FormulaCalculationModule(record.definition).validate()
        if not report.passed:
            raise ValueError("module cannot be promoted because validation cases failed")
        promoted = replace(
            record,
            status="validated",
            events=record.events + (ModuleEvent("promoted", actor, _now()),),
        )
        self._write_record(promoted)
        self._set_active(module_id, version, actor=actor, action="promote")
        return promoted

    def deprecate(
        self,
        module_id: str,
        version: str,
        *,
        approved_by: str,
        reason: str,
    ) -> StoredModuleRecord:
        actor = require_text("approved_by", approved_by)
        reason = require_text("deprecation reason", reason)
        record = self.load(module_id, version)
        if record.status != "validated":
            raise ValueError("only validated modules can be deprecated")
        deprecated = replace(
            record,
            status="deprecated",
            events=record.events
            + (ModuleEvent("deprecated", actor, _now(), reason),),
        )
        self._write_record(deprecated)
        active = self._load_active()
        if active.get(module_id, {}).get("version") == version:
            del active[module_id]
            self._write_active(active)
        return deprecated

    def rollback(
        self, module_id: str, version: str, *, approved_by: str
    ) -> StoredModuleRecord:
        actor = require_text("approved_by", approved_by)
        record = self.load(module_id, version)
        if record.status != "validated":
            raise ValueError("rollback target must be a validated module version")
        self._set_active(module_id, version, actor=actor, action="rollback")
        updated = replace(
            record,
            events=record.events + (ModuleEvent("activated_by_rollback", actor, _now()),),
        )
        self._write_record(updated)
        return updated

    def active_records(self) -> tuple[StoredModuleRecord, ...]:
        active = self._load_active()
        records = []
        for module_id, value in sorted(active.items()):
            record = self.load(module_id, value["version"])
            if record.status != "validated":
                raise ValueError(
                    f"active module is not validated: {module_id}@{record.definition.version}"
                )
            records.append(record)
        return tuple(records)

    def _record_path(self, module_id: str, version: str) -> Path:
        return self.records_root / module_id / f"{version}.json"

    def _write_record(self, record: StoredModuleRecord) -> None:
        path = self._record_path(record.definition.id, record.definition.version)
        self._write_json(path, record.to_dict(), overwrite=True)

    def _load_active(self) -> dict[str, dict[str, str]]:
        if not self.active_path.exists():
            return {}
        with self.active_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        data = _strict_object(
            payload,
            required={"schema_version", "active"},
            label="active module index",
        )
        if data["schema_version"] != 1 or not isinstance(data["active"], dict):
            raise ValueError("invalid active module index")
        return data["active"]

    def _set_active(
        self, module_id: str, version: str, *, actor: str, action: str
    ) -> None:
        active = self._load_active()
        active[module_id] = {
            "version": version,
            "changed_at": _now(),
            "approved_by": actor,
            "action": action,
        }
        self._write_active(active)

    def _write_active(self, active: dict[str, dict[str, str]]) -> None:
        self._write_json(
            self.active_path,
            {"schema_version": 1, "active": active},
            overwrite=True,
        )

    @staticmethod
    def _write_json(path: Path, value: object, *, overwrite: bool) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and not overwrite:
            raise FileExistsError(path)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)
