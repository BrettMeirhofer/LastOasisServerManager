import requests
import threading
import json

log_folder = "C:/Program Files (x86)/Steam/steamapps/common/Last Oasis - Dedicated Server/Mist/Saved/Logs/"
URL = "https://discord.com/api/webhooks/1233164999178981456/sNNzdaM9oGp7R1rb1o1u2amaxgzR-OiznzohVukd_U6zrouaFDIRJd7BTbYfuPj3nW9I"



def send_discord_message(webhook_url, message, color):
    data = {
        "embeds": [
            {
                "description": message,
                "color": color  # Blue color
            }
        ]
    }

    # Set the headers for the HTTP request
    headers = {
        "Content-Type": "application/json"
    }

    # Send the POST request to the Discord webhook URL
    response = requests.post(webhook_url, headers=headers, data=json.dumps(data))

    if response.status_code == 204:
        print("Message sent successfully!")
    else:
        print(f"Failed to send message, status code: {response.status_code}")


def process_chat_message(line):
    # Check if the line starts with "chat message from"
    if "Chat message from" in line:
        parts = line.split()
        # Ensure there are enough parts in the message
        if len(parts) > 4:
            # Print the second part after the initial trigger phrase
            message = ' '.join(parts[4:])
            send_discord_message(URL, message, 3447003)
    elif "Join succeeded" in line:
        parts = line.split()
        # Ensure there are enough parts in the message
        if len(parts) > 3:
            # Print the second part after the initial trigger phrase
            message = ' '.join(parts[3:])
            send_discord_message(URL, "{} Joined the server".format(message), 65280)

    elif "LogPersistence: tile_name:" in line:
        parts = line.split()
        # Ensure there are enough parts in the message
        if len(parts) > 2:
            # Print the second part after the initial trigger phrase
            message = ' '.join(parts[2:])
            send_discord_message(URL, "{} Tile is ready to join".format(message), 65280)

    elif "killed" in line and "LogGame" in line:
        parts = line.split()
        # Ensure there are enough parts in the message
        if len(parts) > 1:
            # Print the second part after the initial trigger phrase
            message = ' '.join(parts[1:])
            send_discord_message(URL, "{}".format(message), 16776960)


files = []
logs = ["Mist.log", "Mist_2.log", "Mist_3.log"]
end = []

for i in range(3):
    try:
        files.append(open(log_folder + logs[i], 'r'))
    except FileNotFoundError:
        print("Not found")

while True:
    for i in files:
        current_position = i.tell()
        new = i.readline()
        if new:
            print(new.strip())
            process_chat_message(new.strip())