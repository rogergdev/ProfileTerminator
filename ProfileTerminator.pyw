import sys
import os
import shutil
import subprocess
import winreg
import ctypes
import ctypes.wintypes
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

if not is_admin():
    ctypes.windll.shell32.ShellExecuteW(
        None,
        "runas",
        sys.executable,
        __file__,
        None,
        1
    )
    sys.exit(0)

WTS_CURRENT_SERVER_HANDLE = 0
WTSUserName = 5

wtsapi32 = ctypes.windll.wtsapi32
kernel32 = ctypes.windll.kernel32

WTSQuerySessionInformationW = wtsapi32.WTSQuerySessionInformationW
WTSFreeMemory = wtsapi32.WTSFreeMemory
WTSGetActiveConsoleSessionId = kernel32.WTSGetActiveConsoleSessionId

def get_console_active_user():
    session_id = WTSGetActiveConsoleSessionId()
    if session_id == 0xFFFFFFFF:
        return None

    ppBuffer = ctypes.c_void_p()
    bytesReturned = ctypes.wintypes.DWORD()

    ret = WTSQuerySessionInformationW(
        WTS_CURRENT_SERVER_HANDLE,
        session_id,
        WTSUserName,
        ctypes.byref(ppBuffer),
        ctypes.byref(bytesReturned)
    )
    if not ret:
        return None

    user_name = ctypes.wstring_at(ppBuffer)
    WTSFreeMemory(ppBuffer)
    return user_name if user_name else None

def tomar_propiedad(ruta):
    try:
        takeown_cmd = ["takeown", "/f", ruta, "/r", "/d", "y"]
        subprocess.run(takeown_cmd, shell=True, check=True)

        icacls_cmd = ["icacls", ruta, "/grant", "Administrators:F", "/t"]
        subprocess.run(icacls_cmd, shell=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ADVERTENCIA] No se pudo cambiar propiedad de '{ruta}': {e}")

def intentar_matar_proceso_archivo(item):
    base_name = os.path.basename(item)
    if not base_name:
        return False
    cmd = ["taskkill", "/F", "/IM", base_name]
    try:
        subprocess.run(cmd, check=True, capture_output=True)
        return True
    except Exception as e:
        print("[ADVERTENCIA] No se logró matar proceso:", e)
        return False

def manual_remove_with_progress(path, progress_window, progress_bar):
    all_items = []
    for root, dirs, files in os.walk(path):
        for f in files:
            full_path = os.path.join(root, f)
            all_items.append(full_path)
        for d in dirs:
            full_path = os.path.join(root, d)
            all_items.append(full_path)

    all_items.sort(key=lambda p: len(p), reverse=True)

    total_count = len(all_items) + 1
    progress_bar["maximum"] = total_count
    current_count = 0

    for item in all_items:
        current_count += 1
        progress_bar["value"] = current_count
        progress_bar.update_idletasks()
        progress_window.update()

        try:
            if os.path.isfile(item) or os.path.islink(item):
                os.remove(item)
            else:
                os.rmdir(item)
        except PermissionError as pe:
            resp = messagebox.askyesno(
                "Archivo Bloqueado",
                f"No se pudo eliminar: {item}\n{pe}\n\n"
                "¿Deseas intentar matar el proceso que lo bloquea?"
            )
            if resp:
                ok = intentar_matar_proceso_archivo(item)
                if ok:
                    try:
                        if os.path.isfile(item) or os.path.islink(item):
                            os.remove(item)
                        else:
                            os.rmdir(item)
                    except Exception as e2:
                        print(f"[ADVERTENCIA] Reintento falló: {e2}")
                else:
                    print("[ADVERTENCIA] Proceso no se pudo matar.")
            else:
                print("[INFO] Se omitió el archivo bloqueado.")
        except Exception as e:
            print(f"[ADVERTENCIA] Error eliminando {item}: {e}")

    if os.path.exists(path):
        current_count += 1
        progress_bar["value"] = current_count
        progress_bar.update_idletasks()
        progress_window.update()

        try:
            os.rmdir(path)
        except Exception as e:
            print(f"[ADVERTENCIA] Error eliminando la carpeta base '{path}': {e}")

USUARIOS_CARGADOS = []
FILTRO_ACTUAL = ""

def listar_usuarios():
    usuario_consola = get_console_active_user() or os.getlogin()
    lista = []
    key_path = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList"

    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, key_path) as key:
            count = winreg.QueryInfoKey(key)[0]
            for i in range(count):
                subkey_name = winreg.EnumKey(key, i)
                with winreg.OpenKey(key, subkey_name) as subkey:
                    try:
                        profile_path = winreg.QueryValueEx(subkey, "ProfileImagePath")[0]
                        nombre_usuario = profile_path.split("\\")[-1]
                        if nombre_usuario not in [
                            "systemprofile", "LocalService", "NetworkService", "defaultuser0"
                        ]:
                            lista.append((nombre_usuario, profile_path, subkey_name))
                    except FileNotFoundError:
                        pass
    except Exception as e:
        messagebox.showerror("Error", f"No se pudieron listar los usuarios: {str(e)}")

    return lista, usuario_consola

