import re
import json
import unidecode


def translate_emojis(posts, lang='es'):
    with open('./data/simple_emojis.json', 'r') as f:
        simple_emojis = json.load(f)
    with open('./data/complex_emojis.json', 'r') as f:
        complex_emojis = json.load(f)

    # print('##### Replacing simple emojis...')
    pattern = '|'.join(sorted(re.escape(k) for k in simple_emojis))
    posts = posts.apply(lambda t: re.sub(pattern,
                                         lambda m: simple_emojis.get(m.group(0).upper()).get(lang),
                                         t,
                                         flags=re.IGNORECASE))

    # print('##### Replacing complex emojis...')
    pattern = '|'.join(sorted(re.escape(k) for k in complex_emojis))
    return posts.apply(lambda t: re.sub(pattern,
                                        lambda m: complex_emojis.get(m.group(0).upper()).get(lang),
                                        t,
                                        flags=re.IGNORECASE))


def normalize_laughs(posts):
    # print('##### Normalizing laughs...')
    return posts.apply(lambda t: re.sub('[jha]{5,}', 'jajaja', t))


def url_masking(posts, drop=False):
    # print('##### Masking URLs...')
    out_str = 'URL' if not drop else ''
    url_regex = '([…\-—]\s)?(http|ftp|https)://([\w_-]+(?:(?:\.[\w_-]+)+))' \
                '([\w.,@?^=%&:/~+#-]*[\w@?^=%&/~+#-])?'  # \u2026\u002d\u2014
    return posts.apply(lambda t: re.sub(url_regex, out_str, t))


def user_masking(posts):
    # print('##### Masking users...')
    return posts.apply(lambda t: re.sub('@[\w]+', '', t))


def hashtag_masking(posts):
    # print('##### Masking hashtags...')
    return posts.apply(lambda t: re.sub('#[\w]+', 'HASHTAG', t))


def normalize_accents(posts):
    return posts.apply(lambda t: unidecode.unidecode(t))


def delete_emojis(posts):
    return posts.apply(lambda t: re.sub('[^a-zA-Z0-9àèéìùòçñ\s]', '', t))


def basic_text_normalization(data, drop=False):
    data = url_masking(data, drop)
    data = user_masking(data)
    data = normalize_accents(data)
    data = delete_emojis(data)
    data = data.apply(lambda t: re.sub('\s+', ' ', t).strip())
    return data
