import time
import os
import re
import csv
import nltk
import requests
import pandas as pd
import numpy as np

from utils.inout import read_tweets
from utils.preprocess import basic_text_normalization
from utils.search import Searcher
from utils.constants import *

from newspaper import Article
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
from bs4 import BeautifulSoup

MAX_TWEETS = 100000


def clean_duplicates(data):
    initial_size = data.shape[0]
    data.drop_duplicates(subset='tweet_id', keep='first', inplace=True)
    data.reset_index(drop=True, inplace=True)
    data['clean_text'] = basic_text_normalization(data.text, drop=True)
    # tw_data.sort_values(by=['clean_text', 'in_reply_to_user_id'], ascending=True, na_position='first', inplace=True)

    data.set_index('tweet_id', inplace=True, drop=True)
    data['my_reply_count'] = 0
    tweet_replies = data.groupby('in_reply_to_tweet_id').size()
    data.my_reply_count.update(tweet_replies)

    del_ixs = []
    for ctext, subset in data.groupby('clean_text'):
        if subset.shape[0] > 1:
            cond1 = (subset.my_reply_count == 0)
            if all(cond1):
                cond1[0] = False
            del_ixs.extend(subset[cond1].index.tolist())
    data.drop(del_ixs, axis=0, inplace=True)

    data.sort_values(by=['conversation_id', 'date'], ascending=True, na_position='first', inplace=True)
    data.drop(['clean_text', 'my_reply_count'], axis=1, inplace=True)
    data.reset_index(drop=False, inplace=True)
    data = data[['author_id'] + [c for c in data.columns if c != 'author_id']]
    print(f'The number of tweets after the deduplication step went from {initial_size} to {data.shape[0]}')
    return data


def run_title_strategy(title, date, source, rh_id, keep_stopwords=True):
    filename = f'{source}_tweets.csv'

    if not keep_stopwords:
        title = ' '.join([w for w in nltk.word_tokenize(title)
                          if w not in stopwords.words(LANG_MAPPER[SOURCE_LANG[source]])])
        title = re.sub('\s+', ' ', re.sub('[^\w\s]', '', title))

    query_params = {'keys': title,
                    'date_since': f'{date-5}-01-01',
                    'date_to': '',  # min(f'{date}-12-31', time.strftime('%Y-%m-%d')),
                    'lang': SOURCE_LANG[source]}

    # Specify whether the column names must be initially written to the output file or not
    if os.path.isfile(f'./data/{filename}'):
        header = False
    else:
        header = True

    searcher = Searcher(max_tweets=MAX_TWEETS)
    searcher.run_query(query_params, filename, header, rh_id)

    # Wait for the searcher to finish before going to another query
    while searcher.is_running:
        pass

    time.sleep(searcher.sleep_time)


def run_url_tweets_strategy(url, fact_checker, rh_id):
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, "lxml")
    links = soup.find_all("blockquote", attrs={"class": "twitter-tweet"})
    # embed_tweets = [re.sub('\s+pic\.twitter\..*\s?', ' ', item.find('p').text) for item in links]
    embed_tweet_ids = [re.sub('.*/status/(.*)\?.*', r'\g<1>', item.find_all('a')[-1]['href']) for item in links]
    filename = f'{fact_checker}_tweets.csv'
    # for i, (q, ix) in enumerate(zip(embed_tweets, embed_tweet_ids)):
    #     print(f'\t{i} --> {q} : {ix}')
    if embed_tweet_ids:
        print(f'\t+++ Searching for {len(embed_tweet_ids)} embedded tweet ids...')
        Searcher(max_tweets=MAX_TWEETS).tweet_lookup(embed_tweet_ids, filename=filename, rh_id=rh_id)
    else:
        print('\t+++ No embedded tweets were found...')
    # multiple_search(embed_tweets, query_params, rh_id, filename)


def run_url_quotes_strategy(url, date, source, rh_id):
    # Extract body of the article
    article = Article(url)
    article.download()
    article.parse()

    # Obtain the quoted text from the fact-checker article
    quotations = re.findall('["“«](.*?)[”"»]', re.sub('[‘’]', '', article.text))
    quotations = [[w for w in nltk.word_tokenize(q) if w not in stopwords.words('spanish')] for q in quotations]
    quotations = [re.sub('[\W]+', ' ', ' '.join(list(set(q))).lower()) for q in quotations if len(q) > 3]

    # Build search query and retrieve tweets per quote
    query_params = {'date_since': f'{date - 2}-01-01',
                    'date_to': '',  # min(f'{date}-12-31', time.strftime('%Y-%m-%d')),
                    'lang': SOURCE_LANG[source],
                    'max_tweets': MAX_TWEETS}
    filename = f'{source}_tweets.csv'
    # for i, q in enumerate(quotations):
    #     print(f'\t{i} --> {q}')
    multiple_search(quotations, query_params, rh_id, filename)


def multiple_search(queries, query_params, rh_id, filename):
    searcher = Searcher(max_tweets=MAX_TWEETS)
    if os.path.isfile(f'./data/{filename}'):
        header = False
    else:
        header = True
    for query in queries:
        print(f'\t+++ Searching the following keys: {query}')
        query_params['keys'] = query
        searcher.run_query(query_params, filename, header, rh_id)
        while searcher.is_running:
            pass
        time.sleep(searcher.sleep_time)
        header = False


