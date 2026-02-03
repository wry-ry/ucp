# *Macro Rendering Error*

*File*: `specification/overview.md`

*ValueError*: Invalid entity name format for def: capability.json (in file: specification/overview.md)

```text
Traceback (most recent call last):
  File "/home/runner/work/ucp/ucp/.venv/lib/python3.12/site-packages/mkdocs_macros/plugin.py", line 699, in render
    return md_template.render(**page_variables)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
  File "/home/runner/work/ucp/ucp/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "<template>", line 163, in top-level template code
  File "/home/runner/work/ucp/ucp/main.py", line 814, in extension_schema_fields
    return _read_schema_from_defs(entity_name, spec_file_name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/main.py", line 719, in _read_schema_from_defs
    return _render_table_from_schema(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/main.py", line 573, in _render_table_from_schema
    _render_embedded_table(
  File "/home/runner/work/ucp/ucp/main.py", line 452, in _render_embedded_table
    return _read_schema_from_defs(
           ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/main.py", line 687, in _read_schema_from_defs
    raise ValueError(f"Invalid entity name format for def: {entity_name}{get_error_context()}")
ValueError: Invalid entity name format for def: capability.json (in file: specification/overview.md)
```
