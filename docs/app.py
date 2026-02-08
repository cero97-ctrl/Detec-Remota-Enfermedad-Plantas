from flask import Flask, request, render_template, send_from_directory
import os
import requests
from pprint import pprint

app = Flask(__name__)

# --- Configuración ---
# Seguridad: Leer API KEY desde variable de entorno o usar un valor por defecto seguro
API_KEY = os.environ.get("PLANTNET_API_KEY", "TU_API_KEY_AQUI")
PROJECT = "all"
API_ENDPOINT = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"

# Carpetas: Usar 'static' es el estándar de Flask para archivos servidos públicamente
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Estado Global
# Nota: Mantenemos esto simple, pero recuerda que no es ideal para múltiples usuarios simultáneos
current_state = {
    "plant_type": "Esperando identificación...",
    "image_filename": "image.jpg"
}

def ensure_upload_folder():
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route("/identify", methods=["POST"])
def identify_plant():
    global current_state
    
    # 1. Guardar la imagen recibida
    image_data = request.data
    filename = current_state["image_filename"]
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    ensure_upload_folder()
    with open(file_path, 'wb') as f:
        f.write(image_data)
    
    # 2. Consultar API de PlantNet
    files = {'images': open(file_path, 'rb')}
    
    try:
        response = requests.post(API_ENDPOINT, files=files)
        
        if response.status_code == 200:
            json_result = response.json()
            best_match = json_result.get('bestMatch', 'No identificado')
            current_state["plant_type"] = best_match
            pprint(f"Identificado: {best_match}")
        else:
            current_state["plant_type"] = f"Error API: {response.status_code}"
            pprint(response.text)
    except Exception as e:
        current_state["plant_type"] = "Error de conexión"
        print(e)

    return render_template("index.html", plant_type=current_state["plant_type"])

@app.route("/")
def index():
    return render_template("index.html", plant_type=current_state["plant_type"])

# Ruta de compatibilidad: Si el HTML pide /templates/image.jpg, servimos desde static
@app.route('/templates/<path:filename>')
def serve_image_compatibility(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == "__main__":
    ensure_upload_folder()
    app.run(host="0.0.0.0", port=33)