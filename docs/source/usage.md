# Usage


(installation)=
Installation
--------

Install the `sapling-py` package with [pip](https://pip.pypa.io/en/stable/installation/). [Package link](https://sapling.ai)


```
python -m pip install sapling-py
```


(quickstart)=
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
