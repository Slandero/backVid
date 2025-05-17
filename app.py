from flask import Flask, request, jsonify, session, render_template
from database import Database
from functools import wraps
import os
import datetime
import base64
from werkzeug.utils import secure_filename
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Clave secreta para las sesiones
db = Database()

# Configuración para archivos subidos
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return jsonify({
        "mensaje": "Bienvenido a la API de Proyecto Vid",
        "endpoints": {
            "imagenes": "/imagenes (GET/POST)",
            "caidas": "/caidas (GET/POST)"
        }
    })

@app.route('/imagenes', methods=['POST'])
def subir_imagen():
    logger.info("Iniciando proceso de subida de imagen")
    try:
        # Verificar si se envió un archivo
        logger.debug("Verificando archivos en la petición")
        logger.debug(f"Files en request: {request.files}")
        logger.debug(f"Form data: {request.form}")
        
        if 'imagen' not in request.files:
            logger.error("No se encontró el archivo 'imagen' en la petición")
            return jsonify({"error": "No se envió ningún archivo"}), 400
        
        file = request.files['imagen']
        logger.debug(f"Archivo recibido: {file.filename}")
        
        if file.filename == '':
            logger.error("Nombre de archivo vacío")
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"Tipo de archivo no permitido: {file.filename}")
            return jsonify({"error": "Tipo de archivo no permitido"}), 400

        # Guardar el archivo temporalmente
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        logger.debug(f"Guardando archivo temporalmente en: {filepath}")
        
        try:
            file.save(filepath)
            logger.info("Archivo guardado temporalmente con éxito")
        except Exception as e:
            logger.error(f"Error al guardar archivo temporal: {str(e)}")
            raise

        # Generar un nombre único para la imagen en Cloudinary
        nombre_publico = f"imagen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.debug(f"Nombre público generado: {nombre_publico}")
        
        try:
            # Subir la imagen a Cloudinary
            logger.info("Iniciando subida a Cloudinary")
            cloudinary_data = db.subir_imagen_cloudinary(filepath, nombre_publico)
            logger.info("Imagen subida exitosamente a Cloudinary")
            
            # Preparar los datos para guardar en MongoDB
            imagen_data = {
                "descripcion": request.form.get('descripcion', ''),
                "nombre_archivo": filename,
                "url_cloudinary": cloudinary_data['url_optimizada'],
                "url_thumbnail": cloudinary_data['url_thumbnail'],
                "cloudinary_id": cloudinary_data['public_id'],
                "metadata": {
                    "formato": cloudinary_data.get('format', 'desconocido'),
                    "tamaño": cloudinary_data.get('bytes', 0),
                    "ancho": cloudinary_data.get('width', 0),
                    "alto": cloudinary_data.get('height', 0)
                },
                "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            logger.debug("Guardando datos en MongoDB")
            resultado = db.guardar_imagen(imagen_data)
            logger.info("Datos guardados exitosamente en MongoDB")
            
            return jsonify({
                "mensaje": "Imagen procesada y guardada exitosamente",
                "datos": {
                    "id": str(resultado['id']),
                    "nombre_archivo": imagen_data['nombre_archivo'],
                    "url_cloudinary": imagen_data['url_cloudinary'],
                    "url_thumbnail": imagen_data['url_thumbnail'],
                    "metadata": imagen_data['metadata']
                }
            }), 201
            
        finally:
            # Limpiar: eliminar el archivo temporal
            if os.path.exists(filepath):
                logger.debug(f"Eliminando archivo temporal: {filepath}")
                os.remove(filepath)
                logger.info("Archivo temporal eliminado")
                
    except Exception as e:
        logger.error(f"Error en el proceso de subida: {str(e)}")
        logger.exception("Detalles del error:")
        return jsonify({"error": f"Error al procesar la imagen: {str(e)}"}), 400

@app.route('/imagenes', methods=['GET'])
def obtener_imagenes():
    try:
        imagenes = db.obtener_imagenes()
        # Convertir ObjectId a string para la serialización JSON
        for imagen in imagenes:
            imagen['_id'] = str(imagen['_id'])
        return jsonify({"imagenes": imagenes})
    except Exception as e:
        return jsonify({"error": f"Error al obtener imágenes: {str(e)}"}), 400

@app.route('/caidas', methods=['GET'])
def obtener_caidas():
    caidas = db.obtener_caidas()
    return jsonify({"caidas": caidas})

@app.route('/caidas', methods=['POST'])
def registrar_caida():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requieren datos de la caída"}), 400
    
    try:
        resultado = db.guardar_caida({
            **data,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        return jsonify({"mensaje": "Caída registrada exitosamente", "datos": resultado}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True, port=5000) 