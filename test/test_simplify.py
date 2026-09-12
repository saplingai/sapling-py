import json

import pytest
import responses

from sapling import SaplingClient

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

TEXT = ('The party of the first part shall remit payment within thirty (30) '
        'days of receipt of the invoice.')

SIMPLIFY_RESPONSE = {
    'simplified': 'You must pay within 30 days of getting the invoice.',
    'reading_level': 'plain',
    'lang': 'en',
    'readability': {
        'before': {'grade': 12.3, 'ease': 42.1},
        'after': {'grade': 5.8, 'ease': 78.4},
    },
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_simplify_returns_json_and_sends_key_and_text(client):
    responses.add(responses.POST, BASE + 'simplify',
                  json=SIMPLIFY_RESPONSE, status=200)
    result = client.simplify(TEXT)
    assert result == SIMPLIFY_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': TEXT}


@responses.activate
def test_simplify_posts_to_simplify_endpoint(client):
    responses.add(responses.POST, BASE + 'simplify',
                  json=SIMPLIFY_RESPONSE, status=200)
    client.simplify(TEXT)
    assert responses.calls[-1].request.url == BASE + 'simplify'


@responses.activate
def test_simplify_omits_optional_arguments_when_not_given(client):
    responses.add(responses.POST, BASE + 'simplify',
                  json=SIMPLIFY_RESPONSE, status=200)
    client.simplify(TEXT)
    body = _last_request_body()
    assert 'reading_level' not in body
    assert 'preserve_terms' not in body
    assert 'lang' not in body


@responses.activate
def test_simplify_sends_optional_arguments(client):
    responses.add(responses.POST, BASE + 'simplify',
                  json=SIMPLIFY_RESPONSE, status=200)
    client.simplify(TEXT, reading_level='middle_school',
                    preserve_terms=['invoice', 'Sapling'], lang='en')
    body = _last_request_body()
    assert body['reading_level'] == 'middle_school'
    assert body['preserve_terms'] == ['invoice', 'Sapling']
    assert body['lang'] == 'en'


@responses.activate
def test_simplify_accepts_a_tuple_of_preserve_terms(client):
    responses.add(responses.POST, BASE + 'simplify',
                  json=SIMPLIFY_RESPONSE, status=200)
    client.simplify(TEXT, preserve_terms=('invoice',))
    assert _last_request_body()['preserve_terms'] == ['invoice']


def test_simplify_rejects_non_list_preserve_terms(client):
    for bad in ('invoice', b'invoice', {'term': 'invoice'}, 5):
        with pytest.raises(TypeError):
            client.simplify(TEXT, preserve_terms=bad)


@responses.activate
def test_simplify_http_error_raises(client):
    responses.add(responses.POST, BASE + 'simplify',
                  json={'msg': 'Unexpected error simplifying text.'},
                  status=502)
    with pytest.raises(Exception):
        client.simplify(TEXT)
