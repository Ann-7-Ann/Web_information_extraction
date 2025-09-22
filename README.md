# Web information extraction

This repository presents two approaches for the same task: scrapping and extracting structured information (like organization name, email, phone, city, postal code, description) of Austrian organizations.  


# Rule-based approach

The first approach is rule-based. It combines web scrapping (`urllib`, `BeautifulSoup`), text processing (`re`, `nltk`), linguistic analysis (tokenization, lemmatization, POS tagging, stopword removal), domain knowledge (Austrian postal codes & cities mapping).  
The outcome is saved in `data.json` file.


# Scrapy 

Second approach uses Scrapy to scrape the website and extract analogous information. It loops through `<p>` tags in the details section and captures corresponding labels and logo image URL.  
The outcome is saved in `site_1.json` file.
