import requests
import uuid
from collections.abc import Iterable


class SaplingError(Exception):
    '''
    Raised when the Sapling API returns a non-2xx response.

    :ivar status_code: HTTP status code returned by the API.
    :ivar body: Raw response body returned by the API (may be empty).
    '''

    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self.body = body
        super().__init__(f'HTTP {status_code}: {body}')


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
        self.session = requests.Session()

    def _request(self, url, data):
        '''
        Issues a POST request to the Sapling API and returns the parsed JSON body.

        :param url: Fully-qualified endpoint URL.
        :type url: str
        :param data: JSON-serializable request body.
        :type data: dict
        :rtype: dict, list, or None
        :raises SaplingError: If the API responds with a non-2xx status code.
        '''
        resp = self.session.post(
            url,
            json=data,
            timeout=self.timeout,
        )
        if not 200 <= resp.status_code < 300:
            raise SaplingError(resp.status_code, resp.text)
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return None

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

        return self._request(url, data)

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

        self._request(url, data)

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

        self._request(url, data)

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
        :param user_data: Optional custom data (e.g. a personal dictionary) to inform spellchecking.
        :type user_data: dict
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

        return self._request(url, data)


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

        return self._request(url, data)

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
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'session_id': session_id,
            'context': {
                'query': query,
                'completion': completion,
            }
        }
        self._request(url, data)

    def aidetect(
        self,
        text,
        sent_scores=None,
    ):
        '''
        Score a piece of text on how likely it was generated by AI.

        :param text: Text to score for AI-generated content.
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
        return self._request(url, data)

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
        return self._request(url, data)

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
        return self._request(url, data)

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
        return self._request(url, data)

    def rephrase(
        self,
        text,
        mapping=None,
        tone_mapping=None,
        tense_mapping=None,
        num_results=None,
        session_id=None,
    ):
        '''
        Rephrases the input text, optionally applying a style transformation.

        Given an input sentence, returns output sentences that preserve meaning
        but use alternative phrasings or styles.

        :param text: Text to rephrase. Current maximum length is 400 characters.
        :type text: str
        :param mapping: The transformation to apply. Defaults to `paraphrase`.
            Options include: `paraphrase`, `informal_to_formal`, `passive_to_active`,
            `active_to_passive`, `sentence_split`, `expand`, and `switch_tone`.
        :type mapping: str
        :param tone_mapping: Target tone when `mapping` is `switch_tone`. Options
            include: `straightforward`, `confident`, `friendly`, and `empathetic`.
        :type tone_mapping: str
        :param tense_mapping: Target tense transformation, when applicable.
        :type tense_mapping: str
        :param num_results: Number of results to return (currently only for
            `paraphrase`). Minimum 1, maximum 8. Defaults to 5.
        :type num_results: int
        :param session_id: Unique name or UUID of document or portion of text that is being processed
        :type session_id: str
        :rtype: dict
        :return:
            - results: List of rephrases, each with `original`, `replacement`,
              `rephrase_type`, `model_version`, and `hash`.
        '''
        url = self.url_endpoint + 'rephrase'
        session_id = session_id or self.default_session_id
        data = {
            'key': self.api_key,
            'text': text,
            'session_id': session_id,
        }
        if mapping is not None:
            data['mapping'] = mapping
        if tone_mapping is not None:
            data['tone_mapping'] = tone_mapping
        if tense_mapping is not None:
            data['tense_mapping'] = tense_mapping
        if num_results is not None:
            data['num_results'] = num_results
        return self._request(url, data)

    def summarize(
        self,
        text,
    ):
        '''
        Summarizes a longer document into a shorter, more digestible one.

        :param text: Input document to summarize.
        :type text: str
        :rtype: dict
        :return:
            - result: The summarized text.
        '''
        url = self.url_endpoint + 'summarize'
        data = {
            'key': self.api_key,
            'text': text,
        }
        return self._request(url, data)

    def extract(
        self,
        text,
        fields,
        context=None,
    ):
        '''
        Extracts structured data from unstructured text: you name the fields you
        want, the API returns their values pulled from the document. Every value is
        grounded in a verbatim span of the input, so this is extraction rather than
        summarization or inference; a field the text does not state is reported
        missing rather than guessed.

        Example::

            client.extract(
                'Invoice INV-1042 for Acme Corp, total $1,299.00, due March 5, 2026.',
                fields=[
                    'invoice_number',
                    {'name': 'total', 'type': 'number', 'description': 'Amount due',
                     'required': True},
                    {'name': 'due_date', 'type': 'date'},
                    'purchase_order',
                ],
                context='A vendor invoice',
            )
            # {'data': {'invoice_number': 'INV-1042', 'total': 1299.0,
            #           'due_date': '2026-03-05', 'purchase_order': None},
            #  'fields': [{'name': 'invoice_number', 'type': 'string',
            #              'value': 'INV-1042', 'evidence': 'Invoice INV-1042',
            #              'found': True},
            #             {'name': 'total', 'type': 'number', 'value': 1299.0,
            #              'evidence': 'total $1,299.00', 'found': True},
            #             {'name': 'due_date', 'type': 'date', 'value': '2026-03-05',
            #              'evidence': 'due March 5, 2026', 'found': True},
            #             {'name': 'purchase_order', 'type': 'string', 'value': None,
            #              'evidence': '', 'found': False}],
            #  'missing': ['purchase_order']}

        :param text: Document to extract from, plain text or HTML (tags are
            stripped), up to 10,000 characters.
        :type text: str
        :param fields: 1-20 fields to extract. Each entry is either a field name
            (str) or a dict ``{'name': str, 'type': str, 'description': str,
            'required': bool}`` where everything but ``name`` is optional. Names are
            up to 50 characters and must be unique (case-insensitive). ``type`` is
            one of ``'string'`` (the default), ``'number'``, ``'integer'``,
            ``'boolean'``, ``'date'`` or ``'list'``. ``description`` is up to 200
            characters and sharpens ambiguous fields. ``required`` is a hint to the
            model; a required field the text does not state is still reported
            missing, never guessed.
        :type fields: list[str | dict]
        :raises TypeError: If ``fields`` is None, a single string or a dict rather
            than a list/tuple of fields.
        :param context: Up to 500 characters describing what the document is or how
            to read ambiguous fields (e.g. ``'A vendor invoice'``).
        :type context: str
        :rtype: dict
        :return:
            - data: ``{field name: value}`` map. Every requested field is present,
              with ``None`` where the text did not state it. ``date`` values are
              ``YYYY-MM-DD`` strings and ``list`` values are lists of strings.
            - fields: One dict per requested field, in the order requested, with
              ``name``, ``type``, ``value``, the verbatim ``evidence`` span the value
              came from (``''`` when not found) and ``found``.
            - missing: Names of the fields the text did not yield, in request order.
              Finding nothing is a normal, successful response.
        '''
        # A bare string would silently be split into one-character field names,
        # a dict would be reduced to its keys, and a non-iterable (None, an int)
        # would raise an opaque "'int' object is not iterable" from list().
        # Fail loudly with a message that names the right shape instead.
        if (not isinstance(fields, Iterable)
                or isinstance(fields, (str, bytes, dict))):
            raise TypeError('fields must be a list of field names or '
                            '{name, type, description, required} dicts')
        url = self.url_endpoint + 'extract'
        data = {
            'key': self.api_key,
            'text': text,
            'fields': list(fields),
        }
        if context is not None:
            data['context'] = context
        return self._request(url, data)

    def tone(
        self,
        text,
    ):
        '''
        Detects the tone of the provided text across 28 fine-grained categories.

        The overall tone is returned along with the tone for each sentence.

        :param text: Text to analyze the tone for.
        :type text: str
        :rtype: dict
        :return:
            - sents: The sentences the text contains.
            - overall: List of ``(probability, tone, emoji)`` tuples for the whole text.
            - results: For each sentence, a list of ``(probability, tone, emoji)`` tuples.
        '''
        url = self.url_endpoint + 'tone'
        data = {
            'key': self.api_key,
            'text': text,
        }
        return self._request(url, data)

    def sentiment(
        self,
        text,
    ):
        '''
        Detects the sentiment (positive, negative, or neutral) of the provided text.

        The overall sentiment is returned along with the sentiment for each sentence.

        :param text: Text to analyze the sentiment for.
        :type text: str
        :rtype: dict
        :return:
            - sents: The sentences the text contains.
            - overall: List of ``(probability, sentiment)`` tuples for the whole text.
            - results: For each sentence, a list of ``(probability, sentiment)`` tuples.
        '''
        url = self.url_endpoint + 'sentiment'
        data = {
            'key': self.api_key,
            'text': text,
        }
        return self._request(url, data)

    def quality(
        self,
        text,
        sentence_scores=None,
        rubric=None,
    ):
        '''
        Computes a quality score for the provided text based on how "surprising"
        the text is to the model. Lower surprisal corresponds to higher scores.
        Optionally also returns a per-sentence breakdown and an LLM-judged rubric.

        :param text: Text to compute a quality score for. The base score is computed
            on the leading ~4,000 characters; the rubric evaluates the whole text
            (up to 20,000 characters).
        :type text: str
        :param sentence_scores: If true, also return a 1-5 score for each sentence
            under `sentences`.
        :type sentence_scores: bool
        :param rubric: If true, also return an LLM-judged rubric under `rubric`
            (billed at the Tone rate).
        :type rubric: bool
        :rtype: dict
        :return:
            - score: A score from 1 (low quality) to 5 (high quality).
            - sentences: If sentence_scores is set, list of {start, end, text, score} in
              document order; start/end are character offsets into the text.
            - rubric: If rubric is set, {overall, dimensions: {clarity, coherence,
              correctness, concision}, summary, issues: [{quote, dimension, note,
              suggestion, start, end}]}; scores are integers 1-5.
        '''
        url = self.url_endpoint + 'quality'
        data = {
            'key': self.api_key,
            'text': text,
        }
        if sentence_scores is not None:
            data['sentence_scores'] = sentence_scores
        if rubric is not None:
            data['rubric'] = rubric
        return self._request(url, data)

    def langdetect(
        self,
        text,
        top_k=None,
        segments=None,
    ):
        '''
        Identifies the language of the provided text, with optional runner-up
        candidates and a per-segment breakdown for mixed-language text.

        :param text: Text to identify the language for (up to 20,000 characters).
        :type text: str
        :param top_k: Number of language candidates to return, 1-10. Defaults to 3 server-side.
        :type top_k: int
        :param segments: If true, also detect the language of each line/sentence
            of the text and return them under `segments`.
        :type segments: bool
        :rtype: dict
        :return:
            - lang: The detected language code (mostly ISO 639-1).
            - name: English name of the detected language.
            - conf: Confidence score for the detection result.
            - candidates: List of {lang, name, conf} for the top languages, most likely first.
            - segments: If segments is set, list of {start, end, text, lang, name, conf, candidates}
              in document order; start/end are character offsets into the text.
        '''
        url = self.url_endpoint + 'langdetect'
        data = {
            'key': self.api_key,
            'text': text,
        }
        if top_k is not None:
            data['top_k'] = top_k
        if segments is not None:
            data['segments'] = segments
        return self._request(url, data)

    def profanity(
        self,
        text,
    ):
        '''
        Checks the provided text for profanity, returning a 0/1 label per token.

        :param text: Text to check for profanity.
        :type text: str
        :rtype: dict
        :return:
            - toks: The tokens (words) detected in the text.
            - labels: For each token, 0 (not profanity) or 1 (profanity).
        '''
        url = self.url_endpoint + 'profanity'
        data = {
            'key': self.api_key,
            'text': text,
        }
        return self._request(url, data)

    def safety(
        self,
        text,
        threshold=None,
        spans=None,
    ):
        '''
        Scores the provided text on seven content-safety categories: toxicity,
        profanity, harassment, hate_speech, self_harm, sexual, and violence.

        :param text: Text to score, up to 20,000 characters.
        :type text: str
        :param threshold: Score at or above which a category is flagged.
            Between 0 and 1 inclusive; the API defaults to 0.5.
        :type threshold: float
        :param spans: When True, the response also includes the offending
            passages as spans, each with its text, start/end character offsets
            into the submitted text, per-passage category scores, and
            flagged_categories. The API defaults to False.
        :type spans: bool
        :rtype: dict
        :return:
            - scores: A probability from 0 to 1 for each category.
            - flagged: True if any category scored at or above the threshold.
            - flagged_categories: Categories that scored at or above the threshold.
            - threshold: The threshold that was applied.
            - spans: Only with spans=True — the offending passages, most
              severe first, as {text, start, end, scores, flagged_categories}.
        '''
        url = self.url_endpoint + 'safety'
        data = {
            'key': self.api_key,
            'text': text,
        }
        if threshold is not None:
            data['threshold'] = threshold
        if spans is not None:
            data['spans'] = spans
        return self._request(url, data)

    def pii(
        self,
        text,
        types=None,
        redact=None,
    ):
        '''
        Detects personally identifiable information (PII) in the provided text and
        optionally returns a redacted copy.

        Detection is deterministic (pattern matching plus checksum validation, no ML)
        and every entity comes with exact character offsets into ``text``, so pass
        raw text (not HTML) and apply the spans to your own copy of the document.
        Person names and street addresses are not detected.

        :param text: Text to scan for PII.
        :type text: str
        :param types: Optional list of PII types to detect. Defaults to all types:
            ``email``, ``phone``, ``ssn``, ``credit_card``, ``ip_address``, ``iban``,
            ``us_bank_routing``.
        :type types: list[str]
        :param redact: If True, the response also includes ``redacted_text`` with every
            detected entity replaced by a placeholder such as ``[EMAIL]``.
        :type redact: bool
        :rtype: dict
        :return:
            - entities: List of ``{type, text, start, end, replacement}`` dicts, sorted
              by ``start``; spans never overlap.
            - flagged: True if any PII was detected.
            - types: Sorted list of the PII types found.
            - redacted_text: Only present when ``redact`` is True.
        '''
        url = self.url_endpoint + 'pii'
        data = {
            'key': self.api_key,
            'text': text,
        }
        if types is not None:
            if (not isinstance(types, Iterable)
                    or isinstance(types, (str, bytes, dict))):
                raise TypeError('types must be a list of entity type names')
            data['types'] = list(types)
        if redact is not None:
            data['redact'] = redact
        return self._request(url, data)

    def seo(
        self,
        text,
        keywords=None,
        suggestions=None,
        lang=None,
    ):
        '''
        Analyzes the provided page or article text for SEO: deterministic content
        statistics and readability, target-keyword usage, the most frequent terms, and
        (optionally) LLM-generated titles, meta descriptions, a URL slug, and focus
        keywords.

        :param text: Page or article body, plain text or HTML (block tags become line
            breaks, inline tags are removed), up to 20,000 characters.
        :type text: str
        :param keywords: Optional list of up to 10 target keyword phrases, most
            important first (the first is the primary keyword). Each 1-100 characters.
            Measured in the text and steered into the suggestions.
        :type keywords: list[str]
        :param suggestions: If False, only the deterministic ``stats``, ``keywords`` and
            ``top_terms`` are returned (free); no ``suggestions`` are generated. The API
            defaults to True (billed at the Tone rate).
        :type suggestions: bool
        :param lang: ISO 639-1 language code of the text (a region subtag such as
            ``pt-BR`` is allowed, or ``auto``). The API defaults to ``en``. Only selects
            the readability formulas: ``flesch_reading_ease`` and
            ``flesch_kincaid_grade`` are computed for ``en``, ``de``, ``es``, ``fr``,
            ``it``, ``nl``, ``pl`` and ``ru`` and are None for any other language.
        :type lang: str
        :rtype: dict
        :return:
            - stats: ``{chars, words, sentences, paragraphs, reading_time_min,
              flesch_reading_ease, flesch_kincaid_grade}``; the two readability fields
              are None for languages without readability support.
            - keywords: One ``{keyword, count, density, in_first_100_words}`` dict per
              submitted target keyword, in the same order; empty when none were sent.
            - top_terms: Up to 10 most frequent content unigrams/bigrams as
              ``{term, count}`` dicts (lower-cased, English stopwords removed).
            - suggestions: Only present when ``suggestions`` is not False:
              ``{titles, meta_descriptions, slug, keywords}`` where ``titles`` and
              ``meta_descriptions`` are lists of strings, ``slug`` is a kebab-case
              string (or None when no ASCII slug could be derived, e.g. purely CJK
              content) and ``keywords`` is a list of focus-keyword phrases.
        '''
        url = self.url_endpoint + 'seo'
        data = {
            'key': self.api_key,
            'text': text,
        }
        if keywords is not None:
            if (not isinstance(keywords, Iterable)
                    or isinstance(keywords, (str, bytes, dict))):
                raise TypeError('keywords must be a list of keyword strings')
            data['keywords'] = list(keywords)
        if suggestions is not None:
            data['suggestions'] = suggestions
        if lang is not None:
            data['lang'] = lang
        return self._request(url, data)

    def classify(
        self,
        text,
        labels,
        multi_label=None,
        threshold=None,
        context=None,
    ):
        '''
        Classifies the provided text into one (or several) of the labels you supply.
        Zero-shot: no training data or setup is needed, just the label names and,
        optionally, a short description per label.

        Example::

            client.classify(
                'I was charged twice for my last invoice.',
                labels=[
                    'billing',
                    {'name': 'technical issue', 'description': 'Bugs, crashes, errors'},
                    'shipping',
                    'other',
                ],
                context='Support tickets for a SaaS billing product',
            )
            # {'label': 'billing',
            #  'labels': ['billing'],
            #  'scores': [{'label': 'billing', 'score': 0.86},
            #             {'label': 'technical issue', 'score': 0.07},
            #             {'label': 'shipping', 'score': 0.04},
            #             {'label': 'other', 'score': 0.03}],
            #  'rationale': 'The customer reports being charged twice on one invoice.',
            #  'multi_label': False}

        :param text: Text to classify, plain text or HTML (tags are stripped), up to
            10,000 characters.
        :type text: str
        :param labels: 2-20 candidate labels. Each entry is either a label name (str) or
            a dict ``{'name': str, 'description': str}`` where ``description`` is
            optional. Names are up to 50 characters and must be unique
            (case-insensitive); descriptions are up to 200 characters and help the
            model with borderline decisions.
        :type labels: list[str | dict]
        :raises TypeError: If ``labels`` is None, a single string or a dict rather
            than a list/tuple of labels.
        :param multi_label: If False (the API default), exactly one label applies and
            the scores form a probability distribution over the labels. If True, zero,
            one or several labels may apply and each score is an independent 0-1
            probability.
        :type multi_label: bool
        :param threshold: Multi-label cut-off, 0-1: ``labels`` in the response contains
            every label with ``score >= threshold``. The API defaults to 0.5. Ignored in
            single-label mode.
        :type threshold: float
        :param context: Up to 500 characters describing what the texts are or how to
            decide (e.g. ``'Support tickets for a SaaS billing product'``). Guidance
            only; the model can still only answer with the labels you provide.
        :type context: str
        :rtype: dict
        :return:
            - label: Best-matching label name (always one of the input labels).
            - labels: Single-label mode: ``[label]``. Multi-label mode: every label
              with ``score >= threshold``, descending by score; may be empty when none
              of the labels apply.
            - scores: One ``{label, score}`` dict per input label, sorted descending
              by score (0-1, rounded to 4 decimals).
            - rationale: One sentence naming the evidence in the text (may be empty).
            - multi_label: The mode that was used.
        '''
        # A bare string would silently be split into one-character labels and
        # None would raise an opaque TypeError from list(); fail loudly instead.
        if (not isinstance(labels, Iterable)
                or isinstance(labels, (str, bytes, dict))):
            raise TypeError('labels must be a list of label names or '
                            '{name, description} dicts')
        url = self.url_endpoint + 'classify'
        data = {
            'key': self.api_key,
            'text': text,
            'labels': list(labels),
        }
        if multi_label is not None:
            data['multi_label'] = multi_label
        if threshold is not None:
            data['threshold'] = threshold
        if context is not None:
            data['context'] = context
        return self._request(url, data)
