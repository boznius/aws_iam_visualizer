#!/usr/bin/env python3
import boto3
import yaml
import argparse
import os
import subprocess
import sys

def get_iam_data(iam_client):
    """Retrieve IAM users, groups, roles, and their policies."""
    iam_data = {
        'Users': {},
        'Roles': {}
    }

    # Get Users and their policies
    paginator = iam_client.get_paginator('list_users')
    for response in paginator.paginate():
        for user in response['Users']:
            user_name = user['UserName']
            user_data = {
                'AttachedPolicies': [],
                'InlinePolicies': [],
                'Groups': {}
            }

            # Attached managed policies
            attached_policies = iam_client.list_attached_user_policies(UserName=user_name)['AttachedPolicies']
            user_data['AttachedPolicies'] = [policy['PolicyName'] for policy in attached_policies]

            # Inline policies
            inline_policies = iam_client.list_user_policies(UserName=user_name)['PolicyNames']
            user_data['InlinePolicies'] = inline_policies

            # Groups and their policies
            groups = iam_client.list_groups_for_user(UserName=user_name)['Groups']
            for group in groups:
                group_name = group['GroupName']
                group_data = {
                    'AttachedPolicies': [],
                    'InlinePolicies': []
                }

                # Group attached policies
                attached_group_policies = iam_client.list_attached_group_policies(GroupName=group_name)['AttachedPolicies']
                group_data['AttachedPolicies'] = [policy['PolicyName'] for policy in attached_group_policies]

                # Group inline policies
                inline_group_policies = iam_client.list_group_policies(GroupName=group_name)['PolicyNames']
                group_data['InlinePolicies'] = inline_group_policies

                user_data['Groups'][group_name] = group_data

            iam_data['Users'][user_name] = user_data

    # Get Roles and their policies
    paginator = iam_client.get_paginator('list_roles')
    for response in paginator.paginate():
        for role in response['Roles']:
            role_name = role['RoleName']
            role_data = {
                'AttachedPolicies': [],
                'InlinePolicies': []
            }

            # Attached managed policies
            attached_policies = iam_client.list_attached_role_policies(RoleName=role_name)['AttachedPolicies']
            role_data['AttachedPolicies'] = [policy['PolicyName'] for policy in attached_policies]

            # Inline policies
            inline_policies = iam_client.list_role_policies(RoleName=role_name)['PolicyNames']
            role_data['InlinePolicies'] = inline_policies

            iam_data['Roles'][role_name] = role_data

    return iam_data

def write_yaml(iam_data, yaml_file):
    """Write IAM data to a YAML file."""
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

            # Attached Policies
            for policy in user_data.get('AttachedPolicies', []):
                f.write(f'  "{user}" -> "{policy}" [label="has policy"];\n')

            # Inline Policies
            for policy in user_data.get('InlinePolicies', []):
                f.write(f'  "{user}" -> "{policy}" [label="has inline policy"];\n')

            # Groups
            for group, group_data in user_data.get('Groups', {}).items():
                f.write(f'  "{user}" -> "{group}" [label="member of"];\n')

                # Group Policies
                for policy in group_data.get('AttachedPolicies', []):
                    f.write(f'  "{group}" -> "{policy}" [label="has policy"];\n')
                for policy in group_data.get('InlinePolicies', []):
                    f.write(f'  "{group}" -> "{policy}" [label="has inline policy"];\n')

        # Process Roles
        for role, role_data in iam_data.get('Roles', {}).items():
            f.write(f'  "{role}" [label="Role: {role}", shape=oval];\n')

            # Attached Policies
            for policy in role_data.get('AttachedPolicies', []):
                f.write(f'  "{role}" -> "{policy}" [label="has policy"];\n')

            # Inline Policies
            for policy in role_data.get('InlinePolicies', []):
                f.write(f'  "{role}" -> "{policy}" [label="has inline policy"];\n')

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
    args = parser.parse_args()

    iam_client = boto3.client('iam')
    print("Retrieving IAM data...")
    iam_data = get_iam_data(iam_client)

    print(f"Writing IAM data to YAML file: {args.yaml_file}")
    write_yaml(iam_data, args.yaml_file)

    print(f"Writing IAM data to DOT file: {args.dot_file}")
    write_dot(iam_data, args.dot_file)

    if args.generate_graph:
        print("Generating graph visualization...")
        generate_graph(args.dot_file, args.graph_image)
    else:
        print("Graph generation skipped. Use '--generate-graph' to generate the graph visualization.")

if __name__ == "__main__":
    main()