def eliminar_usuario():
    seleccionados = lista_usuarios.curselection()
    if not seleccionados:
        messagebox.showwarning("Advertencia", "No hay ningún usuario seleccionado.")
        return

    for idx in reversed(seleccionados):
        texto_item = lista_usuarios.get(idx)
        if "[Usuario Actual]" in texto_item:
            messagebox.showwarning("Advertencia", "No se puede eliminar el usuario actual.")
            continue

        user = texto_item.split(" ")[0]

        for nombre, path, sid in USUARIOS_CARGADOS:
            if nombre == user:
                try:
                    clave = rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}"
                    winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, clave)
                    print(f"[INFO] Usuario '{user}' eliminado del registro.")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar el usuario '{user}': {str(e)}")
    messagebox.showinfo("Éxito", "Operación de borrado del registro finalizada.")
    actualizar_lista()

def eliminar_usuario_y_archivos():
    seleccionados = lista_usuarios.curselection()
    if not seleccionados:
        messagebox.showwarning("Advertencia", "No hay ningún usuario seleccionado.")
        return

    for idx in reversed(seleccionados):
        texto_item = lista_usuarios.get(idx)
        if "[Usuario Actual]" in texto_item:
            messagebox.showwarning("Advertencia", "No se puede eliminar el usuario actual.")
            continue

        user = texto_item.split(" ")[0]

        for nombre, profile_path, sid in USUARIOS_CARGADOS:
            if nombre == user:
                try:
                    clave = rf"SOFTWARE\Microsoft\Windows NT\CurrentVersion\ProfileList\{sid}"
                    winreg.DeleteKey(winreg.HKEY_LOCAL_MACHINE, clave)

                    if os.path.exists(profile_path):
                        tomar_propiedad(profile_path)
                        progress_window = tk.Toplevel()
                        progress_window.title("Eliminando carpeta...")
                        progress_window.geometry("400x100")
                        progress_window.resizable(False, False)

                        lbl = tk.Label(progress_window, text=f"Eliminando '{user}'...", font=("Segoe UI", 11))
                        lbl.pack(pady=10)

                        progress_bar = ttk.Progressbar(
                            progress_window,
                            orient="horizontal",
                            length=300,
                            mode="determinate",
                            style="App.Horizontal.TProgressbar"
                        )
                        progress_bar.pack(pady=5)

                        manual_remove_with_progress(profile_path, progress_window, progress_bar)
                        progress_window.destroy()

                        messagebox.showinfo(
                            "Éxito",
                            f"Usuario '{user}' y carpeta eliminados (archivos bloqueados se omiten)."
                        )
                    else:
                        messagebox.showwarning(
                            "Advertencia",
                            f"No se encontró la carpeta de perfil: {profile_path}"
                        )

                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo eliminar '{user}' y sus archivos: {str(e)}")

    actualizar_lista()

def actualizar_lista():
    lista_usuarios.delete(0, tk.END)

    usuarios_consola = [u[0] for u in USUARIOS_CARGADOS]

    for (nombre_usuario, _, _) in USUARIOS_CARGADOS:
        if FILTRO_ACTUAL.strip():
            if FILTRO_ACTUAL.lower() not in nombre_usuario.lower():
                continue

        if nombre_usuario.lower() == USUARIO_ACTUAL.lower():
            lista_usuarios.insert(tk.END, f"{nombre_usuario} [Usuario Actual]")
        else:
            lista_usuarios.insert(tk.END, nombre_usuario)

class HoverButton(ttk.Button):
    def __init__(self, master=None, text="", command=None):
        super().__init__(master, text=text, command=command, style="App.TButton")
        self.default_style = "App.TButton"
        self.hover_style = "AppHover.TButton"
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def on_enter(self, event):
        self.configure(style=self.hover_style)

    def on_leave(self, event):
        self.configure(style=self.default_style)

def crear_gradiente_fondo(canvas, width, height, color1, color2):
    steps = max(1, height)
    r1, g1, b1 = canvas.winfo_rgb(color1)
    r2, g2, b2 = canvas.winfo_rgb(color2)

    r_ratio = (r2 - r1) / steps
    g_ratio = (g2 - g1) / steps
    b_ratio = (b2 - b1) / steps

    for i in range(height):
        nr = int(r1 + r_ratio * i)
        ng = int(g1 + g_ratio * i)
        nb = int(b1 + b_ratio * i)
        hex_color = f"#{nr>>8:02x}{ng>>8:02x}{nb>>8:02x}"
        canvas.create_line(0, i, width, i, fill=hex_color)

