import json
import requests
from bs4 import BeautifulSoup


def read_json(json_file):
    """Read the JSON file and return a dictionary of mod ids and last update times."""
    with open(json_file, 'r') as file:
        return json.load(file)


def fetch_mod_update_time(mod_id):
    """Fetch the mod's last update time from Steam Workshop using the mod's ID."""
    print("Started steam retrieval for {}".format(mod_id))
    url = f"https://steamcommunity.com/sharedfiles/filedetails/?id={mod_id}"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # You need to find the correct selector for the update date; this is just a placeholder
    update_tag = soup.find('div', class_='detailsStatsContainerRight')  # Example; likely needs adjustment
    return update_tag.text.strip() if update_tag else None


def update_mods_info(mods_info, mod_ids):
    """Check and update mods info based on current data from Steam Workshop."""
    out_of_date = []

    for mod_id in mod_ids:
        current_time = fetch_mod_update_time(mod_id)
        if mod_id in mods_info:
            if mods_info[mod_id] != current_time:
                print("SavedMod {} CurrentMod {}".format(mods_info[mod_id], current_time))
                out_of_date.append(mod_id)
                mods_info[mod_id] = current_time  # Update the recorded last update time
        else:
            mods_info[mod_id] = current_time  # Add new mod to the dictionary

    return out_of_date, mods_info


def add_new_mod_ids(mods_info, new_mod_ids):
    """Add new mod IDs from a comma-delimited string if they aren't already in the mods info."""
    for mod_id in new_mod_ids:
        if mod_id.strip() not in mods_info:
            mods_info[mod_id.strip()] = None  # Initialize with None, or fetch and set the current update time