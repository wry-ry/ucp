#!/usr/bin/env -S uv run

"""Validate JSON examples in docs against schemas (using ucp-schema)."""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse

from jsonschema.validators import validator_for, extend
from referencing import Registry, Resource

# ANSI color codes
COLOR_RED = "\033[91m"
COLOR_GREEN = "\033[92m"
COLOR_YELLOW = "\033[93m"
COLOR_RESET = "\033[0m"

# Matches: <!-- schema: path/to/schema.json [op=create direction=request] -->
ANNOTATION_PATTERN = re.compile(r"<!--\s*schema:\s*(\S+)(?:\s+(.*))?\s*-->")
CODE_BLOCK_PATTERN = re.compile(r"""```json\n(.*?)```""", re.DOTALL)

ROOT_DIR = Path(__file__).parent.parent
SCHEMAS_DIR = ROOT_DIR / "source" / "schemas"
# Try to find ucp-schema binary in sibling directory
LOCAL_BIN = ROOT_DIR.parent / "ucp-schema" / "target" / "release" / "ucp-schema"

# Sentinel value for ellipsis wildcards
ELLIPSIS_SENTINEL = "__UCP_ELLIPSIS__"


def get_ucp_schema_bin():
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


def resolve_with_ucp_schema(schema_file, op, direction):
    """Resolve schema using ucp-schema CLI."""
    bin_path = get_ucp_schema_bin()

    cmd = [
        bin_path,
        "resolve",
        str(schema_file),
        f"--{direction}",
        "--op",
        op,
        "--bundle",  # Bundle external refs
    ]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            cwd=ROOT_DIR,
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        msg = f"ucp-schema resolve failed for {schema_file}:"
        print(f"  {COLOR_YELLOW}[WARN]{COLOR_RESET} {msg}")
        print(f"    {e.stderr.strip()}")
        return None


def load_schema_raw(schema_path):
    """Load raw schema from file (fallback)."""
    if "#" in schema_path:
        file_path_str = schema_path.split("#")[0]
    else:
        file_path_str = schema_path

    path = Path(file_path_str)
    if not path.is_absolute():
        # Try finding it in repo root
        candidate = ROOT_DIR / path
        if candidate.exists():
            full_path = candidate
        else:
            # Try source/schemas (if user just provided filename)
            candidate = SCHEMAS_DIR / path
            if candidate.exists():
                full_path = candidate
            else:
                msg = f"Schema file not found: {file_path_str}"
                raise FileNotFoundError(msg)
    else:
        full_path = path

    with full_path.open("r") as f:
        return json.load(f), full_path


def strip_json_comments(text):
    """Strip C-style comments from JSON text."""
    # Matches strings OR comments. We keep strings, remove comments.
    pattern = r'("(?:\\.|[^"\\])*")|//.*?$|/\*.*?\*/'

    def replace(match):
        if match.group(1):
            return match.group(1)
        return ""

    return re.sub(pattern, replace, text, flags=re.MULTILINE | re.DOTALL)


def handle_ellipses(text):
    """Replace [...] and {...} with valid JSON sentinels."""
    # Use regex that matches either a string literal OR an ellipsis pattern.
    # This avoids replacing '...' if it happens to be inside a string literal.
    pattern = (
        r'("(?:\\.|[^"\\])*")|'
        r"(\[[\s\n]*\.\.\.[\s\n]*\]|\{[\s\n]*\.\.\.[\s\n]*\})"
    )

    def replace(match):
        if match.group(1):  # String literal
            return match.group(1)

        # It's an ellipsis pattern
        ellipsis = match.group(2)
        if ellipsis.startswith("["):
            return f'["{ELLIPSIS_SENTINEL}"]'
        return f'{{"{ELLIPSIS_SENTINEL}": true}}'

    return re.sub(pattern, replace, text)


def is_ellipsis(instance):
    """Check if a JSON instance is a sentinel ellipsis wildcard."""
    if instance == [ELLIPSIS_SENTINEL]:
        return True
    return isinstance(instance, dict) and ELLIPSIS_SENTINEL in instance


def extract_json_from_mixed(text):
    """Extract JSON payload from potential HTTP/mixed content."""
    stripped = text.lstrip()
    is_http = re.match(
        r"^(?:POST|GET|PUT|DELETE|PATCH|HEAD|OPTIONS|CONNECT|TRACE|HTTP/)",
        stripped,
        re.IGNORECASE,
    )

    if is_http:
        # Find first '{' or '[' that is likely the start of JSON
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


