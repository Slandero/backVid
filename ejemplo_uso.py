from database import Database

# Crear una instancia de la base de datos
db = Database()

# Ejemplo de guardar un usuario
usuario = {
    "nombre": "Juan Pérez",
    "email": "juan@ejemplo.com",
    "fecha_registro": "2024-03-20"
}
resultado_usuario = db.guardar_usuario(usuario)
print(f"Usuario guardado con ID: {resultado_usuario.inserted_id}")

# Ejemplo de guardar una imagen
imagen = {
    "url": "https://ejemplo.com/imagen.jpg",
    "descripcion": "Imagen de ejemplo",
    "fecha_subida": "2024-03-20"
}
resultado_imagen = db.guardar_imagen(imagen)
print(f"Imagen guardada con ID: {resultado_imagen.inserted_id}")

# Ejemplo de guardar una caída
caida = {
    "fecha": "2024-03-20",
    "ubicacion": "Sala 101",
    "severidad": "media",
    "detalles": "Caída detectada por el sensor"
}
resultado_caida = db.guardar_caida(caida)
print(f"Caída guardada con ID: {resultado_caida.inserted_id}")

# Ejemplo de obtener datos
usuario_encontrado = db.obtener_usuario({"email": "juan@ejemplo.com"})
print(f"Usuario encontrado: {usuario_encontrado}")

todas_imagenes = db.obtener_imagenes()
print(f"Total de imágenes: {len(todas_imagenes)}")

todas_caidas = db.obtener_caidas()
print(f"Total de caídas: {len(todas_caidas)}") 