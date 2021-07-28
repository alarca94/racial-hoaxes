import csv
import functools
import json
import re
import os
import threading

import dateutil.parser
import pandas as pd
import requests

from utils.inout import DATA_PATH, DOWNLOAD_FILE

HTTP_OK = 200


class PeriodicTimer(object):
    def __init__(self, interval, callback):
        self.interval = interval

        @functools.wraps(callback)
        def wrapper(*args, **kwargs):
            result = callback(*args, **kwargs)
            if result:
                self.thread = threading.Timer(self.interval,
                                              self.callback)
                self.thread.start()

        self.callback = wrapper

    def start(self):
        self.thread = threading.Timer(self.interval, self.callback)
        self.thread.start()

    def stop(self):
        self.thread.cancel()


class Searcher:
    def __init__(self, out_widget=None):
        self.search_all_endpoint = "https://api.twitter.com/2/tweets/search/all"
        self.tweet_lookup_endpoint = "https://api.twitter.com/2/tweets"
        self.search_url = self.search_all_endpoint
        self.out_widget = out_widget
        self.enabled = True
        self.sleep_time = 3
        self.columns = ['author_id', 'tweet_id', 'conversation_id', 'in_reply_to_tweet_id', 'date', 'lang', 'text',
                        'hashtags', 'annotations', 'possibly_sensitive', 'like_count', 'quote_count', 'reply_count',
                        'retweet_count', 'urls', 'place_name', 'country', 'place_type']
        self.headers = ''
        self.params = {}
        self.max_tweets = 1000000
        self.curr_tweets = 0
        # self.timer = QTimer()
        self.timer = PeriodicTimer(self.sleep_time, self._continure_query)
        # self.timer.timeout.connect(self._continure_query)
        # self.timer.setInterval(self.sleep_time * 1000)
        self.save_to_file = None
        self.is_running = False

    def disable(self):
        self.enabled = False

    def enable(self):
        self.enabled = True

    @staticmethod
    def _create_headers():
        with open('keys.json', 'r') as f:
            keys = json.load(f)
        headers = {"Authorization": "Bearer {}".format(keys['bearer_token'])}
        return headers

    def _connect_to_endpoint(self, headers, params):
        try:
            response = requests.request("GET", self.search_url, headers=headers, params=params)
        except Exception:
            response = requests.request("GET", self.search_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f'ERROR Code: {response.status_code}, with ERROR Message: {response.text}')
            return response.status_code, {}
        return response.status_code, response.json()

    @staticmethod
    def _extract_info(tweet, places):
        author_id = tweet.get('author_id', None)
        created_at = tweet.get('created_at', None)
        conversation_id = tweet.get('conversation_id', None)
        in_reply_to_user_id = tweet.get('in_reply_to_user_id', None)
        referenced_tweets = tweet.get('referenced_tweets', [])
        in_reply_to_tweet_id = None
        for ref_tweet in referenced_tweets:
            if ref_tweet['type'] == 'replied_to':
                in_reply_to_tweet_id = ref_tweet['id']
        hashtags = [h.get('tag', None) for h in tweet.get('entities', {}).get('hashtags', [])]
        annotations = [(a.get('normalized_text', None), a.get('type', None), a.get('probability', None))
                       for a in tweet.get('entities', {}).get('annotations', [])]
        urls = [url.get('expanded_url', None) for url in tweet.get('entities', {}).get('urls', [])]
        tweet_id = tweet.get('id', None)
        lang = tweet.get('lang', None)
        possibly_sensitive = tweet.get('possibly_sensitive', None)
        like_count = tweet.get('public_metrics', {}).get('like_count', None)
        quote_count = tweet.get('public_metrics', {}).get('quote_count', None)
        reply_count = tweet.get('public_metrics', {}).get('reply_count', None)
        retweet_count = tweet.get('public_metrics', {}).get('retweet_count', None)
        place_name = None
        country = None
        place_type = None
        place_id = tweet.get('geo', {}).get('place_id', None)
        if places.shape[0] > 0 and place_id is not None and place_id in places.index.values:
            place_name = places.loc[place_id, 'full_name']
            country = places.loc[place_id, 'country_code']
            place_type = places.loc[place_id, 'place_type']

        text = tweet.get('text', None)
        return (author_id, tweet_id, conversation_id, in_reply_to_tweet_id, created_at, lang, text, hashtags,
                annotations, possibly_sensitive, like_count, quote_count, reply_count, retweet_count, urls,
                place_name, country, place_type)

    def _create_query(self, query_params):
        # key_list = query_params['hashtags'] + query_params['keywords']
        q = f'lang:{query_params["lang"]} -is:retweet'
        if query_params.get('keys', False):
            keys = re.sub(r"([\W\s]+|\sor\s)", " ", query_params["keys"])
            q = f'({keys}) {q}'
        if query_params.get('conversation_id', False):
            q = f'conversation_id:{query_params["conversation_id"]} {q}'
        if query_params.get('url', False):
            q += f' url:{query_params["url"]}'
        return q

    def _continure_query(self):
        if 'next_token' in self.json_response.get('meta', {}).keys() and self.curr_tweets < self.max_tweets and \
                self.enabled:
            # Repeat the request with the same parameters but adding the "next_token" keyword with the value of the
            # previous request
            self.params['next_token'] = self.json_response['meta']['next_token']
            if (self.max_tweets - self.curr_tweets) < self.params['max_results']:
                self.params['max_results'] = max(10, self.max_tweets - self.curr_tweets)
            status_code, self.json_response = self._connect_to_endpoint(self.headers, self.params)

            if status_code != HTTP_OK:
                print(f'Program exit due to HTTP code: {status_code}')
                self.timer.stop()
            else:
                data = self.json_response.get('data', [])
                places = pd.DataFrame(self.json_response.get('includes', {}).get('places', []))
                if places.shape[0] > 0:
                    places.set_index('id', drop=True, inplace=True)

                tweet_data = []
                # Extract necessary tweets info
                for tweet in data:
                    tweet_data.append(self._extract_info(tweet, places))
                self.curr_tweets += len(tweet_data)

                msg = f'Number of tweets retrieved: {self.curr_tweets}'  # \tLast Date: {tweet_data[-1][2]}'
                if self.out_widget is not None:
                    self.out_widget.show_message(msg, self.sleep_time * 1000, 'default')
                else:
                    print(msg)

                # Keep saving the dataset in the file per tweets request
                tweet_df = pd.DataFrame(tweet_data, columns=self.columns)
                if self.rh_id is not None:
                    tweet_df['rh_id'] = self.rh_id
                tweet_df.to_csv(self.save_to_file, mode='a', index=False, header=False, quoting=csv.QUOTE_ALL)

                return True
        else:
            self.timer.stop()
            self.is_running = False

    def tweet_lookup(self, query_params, filename=None, initial_header=True, rh_id=None):
        self.search_url = self.tweet_lookup_endpoint
        return self.run_query(query_params, filename, initial_header, rh_id)

    def search_all(self, query_params, filename=None, initial_header=True, rh_id=None):
        self.search_url = self.search_all_endpoint
        return self.run_query(query_params, filename, initial_header, rh_id)

    def run_query(self, query_params, filename=None, initial_header=True, rh_id=None):
        self.is_running = True
        self.rh_id = rh_id

        if filename is None:
            self.save_to_file = DOWNLOAD_FILE
        else:
            self.save_to_file = filename

        self.save_to_file = os.path.join(DATA_PATH, self.save_to_file)

        q = self._create_query(query_params)

        tweet_fields = ['attachments', 'author_id', 'conversation_id', 'created_at', 'entities',
                        'id', 'in_reply_to_user_id', 'lang', 'possibly_sensitive', 'public_metrics',
                        'referenced_tweets', 'source', 'text', 'withheld']

        self.headers = self._create_headers()

        self.params = {'query': q,
                       'tweet.fields': ','.join(tweet_fields),
                       'media.fields': ','.join(['type', 'preview_image_url']),
                       'expansions': 'geo.place_id',
                       'place.fields': ','.join(['country', 'country_code', 'full_name', 'place_type']),
                       'max_results': query_params['max_results']}

        if query_params.get('date_to', False):
            date_to = dateutil.parser.isoparse(query_params['date_to'])
            self.params['end_time'] = date_to.isoformat('T') + 'Z'
        if query_params.get('date_since', False):
            date_since = dateutil.parser.isoparse(query_params['date_since'])
            self.params['start_time'] = date_since.isoformat('T') + 'Z'

        status_code, self.json_response = self._connect_to_endpoint(self.headers, self.params)
        if status_code != 200:
            print(f'Program exit due to HTTP code: {status_code}')
            exit()

        data = self.json_response.get('data', [])
        places = pd.DataFrame(self.json_response.get('includes', {}).get('places', []))

        self.max_tweets = query_params['max_tweets']
        self.curr_tweets = 0

        if data:
            tweet_data = []
            if places.shape[0] > 0:
                places.set_index('id', drop=True, inplace=True)

            for tweet in data:
                tweet_data.append(self._extract_info(tweet, places))
            self.curr_tweets += len(tweet_data)

            # Save initial tweets request
            tweet_df = pd.DataFrame(tweet_data, columns=self.columns)
            if self.rh_id is not None:
                tweet_df['rh_id'] = self.rh_id
            tweet_df.to_csv(self.save_to_file, mode='a', index=False, header=initial_header, quoting=csv.QUOTE_ALL)

            msg = f'Number of tweets retrieved: {self.curr_tweets}'  # \tLast Date: {tweet_data[-1][2]}'
            if self.out_widget is not None:
                self.out_widget.show_message(msg, self.sleep_time * 1000, 'default')
            else:
                print(msg)

            # The response is supposed to return a "next_token" keyword when all tweets do not fit in a single response
            if 'next_token' in self.json_response.get('meta', {}).keys() and self.curr_tweets < self.max_tweets:
                self.timer.start()
            else:
                self.is_running = False
        else:
            if self.out_widget is not None:
                self.out_widget.showMessage(f'No data was retrieved with the specified query', self.sleep_time * 1000)
            else:
                print(f'No data was retrieved with the following query: {query_params}')
            self.is_running = False
