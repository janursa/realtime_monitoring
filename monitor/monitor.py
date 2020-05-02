

"""This module is designed to visualize csv files on a browser in a real time fashion. 
Author: Jalil Nourisa

"""
import  sys, time, os
import dash
import dash_core_components as dcc
import dash_html_components as html
from   dash.dependencies import Input, Output
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
import plotly
import numpy as np

def _get_docs_index_path(): # returns dir of the documentation file
    # my_package_root = os.path.dirname(os.path.dirname(__file__))
    docs_index = os.path.join('docs', 'build', 'html', 'index.html')
    return docs_index
def _docstring_parameter(*args, **kwargs): # addes keywords to the docstring
    def dec(obj):
        obj.__doc__ = obj.__doc__.format(*args, **kwargs)
        return obj
    return dec
    
class _externals:
    @staticmethod
    def get_stylesheets():
        return [ "https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/css/materialize.min.css"]
    @staticmethod
    def get_scripts():
        return ['https://cdnjs.cloudflare.com/ajax/libs/materialize/0.100.2/js/materialize.min.js']

class plots:
    line_types = ['solid', 'dot', 'dash', 'longdash', 'dashdot', 'longdashdot']
    @staticmethod
    def lines(data,name):
        """Constructs a lines plot using Plotly Go

        Args:
            data (DataFrame): data in the form of Pandas DataFrame
            name (str): the title of the plot
        
        Returns:
            Figure: Returns a figure object
        """
        
        traces = []
        i =0
        for key,value in data.items():
            traces.append(go.Scatter(
                y=value,
                name=key,
                line = dict(width=3, dash=plots.line_types[i])
            ))
            i+=1

        layout = go.Layout(
            title=dict(
                text= '<b>'+name+'</b>',
                y= 0.9,
                x= 0.5,
                xanchor= 'center',
                yanchor= 'top',
                font=dict(
                    family='sans-serif',
                    size=20,
                    color='#100'
                )),
            xaxis = dict(title = "Intervals", zeroline = False,range=
                        [min(data.index) - 0.5,
                         max(data.index) + 0.5]),
            yaxis = dict(title = "Values", zeroline = False, range =
                        [min([min(data[key]) for key in data.keys()]) - 0.5,
                         max([max(data[key]) for key in data.keys()]) + 0.5]),
            legend=dict(
                x=1,
                y=.95,
                traceorder='normal',
                font=dict(
                    family='sans-serif',
                    size=12,
                    color='#000'
                ),
                bordercolor='#FFFFFF',
                borderwidth=1
            ),
            margin=dict(
                l=50,
                r=50,
                b=100,
                t=100,
                pad=4
            )
        )
        return traces, layout
    def scatter(data,name):
        """Constructs a scatter plot using Plotly express
        
        Args:
            data (DataFrame): data in the form of Pandas DataFrame
            name (str): the title of the plot
        
        Returns:
            Figure: Returns a figure object
        """
        x_length = max(data["x"]) - min(data["x"])
        y_length = max(data["y"]) - min(data["y"])

        max_agent_size = max(data["size"])
        min_agent_size = min(data["size"])
        marker_max_size = 2.*(max_agent_size / 20**2)
        fig = px.scatter(
            data,
            x = data["x"],
            y = data["y"],
            color = data["agent_type"],
            size = data["size"],
            size_max = marker_max_size,
            # size_min=min_agent_size,
            hover_name = data["agent_type"],
            render_mode='webgl',
            width = data["graph_size"],
            height = data["graph_size"]*(y_length / x_length)
        )
        fig.update_layout(
            title=dict(
                text= '<b>'+name+'</b>',
                y= .9,
                x= 0.5,
                xanchor= 'center',
                yanchor= 'top',
                font=dict(
                    family='sans-serif',
                    size=20,
                    color='#100'
                )),
            # autosize=False,
            # width=1200,
            # height=1200
            margin=dict(
                l=50,
                r=150,
                b=100,
                t=100,
                pad=4
            )
            # paper_bgcolor="#b6e2f5"
            )
        fig.update_yaxes(automargin=True,showgrid=False,zeroline=False)
        fig.update_xaxes(automargin=True,showgrid=False,zeroline=False)
        return fig

