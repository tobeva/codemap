import plotly.express as px

def create_treemap():
    names = ['a', 'b', 'c', 'd']
    ids = ['a', 'a/b', 'a/c', 'a/c/d']
    parents = ['', 'a', 'a', 'a/c']
    values = [10, 5, 5, 2]

    colors = {
        'a': 'red',
        'a/b': 'green',
        'a/c': 'gold',
        'a/c/d': 'grey'
    }

    fig = px.treemap(names=names, ids=ids, parents=parents, values=values,
                     color=ids,
                     color_discrete_map=colors, 
                     branchvalues='total', title="my treemap")
    fig.update_layout(margin=dict(t=50, l=25, r=25, b=25))
    return fig

create_treemap().show()
