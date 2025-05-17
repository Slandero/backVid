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
    logger.info("Accediendo a la ruta raíz")
    return jsonify({
        "mensaje": "Bienvenido a la API de Proyecto Vid",
        "endpoints": {
            "registro": "/registro (POST)",
            "login": "/login (POST)",
            "logout": "/logout (POST)",
            "perfil": "/perfil (GET/PUT)",
            "imagenes": "/imagenes (GET/POST)",
            "caidas": "/caidas (GET/POST)"
        }
    })

@app.route('/test', methods=['GET'])
def test():
    logger.info("Accediendo a la ruta de prueba")
    return jsonify({"mensaje": "El servidor está funcionando correctamente"})

@app.route('/registro', methods=['POST'])
def registro():
    logger.info("Recibida petición de registro")
    try:
        data = request.get_json()
        logger.debug(f"Datos recibidos: {data}")
        
        if not data:
            logger.error("No se recibieron datos JSON")
            return jsonify({"error": "No se recibieron datos"}), 400
            
        if not all(k in data for k in ('nombre', 'email', 'password')):
            logger.error("Faltan campos requeridos")
            return jsonify({"error": "Faltan campos requeridos (nombre, email, password)"}), 400
        
        success, message = db.crear_usuario(
            data['nombre'],
            data['email'],
            data['password']
        )
        
        if success:
            logger.info(f"Usuario creado exitosamente: {data['email']}")
            return jsonify({"mensaje": message}), 201
        logger.error(f"Error al crear usuario: {message}")
        return jsonify({"error": message}), 400
    except Exception as e:
        logger.error(f"Error en registro: {str(e)}")
        return jsonify({"error": f"Error en el servidor: {str(e)}"}), 500

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    if not all(k in data for k in ('email', 'password')):
        return jsonify({"error": "Faltan campos requeridos"}), 400
    
    success, result = db.verificar_usuario(data['email'], data['password'])
    
    if success:
        session['user_email'] = data['email']
        return jsonify({
            "mensaje": "Login exitoso",
            "usuario": {
                "nombre": result['nombre'],
                "email": result['email']
            }
        })
    return jsonify({"error": result}), 401

@app.route('/logout', methods=['POST'])
def logout():
    session.pop('user_email', None)
    return jsonify({"mensaje": "Sesión cerrada"})

@app.route('/perfil', methods=['GET'])
def obtener_perfil():
    usuario = db.db.usuarios.find_one({"email": request.args.get('email')})
    if usuario:
        return jsonify({
            "nombre": usuario['nombre'],
            "email": usuario['email'],
            "fecha_registro": usuario['fecha_registro']
        })
    return jsonify({"error": "Usuario no encontrado"}), 404

@app.route('/perfil', methods=['PUT'])
def actualizar_perfil():
    data = request.get_json()
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Se requiere email como parámetro"}), 400
        
    success, message = db.actualizar_usuario(email, data)
    
    if success:
        return jsonify({"mensaje": message})
    return jsonify({"error": message}), 400

@app.route('/imagenes', methods=['POST'])
def subir_imagen():
    logger.info("Iniciando proceso de subida de imagen")
    try:
        if 'imagen' not in request.files:
            logger.error("No se encontró el archivo 'imagen' en la petición")
            return jsonify({"error": "No se envió ningún archivo"}), 400
        
        file = request.files['imagen']
        if file.filename == '':
            logger.error("Nombre de archivo vacío")
            return jsonify({"error": "No se seleccionó ningún archivo"}), 400
        
        if not allowed_file(file.filename):
            logger.error(f"Tipo de archivo no permitido: {file.filename}")
            return jsonify({"error": "Tipo de archivo no permitido"}), 400

        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            file.save(filepath)
            
            if os.path.exists(filepath):
                logger.info(f"Archivo guardado exitosamente en: {filepath}")
            else:
                raise Exception("El archivo no se guardó correctamente")
                
        except Exception as e:
            logger.error(f"Error al guardar archivo temporal: {str(e)}")
            raise

        nombre_publico = f"imagen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        try:
            cloudinary_data = db.subir_imagen_cloudinary(filepath, nombre_publico)
            
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
            
            resultado = db.guardar_imagen(imagen_data)
            
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
            if os.path.exists(filepath):
                os.remove(filepath)
                
    except Exception as e:
        logger.error(f"Error en el proceso de subida: {str(e)}")
        return jsonify({"error": f"Error al procesar la imagen: {str(e)}"}), 400

@app.route('/imagenes', methods=['GET'])
def obtener_imagenes():
    try:
        imagenes = db.obtener_imagenes()
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
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor en puerto {port}")
    logger.info("Rutas disponibles:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.methods} {rule}")
    app.run(host='0.0.0.0', port=port, debug=True) 