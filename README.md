# gosu-vcr-grpc
Pytest plugin to record grpc streams in cassettes.

## Usage
```python
import pytest

@pytest.mark.vcr_grpc
async def test_with_grpc():
    ...
```

## Compile deps
```bash
pip install pip-tools
pip-compile
```
