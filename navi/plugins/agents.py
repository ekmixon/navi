import click
from .api_wrapper import tenb_connection
import textwrap

tio = tenb_connection()


@click.group(help="Perform common tasks against Agents and Agent Groups")
def agent():
    pass


@agent.command(help="Display Agent information - Agent ID/UUID")
@click.option("--aid", default=None, help="Display Agent information using the Agent ID")
def display(aid):
    try:
        if aid:
            try:
                agent_details = tio.agents.details(aid)

                click.echo("\nAgent Details")
                click.echo("-----------------\n")
                click.echo(f"Agent Name: {agent_details['distro']}")
                click.echo(f"Agent IP: {agent_details['distro']}")
                click.echo(f"Agent UUID: {agent_details['uuid']}")
                click.echo(f"Network UUID: {agent_details['network_uuid']}")
                click.echo(f"Plugin Feed: {agent_details['plugin_feed_id']}")

                click.echo("\nDistribution Information")
                click.echo("----------------------------\n")
                click.echo(f"Platform: {agent_details['platform']}")
                click.echo(f"Distribution: {agent_details['distro']}")
                click.echo(f"Core Version: {agent_details['core_version']}")
                click.echo(f"Core Build: {agent_details['core_build']}")

                click.echo("\nAgent Connection information")
                click.echo("----------------------------\n")
                click.echo(f"Last Connect Time: {agent_details['last_connect']}")
                click.echo(f"Last Scan Time: {agent_details['last_scanned']}")
                click.echo(f"Restart Pending: {agent_details['restart_pending']}")
                click.echo(f"Status: {agent_details['status']}")

                click.echo("\nAgent Groups")
                click.echo("----------------------------\n")
                for agent_groups in agent_details['groups']:
                    click.echo(
                        f"Group Name({str(agent_groups['id'])}): {str(agent_groups['name'])}"
                    )

            except TypeError:
                click.echo("\nCommon...really? Focus...You need the Agent ID... Try again\n")
                exit()

        else:
            click.echo("\n*** To see Agent Details use: navi agent --aid <agent id> ***\n")
            click.echo("\n{:45s} {:12} {}".format("Agent Name", "Agent ID", "Group(id)s"))
            click.echo("-" * 150)

            for agent_info in tio.agents.list():
                groups_string = ''
                try:
                    for group in agent_info['groups']:
                        groups_string = groups_string + f", {group['name']}({group['id']})"
                except KeyError:
                    pass
                click.echo("{:45s} {:12} {}".format(textwrap.shorten(str(agent_info['name']), width=45),
                                                    str(agent_info['id']),
                                                    textwrap.shorten(groups_string[1:], width=90)))
        click.echo()
    except AttributeError:
        click.echo("\nCheck your permissions or your API keys\n")


@agent.command(help="Display Agent Groups and membership information ")
@click.option("--gid", default=None, help="Display the agents that are members of the group using the group ID")
def groups(gid):

    if gid:
        group_details = tio.agent_groups.details(gid)
        click.echo("\n{:85s} {:15} {:40}".format("Agent Name", "Agent ID", "UUID", "Status"))
        click.echo("-" * 150)

        for agent_info in group_details['agents']:
            click.echo("{:85s} {:15} {:40s}".format(textwrap.shorten(str(agent_info['name']), width=85),
                                                    str(agent_info['id']),
                                                    str(agent_info['uuid']), str(agent_info['status'])))

        click.echo()
    else:
        click.echo("\n*** To see group membership use: navi agent groups --gid <group id> ***\n")
        try:
            click.echo("\n{:45} {:40} {:10}".format("Group Name", "Group UUID", "Group ID"))
            click.echo("-" * 150)

            group_list = tio.agent_groups.list()

            for group in group_list:
                click.echo("{:45} {:40} {:10}".format(str(group['name']), str(group['uuid']), str(group['id'])))

            click.echo()
        except AttributeError:
            click.echo("\nCheck your permissions or your API keys\n")


@agent.command(help="Create a new Agent Group")
@click.option("--name", default=None, required=True, help="The name of the new Agent Group you want to create")
@click.option("--scanner", default=1, help="Add Agent Group to a specific scanner")
def create(name, scanner):
    group_creation = tio.agent_groups.create(name=name, scanner_id=scanner)

    click.echo(
        f"\nYour agent group: {group_creation['name']} has been created.\n\nHere is the ID: {str(group_creation['id'])} and UUID : {str(group_creation['uuid'])}\n"
    )


@agent.command(help="Add an agent to a Group")
@click.option("--aid", default=None, required=True, help="The agent ID of the agent you want to add ")
@click.option("--gid", default=None, required=True, help="The Group ID you want to add the agent(s) to.")
def add(aid, gid):
    # Add agent to Group
    tio.agent_groups.add_agent(gid, aid)

    click.echo(f"\nYour agent has been added to the Group ID: {gid}\n")


@agent.command(help="Remove an Agent from a Agent Group")
@click.option("--aid", default=None, required=True, help="The agent ID of the agent you want to remove ")
@click.option("--gid", default=None, required=True, help="The Group ID you want to add the agent(s) to.")
def remove(aid, gid):
    # Remove an agent from a Group
    tio.agent_groups.delete_agent(gid, aid)

    click.echo(f"\nYour agent has been removed from the Group ID: {gid}\n")


@agent.command(help="Unlink an by Agent ID")
@click.option("--aid", default=None, required=True, help="The Agent ID of the agent you want to unlink")
def unlink(aid):
    tio.agents.unlink(aid)
    click.echo(f"\nYour Agent: {aid} has been unlinked")
