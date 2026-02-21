#!/usr/bin/env -S uv run

"""Validate JSON examples in docs against schemas (using ucp-schema)."""

import json
import re
import shutil
import subprocess
import sys
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from jsonschema.validators import extend, validator_for
from referencing import Registry, Resource

# ANSI color codes
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_CYAN = "\033[96m"
COLOR_RESET = "\033[0m"

# Matches: <!-- schema: path/to/schema.json [op=create direction=request] -->
ANNOTATION_PATTERN = re.compile(r"<!--\s*schema:\s*(\S+)(?:\s+(.*))?\s*-->")
CODE_BLOCK_PATTERN = re.compile(r"```json\n(.*?)```", re.DOTALL)

ROOT_DIR = Path(__file__).parent.parent
SCHEMAS_DIR = ROOT_DIR / "source" / "schemas"
LOCAL_BIN = ROOT_DIR.parent / "ucp-schema" / "target" / "release" / "ucp-schema"

ELLIPSIS_SENTINEL = "__UCP_ELLIPSIS__"


def get_ucp_schema_bin() -> str:
    """Locate the ucp-schema binary. Fails loudly if not found."""
    if LOCAL_BIN.exists():
        return str(LOCAL_BIN)
    bin_path = shutil.which("ucp-schema")
    if not bin_path:
        msg = (
            "ucp-schema binary not found. Please ensure it is in your PATH "
            "or built in ../ucp-schema/target/release/ucp-schema"
        )
        raise FileNotFoundError(msg)
    return bin_path


def resolve_with_ucp_schema(schema_file: Path, op: str, direction: str) -> dict:
    """Resolve schema using ucp-schema CLI."""
    bin_path = get_ucp_schema_bin()
    cmd = [
        bin_path,
        "resolve",
        str(schema_file),
        f"--{direction}",
        "--op",
        op,
        "--bundle",
    ]
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=True, cwd=ROOT_DIR
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        msg = f"ucp-schema resolve failed for {schema_file}:"
        print(f"  {COLOR_YELLOW}[WARN]{COLOR_RESET} {msg}")
        print(f"    {e.stderr.strip()}")
        return {}


def load_schema_raw(schema_path: str) -> tuple[dict, Path]:
    """Load raw schema from file (fallback)."""
    file_path_str = schema_path.split("#")[0] if "#" in schema_path else schema_path
    path = Path(file_path_str)

    if not path.is_absolute():
        if (ROOT_DIR / path).exists():
            full_path = ROOT_DIR / path
        elif (SCHEMAS_DIR / path).exists():
            full_path = SCHEMAS_DIR / path
        else:
            raise FileNotFoundError(f"Schema file not found: {file_path_str}")
    else:
        full_path = path

    with full_path.open("r", encoding="utf-8") as f:
        return json.load(f), full_path


def strip_json_comments(text: str) -> str:
    """Strip C-style comments from JSON text."""
    pattern = r'("(?:\\.|[^"\\])*")|//.*?$|/\*.*?\*/'

    def replace(match: re.Match) -> str:
        return match.group(1) if match.group(1) else ""

    return re.sub(pattern, replace, text, flags=re.MULTILINE | re.DOTALL)


def handle_ellipses(text: str) -> str:
    """Replace [...] and {...} with valid JSON sentinels."""
    pattern = (
        r'("(?:\\.|[^"\\])*")|'
        r"(\[[\s\n]*\.\.\.[\s\n]*\]|\{[\s\n]*\.\.\.[\s\n]*\})"
    )

    def replace(match: re.Match) -> str:
        if match.group(1):
            return match.group(1)
        ellipsis = match.group(2)
        if ellipsis.startswith("["):
            return f'["{ELLIPSIS_SENTINEL}"]'
        return f'{{"{ELLIPSIS_SENTINEL}": true}}'

    return re.sub(pattern, replace, text)


def is_ellipsis(instance) -> bool:
    """Check if a JSON instance is a sentinel ellipsis wildcard."""
    if instance == [ELLIPSIS_SENTINEL]:
        return True
    return isinstance(instance, dict) and ELLIPSIS_SENTINEL in instance


def extract_json_from_mixed(text: str) -> str:
    """Extract JSON payload from potential HTTP/mixed content."""
    stripped = text.lstrip()
    is_http = re.match(
        r"^(?:POST|GET|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE|HTTP/)",
        stripped,
        re.IGNORECASE,
    )
    if is_http:
        match = re.search(r"(?m)^[ \t]*([\[\{])", text)
        if match:
            return text[match.start() :]
    return text


