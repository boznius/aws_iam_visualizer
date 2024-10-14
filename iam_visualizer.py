#!/usr/bin/env python3
import boto3
import yaml
import argparse
import os
import subprocess
import sys

def get_iam_data(iam_client, entities, name):
    """Retrieve IAM users, roles, or policies based on specified names."""
    iam_data = {}

    if 'users' in entities or 'all' in entities:
        iam_data['Users'] = {}
        if name:
            try:
                user = iam_client.get_user(UserName=name)['User']
                user_data = get_user_data(iam_client, name)
                iam_data['Users'][name] = user_data
            except iam_client.exceptions.NoSuchEntityException:
                print(f"User '{name}' does not exist.")
                sys.exit(1)
        else:
            paginator = iam_client.get_paginator('list_users')
            for response in paginator.paginate():
                for user in response['Users']:
                    user_name = user['UserName']
                    user_data = get_user_data(iam_client, user_name)
                    iam_data['Users'][user_name] = user_data

    if 'roles' in entities or 'all' in entities:
        iam_data['Roles'] = {}
        if name:
            try:
                role = iam_client.get_role(RoleName=name)['Role']
                role_data = get_role_data(iam_client, name)
                iam_data['Roles'][name] = role_data
            except iam_client.exceptions.NoSuchEntityException:
                print(f"Role '{name}' does not exist.")
                sys.exit(1)
        else:
            paginator = iam_client.get_paginator('list_roles')
            for response in paginator.paginate():
                for role in response['Roles']:
                    role_name = role['RoleName']
                    role_data = get_role_data(iam_client, role_name)
                    iam_data['Roles'][role_name] = role_data

    if 'policies' in entities or 'all' in entities:
        iam_data['Policies'] = {}
        if name:
            paginator = iam_client.get_paginator('list_policies')
            found_policy = False
            for response in paginator.paginate(Scope='Local'):
                for policy in response['Policies']:
                    if policy['PolicyName'] == name:
                        policy_data = {
                            'Arn': policy['Arn'],
                            'AttachmentCount': policy['AttachmentCount'],
                            'DefaultVersionId': policy['DefaultVersionId']
                        }
                        iam_data['Policies'][name] = policy_data
                        found_policy = True
            if not found_policy:
                print(f"Policy '{name}' does not exist.")
                sys.exit(1)
        else:
            paginator = iam_client.get_paginator('list_policies')
            for response in paginator.paginate(Scope='Local'):
                for policy in response['Policies']:
                    policy_name = policy['PolicyName']
                    policy_data = {
                        'Arn': policy['Arn'],
                        'AttachmentCount': policy['AttachmentCount'],
                        'DefaultVersionId': policy['DefaultVersionId']
                    }
                    iam_data['Policies'][policy_name] = policy_data

    return iam_data

def get_user_data(iam_client, user_name):
    """Retrieve data for a specific user."""
    user_data = {
        'AttachedPolicies': [],
        'InlinePolicies': [],
        'Groups': {}
    }

    attached_policies = iam_client.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
    user_data['AttachedPolicies'] = [policy['PolicyName'] for policy in attached_policies]

    inline_policies = iam_client.list_user_policies(UserName=user_name)['PolicyNames']
    user_data['InlinePolicies'] = inline_policies

    groups = iam_client.list_groups_for_user(UserName=user_name)['Groups']
    for group in groups:
        group_name = group['GroupName']
        group_data = get_group_data(iam_client, group_name)
        user_data['Groups'][group_name] = group_data

    return user_data

def get_group_data(iam_client, group_name):
    """Retrieve data for a specific group."""
    group_data = {
        'AttachedPolicies': [],
        'InlinePolicies': []
    }

    attached_policies = iam_client.list_attached_group_policies(GroupName=group_name)['AttachedPolicies']
    group_data['AttachedPolicies'] = [policy['PolicyName'] for policy in attached_policies]

    inline_policies = iam_client.list_group_policies(GroupName=group_name)['PolicyNames']
    group_data['InlinePolicies'] = inline_policies

    return group_data

def get_role_data(iam_client, role_name):
    """Retrieve data for a specific role."""
    role_data = {
        'AttachedPolicies': [],
        'InlinePolicies': []
    }

    attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
    role_data['AttachedPolicies'] = [policy['PolicyName'] for policy in attached_policies]

    inline_policies = iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
    role_data['InlinePolicies'] = inline_policies

    return role_data

