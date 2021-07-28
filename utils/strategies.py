import time
import os
import re
import csv
import requests
import nltk
import pandas as pd
import numpy as np

from utils.search import Searcher
from utils.constants import *

from newspaper import Article
from nltk.corpus import stopwords
from bs4 import BeautifulSoup

MAX_TWEETS = 100000


def run_title_strategy(title, date, source, rh_id):
    filename = f'{source}_tweets.csv'
    query_params = {'keys': title,
                    'date_since': f'{date-5}-01-01',
                    'date_to': '',  # min(f'{date}-12-31', time.strftime('%Y-%m-%d')),
                    'lang': SOURCE_LANG[source],
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}

    # Specify whether the column names must be initially written to the output file or not
    if os.path.isfile(f'./data/{filename}'):
        header = False
    else:
        header = True

    searcher = Searcher()
    searcher.run_query(query_params, filename, header, rh_id)

    # Wait for the searcher to finish before going to another query
    while searcher.is_running:
        pass

    time.sleep(searcher.sleep_time)


def run_url_tweets_strategy(url, date, source, rh_id):
    html_content = requests.get(url).text
    soup = BeautifulSoup(html_content, "lxml")
    links = soup.find_all("blockquote", attrs={"class": "twitter-tweet"})
    embed_tweets = [re.sub('\s+pic\.twitter\..*\s?', ' ', item.find('p').text) for item in links]
    embed_tweet_ids = [int(re.sub('.*/status/(.*)\?.*', r'\g<1>', item.find_all('a')[-1]['href'])) for item in links]
    query_params = {'date_since': f'{date - 2}-01-01',
                    'date_to': '',
                    'lang': SOURCE_LANG[source],
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}
    filename = f'{source}_tweets_embed.csv'
    for i, (q, ix) in enumerate(zip(embed_tweets, embed_tweet_ids)):
        print(f'\t{i} --> {q} : {ix}')
    # Seacher().tweet_lookup(embed_tweet_ids, query_params, filename)
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
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}
    filename = f'{source}_tweets_quotes.csv'
    for i, q in enumerate(quotations):
        print(f'\t{i} --> {q}')
    # multiple_search(quotations, query_params, rh_id, filename)


def multiple_search(queries, query_params, rh_id, filename):
    searcher = Searcher()
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
    tweets = pd.read_csv(os.path.join(DATA_PATH, filename))
    # filename = f'{fact_checker}_tweets.csv'
    # print(f'Current size {tweets.shape[0]}')
    # tweets.to_csv(os.path.join(DATA_PATH, filename), mode='w', index=False, quoting=csv.QUOTE_ALL)
    ixs_interest = np.bitwise_or(tweets.reply_count > 0, tweets.conversation_id != tweets.tweet_id)
    expand_ids = tweets[ixs_interest][['conversation_id', 'rh_id']].drop_duplicates()

    print(f'\033[94m Expanding {expand_ids.shape[0]} conversations for {fact_checker} fact checker...\033[0m')

    # 'start_time' must be on or after 2006-03-21T00:00Z
    query_params = {'lang': SOURCE_LANG[fact_checker],
                    'date_since': f'2006-03-21',
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}
    searcher = Searcher()
    for _, row in expand_ids.iterrows():
        print(f'\033[94m Expanding {row.conversation_id} corresponding to {row.rh_id}...\033[0m')
        query_params['conversation_id'] = row.conversation_id
        searcher.run_query(query_params, filename, initial_header=False, rh_id=row.rh_id)
        while searcher.is_running:
            pass
        # break
        time.sleep(searcher.sleep_time)

    # Deduplicate retrieved tweets
    tweets = pd.read_csv(os.path.join(DATA_PATH, filename))
    tweets.drop_duplicates(subset=['tweet_id'], inplace=True)
    tweets.to_csv(os.path.join(DATA_PATH, filename), mode='w', index=False, quoting=csv.QUOTE_ALL)
