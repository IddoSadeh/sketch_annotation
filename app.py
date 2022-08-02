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
        dcc.Store(id='shapes_data',data=[], storage_type='memory'),
        dcc.Store(id='text_data',data=[], storage_type='memory'),
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
            html.Pre("Enter text"),
            dcc.Input(id="text-input", type='text'),
            html.Pre("Choose text font size"),
            dcc.Input(id='font-size', type="number", min=10, max=30, step=1,value = 28),
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
    Output('confirm-reset', 'displayed'),
    Input('confirm-reset', 'submit_n_clicks'),
    Input('clean-reset', 'n_clicks'))
def display_confirm(submit, reset):
    if reset and not submit:
        return True
    if reset and submit:
        if reset > submit:
            return True
    return False


@app.callback(
    Output("fig-image", "figure"),
    Output('submit-val', 'n_clicks'),
    Output('confirm-reset', 'submit_n_clicks'),
    Output('clean-reset', 'n_clicks'),
    # for explanation on relayout data:
    # https://dash.plotly.com/interactive-graphing
    Input('fig-image', 'relayoutData'),
    State('text-input', 'value'),
    Input('submit-val', 'n_clicks'),
    Input('confirm-reset', 'submit_n_clicks'),
    Input('clean-reset', 'n_clicks'),
    Input("annotation-color-picker", "value"),
    State("font-size", "value"),
)
def save_data(relayout_data, inputText, submit_clicks, confirm, reset, color_value, font_size):
    print("new")
    # adding new text
    if submit_clicks:
        if not len(fig.layout.annotations) == submit_clicks:
            return add_text(inputText, color_value, font_size), submit_clicks, confirm, reset

    #this adds reactive color changes if the color picker was what triggered the callback
    #https://dash.plotly.com/determining-which-callback-input-changed
    if ctx.triggered_id == "annotation-color-picker":
        update_annotations(relayout_data, color_value)
        return fig, submit_clicks, confirm, reset

    # resetting image if confirm was clicked
    if confirm:
        return clean_figure(confirm)

    print(relayout_data)
    # relayout_data gives back user changes data, if it exists, update changes to figure
    if "dragmode" in str(relayout_data):
        fig.update_layout(relayout_data)
    elif relayout_data:
        print("1")
        update_annotations(relayout_data, color_value,font_size)

    return fig, submit_clicks, confirm, reset





# precondition: inputText is not none and the figure has more annotations on it than those saved in figure data
# postcondition: add inputText to figure data
def add_text(inputText, color_value, font_size=28):
    r = color_value['rgb']['r']
    g = color_value['rgb']['g']
    b = color_value['rgb']['b']
    a = color_value['rgb']['a']
    fig.add_annotation(
        text=inputText,
        showarrow=False,
        font=dict(
            family="Courier New, monospace",
            size=font_size,
            color=f'rgba({r},{g},{b},{1})',

        ),
        x=img_width / 4,
        y=img_height / 2.5,
    )
    return fig


# preconditions: relayout_data is not none
# function updates annotations for figure
def update_annotations(relayout_data, color_value='black', size=28):
    r = color_value['rgb']['r']
    g = color_value['rgb']['g']
    b = color_value['rgb']['b']
    a = color_value['rgb']['a']

# for shape layouts
# https://plotly.com/python/reference/layout/shapes/#layout-shapes-items-shape-type
    if "'shapes':" in str(relayout_data):
        if len(relayout_data['shapes']) == 0:
            fig.layout.shapes = ()
        else:
            print(color_value)
            if 'hex' in str(color_value):
                relayout_data['shapes'][-1]["line"]["color"] = color_value["hex"]
            fig.layout.shapes = ()
            # all shapes on screen will be returned in relay data upon new shape creation.
            for i in relayout_data['shapes']:
                fig.add_shape(i)
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
        if 'hex' in str(color_value):
            new_dict["line"]= dict(color=color_value["hex"])
        fig.update_shapes(new_dict, i)
# for text layout:
# https://plotly.com/python/reference/layout/annotations/
    # if text is changed, "annotations" wil be part of the relayout data
    elif "annotations" in str(relayout_data):
        fig.update_annotations(captureevents=True)
        # using regex to find which annotation was changed
        anno_num_index = re.search(r"\d", str(relayout_data))
        i = int(str(relayout_data)[anno_num_index.start()])

        # if text content is changed "text" will be in relay data
        if "text" in str(relayout_data):
            fig.update_annotations(Annotation(fig.layout.annotations[i]['x'], fig.layout.annotations[i]['y'],
                                              relayout_data[f'annotations[{i}].text'], f'rgba({r},{g},{b},1)',
                                              size).__dict__,
                                   i)

        # if text is just moved relay data wont have "text" in data
        else:
            fig.update_annotations(
                Annotation(relayout_data[f'annotations[{i}].x'], relayout_data[f'annotations[{i}].y'],
                           fig.layout.annotations[i]['text'], f'rgba({r},{g},{b},1)', size).__dict__, i)


# precondition: confirm is not none
# postcondition: all shape and text annotation data in figure is erase, all button click counters are reset
def clean_figure(confirm):
    fig.layout.shapes = ()
    fig.layout.annotations = ()
    return fig, 0, 0, 0


class Annotation:
    def __init__(self, x, y, text, color, size):
        self.x = x
        self.y = y
        self.text = text
        self.font = dict(
            family="Courier New, monospace",
            size=size,
            color=color,

        )


if __name__ == "__main__":
    app.run_server(debug=True,host="0.0.0.0", port=8050)