def wrap_validator_with_ellipsis(original):
    """Wrap a validator to ignore ellipsis sentinels."""

    def wrapper(validator, value, instance, schema):
        if is_ellipsis(instance):
            return
        yield from original(validator, value, instance, schema)

    return wrapper


def create_registry(canonical_uri: str, root_schema: dict, base_path: Path) -> Registry:
    """Create a referencing Registry that can resolve local file paths."""

    def retrieve_resource(uri: str, sfp: Path = base_path) -> Resource:
        parsed = urlparse(uri)
        candidate_path = None

        if uri.startswith("https://ucp.dev/schemas/"):
            rel_uri = uri.replace("https://ucp.dev/schemas/", "")
            candidate = SCHEMAS_DIR / rel_uri
            if candidate.exists():
                candidate_path = candidate

        is_file = parsed.scheme == "file" or not parsed.scheme
        if not candidate_path and is_file and Path(parsed.path).exists():
            candidate_path = Path(parsed.path)

        if not candidate_path and (SCHEMAS_DIR / parsed.path).exists():
            candidate_path = SCHEMAS_DIR / parsed.path

        if not candidate_path and sfp and (sfp.parent / parsed.path).exists():
            candidate_path = sfp.parent / parsed.path

        if candidate_path:
            res_content = json.loads(candidate_path.read_text(encoding="utf-8"))
            return Resource.from_contents(res_content)

        raise FileNotFoundError(f"Could not retrieve {uri}")

    resource = Resource.from_contents(root_schema)
    return Registry(retrieve=retrieve_resource).with_resource(canonical_uri, resource)


def validate_against_schema(
    instance: dict | list, schema_ref: str, op: str | None, direction: str | None
) -> None:
    """Run JSON Schema validation on the parsed instance."""
    root_schema, schema_file_path = load_schema_raw(schema_ref)
    canonical_uri = schema_file_path.absolute().as_uri()

    if op and direction:
        resolved_schema = resolve_with_ucp_schema(schema_file_path, op, direction)
        if resolved_schema:
            root_schema = resolved_schema

    if "#" in schema_ref:
        fragment = schema_ref.split("#", 1)[1]
        fragment = fragment if fragment.startswith("/") else f"/{fragment}"
        schema_to_validate = {"$ref": f"{canonical_uri}#{fragment}"}
    else:
        schema_to_validate = root_schema

    registry = create_registry(canonical_uri, root_schema, schema_file_path)
    validator_cls = validator_for(root_schema)

    ellipsis_validator_cls = extend(
        validator_cls,
        validators={
            k: wrap_validator_with_ellipsis(v)
            for k, v in validator_cls.VALIDATORS.items()
        },
    )

    validator = ellipsis_validator_cls(schema_to_validate, registry=registry)
    validator.validate(instance)


def process_example(
    json_text: str, schema_ref: str, attrs: dict, location: str, tally: dict
) -> bool:
    """Process and validate a single JSON example."""
    if schema_ref == "ignore":
        msg = f"{COLOR_CYAN}[IGNR]{COLOR_RESET} {location} ignored"
        print(msg)
        tally["IGNORE"] += 1
        return True

    op = attrs.get("op")
    direction = attrs.get("direction")
    is_empty_expected = attrs.get("body") == "empty"
    params_str = f"(op={op}, dir={direction})"

    potential_json = extract_json_from_mixed(json_text)

    if is_empty_expected:
        has_json_start = re.search(r"(?m)^[ \t]*([\[\{])", json_text)
        if not has_json_start:
            msg = f"{COLOR_GREEN}[PASS]{COLOR_RESET} {location} empty as expected"
            print(msg)
            tally["PASS"] += 1
            return True

        clean_json = strip_json_comments(potential_json).strip()
        if clean_json == "{}":
            msg = f"{COLOR_GREEN}[PASS]{COLOR_RESET} {location} empty object"
            print(msg)
            tally["PASS"] += 1
            return True

        msg = f"{location} expected empty body but found: {clean_json[:20]}..."
        print(f"{COLOR_RED}[FAIL]{COLOR_RESET} {msg}")
        tally["FAIL"] += 1
        return False

    clean_json = strip_json_comments(potential_json)
    final_json = handle_ellipses(clean_json).replace(
        "{{ ucp_version }}", date.today().isoformat()
    )

    try:
        instance = json.loads(final_json)
    except json.JSONDecodeError as e:
        msg = f"{COLOR_RED}[FAIL]{COLOR_RESET} {location} Invalid JSON {params_str}"
        print(msg)
        print(f"    Error: {e}")
        tally["FAIL"] += 1
        return False

    try:
        validate_against_schema(instance, schema_ref, op, direction)
        msg = f"{COLOR_GREEN}[PASS]{COLOR_RESET} {location} matches {schema_ref}"
        print(msg)
        tally["PASS"] += 1
        return True
    except Exception as e:
        msg = f"{COLOR_RED}[FAIL]{COLOR_RESET} {location} vs {schema_ref} {params_str}"
        print(msg)
        err_msg = getattr(e, "message", str(e))
        print(f"    Error: {err_msg}")
        tally["FAIL"] += 1
        return False


