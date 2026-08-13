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