def validate_examples(target_file=None):
    """Scan docs and validate examples."""
    # Fail fast if ucp-schema is not found
    try:
        get_ucp_schema_bin()
    except FileNotFoundError as e:
        print(f"{COLOR_RED}[ERROR]{COLOR_RESET} {e}")
        sys.exit(1)

    docs_dir = ROOT_DIR / "docs"
    failed = False

    tally = {"PASS": 0, "FAIL": 0, "WARN": 0}

    if target_file:
        target_path = Path(target_file)
        if not target_path.is_absolute():
            target_path = ROOT_DIR / target_path

        if not target_path.exists():
            msg = (
                f"{COLOR_RED}[ERROR]{COLOR_RESET} "
                f"File not found: {target_file}"
            )
            print(msg)
            sys.exit(1)

        files_to_scan = [target_path]
        print(f"Validating annotated JSON examples in {target_file}...")
    else:
        files_to_scan = list(docs_dir.rglob("*.md"))
        print(f"Scanning {docs_dir} for annotated JSON examples...")

    for doc_file in files_to_scan:
        content = doc_file.read_text(encoding="utf-8")

        annotations = list(ANNOTATION_PATTERN.finditer(content))
        validated_blocks = set()

        if annotations:
            for match in annotations:
                schema_ref = match.group(1)
                attrs_str = match.group(2) or ""
                start_pos = match.end()

                # Calculate location (1-based)
                line_num = content[: match.start()].count("\n") + 1
                rel_path = doc_file.relative_to(ROOT_DIR)
                location = f"{rel_path}:{line_num}"

                # Parse attributes
                attrs = {}
                for part in attrs_str.split():
                    if "=" in part:
                        k, v = part.split("=", 1)
                        attrs[k] = v

                op = attrs.get("op")
                direction = attrs.get("direction")  # request or response
                is_empty_expected = attrs.get("body") == "empty"
                params_str = f"(op={op}, dir={direction})"

                block_match = CODE_BLOCK_PATTERN.search(content, start_pos)
                if not block_match:
                    msg = f"{location} Annotation for {schema_ref} found "
                    print(
                        f"{COLOR_YELLOW}[WARN]{COLOR_RESET} {msg}"
                        "but no JSON block follows."
                    )
                    tally["WARN"] += 1
                    continue

                gap = content[start_pos : block_match.start()]
                if gap.strip():
                    msg = (
                        f"{location} Content found between annotation "
                        f"{schema_ref} "
                    )
                    print(
                        f"{COLOR_YELLOW}[WARN]{COLOR_RESET} {msg}"
                        "and JSON block. Skipping."
                    )
                    tally["WARN"] += 1
                    continue

                validated_blocks.add(block_match.start())

                json_text = block_match.group(1)

                # Handle mixed HTTP/JSON content, comments, and ellipses
                potential_json = extract_json_from_mixed(json_text)

                if is_empty_expected:
                    has_json_start = re.search(r"(?m)^[ \t]*([\[\{])", json_text)
                    if not has_json_start:
                        # Success: no JSON body found
                        print(f"{COLOR_GREEN}[PASS]{COLOR_RESET} {location} is empty as expected")
                        tally["PASS"] += 1
                        continue

                    # If JSON found, must be empty object {}
                    clean_json = strip_json_comments(potential_json).strip()
                    if clean_json == "{}":
                        print(f"{COLOR_GREEN}[PASS]{COLOR_RESET} {location} is empty object as expected")
                        tally["PASS"] += 1
                        continue
                    else:
                        msg = f"{location} expected empty body but found: {clean_json[:20]}..."
                        print(f"{COLOR_RED}[FAIL]{COLOR_RESET} {msg}")
                        tally["FAIL"] += 1
                        failed = True
                        continue

                clean_json = strip_json_comments(potential_json)
                final_json = handle_ellipses(clean_json)

                try:
                    instance = json.loads(final_json)
                except json.JSONDecodeError as e:
                    msg = f"{location} Invalid JSON in example for {schema_ref}"
                    print(
                        f"{COLOR_RED}[FAIL]{COLOR_RESET} {msg} {params_str}"
                    )
                    print(f"    Error: {e}")
                    tally["FAIL"] += 1
                    failed = True
                    continue

                try:
                    resolved_schema = None
                    cur_schema_file_path = None

                    # Locate file first
                    _, cur_schema_file_path = load_schema_raw(schema_ref)

                    # Convert to absolute file URI for the Registry
                    canonical_uri = cur_schema_file_path.absolute().as_uri()

                    if op and direction:
                        resolved_schema = resolve_with_ucp_schema(
                            cur_schema_file_path, op, direction
                        )

                    if resolved_schema:
                        root_schema = resolved_schema
                    else:
                        root_schema, _ = load_schema_raw(schema_ref)

                    # Determine the target schema to validate against
                    if "#" in schema_ref:
                        fragment = schema_ref.split("#", 1)[1]
                        if not fragment.startswith("/"):
                            fragment = "/" + fragment
                        ref_uri = f"{canonical_uri}#{fragment}"
                        schema_to_validate = {"$ref": ref_uri}
                    else:
                        schema_to_validate = root_schema

                    # Validate
                    def retrieve_resource(uri, sfp=cur_schema_file_path):
                        parsed = urlparse(uri)
                        candidate_path = None
                        if uri.startswith("https://ucp.dev/schemas/"):
                            base_uri = "https://ucp.dev/schemas/"
                            rel_uri = uri.replace(base_uri, "")
                            candidate = SCHEMAS_DIR / rel_uri
                            if candidate.exists():
                                candidate_path = candidate

                        is_file = parsed.scheme == "file" or not parsed.scheme
                        if not candidate_path and is_file:
                            candidate = Path(parsed.path)
                            if candidate.exists():
                                candidate_path = candidate

                        if not candidate_path:
                            candidate = SCHEMAS_DIR / parsed.path
                            if candidate.exists():
                                candidate_path = candidate

                        if not candidate_path and sfp:
                            candidate = sfp.parent / parsed.path
                            if candidate.exists():
                                candidate_path = candidate

                        if candidate_path:
                            res_txt = candidate_path.read_text(encoding="utf-8")
                            res_content = json.loads(res_txt)
                            return Resource.from_contents(res_content)

                        raise FileNotFoundError(f"Could not retrieve {uri}")

                    resource = Resource.from_contents(root_schema)
                    registry = Registry(
                        retrieve=retrieve_resource
                    ).with_resource(canonical_uri, resource)

                    validator_cls = validator_for(root_schema)

                    # Create new validator class that intercepts ellipsis
                    ellipsis_validator_cls = extend(
                        validator_cls,
                        validators={
                            k: wrap_validator_with_ellipsis(v)
                            for k, v in validator_cls.VALIDATORS.items()
                        },
                    )

                    validator = ellipsis_validator_cls(
                        schema_to_validate, registry=registry
                    )

                    validator.validate(instance)
                    msg = f"{location} matches {schema_ref} {params_str}"
                    print(f"{COLOR_GREEN}[PASS]{COLOR_RESET} {msg}")
                    tally["PASS"] += 1

                except Exception as e:
                    msg = f"{location} does not match {schema_ref}"
                    print(f"{COLOR_RED}[FAIL]{COLOR_RESET} {msg} {params_str}")
                    if hasattr(e, "message"):
                        print(f"    Error: {e.message}")
                    else:
                        print(f"    {e}")
                    tally["FAIL"] += 1
                    failed = True

        # Check for unannotated blocks
        for match in CODE_BLOCK_PATTERN.finditer(content):
            if match.start() not in validated_blocks:
                line_num = content[: match.start()].count("\n") + 1
                rel_path = doc_file.relative_to(ROOT_DIR)
                msg = f"{rel_path}:{line_num} Unannotated JSON example."
                print(f"{COLOR_YELLOW}[WARN]{COLOR_RESET} {msg}")
                tally["WARN"] += 1

    print("\n" + "=" * 30)
    print("Summary:")
    print(f"  {COLOR_GREEN}PASS: {tally['PASS']}{COLOR_RESET}")
    print(f"  {COLOR_RED}FAIL: {tally['FAIL']}{COLOR_RESET}")
    print(f"  {COLOR_YELLOW}WARN: {tally['WARN']}{COLOR_RESET}")
    print("=" * 30)

    if failed:
        sys.exit(1)


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else None
    validate_examples(target)
