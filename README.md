# Sapling AI Writing Assistant Python Client


Installation
--------

Install the `sapling-py` package with [pip](https://sapling.ai)


```
python -m pip install sapling-py
```


Documentation
-------------

Documentation for the client is availible at [Read the Docs](https://sapling.readthedocs.io/) and on [sapling.ai](https://sapling.ai/docs).


Quick Start
-----------

- Register for an account at [sapling.ai](https://sapling.ai)
- Get a development api key in the [dashboard](https://sapling.ai/user_settings)

```
from sapling import SaplingClient

api_key = '<api_key>'
client = SaplingClient(api_key=api_key)

client.edits('Lets get started!', session_id='test')

# View the edits
[{
  'id': 'aa5ee291-a073-5146-8ebc-c9c899d01278',
  'sentence': 'Lets get started!',
  'sentence_start': 0,
  'start': 0
  'end': 4,
  'replacement': "Let's",
  'error_type': 'R:OTHER',
  'general_error_type': 'Other',
}]

```

- More information on [request options and response structure](https://sapling.ai/docs/api/edits-overview)
- You can read more about getting a production key in the [documentation](https://sapling.ai/docs/api/api-access).

License
-------

Copyright 2022 Sapling Intelligence Licensed under the Apache License, Version 2.0.
