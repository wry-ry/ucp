#   Copyright 2026 UCP Authors
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


"""MkDocs hooks for UCP documentation.

This module contains functions that are executed during the MkDocs build
process:
- Copy source files into site directory with $ref resolution
- Publish bundled schemas to /schemas/{version}/ for consumers
"""

import json
import logging
import shutil
from pathlib import Path

log = logging.getLogger("mkdocs")

# Directory containing capability schemas to publish (excludes types/ subdir)
SCHEMAS_DIR = Path("source/schemas/shopping")


def _publish_versioned_schemas(config):
  """Publish source schemas to /schemas/.

  Copies source schemas with ucp_* annotations intact and injects version.
  Consumers use ucp-schema to resolve for their specific direction/operation.

  Mike handles the doc version path (e.g., /2026-01-11/schemas/checkout.json).
  """
  version = config.get("extra", {}).get("ucp_version")
  if not version:
    log.warning("No ucp_version in mkdocs.yml extra config, skipping schemas")
    return

  output_dir = Path(config["site_dir"]) / "schemas"
  output_dir.mkdir(parents=True, exist_ok=True)

  # Copy all schemas recursively (includes types/ subdirectory)
  for schema_file in SCHEMAS_DIR.rglob("*.json"):
    try:
      with schema_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

      # Inject version
      data.setdefault("ucp", {})["version"] = version

      # Preserve directory structure
      rel_path = schema_file.relative_to(SCHEMAS_DIR)
      output_file = output_dir / rel_path
      output_file.parent.mkdir(parents=True, exist_ok=True)

      with output_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
      log.info("Published schema: %s", output_file)

    except (json.JSONDecodeError, OSError) as e:
      log.error("Failed to process %s: %s", schema_file, e)


def _process_refs(data, current_file_dir):
  """Recursively processes $ref fields in a JSON object."""
  if isinstance(data, dict):
    for key, value in data.items():
      if (
        key == "$ref"
        and isinstance(value, str)
        and not value.startswith(("#", "http"))
      ):
        ref_parts = value.split("#", 1)
        relative_path = ref_parts[0]
        fragment = f"#{ref_parts[1]}" if len(ref_parts) > 1 else ""

        if not relative_path:
          continue

        ref_file_path = (current_file_dir / relative_path).resolve()

        try:
          with ref_file_path.open("r", encoding="utf-8") as f:
            ref_data = json.load(f)

          if "$id" in ref_data:
            data[key] = ref_data["$id"] + fragment
          else:
            log.warning(
              f"No '$id' found in {ref_file_path}. "
              f"Keeping original '$ref': {value}"
            )
        except FileNotFoundError:
          log.error(
            f"Referenced file not found: {ref_file_path}. "
            f"Keeping original '$ref': {value}"
          )
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
          log.error(
            f"Failed to read referenced file {ref_file_path}: {e}. "
            f"Keeping original '$ref': {value}"
          )
      else:
        _process_refs(value, current_file_dir)
  elif isinstance(data, list):
    for item in data:
      _process_refs(item, current_file_dir)


def on_post_build(config):
  """Copy and process source files into the site directory.

  For JSON files, it resolves $ref paths to absolute URLs.
  Non-JSON files are copied as-is.

  Also publishes bundled schemas to /schemas/{version}/ for consumers.
  """
  # Publish versioned schemas for consumers
  _publish_versioned_schemas(config)

  # Copy source files (with ucp_* annotations intact for agents)
  base_src_path = Path.cwd() / "source"
  if not base_src_path.exists():
    log.warning("Source directory not found: %s", base_src_path)
    return

  for src_file in base_src_path.rglob("*"):
    if not src_file.is_file():
      continue
    rel_path = src_file.relative_to(base_src_path).as_posix()

    if not src_file.name.endswith(".json"):
      dest_file = Path(config["site_dir"]) / rel_path
      dest_dir = dest_file.parent
      dest_dir.mkdir(exist_ok=True, parents=True)
      shutil.copy2(src_file, dest_file)
      log.info("Copied %s to %s", src_file, dest_file)
      continue

    # Process JSON files
    try:
      with src_file.open("r", encoding="utf-8") as f:
        data = json.load(f)

      # Determine the final relative path for the destination from $id
      file_id = data.get("$id")
      prefix = "https://ucp.dev"
      if file_id and file_id.startswith(prefix):
        file_rel_path = file_id[len(prefix) :].lstrip("/")
      else:
        file_rel_path = rel_path

      # Process refs using the final path
      _process_refs(data, src_file.parent)

      dest_file = Path(config["site_dir"]) / file_rel_path
      dest_dir = dest_file.parent

      dest_dir.mkdir(exist_ok=True, parents=True)
      with dest_file.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
      log.info("Processed and copied %s to %s", src_file, dest_file)

    except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
      log.error(
        "Failed to process JSON file %s, copying as-is: %s", src_file, e
      )
      # Fallback to copying if processing fails
      dest_file = Path(config["site_dir"]) / rel_path
      dest_dir = dest_file.parent
      dest_dir.mkdir(exist_ok=True, parents=True)
      shutil.copy2(src_file, dest_file)
