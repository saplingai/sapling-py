# Sapling Python Client

Python wrapper for the [Sapling.ai API](https://sapling.ai/api).

Try out a [grammar check demo](https://sapling.ai/grammar-check).
Compare against grammar checking tools and APIs like Grammarly (Grammerly), LanguageTool, ProWritingAid and Ginger.

Functionality
--------

Sapling is an AI messaging assistant.
The API currently offers spelling and grammar checking endpoints.

Benefits include:
- **60% more grammar corrections**: compared to [other systems](https://sapling.ai/comparison/api) at similar accuracy using state-of-the-art machine learning systems for natural language processing.
- **Low Latency**: Achieve the same real-time performance that users of Sapling's own interface experience.
- **Over 20 error types**: Error categories such as preposition, noun form, and verb tense, including both high-level and fine-grained error information.
- **Custom Models**: Get corrections and edits tuned to the domain of your text—for example academic writing vs. subtitles.
- **Enterprise Security**: Ask us about our no data retention policies, [self-hosted/on-premises](https://sapling.ai/onprem) deployment options, and other [cybersecurity policies and procedures](https://sapling.ai/security).
- **Rich Text Editor Support**: TinyMCE, CKEditor, QuillJS, Trix, ProseMirror, WordPress, Draft.js, Froala, Lexical and others. Consider using [Sapling's JavaScript SDK](https://sapling.ai/docs/sdk/JavaScript/quickstart) for displaying the API's outputs on webpage editors.


Installation
--------

Install the `sapling-py` package with [pip](https://pip.pypa.io/en/stable/installation/)


```
python -m pip install sapling-py
```


Documentation
-------------

Documentation for the client is available at [Read the Docs](https://sapling.readthedocs.io/) and
documentation for the HTTP API is available at [Sapling.ai](https://sapling.ai/docs).


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

The result should be an array of edits of this form:

```json
[{
  "id": "aa5ee291-a073-5146-8ebc-c9c899d01278",
  "sentence": "Lets get started!",
  "sentence_start": 0,
  "start": 0,
  "end": 4,
  "replacement": "Let's",
  "error_type": "R:OTHER",
  "general_error_type": "Other",
}]
```

Get a production key by following [this documentation](https://sapling.ai/docs/api/api-access).

Here's some more information on [request options and response structure](https://sapling.ai/docs/api/edits-overview).

License
-------

Copyright 2022 Sapling Intelligence, Inc.

Licensed under the Apache License, Version 2.0.
