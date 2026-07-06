import json

import pytest
import responses

from sapling import SaplingClient, SaplingError

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    '''Return the JSON body of the most recent mocked request.'''
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_edits_returns_json_and_sends_key(client):
    responses.add(
        responses.POST,
        BASE + 'edits',
        json={'edits': [{'replacement': "Let's"}]},
        status=200,
    )
    result = client.edits('Lets go', session_id='s1')
    assert result == {'edits': [{'replacement': "Let's"}]}
    body = _last_request_body()
    assert body['key'] == API_KEY
    assert body['text'] == 'Lets go'
    assert body['session_id'] == 's1'


@responses.activate
def test_edits_uses_default_session_id(client):
    responses.add(responses.POST, BASE + 'edits', json={'edits': []}, status=200)
    client.edits('hi')
    assert _last_request_body()['session_id'] == client.default_session_id


@responses.activate
def test_optional_params_only_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'edits', json={'edits': []}, status=200)
    client.edits('hi')
    body = _last_request_body()
    for absent in ('lang', 'variety', 'medical', 'advanced_edits', 'user_id', 'is_anon_user'):
        assert absent not in body
    # auto_apply defaults to False and is always included
    assert body['auto_apply'] is False


@responses.activate
def test_error_response_raises_saplingerror_with_body(client):
    responses.add(
        responses.POST,
        BASE + 'edits',
        json={'msg': 'Invalid text.'},
        status=400,
    )
    with pytest.raises(SaplingError) as exc_info:
        client.edits('hi')
    err = exc_info.value
    assert err.status_code == 400
    # Regression test: the response body must be interpolated into the message.
    assert 'Invalid text.' in str(err)
    assert 'Invalid text.' in err.body


@responses.activate
def test_accept_edit_error_includes_body(client):
    '''Regression: accept_edit previously never interpolated resp.text.'''
    responses.add(
        responses.POST,
        BASE + 'edits/some-uuid/accept',
        json={'msg': 'Not found'},
        status=404,
    )
    with pytest.raises(SaplingError) as exc_info:
        client.accept_edit('some-uuid', session_id='s1')
    assert 'Not found' in str(exc_info.value)


@responses.activate
def test_accept_edit_success_returns_none(client):
    responses.add(responses.POST, BASE + 'edits/some-uuid/accept', body='', status=200)
    assert client.accept_edit('some-uuid') is None


@responses.activate
def test_reject_edit_success_returns_none(client):
    responses.add(responses.POST, BASE + 'edits/some-uuid/reject', body='', status=200)
    assert client.reject_edit('some-uuid') is None


@responses.activate
def test_accept_complete_sends_string_session_id(client):
    '''Regression: session_id fallback must be a str, not a uuid.UUID.'''
    responses.add(responses.POST, BASE + 'complete/c-uuid/accept', body='', status=200)
    client.accept_complete('c-uuid', 'the query', 'the completion')
    body = _last_request_body()
    assert isinstance(body['session_id'], str)
    assert body['session_id'] == client.default_session_id
    assert body['context'] == {'query': 'the query', 'completion': 'the completion'}


@responses.activate
def test_aidetect_error_includes_body(client):
    '''Regression: aidetect previously never interpolated resp.text.'''
    responses.add(responses.POST, BASE + 'aidetect', json={'msg': 'boom'}, status=500)
    with pytest.raises(SaplingError) as exc_info:
        client.aidetect('some text')
    assert 'boom' in str(exc_info.value)


@responses.activate
def test_rephrase_sends_expected_params(client):
    responses.add(responses.POST, BASE + 'rephrase', json={'results': []}, status=200)
    client.rephrase('hey wuts up', mapping='informal_to_formal', num_results=3)
    body = _last_request_body()
    assert body['text'] == 'hey wuts up'
    assert body['mapping'] == 'informal_to_formal'
    assert body['num_results'] == 3
    assert 'session_id' in body
    # Unset optional params should be omitted.
    assert 'tone_mapping' not in body
    assert 'tense_mapping' not in body


@pytest.mark.parametrize(
    'method,path,payload',
    [
        ('summarize', 'summarize', {'result': 'short'}),
        ('tone', 'tone', {'overall': [], 'results': [], 'sents': []}),
        ('sentiment', 'sentiment', {'overall': [], 'results': [], 'sents': []}),
        ('quality', 'quality', {'score': 3.5}),
        ('langdetect', 'langdetect', {'lang': 'en', 'conf': 0.99}),
        ('profanity', 'profanity', {'toks': ['a'], 'labels': [0]}),
    ],
)
@responses.activate
def test_single_text_endpoints(client, method, path, payload):
    responses.add(responses.POST, BASE + path, json=payload, status=200)
    result = getattr(client, method)('some text')
    assert result == payload
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': 'some text'}


@responses.activate
def test_hostname_and_pathname_override():
    client = SaplingClient(api_key=API_KEY, hostname='http://localhost:5000', pathname='/api/v1/')
    responses.add(responses.POST, 'http://localhost:5000/api/v1/edits', json={'edits': []}, status=200)
    client.edits('hi')
    assert responses.calls[-1].request.url == 'http://localhost:5000/api/v1/edits'