def parse_attributes(attrs_str: str) -> dict:
    """Parse key=value pairs from the annotation string."""
    attrs = {}
    for part in (attrs_str or "").split():
        if "=" in part:
            k, v = part.split("=", 1)
            attrs[k] = v
    return attrs


def validate_file(doc_file: Path, tally: dict) -> bool:
    """Scan and validate all annotated JSON examples within a markdown file."""
    content = doc_file.read_text(encoding="utf-8")
    annotations = list(ANNOTATION_PATTERN.finditer(content))
    validated_blocks = set()
    success = True

    for match in annotations:
        schema_ref = match.group(1)
        attrs = parse_attributes(match.group(2))
        start_pos = match.end()

        line_num = content[: match.start()].count("\n") + 1
        rel_path = doc_file.relative_to(ROOT_DIR)
        location = f"{rel_path}:{line_num}"

        block_match = CODE_BLOCK_PATTERN.search(content, start_pos)
        if not block_match:
            msg = f"{COLOR_YELLOW}[WARN]{COLOR_RESET} {location} Missing JSON block."
            print(msg)
            tally["WARN"] += 1
            continue

        if content[start_pos : block_match.start()].strip():
            msg = f"{location} Content found between annotation and JSON block."
            print(f"{COLOR_YELLOW}[WARN]{COLOR_RESET} {msg}")
            tally["WARN"] += 1
            continue

        validated_blocks.add(block_match.start())

        if not process_example(
            block_match.group(1), schema_ref, attrs, location, tally
        ):
            success = False

    for match in CODE_BLOCK_PATTERN.finditer(content):
        if match.start() not in validated_blocks:
            line_num = content[: match.start()].count("\n") + 1
            rel_path = doc_file.relative_to(ROOT_DIR)
            msg = f"{COLOR_YELLOW}[WARN]{COLOR_RESET} {rel_path}:{line_num} Unannotated"
            print(msg)
            tally["WARN"] += 1

    return success


def main(target_file: str | None = None) -> None:
    """Execute main logic."""
    try:
        get_ucp_schema_bin()
    except FileNotFoundError as e:
        print(f"{COLOR_RED}[ERROR]{COLOR_RESET} {e}")
        sys.exit(1)

    tally = {"PASS": 0, "FAIL": 0, "WARN": 0, "IGNORE": 0}
    docs_dir = ROOT_DIR / "docs"
    failed = False

    if target_file:
        target_path = Path(target_file)
        if not target_path.is_absolute():
            target_path = ROOT_DIR / target_path

        if not target_path.exists():
            msg = f"{COLOR_RED}[ERROR]{COLOR_RESET} File not found: {target_file}"
            print(msg)
            sys.exit(1)

        files_to_scan = [target_path]
        print(f"Validating annotated JSON examples in {target_file}...")
    else:
        files_to_scan = list(docs_dir.rglob("*.md"))
        print(f"Scanning {docs_dir} for annotated JSON examples...")

    for doc_file in files_to_scan:
        if not validate_file(doc_file, tally):
            failed = True

    print("\n" + "=" * 30)
    print("Summary:")
    print(f"  {COLOR_GREEN}PASS: {tally['PASS']}{COLOR_RESET}")
    print(f"  {COLOR_RED}FAIL: {tally['FAIL']}{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}WARN: {tally['WARN']}{COLOR_RESET}")
    print(f"  {COLOR_CYAN}IGNR: {tally['IGNORE']}{COLOR_RESET}")
    print("=" * 30)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    main(target)
