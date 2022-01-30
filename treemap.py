import os
from pathlib import Path

import click
import plotly.express as px


class TreemapData:
    def __init__(self, node, child):
        self.name = child.name
        self.id = child.rel_path
        self.parent = node.rel_path
        self.lines = child.lines

class Tree:
    def __init__(self, root):
        self.root = root


class Node:
    def __init__(self, full_path, rel_path):
        full_path = Path(full_path)
        rel_path = Path(rel_path)
        self.name = rel_path.stem
        self.full_path = full_path
        self.rel_path = rel_path
        self.children = {}
        self.lines = 0  # set later in compute_lines()

    def add_child(self, full_path, rel_path):
        child_name = rel_path.stem
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


def compute_lines(node, level=0):
    """Recursively set node.lines for the whole tree."""
    path = node.full_path
    if path.exists() and not path.is_dir():
        try:
            node.lines = len(open(path).readlines())
        except UnicodeDecodeError:
            node.lines = 1000  # size of binary?
    else:
        node.lines = sum(compute_lines(child, level + 1) for child in node.children.values())
    return node.lines


def get_treemap_data(node):
    data = []
    for child in node.children.values():
        data.append(TreemapData(node, child))
        child_data = get_treemap_data(child)
        data += child_data
    return data


def create_tree(base, paths, root_name):
    base = Path(base)
    root = Node(root_name, root_name)
    for file_path in paths:
        node = root
        rel_path = file_path.relative_to(base)
        child_path = Path("")
        for name in rel_path.parts:
            child_path /= name
            full_path = base / child_path
            node = node.add_child(full_path, child_path)
    compute_lines(root)
    return root


def create_treemap(data):
    names = [x.name for x in data]
    ids = [str(x.id) for x in data]
    parents = [str(x.parent) for x in data]
    values = [x.lines for x in data]
    fig = px.treemap(names=names, ids=ids, parents=parents, values=values, branchvalues='total')
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    fig.show()


@click.command()
@click.argument('root')
@click.option('--root_name', default="root",
              help="Name to use as root in the treepmap")
def create(root, root_name):
    root = Path(root)
    paths = get_paths(root)
    root = create_tree(root, paths, root_name)
    #print_tree(root)
    data = get_treemap_data(root)
    create_treemap(data)


if __name__ == '__main__':
    create()
