import nltk
from urllib import request, error
from bs4 import BeautifulSoup
from nltk import word_tokenize, sent_tokenize, pos_tag
import re
import cities_data
from collections import Counter
import json
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from urllib.parse import urlparse

# Download necessary NLTK corpora and models
nltk.download('punkt_tab')
nltk.download('punkt')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('averaged_perceptron_tagger_eng')
nltk.download('maxent_ne_chunker_tab')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('treebank')
nltk.download('gazetteers')

# Function to extract raw text from a URL
def extract_raw_text(url):
    try:
        # Fetch HTML content from the URL and parse it to get raw text
        html = request.urlopen(url).read().decode('utf8')
        raw = BeautifulSoup(html, 'html.parser').get_text(separator=' ', strip=True)
        # Remove unwanted terms from raw text
        raw = re.sub(r'\behrenamt\b', '', raw, flags=re.IGNORECASE)
        return raw
    except error.HTTPError:
        print("This link is not working:", url)
        return None
    except error.URLError:
        print("Failed to reach the server:", url)
        return None

# Loop through each page link and extract information
def loop_through_pages(links: list[str], output_file: str):
    data_collected = []
    for link in links:
        raw_text = extract_raw_text(link)  # Extract raw text from the link
        info = extract_info(raw_text, link)  # Extract structured info from the text
        data_collected.append(info)

    # Save collected data to a JSON file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data_collected, f, ensure_ascii=False, indent=4)
    print(f"Data saved to {output_file}")

# Data containing cities and postal codes for matching
cities_df = cities_data.cities_df

# Function to extract a description related to the organization
def extract_description(text, org_name):
    org_tokens = word_tokenize(org_name.lower())  # Tokenize and normalize the organization name
    sentences = sent_tokenize(text)  # Split the text into sentences
    
    # Filter sentences based on length
    filtered = [s for s in sentences if 5 <= len(word_tokenize(s)) <= 30]
    
    matching_sentences = []
    # Select sentences containing organization tokens
    for sentence in filtered:
        lowered = sentence.lower()
        if any(word in lowered for word in org_tokens):
            matching_sentences.append(sentence)
            if len(matching_sentences) == 3:  # Limit to first 3 matches
                break

    return matching_sentences if matching_sentences else ["No relevant description found."]

# Function to extract relevant keywords (nouns/adjectives)
def extract_interest_keywords(text):
    stop_words = set(stopwords.words('english') + stopwords.words('german'))  # Define stop words for filtering
    tokens = word_tokenize(text.lower())  # Tokenize the text
    tagged = pos_tag(tokens)  # Perform part-of-speech tagging

    # Extract nouns and adjectives while excluding stopwords
    interest_words = [word for word, tag in tagged if tag in ('NN', 'NNS') and word not in stop_words]
    word_counts = Counter(interest_words)  # Count word frequency
    
    # Return top 5 most common words
    most_common = word_counts.most_common(5)
    return [word for word, _ in most_common] if most_common else None

# Function to extract the most common keywords in the text (lemmatized and stopword-free)
def extract_most_common_keyword(text):
    tokens = word_tokenize(text.lower())  # Tokenize and lowercase text
    stop_words = set(stopwords.words('german') + stopwords.words('english'))  # Exclude stopwords
    tokens = [t for t in tokens if t.isalpha() and t not in stop_words]  # Filter out non-alphabetic and stopwords

    # Replace German umlauts with their respective letters
    tokens = [t.replace('ü', 'ue').replace('ö', 'oe').replace('ä', 'ae').replace('ß', 'ss') for t in tokens]
    
    # Lemmatize tokens (reduce words to their base forms)
    lemmatizer = WordNetLemmatizer()
    lemmatized = [lemmatizer.lemmatize(token) for token in tokens]
    
    # Count the most frequent words
    counter = Counter(lemmatized)
    most_common = counter.most_common(20)
    
    return [word for word, _ in most_common] if most_common else None

# Function to parse URL and extract meaningful parts (path and domain)
def get_url_parts(url):
    parsed = urlparse(url)
    slug = parsed.path.lower()  # Extract path part of the URL
    domain = parsed.netloc.lower()  # Extract domain part of the URL
    combined = slug + " " + domain  # Combine both parts
    combined = re.sub(r'[^a-z0-9\-]', ' ', combined).replace('-', ' ')  # Clean and normalize the string
    words = combined.split()  # Split into individual words
    return words

