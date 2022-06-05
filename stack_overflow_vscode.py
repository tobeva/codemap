    import plotly.express as px

    TEMPLATE="""
    %{label}<br>
    Link1: <a href='http://google.com'>google</a>
    Link2: <a href='vscode://file/somefile>somefile</a>
    """

    def create_treemap():
        names = ['parent', 'child-1', 'child-2']
        ids = [1, 2, 3]
        parents = [None, 1, 1]
        values = [10, 5, 5]

        fig = px.treemap(names=names, ids=ids, parents=parents, values=values,
                        branchvalues='total', title="My Treemap")
        fig.update_traces(texttemplate=TEMPLATE)
        return fig

    create_treemap().write_html("test.html")
