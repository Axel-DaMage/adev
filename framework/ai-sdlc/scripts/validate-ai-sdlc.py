#!/usr/bin/env python3
"""
A-Dev AI-SDLC Declarative Configuration Validator

Validates .ai-sdlc.yaml / .ai-sdlc.json files against the normative
JSON Schema and A-Dev semantic lifecycle invariants.

Usable in CI pipelines, pre-commit hooks, and local development.
Zero external dependencies required (Python 3.8+ stdlib compatible).
"""

import sys
import os
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union


def parse_yaml_or_json(content: str, filepath: str = "") -> Any:
    """
    Parses YAML or JSON string into Python data structures.
    Uses PyYAML if available; falls back to robust built-in parser for YAML/JSON.
    """
    try:
        import yaml
        return yaml.safe_load(content)
    except ImportError:
        pass

    # Try standard JSON first
    trimmed = content.strip()
    if trimmed.startswith("{") or trimmed.startswith("["):
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

    # Fallback built-in YAML parser
    return _parse_simple_yaml(content)


def _parse_simple_yaml(text: str) -> Any:
    """
    Lightweight, robust YAML parser supporting maps, lists,
    strings, ints, floats, booleans, nulls, inline maps/lists, and comments.
    """
    lines = text.splitlines()
    cleaned_lines: List[Tuple[int, str]] = []

    for line in lines:
        s = line
        in_single = False
        in_double = False
        comment_idx = -1
        for i, ch in enumerate(s):
            if ch == "'" and not in_double:
                in_single = not in_single
            elif ch == '"' and not in_single:
                in_double = not in_double
            elif ch == '#' and not in_single and not in_double:
                comment_idx = i
                break
        if comment_idx >= 0:
            s = s[:comment_idx]
        if not s.strip():
            continue
        indent = len(s) - len(s.lstrip(' '))
        cleaned_lines.append((indent, s.strip()))

    if not cleaned_lines:
        return {}

    def parse_scalar(v: str) -> Any:
        v = v.strip()
        if not v or v == "null" or v == "~":
            return None
        if v.lower() == "true":
            return True
        if v.lower() == "false":
            return False
        if (v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'")):
            return v[1:-1]
        # Check integer
        if re.match(r"^-?[0-9]+$", v):
            return int(v)
        # Check float
        if re.match(r"^-?[0-9]+\.[0-9]+$", v):
            return float(v)
        # Check inline JSON array/object
        if (v.startswith("[") and v.endswith("]")) or (v.startswith("{") and v.endswith("}")):
            try:
                j_str = v
                if "'" in j_str and '"' not in j_str:
                    j_str = j_str.replace("'", '"')
                return json.loads(j_str)
            except Exception:
                pass
        return v

    def find_key_value_split(line: str) -> Tuple[str, Optional[str]]:
        colon_idx = -1
        in_s = False
        in_d = False
        for ci, c in enumerate(line):
            if c == "'" and not in_d:
                in_s = not in_s
            elif c == '"' and not in_s:
                in_d = not in_d
            elif c == ':' and not in_s and not in_d:
                # Colon must be followed by space, end of string, or start of block
                if ci == len(line) - 1 or line[ci + 1] in (' ', '\t'):
                    colon_idx = ci
                    break
        if colon_idx == -1:
            return line, None
        key = line[:colon_idx].strip()
        val = line[colon_idx + 1:].strip()
        if (key.startswith('"') and key.endswith('"')) or (key.startswith("'") and key.endswith("'")):
            key = key[1:-1]
        return key, val

    def parse_node(idx: int, min_indent: int) -> Tuple[Any, int]:
        if idx >= len(cleaned_lines):
            return {}, idx

        cur_indent, cur_line = cleaned_lines[idx]
        if cur_indent < min_indent:
            return {}, idx

        if cur_line.startswith("- ") or cur_line == "-":
            # List node
            items: List[Any] = []
            list_indent = cur_indent
            while idx < len(cleaned_lines):
                ind, l = cleaned_lines[idx]
                if ind < list_indent:
                    break
                if ind == list_indent and (l.startswith("- ") or l == "-"):
                    item_content = l[2:].strip() if l.startswith("- ") else ""
                    if not item_content:
                        # Nested item on next lines
                        child_val, idx = parse_node(idx + 1, list_indent + 1)
                        items.append(child_val)
                    else:
                        key, val_part = find_key_value_split(item_content)
                        if val_part is not None:
                            # It's an inline dictionary starting on the '- ' line
                            sub_dict: Dict[str, Any] = {}
                            if val_part:
                                sub_dict[key] = parse_scalar(val_part)
                                idx += 1
                            else:
                                child_val, idx = parse_node(idx + 1, list_indent + 2)
                                sub_dict[key] = child_val

                            # Collect subsequent keys belonging to this dict
                            while idx < len(cleaned_lines):
                                k_ind, k_line = cleaned_lines[idx]
                                if k_ind <= list_indent or k_line.startswith("-"):
                                    break
                                next_k, next_v = find_key_value_split(k_line)
                                if next_v is not None:
                                    if next_v:
                                        sub_dict[next_k] = parse_scalar(next_v)
                                        idx += 1
                                    else:
                                        nested_val, idx = parse_node(idx + 1, k_ind + 1)
                                        sub_dict[next_k] = nested_val
                                else:
                                    idx += 1
                            items.append(sub_dict)
                        else:
                            items.append(parse_scalar(item_content))
                            idx += 1
                else:
                    break
            return items, idx

        else:
            # Map node
            res_dict: Dict[str, Any] = {}
            map_indent = cur_indent
            while idx < len(cleaned_lines):
                ind, l = cleaned_lines[idx]
                if ind < map_indent:
                    break
                if ind == map_indent:
                    key, val_part = find_key_value_split(l)
                    if val_part is not None:
                        if val_part:
                            res_dict[key] = parse_scalar(val_part)
                            idx += 1
                        else:
                            # Sub block
                            if idx + 1 < len(cleaned_lines) and cleaned_lines[idx + 1][0] > map_indent:
                                child_val, idx = parse_node(idx + 1, cleaned_lines[idx + 1][0])
                                res_dict[key] = child_val
                            else:
                                res_dict[key] = None
                                idx += 1
                    else:
                        idx += 1
                else:
                    break
            return res_dict, idx

    res, _ = parse_node(0, cleaned_lines[0][0])
    return res


class ValidationError(Exception):
    def __init__(self, message: str, path: str = "$"):
        super().__init__(f"[{path}] {message}")
        self.message = message
        self.path = path


class SchemaValidator:
    """
    Validates data structures against JSON Schema Draft-07 specs.
    """
    def __init__(self, schema: Dict[str, Any]):
        self.schema = schema
        self.definitions = schema.get("definitions", {})

    def validate(self, instance: Any) -> List[str]:
        errors: List[str] = []
        self._validate_node(instance, self.schema, "$", errors)
        return errors

    def _resolve_ref(self, ref: str) -> Dict[str, Any]:
        if ref.startswith("#/definitions/"):
            def_name = ref.split("/")[-1]
            if def_name in self.definitions:
                return self.definitions[def_name]
        raise ValidationError(f"Unresolvable $ref: {ref}")

    def _validate_node(self, instance: Any, schema: Dict[str, Any], path: str, errors: List[str]):
        if "$ref" in schema:
            target_schema = self._resolve_ref(schema["$ref"])
            self._validate_node(instance, target_schema, path, errors)
            return

        expected_type = schema.get("type")
        if expected_type:
            if not self._check_type(instance, expected_type):
                errors.append(f"{path}: Expected type '{expected_type}', got '{type(instance).__name__}'")
                return

        if "enum" in schema:
            if instance not in schema["enum"]:
                errors.append(f"{path}: Value '{instance}' is not one of allowed enum values: {schema['enum']}")

        if "oneOf" in schema:
            matched = 0
            for candidate in schema["oneOf"]:
                candidate_errors: List[str] = []
                self._validate_node(instance, candidate, path, candidate_errors)
                if not candidate_errors:
                    matched += 1
            if matched == 0:
                errors.append(f"{path}: Value '{instance}' does not match any allowed oneOf sub-schemas")

        if isinstance(instance, str):
            if "pattern" in schema:
                pattern = schema["pattern"]
                if not re.search(pattern, instance):
                    errors.append(f"{path}: String '{instance}' does not match required pattern '{pattern}'")
            if "minLength" in schema and len(instance) < schema["minLength"]:
                errors.append(f"{path}: String length {len(instance)} is less than minLength {schema['minLength']}")

        elif isinstance(instance, (int, float)) and not isinstance(instance, bool):
            if "minimum" in schema and instance < schema["minimum"]:
                errors.append(f"{path}: Number {instance} is less than minimum {schema['minimum']}")
            if "maximum" in schema and instance > schema["maximum"]:
                errors.append(f"{path}: Number {instance} is greater than maximum {schema['maximum']}")

        elif isinstance(instance, list):
            if "minItems" in schema and len(instance) < schema["minItems"]:
                errors.append(f"{path}: Array has {len(instance)} items, minimum is {schema['minItems']}")
            items_schema = schema.get("items")
            if items_schema:
                for idx, item in enumerate(instance):
                    self._validate_node(item, items_schema, f"{path}[{idx}]", errors)

        elif isinstance(instance, dict):
            required = schema.get("required", [])
            for req in required:
                if req not in instance:
                    errors.append(f"{path}: Missing required property '{req}'")

            props = schema.get("properties", {})
            additional_props = schema.get("additionalProperties", True)

            for key, val in instance.items():
                prop_path = f"{path}.{key}" if path != "$" else f"$.{key}"
                if key in props:
                    self._validate_node(val, props[key], prop_path, errors)
                elif isinstance(additional_props, dict):
                    self._validate_node(val, additional_props, prop_path, errors)
                elif additional_props is False:
                    errors.append(f"{path}: Undefined property '{key}' not allowed (additionalProperties is false)")

            if "minProperties" in schema and len(instance) < schema["minProperties"]:
                errors.append(f"{path}: Object has {len(instance)} properties, minimum is {schema['minProperties']}")

    def _check_type(self, val: Any, expected: str) -> bool:
        if expected == "object":
            return isinstance(val, dict)
        if expected == "array":
            return isinstance(val, list)
        if expected == "string":
            return isinstance(val, str)
        if expected == "integer":
            return isinstance(val, int) and not isinstance(val, bool)
        if expected == "number":
            return (isinstance(val, (int, float))) and not isinstance(val, bool)
        if expected == "boolean":
            return isinstance(val, bool)
        if expected == "null":
            return val is None
        return True


def normalize_autonomy_level(level_raw: Union[int, str]) -> int:
    """Maps autonomy level representations (0-4, 'L0', 'A0', 'L2-autonomous-pr') to canonical integer 0..4."""
    if isinstance(level_raw, int):
        return level_raw
    s = str(level_raw).strip().upper()
    if s in ("0", "L0", "A0", "L0-ADVISORY", "A0-ADVISORY"):
        return 0
    if s in ("1", "L1", "A1", "L1-ASSISTED", "A1-ASSISTED"):
        return 1
    if s in ("2", "L2", "A2", "L2-AUTONOMOUS-PR", "A2-AUTONOMOUS-PR"):
        return 2
    if s in ("3", "L3", "A3", "L3-GUARDED-MERGE", "A3-GUARDED-MERGE"):
        return 3
    if s in ("4", "L4", "A4", "L4-FULL-LIFECYCLE", "A4-FULL-LIFECYCLE"):
        return 4
    raise ValueError(f"Unknown autonomy level: {level_raw}")


def validate_semantic_invariants(config: Dict[str, Any]) -> List[str]:
    """
    Validates normative A-Dev semantic invariants across configuration fields.
    """
    errors: List[str] = []

    # 1. Verification Default Profile Invariant
    verification = config.get("verification", {})
    default_profile = verification.get("default_profile")
    profiles = verification.get("profiles", {})
    if default_profile and default_profile not in profiles:
        errors.append(
            f"$.verification.default_profile: Specified default profile '{default_profile}' "
            f"is not defined in $.verification.profiles (available: {list(profiles.keys())})"
        )

    # 2. Progressive Autonomy vs Max Risk Tier Ladder Invariant
    autonomy = config.get("autonomy", {})
    raw_level = autonomy.get("level")
    max_risk = autonomy.get("max_autonomous_risk_tier")

    if raw_level is not None and max_risk is not None:
        try:
            level_num = normalize_autonomy_level(raw_level)
            risk_rank = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}.get(max_risk, 99)

            # Progressive Autonomy Ladder limits:
            # Level 0 (Advisory) -> max R0
            # Level 1 (Assisted) -> max R1
            # Level 2 (Autonomous PR) -> max R2
            # Level 3/4 (Guarded Merge / Full Lifecycle) -> max R3
            max_allowed_risk_for_level = {
                0: 0, # R0
                1: 1, # R1
                2: 2, # R2
                3: 3, # R3
                4: 3, # R3
            }
            allowed_max = max_allowed_risk_for_level.get(level_num, 0)
            if risk_rank > allowed_max:
                errors.append(
                    f"$.autonomy: Invariant violation on Progressive Autonomy Ladder. "
                    f"Level {level_num} is restricted to maximum risk tier 'R{allowed_max}', "
                    f"but configured with 'max_autonomous_risk_tier: {max_risk}'."
                )
        except ValueError as e:
            errors.append(f"$.autonomy.level: {str(e)}")

    # 3. Auto-Merge Invariants
    review = config.get("review", {})
    auto_merge = review.get("auto_merge", {})
    if auto_merge.get("enabled") is True:
        checks = auto_merge.get("required_status_checks", [])
        if not checks:
            errors.append(
                "$.review.auto_merge: 'enabled' is true, but 'required_status_checks' is empty. "
                "Auto-merge requires at least one required status check for safety."
            )
        auto_merge_risk = auto_merge.get("max_risk_tier")
        if auto_merge_risk and max_risk:
            risk_rank_auto = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}.get(auto_merge_risk, 99)
            risk_rank_max = {"R0": 0, "R1": 1, "R2": 2, "R3": 3}.get(max_risk, 99)
            if risk_rank_auto > risk_rank_max:
                errors.append(
                    f"$.review.auto_merge.max_risk_tier ('{auto_merge_risk}') cannot exceed "
                    f"$.autonomy.max_autonomous_risk_tier ('{max_risk}')."
                )

    # 4. Escalation Contacts Invariant
    escalation = config.get("escalation", {})
    contacts = escalation.get("contacts", [])
    if not contacts:
        errors.append("$.escalation.contacts: At least one escalation contact is mandatory.")
    else:
        for idx, contact in enumerate(contacts):
            has_channel = any([
                contact.get("github_handle"),
                contact.get("email"),
                contact.get("slack_channel"),
                contact.get("pagerduty_service")
            ])
            if not has_channel:
                errors.append(
                    f"$.escalation.contacts[{idx}]: Contact for role '{contact.get('role', 'unknown')}' "
                    "must specify at least one notification channel (github_handle, email, slack_channel, or pagerduty_service)."
                )

    # 5. Label Taxonomy Prefix Consistency
    labels_cfg = config.get("labels", {})
    taxonomy = labels_cfg.get("taxonomy", {})
    for cat_name, cat_def in taxonomy.items():
        if isinstance(cat_def, dict):
            prefix = cat_def.get("prefix")
            values = cat_def.get("values", [])
            if prefix and isinstance(values, list):
                for v_idx, val_item in enumerate(values):
                    v_name = val_item.get("name", "")
                    if v_name and not v_name.startswith(prefix):
                        errors.append(
                            f"$.labels.taxonomy.{cat_name}.values[{v_idx}]: Label name '{v_name}' "
                            f"does not start with declared category prefix '{prefix}'"
                        )

    return errors


