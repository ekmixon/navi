import csv
import click
from sqlite3 import Error
from .api_wrapper import request_data


def add_helper(file, source):
    try:

        with open(file, 'r', newline='') as new_file:
            add_assets = csv.reader(new_file)

            for row in add_assets:
                ipv4 = [row[0]]
                asset = {"ip_address": ipv4}
                macs = [row[1]]
                asset["mac_address"] = macs

                hostnames = [row[2]]
                asset["hostname"] = hostnames

                fqdns = [row[3]]
                asset["fqdn"] = fqdns

                # create Payload
                payload = {"assets": [asset], "source": source}

                click.echo(f"Added the following Data : \n{payload}\n")

                # request Import Job
                data = request_data('POST', '/import/assets', payload=payload)
                click.echo(f"Your Import ID is : {data['asset_import_job_uuid']}")
    except Error as e:
        click.echo(e)