USUARIO_ACTUAL = ""
entry_filtro = None

def main():
    global USUARIOS_CARGADOS, USUARIO_ACTUAL, entry_filtro

    PRIMARY_PURPLE = "#6C33A3"
    NEON_GREEN = "#7FFF00"
    DARK_BG = "#1B1B2F"

    root = tk.Tk()
    root.title("ProfileTerminator")
    root.geometry("900x650")
    root.resizable(False, False)

    w, h = 900, 650
    bg_canvas = tk.Canvas(root, width=w, height=h, highlightthickness=0)
    bg_canvas.place(x=0, y=0)
    crear_gradiente_fondo(bg_canvas, w, h, DARK_BG, "#3c2b47")

    style = ttk.Style()
    style.theme_use("clam")

    style.configure(
        "App.TButton",
        font=("Segoe UI", 11, "bold"),
        foreground=PRIMARY_PURPLE,
        padding=10,
        relief="flat",
        borderwidth=0
    )
    style.configure(
        "AppHover.TButton",
        font=("Segoe UI", 11, "bold"),
        foreground="#000000",
        background=NEON_GREEN,
        padding=10,
        relief="flat",
        borderwidth=0
    )

    style.configure(
        "App.Horizontal.TProgressbar",
        troughcolor="#3f3f4e",
        background=PRIMARY_PURPLE,
        bordercolor="#000000",
        lightcolor="#000000",
        darkcolor="#000000"
    )

    main_frame = tk.Frame(root, bg="#000000")
    main_frame.place(relx=0.5, rely=0.5, anchor=tk.CENTER)

    titulo = tk.Label(
        main_frame,
        text="PROFILE TERMINATOR",
        font=("Segoe UI Black", 20),
        fg=NEON_GREEN,
        bg="#000000"
    )
    titulo.pack(pady=20)

    filtro_frame = tk.Frame(main_frame, bg="#000000")
    filtro_frame.pack(pady=10)

    tk.Label(
        filtro_frame,
        text="Buscar usuario:",
        font=("Segoe UI", 11),
        fg="#dddddd",
        bg="#000000"
    ).pack(side=tk.LEFT)

    entry_filtro = tk.Entry(
        filtro_frame,
        font=("Consolas", 12),
        width=20
    )
    entry_filtro.pack(side=tk.LEFT, padx=5)

    def filtrar_usuarios():
        global FILTRO_ACTUAL
        FILTRO_ACTUAL = entry_filtro.get().strip()
        actualizar_lista()

    btn_filtro = HoverButton(
        filtro_frame,
        text="Filtrar",
        command=filtrar_usuarios
    )
    btn_filtro.pack(side=tk.LEFT, padx=5)

    frame_lista = tk.Frame(main_frame, bg="#000000")
    frame_lista.pack(pady=10)

    scrollbar = ttk.Scrollbar(frame_lista, orient="vertical")
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    global lista_usuarios
    lista_usuarios = tk.Listbox(
        frame_lista,
        width=60,
        height=12,
        font=("Consolas", 12),
        bg="#2f2f40",
        fg=NEON_GREEN,
        selectbackground=PRIMARY_PURPLE,
        selectforeground="#ffffff",
        highlightthickness=1,
        relief="flat",
        yscrollcommand=scrollbar.set,
        selectmode=tk.EXTENDED
    )
    lista_usuarios.pack(side=tk.LEFT, fill=tk.BOTH)
    scrollbar.config(command=lista_usuarios.yview)

    frame_botones = tk.Frame(main_frame, bg="#000000")
    frame_botones.pack(pady=20)

    b_eliminar = HoverButton(
        frame_botones,
        text="Eliminar del Registro",
        command=eliminar_usuario
    )
    b_eliminar.grid(row=0, column=0, padx=10, pady=10)

    b_eliminar_arch = HoverButton(
        frame_botones,
        text="Eliminar usuario y archivos",
        command=eliminar_usuario_y_archivos
    )
    b_eliminar_arch.grid(row=0, column=1, padx=10, pady=10)

    b_actualizar = HoverButton(
        frame_botones,
        text="Actualizar lista",
        command=update_list
    )
    b_actualizar.grid(row=0, column=2, padx=10, pady=10)

    footer = tk.Label(
        main_frame,
        text="© rogergdev",
        font=("Segoe UI", 10),
        fg="#dddddd",
        bg="#000000"
    )
    footer.pack(pady=5)

    data, usr_actual = listar_usuarios()
    USUARIOS_CARGADOS.clear()
    USUARIOS_CARGADOS.extend(data)
    global USUARIO_ACTUAL
    USUARIO_ACTUAL = usr_actual

    update_list()

    root.mainloop()

def update_list():
    actualizar_lista()

if __name__ == "__main__":
    main()
