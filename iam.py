#!/usr/bin/env python3.6
# vim: sw=2 ts=2

import click
import boto3
import re
import json

CTX_SILENT_MODE = 'silent'
CTX_DEBUG_MODE = 'debug'
ADD_CMD = 'add_user'
CONTEXT_SETTINGS = dict(token_normalize_func=lambda x: x.lower())

def is_silent(ctx):
    return ctx.obj[CTX_SILENT_MODE]

def is_debug(ctx):
    return ctx.obj[CTX_DEBUG_MODE]

@click.group()
@click.option('--silent', is_flag=True, default=False, help='Accept all prompts')
@click.option('--debug', is_flag=True, default=False, help='Verbose output')
@click.pass_context
def cli(ctx, silent, debug):
    ctx.obj[CTX_SILENT_MODE] = silent
    ctx.obj[CTX_DEBUG_MODE] = debug
    click.echo('Silent mode is %s' % (is_silent(ctx) and 'on' or 'off'))
    click.echo('Debug mode is %s' % (is_silent(ctx) and 'on' or 'off'))

@cli.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.argument('profile')
def list_groups(ctx, profile):
    """List possible AWS IAM groups"""

    session = boto3.Session(profile_name=profile)
    client = session.client('iam')

    click.echo("Using profile: {0}".format(profile))

    response = client.list_groups()

    click.echo(click.style("\n....Group Names....", bold=True))
    for i in response['Groups']:
        click.echo(i['GroupName'])

@cli.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.argument('name')
@click.argument('profile')
@click.argument('group')
@click.option('--access-keys', is_flag=True, default=False, help='Add access keys to user in IAM')
def add_user(ctx, name, profile, group, access_keys):
    """Add IAM User"""

    silent = is_silent(ctx)

    session = boto3.Session(profile_name=profile)
    client = session.client('iam')

    click.echo("Using profile: {0}".format(profile))

    if silent:
        click.echo('Adding user "{0}" with group {1} to IAM'.format(name, group))
    elif not click.confirm('Add user "{0}" with group {1} to IAM?'.format(name, group)):
        sys.exit

    response = client.create_user(
        UserName = name
    )

    attach_group = client.add_user_to_group(
        GroupName = group,
        UserName = name
    )

    if access_keys:
        add_access_key = client.create_access_key(
            UserName = name
        )
        access_key_response = add_access_key['AccessKey']
        file = open('{0}_credentials.txt'.format(name), 'w')
        file.write(str(access_key_response))
        file.close()
    else:
        exit


    status = response['User']
    click.echo('"{0}" added in IAM.'.format(name))
    click.echo("Access Key file downloaded")

@cli.command(context_settings=CONTEXT_SETTINGS)
@click.pass_context
@click.argument('action', type=click.Choice([ADD_CMD]))
@click.argument('filename', type=click.Path(exists=True))
@click.argument('profile')
@click.option('--access-keys', is_flag=True, default=False, help='Add access keys to user in IAM')
def batch(ctx, action, filename, profile, access_keys):
    """Batch ECS Task"""

    silent = is_silent(ctx)
    filename = click.format_filename(filename)

    session = boto3.Session(profile_name=profile)
    client = session.client('iam')

    click.echo("Using profile: {0}".format(profile))

    if silent:
        click.echo('Batch processing {0}'.format(filename))
    elif not click.confirm('Batch process {0}?'.format(filename)):
        sys.exit(1)

    lines = tuple(open(filename, 'r'))
    for line in lines:
        line_split = line.strip().split(':')
        click.echo(line_split)
        ctx.invoke(add_user, name=line_split[0], group=line_split[1], profile=profile, access_keys=access_keys)

if __name__ == '__main__':
    cli(obj={})
