AVAILABLE_LANGS = {'Spanish': 'es', 'English': 'en', 'French': 'fr', 'Arabic': 'ar', 'Japanese': 'ja',
                   'German': 'de', 'Italian': 'it', 'Indonesian': 'id', 'Portuguese': 'pt', 'Korean': 'ko',
                   'Turkish': 'tr', 'Russian': 'ru', 'Dutch': 'nl', 'Filipino': 'fil', 'Malay': 'msa',
                   'Traditional Chinese': 'zh-tw', 'Simplified Chinese': 'zh-cn', 'Hindi': 'hi',
                   'Norwegian': 'no', 'Swedish': 'sv', 'Finnish': 'fi', 'Danish': 'da', 'Polish': 'pl',
                   'Hungarian': 'hu', 'Farsi': 'fa', 'Hebrew': 'he', 'Urdu': 'ur', 'Thai': 'th',
                   'English UK': 'en-gb'}

DATA_PATH = './data'
QUERY_PATH = './query_files'
DOWNLOAD_FILE = 'downloaded_tweets.csv'
CLEAN_FILE = 'kept_tweets.csv'
ANNOTATE_FILE = 'labeled_tweets.csv'

SOURCE_LANG = {
    'bufale': 'it',
    'butac': 'it',
    'newtral': 'es',
    'migracion.maldita': 'es'
}

LANG_MAPPER = {
    'es': 'spanish',
    'it': 'italian'
}
