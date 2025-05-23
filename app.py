from flask import Flask, request, jsonify, session, render_template
from database import Database
from functools import wraps
import os
import datetime
import base64
from werkzeug.utils import secure_filename
import logging
from flask_cors import CORS
from bson.objectid import ObjectId  # Importar ObjectId para manejar IDs de MongoDB

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# Configurar CORS para permitir todas las solicitudes
CORS(app, resources={r"/*": {"origins": "*"}})
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
            "registro": "/registro (POST) - Registrar nuevo usuario",
            "login": "/login (POST) - Iniciar sesión",
            "logout": "/logout (POST) - Cerrar sesión",
            "perfil": "/perfil (GET/PUT) - Obtener/actualizar perfil",
            "imagenes": "/imagenes (GET/POST) - Obtener todas/subir nueva imagen",
            "imagenes_filtradas": "/imagenes?caida_id=ID_CAIDA (GET) - Obtener imágenes de una caída específica",
            "caidas": "/caidas (GET/POST) - Obtener todas/registrar nueva caída",
            "caida_especifica": "/caidas/ID_CAIDA (GET) - Obtener una caída específica con sus imágenes"
        },
        "documentacion": {
            "subir_imagen": "Para subir una imagen, se debe enviar un formulario con los campos 'imagen' (archivo) y 'caida_id' (obligatorio)",
            "registrar_caida": "Para registrar una caída, se debe enviar un JSON con los datos de la caída. Se crea con un arreglo de imágenes vacío"
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
            
        if not all(k in data for k in ('nombre', 'email', 'password', 'telefono')):
            logger.error("Faltan campos requeridos")
            return jsonify({"error": "Faltan campos requeridos (nombre, email, password, telefono)"}), 400
        
        success, message = db.crear_usuario(
            data['nombre'],
            data['email'],
            data['password'],
            data['telefono']
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
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Se requiere el email como parámetro"}), 400
        
    usuario = db.db.usuarios.find_one({"email": email})
    if usuario:
        return jsonify({
            "nombre": usuario['nombre'],
            "email": usuario['email'],
            "telefono": usuario.get('telefono', ''),
            "fecha_registro": usuario['fecha_registro']
        })
    return jsonify({"error": "Usuario no encontrado"}), 404

@app.route('/perfil', methods=['PUT'])
def actualizar_perfil():
    email = request.args.get('email')
    if not email:
        return jsonify({"error": "Se requiere el email como parámetro"}), 400
        
    data = request.get_json()
    success, message = db.actualizar_usuario(email, data)
    
    if success:
        return jsonify({"mensaje": message})
    return jsonify({"error": message}), 400

@app.route('/imagenes', methods=['POST'])
def subir_imagen():
    logger.info("Iniciando proceso de subida de imagen")
    try:
        # Verificar que se proporcionó un ID de caída
        caida_id = request.form.get('caida_id')
        if not caida_id:
            logger.error("No se proporcionó ID de caída")
            return jsonify({"error": "Se requiere el ID de la caída asociada"}), 400

        # Verificar que la caída existe
        caida = db.db.caidas.find_one({"_id": ObjectId(caida_id)})
        if not caida:
            logger.error(f"Caída con ID {caida_id} no encontrada")
            return jsonify({"error": "La caída especificada no existe"}), 404

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
                "caida_id": caida_id,  # Vinculación con la caída
                "metadata": {
                    "formato": cloudinary_data.get('format', 'desconocido'),
                    "tamaño": cloudinary_data.get('bytes', 0),
                    "ancho": cloudinary_data.get('width', 0),
                    "alto": cloudinary_data.get('height', 0)
                },
                "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            resultado = db.guardar_imagen(imagen_data)
            
            # Actualizar la caída con referencia a la imagen
            db.db.caidas.update_one(
                {"_id": ObjectId(caida_id)},
                {"$push": {"imagenes": str(resultado['id'])}}
            )
            
            return jsonify({
                "mensaje": "Imagen procesada y guardada exitosamente",
                "datos": {
                    "id": str(resultado['id']),
                    "caida_id": caida_id,
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
        # Obtener parámetros de filtrado
        caida_id = request.args.get('caida_id')
        
        # Construir filtro basado en los parámetros
        filtro = {}
        if caida_id:
            filtro['caida_id'] = caida_id
            
        imagenes = db.obtener_imagenes(filtro)
        for imagen in imagenes:
            imagen['_id'] = str(imagen['_id'])
            
        return jsonify({
            "imagenes": imagenes,
            "total": len(imagenes),
            "filtros_aplicados": {"caida_id": caida_id} if caida_id else {}
        })
    except Exception as e:
        return jsonify({"error": f"Error al obtener imágenes: {str(e)}"}), 400

@app.route('/caidas', methods=['GET'])
def obtener_caidas():
    try:
        caidas = db.obtener_caidas()
        caidas_serializadas = []
        
        for caida in caidas:
            caida['_id'] = str(caida['_id'])
            
            # Verificar si la caída tiene imágenes asociadas
            if 'imagenes' in caida and caida['imagenes']:
                # Recuperar información de las imágenes asociadas
                imagenes_info = []
                for imagen_id in caida['imagenes']:
                    try:
                        imagen = db.db.imagenes.find_one({"_id": ObjectId(imagen_id)})
                        if imagen:
                            imagen['_id'] = str(imagen['_id'])
                            imagenes_info.append({
                                "id": imagen['_id'],
                                "url_thumbnail": imagen.get('url_thumbnail', ''),
                                "url_cloudinary": imagen.get('url_cloudinary', ''),
                                "descripcion": imagen.get('descripcion', '')
                            })
                    except Exception as e:
                        logger.error(f"Error al obtener imagen {imagen_id}: {str(e)}")
                
                caida['imagenes_info'] = imagenes_info
            
            caidas_serializadas.append(caida)
            
        return jsonify({"caidas": caidas_serializadas})
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/caidas', methods=['POST'])
def registrar_caida():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Se requieren datos de la caída"}), 400
    
    try:
        caida_data = {
            **data,
            "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "imagenes": []  # Inicializar arreglo vacío para almacenar referencias a imágenes
        }
        resultado = db.guardar_caida(caida_data)
        
        caida_guardada = {
            "mensaje": "Caída registrada exitosamente",
            "datos": {
                "id": str(resultado.inserted_id),  # Devolver el ID de la caída
                "tipo": caida_data.get("tipo"),
                "descripcion": caida_data.get("descripcion"),
                "ubicacion": caida_data.get("ubicacion"),
                "fecha": caida_data.get("fecha"),
                "imagenes": []
            }
        }
        
        return jsonify(caida_guardada), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/caidas/<caida_id>', methods=['GET'])
def obtener_caida(caida_id):
    try:
        # Buscar la caída por su ID
        try:
            caida = db.db.caidas.find_one({"_id": ObjectId(caida_id)})
        except Exception as e:
            return jsonify({"error": f"ID de caída inválido: {str(e)}"}), 400
            
        if not caida:
            return jsonify({"error": "Caída no encontrada"}), 404
            
        # Convertir _id a string para serialización JSON
        caida['_id'] = str(caida['_id'])
        
        # Verificar si la caída tiene imágenes asociadas
        if 'imagenes' in caida and caida['imagenes']:
            # Recuperar información de las imágenes asociadas
            imagenes_info = []
            for imagen_id in caida['imagenes']:
                try:
                    imagen = db.db.imagenes.find_one({"_id": ObjectId(imagen_id)})
                    if imagen:
                        imagen['_id'] = str(imagen['_id'])
                        imagenes_info.append({
                            "id": imagen['_id'],
                            "url_thumbnail": imagen.get('url_thumbnail', ''),
                            "url_cloudinary": imagen.get('url_cloudinary', ''),
                            "descripcion": imagen.get('descripcion', '')
                        })
                except Exception as e:
                    logger.error(f"Error al obtener imagen {imagen_id}: {str(e)}")
            
            caida['imagenes_info'] = imagenes_info
        
        return jsonify({"caida": caida})
    except Exception as e:
        return jsonify({"error": f"Error al obtener caída: {str(e)}"}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    logger.info(f"Iniciando servidor en puerto {port}")
    logger.info("Rutas disponibles:")
    for rule in app.url_map.iter_rules():
        logger.info(f"{rule.endpoint}: {rule.methods} {rule}")
    app.run(host='0.0.0.0', port=port, debug=True) 