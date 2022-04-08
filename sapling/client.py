import requests
import uuid

class SaplingClient:
    '''
    Sapling client class. Provides a mapping of Python functions to Sapling HTTP REST APIs.

    :param api_key: 32-character API key
    :type api_key: str
    :param timeout: Timeout for API call in seconds. Defaults to 120 seconds.
    :type timeout: int
    :param hostname: Hostname override for SDK and self-hosted deployments.
    :type hostname: str
    :param pathname: Pathname override for SDK and self-hosted deployments as well as version requirements.
    :type pathname: str
    '''

    def __init__(
        self,
        api_key,
        timeout=120,
        hostname=None,
        pathname=None,
    ):
        self.api_key = api_key
        self.timeout = timeout
        self.hostname = hostname or 'https://api.sapling.ai'
        self.pathname = pathname or '/api/v1/'
        self.url_endpoint = self.hostname + self.pathname

    def edits(
        self,
        text,
        session_id=None,
        variety=None,
        auto_apply=False,
    ):
        '''
        Fetches edits (including for grammar and spelling) for provided text.

        :param text: Text to process for edits.
        :type text: str
        :param session_id: Unique name or UUID of document or portion of text that is being checked
        :type session_id: str
        :param variety: Specifies regional English variety preference. Defaults to the configuration in the user Sapling dashboard.
        :type variety: str
        :param auto_apply: Whether to return a field with edits applied to the text
        :type auto_apply: bool
        :rtype: list[dict]

        Supported varieties:
            - `us-variety`: American English
            - `gb-variety`: British English
            - `au-variety`: Australian English
            - `ca-variety`: Canadian English
            - `null-variety`: Don't suggest changes based on English variety

        '''

        url = self.url_endpoint + 'edits'
        session_id = session_id or str(uuid.uuid4())
        data = {
            'key': self.api_key,
            'text': text,
            'session_id': session_id,
        }
        if variety is not None:
            data['variety'] = variety
        if auto_apply is not None:
            data['auto_apply'] = auto_apply

        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            resp_json = resp.json()
            return resp_json.get('edits')
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')

    def accept(
        self,
        edit_uuid,
        session_id=None,
    ):
        '''
        Use this API endpoint to have Sapling adapt its system over time.

        Each suggested edit has an edit UUID. You can pass this information back to Sapling to
        indicate the edit suggestion was helpful.
        For each unique edit in each document, use the accept or reject API endpoint only once in total.

        :param edit_uuid: Opaque UUID of the edit returned from the edits endpoint
        :type edit_uuid: str, uuid
        :param session_id: Unique name or UUID of text that is being processed
        :type session_id: str
        '''
        url = f'{self.url_endpoint}edits/{edit_uuid}/accept'
        session_id = session_id or uuid.uuid4()
        data = {
            'key': self.api_key,
            'session_id': session_id,
        }
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return
        raise Exception(f'HTTP {resp.status_code}: resp.text')

    def reject(
        self,
        edit_uuid,
        session_id=None,
    ):
        '''
        Use this API endpoint to have Sapling not recommend the same edit anymore.

        Each suggested edit has an edit UUID. You can pass this information back to Sapling to
        indicate the edit suggestion was not helpful.
        For each unique edit in each document, use the accept or reject API endpoint only once in total.

        :param edit_uuid: Opaque UUID of the edit returned from the edits endpoint
        :type edit_uuid: str, uuid
        :param session_id: Unique name or UUID of text that is being processed
        :type session_id: str
        '''
        url = f'{self.url_endpoint}edits/{edit_uuid}/reject'
        session_id = session_id or uuid.uuid4()
        data = {
            'key': self.api_key,
            'session_id': session_id,
        }
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return
        raise Exception(f'HTTP {resp.status_code}: resp.text')