@_docstring_parameter(_get_docs_index_path())
class watch:
    """This is the main class to read the files, construct plots and monitor changes.
    For documentation, see {}

    """
    
    def __init__(self,info):
        """Initialize the app by setting up the framework py::meth:`frame` and callback functions py::meth:`callbacks`.
        
        Args:
            info (dict): The information of the plots entered by the user.
        """
        self.df = info 

        self.app = dash.Dash(__name__,
                            external_stylesheets = _externals.get_stylesheets(),
                            external_scripts = _externals.get_scripts())

        self.app.css.config.serve_locally = True
        self.app.scripts.config.serve_locally = True

        self.frame()
        self.callbacks()

    app = 0
    df = {}
    def postprocess(self,df,fig_type):
        """
            - Catches some errors in the input file.
            - Addes generic size and type columns in case they are not given in the file. 
                    For the case of custom plots, the process is skipped.
        
        Args:
            df (DataFrame): Data read from the directory file. This data needs processing.
            fig_type (TYPE): The type of the plot, i.e. lines and scatter.
        
        Returns:
            DataFrame: The processed data.
        """
        if "Unnamed: 0" in df.keys(): # processing some errors
            df = df.drop("Unnamed: 0", axis=1)

        if fig_type == "custom": #custom plot is given
            pass
        else: # add these items if custom plot is not given
            # add size if it's not there
            if fig_type == "scatter":  #if it's a scatter plot, add missin items, i.e. size and type
                if "size" not in df.keys():
                    fixed_size = np.ones(len(df["x"]))
                    df["size"] = fixed_size
        
                if "agent_type" not in df.keys():
                    fixed_agent_type = "agent"
                    df["agent_type"] = fixed_agent_type
        return df
    def read(self,file_dir):
        """Reads the data files in csv and converts them into pandas DataFrame.
        
        Args:
            file_dir (string): file directory
        
        Returns:
            DataFrame: content of the file

        """
        try:
            data = pd.read_csv(file_dir)
        except FileNotFoundError:
            print("Given file directory {} is invalid".format(file_dir))
            sys.exit()
        return data
    def update_db(self):
        """Updates the global database in case there are changes in the files. 
        It queries modification date of files and upon change in the modification date, it calles :py:meth:`read`,
        to import the new data and then :py:meth:`postprocess` to process. 
        
        Returns:
            bool: if any changes occures, this flag will be true
        """
        any_update_flag = False  # if any of the files has changed
        for name in self.df.keys(): # main keys such as plot names
            file = self.df[name]["graph_dir"]
            last_moddate = os.stat(file)[8] # last modification time
            if "moddate" not in self.df[name].keys() : # in this case, file is not upload for the first optimizer
                data = self.read(file)
                data = self.postprocess(data,self.df[name]["graph_type"])

                self.df[name].update({"data":data})
                self.df[name].update({"moddate":last_moddate})
                any_update_flag = True
            elif self.df[name]["moddate"] != last_moddate:# if the new date is different
                data = self.read(file)
                data = self.postprocess(data,self.df[name]["graph_type"])

                self.df[name].update({"data":data})
                self.df[name].update({"moddate":last_moddate})
                any_update_flag = True

            else:
                continue
        return any_update_flag
    def frame(self):
        """
        Lays out the HTML and defines holders
        """
        self.app.layout = html.Div([
            html.Div([
                html.H2('List of plots',
                        style={'float': 'left',
                               }),
                ]),
            dcc.Dropdown(id='list_of_plots',
                         options=[{'label': s, 'value': s}
                                  for s in self.df.keys()],
                         value=[s for s in self.df.keys()],
                         multi=True
                         ),
            html.Button(id='flag', children='update'),
            html.Div(children=html.Div(id='graphs'), className='row'),

            dcc.Interval(
                id='time',
                interval=1000,
                n_intervals = 0)
        ], className="container",style={'width':'98%','margin-left':10,'margin-right':10,'max-width':50000})
    def callbacks(self):
        """Contains two call back functions. py::meth:`update_graph`.
        """
        @self.app.callback(
            dash.dependencies.Output('graphs','children'),
            [dash.dependencies.Input('list_of_plots', 'value'),
            dash.dependencies.Input('flag','n_clicks')
            ]
            )
        def update_graph(req_graph_tags,n_clicks):
            """Summary
            
            Args:
                req_graph_tags (TYPE): Description
                n_clicks (TYPE): Description
            
            Returns:
                TYPE: Description
            """
            graphs = []
            if len(req_graph_tags)>2:
                class_choice = 'col s12 m6 l6'
            elif len(req_graph_tags) == 2:
                class_choice = 'col s12 m6 l6'
            else:
                class_choice = 'col s12'
            for req_graph_tag in req_graph_tags: # iterate through requested graph tags
                if self.df[req_graph_tag]["graph_type"] == "custom": # if the plot is given, just add it to the graph list
                    figure_func = self.df[req_graph_tag]["figure"]
                    figure = figure_func(self.df[req_graph_tag]["data"])
                    graph = html.Div(dcc.Graph(
                                    id=req_graph_tag,
                                    figure=figure
                                    ), className=class_choice)
                    graphs.append(graph)
                else:
                    if self.df[req_graph_tag]["graph_type"] == "lines":
                        sub_graph,layout = plots.lines(self.df[req_graph_tag]["data"],req_graph_tag)
                        graph = html.Div(dcc.Graph(
                                        id=req_graph_tag,
                                        figure={'data': sub_graph,'layout' : layout}
                                        ), className=class_choice)
                        graphs.append(graph)
                    elif self.df[req_graph_tag]["graph_type"] == "scatter":
                        figure = plots.scatter(self.df[req_graph_tag]["data"],req_graph_tag)
                        graph = html.Div(dcc.Graph(
                                        id=req_graph_tag,
                                        figure=figure
                                        ), className=class_choice)
                        graphs.append(graph)
                    else:
                        print("Graph type is not defined. It should be either lines or scatter")
                        sys.exit()

            return graphs

        @self.app.callback(dash.dependencies.Output('flag','n_clicks'),
            [dash.dependencies.Input('time', 'n_intervals')]
        )
        def check(n_intervals):
            """If any of the files are changed, sets the buttom flag to 1 (a change) to intrigue py::meth:`update_graph`. 
            
            Args:
                n_intervals (int): time
            
            Returns:
                int: value of the buttom 
            
            Raises:
                dash.exceptions.PreventUpdate
                if there is no update, simply raise an exception to prevent alteration of the button value.
            """
            any_update_flag = self.update_db()
            if any_update_flag:
                return 1
            else:
                raise dash.exceptions.PreventUpdate()

    def run(self):
        """Summary
        """

        self.app.run_server(debug=True, host='127.0.0.1')
