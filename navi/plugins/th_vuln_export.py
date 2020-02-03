import time
import threading
from queue import Queue
from sqlite3 import Error
from .api_wrapper import request_data
from .database import new_db_connection, drop_tables, insert_vulns
from .dbconfig import create_vulns_table

ock = threading.Lock()

q = Queue()

navi_id = 0


def worker():
    # The worker thread pulls an item from the queue and processes it
    while True:
        item = q.get()
        parse_data(request_data('GET', item))
        q.task_done()


def parse_data(chunk_data):
    database = r"navi.db"
    vuln_conn = new_db_connection(database)
    vuln_conn.execute('pragma journal_mode=wal;')
    with vuln_conn:
        # loop through all of the vulns in this chunk
        for vulns in chunk_data:
            # create a blank list to append asset details
            vuln_list = []
            global navi_id
            navi_id = navi_id + 1
            # Try block to ignore assets without IPs
            try:
                vuln_list.append(navi_id)
                try:
                    ipv4 = vulns['asset']['ipv4']
                    vuln_list.append(ipv4)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    asset_uuid = vulns['asset']['uuid']
                    vuln_list.append(asset_uuid)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    hostname = vulns['asset']['hostname']
                    vuln_list.append(hostname)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    first_found = vulns['first_found']
                    vuln_list.append(first_found)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    last_found = vulns['last_found']
                    vuln_list.append(last_found)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    output = vulns['output']
                    vuln_list.append(output)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    plugin_id = vulns['plugin']['id']
                    vuln_list.append(plugin_id)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    plugin_name = vulns['plugin']['name']
                    vuln_list.append(plugin_name)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    plugin_family = vulns['plugin']['family']
                    vuln_list.append(plugin_family)
                except KeyError:
                    vuln_list.append(" ")
                try:
                    port = vulns['port']['port']
                    vuln_list.append(port)
                except KeyError:
                    vuln_list.append(" ")
                try:
                    protocol = vulns['port']['protocol']
                    vuln_list.append(protocol)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    severity = vulns['severity']
                    vuln_list.append(severity)
                except KeyError:
                    vuln_list.append(" ")
                try:
                    scan_completed = vulns['scan']['completed_at']
                    vuln_list.append(scan_completed)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    scan_started = vulns['scan']['started_at']
                    vuln_list.append(scan_started)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    scan_uuid = vulns['scan']['uuid']
                    vuln_list.append(scan_uuid)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    schedule_id = vulns['scan']['schedule_id']
                    vuln_list.append(schedule_id)
                except KeyError:
                    vuln_list.append(" ")

                try:
                    state = vulns['state']
                    vuln_list.append(state)
                except KeyError:
                    vuln_list.append(" ")
                try:
                    insert_vulns(vuln_conn, vuln_list)
                except Error as e:
                    print(e)
            except IndexError:
                print("skipped one")

    vuln_conn.close()


def vuln_export(days):
    start = time.time()
    # Crete a new connection to our database
    database = r"navi.db"
    drop_conn = new_db_connection(database)

    # Right now we just drop the table.  Eventually I will actually update the database
    drop_tables(drop_conn, 'vulns')

    # Set URLS for threading
    urls = []

    # Set the payload to the maximum number of assets to be pulled at once
    day = 86400
    new_limit = day * int(days)
    day_limit = time.time() - new_limit
    pay_load = {"num_assets": 5000, "filters": {"last_found": int(day_limit)}}
    try:
        # request an export of the data
        export = request_data('POST', '/vulns/export', payload=pay_load)

        # grab the export UUID
        ex_uuid = export['export_uuid']
        print('\nRequesting Vulnerability Export with ID : ' + ex_uuid)

        # now check the status
        status = request_data('GET', '/vulns/export/' + ex_uuid + '/status')

        # status = get_data('/vulns/export/89ac18d9-d6bc-4cef-9615-2d138f1ff6d2/status')
        print("Status : " + str(status["status"]))

        # set a variable to True for our While loop
        not_ready = True

        # loop to check status until finished
        while not_ready is True:
            # Pull the status, then pause 5 seconds and ask again.
            if status['status'] == 'PROCESSING' or 'QUEUED':
                time.sleep(15)
                status = request_data('GET', '/vulns/export/' + ex_uuid + '/status')
                print("Status : " + str(status["status"]))

            # Exit Loop once confirmed finished
            if status['status'] == 'FINISHED':
                ptime = time.time()
                print("\nProcessing Time took : " + str(ptime - start))
                not_ready = False

            # Tell the user an error occured
            if status['status'] == 'ERROR':
                print("Error occurred")

        create_vulns_table()
        # Open a fresh connection to import data

        # grab all of the chunks and craft the URLS for threading
        for y in range(len(status['chunks_available'])):
            urls.append('/vulns/export/' + ex_uuid + '/chunks/' + str(y+1))

        for i in range(10):
            t = threading.Thread(target=worker)
            t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
            t.start()

        # stuff work items on the queue (in this case, just a number).
        # start = time.perf_counter()
        for item in range(len(urls)):
            q.put(urls[item])

        q.join()
        end = time.time()
        print(end - start)

    except KeyError:
        print("Well this is a bummer; you don't have permissions to download Asset data :( ")
    except TypeError:
        print("You may not be authorized or your keys are invalid")
