import json

import pytest
import responses

from sapling import SaplingClient, SaplingError

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

SEO_STATS_RESPONSE = {
    'stats': {
        'chars': 372, 'words': 63, 'sentences': 6, 'paragraphs': 3,
        'reading_time_min': 1, 'flesch_reading_ease': 66.4, 'flesch_kincaid_grade': 7.2,
    },
    'keywords': [],
    'top_terms': [{'term': 'grammar', 'count': 6}, {'term': 'grammar checker', 'count': 5}],
}

SEO_RESPONSE = dict(
    SEO_STATS_RESPONSE,
    keywords=[{'keyword': 'grammar checker', 'count': 5, 'density': 7.94,
               'in_first_100_words': True}],
    suggestions={
        'titles': ['Grammar Checker Guide: What Modern Tools Catch'],
        'meta_descriptions': ['Learn what a modern grammar checker catches beyond typos.'],
        'slug': 'grammar-checker-guide',
        'keywords': ['grammar checker', 'grammar checker for teams'],
    },
)


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_seo_returns_json_and_sends_key(client):
    responses.add(responses.POST, BASE + 'seo', json=SEO_RESPONSE, status=200)
    result = client.seo('Grammar checkers catch more than typos.')
    assert result == SEO_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': 'Grammar checkers catch more than typos.'}


@responses.activate
def test_seo_optional_params_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'seo', json=SEO_RESPONSE, status=200)
    result = client.seo('some text', keywords=('grammar checker', 'passive voice'),
                        suggestions=True, lang='en')
    assert result['suggestions']['slug'] == 'grammar-checker-guide'
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': 'some text',
                    'keywords': ['grammar checker', 'passive voice'],
                    'suggestions': True, 'lang': 'en'}


@responses.activate
def test_seo_suggestions_false_sent(client):
    responses.add(responses.POST, BASE + 'seo', json=SEO_STATS_RESPONSE, status=200)
    result = client.seo('some text', suggestions=False)
    assert result == SEO_STATS_RESPONSE
    assert 'suggestions' not in result
    body = _last_request_body()
    assert body['suggestions'] is False
    assert 'keywords' not in body


@responses.activate
def test_seo_lang_sent_when_provided(client):
    # Unsupported readability language: readability fields come back as null.
    payload = dict(SEO_STATS_RESPONSE, stats=dict(
        SEO_STATS_RESPONSE['stats'], flesch_reading_ease=None, flesch_kincaid_grade=None))
    responses.add(responses.POST, BASE + 'seo', json=payload, status=200)
    result = client.seo('some text', lang='pt-BR')
    assert result['stats']['flesch_reading_ease'] is None
    body = _last_request_body()
    assert body['lang'] == 'pt-BR'
    assert 'keywords' not in body
    assert 'suggestions' not in body


@responses.activate
def test_seo_optional_params_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'seo', json=SEO_STATS_RESPONSE, status=200)
    client.seo('some text')
    body = _last_request_body()
    assert 'keywords' not in body
    assert 'suggestions' not in body
    assert 'lang' not in body


@responses.activate
def test_seo_error_raises_saplingerror_with_body(client):
    responses.add(responses.POST, BASE + 'seo',
                  json={'msg': 'Unexpected error generating SEO suggestions.'}, status=502)
    with pytest.raises(SaplingError) as exc_info:
        client.seo('some text')
    err = exc_info.value
    assert err.status_code == 502
    assert 'Unexpected error generating SEO suggestions.' in str(err)


@responses.activate
@pytest.mark.parametrize('bad_keywords', ['grammar', b'grammar', {'grammar': True}, 42, True])
def test_seo_rejects_invalid_keywords(client, bad_keywords):
    # A bare string would be split into characters and a dict reduced to its keys;
    # non-iterables would raise an opaque TypeError from list().
    with pytest.raises(TypeError):
        client.seo('some text', keywords=bad_keywords)
    assert len(responses.calls) == 0
