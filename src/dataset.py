import re
import json
import time
import typer
import requests
import numpy as np
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from loguru import logger
from bs4 import BeautifulSoup
from typing import (
    List,
    Optional,
    Union,
)
from urllib.parse import urljoin

from src.config import (
    PROCESSED_DATA_DIR,
    RAW_DATA_DIR,
    INTERIM_DATA_DIR,
)

from src.data_utils import (
    races,
    professions,
    affiliations,
    big_affiliations,
    category_links,
    human_races,
)

app = typer.Typer()


def get_malazan_characters(
        url: str = "https://malazan.fandom.com/wiki/Malazan_Wiki:Dramatis_Personae_all_books"
) -> Optional[pd.DataFrame]:
    """
    Scrapes character information from the Malazan Wiki Dramatis Personae page.

    Args:
        url (str): URL of the Malazan Wiki Dramatis Personae page.

    Returns:
        pd.DataFrame: DataFrame containing character names and information.
                     Returns None if the request fails.

    DataFrame columns:
        - name: Character name
        - info: Character description and book references
    """
    try:
        # Get the webpage
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')

        # Initialize lists to store data
        names = []
        infos = []

        # Find all li elements that contain character information
        for li in soup.find_all('li'):
            a_tag = li.find('a')
            if a_tag and a_tag.get('title'):
                name = a_tag.text.strip()
                info = li.get_text().replace(name, '', 1).strip()
                if info.startswith(','):
                    info = info[1:].strip()

                # Remove book references using regex
                info = re.sub(r'\s*\([A-Z*/]+(?:\s*,\s*[A-Z*/]+)*\)\s*$', '', info)

                names.append(name)
                infos.append(info)

        # Create DataFrame
        df = pd.DataFrame({
            'name': names,
            'info': infos
        })

        # Clean the DataFrame
        df['info'] = df['info'].str.strip()
        df['info'] = df['info'].str.replace('---->', '', regex=False)
        df['info'] = df['info'].str.replace('->', '', regex=False)
        df = df[df['info'] != '']
        df = df.reset_index(drop=True)

        return df

    except requests.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def find_match(text: str, search_list: List) -> str | None:
    """finds matches for lists (with professions, titles, etc.) in character description field"""
    if not text or not search_list:
        return None

    # Remove special characters and convert to lowercase
    def clean_text(input_text):
        # Replace special characters with spaces
        cleaned = ''.join(char if char.isalnum() or char.isspace() else ' ' for char in input_text)
        # Convert to lowercase and normalize spaces
        return ' '.join(cleaned.lower().split())

    text_clean = clean_text(text)

    # Clean search terms similarly and create pairs of (original, cleaned)
    search_pairs = [(item, clean_text(item)) for item in search_list if item]

    # Sort by length (number of words) in descending order
    search_pairs.sort(key=lambda x: len(x[1].split()), reverse=True)

    # Look for matches, starting with multi-word terms
    for original, clean_item in search_pairs:
        words = clean_item.split()
        for i in range(len(text_clean.split()) - len(words) + 1):
            text_segment = ' '.join(text_clean.split()[i:i + len(words)])
            if text_segment == clean_item:
                return original

    return None


def get_character_info(url: str) -> dict:
    """
    Takes url-address from Malazan wiki and returns dictionary with a character parameters.
    :param url: character web-page from malazan-wiki. For example, `https://malazan.fandom.com/wiki/Anomander_Rake`.
    :return: dictionary with the following keys: `name`, `affiliation`, `race`, `gender`, `warrens`.
    """
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    # Extract character name
    character_info = {'name': soup.find('h1', class_='page-header__title').text.strip()}

    # Helper function to extract list data
    def extract_list_data(data_source: str) -> str:
        data_div = soup.find('div', {'data-source': data_source})
        if data_div:
            data_value = data_div.find('div', class_='pi-data-value')
            if data_value:
                links = data_value.find_all('a')
                if links:
                    return [link.text.strip() for link in links]
                else:
                    return [data_value.text.strip()]
        return []

    # Extract affiliation, race, gender, and warrens
    character_info['affiliation'] = extract_list_data('affiliation')
    character_info['race'] = extract_list_data('race')
    character_info['gender'] = extract_list_data('gender')
    character_info['warrens'] = extract_list_data('warren')

    return character_info


def normalize_name(name):
    # Remove special characters and convert to lowercase
    return re.sub(r'\W+', '', name).lower()


def clean_name(name):
    if pd.isna(name):  # Handle NaN values
        return name

    # Convert to lowercase
    name = str(name).lower()

    # Remove brackets and their contents
    name = re.sub(r'\([^)]*\)', '', name)
    name = re.sub(r'\[[^\]]*\]', '', name)
    name = re.sub(r'\{[^}]*\}', '', name)

    # Remove 'the' (make sure it's a word by itself)
    name = re.sub(r'\bthe\b', '', name)

    # Strip whitespace and remove multiple spaces
    name = ' '.join(name.split())

    return name


