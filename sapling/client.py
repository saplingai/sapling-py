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
        self.default_session_id = str(uuid.uuid4())

    def edits(
        self,
        text,
        session_id=None,
        lang=None,
        variety=None,
        medical=None,
        auto_apply=False,
    ):
        '''
        Fetches edits (including for grammar and spelling) for provided text.

        :param text: Text to process for edits.
        :type text: str
        :param session_id: Unique name or UUID of document or portion of text that is being checked
        :type session_id: str
        :param session_id: 2 letter ISO 639-1 language code
        :type session_id: str
        :param variety: Specifies regional English variety preference. Defaults to the configuration in the user Sapling dashboard.
        :type variety: str
        :param medical: If true, the backend will apply Sapling's medical dictionary.
        :type medical: bool
        :param auto_apply: Whether to return a field with edits applied to the text
        :type auto_apply: bool
        :rtype: list[dict]

        Supported languages:
            - `de`:  German (Deutsch)
            - `el`:  Greek (Ελληνικά)
            - `en`:  English (US/UK/CA/AU)
            - `es`:  Spanish (Español)
            - `fr`:  French  (Français) (`fr-fr` and `fr-ca` coming soon)
            - `it`:  Italian (Italiano)
            - `jp`:  Japanese (日本語)
            - `ko`:  Korean (한국어)
            - `nl`:  Dutch (Nederlands)
            - `pl`:  Polish (Polski)
            - `pt`:  Portuguese (Português) (`pt-pt` and `pt-br` coming soon)
            - `sv`:  Swedish (Svenska)
            - `tl`:  Tagalog
            - `zh`:  Chinese (中文)

        Supported varieties:
            - `us-variety`: American English
            - `gb-variety`: British English
            - `au-variety`: Australian English
            - `ca-variety`: Canadian English
            - `null-variety`: Don't suggest changes based on English variety

        '''

        url = self.url_endpoint + 'edits'
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'text': text,
            'session_id': session_id,
        }
        if lang is not None:
            data['lang'] = lang
        if variety is not None:
            data['variety'] = variety
        if medical is not None:
            data['medical'] = medical
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

    def accept_edit(
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
        session_id = session_id or self.default_session_id
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

    def reject_edit(
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
        session_id = session_id or self.default_session_id
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

    def spellcheck(
        self,
        text,
        session_id=None,
        min_length=None,
        multiple_edits=None,
        lang=None,
        auto_apply=False,
        variety=None,
        user_data=None,
    ):
        '''
        Fetches spelling (no grammar or phrase level) edits for provided text.

        :param text: Text to process for edits.
        :type text: str
        :param session_id: Unique name or UUID of document or portion of text that is being checked
        :type session_id: str
        :param min_length: Default is 3. Minimum character length of words to suggest corrections for. Setting this too low will result in much higher false positives.
        :type min_length: int
        :param multiple_edits: Default is false. If true, will return `candidates` field containing list of other potential corrections for each error.
        :type multiple_edits: bool
        :param lang: Default is English. Specify a language to spellcheck the text against.
        :type lang: str
        :param auto_apply: Whether to return a field with edits applied to the text. Cannot be set with multiple_edits option.
        :type auto_apply: bool
        :param variety: Specifies regional English variety preference. Defaults to the configuration in the user Sapling dashboard.
        :type variety: str

        :rtype: list[dict]

        Supported languages:
            - `en`: English
            - `ar`: عربي
            - `bg`: български
            - `ca`: català
            - `cs`: čeština
            - `da`: dansk
            - `de`: Deutsch
            - `el`: Ελληνικά
            - `es`: español
            - `et`: eesti keel
            - `fa`: فارسی
            - `fi`: suomi
            - `fr`: français (`fr-fr` and `fr-ca` coming soon)
            - `he`: עִבְרִית
            - `hi`: हिन्दी",
            - `hr`: hrvatski,
            - `hu`: magyar nyelv
            - `id`: bahasa Indonesia
            - `is`: íslenska
            - `it`: italiano
            - `jp/ja`: 日本語
            - `ko`: 한국어
            - `lt`: lietuvių kalba
            - `lv`: latviešu valoda
            - `nl`: Nederlands
            - `no`: norsk
            - `pl`: polski
            - `pt`: português
            - `ro`: limba română
            - `ru`: русский
            - `sk`: slovenčina
            - `sq`: shqip
            - `sr`: srpski
            - `sv`: svenska
            - `th`: ภาษาไทย
            - `tl`: Tagalog / ᜆᜄᜎᜓᜄ᜔
            - `tr`: Türkçe
            - `uk`: Українська мова
            - `vi`: Tiếng Việt
            - `zh`: 中文


        Supported varieties:
            - `us-variety`: American English
            - `gb-variety`: British English
            - `au-variety`: Australian English
            - `ca-variety`: Canadian English
            - `null-variety`: Don't suggest changes based on English variety

        '''
        url = self.url_endpoint + 'spellcheck'
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'text': text,
            'session_id': session_id,
        }

        if min_length is not None:
            data['min_length'] = min_length
        if multiple_edits is not None:
            data['multiple_edits'] = multiple_edits
        if lang is not None:
            data['lang'] = lang
        if auto_apply is not None:
            data['auto_apply'] = auto_apply
        if variety is not None:
            data['variety'] = variety
        if user_data is not None:
            data['user_data'] = user_data

        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            resp_json = resp.json()
            return resp_json.get('edits')
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')


    def complete(
        self,
        query,
        session_id=None,
    ):
        '''
        Provides predictions of the next few characters or words

        :param query: Text to get completions against.
        :type query: str
        :param session_id: Unique name or UUID of document or portion of text that is being checked
        :type session_id: str
        '''
        url = self.url_endpoint + 'complete'
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'query': query,
            'session_id': session_id,
        }

        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            resp_json = resp.json()
            return resp_json
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')

    def accept_complete(
        self,
        complete_uuid,
        query,
        completion,
        session_id=None,
    ):
        '''
        Use this API endpoint to have Sapling improve completions over time.

        Each suggested autocomplete has a UUID. You can pass this information back to Sapling to
        indicate the suggestion was helpful.

        :param complete_uuid: Opaque UUID of the edit returned from the complete endpoint.
        :type complete_uuid: str, uuid
        :param query: The query text passed to the complete endpoint.
        :type query: str
        :param completion: The suggested completion text returned from the complete endpoint.
        :type completion: str
        '''
        url = f'{self.url_endpoint}complete/{complete_uuid}/accept'
        session_id = session_id or uuid.uuid4()
        data = {
            'key': self.api_key,
            'session_id': session_id,
            'context': {
                'query': query,
                'completion': completion,
            }
        }
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return
        raise Exception(f'HTTP {resp.status_code}: resp.text')
