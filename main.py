from database import Database
import datetime

def mostrar_menu():
    print("\n=== MENÚ PRINCIPAL ===")
    print("1. Gestionar Usuarios")
    print("2. Gestionar Imágenes")
    print("3. Gestionar Caídas")
    print("4. Ver Estadísticas")
    print("5. Ver todos los datos")
    print("6. Salir")
    return input("Seleccione una opción: ")

def menu_usuarios(db):
    while True:
        print("\n=== GESTIÓN DE USUARIOS ===")
        print("1. Crear nuevo usuario")
        print("2. Buscar usuario")
        print("3. Volver al menú principal")
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            nombre = input("Nombre del usuario: ")
            email = input("Email del usuario: ")
            usuario = {
                "nombre": nombre,
                "email": email,
                "fecha_registro": datetime.datetime.now().strftime("%Y-%m-%d")
            }
            resultado = db.guardar_usuario(usuario)
            print(f"Usuario creado con ID: {resultado.inserted_id}")
        
        elif opcion == "2":
            email = input("Ingrese el email a buscar: ")
            usuario = db.obtener_usuario({"email": email})
            if usuario:
                print(f"Usuario encontrado: {usuario}")
            else:
                print("Usuario no encontrado")
        
        elif opcion == "3":
            break

def menu_imagenes(db):
    while True:
        print("\n=== GESTIÓN DE IMÁGENES ===")
        print("1. Agregar nueva imagen")
        print("2. Ver todas las imágenes")
        print("3. Buscar imagen por descripción")
        print("4. Volver al menú principal")
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            print("\nOpciones de entrada de imagen:")
            print("1. URL de imagen")
            print("2. Ruta local de imagen")
            tipo_entrada = input("Seleccione el tipo de entrada: ")
            
            if tipo_entrada == "1":
                url = input("URL de la imagen: ")
                descripcion = input("Descripción de la imagen: ")
                imagen = {
                    "url": url,
                    "descripcion": descripcion
                }
            elif tipo_entrada == "2":
                ruta = input("Ruta local de la imagen: ")
                descripcion = input("Descripción de la imagen: ")
                imagen = {
                    "url": ruta,
                    "descripcion": descripcion
                }
            else:
                print("Opción no válida")
                continue
            
            try:
                resultado = db.guardar_imagen(imagen)
                print("\n=== Imagen guardada exitosamente ===")
                print(f"ID: {resultado['id']}")
                print(f"Descripción: {resultado['datos']['descripcion']}")
                print(f"Fecha de subida: {resultado['datos']['fecha_subida']}")
                print(f"Estado: {resultado['datos']['estado']}")
                
                if resultado['datos']['estado'] == 'procesada':
                    print("\nURLs:")
                    print(f"Original: {resultado['datos']['url_original']}")
                    print(f"Optimizada: {resultado['datos']['url_optimizada']}")
                    print(f"Thumbnail: {resultado['datos']['url_thumbnail']}")
                    
                    print("\nMetadatos:")
                    print(f"Formato: {resultado['datos']['metadata']['formato']}")
                    print(f"Tamaño: {resultado['datos']['metadata']['tamaño']} bytes")
                    print(f"Dimensiones: {resultado['datos']['metadata']['ancho']}x{resultado['datos']['metadata']['alto']}")
            except Exception as e:
                print(f"Error al guardar la imagen: {str(e)}")
        
        elif opcion == "2":
            imagenes = db.obtener_imagenes()
            print(f"\nTotal de imágenes: {len(imagenes)}")
            for img in imagenes:
                print("\n" + "=" * 50)
                print(f"ID: {img['_id']}")
                print(f"Descripción: {img['descripcion']}")
                print(f"Fecha de subida: {img['fecha_subida']}")
                print(f"Estado: {img['estado']}")
                
                if img['estado'] == 'procesada':
                    print("\nURLs:")
                    print(f"Original: {img['url_original']}")
                    print(f"Optimizada: {img['url_optimizada']}")
                    print(f"Thumbnail: {img['url_thumbnail']}")
                    
                    print("\nMetadatos:")
                    print(f"Formato: {img['metadata']['formato']}")
                    print(f"Tamaño: {img['metadata']['tamaño']} bytes")
                    print(f"Dimensiones: {img['metadata']['ancho']}x{img['metadata']['alto']}")
                else:
                    print(f"Error: {img.get('error', 'Desconocido')}")
                print("=" * 50)
        
        elif opcion == "3":
            busqueda = input("Ingrese la descripción a buscar: ")
            imagenes = db.obtener_imagenes({"descripcion": {"$regex": busqueda, "$options": "i"}})
            print(f"\nImágenes encontradas: {len(imagenes)}")
            for img in imagenes:
                print("\n" + "=" * 50)
                print(f"ID: {img['_id']}")
                print(f"Descripción: {img['descripcion']}")
                print(f"Fecha de subida: {img['fecha_subida']}")
                print(f"Estado: {img['estado']}")
                
                if img['estado'] == 'procesada':
                    print("\nURLs:")
                    print(f"Original: {img['url_original']}")
                    print(f"Optimizada: {img['url_optimizada']}")
                    print(f"Thumbnail: {img['url_thumbnail']}")
                else:
                    print(f"Error: {img.get('error', 'Desconocido')}")
                print("=" * 50)
        
        elif opcion == "4":
            break

