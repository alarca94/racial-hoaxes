from utils.aux_funcs import *


def run_automatic_downloader():
    '''
    After analysing the hoax verification websites/sources, the automatic downloader runs a certain strategy depending
    on the specific hoax article. The steps are the following ones:
    1. Search the tweets based on the selected strategies.
    2. Once the Twitter search has been performed, tweets downloaded according to migracion.maldita's article need to be
    cleansed (by forcing the annotated racial hoax target to be in the text).
    3. For those conversations missing the root tweet, perform a targetted tweet lookup.
    4. Given the amount of noise perceived from manual analysis, the conversations are reduced to those tweets containing
    the manually annotated racial target and both, previous and posterior tweets within the conversation (neignbors)
    '''

    download_from_sources = ['bufale', 'butac', 'newtral', 'migracion.maldita']  # Possible values: ['bufale', 'butac', 'newtral', 'migracion.maldita']
    racial_hoaxes = pd.read_csv('./query_files/full_version.csv')
    visited_urls = []
    for ix, row in racial_hoaxes.iterrows():
        fact_check_url = row.Source.replace(' ', '')
        if fact_check_url not in visited_urls:
            visited_urls.append(fact_check_url)

            fact_checker = re.sub('\s*(https://)?(www.)?([\w\.]+)\..*', '\g<3>', fact_check_url)
            fact_title = row.Title
            fact_check_date = row.Date
            rh_id = row['RH ID']

            if fact_checker in download_from_sources:
                print(f'\033[94m {rh_id} \u27f6 {fact_checker} \u27f6 {fact_title}\033[0m')

                if fact_checker == 'bufale':
                    run_title_strategy(fact_title, int(fact_check_date), fact_checker, rh_id)
                elif fact_checker == 'butac':
                    run_title_strategy(fact_title, int(fact_check_date), fact_checker, rh_id, keep_stopwords=False)
                elif fact_checker in ['newtral', 'migracion.maldita']:  # Possible values: ['newtral', 'migracion.maldita']
                    html = requests.get(fact_check_url)
                    if not html.ok:
                        print(f'\033[91m URL {fact_check_url} Request failed with status code {html.status_code}\033[0m')
                        continue
                    print('Searching by embedded tweets...')
                    run_url_tweets_strategy(fact_check_url, fact_checker, rh_id)
                    print('Searching by quoted text...')
                    run_url_quotes_strategy(fact_check_url, int(fact_check_date[-4:]), fact_checker, rh_id)

    noisy_sources = ['migracion.maldita']  # Possible values: ['migracion.maldita']
    for fact_checker in noisy_sources:
        print(f'De-noising {fact_checker} data...')
        force_target_in_text(racial_hoaxes, fact_checker)

    expand_from_sources = ['bufale', 'butac', 'newtral', 'migracion.maldita']  # Possible values: ['bufale', 'butac', 'newtral', 'migracion.maldita']
    for fact_checker in expand_from_sources:
        expand_conversations(fact_checker)

    reduce_conv_from_sources = ['newtral', 'migracion.maldita']  # Possible values: ['newtral', 'migracion.maldita']
    for fact_checker in reduce_conv_from_sources:
        reduce_conversations(racial_hoaxes, fact_checker)


if __name__ == '__main__':
    run_automatic_downloader()

    print('Finished...')
