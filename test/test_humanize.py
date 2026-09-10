import json

import pytest
import responses

from sapling import SaplingClient

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

TEXT = ('Furthermore, it is important to note that our solution leverages '
        'cutting-edge technology. The team ships fixes fast.')

HUMANIZE_RESPONSE = {
    'text': 'One more thing worth knowing: we build on the newest tech out '
            'there. The team ships fixes fast.',
    'original_text': TEXT,
    'ai_score': 0.74,
    'sentences': [
        {'original': 'Furthermore, it is important to note that our solution '
                     'leverages cutting-edge technology.',
         'humanized': 'One more thing worth knowing: we build on the newest '
                      'tech out there.',
         'ai_score': 0.91, 'was_rephrased': True},
        {'original': 'The team ships fixes fast.',
         'humanized': 'The team ships fixes fast.',
         'ai_score': 0.12, 'was_rephrased': False},
    ],
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_humanize_returns_json_and_sends_key(client):
    responses.add(responses.POST, BASE + 'humanize',
                  json=HUMANIZE_RESPONSE, status=200)
    result = client.humanize(TEXT)
    assert result == HUMANIZE_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': TEXT}


@responses.activate
def test_humanize_posts_to_humanize_endpoint(client):
    responses.add(responses.POST, BASE + 'humanize',
                  json=HUMANIZE_RESPONSE, status=200)
    client.humanize(TEXT)
    assert responses.calls[-1].request.url == BASE + 'humanize'


@responses.activate
def test_humanize_threshold_sent_only_when_given(client):
    responses.add(responses.POST, BASE + 'humanize',
                  json=HUMANIZE_RESPONSE, status=200)
    client.humanize(TEXT)
    assert 'threshold' not in _last_request_body()

    client.humanize(TEXT, threshold=0.8)
    assert _last_request_body()['threshold'] == 0.8

    # 0 is a real threshold, not a missing one.
    client.humanize(TEXT, threshold=0)
    assert _last_request_body()['threshold'] == 0
