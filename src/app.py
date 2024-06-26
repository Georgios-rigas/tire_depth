import base64
from azure.storage.blob import BlobServiceClient
import os
import io
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
from dash.exceptions import PreventUpdate
from flask import Flask, request, jsonify
import tensorflow as tf
from PIL import Image
from tensorflow.keras.models import load_model
from tensorflow.keras.applications.resnet50 import preprocess_input, ResNet50
from tensorflow.keras.layers import GlobalAveragePooling2D, Dense
from tensorflow.keras.models import Model
from tensorflow.keras.models import load_model

import logging
logging.basicConfig(level=logging.DEBUG)

def download_model_from_blob(storage_connection_string, container_name, blob_name, download_file_path):
    blob_service_client = BlobServiceClient.from_connection_string(storage_connection_string)
    blob_client = blob_service_client.get_blob_client(container=container_name, blob=blob_name)
 
    os.makedirs(os.path.dirname(download_file_path), exist_ok=True)
    with open(download_file_path, "wb") as download_file:
        download_file.write(blob_client.download_blob().readall())
 
# Use your actual storage connection string, container name, and blob name
storage_connection_string = os.getenv("STORAGE_CONNECTION_STRING")
container_name = "modelcv"
blob_name1 = "best_model.h5"
blob_name2 = "tire_or_not_best_model2.h5"

download_file_path1 = "./best_model.h5"
download_file_path2 = "./tire_or_not_best_model2.h5"
 
# Download the model file from Azure Blob Storage to the local file system
download_model_from_blob(storage_connection_string, container_name, blob_name1, download_file_path1)
download_model_from_blob(storage_connection_string, container_name, blob_name2, download_file_path2)


def load_main_model():
    base_model = ResNet50(weights='imagenet', include_top=False, input_shape=(224, 224, 3))
    x = base_model.output
    x = GlobalAveragePooling2D()(x)
    class_output = Dense(1, activation='sigmoid', name='class_output')(x)
    depth_output = Dense(128, activation='relu')(x)
    depth_output = Dense(1, activation='linear', name='depth_output')(depth_output)
    model = Model(inputs=base_model.input, outputs=[class_output, depth_output])
    model.load_weights('best_model.h5')
    return model

model = load_main_model()

model2 = load_model('tire_or_not_best_model2.h5')

app = dash.Dash(__name__, external_stylesheets=['https://codepen.io/chriddyp/pen/bWLwgP.css'])
server = app.server

app.layout = html.Div([
    html.Img(
        src='/assets/valcon.jpg',
        style={
            'height': '60px',
            'position': 'absolute',
            'top': '10px',
            'left': '10px'
        }
    ),
    html.H1('Tread Depth App', style={'textAlign': 'center', 'color': '#9932CC', 'marginTop': '40px'}),
    dcc.Upload(
        id='upload-image',
        children=html.Div(['Drag and Drop or ', html.A('Select Files')]),
        style={
            'width': '100%',
            'height': '60px',
            'lineHeight': '60px',
            'borderWidth': '2px',
            'borderStyle': 'dashed',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px auto',
            'color': '#9932CC',
            'fontSize': '20px',
        },
        multiple=False
    ),
    html.Div([
        html.Button('Open Camera', id='camera-btn', n_clicks=0, style={
            'width': '200px',
            'height': '40px',
            'borderWidth': '2px',
            'borderStyle': 'solid',
            'borderRadius': '5px',
            'textAlign': 'center',
            'margin': '10px auto',
            'color': '#BA55D3',
            'fontSize': '16px',
            'cursor': 'pointer',
            'backgroundColor': '#2F4F4F',
            'border': 'none',
            'outline': 'none',
            'display': 'block',
        }),
        html.Div(id='camera-modal', style={'margin': '10px auto'}),
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),
    html.Div(id='output-container', style={
        'textAlign': 'center',
        'marginTop': '20px',
    }, children=[
        html.Div(id='output-image-upload')
    ]),
    html.Script(src="/assets/webcam_capture.js")
], style={'backgroundColor': '#D3D3D3', 'padding': '20px', 'fontFamily': 'Open Sans, sans-serif', 'maxWidth': '800px', 'margin': '0 auto', 'position': 'relative'})
@app.callback(Output('camera-btn', 'children'),
              [Input('camera-btn', 'n_clicks')])
def toggle_camera_button(n_clicks):
    if n_clicks % 2 == 0:
        return 'Open Camera'
    else:
        return 'Capture Image'

@app.callback(Output('output-image-upload', 'children'),
              [Input('upload-image', 'contents')],
              prevent_initial_call=True)
def update_output(contents):
    if contents is None:
        logging.debug("No contents found in upload-image.")
        raise PreventUpdate

    content_string = contents.split(",")[1]
    logging.debug(f"Content string length: {len(content_string)}")

    decoded = base64.b64decode(content_string)
    image = Image.open(io.BytesIO(decoded))

    logging.info(f"Loaded image size: {image.size}")

    # Check if the uploaded image contains a tire using model2
    tire_detection_image = image.resize((224, 224))
    tire_detection_array = tf.keras.preprocessing.image.img_to_array(tire_detection_image)
    tire_detection_array = tf.expand_dims(tire_detection_array, axis=0)
    tire_detection_array = tire_detection_array / 255.0

    tire_prediction = model2.predict(tire_detection_array)
    has_tire = tire_prediction[0][0] > 0.5

    if not has_tire:
        return html.Div([
            html.Img(src=f"data:image/jpeg;base64,{content_string}", style={'maxHeight': '300px', 'padding': '10'}),
            html.Hr(),
            html.Div('No tire detected in the image', style={'color': '#9932CC', 'fontSize': '25px'}),
        ])

    image_array = tf.keras.preprocessing.image.img_to_array(image.resize((224, 224)))
    image_array = tf.expand_dims(image_array, axis=0)
    image_array = preprocess_input(image_array)

    depth_prediction = model.predict(image_array)[1][0][0]

    image_src = f"data:image/jpeg;base64,{content_string}"
    return html.Div([
        html.Img(src=image_src, style={'maxHeight': '300px', 'padding': '10'}),
        html.Hr(),
        html.Div(f'Estimated Depth: {depth_prediction:.2f} mm', style={'color': '#9932CC', 'fontSize': '25px'}),
    ])

@server.route('/capture', methods=['POST'])
def handle_capture():
    data = request.get_json()
    image_data = data['image_data']

    content_string = image_data.split(",")[1]
    decoded = base64.b64decode(content_string)
    image = Image.open(io.BytesIO(decoded))

    # Check if the captured image contains a tire using model2
    tire_detection_image = image.resize((224, 224))
    tire_detection_array = tf.keras.preprocessing.image.img_to_array(tire_detection_image)
    tire_detection_array = tf.expand_dims(tire_detection_array, axis=0)
    tire_detection_array = tire_detection_array / 255.0

    tire_prediction = model2.predict(tire_detection_array)
    has_tire = tire_prediction[0][0] > 0.5

    if not has_tire:
        return jsonify({
            'image_data': image_data,
            'predicted_depth': 'No tire detected in the image'
        })

    image_array = tf.keras.preprocessing.image.img_to_array(image.resize((224, 224)))
    image_array = tf.expand_dims(image_array, axis=0)
    image_array = preprocess_input(image_array)

    depth_prediction = model.predict(image_array)[1][0][0]

    return jsonify({
        'image_data': image_data,
        'predicted_depth': f'{depth_prediction:.2f}'
    })

if __name__ == '__main__':
    app.run_server(debug=True, port=2113)