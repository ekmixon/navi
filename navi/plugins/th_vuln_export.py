import time
import threading
import click
from queue import Queue
from sqlite3 import Error
from .api_wrapper import request_data
from .database import new_db_connection, drop_tables, insert_vulns, insert_update_info, get_last_update_id, db_query
from .dbconfig import create_vulns_table

lock = threading.Lock()

q = Queue()


def worker():
    # The worker thread pulls an item from the queue and processes it
    while True:
        item = q.get()
        chunk_num = item[58:]
        # parse_data(request_data('GET', item))
        data = request_data('GET', item)
        parse_data(data, chunk_num)
        q.task_done()


def parse_data(chunk_data, chunk_number):
    database = r"navi.db"
    vuln_conn = new_db_connection(database)
    vuln_conn.execute('pragma journal_mode=wal;')
    vuln_conn.execute('pragma cashe_size=-10000')
    vuln_conn.execute('pragma synchronous=OFF')
    with vuln_conn:
        try:
            # loop through all of the vulns in this chunk
            for vulns in chunk_data:
                # create a blank list to append asset details
                vuln_list = []
                # Try block to ignore assets without IPs
                try:
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
                        cves = vulns['plugin']['cve']
                        vuln_list.append(str(cves))
                    except KeyError:
                        vuln_list.append(" ")

                    try:
                        score = vulns['plugin']['vpr']['score']
                        vuln_list.append(score)
                    except KeyError:
                        vuln_list.append(" ")

                    try:
                        exploit = vulns['plugin']['exploit_available']
                        vuln_list.append(str(exploit))
                    except KeyError:
                        vuln_list.append(" ")

                    try:
                        insert_vulns(vuln_conn, vuln_list)
                    except Error as e:
                        click.echo(e)
                except IndexError:
                    click.echo("skipped one")
        except TypeError:
            click.echo("Your Export has no data.  It may have expired")
            click.echo(f"Error on Chunk {chunk_number}")

    click.echo(f"Chunk {chunk_number} Finished")
    vuln_conn.close()


def vuln_export(days, ex_uuid, threads):
    start = time.time()

    database = r"navi.db"
    drop_conn = new_db_connection(database)
    drop_conn.execute('pragma journal_mode=wal;')

    # Right now we just drop the table.  Eventually I will actually update the database
    drop_tables(drop_conn, 'vulns')

    create_vulns_table()

    # Set URLS for threading
    urls = []

    # Set the payload to the maximum number of assets to be pulled at once
    day = 86400
    new_limit = day * int(days)
    day_limit = time.time() - new_limit
    pay_load = {"num_assets": 50, "filters": {'last_found': int(day_limit), "state": ['open', 'reopened']}}
    try:

        if ex_uuid == '0':
            # request an export of the data
            export = request_data('POST', '/vulns/export', payload=pay_load)

            # grab the export UUID
            ex_uuid = export['export_uuid']
            click.echo(f'\nRequesting Vulnerability Export with ID : {ex_uuid}')

        else:
            click.echo("\nUsing your Export UUID\n")
        # set a variable to True for our While loop
        not_ready = True
        # now check the status
        status = request_data('GET', f'/vulns/export/{ex_uuid}/status')

        # status = get_data('/vulns/export/89ac18d9-d6bc-4cef-9615-2d138f1ff6d2/status')
        click.echo(f'Status : {str(status["status"])}')

        # loop to check status until finished
        while not_ready:
            time.sleep(2.5)
            status = request_data('GET', f'/vulns/export/{ex_uuid}/status')
            # Exit Loop once confirmed finished
            if status['status'] == 'FINISHED':
                ptime = time.time()
                click.echo(f"\nProcessing Time took : {str(ptime - start)}")

                # Display how many chunks there are
                avail = status['total_chunks']
                click.echo(f"\nChunks Available - {avail}")
                click.echo("Downloading chunks now...hold tight...This can take some time\n")
                not_ready = False

            # Tell the user an error occured
            if status['status'] == 'ERROR':
                click.echo("Error occurred")

        # grab all of the chunks and craft the URLS for threading
        urls.extend(
            f'/vulns/export/{ex_uuid}/chunks/{str(y)}'
            for y in status['chunks_available']
        )

        for _ in range(threads):
            t = threading.Thread(target=worker)
            t.daemon = True  # thread dies when main thread (only non-daemon thread) exits.
            t.start()

        for url in urls:
            q.put(url)

        q.join()
        end = time.time()
        click.echo(f"Vulnerability Update Time took : {str(end - start)}\n")

        update_id = get_last_update_id()
        diff_dict = [update_id, str(start), str(days), "Vuln update", str(ex_uuid)]  # need to ignore if the Ex_uuid exists in the db.
        database_2 = r"navi.db"
        conn = new_db_connection(database_2)
        with conn:
            insert_update_info(conn, diff_dict)

        click.echo("\nCreating a few indexes to make queries faster.\n")
        db_query("CREATE INDEX vulns_plugin_id on vulns (plugin_id);")
        db_query("CREATE INDEX vulns_ports on vulns (port);")
        db_query("CREATE INDEX vulns_uuid on vulns (asset_uuid);")

    except KeyError:
        click.echo("Well this is a bummer; you don't have permissions to download Asset data :( ")

    except TypeError:
        click.echo("You may not be authorized or your keys are invalid")
