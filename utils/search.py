import requests
import json
import time
import csv
import os
import dateutil.parser
import pandas as pd
from PyQt5.QtCore import QTimer

from utils.inout import DATA_PATH, DOWNLOAD_FILE

HTTP_OK = 200


class Searcher:
    def __init__(self, out_widget=None):
        self.search_url = "https://api.twitter.com/2/tweets/search/all"
        self.out_widget = out_widget
        self.enabled = True
        self.sleep_time = 3
        self.columns = ['author_id', 'tweet_id', 'conversation_id', 'date', 'lang', 'text', 'hashtags', 'annotations',
                        'possibly_sensitive', 'like_count', 'quote_count', 'reply_count', 'retweet_count', 'urls']
        self.headers = ''
        self.params = {}
        self.max_tweets = 1000000
        self.curr_tweets = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self._continure_query)
        self.timer.setInterval(self.sleep_time * 1000)
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
        response = requests.request("GET", self.search_url, headers=headers, params=params)
        if response.status_code != 200:
            print(f'ERROR Code: {response.status_code}, with ERROR Message: {response.text}')
            return response.status_code, {}
        return response.status_code, response.json()

    @staticmethod
    def _extract_info(tweet):
        author_id = tweet.get('author_id', None)
        created_at = tweet.get('created_at', None)
        conversation_id = tweet.get('conversation_id', None)
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
        text = tweet.get('text', None)
        return (author_id, tweet_id, conversation_id, created_at, lang, text, hashtags, annotations, possibly_sensitive,
                like_count, quote_count, reply_count, retweet_count, urls)

    def _create_query(self, query_params):
        key_list = query_params["hashtags"] + query_params["keywords"]
        lang = query_params['lang']
        q = f'({" OR ".join(key_list)}) lang:{lang} -is:retweet'
        return q

    def _continure_query(self):
        if 'next_token' in self.json_response.get('meta', {}).keys() and self.curr_tweets < self.max_tweets and \
                self.enabled:
            # Repeat the request with the same parameters but adding the "next_token" keyword with the value of the
            # previous request
            self.params['next_token'] = self.json_response['meta']['next_token']
            if (self.max_tweets - self.curr_tweets) < self.params['max_results']:
                self.params['max_results'] = max(10, self.max_tweets - self.curr_tweets)
            status_code, json_response = self._connect_to_endpoint(self.headers, self.params)

            if status_code != HTTP_OK:
                self.timer.stop()
            else:
                data = json_response.get('data', [])

                tweet_data = []
                # Extract necessary tweets info
                for tweet in data:
                    tweet_data.append(self._extract_info(tweet))
                self.curr_tweets += len(tweet_data)
                print(len(tweet_data))

                msg = f'Number of tweets retrieved: {self.curr_tweets}'  # \tLast Date: {tweet_data[-1][2]}'
                if self.out_widget is not None:
                    self.out_widget.show_message(msg, self.sleep_time * 1000, 'default')
                else:
                    print(msg)

                # Keep saving the dataset in the file per tweets request
                tweet_df = pd.DataFrame(tweet_data, columns=self.columns)
                tweet_df.to_csv(self.save_to_file, mode='a', index=False, header=False, quoting=csv.QUOTE_ALL)
        else:
            self.timer.stop()
            self.is_running = False

    def run_query(self, query_params, filename=None):
        self.is_running = True

        if filename is None:
            self.save_to_file = DOWNLOAD_FILE
        else:
            self.save_to_file = filename

        self.save_to_file = os.path.join(DATA_PATH, self.save_to_file)

        date_to = dateutil.parser.isoparse(query_params['date_to'])
        date_since = dateutil.parser.isoparse(query_params['date_since'])
        q = self._create_query(query_params)

        tweet_fields = ['attachments', 'author_id', 'conversation_id', 'context_annotations', 'created_at', 'entities', 'geo', 'id',
                        'in_reply_to_user_id', 'lang', 'possibly_sensitive', 'public_metrics', 'referenced_tweets',
                        'source', 'text', 'withheld']

        self.headers = self._create_headers()

        self.params = {'query': q,
                       'tweet.fields': ','.join(tweet_fields),
                       'media.fields': ','.join(['type', 'preview_image_url']),
                       'start_time': date_since.isoformat('T') + 'Z',
                       'end_time': date_to.isoformat('T') + 'Z',
                       'max_results': query_params['max_results']}

        status_code, self.json_response = self._connect_to_endpoint(self.headers, self.params)
        if status_code != 200:
            exit()

        data = self.json_response.get('data', [])

        self.max_tweets = query_params['max_tweets']
        self.curr_tweets = 0

        if data:
            tweet_data = []
            for tweet in data:
                tweet_data.append(self._extract_info(tweet))
            self.curr_tweets += len(tweet_data)
            print(len(tweet_data))

            # Save initial tweets request
            tweet_df = pd.DataFrame(tweet_data, columns=self.columns)
            tweet_df.to_csv(self.save_to_file, mode='a', index=False, quoting=csv.QUOTE_ALL)

            msg = f'Number of tweets retrieved: {self.curr_tweets}'  # \tLast Date: {tweet_data[-1][2]}'
            if self.out_widget is not None:
                self.out_widget.show_message(msg, self.sleep_time * 1000, 'default')
            else:
                print(msg)

            # The response is supposed to return a "next_token" keyword when all tweets do not fit in a single response
            self.timer.start()
        else:
            if self.out_widget is not None:
                self.out_widget.showMessage(f'No data was retrieved with the specified query', self.sleep_time * 1000)
            else:
                print(f'No data was retrieved with the following query: {query_params}')
