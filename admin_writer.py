import json
import time


def write_to_json(message):
    """Helper function to write a message to a JSON file."""
    with open('C:/Program Files (x86)/Steam/steamapps/common/Last Oasis - Dedicated Server/Mist/Content/admin.json', 'w') as file:
        json.dump({"Message": message}, file)


def write(message):
    write_to_json(message)
    time.sleep(11)
    write_to_json("")

def main():
    user_input = input("Enter your message: ")
    write(user_input)
    main()


if __name__ == "__main__":
    main()