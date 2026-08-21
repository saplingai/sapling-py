import json

import pytest
import responses

from sapling import SaplingClient, SaplingError

API_KEY = 'a' * 32
BASE = 'https://api.sapling.ai/api/v1/'

TEXT = 'Invoice INV-1042 for Acme Corp, total $1,299.00, due March 5, 2026.'

FIELDS = [
    'invoice_number',
    {'name': 'total', 'type': 'number', 'description': 'Amount due', 'required': True},
    {'name': 'due_date', 'type': 'date'},
    'purchase_order',
]

EXTRACT_RESPONSE = {
    'data': {
        'invoice_number': 'INV-1042',
        'total': 1299.0,
        'due_date': '2026-03-05',
        'purchase_order': None,
    },
    'fields': [
        {'name': 'invoice_number', 'type': 'string', 'value': 'INV-1042',
         'evidence': 'Invoice INV-1042', 'found': True},
        {'name': 'total', 'type': 'number', 'value': 1299.0,
         'evidence': 'total $1,299.00', 'found': True},
        {'name': 'due_date', 'type': 'date', 'value': '2026-03-05',
         'evidence': 'due March 5, 2026', 'found': True},
        {'name': 'purchase_order', 'type': 'string', 'value': None,
         'evidence': '', 'found': False},
    ],
    'missing': ['purchase_order'],
}


@pytest.fixture
def client():
    return SaplingClient(api_key=API_KEY)


def _last_request_body():
    return json.loads(responses.calls[-1].request.body)


@responses.activate
def test_extract_returns_json_and_sends_key(client):
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    result = client.extract(TEXT, FIELDS)
    assert result == EXTRACT_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': TEXT, 'fields': FIELDS}


@responses.activate
def test_extract_posts_to_extract_endpoint(client):
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    client.extract('some text', ['invoice_number'])
    assert len(responses.calls) == 1
    assert responses.calls[0].request.url == BASE + 'extract'
    assert responses.calls[0].request.method == 'POST'


@responses.activate
def test_extract_field_dicts_passed_through(client):
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    fields = [
        'invoice_number',
        {'name': 'total', 'type': 'number', 'description': 'Amount due', 'required': True},
        {'name': 'line_items', 'type': 'list'},
        {'name': 'is_urgent', 'type': 'boolean'},
    ]
    client.extract('some text', fields)
    body = _last_request_body()
    assert body['fields'] == fields


@responses.activate
def test_extract_fields_tuple_sent_as_list(client):
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    client.extract('some text', ('invoice_number', 'total'))
    body = _last_request_body()
    assert body['fields'] == ['invoice_number', 'total']


@responses.activate
def test_extract_optional_params_omitted_by_default(client):
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    client.extract('some text', FIELDS)
    body = _last_request_body()
    assert 'context' not in body


@responses.activate
def test_extract_context_sent_when_provided(client):
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    result = client.extract(TEXT, FIELDS, context='A vendor invoice')
    assert result == EXTRACT_RESPONSE
    body = _last_request_body()
    assert body == {'key': API_KEY, 'text': TEXT, 'fields': FIELDS,
                    'context': 'A vendor invoice'}


@responses.activate
def test_extract_empty_context_sent(client):
    # '' is not None, so it is forwarded rather than dropped.
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    client.extract('some text', FIELDS, context='')
    body = _last_request_body()
    assert body['context'] == ''


@responses.activate
def test_extract_nothing_found_returned_verbatim(client):
    # Finding nothing is a normal 200, not an error.
    payload = {
        'data': {'invoice_number': None, 'total': None},
        'fields': [
            {'name': 'invoice_number', 'type': 'string', 'value': None,
             'evidence': '', 'found': False},
            {'name': 'total', 'type': 'number', 'value': None,
             'evidence': '', 'found': False},
        ],
        'missing': ['invoice_number', 'total'],
    }
    responses.add(responses.POST, BASE + 'extract', json=payload, status=200)
    result = client.extract('Nothing invoice-like here.', ['invoice_number', 'total'])
    assert result == payload
    assert result['missing'] == ['invoice_number', 'total']
    assert all(value is None for value in result['data'].values())


@responses.activate
def test_extract_error_raises_saplingerror_with_body(client):
    responses.add(responses.POST, BASE + 'extract',
                  json={'msg': 'Invalid fields: Needs between 1 and 20 fields.'},
                  status=400)
    with pytest.raises(SaplingError) as exc_info:
        client.extract('some text', [])
    err = exc_info.value
    assert err.status_code == 400
    assert 'Invalid fields: Needs between 1 and 20 fields.' in str(err)


@responses.activate
def test_extract_upstream_error_raises_saplingerror(client):
    responses.add(responses.POST, BASE + 'extract',
                  json={'msg': 'Unexpected error extracting from text.'}, status=502)
    with pytest.raises(SaplingError) as exc_info:
        client.extract('some text', FIELDS)
    err = exc_info.value
    assert err.status_code == 502
    assert 'Unexpected error extracting from text.' in str(err)


@responses.activate
def test_extract_unauthorized_raises_saplingerror(client):
    responses.add(responses.POST, BASE + 'extract', json={'msg': 'Invalid API key.'},
                  status=401)
    with pytest.raises(SaplingError) as exc_info:
        client.extract('some text', FIELDS)
    assert exc_info.value.status_code == 401


@responses.activate
def test_extract_rate_limited_raises_saplingerror(client):
    responses.add(responses.POST, BASE + 'extract',
                  json={'msg': 'Too many requests.'}, status=429)
    with pytest.raises(SaplingError) as exc_info:
        client.extract('some text', FIELDS)
    assert exc_info.value.status_code == 429


@responses.activate
def test_extract_custom_hostname_and_pathname():
    client = SaplingClient(api_key=API_KEY, hostname='https://sapling.example.com',
                           pathname='/custom/v1/')
    responses.add(responses.POST, 'https://sapling.example.com/custom/v1/extract',
                  json=EXTRACT_RESPONSE, status=200)
    result = client.extract(TEXT, FIELDS)
    assert result == EXTRACT_RESPONSE


# None / an int / a bool are not iterable at all; a str, bytes or dict is
# iterable but into the wrong thing (characters, bytes, keys).
BAD_FIELDS = [None, 42, 3.5, True, 'invoice_number', b'invoice_number',
              {'name': 'invoice_number'}]


@pytest.mark.parametrize('bad_fields', BAD_FIELDS)
def test_extract_rejects_non_list_fields(client, bad_fields):
    with pytest.raises(TypeError):
        client.extract(TEXT, bad_fields)


@pytest.mark.parametrize('bad_fields', BAD_FIELDS)
def test_extract_non_list_fields_message_is_helpful(client, bad_fields):
    # Not the opaque "'int' object is not iterable" from list().
    with pytest.raises(TypeError, match='fields must be a list'):
        client.extract(TEXT, bad_fields)


@responses.activate
def test_extract_accepts_any_iterable_of_fields(client):
    # list(fields) already handled tuples; a generator is iterable too and must
    # not be rejected by the stricter guard.
    responses.add(responses.POST, BASE + 'extract', json=EXTRACT_RESPONSE, status=200)
    client.extract(TEXT, (name for name in ['invoice_number', 'total']))
    assert _last_request_body()['fields'] == ['invoice_number', 'total']
