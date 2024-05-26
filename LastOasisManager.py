import json
import signal
import subprocess
import time
import threading
import os
import requests
import shutil
import ctypes
import subprocess
import psutil
import time

import admin_writer
from mod_checker import add_new_mod_ids, read_json, update_mods_info

stop_events = []
processes = []
wait_restart_time = 0
config = {}
crash_total = 0

kernel32 = ctypes.WinDLL('kernel32', use_last_error=True)


def send_discord_message(webhook_url, message):
    print("Discord Message: {}".format(message))
    data = {"content": message}
    response = requests.post(webhook_url, json=data)

    return response.status_code


def run_process(path, stop_event):
    """ Run an executable and monitor it. """
    while not stop_event.is_set():
        print(f"Starting {path}")
        # ,
        process = subprocess.Popen(path, stdout=subprocess.DEVNULL, text=True, universal_newlines=True,
                                   shell=True)  #, creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)

        while process.poll() is None and not stop_event.is_set():
            time.sleep(1)  # Check every 500ms

        print("Process stopped or crashed {}".format(stop_event.is_set()))

        if stop_event.is_set():
            send_discord_message(config["server_status_webhook"], "Tile is being restarted for mod update")
            print(f"Stopping {path}")

            kill_process = psutil.Process(process.pid)
            for proc in kill_process.children(recursive=True):
                proc.kill()
            kill_process.kill()

            #if not kernel32.GenerateConsoleCtrlEvent(ctypes.c_uint(1), process.pid):
            #    print("Failed to send CTRL+C", ctypes.get_last_error())
            #else:
            #    print("CTRL+C sent successfully")
            break
        else:
            send_discord_message(config["server_status_webhook"], "Tile Crashed: Restarting")
            print(f"{path} has exited. It will be checked for restart conditions.")
            global crash_total
            crash_total += 1
            time.sleep(1)


def start_processes():
    global processes, stop_events
    processes = []
    stop_events = []
    for i in range(config["tile_num"]):
        exe_string = ('"{folder_path}MistServer.exe" -log -messaging -NoLiveServer -noupnp'
                      ' -EnableCheats -backendapiurloverride="{backend}" -CustomerKey={customer_key}'
                      ' -ProviderKey={provider_key}'
                      ' -slots={slots} -OverrideConnectionAddress={connection_ip} -identifier={identifier}{index}'
                      ' -port={start_port} -QueryPort={start_query_port}').format(
            folder_path=config["folder_path"],  # These should match the placeholders
            backend=config["backend"],
            customer_key=config["customer_key"],
            provider_key=config["provider_key"],
            connection_ip=config["connection_ip"],
            slots=config["slots"],
            identifier=config["identifier"],  # Placeholder for actual identifier
            index=i,  # Ensure 'i' is defined correctly in your context
            start_port=config["start_port"] + i,  # Adjusting according to your loop or calculation
            start_query_port=config["start_query_port"] + i)

        stop_event = threading.Event()
        stop_events.append(stop_event)
        process = threading.Thread(target=run_process, args=(exe_string, stop_event))
        process.start()
        processes.append(process)


def stop_processes():
    """ Stop all processes gracefully """
    for event in stop_events:
        event.set()

    for process in processes:
        process.join()


def update_config():
    global config
    with open("config.json", 'r') as file:
        config = json.load(file)


def check_mod_updates():
    try:
        update_config()
        mods_info = read_json('mods_info.json')

        print("Added new mod ids")

        out_of_date, updated_mods_info = update_mods_info(mods_info, config["mods"].split(","))

        print("Out-of-date mods:", out_of_date)
        return out_of_date, updated_mods_info
    except requests.exceptions as E:
        print("CheckModUpdates failed: " + E)
        return [], None


def download_mods(workshop_ids, updated_mods_info):
    try:
        mods_folder = config["folder_path"] + "Mist/Content/Mods"
        if not os.path.exists(mods_folder):
            # Create the folder if it does not exist
            os.makedirs(mods_folder)

        for item in os.listdir(mods_folder):
            item_path = os.path.join(mods_folder, item)
            try:
                if os.path.isfile(item_path) or os.path.islink(item_path):
                    os.unlink(item_path)  # Removes files and symbolic links
                elif os.path.isdir(item_path):
                    shutil.rmtree(item_path)  # Removes directories
            except Exception as e:
                print(f"Failed to delete {item_path}. Reason: {e}")

        for workshop_id in workshop_ids:
            cmd = f'"{config["steam_cmd_path"]}steamcmd.exe" +login anonymous +workshop_download_item 903950 {workshop_id} +quit'
            process = subprocess.run(cmd, shell=True, text=True, capture_output=True)
            output = process.stdout
            print(output)
            #if "Success" in output:  # Check the appropriate keyword based on your steamcmd output
            #    updated = True

        # Copy active mods over
        for workshop_id in config["mods"].split(","):
            src_item = os.path.join(config["steam_cmd_path"] + "steamapps/workshop/content/903950/", workshop_id)
            dest_item = os.path.join(mods_folder, workshop_id)
            try:
                if os.path.isdir(src_item):
                    shutil.copytree(src_item, dest_item)  # Copy directory
                else:
                    shutil.copy2(src_item, dest_item)
                    with open(dest_item + '/modinfo.json', 'r') as file:
                        mod_data = json.load(file, )

                    mod_data["active"] = True

                    with open(dest_item + '/modinfo.json', 'w') as file:
                        json.dump(mod_data, file)
                  # Copy files
            except Exception as e:
                print(f"Failed to copy {src_item} to {dest_item}. Reason: {e}")

        # Write updated data back to the JSON file
        with open('mods_info.json', 'w') as file:
            json.dump(updated_mods_info, file, indent=4)

    except Exception as E:
        print(E)

    return


def restart_all_tiles(wait):
    global wait_restart_time
    wait_restart_time = 0
    stop_processes()
    time.sleep(5)
    update_game()
    out_of_date, updated_mods_info = check_mod_updates()
    download_mods(out_of_date, updated_mods_info)
    time.sleep(wait)
    start_processes()


def update_game():
    # Define the SteamCMD command
    try:
        print("Starting steam update")
        steamcmd_command = "{}steamcmd +login anonymous +app_update 920720 validate -beta sdktest +quit".format(
            config["steam_cmd_path"])

        print(steamcmd_command)

        process = subprocess.Popen(steamcmd_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        # Read and print the output line by line
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                print(output.strip())

        # Capture any remaining output
        stdout, stderr = process.communicate()
        print(stdout)
        if stderr:
            print(stderr)

    except Exception as E:
        print(E)


def main():
    update_config()
    restart_all_tiles(1)

    while True:
        time.sleep(config["mod_check_interval"])
        out_of_date, updated_mods_info = check_mod_updates()
        if len(out_of_date) != 0:
            workshop = []
            for mod in out_of_date:
                workshop.append("https://steamcommunity.com/sharedfiles/filedetails/?id=" + mod)

            send_discord_message(config["server_status_webhook"], "Out-of-date mods restarting tiles in {} seconds: {}"
                                 .format(config["restart_time"], workshop))
            admin_writer.write("Restart", config["folder_path"])
            time.sleep(config["restart_time"])
            restart_all_tiles(1)


try:
    main()
except KeyboardInterrupt:
    admin_writer.write("Restart", config["folder_path"])
    #time.sleep(config["restart_time"])
    stop_processes()