# Function to compare organization names in text to URL parts
def compare_orgs_to_url(text, url):
    org_names = extract_most_common_keyword(text)  # Extract common keywords from text
    url_parts = get_url_parts(url)  # Extract parts from the URL
    name = []
    for part in url_parts:
        if part in org_names and part not in  ['linz', 'treffpunkt', 'organisation']:  # Filter out irrelevant terms
            name.append(part)
    return ' '.join(name)  # Return matched organization name

# Function to extract structured information (e.g., organization name, contact info)
def extract_info(text, link):
    cleaned_text = re.sub(r'[\s\-\/()]', '', text)  # Clean text for phone extraction

    # Extract org name by matching keywords in text with parts of the URL
    organization_name = compare_orgs_to_url(text, link)
    
    # Get relevant description based on organization name
    description = extract_description(text, organization_name)
    
    # Extract emails (excluding .gv.at addresses)
    email = set(re.findall(r"\b\S+@(?:(?![\w.-]*\.gv\.at)\w[\w.-]*\.at)\b", text))
    
    # Extract phone numbers (Austrian format)
    phone = set(re.findall(r'(?:\+43)\d{9,}', cleaned_text))

    # Extract homepage URLs (excluding .gv.at)
    homepage = set(re.findall(r'(?<![a-zA-Z0-9])(?:www\.)?[a-zA-Z0-9-]+\.(?!gv\.)at(?!\S)', text))
    
    # Extract street addresses with Austrian suffixes (e.g., Straße, Weg)
    street = set(re.findall(r'\b[A-ZÄÖÜa-zäöüß\-]+(?:\s)?(?:straße|strasse|gasse|asse|aße|weg)\s\d+[a-zA-Z]?\b', text))

    
    # Find matching cities based on known city names
    cities = cities_df[cities_df['Name'].apply(lambda c: re.search(rf'\b{re.escape(c)}\b', text) is not None)]['Name'].to_list()

    # Extract postal codes (4-digit)
    postal_codes = re.findall(r'\b\d{4}\b', text)

    # Extract keywords of interest (e.g., sport, elderly)
    field = extract_interest_keywords(text)

    if len(cities) == 0:
        print("No city found", link)
        city_postal_code = ""
    else:
        for city in cities:
            # Match city to postal code
            prefix = cities_df[cities_df['Name'].str.lower() == city.lower()]["Postal prefix"].to_list()
            postal_code = [code for code in postal_codes if code[0] in prefix[0]]
            if len(postal_code) == 0:
                print("No matching postal code", link)
                city_postal_code = ""
            else:
                city_postal_code = str(postal_code[0]) + " " + city

    return {
        "url": link,
        "organization name": organization_name,
        'description': description,
        'field': list(field),
        "email": list(email),
        "phone": list(phone),
        "homepage": list(homepage),
        "city_and_postal_code": city_postal_code,
        "street": list(street),
    }

pages_list = [
    "http://caritas-kaernten.at/",
    "https://contraste.at/",
    "https://www.kardinal-koenig-haus.at/",  #no city found
    "http://www.allianz-fuer-kinder.at/",
    "http://www.aktivertierschutz.at/",
    "https://www.dioezese-linz.at/biblio/home&ts=1746030901920",
    "https://www.alpenverein.at/jugend-tirol",  #no city found
    "https://onlinemarktl.at/lieferantenprofile",
    "https://www.b3-netzwerk.at/",# no city found
    "https://verein-wohnplattform.at/ova_por/auf-gute-nachbarschaft/", #no matching postal code
    "https://treffpunkt-ehrenamt.at/organisation/checkpoint-verein-jugendzentrum-gmunden/",
    "https://treffpunkt-ehrenamt.at/organisation/admira-linz/",
    "https://treffpunkt-ehrenamt.at/organisation/aktion-kritischer-schueler_innen-aks-oberoesterreich/",
    "https://treffpunkt-ehrenamt.at/organisation/aktivtreff-pro-mente-ooe/",
    "https://treffpunkt-ehrenamt.at/organisation/allg-turnverein-1889-voecklabruck/",
    "https://treffpunkt-ehrenamt.at/organisation/allianz-fuer-kinder-besuchsdienst-gastfamilien-fuer-kranke-kinder-aus-krisengebieten/",
    "https://treffpunkt-ehrenamt.at/organisation/allianz-fuer-kinder-in-kriegs-und-krisengebieten/",
    "https://treffpunkt-ehrenamt.at/organisation/alpenverein/",
    "https://treffpunkt-ehrenamt.at/organisation/alpenverein-altenberg/",
    "https://treffpunkt-ehrenamt.at/organisation/alpenverein-linz/"
]


loop_through_pages(pages_list, 'data')

