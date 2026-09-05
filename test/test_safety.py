import json

import pytest
import responses

from sapling import SaplingClient

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


@responses.activate
def test_safety_threshold_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'safety', json={'flagged': False}, status=200)
    client.safety('some text', threshold=0.8)
    body = json.loads(responses.calls[-1].request.body)
    assert body == {'key': API_KEY, 'text': 'some text', 'threshold': 0.8}


@responses.activate
def test_safety_threshold_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'safety', json={'flagged': False}, status=200)
    client.safety('some text')
    body = json.loads(responses.calls[-1].request.body)
    assert 'threshold' not in body


@responses.activate
def test_safety_spans_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'safety', json={'flagged': False}, status=200)
    client.safety('some text', spans=True)
    body = json.loads(responses.calls[-1].request.body)
    assert body == {'key': API_KEY, 'text': 'some text', 'spans': True}


@responses.activate
def test_safety_spans_false_still_sent_explicitly(client):
    # spans=False is a real value (not "unset"): send it rather than silently
    # dropping it, mirroring the threshold-style None sentinel.
    responses.add(responses.POST, BASE + 'safety', json={'flagged': False}, status=200)
    client.safety('some text', spans=False)
    body = json.loads(responses.calls[-1].request.body)
    assert body['spans'] is False


@responses.activate
def test_safety_spans_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'safety', json={'flagged': False}, status=200)
    client.safety('some text')
    body = json.loads(responses.calls[-1].request.body)
    assert 'spans' not in body


@responses.activate
def test_safety_batch_list_sent_as_texts(client):
    # A list of texts is the batch form (SAP-397): sent as `texts`, no `text`
    # key, and the {'results': [...]} body comes back untouched.
    batch_response = {'results': [{'flagged': True}, {'flagged': False}]}
    responses.add(responses.POST, BASE + 'safety', json=batch_response, status=200)
    result = client.safety(['first message', 'second message'], threshold=0.7)
    assert result == batch_response
    body = json.loads(responses.calls[-1].request.body)
    assert body == {'key': API_KEY, 'texts': ['first message', 'second message'],
                    'threshold': 0.7}


@responses.activate
def test_safety_batch_tuple_sent_as_list(client):
    responses.add(responses.POST, BASE + 'safety',
                  json={'results': [{'flagged': False}]}, status=200)
    client.safety(('only message',))
    body = json.loads(responses.calls[-1].request.body)
    assert body['texts'] == ['only message']
    assert 'text' not in body
