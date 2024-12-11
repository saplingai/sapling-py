# Sapling Python Client

Python SDK wrapper for the [Sapling.ai API](https://sapling.ai/docs).

Try our [grammar check demo](https://sapling.ai/grammar-check).
Compare against leading grammar checking tools and APIs like Grammarly (Grammerly), LanguageTool, ProWritingAid and Ginger.

## Overview

Sapling is a toolkit for helping developers build language model-powered applications.
The API provides spelling and grammar checking, autocomplete, tone detection, rephrasing, AI detection, and more.

Key Features:
- **60% More Corrections**: Outperforms [competing solutions](https://sapling.ai/comparison/api) at similar accuracy levels using state-of-the-art generative AI models.
- **Real-Time Performance**: Experience the same low-latency corrections as Sapling's native integrations.
- **Comprehensive Error Detection**: Identifies over 20 error types including prepositions, noun forms, verb tense, with both high-level and fine-grained error information.
- **Domain-Specific Models**: Get corrections optimized for your content type, from academic writing, to doctors notes, to user-generated reviews.
- **Enterprise-Grade Security**: Features include no data retention policies, [self-hosted/on-premises](https://sapling.ai/onprem) deployment options, and enterprise-grade [security policies and procedures](https://sapling.ai/security).
- **Rich Text Editor Integration**: Supports TinyMCE, CKEditor, QuillJS, Trix, ProseMirror, WordPress, Draft.js, Froala, Lexical and more. For web-based editors, consider using our [JavaScript SDK](https://sapling.ai/docs/sdk/JavaScript/quickstart) for display UI components.

## Installation

Install the `sapling-py` package with [pip](https://pip.pypa.io/en/stable/installation/)

```
python -m pip install sapling-py
```

## Documentation
Documentation for the client is available at [Read the Docs](https://sapling.readthedocs.io/) and
documentation for the HTTP API is available at [Sapling.ai](https://sapling.ai/docs).

## Quickstart

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

## License

Copyright 2024--present Sapling Intelligence, Inc.

Licensed under the Apache License, Version 2.0.