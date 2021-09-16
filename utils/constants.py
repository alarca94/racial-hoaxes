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

EXCLUDE_TWEET_IDS = {
    'migracion.maldita': ['1323096875784953857', '1275750804713062402', '1166228309623148544', '1202137423741964288',
                          '1344048821001723904', '1253308302802501632', '1109053630466928641', '1081480259994873856',
                          '1272976899300634632']
}

EXCLUDE_CONV_IDS = {
    'newtral': ['929343192272637952']
}
