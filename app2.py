import re
import plotly.graph_objects as go
import dash
from dash import Dash, dcc, html, Input, Output, State, ctx
import dash_daq as daq

app = dash.Dash(__name__)
server = app.server
# Build App
fig = go.Figure()

# config options
# https://community.plotly.com/t/shapes-and-annotations-become-editable-after-using-config-key/18585
# start here for basic shape annotations:
# https://dash.plotly.com/annotations
config = {
    # 'editable': True,
    # # more edits options: https://dash.plotly.com/dash-core-components/graph
    'edits': {
        'annotationPosition': True,
        'annotationText': True,
        # 'shapePosition': True
    },
    "modeBarButtonsToAdd": [
        "drawline",
        "drawopenpath",
        "drawclosedpath",
        "drawcircle",
        "drawrect",
        "eraseshape",
        "addtext",

    ],

}
app.layout = html.Div(
    [
        # store not in use for now
        # for documentation
        # https://dash.plotly.com/dash-core-components/store
        dcc.Store(id='shape_data', data=[], storage_type='session'),
        dcc.Store(id='text_data', data=[], storage_type='session'),
        dcc.ConfirmDialog(
            id='confirm-reset',
            message='Warning! All progress wil be lost! Are you sure you want to continue?',
        ),

        html.H3("Drag and draw annotations - use the modebar to pick a different drawing tool"),

        html.Div(
            [dcc.Graph(id="fig-image", figure=fig, config=config)],
            style={
                "display": "inline-block",
                "position": "absolute",
                "left": 0,
            }, ),

        html.Div([
            # for input documentation
            # https://dash.plotly.com/dash-core-components/input
            html.Pre("Enter text 2"),
            dcc.Input(id="text-input", type='text'),
            html.Pre("Choose text font size"),
            dcc.Input(id='font-size', type="number", min=10, max=30, step=1, value=28),
            html.Pre(),
            html.Button('add text to image', id='submit-val', n_clicks=0),
            html.Pre("Clear Image"),
            html.Button('clear image', id="clean-reset", n_clicks=0),
            html.Pre('Color Picker'),
            # for colorpicker documentation
            # https://dash.plotly.com/dash-daq
            daq.ColorPicker(
                id="annotation-color-picker", label="Color Picker", value=dict(rgb=dict(r=0, g=0, b=0, a=0))
            )

        ],
            style={
                "display": "inline-block",
                "position": "absolute",
                "right": 20,
            },
        ),

    ],
)

img = "https://images.unsplash.com/photo-1453728013993-6d66e9c9123a?ixlib=rb-1.2.1&ixid" \
      "=MnwxMjA3fDB8MHxzZWFyY2h8Mnx8Zm9jdXN8ZW58MHx8MHx8&w=1000&q=80 "

img_width = 1600
img_height = 900
scale_factor = 0.5

# Add invisible scatter trace.
# This trace is added to help the autoresize logic work.
fig.add_trace(
    go.Scatter(
        x=[0, img_width * scale_factor],
        y=[0, img_height * scale_factor],
        mode="markers",
        marker_opacity=0
    )
)

# Configure axes
fig.update_xaxes(
    visible=False,
    range=[0, img_width * scale_factor]
)

fig.update_yaxes(
    visible=False,
    range=[0, img_height * scale_factor],
    # the scaleanchor attribute ensures that the aspect ratio stays constant
    scaleanchor="x"
)

# Add image
fig.add_layout_image(
    dict(
        x=0,
        sizex=img_width * scale_factor,
        y=img_height * scale_factor,
        sizey=img_height * scale_factor,
        xref="x",
        yref="y",
        opacity=0.5,
        layer="below",
        sizing="stretch",
        source=img)
)

# Configure other layout
fig.update_layout(
    width=img_width * scale_factor,
    height=img_height * scale_factor,
    margin={"l": 0, "r": 0, "t": 0, "b": 0},
)


@app.callback(
    Output("fig-image", "figure"),
    # for explanation on relayout data:
    # https://dash.plotly.com/interactive-graphing
    Input('fig-image', 'relayoutData'),
    Input("text_data", "data"),
    Input("shape_data", "data"),

)
def update_figure(relayout_data, text, shapes):
    print("b")
    print(relayout_data)
    if "dragmode" in str(relayout_data):
        fig.update_layout(relayout_data)
    elif "shape" in str(relayout_data):
        fig.layout.shapes = ()
        for i in shapes:
            fig.add_shape(i)
    elif len(fig.layout.annotations) is not len(text) or "annotations" in str(relayout_data):
        fig.layout.annotations = ()
        for i in text:
            fig.add_annotation(i)

    return fig


