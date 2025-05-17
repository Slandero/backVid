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
        # Verificar configuración de Cloudinary
        try:
            # Intentar una operación simple de Cloudinary
            cloudinary.uploader.upload("https://res.cloudinary.com/demo/image/upload/sample.jpg", 
                                     public_id="test_connection",
                                     overwrite=True)
            print("Conexión a Cloudinary establecida correctamente")
        except Exception as e:
            print(f"Error al conectar con Cloudinary: {str(e)}")
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
            print("Conexión a MongoDB Atlas establecida correctamente")
        except Exception as e:
            print(f"Error al conectar con MongoDB Atlas: {str(e)}")
            raise

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

    def subir_imagen_cloudinary(self, url_imagen, nombre_publico):
        """
        Sube una imagen a Cloudinary y devuelve la URL optimizada
        """
        try:
            print(f"\nIniciando subida a Cloudinary...")
            print(f"URL/Ruta de imagen: {url_imagen}")
            print(f"Nombre público: {nombre_publico}")

            # Validar la URL antes de subir
            es_valida, mensaje = self.validar_url_imagen(url_imagen)
            if not es_valida:
                raise Exception(f"URL de imagen inválida: {mensaje}")

            # Subir la imagen a Cloudinary con opciones adicionales
            upload_result = cloudinary.uploader.upload(
                url_imagen,
                public_id=nombre_publico,
                fetch_format="auto",
                quality="auto",
                resource_type="image",
                eager=[
                    {"width": 500, "height": 500, "crop": "auto", "gravity": "auto"},
                    {"width": 1000, "height": 1000, "crop": "auto", "gravity": "auto"}
                ]
            )
            
            print("Imagen subida exitosamente a Cloudinary")
            print(f"URL original: {upload_result['secure_url']}")
            
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
            
            print("URLs generadas:")
            print(f"- Optimizada: {optimize_url}")
            print(f"- Thumbnail: {thumbnail_url}")
            
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
            print(f"\nError al subir imagen a Cloudinary:")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje de error: {str(e)}")
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
            print("\nIniciando proceso de guardado de imagen...")
            
            # Preparar los datos básicos de la imagen
            imagen_data = {
                "descripcion": datos_imagen.get("descripcion", ""),
                "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "tipo_entrada": "url" if datos_imagen.get("url", "").startswith(("http://", "https://")) else "local"
            }

            # Si la imagen viene como URL o ruta local, la subimos a Cloudinary
            if "url" in datos_imagen:
                print(f"Tipo de entrada: {imagen_data['tipo_entrada']}")
                print(f"URL/Ruta de imagen: {datos_imagen['url']}")
                
                # Generar un nombre público único
                nombre_publico = f"imagen_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
                
                # Subir a Cloudinary
                cloudinary_data = self.subir_imagen_cloudinary(
                    datos_imagen["url"],
                    nombre_publico
                )
                
                # Actualizar los datos con la información de Cloudinary
                imagen_data.update({
                    "url_original": cloudinary_data["url_original"],
                    "url_optimizada": cloudinary_data["url_optimizada"],
                    "url_thumbnail": cloudinary_data["url_thumbnail"],
                    "cloudinary_id": cloudinary_data["public_id"],
                    "url_fuente": datos_imagen["url"],
                    "estado": "procesada",
                    "metadata": {
                        "formato": cloudinary_data.get("format", "desconocido"),
                        "tamaño": cloudinary_data.get("bytes", 0),
                        "ancho": cloudinary_data.get("width", 0),
                        "alto": cloudinary_data.get("height", 0)
                    }
                })
                print("Datos de Cloudinary agregados correctamente")
            else:
                print("No se proporcionó URL o ruta de imagen")
                imagen_data["estado"] = "error"
                imagen_data["error"] = "No se proporcionó URL o ruta de imagen"

            # Guardar en MongoDB
            print("\nGuardando en MongoDB...")
            resultado = self.db.imagenes.insert_one(imagen_data)
            print(f"Imagen guardada en MongoDB con ID: {resultado.inserted_id}")
            
            # Devolver el ID y los datos guardados
            return {
                "id": resultado.inserted_id,
                "datos": imagen_data
            }

        except Exception as e:
            print(f"\nError al procesar la imagen:")
            print(f"Tipo de error: {type(e).__name__}")
            print(f"Mensaje de error: {str(e)}")
            
            # Guardar el error en la base de datos
            error_data = {
                "descripcion": datos_imagen.get("descripcion", ""),
                "fecha_subida": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "estado": "error",
                "error": str(e),
                "url_fuente": datos_imagen.get("url", "")
            }
            self.db.imagenes.insert_one(error_data)
            print("Error guardado en la base de datos")
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