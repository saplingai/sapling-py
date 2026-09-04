import json

import pytest
import responses

from sapling import SaplingClient, SaplingError

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

LABELS = ['billing', 'technical issue', 'shipping', 'other']

CLASSIFY_RESPONSE = {
    'label': 'billing',
    'labels': ['billing'],
    'scores': [
        {'label': 'billing', 'score': 0.86},
        {'label': 'technical issue', 'score': 0.07},
        {'label': 'shipping', 'score': 0.04},
        {'label': 'other', 'score': 0.03},
    ],
    'rationale': 'The customer reports being charged twice on one invoice.',
    'multi_label': False,
}

MULTI_LABEL_RESPONSE = {
    'label': 'billing',
    'labels': ['billing', 'technical issue'],
    'scores': [
        {'label': 'billing', 'score': 0.92},
        {'label': 'technical issue', 'score': 0.81},
        {'label': 'shipping', 'score': 0.03},
        {'label': 'other', 'score': 0.02},
    ],
    'rationale': 'Mentions a duplicate charge and an app crash.',
    'multi_label': True,
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_classify_returns_json_and_sends_key(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    result = client.classify('I was charged twice for my last invoice.', LABELS)
    assert result == CLASSIFY_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': 'I was charged twice for my last invoice.',
                    'labels': LABELS}


@responses.activate
def test_classify_posts_to_classify_endpoint(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    client.classify('some text', LABELS)
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == BASE + 'classify'
    assert responses.calls[0].request.method == 'POST'


@responses.activate
def test_classify_label_dicts_passed_through(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    labels = [
        'billing',
        {'name': 'technical issue', 'description': 'Bugs, crashes, errors'},
        {'name': 'shipping'},
        'other',
    ]
    client.classify('some text', labels)
    body = _last_request_body()
    assert body['labels'] == labels


@responses.activate
def test_classify_labels_tuple_sent_as_list(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    client.classify('some text', ('billing', 'shipping'))
    body = _last_request_body()
    assert body['labels'] == ['billing', 'shipping']


@responses.activate
def test_classify_optional_params_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    client.classify('some text', LABELS)
    body = _last_request_body()
    assert 'multi_label' not in body
    assert 'threshold' not in body
    assert 'context' not in body


@responses.activate
def test_classify_optional_params_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'classify', json=MULTI_LABEL_RESPONSE, status=200)
    result = client.classify('I was charged twice and the app crashes on launch', LABELS,
                             multi_label=True, threshold=0.7,
                             context='Support tickets for a SaaS billing product')
    assert result == MULTI_LABEL_RESPONSE
    assert result['labels'] == ['billing', 'technical issue']
    body = _last_request_body()
    assert body == {'key': API_KEY,
                    'text': 'I was charged twice and the app crashes on launch',
                    'labels': LABELS,
                    'multi_label': True, 'threshold': 0.7,
                    'context': 'Support tickets for a SaaS billing product'}


@responses.activate
def test_classify_multi_label_false_sent(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    client.classify('some text', LABELS, multi_label=False)
    body = _last_request_body()
    assert body['multi_label'] is False
    assert 'threshold' not in body
    assert 'context' not in body


@responses.activate
def test_classify_threshold_zero_sent(client):
    responses.add(responses.POST, BASE + 'classify', json=MULTI_LABEL_RESPONSE, status=200)
    client.classify('some text', LABELS, multi_label=True, threshold=0)
    body = _last_request_body()
    assert body['threshold'] == 0
    assert body['multi_label'] is True


@responses.activate
def test_classify_context_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'classify', json=CLASSIFY_RESPONSE, status=200)
    client.classify('some text', LABELS, context='Product reviews')
    body = _last_request_body()
    assert body['context'] == 'Product reviews'
    assert 'multi_label' not in body
    assert 'threshold' not in body


@responses.activate
def test_classify_multi_label_empty_labels_returned_verbatim(client):
    # "None of these apply" is a valid multi-label answer.
    payload = dict(MULTI_LABEL_RESPONSE, labels=[], rationale='')
    responses.add(responses.POST, BASE + 'classify', json=payload, status=200)
    result = client.classify('some text', LABELS, multi_label=True, threshold=0.95)
    assert result['labels'] == []
    assert result['rationale'] == ''
    assert result['scores'] == MULTI_LABEL_RESPONSE['scores']


@responses.activate
def test_classify_error_raises_saplingerror_with_body(client):
    responses.add(responses.POST, BASE + 'classify',
                  json={'msg': 'Invalid labels: Needs between 2 and 20 labels.'}, status=400)
    with pytest.raises(SaplingError) as exc_info:
        client.classify('some text', ['only one'])
    err = exc_info.value
    assert err.status_code == 400
    assert 'Invalid labels: Needs between 2 and 20 labels.' in str(err)


@responses.activate
def test_classify_upstream_error_raises_saplingerror(client):
    responses.add(responses.POST, BASE + 'classify',
                  json={'msg': 'Unexpected error classifying text.'}, status=502)
    with pytest.raises(SaplingError) as exc_info:
        client.classify('some text', LABELS)
    err = exc_info.value
    assert err.status_code == 502
    assert 'Unexpected error classifying text.' in str(err)


@responses.activate
def test_classify_unauthorized_raises_saplingerror(client):
    responses.add(responses.POST, BASE + 'classify', json={'msg': 'Invalid API key.'},
                  status=401)
    with pytest.raises(SaplingError) as exc_info:
        client.classify('some text', LABELS)
    assert exc_info.value.status_code == 401


@responses.activate
def test_classify_custom_hostname_and_pathname():
    client = SaplingClient(api_key=API_KEY, hostname='https://sapling.example.com',
                           pathname='/custom/v1/')
    responses.add(responses.POST, 'https://sapling.example.com/custom/v1/classify',
                  json=CLASSIFY_RESPONSE, status=200)
    result = client.classify('some text', LABELS)
    assert result == CLASSIFY_RESPONSE


@pytest.mark.parametrize('bad_labels', [None, 'billing', b'billing', {'name': 'billing'}, 42, True])
def test_classify_rejects_non_list_labels(client, bad_labels):
    with pytest.raises(TypeError):
        client.classify('I was charged twice.', bad_labels)


@responses.activate
def test_classify_batch_list_sent_as_texts(client):
    # A list of texts is the batch form (SAP-395): sent as `texts`, no `text`
    # key, and the {'results': [...]} body comes back untouched.
    batch_response = {'results': [CLASSIFY_RESPONSE, MULTI_LABEL_RESPONSE]}
    responses.add(responses.POST, BASE + 'classify', json=batch_response, status=200)
    result = client.classify(['first ticket', 'second ticket'], LABELS)
    assert result == batch_response
    body = _last_request_body()
    assert body == {'key': API_KEY, 'texts': ['first ticket', 'second ticket'],
                    'labels': LABELS}


@responses.activate
def test_classify_batch_tuple_sent_as_list(client):
    responses.add(responses.POST, BASE + 'classify',
                  json={'results': [CLASSIFY_RESPONSE]}, status=200)
    client.classify(('only ticket',), LABELS)
    body = _last_request_body()
    assert body['texts'] == ['only ticket']
    assert 'text' not in body
