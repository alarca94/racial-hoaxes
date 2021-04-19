import run_gui
import run_twitter_api
import json
import pandas as pd
import dateutil.parser


def prepare_response():
    with open('./documentation/output_example.json', 'r') as f:
        data = json.load(f)
        tweet_data = []
        for tweet in data['data']:
            (author_id, tweet_id, date, lang, text, hashtags, annotations, possibly_sensitive, like_count, quote_count,
             reply_count, retweet_count, urls) = run_twitter_api.extract_info(tweet)
            tweet_data.append(run_twitter_api.extract_info(tweet))
            print(f'AUTHOR ID: {author_id};\tTWEET ID: {tweet_id}; DATE: {date}; LANG: {lang}; TEXT: {text}; '
                  f'HASHTAGS: {hashtags}; ANNOTATIONS: {annotations}; POSSIBLY SENSITIVE: {possibly_sensitive}; '
                  f'LIKES: {like_count}; QUOTES: {quote_count}; REPLIES: {reply_count}; RETWEETS: {retweet_count}; '
                  f'URLS: {urls}')

        columns = ['author_id', 'tweet_id', 'date', 'lang', 'text', 'hashtags', 'annotations', 'possibly_sensitive',
                   'like_count', 'quote_count', 'reply_count', 'retweet_count', 'urls']
        tweet_data = pd.DataFrame(tweet_data, columns=columns)
        print(dateutil.parser.isoparse(date).isoformat('T') + 'Z')

    print(tweet_data)


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
    file = 'stereotypes_tweets.csv'
    data = pd.read_csv(os.path.join(data_path, file))


if __name__ == '__main__':
    run_gui.run()
    # visualize_data()

    print('Finished...')
