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
        advanced_edits=None,
        user_id=None,
        is_anon_user=None,
    ):
        '''
        Fetches edits (including for grammar and spelling) for provided text.

        :param text: Text to process for edits.
        :type text: str
        :param session_id: Unique name or UUID of document or portion of text that is being checked
        :type session_id: str
        :param lang: 2 letter ISO 639-1 language code
        :type lang: str
        :param variety: Specifies regional English variety preference. Defaults to the configuration in the user Sapling dashboard.
        :type variety: str
        :param medical: If true, the backend will apply Sapling's medical dictionary.
        :type medical: bool
        :param auto_apply: Whether to return a field with edits applied to the text
        :type auto_apply: bool
        :param advanced_edits: Additional edit configurations
        :type advanced_edits: dict
        :param user_id: Track IDs representing your end users
        :type user_id: str
        :param is_anon_user: If user_id represents a logged-in or anonymous user
        :type is_anon_user: bool
        :rtype: dict
        :return:
            - edits: List of Edits:
                - sentence: Unedited sentence
                - sentence_start: Offset of sentence from start of text
                - start: Offset of edit start relative to sentence
                - end: Offset of edit end relative to sentence
                - replacement: Suggested replacement
                - error_type: Error type
                - general_error_type: General Error type
            - applied_text: Transformed text if auto_apply is set.

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

        Supported advanced_edit options:
            - advanced_edits
            - adverbs
            - simplifications
            - hard_to_read
            - qualifiers
            - voice
            - dei
            - gender
            - gender_pronoun
            - gender_noun
            - gender_id
            - sensitivity
            - disability
            - age
            - race
            - social_class
            - violence
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
        if advanced_edits is not None:
            data['advanced_edits'] = advanced_edits

        if user_id is not None:
            data['user_id'] = user_id
        if is_anon_user is not None:
            data['is_anon_user'] = is_anon_user

        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return resp.json()
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')

    def accept_edit(
        self,
        edit_uuid,
        session_id=None,
        user_id=None,
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
        :param user_id: Track IDs representing your end users
        :type user_id: str
        '''
        url = f'{self.url_endpoint}edits/{edit_uuid}/accept'
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'session_id': session_id,
        }

        if user_id is not None:
            data['user_id'] = user_id

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
        user_id=None,
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
        :param user_id: Track IDs representing your end users
        :type user_id: str
        '''
        url = f'{self.url_endpoint}edits/{edit_uuid}/reject'
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'session_id': session_id,
        }

        if user_id is not None:
            data['user_id'] = user_id

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
        user_id=None,
        is_anon_user=None
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
        :param advanced_edits: additional edit checking options
        :type advanced_edits: dict
        :param variety: Specifies regional English variety preference. Defaults to the configuration in the user Sapling dashboard.
        :type variety: str
        :param user_id: Track IDs representing your end users
        :type user_id: str
        :param is_anon_user: If user_id represents a logged-in or anonymous user
        :type is_anon_user: bool

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

        if user_id is not None:
            data['user_id'] = user_id
        if is_anon_user is not None:
            data['is_anon_user'] = is_anon_user

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

    def aidetect(
        self,
        text,
        sent_scores=None,
    ):
        '''
        Score a piece of text on how likely it was generated by AI.

        :param text: Text to
        :type text: str
        :param sent_scores: If true, each sentence will also be scored individually.
        :type sent_scores: bool

        :rtype: dict
        :return:
            - score: float between 0 and 1, probability that text is AI generated
            - sentence_scores: If sent_scores is set, will return a list of scores per sentence.
            - text: text that was processed

        '''
        url = f'{self.url_endpoint}aidetect'
        data = {
            'key': self.api_key,
            'text': text,
        }
        if sent_scores is not None:
            data['sent_scores'] = sent_scores
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return resp.json()
        raise Exception(f'HTTP {resp.status_code}: resp.text')

    def chunk_text(
        self,
        text,
        max_length,
        step_size=None,
    ):
        '''
        Break an input text into blocks of length of most max_length. When splitting the text, the API follows the following preference stack:

        page break > paragraph breaks > line breaks > tabs > punctuation > all other whitespace

        :param text: Text to be chunked
        :type text: str
        :param max_length: Maximum length of text segments.
        :type max_length: integer
        :param step_size: Size of window to look for split points.
        :type step_size: integer
        :rtype: dict
        :return:
            - chunks: List of resulting chunks
        '''
        url = f'{self.url_endpoint}ingest/chunk_text'
        data = {
            'key': self.api_key,
            'text': text,
            'max_length': max_length
        }
        if step_size is not None:
            data['step_size'] = step_size
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return resp.json()
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')

    def chunk_html(
        self,
        html,
        max_length,
        step_size=None,
    ):
        '''
        Break an input text into blocks of length of most max_length. When splitting the text, the API follows the following preference stack:

        page break > paragraph breaks > line breaks > tabs > punctuation > all other whitespace

        Note: This endpoint not only breaks up the HTML but also discards all HTML tags, resulting in plain text.

        :param html: HTML to be chunked
        :type html: str
        :param max_length: Maximum length of text segments.
        :type max_length: integer
        :param step_size: Size of window to look for split points.
        :type step_size: integer
        :rtype: dict
        :return:
            - chunks: List of resulting chunks representing the segmented text contained within the HTML
        '''
        url = f'{self.url_endpoint}ingest/chunk_html'
        data = {
            'key': self.api_key,
            'html': html,
            'max_length': max_length
        }
        if step_size is not None:
            data['step_size'] = step_size
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return resp.json()
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')

    def postprocess(
        self,
        text,
        session_id,
        operations,
    ):
        '''
        Performs a variety of operations that are useful for working with the outputs of an NLP (whether human or AI) system. These include:
            - Fixing or restoring punctuation
            - Fixing capitalization
            - Fixing or restoring whitespace

        Example use cases include repairing transcriptions or captions.

        :param text: Text to postprocess
        :type text: str
        :param session_id: Unique name or UUID of document or portion of text that is being chunked
        :type text: str
        :param operations: Operations to apply. The currently accepted operations are:
            - capitalize
            - punctuate
            - fixspaces

        :type operations: list[str]
        :rtype: list[dict]
        :return:
            Same as the edits endpoint:
            - sentence: Unedited sentence
            - sentence_start: Offset of sentence from start of text
            - start: Offset of edit start relative to sentence
            - end: Offset of edit end relative to sentence
            - replacement: Suggested replacement
            - error_type: Error type
            - general_error_type: General Error type
        '''
        url = f'{self.url_endpoint}postprocess'
        data = {
            'key': self.api_key,
            'text': text,
            'session_id': session_id,
            'operations': operations,
        }
        resp = requests.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if 200 <= resp.status_code < 300:
            return resp.json()
        raise Exception(f'HTTP {resp.status_code}: {resp.text}')