def validate_config(config_data: Any, schema_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Runs schema validation and semantic invariant validation."""
    if not isinstance(config_data, dict):
        return False, ["Root configuration must be a valid mapping/object."]

    validator = SchemaValidator(schema_data)
    schema_errors = validator.validate(config_data)

    if schema_errors:
        return False, [f"[SCHEMA] {err}" for err in schema_errors]

    semantic_errors = validate_semantic_invariants(config_data)
    if semantic_errors:
        return False, [f"[SEMANTIC] {err}" for err in semantic_errors]

    return True, []


def main() -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Validate .ai-sdlc.yaml / .ai-sdlc.json repository configuration.")
    parser.add_argument("config", nargs="?", default=".ai-sdlc.yaml", help="Path to config file (default: .ai-sdlc.yaml)")
    parser.add_argument("--schema", default=None, help="Path to ai-sdlc.schema.json (defaults to framework/ai-sdlc.schema.json)")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet output (exit code only)")
    args = parser.parse_args()

    # Determine schema path
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent.parent.parent

    schema_candidates = [
        args.schema,
        str(repo_root / "framework" / "ai-sdlc.schema.json"),
        str(repo_root / "framework" / "schema" / "ai-sdlc.schema.json"),
    ]
    schema_path = next((p for p in schema_candidates if p and os.path.exists(p)), None)

    if not schema_path:
        print(f"Error: Could not locate ai-sdlc.schema.json. Looked at: {schema_candidates}", file=sys.stderr)
        return 2

    # Load schema
    with open(schema_path, "r", encoding="utf-8") as f:
        schema_data = json.load(f)

    # Locate config file
    config_path = Path(args.config)
    if not config_path.is_absolute():
        config_path = (Path.cwd() / config_path).resolve()

    if not config_path.exists():
        # Check alternative extensions
        alt_yaml = config_path.with_suffix(".yaml")
        alt_yml = config_path.with_suffix(".yml")
        alt_json = config_path.with_suffix(".json")
        if alt_yaml.exists():
            config_path = alt_yaml
        elif alt_yml.exists():
            config_path = alt_yml
        elif alt_json.exists():
            config_path = alt_json
        else:
            print(f"Error: Configuration file not found at: {args.config}", file=sys.stderr)
            return 1

    with open(config_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    try:
        config_data = parse_yaml_or_json(raw_text, str(config_path))
    except Exception as e:
        print(f"Syntax Error: Failed to parse configuration file '{config_path}': {e}", file=sys.stderr)
        return 1

    is_valid, errors = validate_config(config_data, schema_data)

    if is_valid:
        if not args.quiet:
            archetype = config_data.get("repository", {}).get("archetype", "generic")
            level = config_data.get("autonomy", {}).get("level")
            print(f"PASS: '{config_path.name}' is a valid AI-SDLC configuration.")
            print(f"      Archetype: {archetype} | Autonomy Level: {level} | Max Risk: {config_data.get('autonomy', {}).get('max_autonomous_risk_tier')}")
        return 0
    else:
        if not args.quiet:
            print(f"FAIL: '{config_path.name}' failed AI-SDLC validation with {len(errors)} error(s):", file=sys.stderr)
            for err in errors:
                print(f"  • {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
