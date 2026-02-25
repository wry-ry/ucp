# *Macro Rendering Error*

*File*: `specification/fulfillment.md`

*RuntimeError*: Error loading extension 'fulfillment_resp': [Errno 2] No such file or directory: 'source/schemas/shopping/fulfillment_resp.json' (in file: specification/fulfillment.md)

```text
Traceback (most recent call last):
  File "/home/runner/work/ucp/ucp/main.py", line 974, in extension_fields
    with full_path.open(encoding="utf-8") as f:
         ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/pathlib/_local.py", line 537, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'source/schemas/shopping/fulfillment_resp.json'

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/site-packages/mkdocs_macros/plugin.py", line 699, in render
    return md_template.render(**page_variables)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/site-packages/jinja2/environment.py", line 1295, in render
    self.environment.handle_exception()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/site-packages/jinja2/environment.py", line 942, in handle_exception
    raise rewrite_traceback_stack(source=source)
  File "<template>", line 55, in top-level template code
  File "/home/runner/work/ucp/ucp/main.py", line 994, in extension_fields
    raise RuntimeError(
      f"Error loading extension '{entity_name}': {e}{get_error_context()}"
    ) from e
RuntimeError: Error loading extension 'fulfillment_resp': [Errno 2] No such file or directory: 'source/schemas/shopping/fulfillment_resp.json' (in file: specification/fulfillment.md)
```
