# treemap.py
#
# Creates an output HTML file which has a plotly-drive interactive treemap
# show the size of files into report: in lines for text files and in
# bytes for all files.
#
import json
import os
from pathlib import Path

import click
import humanize
import numpy as np
import plotly
import plotly.express as px

IGNORE = ['.git']
EXTENSIONS = ['.py']

class NpEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

class Tree:
    def __init__(self, root):
        self.root = root
        self.compute_size(self.root)

    def get_treemap_data(self):
        data = [TreemapData("", self.root)]
        return data + self.get_treemap_data_(self.root)

    def get_treemap_data_(self, parent):
        data = []
        for child in parent.children.values():
            data.append(TreemapData(parent, child))
            data += self.get_treemap_data_(child)
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
        self.parent = parent
        self.node = child


class Node:
    def __init__(self, full_path, rel_path):
        full_path = Path(full_path)
        rel_path = Path(rel_path)
        self.name = rel_path.name
        self.full_path = full_path
        self.rel_path = rel_path
        self.children = {}

        # Lines and bytes set later by compute_size()
        self.lines = 0
        self.bytes = 0

    def add_child(self, full_path, rel_path):
        child_name = rel_path.name
        return self.children.setdefault(child_name, Node(full_path, rel_path))


def get_paths(root):
    root = Path(root)
    paths = []
    for root, dirs, files in os.walk(root, topdown=True):
        for name in files:
            if name.startswith('test_'):
                continue
            ext = os.path.splitext(name)[1]
            if ext in EXTENSIONS:
                paths.append(Path(os.path.join(root, name)))
        dirs[:] = [x for x in dirs if x not in IGNORE]
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


def format_name(repo_path, node):
    if node.lines == 0:
        line_str = "binary"
    elif node.lines < 1_000_000:
        line_str = f"{humanize.intcomma(node.lines)} lines"
    else:
        line_str = f"{humanize.intword(node.lines)} lines"
    return f"{node.name} - {line_str}"

def format_parent(parent):
    if type(parent) == str:
        return parent
    return str(parent.rel_path)
# style='cursor: pointer' target='_blank' rel='noopener noreferrer'
TEMPLATE="""
%{label}<br>
Lines: %{value}<br>
Google: <a href='http://google.com'>google</a>
Google2: <a href='http://file/Users/pwinston/benchsci'>google</a>
File: <a href='vscode://file/Users/pwinston/benchsci/%{value}'>%{value}</a>
"""

def create_treemap_figure(data, repo_path):
    names = [format_name(repo_path, x.node) for x in data]
    ids = [str(x.node.rel_path) for x in data]
    parents = [format_parent(x.parent) for x in data]
    values = [x.node.lines for x in data]
    title_str = repo_path

    print(plotly.express.colors.named_colorscales())

    # tealrose
    scale = plotly.express.colors.get_colorscale('temps')
    colors = plotly.colors.colorscale_to_colors(scale)
    print(colors[0])
    print(len(colors))

    #print(names[:10])
    #print(parents[:10])
    color_map = {}
    

    for i, x in enumerate(ids):
        test = names[i].startswith('test_')
        depth = ids[i].count('/')
        color = colors[depth % len(colors)]        
        if test:
            r, g, b = plotly.colors.unlabel_rgb(color)
            r = min(r + 20, 255)
            g = min(g + 20, 255)
            b = min(b + 20, 255)
            color = f"rgb({r}, {g}, {b}"
        color_map[x] = color

    fig = px.treemap(names=names, ids=ids, parents=parents, values=values,
                     color=ids,
                     color_discrete_map=color_map, 
                     branchvalues='total', title=title_str)
    #fig.update_traces(root_color="lightgrey")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    fig.update_traces(texttemplate=TEMPLATE)
    return fig


@click.command()
@click.argument('repo_root')
@click.argument('repo_path')
@click.option('--config', default="config.json", help="JSON config file")
@click.option('--write', help="Write HTML page to this file")
@click.option('--show', is_flag=True, help="Show the figure with embedded browser")
def create(repo_root, repo_path, config, write, show):
    with open(config) as fp:
        config_data = json.load(fp)
    print(config_data)

    root = Path(repo_root) / repo_path
    paths = get_paths(root)
    print(f"Found {len(paths)} files...")

    tree = create_tree(repo_path, root, paths)
    #print_tree(root)

    data = tree.get_treemap_data()
    fig = create_treemap_figure(data, repo_path)

    print("WRITING")
    with open("fig.json", "w") as outf:
        outf.write(json.dumps(fig.to_dict(), indent=4, cls=NpEncoder))

    if write:
        fig.write_html(write)
    if show:
        fig.show()
    print("DONE")


if __name__ == '__main__':
    create()
