import run_gui
import run_twitter_api
import json
import re
import pandas as pd
import dateutil.parser

from utils.constants import *
from utils.search import Searcher
from utils.strategies import *


def read_data():
    from ast import literal_eval

    list_cols = ['hashtags', 'annotations', 'urls']
    converters = {c: literal_eval for c in list_cols}
    converters['date'] = lambda d: dateutil.parser.isoparse(d[:-5])

    before_data = pd.read_csv('./data/tweets_before_query_2.csv', converters=converters)
    print(f'Number of tweets before the specified date: {before_data.shape[0]}')
    after_data = pd.read_csv('./data/tweets_after_query_2.csv', converters=converters)
    print(f'Number of tweets after the specified date: {after_data.shape[0]}')

    return before_data, after_data


def visualize_data():
    import os

    data_path = './data'
    file = 'bufale_tweets.csv'
    data = pd.read_csv(os.path.join(data_path, file))
    data.sort_values(by=['conversation_id', 'in_reply_to_tweet_id'], na_position='first', inplace=True)
    print(data.info())


def run_query():
    # See all available languages and their code in ./utils/constants.py --> AVAILABLE_LANGS
    lang = AVAILABLE_LANGS['Spanish']
    # Date in the format 'yyyy-MM-dd'. Maximum possible end date is today
    start_date = '2021-05-20'
    end_date = '2021-05-22'
    # Maximum number of tweets to be retrieved from Twitter
    max_tweets = 12
    # Combination of keywords and hashtags that needs to be met by the retrieved tweets
    keys = 'Ceuta (inmigrante OR migrante)'
    # (Partial) URL to be contained in the tweet
    url = ''  # 'youtube.com'
    query_params = {'hashtags': [],
                    'keywords': [],
                    'keys': keys,
                    'url': url,
                    'date_since': start_date,
                    'date_to': end_date,
                    'lang': lang,
                    'max_tweets': max_tweets,
                    'max_results': min(500, max_tweets)}

    searcher = Searcher()
    searcher.run_query(query_params, filename='raw_mode.csv')


def run_automatic_downloader():
    download_from_sources = ['newtral', 'migracion.maldita']  # ['bufale', 'butac', 'newtral', 'migracion.maldita']
    racial_hoaxes = pd.read_csv('./query_files/es_version.csv')
    visited_urls = []
    for ix, row in racial_hoaxes.iterrows():
        fact_check_url = row.Source
        if fact_check_url not in visited_urls:
            visited_urls.append(fact_check_url)

            fact_checker = re.sub('\s*(https://)?(www.)?([\w\.]+)\..*', '\g<3>', fact_check_url)
            fact_title = row.Title
            fact_check_date = row.Date
            rh_id = row['RH ID']

            if fact_checker in download_from_sources:
                print(f'\033[94m {row["RH ID"]} \u27f6 {fact_checker} \u27f6 {fact_title}\033[0m')

                if fact_checker == 'bufale':
                    run_title_strategy(fact_title, int(fact_check_date), fact_checker, rh_id)
                elif fact_checker in ['newtral', 'migracion.maldita']:  # 'newtral', 'migracion.maldita'
                    print('Searching by embedded tweets...')
                    run_url_tweets_strategy(fact_check_url, int(fact_check_date[-4:]), fact_checker, rh_id)
                    print('Searching by quoted text...')
                    run_url_quotes_strategy(fact_check_url, int(fact_check_date[-4:]), fact_checker, rh_id)

    expand_from_sources = []
    for fact_checker in expand_from_sources:
        expand_conversations(fact_checker)


if __name__ == '__main__':
    # run_gui.run()
    # run_query()
    run_automatic_downloader()
    # visualize_data()

    print('Finished...')