def get_malazan_characters_url(character_names, html_page_url):
    """Given the link to the malazan wiki page parse the links to the pages about the characters"""
    # Fetch the HTML content of the page
    response = requests.get(html_page_url)
    response.raise_for_status()  # Ensure we notice bad responses
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract all links from the page
    links = soup.find_all('a', href=True)

    # Normalize character names
    normalized_character_names = [normalize_name(name) for name in character_names]

    # Dictionary to store the matched URLs
    matched_urls = []

    # Iterate over all links and check for matches
    for link in links:
        href = link['href']
        text = link.get_text()
        normalized_text = normalize_name(text)

        # Check if the link is a relative URL and points to a character page
        if href.startswith('/wiki/') and not any(
                sub in href for sub in ['Special:', 'Category:', 'File:', 'Help:', 'Template:', 'User:', 'Talk:']):
            # Check if the normalized link text matches any of the normalized character names
            if any(normalized_text in normalized_name for normalized_name in normalized_character_names):
                full_url = f"https://malazan.fandom.com{href}"
                matched_urls.append(full_url)

    return matched_urls


@app.command()
def get_raw_data(raw_folder: Path = RAW_DATA_DIR):
    """Fetching raw data to enrich existing data"""
    logger.info("Getting Malazan Dramatis Personae List")
    characters_info = get_malazan_characters()
    character_names = characters_info['name'].tolist()

    try:
        with open(raw_folder / "characters_urls.txt", "r") as file:
            logger.info("File with characters_urls found; loading")
            # Read all lines into a list
            characters_urls = file.readlines()
    except FileNotFoundError:
        logger.info("File with characters_urls not found")
        characters_urls = []
        for category_link in tqdm(category_links):
            category_characters_links = get_malazan_characters_url(
                character_names,
                html_page_url=category_link
            )
            characters_urls.extend(category_characters_links)

        characters_urls = list(set(characters_urls))

        # save links
        with open(raw_folder / "characters_urls.txt", "w") as file:
            # Iterate through the list and write each item to the file
            for item in characters_urls:
                file.write(f"{item}\n")

    logger.info("Get Characters Data")
    character_page_wiki_info = []
    for character_url in tqdm(characters_urls):
        character_page_wiki_info.append(get_character_info(str(character_url).strip()))
        time.sleep(1)

    # save character info
    with open(raw_folder / "characters_wiki_info.txt", "w") as file:
        # Iterate through the list and write each item to the file
        for item in character_page_wiki_info:
            file.write(f"{item}\n")

    with open(raw_folder / "characters_wiki_info.json", 'w') as json_file:
        json.dump(character_page_wiki_info, json_file)


def get_edges_data(
        raw_folder: Path = RAW_DATA_DIR,
        processed_folder: Path = INTERIM_DATA_DIR,
) -> None:
    edges_data = (
        pd.read_csv(raw_folder / "malazan_network_data.csv")
        .assign(total_co_occurance=lambda df_: df_.groupby(['name1', 'name2'])['chapter'].transform('count'))
        # .assign(book_co_occurance=lambda df_: df_.groupby(['name1', 'name2', 'book'])['chapter'].transform('count'))
        # .assign(book_chapter_co_occurance=lambda df_: df_.groupby(['name1', 'name2', 'book', 'chapter'])['total_co_occurance'].transform('count'))
        .assign(books_appearance=lambda df_: df_.groupby(['name1', 'name2'])['book'].transform('nunique'))
        .assign(book_chapter=lambda df_: df_['book'] + df_['chapter'])
        .assign(
            co_occurance_chapters_cnt=lambda df_: df_.groupby(['name1', 'name2'])['book_chapter'].transform('nunique'))
        # .query("total_co_occurance > 10")  # filter out connections with few interactions over all books
        .drop(columns=['book', 'chapter'])
        .query("name1 not in ['Maybe', 'Hood'] and name2 not in ['Maybe', 'Hood']")
        .drop_duplicates(subset=['name1', 'name2'], ignore_index=True)
        # todo: add additional data on the type of connection
        # todo: add 10th book info
    )

    edges_data.to_csv(processed_folder / "edges_data.csv", index=False)


