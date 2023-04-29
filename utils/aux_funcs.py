import dateutil.parser

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
    file = 'migracion.maldita_tweets.csv'
    data = read_tweets(file)

    conv_size = data.groupby('conversation_id').size()
    unexpanded_data = read_tweets('migracion.maldita_tweets_unexpanded.csv')
    mapper = unexpanded_data.drop_duplicates(subset='conversation_id')[['conversation_id', 'rh_id']]
    mapper = mapper.set_index('conversation_id').rh_id
    data.rh_id = data.conversation_id.map(mapper)
    data.to_csv(os.path.join(DATA_PATH, file), mode='w', index=False, quoting=csv.QUOTE_ALL)
    exit()
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
    '''
    Function to clean the data by filtering out those tweets that do not contain the racial target within their text
    '''
    fact_checker = 'migracion.maldita'

    rh_filename = 'full_version.csv'
    rh_data = pd.read_csv(os.path.join(QUERY_PATH, rh_filename))

    force_target_in_text(rh_data, fact_checker)


def run_query():
    '''
    Function to run a specific query using the Twitter API
    '''
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


def normalize_ids():
    '''
    The conversation, tweet and author ids need to be read as str rather than float. Floating points imply a rounding
    operation on the ids and messes up the identifiers.
    '''
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
    '''
    In case the tweet_id is known a priori, this functions implements the corresponding tweets lookup.
    '''
    Searcher(max_tweets=10).tweet_lookup(['1125295472908886016'], 'test.csv')


def conversation_search():
    '''
    Function to search for specific conversation_ids
    '''
    query_params = {'lang': 'es',
                    'date_since': f'2006-03-21',
                    'max_tweets': MAX_TWEETS,
                    'max_results': min(500, MAX_TWEETS)}
    filename = 'conversation_test.csv'
    if os.path.isfile(os.path.join(DATA_PATH, filename)):
        os.remove(os.path.join(DATA_PATH, filename))
    conversation_ids = [929343192272637952]
    searcher = Searcher()
    for id in conversation_ids:
        print(f'\033[94m Searching conversation {id}...\033[0m')
        query_params['conversation_id'] = id
        searcher.run_query(query_params, filename, initial_header=True, rh_id=None)
        while searcher.is_running:
            pass
        time.sleep(searcher.sleep_time)


def first_tweets_retrieval(filename):
    '''
    Function to do a tweet lookup using Twitter API in search of the root tweets that are missing from several
    conversations (the tweet_id of the root tweet is the same as the conversation_id).
    :param filename: .csv file that contains the Twitter downloaded conversations with missing root tweets.
    '''
    searcher = Searcher(max_tweets=MAX_TWEETS)
    tweets = read_tweets(filename)
    tweets.drop_duplicates(subset=['tweet_id'], inplace=True)

    # Apparently, Twitter API search by conversation_id does not retrieve the first tweet in multiple cases
    lookup_ids = tweets.groupby('conversation_id').apply(lambda s: not any(pd.isna(s.in_reply_to_tweet_id)))
    lookup_ids = lookup_ids[lookup_ids].index.tolist()
    print(f'Looking for {len(lookup_ids)} initial comments to add to the {tweets.shape[0]} existing tweets...')
    searcher.tweet_lookup(lookup_ids, filename)
    while searcher.is_running:
        pass


def get_subset():
    '''
    Get subset of tweets belonging to excessively big conversations (> 1000 tweets) to manually analyze it.
    Preliminary analysis indicate the existence of abundant noise in such large conversations.
    '''
    pd.set_option('display.max_colwidth', None)

    newtral_filename = 'newtral_tweets.csv'
    maldita_filename = 'migracion.maldita_tweets.csv'

    for filename in [newtral_filename, maldita_filename]:
        fact_checker = filename.split('_')[0]
        tweets = read_tweets(filename)
        conv_sizes = tweets.groupby('conversation_id').size()
        conv_sizes.sort_values(inplace=True)
        accu_sizes = conv_sizes.cumsum()
        keep_conv_ixs = accu_sizes.index.tolist()[:np.argwhere(accu_sizes.values > 1000)[1, 0]]

        print(fact_checker.upper())
        print(f'\tDataset with {tweets.shape[0]} tweets and {len(conv_sizes)} conversations')
        # print(f'\tStarting tweets have been retrieved for {sum(starting_conditions)} conversations')

        # filtered_convs = conv_sizes[conv_sizes <= median].index.tolist()
        tweets = tweets[tweets.conversation_id.isin(keep_conv_ixs)]
        print(f'\tKeeping {tweets.shape[0]} tweets out of {len(keep_conv_ixs)} conversations as a subset')

        tweets.sort_values(by=['conversation_id', 'date'], inplace=True)
        tweets.to_csv(os.path.join(DATA_PATH, fact_checker + '_subset.csv'),
                      mode='w', index=False, quoting=csv.QUOTE_ALL)


def test():
    filename = 'newtral_tweets.csv'
    tweets = read_tweets(filename)
    tweets = clean_duplicates(tweets)

    # Save to file with the new data
    tweets.to_csv(os.path.join(DATA_PATH, filename), mode='w', index=False, quoting=csv.QUOTE_ALL)