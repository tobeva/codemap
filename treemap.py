import os
from pathlib import Path

import click
import plotly.express as px


class Node:
    def __init__(self, path):
        path = Path(path)
        self.name = path.stem
        self.path = path
        self.children = {}
        if path.exists() and not path._is_dir():
            self.lines = self.count_lines()
        else:
            self.lines = 0

    def add_child(self, path):
        child_name = path.stem
        return self.children.setdefault(child_name, Node(path))


class TreemapData:
    def __init__(self, node, child):
        self.name = child.name
        self.id = child.path
        self.parent = node.path

def get_paths(base):
    base = Path(base)
    paths = []
    for root, dirs, files in os.walk(base, topdown=False):
        for name in files:
            full_path = Path(os.path.join(root, name))
            rel_path = full_path.relative_to(base)
            paths.append(rel_path)
    return paths


def print_tree(node, indent=0):
    indent_str = " " * indent
    print(f"{indent_str}{node.name}")
    for child in node.children.values():
        print_tree(child, indent + 2)


def get_treemap_data(node):
    data = []
    for child in node.children.values():
        data.append(TreemapData(node, child))
        child_data = get_treemap_data(child)
        data += child_data
    return data


def create_tree(paths, root_name):
    root = Node(root_name)
    for path in paths:
        node = root
        child_path = Path(root_name)
        for name in path.parts:
            child_path /= name
            node = node.add_child(child_path)
    return root


def create_treemap(data):
    names = [x.name for x in data]
    ids = [str(x.id) for x in data]
    parents = [str(x.parent) for x in data]
    fig = px.treemap(names=names, ids=ids, parents=parents)
    fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    fig.show()


@click.command()
@click.argument('root')
@click.option('--root_name', default="root",
              help="Name to use as root in the treepmap")
def create(root, root_name):
    paths = get_paths(root)
    root = create_tree(paths, root_name)
    print_tree(root)
    data = get_treemap_data(root)
    create_treemap(data)


if __name__ == '__main__':
    create()
