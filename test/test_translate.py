import json

import pytest
import responses

from sapling import SaplingClient, SaplingError

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

TEXT = 'Hello world.\nSee you at 5pm.'

TRANSLATE_RESPONSE = {
    'translation': 'Bonjour le monde.\nÀ 17h.',
    'source_lang': 'en',
    'source_lang_name': 'English',
    'target_lang': 'fr',
    'target_lang_name': 'French',
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_translate_returns_json_and_sends_key(client):
    responses.add(responses.POST, BASE + 'translate',
                  json=TRANSLATE_RESPONSE, status=200)
    result = client.translate(TEXT, target_lang='fr')
    assert result == TRANSLATE_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': TEXT, 'target_lang': 'fr'}


@responses.activate
def test_translate_posts_to_translate_endpoint(client):
    responses.add(responses.POST, BASE + 'translate',
                  json=TRANSLATE_RESPONSE, status=200)
    client.translate(TEXT, target_lang='fr')
    assert responses.calls[-1].request.url == BASE + 'translate'


@responses.activate
def test_translate_optional_params_sent_only_when_given(client):
    responses.add(responses.POST, BASE + 'translate',
                  json=TRANSLATE_RESPONSE, status=200)
    client.translate(TEXT, target_lang='fr')
    body = _last_request_body()
    assert 'source_lang' not in body
    assert 'formality' not in body

    client.translate(TEXT, target_lang='fr',
                     source_lang='en', formality='formal')
    body = _last_request_body()
    assert body['source_lang'] == 'en'
    assert body['formality'] == 'formal'


@responses.activate
def test_translate_accepts_names_and_region_variants(client):
    responses.add(responses.POST, BASE + 'translate',
                  json=dict(TRANSLATE_RESPONSE, target_lang='zh-TW',
                            target_lang_name='Traditional Chinese'),
                  status=200)
    result = client.translate(TEXT, target_lang='Traditional Chinese')
    assert result['target_lang'] == 'zh-TW'
    assert _last_request_body()['target_lang'] == 'Traditional Chinese'


@responses.activate
def test_translate_http_error_raises_sapling_error(client):
    responses.add(responses.POST, BASE + 'translate',
                  json={'msg': 'Unknown language: "Klingon".'}, status=400)
    with pytest.raises(SaplingError):
        client.translate(TEXT, target_lang='Klingon')
