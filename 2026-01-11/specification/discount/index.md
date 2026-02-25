# *Macro Rendering Error*

*File*: `specification/discount.md`

*FileNotFoundError*: Schema file 'discount_resp.json' not found in any schema directory (in file: specification/discount.md).

```text
Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/site-packages/mkdocs_macros/plugin.py", line 699, in render
    return md_template.render(**page_variables)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "<template>", line 63, in top-level template code
  File "/home/runner/work/ucp/ucp/main.py", line 834, in extension_schema_fields
    return _read_schema_from_defs(entity_name, spec_file_name)
  File "/home/runner/work/ucp/ucp/main.py", line 747, in _read_schema_from_defs
    raise FileNotFoundError(
    ...<2 lines>...
    )
FileNotFoundError: Schema file 'discount_resp.json' not found in any schema directory (in file: specification/discount.md).
```
