# Tool to download tweets using Twitter API 2.0

The main interest of the application is to download tweets related to Racial Hoaxes (RHs). Therefore, after analysing articles from a few spanish and italian sources, we provide a tool to download and clean tweets (and the whole conversation thread) based on a variety of strategies:

- Title strategy (w/o stopwords): match the RH verification article title to the tweet text.
- Embedded tweets: Tweet lookup of the embedded tweets in the RH verification article.
- Quote strategy: Quotes inside the RH verification article seems an interesting way to find matching tweets in Twitter.

The GUI part of the project is currently under construction, so no complex functionality is provided. If the current simple developed GUI is needed, please change the PeriodicTimer() to the QTimer() of the PyQt5 library in the utils/search.py field. Otherwise, run the main.py file for an automatic download with the previously explained strategies from the following RH verification sites: 'bufale', 'butac', 'newtral', 'migracion.maldita'. If only part of the automatic workflow is required for some of the sources, please modify the variables 'download_from_sources', 'noisy_sources', 'expand_from_sources' and/or 'reduce_conv_from_sources'.

If a specific query needs to be run, you can find as useful the methods run_query(), tweets_search() or conversation_search().

## Requirements:

```PyQt5==5.15.4
pandas==1.1.5
numpy==1.19.3
beautifulsoup4==4.8.2
newspaper3k==0.2.8
nltk==3.4.5
unidecode
```
