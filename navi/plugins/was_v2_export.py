import csv
import click
from .api_wrapper import request_data


def was_export():
    # Crete a csv file object
    with open('was_summary_data.csv', mode='w') as csv_file:
        agent_writer = csv.writer(csv_file, delimiter=',', quotechar='"')
        # write our Header information first
        header_list = ["Scan Name", "Target", "High", "Medium", "Low", "Scan Start", "Scan Finish", "Note Title", "Note Message"]
        agent_writer.writerow(header_list)

        params = {"size": "1000"}
        # Grab all of the Scans
        data = request_data('GET', '/was/v2/scans', params=params)

        for scan_data in data['data']:
            was_scan_id = scan_data['scan_id']
            status = scan_data['status']
            # Ignore all scans that have not completed
            if status == 'completed':
                start = scan_data['started_at']
                finish = scan_data['finalized_at']

                report = request_data('GET', f'/was/v2/scans/{was_scan_id}/report')
                high = []
                medium = []
                low = []
                csv_list = []
                try:
                    name = report['config']['name']
                    try:
                        target = report['scan']['target']
                    except KeyError:
                        target = report['config']['settings']['target']
                    try:
                        title = report['notes'][0]['title']
                        message = report['notes'][0]['message']
                    except IndexError:
                        # There may not be any Notes set the vars to ""
                        title = ""
                        message = ""

                    for finding in report['findings']:
                        risk = finding['risk_factor']
                        plugin_id = finding['plugin_id']
                        if risk == 'high':
                            high.append(plugin_id)
                        elif risk == 'low':
                            low.append(plugin_id)

                        elif risk == 'medium':
                            medium.append(plugin_id)
                    csv_list.extend(
                        (
                            name,
                            target,
                            len(high),
                            len(medium),
                            len(low),
                            start,
                            finish,
                            title,
                            message,
                        )
                    )

                    agent_writer.writerow(csv_list)
                except TypeError as E:
                    print(E)
        click.echo()