def menu_caidas(db):
    while True:
        print("\n=== GESTIÓN DE CAÍDAS ===")
        print("1. Registrar nueva caída")
        print("2. Ver todas las caídas")
        print("3. Volver al menú principal")
        opcion = input("Seleccione una opción: ")
        
        if opcion == "1":
            ubicacion = input("Ubicación de la caída: ")
            severidad = input("Severidad (baja/media/alta): ")
            detalles = input("Detalles de la caída: ")
            caida = {
                "fecha": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ubicacion": ubicacion,
                "severidad": severidad,
                "detalles": detalles
            }
            resultado = db.guardar_caida(caida)
            print(f"Caída registrada con ID: {resultado.inserted_id}")
        
        elif opcion == "2":
            caidas = db.obtener_caidas()
            print(f"\nTotal de caídas registradas: {len(caidas)}")
            for c in caidas:
                print(f"- Fecha: {c['fecha']}, Ubicación: {c['ubicacion']}, Severidad: {c['severidad']}")
        
        elif opcion == "3":
            break

def mostrar_estadisticas(db):
    print("\n=== ESTADÍSTICAS ===")
    usuarios = db.obtener_usuarios()
    imagenes = db.obtener_imagenes()
    caidas = db.obtener_caidas()
    
    print(f"Total de usuarios: {len(usuarios)}")
    print(f"Total de imágenes: {len(imagenes)}")
    print(f"Total de caídas registradas: {len(caidas)}")

def mostrar_todos_los_datos(db):
    print("\n=== DATOS ALMACENADOS ===")
    
    print("\n--- USUARIOS ---")
    usuarios = db.obtener_usuarios()
    if usuarios:
        for usuario in usuarios:
            print(f"ID: {usuario['_id']}")
            print(f"Nombre: {usuario['nombre']}")
            print(f"Email: {usuario['email']}")
            print(f"Fecha de registro: {usuario['fecha_registro']}")
            print("-" * 30)
    else:
        print("No hay usuarios registrados")
    
    print("\n--- IMÁGENES ---")
    imagenes = db.obtener_imagenes()
    if imagenes:
        for imagen in imagenes:
            print(f"ID: {imagen['_id']}")
            print(f"URL: {imagen['url']}")
            print(f"Descripción: {imagen['descripcion']}")
            print(f"Fecha de subida: {imagen['fecha_subida']}")
            print("-" * 30)
    else:
        print("No hay imágenes registradas")
    
    print("\n--- CAÍDAS ---")
    caidas = db.obtener_caidas()
    if caidas:
        for caida in caidas:
            print(f"ID: {caida['_id']}")
            print(f"Fecha: {caida['fecha']}")
            print(f"Ubicación: {caida['ubicacion']}")
            print(f"Severidad: {caida['severidad']}")
            print(f"Detalles: {caida['detalles']}")
            print("-" * 30)
    else:
        print("No hay caídas registradas")

def mostrar_estructura_datos(db):
    print("\n=== ESTRUCTURA DE DATOS EN LA BASE DE DATOS ===")
    
    # Mostrar estructura de usuarios
    print("\n--- Colección 'usuarios' ---")
    usuarios = db.obtener_usuarios()
    if usuarios:
        usuario = usuarios[0]
        print("Ejemplo de documento de usuario:")
        print(f"ID: {usuario['_id']}")
        print(f"Nombre: {usuario['nombre']}")
        print(f"Email: {usuario['email']}")
        print(f"Fecha de registro: {usuario['fecha_registro']}")
    else:
        print("No hay usuarios en la base de datos")
    
    # Mostrar estructura de imágenes
    print("\n--- Colección 'imagenes' ---")
    imagenes = db.obtener_imagenes()
    if imagenes:
        imagen = imagenes[0]
        print("Ejemplo de documento de imagen:")
        print(f"ID: {imagen['_id']}")
        print(f"Descripción: {imagen['descripcion']}")
        print(f"Fecha de subida: {imagen['fecha_subida']}")
        print(f"Tipo de entrada: {imagen['tipo_entrada']}")
        print(f"Estado: {imagen['estado']}")
        if imagen['estado'] == 'procesada':
            print("\nURLs:")
            print(f"Original: {imagen['url_original']}")
            print(f"Optimizada: {imagen['url_optimizada']}")
            print(f"Thumbnail: {imagen['url_thumbnail']}")
            print("\nMetadatos:")
            print(f"Formato: {imagen['metadata']['formato']}")
            print(f"Tamaño: {imagen['metadata']['tamaño']} bytes")
            print(f"Dimensiones: {imagen['metadata']['ancho']}x{imagen['metadata']['alto']}")
    else:
        print("No hay imágenes en la base de datos")
    
    # Mostrar estructura de caídas
    print("\n--- Colección 'caidas' ---")
    caidas = db.obtener_caidas()
    if caidas:
        caida = caidas[0]
        print("Ejemplo de documento de caída:")
        print(f"ID: {caida['_id']}")
        print(f"Fecha: {caida['fecha']}")
        print(f"Ubicación: {caida['ubicacion']}")
        print(f"Severidad: {caida['severidad']}")
        print(f"Detalles: {caida['detalles']}")
    else:
        print("No hay caídas en la base de datos")

def main():
    try:
        db = Database()
        print("Conexión a la base de datos establecida correctamente")
        
        while True:
            opcion = mostrar_menu()
            
            if opcion == "1":
                menu_usuarios(db)
            elif opcion == "2":
                menu_imagenes(db)
            elif opcion == "3":
                menu_caidas(db)
            elif opcion == "4":
                mostrar_estadisticas(db)
            elif opcion == "5":
                mostrar_todos_los_datos(db)
            elif opcion == "6":
                print("¡Hasta luego!")
                break
            else:
                print("Opción no válida")
    
    except Exception as e:
        print(f"Error al conectar con la base de datos: {str(e)}")

if __name__ == "__main__":
    main() 