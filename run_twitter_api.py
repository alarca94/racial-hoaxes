import json
import os

from utils.search import Searcher


def run():
    query_file = 'before_query.json'
    save_to_file = f'tweets_{query_file[:-5]}.csv'

    with open(os.path.join('./query_files/', query_file), 'r') as f:
        query_params = json.load(f)
    query_params['max_results'] = 10
    query_params['max_tweets'] = 10

    searcher = Searcher()
    searcher.run_query(query_params, save_to_file)
