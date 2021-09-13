import run_gui
import run_twitter_api
import json
import re
import pandas as pd
import dateutil.parser

from utils import tweet_lookup
from utils.constants import *
from utils.inout import read_tweets
from utils.preprocess import *
from utils.search import Searcher
from utils.strategies import *
from nltk.stem import SnowballStemmer


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
    file = 'migracion.maldita_tweets_2.csv'
    data = pd.read_csv(os.path.join(data_path, file))
    maybe_data = np.isin(data.conversation_id, data[data['in/out of topic'] == 'maybe'].conversation_id)
    temp = data[maybe_data]
    # print(temp.groupby('conversation_id').size())
    # data[(data.in_reply_to_tweet_id == -1) & (data.reply_count > 0)]
    temp = temp[temp.conversation_id == 1384566303789359111]
    temp_2 = temp[temp.text.str.contains('inmigrante')]
    temp.sort_values(by=['conversation_id', 'in_reply_to_tweet_id', 'date'], na_position='first', inplace=True)
    with_country = ~pd.isna(data.country)
    # print(data[with_country].country.unique())
    conver_size = data.groupby('conversation_id').size()
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    #     print(conver_size)
    # print(data.info())


def update_data():
    import os

    file = 'migracion.maldita_tweets_2.csv'
    data = pd.read_csv(os.path.join(DATA_PATH, file))
    out_ids = [1275538454089211906]

    data.loc[np.isin(data.conversation_id, out_ids), ['in/out of topic']] = 'out'
    data.to_csv(os.path.join(DATA_PATH, file), mode='w', index=False, quoting=csv.QUOTE_ALL)


def clean_data():
    fact_checker = 'migracion.maldita'

    rh_filename = 'full_version.csv'
    rh_data = pd.read_csv(os.path.join(QUERY_PATH, rh_filename))

    force_target_in_text(rh_data, fact_checker)


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
    download_from_sources = ['bufale', 'newtral', 'migracion.maldita']  # ['bufale', 'butac', 'newtral', 'migracion.maldita']
    racial_hoaxes = pd.read_csv('./query_files/full_version.csv')
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
                    run_url_tweets_strategy(fact_check_url, fact_checker, rh_id)
                    print('Searching by quoted text...')
                    run_url_quotes_strategy(fact_check_url, int(fact_check_date[-4:]), fact_checker, rh_id)

    noisy_sources = ['migracion.maldita']
    for fact_checker in noisy_sources:
        print(f'De-noising {fact_checker} data...')
        force_target_in_text(racial_hoaxes, fact_checker)

    expand_from_sources = ['bufale', 'newtral', 'migracion.maldita']
    for fact_checker in expand_from_sources:
        expand_conversations(fact_checker)


def normalize_ids():
    file = 'migracion.maldita_tweets.csv'
    full_data = pd.read_csv(os.path.join(DATA_PATH, file))
    for c in ['conversation_id', 'tweet_id', 'in_reply_to_tweet_id', 'author_id']:
        if full_data[c].dtype == np.int64:
            full_data[c] = full_data[c].astype(str)
        else:
            full_data[c] = full_data[c].fillna(-1)
            full_data[c] = full_data[c].astype(np.float64).astype(np.int64).astype(str)
    full_data.to_csv(os.path.join(DATA_PATH, file), mode='w', index=False, quoting=csv.QUOTE_ALL)


def tweets_search():
    Searcher(max_tweets=10).tweet_lookup(['1384644393752203274', '1384551983391166467'], 'test.csv')


def conversation_search():
    query_params = {'lang': 'es',
                    'date_since': f'2006-03-21',
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}
    filename = 'conversation_test.csv'
    if os.path.isfile(os.path.join(DATA_PATH, filename)):
        os.remove(os.path.join(DATA_PATH, filename))
    conversation_ids = [1384566303789359111]
    searcher = Searcher()
    for id in conversation_ids:
        print(f'\033[94m Searching conversation {id}...\033[0m')
        query_params['conversation_id'] = id
        searcher.run_query(query_params, filename, initial_header=True, rh_id=None)
        while searcher.is_running:
            pass
        time.sleep(searcher.sleep_time)


def test():
    def missing_first(s):
        is_first = s.in_reply_to_tweet_id
        is_first = pd.isna(is_first) | (is_first == -1)
        return not any(is_first)
    filename = 'migracion.maldita_tweets.csv'
    data = read_tweets(filename)
    lookup_ids = data.groupby('conversation_id').apply(lambda s: not any(pd.isna(s.in_reply_to_tweet_id)))
    lookup_ids = lookup_ids[lookup_ids].index.tolist()
    print(f'Looking for first tweet of {len(lookup_ids)} conversations out of {data.conversation_id.nunique()}...')


if __name__ == '__main__':
    # run_gui.run()
    # run_query()
    # run_automatic_downloader()
    # visualize_data()
    clean_data()
    # normalize_ids()
    # tweets_search()
    # conversation_search()
    # test()

    print('Finished...')