def expand_conversations(fact_checker):
    filename = f'{fact_checker}_tweets.csv'
    tweets = read_tweets(filename)

    # Save backup file
    tweets.to_csv(os.path.join(DATA_PATH, filename[:-4] + '_unexpanded.csv'),
                  mode='w', index=False, quoting=csv.QUOTE_ALL)

    # Expand only conversation_ids of tweets either having replies (posterior thread) or being replies (previous thread)
    ixs_interest = np.bitwise_or(tweets.reply_count > 0, tweets.conversation_id != tweets.tweet_id)
    expand_ids = tweets[ixs_interest][['conversation_id', 'rh_id']].drop_duplicates()
    print(f'\033[94m Expanding {expand_ids.shape[0]} conversations for {fact_checker} fact checker...\033[0m')

    # 'start_time' must be on or after 2006-03-21T00:00Z (Twitter constraint)
    query_params = {'lang': SOURCE_LANG[fact_checker],
                    'date_since': f'2006-03-21',
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}
    searcher = Searcher()
    for _, row in expand_ids.iterrows():
        print(f'\033[94m Expanding {row.conversation_id} corresponding to {row.rh_id}...\033[0m')
        if row.conversation_id in EXCLUDE_CONV_IDS.get(fact_checker, []):
            print(f'\t+++ This conversation id has been manually excluded from the expansion')
        else:
            query_params['conversation_id'] = row.conversation_id
            searcher.run_query(query_params, filename, initial_header=False, rh_id=row.rh_id)
            while searcher.is_running:
                pass
            time.sleep(searcher.sleep_time)

    # Deduplicate retrieved tweets by tweet_id
    tweets = read_tweets(filename)
    tweets.drop_duplicates(subset=['tweet_id'], inplace=True)

    # Apparently, Twitter API search by conversation_id does not retrieve the first tweet in multiple cases
    lookup_ids = tweets.groupby('conversation_id').apply(lambda s: not any(pd.isna(s.in_reply_to_tweet_id)))
    lookup_ids = lookup_ids[lookup_ids].index.tolist()

    if lookup_ids:
        print(f'\033[94m Looking for {len(lookup_ids)} initial comments to add to the {tweets.shape[0]} '
              f'existing tweets...\033[0m')
        searcher.tweet_lookup(lookup_ids, filename)
        while searcher.is_running:
            pass
    else:
        print(f'\033[94m All conversations have their initial comments...\033[0m')

    # Deduplicate tweets based on clean text (without user tags or URLs)
    tweets = read_tweets(filename)
    tweets = clean_duplicates(tweets)

    # Populate Racial Hoax ID for the starting tweets previously retrieved
    unexpanded_data = read_tweets(f'{fact_checker}_tweets_unexpanded.csv')
    mapper = unexpanded_data.drop_duplicates(subset='conversation_id')[['conversation_id', 'rh_id']]
    mapper = mapper.set_index('conversation_id').rh_id
    tweets.rh_id = tweets.conversation_id.map(mapper)

    # Save to file with the new data
    tweets.to_csv(os.path.join(DATA_PATH, filename), mode='w', index=False, quoting=csv.QUOTE_ALL)


def force_target_in_text(rh_data, fact_checker):
    def prepare(l):
        return list(set([sub_t for t in l for sub_t in re.split('\s*,\s*', t)]))

    def filter_target_groups(g):
        sub_g = [np.bitwise_and.reduce([subset.text.str.lower().str.contains(stemmer.stem(w.lower()))
                                        for w in re.split('\s+', g_i)])
                 for g_i in g]
        return np.bitwise_or.reduce(sub_g)

    stemmer = SnowballStemmer(LANG_MAPPER[SOURCE_LANG[fact_checker]])

    tw_filename = fact_checker + '_tweets.csv'
    tw_data = read_tweets(tw_filename)

    # Save old data to backup file
    tw_data.to_csv(os.path.join(DATA_PATH, tw_filename[:-4] + '_unfiltered.csv'),
                   mode='w', index=False, header=True, quoting=csv.QUOTE_ALL)

    tw_data.drop_duplicates(subset=['tweet_id'], inplace=True)

    # Filter racial hoaxes to those of the current fact checker
    fc_rh_data = rh_data[rh_data.Source.str.contains(fact_checker)]
    fc_rh_data.Source = fc_rh_data.Source.str.strip()

    # Get all targets per URL (possibly containing a set of hoaxes) for the posterior filtering
    col_of_interest = ['RH ID', 'Object of discourse (literal)']
    url_groups = fc_rh_data.groupby('Source').apply(lambda s: [prepare(s[c].tolist()) for c in col_of_interest]).values

    keep_ixs = []
    for g in url_groups:
        subset = tw_data[tw_data['rh_id'].isin(g[0])]
        # Find tweets within the subset that contain the target group
        keep_ixs.extend(subset[filter_target_groups(g[1])].index.tolist())

    print(f'Out of {tw_data.shape[0]} tweets, we will keep {len(keep_ixs)} due to target-in-text constraint')

    tw_data = tw_data.loc[keep_ixs]
    rm_cond = np.isin(tw_data.tweet_id, EXCLUDE_TWEET_IDS[fact_checker])
    tw_data = tw_data[~rm_cond]

    print(f'Furthermore, {sum(rm_cond)} tweets have been removed according to manual check')

    # Save new data to main file
    tw_data.to_csv(os.path.join(DATA_PATH, tw_filename), index=False, mode='w', header=True, quoting=csv.QUOTE_ALL)
