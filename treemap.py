import json
import os
from pathlib import Path

import click
import humanize
import plotly.express as px


class Tree:
    def __init__(self, root):
        self.root = root
        self.compute_size(self.root)

    def get_treemap_data(self):
        return self.get_treemap_data_(self.root)

    def get_treemap_data_(self, node):
        data = []
        for child in node.children.values():
            data.append(TreemapData(node, child))
            child_data = self.get_treemap_data_(child)
            data += child_data
        return data

    def compute_size(self, node, level=0):
        """Recursively set node.lines and node.bytes for all nodes."""
        path = node.full_path
        lines = bytes = 0
        if path.exists() and not path.is_dir():
            # We count bytes for all files.
            bytes = Path(path).stat().st_size
            try:
                # We only count lines in text files.
                lines = len(open(path).readlines())
            except UnicodeDecodeError:
                pass
        else:
            for child in node.children.values():
                child_lines, child_bytes = self.compute_size(child, level + 1)
                lines += child_lines
                bytes += child_bytes

        node.lines = lines
        node.bytes = bytes
        return lines, bytes


class TreemapData:
    def __init__(self, parent, child):
        self.node = child
        self.parent = parent.rel_path

class Node:
    def __init__(self, full_path, rel_path):
        full_path = Path(full_path)
        rel_path = Path(rel_path)
        self.name = rel_path.name
        self.full_path = full_path
        self.rel_path = rel_path
        self.children = {}

        # Set later in compute_size()
        self.lines = 0
        self.bytes = 0

    def add_child(self, full_path, rel_path):
        child_name = rel_path.name
        return self.children.setdefault(child_name, Node(full_path, rel_path))


def get_paths(root):
    root = Path(root)
    paths = []
    for root, dirs, files in os.walk(root, topdown=False):
        for name in files:
            paths.append(Path(os.path.join(root, name)))
    return paths


def print_tree(node, indent=0):
    indent_str = " " * indent
    print(f"{indent_str}{node.name} {node.rel_path} {node.full_path} {node.lines}")
    for child in node.children.values():
        print_tree(child, indent + 2)


def create_tree(repo_path, base, paths):
    base = Path(base)
    root = Node(repo_path, repo_path)
    for file_path in paths:
        node = root
        rel_path = file_path.relative_to(base)
        child_path = Path("")
        for name in rel_path.parts:
            child_path /= name
            full_path = base / child_path
            node = node.add_child(full_path, child_path)
    return Tree(root)


def format_name(node):
    if node.lines == 0:
        line_str = "binary"
    elif node.lines < 1_000_000:
        line_str = f"{humanize.intcomma(node.lines)} lines"
    else:
        line_str = f"{humanize.intword(node.lines)} lines"
    bytes_str = humanize.naturalsize(node.bytes)
    return f"{node.name} - {line_str} {bytes_str}"


def create_treemap(root, data):
    names = [format_name(x.node) for x in data]
    ids = [str(x.node.rel_path) for x in data]
    parents = [str(x.parent) for x in data]
    values = [x.node.bytes for x in data]
    fig = px.treemap(names=names, ids=ids, parents=parents, values=values,
                     branchvalues='total', title=str(root))
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    fig.show()


@click.command()
@click.argument('repo_root')
@click.argument('repo_path')
@click.option('--config', help="JSON config file")
def create(repo_root, repo_path, config):
    with open(config) as fp:
        config_data = json.load(fp)
    print(config_data)

    root = Path(repo_root) / repo_path
    paths = get_paths(root)
    print(f"Found {len(paths)} files...")

    tree = create_tree(repo_path, root, paths)
    #print_tree(root)
    data = tree.get_treemap_data()
    create_treemap(root, data)


if __name__ == '__main__':
    create()