def write_yaml(iam_data, yaml_file, print_yaml=False):
    """Write IAM data to a YAML file or print it."""
    if print_yaml:
        print(yaml.dump(iam_data, sort_keys=False))
    else:
        with open(yaml_file, 'w') as f:
            yaml.dump(iam_data, f, sort_keys=False)

def write_dot(iam_data, dot_file):
    """Convert IAM data to DOT format and write to a file."""
    with open(dot_file, 'w') as f:
        f.write('digraph IAM {\n')
        f.write('  rankdir=LR;\n')
        f.write('  node [shape=rectangle, style=filled, fillcolor=white];\n')

        # Process Users
        for user, user_data in iam_data.get('Users', {}).items():
            f.write(f'  "{user}" [label="User: {user}"];\n')

            for policy in user_data.get('AttachedPolicies', []):
                f.write(f'  "{user}" -> "{policy}" [label="has policy"];\n')

            for policy in user_data.get('InlinePolicies', []):
                f.write(f'  "{user}" -> "{policy}" [label="has inline policy"];\n')

            for group, group_data in user_data.get('Groups', {}).items():
                f.write(f'  "{user}" -> "{group}" [label="member of"];\n')

                for policy in group_data.get('AttachedPolicies', []):
                    f.write(f'  "{group}" -> "{policy}" [label="has policy"];\n')
                for policy in group_data.get('InlinePolicies', []):
                    f.write(f'  "{group}" -> "{policy}" [label="has inline policy"];\n')

        # Process Roles
        for role, role_data in iam_data.get('Roles', {}).items():
            f.write(f'  "{role}" [label="Role: {role}", shape=oval];\n')

            for policy in role_data.get('AttachedPolicies', []):
                f.write(f'  "{role}" -> "{policy}" [label="has policy"];\n')

            for policy in role_data.get('InlinePolicies', []):
                f.write(f'  "{role}" -> "{policy}" [label="has inline policy"];\n')

        # Process Policies
        if 'Policies' in iam_data:
            for policy_name, policy_data in iam_data['Policies'].items():
                f.write(f'  "{policy_name}" [label="Policy: {policy_name}", shape=note];\n')

        f.write('}\n')

def generate_graph(dot_file, output_image):
    """Generate a graph image from a DOT file using Graphviz."""
    try:
        subprocess.run(['dot', '-Tpng', dot_file, '-o', output_image], check=True)
        print(f"Graph image generated: {output_image}")
    except subprocess.CalledProcessError as e:
        print(f"Error generating graph: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print("Graphviz 'dot' command not found. Please install Graphviz to generate graphs.")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description='AWS IAM Visualizer')
    parser.add_argument('--generate-graph', action='store_true', help='Generate graph visualization if Graphviz is installed')
    parser.add_argument('--yaml-file', default='iam_data.yaml', help='Output YAML file name')
    parser.add_argument('--dot-file', default='iam_graph.dot', help='Output DOT file name')
    parser.add_argument('--graph-image', default='iam_graph.png', help='Output graph image file name (PNG format)')
    parser.add_argument('--entities', default='all', help='Comma-separated list of entities to include: users,roles,policies')
    parser.add_argument('--name', help='Specify a user name, role name, or policy name to visualize')
    parser.add_argument('--print-yaml', action='store_true', help='Output YAML data to console instead of saving to a file')
    args = parser.parse_args()

    entities = [entity.strip().lower() for entity in args.entities.split(',')]

    iam_client = boto3.client('iam')
    print("Retrieving IAM data...")
    iam_data = get_iam_data(iam_client, entities, args.name)

    if args.print_yaml:
        print("Outputting IAM data to console:")
        write_yaml(iam_data, None, print_yaml=True)
    else:
        print(f"Writing IAM data to YAML file: {args.yaml_file}")
        write_yaml(iam_data, args.yaml_file)

    if args.generate_graph:
        print(f"Writing IAM data to DOT file: {args.dot_file}")
        write_dot(iam_data, args.dot_file)
        print("Generating graph visualization...")
        generate_graph(args.dot_file, args.graph_image)
    else:
        print("Graph generation skipped. Use '--generate-graph' to generate the graph visualization.")

if __name__ == "__main__":
    main()
