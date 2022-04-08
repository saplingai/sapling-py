import requests
import uuid

class SaplingClient:
    '''
    Sapling client. Provides a straightforward mapping from Python to Sapling HTTP REST APIs.

    :param api_key: 32-character API key
    :type api_key: str
    :param timeout: Timeout for API call in seconds. Defaults for 120 seconds.
    :type timeout: int
    :param hostname: Hostname override for on-premise deployments.
    :type hostname: str
    :param pathname: Pathname override for on-premise deployments or specific version requirements.
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
        Fetches grammar edits for a piece of text.

        :param text: Text to process for edits.
        :type text: str
        :param session_id: Unique name or UUID of article or portion of text that is being checked
        :type session_id: str
        :param variety: Specifies regional English spelling options. Defaults to the configuration in the Sapling Dashboard.
        :type variety: str
        :param auto_apply:
        :type auto_apply: bool
        :rtype: list[dict]
        Supported regions
            - `us-variety`: American English
            - `gb-variety`: British English
            - `au-variety`: Australian English
            - `ca-variety`: Canadian English
            - `null-variety`: Don’t suggest any changes based on English variety

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
        This API endpoint is a signal that Sapling uses to improve it’s edits over time.
        Each suggested edit has an edit_id edit_UUID. You can pass this information back to Sapling to
        indicate the edit suggestion was good. For each unique edit in each document, try to hit
        the accept or reject API endpoints only one time in total.

        :param edit_uuid: Opaque UUID of the edit returned from the edits endpoint
        :type edit_uuid: str, uuid
        :param session_id: Unique name or UUID of article or portion of text that is being checked
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
        This API endpoint is a signal that Sapling uses to improve it’s edits over time.
        Each suggested edit has an edit_id UUID. You can pass this information back to Sapling to
        indicate the edit suggestion was good. For each unique edit in each document, try to hit
        the accept or reject API endpoints only one time in total.

        :param edit_uuid: Opaque UUID of the edit returned from the edits endpoint
        :type edit_uuid: str, uuid
        :param session_id: Unique name or UUID of article or portion of text that is being checked
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
