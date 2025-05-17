from pymongo import MongoClient
from dotenv import load_dotenv
import os
import cloudinary
import cloudinary.uploader
from cloudinary.utils import cloudinary_url
import datetime
import requests
from urllib.parse import urlparse
import mimetypes
from werkzeug.security import generate_password_hash, check_password_hash
import logging

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Cargar variables de entorno
load_dotenv()

# Configuración de Cloudinary
cloudinary.config( 
    cloud_name = "dw3zlzw0j", 
    api_key = "482461732829777", 
    api_secret = "ffhkAl8LvO21CbdBlX29FLxNeWg",  # API Secret directamente
    secure = True
)

class Database:
    def __init__(self):
        logger.info("Inicializando conexión a Cloudinary y MongoDB")
        # Verificar configuración de Cloudinary
        try:
            # Intentar una operación simple de Cloudinary
            cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/sample.jpg", 
                                     public_id="test_connection",
                                     overwrite=True)
            logger.info("Conexión a Cloudinary establecida correctamente")
        except Exception as e:
            logger.error(f"Error al conectar con Cloudinary: {str(e)}")
            print("Por favor, verifica que las credenciales de Cloudinary sean correctas")
            raise

        # URI de MongoDB Atlas
        self.uri = "mongodb+srv://admin:admin@clustervid.tbuuqia.mongodb.net/"
        # Opciones de conexión
        self.client = MongoClient(
            self.uri,
            serverSelectionTimeoutMS=5000,
            connectTimeoutMS=10000,
            socketTimeoutMS=10000
        )
        self.db = self.client['proyecto_vid']
        
        # Verificar la conexión
        try:
            self.client.server_info()
            logger.info("Conexión a MongoDB Atlas establecida correctamente")
        except Exception as e:
            logger.error(f"Error al conectar con MongoDB Atlas: {str(e)}")
            raise

    def crear_usuario(self, nombre, email, password, telefono):
        """
        Crea un nuevo usuario con contraseña encriptada
        """
        try:
            # Verificar si el email ya existe
            if self.db.usuarios.find_one({"email": email}):
                return False, "El email ya está registrado"

            # Crear el usuario con contraseña encriptada
            usuario = {
                "nombre": nombre,
                "email": email,
                "password": generate_password_hash(password),
                "telefono": telefono,
                "fecha_registro": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            resultado = self.db.usuarios.insert_one(usuario)
            return True, f"Usuario creado con ID: {resultado.inserted_id}"
        except Exception as e:
            return False, f"Error al crear usuario: {str(e)}"

    def verificar_usuario(self, email, password):
        """
        Verifica las credenciales de un usuario
        """
        try:
            usuario = self.db.usuarios.find_one({"email": email})
            if usuario and check_password_hash(usuario["password"], password):
                return True, usuario
            return False, "Credenciales inválidas"
        except Exception as e:
            return False, f"Error al verificar usuario: {str(e)}"

    def actualizar_usuario(self, email, datos):
        """
        Actualiza los datos de un usuario
        """
        try:
            # Verificar si el usuario existe
            if not self.db.usuarios.find_one({"email": email}):
                return False, "Usuario no encontrado"
            
            # Preparar los datos a actualizar
            datos_actualizar = {}
            if 'nombre' in datos:
                datos_actualizar['nombre'] = datos['nombre']
            if 'password' in datos:
                datos_actualizar['password'] = generate_password_hash(datos['password'])
            if 'telefono' in datos:
                datos_actualizar['telefono'] = datos['telefono']
            
            if not datos_actualizar:
                return False, "No hay datos para actualizar"
            
            # Actualizar el usuario
            self.db.usuarios.update_one(
                {"email": email},
                {"$set": datos_actualizar}
            )
            return True, "Usuario actualizado exitosamente"
        except Exception as e:
            return False, f"Error al actualizar usuario: {str(e)}"

    def validar_url_imagen(self, url):
        """
        Valida si una URL es una imagen válida
        """
        try:
            # Verificar si es una URL válida
            parsed = urlparse(url)
            if not all([parsed.scheme, parsed.netloc]):
                return False, "URL inválida"

            # Verificar si la URL es accesible
            response = requests.head(url, allow_redirects=True)
            if response.status_code != 200:
                return False, f"URL no accesible (código {response.status_code})"

            # Verificar el tipo de contenido
            content_type = response.headers.get('content-type', '')
            if not content_type.startswith('image/'):
                return False, f"URL no es una imagen (tipo: {content_type})"

            return True, "URL válida"
        except Exception as e:
            return False, f"Error al validar URL: {str(e)}"

    def subir_imagen_cloudinary(self, ruta_archivo, nombre_publico):
        """
        Sube una imagen a Cloudinary y devuelve la URL optimizada
        """
        try:
            logger.info(f"Iniciando subida a Cloudinary")
            logger.debug(f"Ruta de archivo: {ruta_archivo}")
            logger.debug(f"Nombre público: {nombre_publico}")

            # Verificar que el archivo existe
            if not os.path.exists(ruta_archivo):
                logger.error(f"El archivo no existe: {ruta_archivo}")
                raise Exception(f"El archivo no existe: {ruta_archivo}")

            # Subir la imagen a Cloudinary con opciones adicionales
            logger.debug("Iniciando upload a Cloudinary")
            upload_result = cloudinary.uploader.upload(
                ruta_archivo,
                public_id=nombre_publico,
                fetch_format="auto",
                quality="auto",
                resource_type="image",
                eager=[
                    {"width": 500, "height": 500, "crop": "auto", "gravity": "auto"},
                    {"width": 1000, "height": 1000, "crop": "auto", "gravity": "auto"}
                ]
            )
            
            logger.info("Imagen subida exitosamente a Cloudinary")
            logger.debug(f"URL original: {upload_result['secure_url']}")
            
            # Obtener URL optimizada
            optimize_url, _ = cloudinary_url(
                nombre_publico,
                fetch_format="auto",
                quality="auto"
            )
            
            # Obtener URL para la versión de 500x500
            thumbnail_url, _ = cloudinary_url(
                nombre_publico,
                width=500,
                height=500,
                crop="auto",
                gravity="auto"
            )
            
            logger.debug("URLs generadas:")
            logger.debug(f"- Optimizada: {optimize_url}")
            logger.debug(f"- Thumbnail: {thumbnail_url}")
            
            return {
                "url_original": upload_result["secure_url"],
                "url_optimizada": optimize_url,
                "url_thumbnail": thumbnail_url,
                "public_id": nombre_publico,
                "format": upload_result.get("format", "desconocido"),
                "bytes": upload_result.get("bytes", 0),
                "width": upload_result.get("width", 0),
                "height": upload_result.get("height", 0),
                "created_at": upload_result.get("created_at", ""),
                "resource_type": upload_result.get("resource_type", "image")
            }
        except Exception as e:
            logger.error(f"Error al subir imagen a Cloudinary:")
            logger.error(f"Tipo de error: {type(e).__name__}")
            logger.error(f"Mensaje de error: {str(e)}")
            logger.exception("Detalles del error:")
            raise

    def guardar_usuario(self, datos_usuario):
        """
        Guarda los datos de un usuario en la colección 'usuarios'
        """
        return self.db.usuarios.insert_one(datos_usuario)

    def guardar_imagen(self, datos_imagen):
        """
        Guarda la URL y datos de una imagen en la colección 'imagenes'
        """
        try:
            logger.info("Iniciando proceso de guardado de imagen en MongoDB")
            logger.debug(f"Datos a guardar: {datos_imagen}")
            
            resultado = self.db.imagenes.insert_one(datos_imagen)
            logger.info(f"Imagen guardada en MongoDB con ID: {resultado.inserted_id}")
            
            return {
                "id": resultado.inserted_id,
                "datos": datos_imagen
            }
        except Exception as e:
            logger.error(f"Error al guardar imagen en MongoDB: {str(e)}")
            logger.exception("Detalles del error:")
            raise

    def guardar_caida(self, datos_caida):
        """
        Guarda los datos de una caída en la colección 'caidas'
        """
        return self.db.caidas.insert_one(datos_caida)

    def obtener_usuario(self, filtro):
        """
        Obtiene un usuario basado en un filtro
        """
        return self.db.usuarios.find_one(filtro)

    def obtener_usuarios(self, filtro=None):
        """
        Obtiene todos los usuarios que coincidan con el filtro
        """
        if filtro is None:
            filtro = {}
        return list(self.db.usuarios.find(filtro))

    def obtener_imagenes(self, filtro=None):
        """
        Obtiene todas las imágenes que coincidan con el filtro
        """
        if filtro is None:
            filtro = {}
        return list(self.db.imagenes.find(filtro))

    def obtener_caidas(self, filtro=None):
        """
        Obtiene todas las caídas que coincidan con el filtro
        """
        if filtro is None:
            filtro = {}
        return list(self.db.caidas.find(filtro)) 