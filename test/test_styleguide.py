import json

import pytest
import responses

from sapling import SaplingClient

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

TEXT = 'Our synergy-driven solution was leveraged by the team. It is really great!!'

RULES = ['no jargon',
         {'name': 'no exclamation marks',
          'description': 'Never use exclamation marks.'}]

STYLEGUIDE_RESPONSE = {
    'violations': [
        {'rule': 'no jargon', 'text': 'synergy-driven solution',
         'start': 4, 'end': 27, 'note': 'Corporate buzzword.',
         'suggestion': 'effective product'},
        {'rule': 'no exclamation marks', 'text': 'really great!!',
         'start': 61, 'end': 75, 'note': 'Double exclamation.',
         'suggestion': 'really great.'},
    ],
    'rules': ['no jargon', 'no exclamation marks'],
    'compliant': False,
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_styleguide_returns_json_and_sends_key_text_rules(client):
    responses.add(responses.POST, BASE + 'styleguide',
                  json=STYLEGUIDE_RESPONSE, status=200)
    result = client.styleguide(TEXT, rules=RULES)
    assert result == STYLEGUIDE_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': TEXT, 'rules': RULES}


@responses.activate
def test_styleguide_posts_to_styleguide_endpoint(client):
    responses.add(responses.POST, BASE + 'styleguide',
                  json=STYLEGUIDE_RESPONSE, status=200)
    client.styleguide(TEXT, rules=RULES)
    assert responses.calls[-1].request.url == BASE + 'styleguide'


@responses.activate
def test_styleguide_accepts_a_tuple_of_rules(client):
    responses.add(responses.POST, BASE + 'styleguide',
                  json=STYLEGUIDE_RESPONSE, status=200)
    client.styleguide(TEXT, rules=('no jargon',))
    assert _last_request_body()['rules'] == ['no jargon']


def test_styleguide_rejects_non_list_rules(client):
    for bad in (None, 'no jargon', {'name': 'no jargon'}, b'rules', 5):
        with pytest.raises(TypeError):
            client.styleguide(TEXT, rules=bad)


@responses.activate
def test_styleguide_http_error_raises(client):
    responses.add(responses.POST, BASE + 'styleguide',
                  json={'msg': 'Unexpected error checking text against the style guide.'},
                  status=502)
    with pytest.raises(Exception):
        client.styleguide(TEXT, rules=RULES)
