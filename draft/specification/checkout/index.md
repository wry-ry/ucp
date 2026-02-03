# *Macro Rendering Error*

*File*: `specification/checkout.md`

*RuntimeError*: Failed to resolve '' (in file: specification/checkout.md). Ensure ucp-schema is installed: `cargo install ucp-schema`

```text
Traceback (most recent call last):
  File "/home/runner/work/ucp/ucp/.venv/lib/python3.12/site-packages/mkdocs_macros/plugin.py", line 699, in render
    return md_template.render(**page_variables)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
  File "/home/runner/work/ucp/ucp/.venv/lib/python3.12/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "<template>", line 462, in top-level template code
  File "/home/runner/work/ucp/ucp/main.py", line 801, in extension_schema_fields
    return _read_schema_from_defs(entity_name, spec_file_name)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/main.py", line 706, in _read_schema_from_defs
    return _render_table_from_schema(
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/main.py", line 573, in _render_table_from_schema
    _render_embedded_table(
  File "/home/runner/work/ucp/ucp/main.py", line 462, in _render_embedded_table
    embedded_data = _render_table_from_ref(
                    ^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/ucp/ucp/main.py", line 417, in _render_table_from_ref
    raise RuntimeError(
RuntimeError: Failed to resolve '' (in file: specification/checkout.md). Ensure ucp-schema is installed: `cargo install ucp-schema`
```