@app.callback(
    Output('shape_data', 'clear_data'),
    Output('text_data', 'clear_data'),
    Input('confirm-reset', 'submit_n_clicks'),
)
def clean_figure(confirm):
    fig.layout.shapes = ()
    fig.layout.annotations = ()
    return True, True


@app.callback(
    Output("text_data", "data"),
    Input("text_data", "data"),
    State('text-input', 'value'),
    State("font-size", "value"),
    Input("annotation-color-picker", "value"),
    Input('fig-image', 'relayoutData'),
    Input('submit-val', 'n_clicks'),

)
def text_annotations(text_data, text, font, color, relayout_data, submit):
    r = color['rgb']['r']
    g = color['rgb']['g']
    b = color['rgb']['b']
    a = color['rgb']['a']
    if text_data == {} or text_data is None:
        text_data = []

    if ctx.triggered_id == 'submit-val':
        print("A")
        text_data.append(Annotation(img_width / 4, img_height / 2.5, text, f'rgba({r},{g},{b},1)', font).__dict__)
    elif "annotations" in str(relayout_data):
        # using regex to find which annotation was changed
        anno_num_index = re.search(r"\d", str(relayout_data))
        i = int(str(relayout_data)[anno_num_index.start()])

        # if text content is changed "text" will be in relay data
        if "text" in str(relayout_data):

            text_data[i] = Annotation(fig.layout.annotations[i]['x'], fig.layout.annotations[i]['y'],
                                      relayout_data[f'annotations[{i}].text'], f'rgba({r},{g},{b},1)',
                                      font).__dict__

        # if text is just moved relay data wont have "text" in data
        else:
            text_data[i] = Annotation(relayout_data[f'annotations[{i}].x'], relayout_data[f'annotations[{i}].y'],
                                      fig.layout.annotations[i]['text'], f'rgba({r},{g},{b},1)', font).__dict__
    return text_data


@app.callback(
    Output("shape_data", "data"),
    Input("shape_data", "data"),
    Input("annotation-color-picker", "value"),
    Input('fig-image', 'relayoutData'),

)
def shape_annotations(shape_data, color, relayout_data):
    r = color['rgb']['r']
    g = color['rgb']['g']
    b = color['rgb']['b']
    a = color['rgb']['a']
    if shape_data == {} or shape_data is None:
        shape_data = []
    if "'shapes':" in str(relayout_data):
        print(relayout_data)
        relayout_data['shapes'][-1]["fillcolor"] = f'rgba({r},{g},{b},{a})'
        # all shapes on screen will be returned in relay data upon new shape creation.
        for i in relayout_data['shapes']:
            shape_data.append(i)

        # changing shapes
    elif "shapes[" in str(relayout_data):
        # using regex to find which shape was changed
        shape_num_index = re.search(r"\d", str(relayout_data))
        i = int(str(relayout_data)[shape_num_index.start()])

        # changing dictionary keys so we can update the shape change easily
        dictnames = list(relayout_data.keys())
        new_dict = {}
        counter = 0
        for name in dictnames:
            dictnames[counter] = name[10:]
            counter = counter + 1
        for key, n_key in zip(relayout_data.keys(), dictnames):
            new_dict[n_key] = relayout_data[key]
        new_dict["fillcolor"] = f'rgba({r},{g},{b},{a})'
        shape_data[i] = new_dict
    return shape_data


@app.callback(
    Output('confirm-reset', 'displayed'),
    Input('clean-reset', 'n_clicks'),
    Input('confirm-reset', 'submit_n_clicks')
)
def display_confirm(clean, confirm):
    if ctx.triggered_id == 'clean-reset':
        return True
    if ctx.triggered_id == 'confirm-reset':
        return False


class Annotation:
    def __init__(self, x, y, text, color, size):
        self.showarrow = False
        self.x = x
        self.y = y
        self.text = text
        self.font = dict(
            family="Courier New, monospace",
            size=size,
            color=color,

        )


if __name__ == "__main__":
    app.run_server(debug=True, host="0.0.0.0", port=8050)
