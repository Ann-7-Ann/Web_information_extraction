import pandas as pd

url = "https://en.wikipedia.org/wiki/List_of_cities_and_towns_in_Austria"
state_postcode_map = {
        "Vienna": ['1'],
        "Lower Austria": ['2','3'],
        "Upper Austria": ['4'],
        "Salzburg": ['5'],
        "Tyrol": ['6'],
        "Vorarlberg": ['6'],
        "Burgenland": ['7'],
        "Styria": ['8'],
        "Carinthia": ['9'],
        "East Tyrol": ['9'],
    }

data = pd.read_html(url)
cities_df = data[0]
cities_df = cities_df[["Name", "Federal state"]]

cities_df['Postal prefix'] = cities_df['Federal state'].apply(lambda x: state_postcode_map.get(x, []))

print(cities_df)