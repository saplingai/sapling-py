# Usage


(installation)=
Installation
--------

Install the `sapling-py` package with [pip](https://pip.pypa.io/en/stable/installation/).
Here's the [package link](https://pypi.org/project/sapling-py/).


```
python -m pip install sapling-py
```


(quickstart)=
Quickstart
-----------

- Register for an account at [Sapling.ai](https://sapling.ai).
- After registering and signing in, generate a development API key in your [dashboard](https://sapling.ai/user_settings).
- Install the Python client by following the installation steps above.

```python
from sapling import SaplingClient

API_KEY = '<YOUR_API_KEY>'
client = SaplingClient(api_key=API_KEY)
edits = client.edits('Lets get started!', session_id='test_session')
```


- The result should be an array of edits of this form:

```json
[{
  "id": "aa5ee291-a073-5146-8ebc-c9c899d01278",
  "sentence": "Lets get started!",
  "sentence_start": 0,
  "start": 0
  "end": 4,
  "replacement": "Let's",
  "error_type": "R:OTHER",
  "general_error_type": "Other",
}]
```

- More information on [request options and response structure](https://sapling.ai/docs/api/edits-overview).
- Get a production key by following [this documentation](https://sapling.ai/docs/api/api-access).
