import json

import pytest
import responses

from sapling import SaplingClient

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

PII_RESPONSE = {
    'entities': [{
        'type': 'email', 'text': 'jane@example.com', 'start': 6, 'end': 22,
        'replacement': '[EMAIL]',
    }],
    'flagged': True,
    'types': ['email'],
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_pii_returns_json_and_sends_key(client):
    responses.add(responses.POST, BASE + 'pii', json=PII_RESPONSE, status=200)
    result = client.pii('Email jane@example.com')
    assert result == PII_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': 'Email jane@example.com'}


@responses.activate
def test_pii_optional_params_sent_when_provided(client):
    payload = dict(PII_RESPONSE, redacted_text='Email [EMAIL]')
    responses.add(responses.POST, BASE + 'pii', json=payload, status=200)
    result = client.pii('Email jane@example.com', types=('email', 'phone'), redact=True)
    assert result['redacted_text'] == 'Email [EMAIL]'
    body = _last_request_body()
    assert body['types'] == ['email', 'phone']
    assert body['redact'] is True


@responses.activate
def test_pii_optional_params_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'pii', json=PII_RESPONSE, status=200)
    client.pii('some text')
    body = _last_request_body()
    assert 'types' not in body
    assert 'redact' not in body