def get_nodes_data(
        raw_folder: Path = RAW_DATA_DIR,
        processed_folder: Path = INTERIM_DATA_DIR,
) -> None:
    logger.info("Fetching and Processing Nodes Data")
    nodes_data = (
        pd.read_csv(raw_folder / "malazan_pov_data.csv")
        .assign(norm_name=lambda df_: df_['name'].apply(clean_name))
        .merge(
            (
                pd.read_json(RAW_DATA_DIR / 'characters_wiki_info.json')
                .assign(norm_name=lambda df_: df_['name'].apply(clean_name))
                .drop(columns=['name'])
            ),
            left_on='norm_name', right_on='norm_name', how='left',
        )
        # Dramatis Personae Data
        .merge(
            (
                get_malazan_characters()
                .assign(norm_name=lambda df_: df_['name'].apply(clean_name))
                .assign(dp_race=lambda df_: df_['info'].apply(lambda x: find_match(x, races)))
                .assign(profession=lambda df_: df_['info'].apply(lambda x: find_match(x, professions)))
                .assign(dp_affiliation=lambda df_: df_['info'].apply(lambda x: find_match(x, affiliations)))
            )
        )
        # replace empty Lists [] with NaNs
        .assign(**{col: lambda df_, col=col: df_[col].mask(df_[col].apply(lambda x: x == []), None)
                   for col in ['affiliation', 'race', 'gender', 'warrens']})

        # create the main columns
        .assign(total_words_count=lambda df_: df_.groupby(['name'])['word_count'].transform('sum'))
        .assign(books_appearance=lambda df_: df_.groupby(['name'])['book'].transform('nunique'))
        .assign(first_book_appearance=lambda df_: df_.groupby(['name'])['book'].transform('min'))
        .assign(last_book_appearance=lambda df_: df_.groupby(['name'])['book'].transform('max'))
        .assign(pov_words_per_book_with_pov=lambda df_: np.round(df_['total_words_count'] / df_['books_appearance']))
        .assign(race=lambda df_: df_['race'].combine_first(df_['dp_race']))
        .assign(affiliation=lambda df_: df_['affiliation'].combine_first(df_['dp_affiliation']))

        # hard-coding
        .assign(affiliation_first=lambda df_: df_['affiliation'].apply(
            lambda row: 'Malazan Empire' if (
                row in ['14th Army', '7th Army', 'Bridgeburners', 'Malaz 14th Army', 'Malazan Army'] if isinstance(row,
                                                                                                                   str)
                else isinstance(row, List) and any(
                    x in ['14th Army', '7th Army', 'Bridgeburners', 'Malaz 14th Army', 'Malazan Army'] for x in row))
            else 'Army of the Apocalypse' if (
                row in ['Army of the Apocalypse', 'Army of the Whirlwind', 'Whirlwind'] if isinstance(row, str)
                else isinstance(row, List) and any(
                    x in ['Army of the Apocalypse', 'Army of the Whirlwind', 'Whirlwind'] for x in row))
            else "Kingdom of Lether" if (
                row in ['Kingdom of Lether', 'Lether', 'Letherii Empire'] if isinstance(row, str)
                else isinstance(row, List) and any(
                    x in ['Kingdom of Lether', 'Lether', 'Letherii Empire'] for x in row))
            else row if isinstance(row, str) and row in big_affiliations
            else next((x for x in row if x in big_affiliations), None) if isinstance(row, List)
            else None
        )
                )
        .assign(affiliation_second=lambda df_: df_['affiliation'].apply(
            lambda row: row if isinstance(row, str) and row not in ['Malazan Army', 'Army of the Apocalypse',
                                                                    'Kingdom of Lether']
                               + big_affiliations
            # else isinstance(row, List) and any(x not in ['Malazan Army', 'Army of the Apocalypse', 'Kingdom of Lether']
            #                                    + big_affiliations for x in row))
            else next((x for x in row if x not in big_affiliations), None) if isinstance(row, List)
            else None
        )
                )
        .assign(affiliation_second=lambda df_: df_['affiliation_second'].combine_first(df_['affiliation_first']))
        .assign(race_first=lambda df_: df_['race'].apply(
            lambda row: 'Human' if isinstance(row, str) and row in human_races + ['Human']
            else next((x for x in row if x in human_races + ['Human']), row[0]) if isinstance(row, List)
            else row if isinstance(row, str)
            else None
        )
                )
        # .assign(race_second=)
        .assign(gender=lambda df_: df_['gender'].apply(lambda row: row[0] if isinstance(row, List) else None))
        # .assign(warren_first=) # todo: the most frequent ones first

        # final cleaning steps
        .drop(columns=['order', 'book', 'chapter', 'word_count', 'dp_race', 'dp_affiliation',
                       'affiliation', 'race', 'warrens'])
        .astype({"pov_words_per_book_with_pov": "int"})
        .query("name not in ['Maybe', 'Hood']")
        .drop_duplicates(subset=['name'], ignore_index=True)
        .rename(columns={"name": "id"})
    )
    nodes_data.to_csv(processed_folder / "nodes_data.csv", index=False)
    logger.info(f"Saved Nodes Data to {processed_folder} folder", index=False)


@app.command()
def main(
        raw_folder: Path = RAW_DATA_DIR,
        processed_folder: Path = INTERIM_DATA_DIR,
):
    # get_raw_data(raw_folder=raw_folder)
    get_edges_data(processed_folder=processed_folder)
    get_nodes_data(processed_folder=processed_folder)


if __name__ == "__main__":
    app()
