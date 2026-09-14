import json

import pytest
import responses

from sapling import SaplingClient

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

RESPONSE = {
    'claims': [
        {
            'claim': 'The warranty lasts two years.',
            'verdict': 'supported',
            'confidence': 0.95,
            'evidence': ['covered by a two-year limited warranty'],
            'rationale': 'The source states the warranty period directly.',
        },
    ],
    'all_supported': True,
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


@responses.activate
def test_factcheck_minimal_request(client):
    responses.add(responses.POST, BASE + 'factcheck', json=RESPONSE, status=200)
    result = client.factcheck(
        'Every unit is covered by a two-year limited warranty.',
        ['The warranty lasts two years.'],
    )
    assert result == RESPONSE
    body = json.loads(responses.calls[-1].request.body)
    assert body == {
        'key': API_KEY,
        'text': 'Every unit is covered by a two-year limited warranty.',
        'claims': ['The warranty lasts two years.'],
    }


@responses.activate
def test_factcheck_context_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'factcheck', json=RESPONSE, status=200)
    client.factcheck('some source', ['a claim'], context='a product FAQ page')
    body = json.loads(responses.calls[-1].request.body)
    assert body['context'] == 'a product FAQ page'


@responses.activate
def test_factcheck_context_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'factcheck', json=RESPONSE, status=200)
    client.factcheck('some source', ['a claim'])
    body = json.loads(responses.calls[-1].request.body)
    assert 'context' not in body


@responses.activate
def test_factcheck_claims_sent_verbatim_in_order(client):
    # Entries in the response are index-keyed to the submitted claims — the
    # client must not reorder, dedupe, or otherwise touch the list.
    claims = ['claim B', 'claim A', 'claim B']
    responses.add(responses.POST, BASE + 'factcheck', json=RESPONSE, status=200)
    client.factcheck('some source', claims)
    body = json.loads(responses.calls[-1].request.body)
    assert body['claims'] == claims


@responses.activate
def test_factcheck_html_source_sent_verbatim(client):
    # Tag stripping is server-side (the response's optional `source` echoes
    # the normalized text); the client must not pre-strip.
    text = '<p>First point.</p><p>Second point.</p>'
    responses.add(responses.POST, BASE + 'factcheck', json=RESPONSE, status=200)
    client.factcheck(text, ['a claim'])
    body = json.loads(responses.calls[-1].request.body)
    assert body['text'] == text


@responses.activate
def test_factcheck_normalized_source_passthrough(client):
    # When the API normalized the text it returns `source`; the client hands
    # the response through untouched.
    resp = dict(RESPONSE, source='First point. Second point.')
    responses.add(responses.POST, BASE + 'factcheck', json=resp, status=200)
    result = client.factcheck('<p>First point.</p><p>Second point.</p>', ['a claim'])
    assert result['source'] == 'First point. Second point.'
