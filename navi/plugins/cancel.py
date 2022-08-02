import click
from .api_wrapper import request_data


@click.command(help="Choose your export type --> assets: '-a' or vulns: '-v'")
@click.argument('uuid')
@click.option('-a', is_flag=True, help="Cancel a Asset export")
@click.option('-v', is_flag=True, help="Cancel a Vulnerability Export")
def cancel(uuid, a, v):
    if not a and not v:
        click.echo("\n You need to signify which export type: '-a' or '-v'")
    if a:
        asset_response = request_data('POST', f'/assets/export/{uuid}/cancel')
        click.echo(asset_response)

    if v:
        vuln_response = request_data('POST', f'/vulns/export/{uuid}/cancel')
        click.echo(vuln_response)
