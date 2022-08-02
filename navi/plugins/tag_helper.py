import click
from .api_wrapper import request_data, tenb_connection
from .database import db_query


def grab_all_tags():
    tio = tenb_connection()
    tag_list = []

    for tags in tio.tags.list():
        my_tuple = (tags['category_name'], tags['value'], tags['uuid'])
        tag_list.append(my_tuple)

    return tag_list


def update_tag(c, v, tag_list):
    click.echo("Your tag is being updated\n")

    try:
        list_tags = grab_all_tags()

        for tag_info in list_tags:
            if (
                str(tag_info[0]).lower() == str(c).lower()
                and str(tag_info[1]).lower() == str(v).lower()
            ):
                try:
                    tag_uuid = tag_info[2]
                    payload = {"action": "add", "assets": tag_list, "tags": [tag_uuid]}
                    data = request_data('POST', '/tags/assets/assignments', payload=payload)
                    click.echo(f"Job UUID : {data['job_uuid']}")
                except IndexError:
                    pass
    except:
        pass


def tag_checker(uuid, key, value):
    data = db_query(
        f"SELECT * from tags where asset_uuid='{uuid}' and tag_key='{key}' and tag_value='{value}';"
    )

    length = len(data)
    return 'yes' if length != 0 else 'no'


def confirm_tag_exists(key, value):
    try:
        tag_list = grab_all_tags()

        for tag_info in tag_list:
            if (
                str(tag_info[0]).lower() == str(key).lower()
                and str(tag_info[1]).lower() == str(value).lower()
            ):
                return 'yes'
    except Exception as E:
        click.echo(E)


def return_tag_uuid(key, value):
    tag_list = grab_all_tags()
    try:
        for tag_info in tag_list:
            if str(tag_info[0]).lower() == str(key).lower():
                if str(tag_info[1]).lower() == str(value).lower():
                    return str(tag_info[2])
                else:
                    return 'none'
    except Exception as E:
        click.echo(E)


def tag_msg():
    click.echo("Remember to run the update command if you want to use your new tag in navi")
