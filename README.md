
![ProfileTerminator](https://github.com/user-attachments/assets/3d5381c5-fee0-4656-926b-ec5bad4db590)

# ProfileTerminator

**ProfileTerminator** es una herramienta escrita en Python que permite eliminar perfiles de usuario en sistemas Windows de forma segura y eficiente, tanto del registro como del sistema de archivos, incluyendo aquellos archivos que puedan estar bloqueados por procesos en ejecución.

---

## 🛠️ **Características principales**

- Eliminación de perfiles de usuario en Windows desde el registro.
- Eliminación segura de carpetas y archivos asociados a los perfiles.
- Capacidad para tomar propiedad de archivos protegidos.
- Interfaz gráfica amigable construida con **Tkinter**.
- Progreso visual durante la eliminación de archivos.
- Detección y cierre de procesos que bloquean archivos.
- Búsqueda y filtrado de usuarios.
- Protección contra la eliminación del usuario actual.

---

## 🚀 **Requisitos**

- Python 3.8 o superior.
- Sistema operativo Windows.
- Permisos de administrador.

**Dependencias externas:** Ninguna. Se utilizan solo módulos estándar de Python.

---

## 📦 **Instalación y ejecución**

1. Clona este repositorio:
   ```bash
   git clone https://github.com/tuusuario/ProfileTerminator.git
   cd ProfileTerminator
   ```

2. Ejecuta el script principal:
   ```bash
   python ProfileTerminator.py
   ```

> **Nota:** El script requiere permisos de administrador para ejecutarse correctamente. Si no los tienes, se solicitará elevación de privilegios automáticamente.

---

## 📋 **Uso**

1. Al abrir la aplicación, se mostrará la lista de perfiles de usuario cargados en el sistema.
2. Puedes filtrar usuarios utilizando el campo de búsqueda.
3. Selecciona los usuarios que deseas eliminar.
4. Elige entre las siguientes opciones:
   - **Eliminar del Registro:** Borra el perfil del registro de Windows.
   - **Eliminar Usuario y Archivos:** Borra tanto el perfil del registro como los archivos asociados en el sistema.

---

## 📂 **Estructura del proyecto**

```
ProfileTerminator/
├── ProfileTerminator.py   # Archivo principal del proyecto
├── README.md              # Documentación del proyecto
└── LICENSE                # Licencia del proyecto
```

---

## ⚠️ **Advertencias**

- **¡Cuidado!** Esta herramienta realiza cambios permanentes en el sistema. Úsala con precaución.
- No intentes eliminar el perfil del usuario actualmente conectado, ya que la aplicación bloqueará esta acción.

---

## 🛡️ **Seguridad**

**ProfileTerminator** incluye medidas de seguridad para:
- Solicitar permisos de administrador.
- Prevenir la eliminación del perfil actual del usuario.
- Manejar archivos bloqueados por procesos activos.

---

## 📝 **Licencia**

Este proyecto está licenciado bajo la [Licencia MIT](LICENSE).

---
