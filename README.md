# backVid

## API para gestión de caídas e imágenes

Este proyecto proporciona una API para gestionar accidentes (caídas) y sus imágenes asociadas.

### Características

- Registro y autenticación de usuarios
- Registro de accidentes (caídas)
- Subida de imágenes asociadas a accidentes
- Almacenamiento de imágenes en Cloudinary
- Base de datos MongoDB para persistencia

### Endpoints principales

#### Usuarios
- `/registro` (POST): Registrar nuevo usuario
- `/login` (POST): Iniciar sesión
- `/logout` (POST): Cerrar sesión
- `/perfil` (GET/PUT): Obtener/actualizar perfil de usuario

#### Caídas/Accidentes
- `/caidas` (GET): Obtener todas las caídas con sus imágenes asociadas
- `/caidas` (POST): Registrar nueva caída (se crea con un arreglo de imágenes vacío)
- `/caidas/ID_CAIDA` (GET): Obtener una caída específica con sus imágenes

#### Imágenes
- `/imagenes` (GET): Obtener todas las imágenes
- `/imagenes?caida_id=ID_CAIDA` (GET): Obtener imágenes de una caída específica
- `/imagenes` (POST): Subir nueva imagen asociada a una caída

### Vinculación entre imágenes y accidentes

Cada imagen debe estar vinculada a un accidente específico. Para subir una imagen, se debe proporcionar el ID del accidente al que pertenece. 

#### Flujo de trabajo:

1. Registrar un accidente (caída) mediante POST a `/caidas`
2. Obtener el ID del accidente de la respuesta
3. Subir imágenes relacionadas al accidente mediante POST a `/imagenes`, incluyendo el campo `caida_id` en el formulario

Las imágenes subidas quedarán vinculadas al accidente y podrán ser consultadas junto con él.
