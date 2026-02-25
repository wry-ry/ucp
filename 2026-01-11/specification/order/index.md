# *Macro Rendering Error*

*File*: `specification/order.md`

*RuntimeError*: Error processing OpenAPI: [Errno 2] No such file or directory: 'source/services/shopping/rest.openapi.json' (in file: specification/order.md)

```text
Traceback (most recent call last):
  File "/home/runner/work/ucp/ucp/main.py", line 1016, in method_fields
    with full_path.open(encoding="utf-8") as f:
         ~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.13.11/x64/lib/python3.13/pathlib/_local.py", line 537, in open
    return io.open(self, mode, buffering, encoding, errors, newline)
           ~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
FileNotFoundError: [Errno 2] No such file or directory: 'source/services/shopping/rest.openapi.json'

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
  File "<template>", line 268, in top-level template code
  File "/home/runner/work/ucp/ucp/main.py", line 1187, in method_fields
    raise RuntimeError(
      f"Error processing OpenAPI: {e}{get_error_context()}"
    ) from e
RuntimeError: Error processing OpenAPI: [Errno 2] No such file or directory: 'source/services/shopping/rest.openapi.json' (in file: specification/order.md)
```
