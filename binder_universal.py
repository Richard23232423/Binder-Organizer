import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import json
import os
import csv
import sys
from pathlib import Path
from datetime import datetime

class BinderUniversal:
    def __init__(self, root):
        self.root = root
        self.root.title("Organizador Universal de Binders")
        self.root.geometry("1000x750")
        
        # Configuración de carpetas
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.colecciones_path = os.path.join(self.base_path, "colecciones")
        self.binders_path = os.path.join(self.base_path, "binders")
        
        # Crear carpetas si no existen
        os.makedirs(self.colecciones_path, exist_ok=True)
        os.makedirs(self.binders_path, exist_ok=True)
        
        # Variables principales
        self.binder_actual = None
        self.config_binder = {}
        self.datos_coleccion = {}
        self.occupied_slots = {}
        self.search_var = tk.StringVar()
        self.current_hoja = 1
        
        # Variables de la interfaz 
        self.search_combo = None
        self.canvas = None
        self.counter_label = None
        self.percent_label = None
        self.hoja_title = None
        self.hoja_var = None
        self.prev_btn = None
        self.next_btn = None
        self.info_label = None
        self.current_highlight = None
        self.current_position = None
        
        # Configuración del binder (valores por defecto)
        self.total_slots = 0
        self.total_hojas = 1
        self.spaces_per_hoja = 32
        self.spaces_per_side = 16
        self.rows_per_side = 4
        self.cols_per_side = 4
        self.cell_size = 70
        
        self.root.configure(bg="#121314")
        
        # Cargar binder activo si existe
        self.cargar_binder_activo()
    
    # Gestion de binders
    def cargar_binder_activo(self):
        #Cargar binder activos si existen
        activo_path = os.path.join(self.binders_path, "activo.json")
        
        if os.path.exists(activo_path):
            try:
                with open(activo_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.binder_actual = data.get('nombre')
                ruta_binder = os.path.join(self.binders_path, self.binder_actual)
                
                config_path = os.path.join(ruta_binder, "config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r', encoding='utf-8') as f:
                        self.config_binder = json.load(f)
                    
                    # Cargar datos de la colección
                    self.datos_coleccion = self.cargar_datos_coleccion(
                        self.config_binder.get('ruta_coleccion', '')
                    )
                    
                    # Cargar progreso
                    progreso_path = os.path.join(ruta_binder, "progreso.json")
                    if os.path.exists(progreso_path):
                        with open(progreso_path, 'r') as f:
                            prog_data = json.load(f)
                            self.occupied_slots = {}
                            for key, value in prog_data.items():
                                if key.startswith('('):
                                    key_clean = key.strip('()')
                                    parts = key_clean.split(',')
                                    if len(parts) == 2:
                                        hoja = int(parts[0].strip())
                                        pos = int(parts[1].strip())
                                        self.occupied_slots[(hoja, pos)] = value
                    
                    # Configurar variables del binder
                    self.total_slots = self.config_binder.get('total_cartas', 0)
                    self.total_hojas = self.config_binder.get('total_hojas', 1)
                    self.spaces_per_hoja = self.config_binder.get('espacios_por_hoja', 32)
                    self.spaces_per_side = self.config_binder.get('espacios_por_lado', 16)
                    self.rows_per_side = self.config_binder.get('filas_por_lado', 4)
                    self.cols_per_side = self.config_binder.get('columnas_por_lado', 4)
                    self.cell_size = 70
                    self.current_hoja = 1  #Vuelve a la hoja 1
                    
                    self.create_main_interface()
                    return
                    
            except Exception as e:
                print(f"Error cargando binder activo: {e}")
        
        self.create_home_screen()
    
    def guardar_binder_activo(self):
        #Guarda binder actual como activo
        if not self.binder_actual:
            return
        
        activo_path = os.path.join(self.binders_path, "activo.json")
        try:
            with open(activo_path, 'w', encoding='utf-8') as f:
                json.dump({'nombre': self.binder_actual}, f, indent=2)
        except:
            pass
    
    def guardar_configuracion_binder(self):
        #Guarad configuracion del binder
        if not self.binder_actual:
            return
        
        ruta_binder = os.path.join(self.binders_path, self.binder_actual)
        os.makedirs(ruta_binder, exist_ok=True)
        
        config_path = os.path.join(ruta_binder, "config.json")
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config_binder, f, indent=2, ensure_ascii=False)
        except:
            pass
        
        self.guardar_progreso()
    
    def guardar_progreso(self):
        #Guarda el progreso actual
        if not self.binder_actual:
            return
        
        ruta_binder = os.path.join(self.binders_path, self.binder_actual)
        os.makedirs(ruta_binder, exist_ok=True)
        
        progreso_path = os.path.join(ruta_binder, "progreso.json")
        try:
            data = {str(key): value for key, value in self.occupied_slots.items()}
            with open(progreso_path, 'w') as f:
                json.dump(data, f, indent=2)
            return True
        except:
            return False
    
    # Funcion para faltantes
    def get_faltantes(self):
        #Calcular faltantes
        faltantes = []
        
        marcados = set()
        for (hoja, pos) in self.occupied_slots.keys():
            abs_num = (hoja - 1) * self.spaces_per_hoja + pos
            if abs_num <= self.total_slots:
                marcados.add(abs_num)
        
        for num in range(1, self.total_slots + 1):
            if num not in marcados:
                if num in self.datos_coleccion:
                    item = self.datos_coleccion[num]
                    nombre = item.get('nombre_completo', item.get('nombre', f"Item #{num}"))
                    faltantes.append({
                        'numero': num,
                        'nombre': nombre,
                        'hoja': (num - 1) // self.spaces_per_hoja + 1,
                        'posicion': ((num - 1) % self.spaces_per_hoja) + 1
                    })
                else:
                    faltantes.append({
                        'numero': num,
                        'nombre': f"Item #{num}",
                        'hoja': (num - 1) // self.spaces_per_hoja + 1,
                        'posicion': ((num - 1) % self.spaces_per_hoja) + 1
                    })
        
        return faltantes
    
    def mostrar_faltantes(self):
        #Interfaz faltantes
        faltantes = self.get_faltantes()
        
        if not faltantes:
            messagebox.showinfo("Completado", "¡Felicidades! ¡La colección esta completa!")
            return
        
        faltantes_window = tk.Toplevel(self.root)
        nombre_coleccion = self.config_binder.get('nombre_coleccion', 'Colección')
        faltantes_window.title(f"Cartas Faltantes - {nombre_coleccion} ({len(faltantes)} pendientes)")
        faltantes_window.geometry("550x650")
        faltantes_window.configure(bg="#191A1B")
        
        faltantes_window.update_idletasks()
        x = (faltantes_window.winfo_screenwidth() // 2) - (550 // 2)
        y = (faltantes_window.winfo_screenheight() // 2) - (650 // 2)
        faltantes_window.geometry(f'+{x}+{y}')
        
        main_frame = tk.Frame(faltantes_window, bg="#191A1B", padx=15, pady=15)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="CARTAS FALTANTES",
            font=("Arial", 16, "bold"),
            bg="#191A1B",
            fg="#e74c3c"
        ).pack(pady=(0, 5))
        
        tk.Label(
            main_frame,
            text=f"Te faltan {len(faltantes)} cartas para completar la colección",
            font=("Arial", 11),
            bg="#191A1B",
            fg="#f39c12"
        ).pack(pady=(0, 15))
        
        list_frame = tk.Frame(main_frame, bg="#2c3e50")
        list_frame.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        
        listbox = tk.Listbox(
            list_frame,
            font=("Courier New", 10),
            bg="#2c3e50",
            fg="#ecf0f1",
            selectbackground="#3498db",
            yscrollcommand=scrollbar.set,
            height=25
        )
        listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=listbox.yview)
        
        for item in faltantes:
            texto = f"#{item['numero']:03d} - {item['nombre']:<30}  Hoja {item['hoja']}, Pos {item['posicion']}"
            listbox.insert(tk.END, texto)
        
        btn_frame = tk.Frame(main_frame, bg="#191A1B")
        btn_frame.pack(pady=15)
        
        def copiar_lista():
            texto_completo = ""
            for item in faltantes:
                texto_completo += f"#{item['numero']:03d} - {item['nombre']}\n"
            
            faltantes_window.clipboard_clear()
            faltantes_window.clipboard_append(texto_completo)
            messagebox.showinfo("Copiado", "Lista copiada al portapapeles", parent=faltantes_window)
        
        tk.Button(
            btn_frame,
            text="Copiar Lista",
            command=copiar_lista,
            bg="#27ae60",
            fg="white",
            font=("Arial", 10),
            padx=5,
            pady=5
        ).pack(side="left", padx=5)
        
        def exportar_lista():
            nombre_archivo = f"faltantes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            with open(nombre_archivo, 'w', encoding='utf-8') as f:
                f.write(f"Cartas Faltantes - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Colección: {nombre_coleccion}\n")
                f.write(f"Total: {len(faltantes)} Cartas\n")
                f.write("="*50 + "\n\n")
                
                for item in faltantes:
                    f.write(f"#{item['numero']:03d} - {item['nombre']}\n")
                    f.write(f"  → Hoja {item['hoja']}, Posición {item['posicion']}\n\n")
            
            messagebox.showinfo("Exportado", f"Lista exportada a:\n{nombre_archivo}", parent=faltantes_window)
        
        tk.Button(
            btn_frame,
            text="Exportar",
            command=exportar_lista,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        def buscar_faltante():
            busqueda = simpledialog.askstring(
                "Buscar", 
                "Ingresa número o nombre de la carta:",
                parent=faltantes_window
            )
            if busqueda:
                for i, item in enumerate(faltantes):
                    if busqueda.isdigit():
                        if item['numero'] == int(busqueda):
                            listbox.selection_clear(0, tk.END)
                            listbox.selection_set(i)
                            listbox.see(i)
                            listbox.activate(i)
                            return
                    else:
                        if busqueda.lower() in item['nombre'].lower():
                            listbox.selection_clear(0, tk.END)
                            listbox.selection_set(i)
                            listbox.see(i)
                            listbox.activate(i)
                            return
                
                messagebox.showinfo("No encontrado", f"'{busqueda}' no está en la lista de faltantes", parent=faltantes_window)
        
        tk.Button(
            btn_frame,
            text="Buscar",
            command=buscar_faltante,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        def ir_a_item():
            seleccion = listbox.curselection()
            if seleccion:
                item = faltantes[seleccion[0]]
                faltantes_window.destroy()
                self._find_position_by_number(item['numero'])
        
        tk.Button(
            btn_frame,
            text="Ir a la carta",
            command=ir_a_item,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        tk.Button(
            btn_frame,
            text="Cerrar",
            command=faltantes_window.destroy,
            bg="#7f8c8d",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=5
        ).pack(side="left", padx=5)
        
        tk.Label(
            main_frame,
            text="Haz doble click para ir a la carta",
            font=("Arial", 9),
            bg="#191A1B",
            fg="#7f8c8d"
        ).pack(pady=(10, 0))
        
        listbox.bind('<Double-Button-1>', lambda e: ir_a_item())
    
    # Pantalla de inicio
    def create_home_screen(self):
        #Pantalla con los binders creados

        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg="#121314")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        tk.Label(
            main_frame,
            text="ORGANIZADOR DE BINDERS",
            font=("Arial", 28, "bold"),
            bg="#121314",
            fg="#ecf0f1"
        ).pack(pady=(0, 30))
        
        binders_existentes = self.scan_binders_existentes()
        
        if binders_existentes:
            existentes_frame = tk.LabelFrame(
                main_frame,
                text="TUS BINDERS GUARDADOS",
                font=("Arial", 16, "bold"),
                bg="#191A1B",
                fg="#ecf0f1",
                padx=20,
                pady=20
            )
            existentes_frame.pack(fill="both", expand=True, pady=(0, 20))
            
            row = 0
            col = 0
            for binder_nombre, binder_info in binders_existentes.items():
                card = tk.Frame(
                    existentes_frame,
                    bg="#2c3e50",
                    padx=15,
                    pady=15,
                    relief="raised",
                    borderwidth=2
                )
                card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
                
                nombre_mostrar = binder_info.get('nombre_personalizado', binder_info['coleccion'])
                
                tk.Label(
                    card,
                    text=f"{nombre_mostrar}",
                    font=("Arial", 12, "bold"),
                    bg="#2c3e50",
                    fg="#ecf0f1"
                ).pack(pady=(0, 5))
                
                tk.Label(
                    card,
                    text=f"{binder_info['coleccion']}",
                    font=("Arial", 10),
                    bg="#2c3e50",
                    fg="#3498db"
                ).pack(pady=(0,5))
                
                tk.Label(
                    card,
                    text=f"{binder_info['cartas']} cartas",
                    font=("Arial", 10),
                    bg="#2c3e50",
                    fg="#f39c12"
                ).pack()
                
                tk.Label(
                    card,
                    text=f"{binder_info['progreso']} marcados",
                    font=("Arial", 10),
                    bg="#2c3e50",
                    fg="#2ecc71"
                ).pack(pady=(0, 10))
                
                btn_frame = tk.Frame(card, bg="#2c3e50")
                btn_frame.pack()
                
                tk.Button(
                    btn_frame,
                    text="ABRIR",
                    command=lambda n=binder_nombre: self.abrir_binder_guardado(n),
                    bg="#3498db",
                    fg="white",
                    font=("Arial", 10, "bold"),
                    padx=15,
                    pady=5
                ).pack(side="left", padx=5)
                
                tk.Button(
                    btn_frame,
                    text="Eliminar",
                    command=lambda n=binder_nombre, info=binder_info: self.eliminar_binder(n, info['coleccion']),
                    bg="#e74c3c",
                    fg="white",
                    font=("Arial", 10, "bold"),
                    padx=15,
                    pady=5
                ).pack(side="left", padx=5)
                
                col += 1
                if col > 2:
                    col = 0
                    row += 1
            
            for i in range(3):
                existentes_frame.grid_columnconfigure(i, weight=1)
        
        nuevo_frame = tk.Frame(main_frame, bg="#121314")
        nuevo_frame.pack(pady=20)
        
        tk.Button(
            nuevo_frame,
            text="+ CREAR NUEVO BINDER",
            command=self.show_colecciones_disponibles,
            bg="#27ae60",
            fg="white",
            font=("Arial", 14, "bold"),
            padx=40,
            pady=15,
            cursor="hand2"
        ).pack()
    
    def scan_binders_existentes(self):
        #Escanear binder y mostrar info
        binders = {}
        
        if os.path.exists(self.binders_path):
            for item in os.listdir(self.binders_path):
                item_path = os.path.join(self.binders_path, item)
                config_path = os.path.join(item_path, "config.json")
                progreso_path = os.path.join(item_path, "progreso.json")
                
                if os.path.isdir(item_path) and os.path.exists(config_path) and item != "activo.json":
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        
                        marcadas = 0
                        if os.path.exists(progreso_path):
                            with open(progreso_path, 'r') as f:
                                prog = json.load(f)
                                marcadas = len(prog)
                        
                        binders[item] = {
                            'coleccion': config.get('nombre_coleccion', 'Desconocida'),
                            'nombre_personalizado': config.get('nombre_personalizado', None),
                            'cartas': config.get('total_cartas', 0),
                            'progreso': marcadas,
                            'config': config
                        }
                    except:
                        continue
        
        return binders
    
    def abrir_binder_guardado(self, binder_nombre):
        #Abrir binder guardado
        ruta_binder = os.path.join(self.binders_path, binder_nombre)
        config_path = os.path.join(ruta_binder, "config.json")
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                self.config_binder = json.load(f)
            
            self.binder_actual = binder_nombre
            
            # Cargar datos de la colección
            self.datos_coleccion = self.cargar_datos_coleccion(
                self.config_binder.get('ruta_coleccion', '')
            )
            
            # Cargar progreso
            progreso_path = os.path.join(ruta_binder, "progreso.json")
            self.occupied_slots = {}
            if os.path.exists(progreso_path):
                with open(progreso_path, 'r') as f:
                    prog_data = json.load(f)
                    for key, value in prog_data.items():
                        if key.startswith('('):
                            key_clean = key.strip('()')
                            parts = key_clean.split(',')
                            if len(parts) == 2:
                                hoja = int(parts[0].strip())
                                pos = int(parts[1].strip())
                                self.occupied_slots[(hoja, pos)] = value
            
            # Configurar variables del binder
            self.total_slots = self.config_binder.get('total_cartas', 0)
            self.total_hojas = self.config_binder.get('total_hojas', 1)
            self.spaces_per_hoja = self.config_binder.get('espacios_por_hoja', 32)
            self.spaces_per_side = self.config_binder.get('espacios_por_lado', 16)
            self.rows_per_side = self.config_binder.get('filas_por_lado', 4)
            self.cols_per_side = self.config_binder.get('columnas_por_lado', 4)
            self.cell_size = 70
            self.current_hoja = 1  # Siempre empezar en hoja 1
            
            self.guardar_binder_activo()
            self.create_main_interface()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo abrir el binder:\n{e}")
    
    # Seleccion de coleccion
    def show_colecciones_disponibles(self):
        #Mostrar las colecciones disponibles para crear binders
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg="#121314")
        main_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        tk.Label(
            main_frame,
            text="SELECCIONA UNA COLECCIÓN",
            font=("Arial", 24, "bold"),
            bg="#121314",
            fg="#ecf0f1"
        ).pack(pady=(0, 30))
        
        colecciones_frame = tk.Frame(main_frame, bg="#191A1B", padx=30, pady=30)
        colecciones_frame.pack(fill="both", expand=True)
        
        colecciones = self.scan_colecciones()
        
        if not colecciones:
            tk.Label(
                colecciones_frame,
                text="No hay colecciones disponibles\n\n"
                     "Crea una carpeta en 'colecciones/' con un archivo 'coleccion.csv'",
                font=("Arial", 12),
                bg="#191A1B",
                fg="#e74c3c",
                justify="center"
            ).pack(pady=40)
            
            tk.Button(
                colecciones_frame,
                text="Crear Colección de Ejemplo",
                command=self.create_example_collection,
                bg="#27ae60",
                fg="white",
                font=("Arial", 12, "bold"),
                padx=30,
                pady=15
            ).pack()
            
            tk.Button(
                colecciones_frame,
                text="← Volver",
                command=self.create_home_screen,
                bg="#7f8c8d",
                fg="white",
                font=("Arial", 10),
                padx=20,
                pady=5
            ).pack(pady=20)
            
            return
        
        row = 0
        col = 0
        for nombre, ruta in colecciones.items():
            total_items = self.count_csv_items(ruta)
            
            card = tk.Frame(
                colecciones_frame,
                bg="#2c3e50",
                padx=20,
                pady=20,
                relief="raised",
                borderwidth=2
            )
            card.grid(row=row, column=col, padx=15, pady=15, sticky="nsew")
                        
            tk.Label(
                card,
                text=f"{nombre}",
                font=("Arial", 14, "bold"),
                bg="#2c3e50",
                fg="#ecf0f1"
            ).pack(pady=(0, 10))
            
            tk.Label(
                card,
                text=f"{total_items} cartas",
                font=("Arial", 12),
                bg="#2c3e50",
                fg="#f39c12"
            ).pack()
            
            tk.Button(
                card,
                text="USAR ESTA",
                command=lambda r=ruta, n=nombre, t=total_items: self.configurar_binder(r, n, t),
                bg="#9b59b6",
                fg="white",
                font=("Arial", 10, "bold"),
                padx=20,
                pady=8
            ).pack(pady=10)
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        for i in range(3):
            colecciones_frame.grid_columnconfigure(i, weight=1)
        
        tk.Button(
            main_frame,
            text="← Volver",
            command=self.create_home_screen,
            bg="#7f8c8d",
            fg="white",
            font=("Arial", 10),
            padx=20,
            pady=5
        ).pack(pady=20)
    
    def scan_colecciones(self):
        #Escanea la carpeta de colecciones
        colecciones = {}
        if os.path.exists(self.colecciones_path):
            for item in os.listdir(self.colecciones_path):
                item_path = os.path.join(self.colecciones_path, item)
                csv_path = os.path.join(item_path, "coleccion.csv")
                if os.path.isdir(item_path) and os.path.exists(csv_path):
                    colecciones[item] = item_path
        return colecciones
    
    def count_csv_items(self, ruta):
        #Contador de cartas en CSV
        csv_path = os.path.join(ruta, "coleccion.csv")
        count = 0
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for i, line in enumerate(lines):
                    if i == 0 and ('#' in line or 'número' in line.lower()):
                        continue
                    if line.strip():
                        count += 1
        except:
            pass
        return count
    
    def cargar_datos_coleccion(self, ruta):
        #Cargar datos del csv
        datos = {}
        csv_path = os.path.join(ruta, "coleccion.csv")
        
        try:
            if os.path.exists(csv_path):
                with open(csv_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    
                    for i, line in enumerate(lines):
                        if i == 0 and (line.startswith('#') or 'número' in line.lower()):
                            continue
                        
                        parts = [p.strip() for p in line.strip().split(',')]
                        if len(parts) >= 2:
                            try:
                                num = int(parts[0])
                                nombre = parts[1]
                                
                                datos[num] = {
                                    'numero': num,
                                    'nombre': nombre,
                                    'nombre_completo': nombre
                                }
                                datos[nombre.lower()] = num
                                
                            except:
                                continue
            return datos
        except:
            return {}
    
    def create_example_collection(self):
        #Colección de ejemplo
        ejemplo_path = os.path.join(self.colecciones_path, "ejemplo_pokemon")
        os.makedirs(ejemplo_path, exist_ok=True)
        
        csv_content = """#,Nombre,Tipo
1,Bulbasaur,Grass
2,Ivysaur,Grass
3,Venusaur,Grass
4,Charmander,Fire
5,Charmeleon,Fire
6,Charizard,Fire
"""
        with open(os.path.join(ejemplo_path, "coleccion.csv"), 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        messagebox.showinfo("Creada", "Colección de ejemplo creada")
        self.show_colecciones_disponibles()
    
    # Configuracion del binder
    def configurar_binder(self, ruta_coleccion, nombre_coleccion, total_items_normal):
        #Ventana para configurar el nuevo binder
        config_window = tk.Toplevel(self.root)
        config_window.title(f"Configurar Binder - {nombre_coleccion}")
        config_window.geometry("500x600")
        config_window.configure(bg="#191A1B")
        config_window.transient(self.root)
        config_window.grab_set()
        
        config_window.update_idletasks()
        x = (config_window.winfo_screenwidth() // 2) - (500 // 2)
        y = (config_window.winfo_screenheight() // 2) - (600 // 2)
        config_window.geometry(f'+{x}+{y}')
        
        main_frame = tk.Frame(config_window, bg="#191A1B", padx=30, pady=30)
        main_frame.pack(fill="both", expand=True)
        
        tk.Label(
            main_frame,
            text="CONFIGURAR BINDER",
            font=("Arial", 18, "bold"),
            bg="#191A1B",
            fg="#ecf0f1"
        ).pack(pady=(0, 10))
        
        tk.Label(
            main_frame,
            text=f"Colección: {nombre_coleccion}",
            font=("Arial", 12),
            bg="#191A1B",
            fg="#f39c12"
        ).pack()
        
        # Nombre personalizado
        tk.Label(
            main_frame,
            text="Nombre del Binder (opcional):",
            font=("Arial", 11),
            bg="#191A1B",
            fg="#ecf0f1",
            anchor="w"
        ).pack(anchor="w", pady=(20, 5))
        
        nombre_binder_var = tk.StringVar()
        nombre_entry = tk.Entry(
            main_frame,
            textvariable=nombre_binder_var,
            font=("Arial", 11),
            width=35
        )
        nombre_entry.pack(fill="x", pady=(0, 10))
        
        # Filas
        row_frame = tk.Frame(main_frame, bg="#2c3e50", padx=15, pady=10)
        row_frame.pack(fill="x", pady=5)
        
        tk.Label(
            row_frame,
            text="Filas por lado:",
            font=("Arial", 11),
            bg="#2c3e50",
            fg="#ecf0f1",
            width=15,
            anchor="w"
        ).pack(side="left")
        
        rows_var = tk.IntVar(value=4)
        rows_spin = tk.Spinbox(
            row_frame,
            from_=1,
            to=10,
            textvariable=rows_var,
            width=8,
            font=("Arial", 11)
        )
        rows_spin.pack(side="left", padx=10)
        
        # Columnas
        col_frame = tk.Frame(main_frame, bg="#2c3e50", padx=15, pady=10)
        col_frame.pack(fill="x", pady=5)
        
        tk.Label(
            col_frame,
            text="Columnas por lado:",
            font=("Arial", 11),
            bg="#2c3e50",
            fg="#ecf0f1",
            width=15,
            anchor="w"
        ).pack(side="left")
        
        cols_var = tk.IntVar(value=4)
        cols_spin = tk.Spinbox(
            col_frame,
            from_=1,
            to=10,
            textvariable=cols_var,
            width=8,
            font=("Arial", 11)
        )
        cols_spin.pack(side="left", padx=10)
        
        #Si es master set
        master_frame = tk.Frame(main_frame, bg="#2c3e50", padx=15, pady=10)
        master_frame.pack(fill="x", pady=10)
        
        master_set_var = tk.BooleanVar(value=False)
        master_check = tk.Checkbutton(
            master_frame,
            text="Master Set (con variantes)",
            variable=master_set_var,
            bg="#2c3e50",
            fg="#ecf0f1",
            selectcolor="#2c3e50",
            font=("Arial", 11),
            anchor="w"
        )
        master_check.pack(anchor="w")
        
        tk.Label(
            master_frame,
            text="  Requiere archivo 'coleccion_master.csv' con formato: Numero,Nombre,Variante",
            font=("Arial", 9),
            bg="#2c3e50",
            fg="#7f8c8d"
        ).pack(anchor="w", padx=(20, 0))
        
        # Botones
        btn_frame = tk.Frame(main_frame, bg="#191A1B")
        btn_frame.pack(pady=20)
        
        def crear_binder():
            rows = rows_var.get()
            cols = cols_var.get()
            master_set = master_set_var.get()
            nombre_personalizado = nombre_binder_var.get().strip()
            
            if rows < 1 or rows > 10 or cols < 1 or cols > 10:
                messagebox.showerror("Error", "Valores entre 1 y 10")
                return
            
            self.crear_nuevo_binder(
                ruta_coleccion=ruta_coleccion,
                nombre_coleccion=nombre_coleccion,
                rows=rows,
                cols=cols,
                master_set=master_set,
                nombre_personalizado=nombre_personalizado,
                config_window=config_window
            )
        
        tk.Button(
            btn_frame,
            text="CREAR BINDER",
            command=crear_binder,
            bg="#27ae60",
            fg="white",
            font=("Arial", 12, "bold"),
            padx=30,
            pady=10
        ).pack()
        
        tk.Button(
            btn_frame,
            text="CANCELAR",
            command=config_window.destroy,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 11),
            padx=20,
            pady=8
        ).pack(pady=10)
    
    def crear_nuevo_binder(self, ruta_coleccion, nombre_coleccion, rows, cols, master_set, nombre_personalizado, config_window):
        #Crea bidner
        
        try:
            # Determinar qué CSV cargar
            if master_set:
                csv_path = os.path.join(ruta_coleccion, "coleccion_master.csv")
                if not os.path.exists(csv_path):
                    messagebox.showerror("Error", f"No se encontró 'coleccion_master.csv' en:\n{ruta_coleccion}")
                    return
            else:
                csv_path = os.path.join(ruta_coleccion, "coleccion.csv")
                if not os.path.exists(csv_path):
                    messagebox.showerror("Error", f"No se encontró 'coleccion.csv' en:\n{ruta_coleccion}")
                    return
            
            # Cargar CSV
            items_totales = 0
            datos_temporales = {}
            
            with open(csv_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
                posicion_contador = 1
                
                for i, line in enumerate(lines):
                    if i == 0 and ('#' in line or 'Numero' in line or 'Nombre' in line or 'Pok' in line):
                        continue
                    
                    if not line.strip():
                        continue
                    
                    parts = [p.strip() for p in line.strip().split(',')]
                    
                    if master_set:
                        # Formato: Numero,Nombre,Variante
                        if len(parts) >= 3:
                            num_pokemon = parts[0]
                            nombre = parts[1]
                            variante = parts[2]
                            nombre_completo = f"{nombre} ({variante})"
                            
                            datos_temporales[posicion_contador] = {
                                'numero': posicion_contador,
                                'numero_mostrar': num_pokemon,
                                'nombre': nombre,
                                'nombre_completo': nombre_completo,
                                'variante': variante
                            }
                            datos_temporales[nombre_completo.lower()] = posicion_contador
                            datos_temporales[nombre.lower()] = posicion_contador
                            
                            items_totales += 1
                            posicion_contador += 1
                            
                    else:
                        if len(parts) >= 2:
                            try:
                                num = int(parts[0])
                                nombre = parts[1]
                                
                                datos_temporales[num] = {
                                    'numero': num,
                                    'numero_mostrar': str(num),
                                    'nombre': nombre,
                                    'nombre_completo': nombre
                                }
                                datos_temporales[nombre.lower()] = num
                                items_totales += 1
                            except ValueError:
                                continue
            
            if items_totales == 0:
                messagebox.showerror("Error", "El archivo CSV está vacío o tiene formato incorrecto")
                return
            
            # Generar nombre del binder
            import time
            timestamp = int(time.time())
            if nombre_personalizado:
                nombre_binder = f"{nombre_personalizado}_{timestamp}"
            else:
                nombre_binder = f"{nombre_coleccion}_{timestamp}"
            
            self.binder_actual = nombre_binder
            
            # Calcular configuración
            espacios_lado = rows * cols
            espacios_hoja = espacios_lado * 2
            total_hojas = (items_totales + espacios_hoja - 1) // espacios_hoja
            
            # Guardar configuración
            self.config_binder = {
                "nombre": nombre_binder,
                "nombre_coleccion": nombre_coleccion,
                "nombre_personalizado": nombre_personalizado if nombre_personalizado else None,
                "ruta_coleccion": ruta_coleccion,
                "total_cartas": items_totales,
                "espacios_por_hoja": espacios_hoja,
                "espacios_por_lado": espacios_lado,
                "filas_por_lado": rows,
                "columnas_por_lado": cols,
                "total_hojas": total_hojas,
                "fecha_creacion": timestamp,
                "master_set": master_set
            }
            
            # Cargar datos en memoria
            self.datos_coleccion = datos_temporales
            self.total_slots = items_totales
            self.total_hojas = total_hojas
            self.spaces_per_hoja = espacios_hoja
            self.spaces_per_side = espacios_lado
            self.rows_per_side = rows
            self.cols_per_side = cols
            self.cell_size = 70
            self.occupied_slots = {}
            self.current_hoja = 1
            
            # Guardar y continuar
            self.guardar_configuracion_binder()
            self.guardar_binder_activo()
            
            tipo_msg = "MASTER SET" if master_set else "NORMAL"
            messagebox.showinfo(
                "Binder Creado",
                f"Binder creado exitosamente ({tipo_msg})\n\n"
                f"{items_totales} cartas cargadas\n"
                f"{rows}×{cols} = {espacios_lado} esp/lado\n"
                f"{total_hojas} hojas necesarias"
            )
            
            config_window.destroy()
            self.create_main_interface()
            
        except Exception as e:
            messagebox.showerror("Error", f"Error al crear binder:\n{e}")
            
    def eliminar_binder(self, binder_nombre, coleccion_nombre):
        
        #Confirmar eliminar
        respuesta = messagebox.askyesno(
            f"Confirmar eliminación",
            f"Estás seguro que quieres eliminar este binder?\n\n"
            f"Nombre: {binder_nombre}"
        )
        
        if not respuesta:
            return
        
        try:
            ruta_binder = os.path.join(self.binders_path, binder_nombre)
            
            if not os.path.exists(ruta_binder):
                messagebox.showerror("Error", "El binder no existe")
                return
            
            #Elimina la carpeta
            import shutil
            shutil.rmtree(ruta_binder)
            
            #Eliminar archivo activo si solo habia un binder
            activo_path = os.path.join(self.binders_path, "activo.json")
            if os.path.exists(activo_path):
                with open(activo_path, 'r', encoding='utf-8') as f:
                    activo = json.load(f)
            if activo.get('nombre') == binder_nombre:
                os.remove(activo_path)
    
            messagebox.showinfo("Eliminado", f"Binder '{binder_nombre}' eliminado correctamente")
        
            # Recargar pantalla de inicio
            self.create_home_screen()
        
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo eliminar el binder:\n{e}")
    
    
    
    # Interfaz principal del binder
    def create_main_interface(self):
        #Interfaz principal del binder
        for widget in self.root.winfo_children():
            widget.destroy()
        
        main_frame = tk.Frame(self.root, bg="#121314")
        main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        header_frame = tk.Frame(main_frame, bg="#121314")
        header_frame.pack(fill="x", pady=(0, 10))
        
        nombre_coleccion = self.config_binder.get('nombre_coleccion', 'Colección')
        nombre_personalizado = self.config_binder.get('nombre_personalizado', None)
        
        if nombre_personalizado:
            titulo = f"{nombre_personalizado} ({nombre_coleccion})"
        else:
            titulo = nombre_coleccion
        
        tk.Label(
            header_frame,
            text=f"{titulo}",
            font=("Arial", 22, "bold"),
            bg="#121314",
            fg="#ecf0f1"
        ).pack(side="left")
        
        tk.Button(
            header_frame,
            text="Volver al Inicio",
            command=self.volver_al_inicio,
            bg="#7f8c8d",
            fg="white",
            font=("Arial", 9),
            padx=10,
            pady=2
        ).pack(side="right")
        
        info_text = (f"{self.total_slots} items | "
                     f"{self.rows_per_side}×{self.cols_per_side} = {self.spaces_per_side} esp/lado | "
                     f"{self.spaces_per_hoja} esp/hoja | {self.total_hojas} hojas")
        tk.Label(
            main_frame,
            text=info_text,
            font=("Arial", 11),
            bg="#121314",
            fg="#bdc3c7"
        ).pack(pady=(0, 10))
        
        # Frame superior con contador y botones
        top_frame = tk.Frame(main_frame, bg="#191A1B", padx=15, pady=8)
        top_frame.pack(fill="x", pady=(0, 10))
        
        counter_frame = tk.Frame(top_frame, bg="#191A1B")
        counter_frame.pack(side="left")
        
        self.counter_label = tk.Label(
            counter_frame,
            text=f"Cartas: 0/{self.total_slots}",
            font=("Arial", 12, "bold"),
            bg="#191A1B",
            fg="#2ecc71"
        )
        self.counter_label.pack(side="left", padx=(0, 15))
        
        self.percent_label = tk.Label(
            counter_frame,
            text="0% completado",
            font=("Arial", 11),
            bg="#191A1B",
            fg="#f39c12"
        )
        self.percent_label.pack(side="left")
        
        manage_frame = tk.Frame(top_frame, bg="#191A1B")
        manage_frame.pack(side="right")
        
        tk.Button(
            manage_frame,
            text="Ver Faltantes",
            command=self.mostrar_faltantes,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9),
            padx=8,
            pady=2
        ).pack(side="left", padx=3)
        
        tk.Button(
            manage_frame,
            text="Limpiar Todo",
            command=self.clear_all_markers,
            bg="#e74c3c",
            fg="white",
            font=("Arial", 9),
            padx=8,
            pady=2
        ).pack(side="left", padx=3)
        
        tk.Button(
            manage_frame,
            text="Guardar",
            command=self.guardar_progreso,
            bg="#27ae60",
            fg="white",
            font=("Arial", 9),
            padx=8,
            pady=2
        ).pack(side="left", padx=3)
        
        # Búsqueda
        search_frame = tk.Frame(main_frame, bg="#191A1B", padx=15, pady=10)
        search_frame.pack(fill="x", pady=(0, 10))
        
        tk.Label(
            search_frame,
            text="Buscar:",
            font=("Arial", 11),
            bg="#191A1B",
            fg="#ecf0f1"
        ).pack(side="left", padx=(0, 8))
        
        self.search_combo = ttk.Combobox(
            search_frame,
            textvariable=self.search_var,
            font=("Arial", 11),
            width=40
        )
        self.search_combo.pack(side="left", padx=(0, 8))
        self.setup_autocomplete()
        self.search_combo.bind('<Return>', lambda event: self.find_position())
        
        btn_frame = tk.Frame(search_frame, bg="#191A1B")
        btn_frame.pack(side="left", padx=(10, 0))
        
        tk.Button(
            btn_frame,
            text="Buscar",
            command=self.find_position,
            bg="#3498db",
            fg="white",
            font=("Arial", 10),
            padx=12,
            pady=3
        ).pack(side="left", padx=2)
        
        tk.Button(
            btn_frame,
            text="Marcar",
            command=self.find_and_mark,
            bg="#9b59b6",
            fg="white",
            font=("Arial", 10),
            padx=12,
            pady=3
        ).pack(side="left", padx=2)
        
        tk.Button(
            btn_frame,
            text="Desmarcar",
            command=self.unmark_current,
            bg="#e67e22",
            fg="white",
            font=("Arial", 10),
            padx=12,
            pady=3
        ).pack(side="left", padx=2)
        
        # Canvas
        hoja_frame = tk.Frame(main_frame, bg="#121314", padx=20, pady=5)
        hoja_frame.pack(fill="x", pady=(0, 10))
        
        self.hoja_title = tk.Label(
            hoja_frame,
            text="Hoja 1",
            font=("Arial", 14, "bold"),
            bg="#121314",
            fg="#ecf0f1"
        )
        self.hoja_title.pack(pady=(0, 15))
        
        canvas_width = 60 + (self.cell_size * self.cols_per_side) + 60 + (self.cell_size * self.cols_per_side) + 60
        canvas_height = 60 + (self.cell_size * self.rows_per_side) + 60
        
        self.canvas = tk.Canvas(
            hoja_frame,
            bg="#ecf0f1",
            width=canvas_width,
            height=canvas_height,
            highlightthickness=2,
            highlightbackground="#7f8c8d"
        )
        self.canvas.pack()
        self.canvas.bind('<Button-1>', self.canvas_click)
        
        # Controles de hoja
        control_frame = tk.Frame(main_frame, bg="#121314", pady=5)
        control_frame.pack()
        
        self.prev_btn = tk.Button(
            control_frame,
            text="◀ Hoja Anterior",
            command=self.prev_hoja,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=4,
            state="disabled"
        )
        self.prev_btn.pack(side="left", padx=5)
        
        tk.Label(
            control_frame,
            text="Hoja:",
            font=("Arial", 11),
            bg="#121314",
            fg="#ecf0f1"
        ).pack(side="left", padx=(15, 5))
        
        self.hoja_var = tk.StringVar(value="1")
        hoja_spinbox = tk.Spinbox(
            control_frame,
            from_=1,
            to=self.total_hojas,
            textvariable=self.hoja_var,
            width=5,
            font=("Arial", 11),
            command=self.go_to_hoja
        )
        hoja_spinbox.pack(side="left", padx=5)
        hoja_spinbox.bind('<Return>', lambda event: self.go_to_hoja())
        
        tk.Label(
            control_frame,
            text=f"de {self.total_hojas}",
            font=("Arial", 11),
            bg="#121314",
            fg="#ecf0f1"
        ).pack(side="left", padx=5)
        
        self.next_btn = tk.Button(
            control_frame,
            text="Siguiente Hoja ▶",
            command=self.next_hoja,
            bg="#95a5a6",
            fg="white",
            font=("Arial", 10),
            padx=15,
            pady=4
        )
        self.next_btn.pack(side="left", padx=5)
        
        self.info_label = tk.Label(
            main_frame,
            text=f"Listo | 0/{self.total_slots} cartas",
            font=("Arial", 10),
            bg="#121314",
            fg="#bdc3c7",
            pady=5
        )
        self.info_label.pack()
        
        self.current_highlight = None
        self.current_position = None
        
        self.draw_hoja()
        self.update_counter()
    
    def volver_al_inicio(self):
        #Vuelve a la pantalla de inicio guardando el progreso
        self.guardar_progreso()
        # Limpiar variables 
        self.binder_actual = None
        self.config_binder = {}
        self.datos_coleccion = {}
        self.occupied_slots = {}
        self.create_home_screen()
    
    # Metodos de funcionamiento
    def setup_autocomplete(self):
        #Configura autocompletado
        nombres = []
        nums_vistos = set()
        
        for key, value in self.datos_coleccion.items():
            if isinstance(key, int) and key not in nums_vistos:
                nums_vistos.add(key)
                nombre_completo = value.get('nombre_completo', value.get('nombre', f"Item #{key}"))
                display = f"#{key:03d} - {nombre_completo}"
                nombres.append(display)
        
        nombres.sort()
        self.search_combo['values'] = nombres
        
        def autocomplete(event):
            value = self.search_var.get().lower()
            if value:
                matches = [n for n in nombres if value in n.lower()]
                self.search_combo['values'] = matches
            else:
                self.search_combo['values'] = nombres
        
        self.search_combo.bind('<KeyRelease>', autocomplete)
    
    def parse_search_input(self, text):
        #Parsea búsqueda
        if not text:
            return None
        
        try:
            return int(text)
        except:
            pass
        
        if text.startswith('#'):
            try:
                parts = text.split('-')
                num_str = parts[0].replace('#', '').strip()
                return int(num_str)
            except:
                pass
        
        search_lower = text.lower()
        
        for key, value in self.datos_coleccion.items():
            if isinstance(key, int):
                nombre_completo = value.get('nombre_completo', value.get('nombre', '')).lower()
                nombre_simple = value.get('nombre', '').lower()
                if (search_lower == nombre_completo or search_lower == nombre_simple):
                    return key
        
        return None
    
    def find_position(self):
        #Busca posición
        text = self.search_var.get().strip()
        if not text:
            return
        
        num = self.parse_search_input(text)
        
        if num is None:
            messagebox.showerror("No encontrado", f"No se encontró: '{text}'")
            return
        
        if num < 1 or num > self.total_slots:
            messagebox.showerror("Error", f"Número entre 1 y {self.total_slots}")
            return
        
        if num in self.datos_coleccion:
            item = self.datos_coleccion[num]
            nombre_completo = item.get('nombre_completo', item.get('nombre', f"Item #{num}"))
            display = f"#{num:03d} - {nombre_completo}"
            self.search_var.set(display)
        
        self._find_position_by_number(num)
    
    def _find_position_by_number(self, num):
        #Busca por número
        hoja = (num - 1) // self.spaces_per_hoja + 1
        pos_in_hoja = ((num - 1) % self.spaces_per_hoja) + 1
        
        if pos_in_hoja <= self.spaces_per_side:
            side = "Frente"
            grid_pos = pos_in_hoja
        else:
            side = "Reverso"
            grid_pos = pos_in_hoja - self.spaces_per_side
        
        row = (grid_pos - 1) // self.cols_per_side
        col = (grid_pos - 1) % self.cols_per_side
        
        self.current_position = (hoja, pos_in_hoja)
        is_marked = (hoja, pos_in_hoja) in self.occupied_slots
        
        if num in self.datos_coleccion:
            item = self.datos_coleccion[num]
            nombre = item.get('nombre_completo', item.get('nombre', f"Item #{num}"))
        else:
            nombre = f"Item #{num}"
        
        self.info_label.config(
            text=f"#{num:03d} - {nombre} | Hoja {hoja}, Pos {pos_in_hoja} ({side}) | {'MARCADO' if is_marked else 'DISPONIBLE'} | {len(self.occupied_slots)}/{self.total_slots} cartas",
            fg="#2ecc71" if is_marked else "#3498db"
        )
        
        self.current_hoja = hoja
        self.hoja_var.set(str(hoja))
        self.update_hoja_controls()
        self.draw_hoja()
        self.highlight_position(row, col, side)
    
    def canvas_click(self, event):
        #Manejar clicks
        x, y = event.x, event.y
        cell = self.cell_size
        front_x = 60
        back_x = 60 + cell * self.cols_per_side + 60
        
        if front_x <= x < front_x + cell * self.cols_per_side and 60 <= y < 60 + cell * self.rows_per_side:
            x_offset = front_x
            y_offset = 60
            side = "Frente"
        elif back_x <= x < back_x + cell * self.cols_per_side and 60 <= y < 60 + cell * self.rows_per_side:
            x_offset = back_x
            y_offset = 60
            side = "Reverso"
        else:
            return
        
        col = (x - x_offset) // cell
        row = (y - y_offset) // cell
        
        if 0 <= row < self.rows_per_side and 0 <= col < self.cols_per_side:
            if side == "Frente":
                pos = row * self.cols_per_side + col + 1
            else:
                pos = row * self.cols_per_side + col + 1 + self.spaces_per_side
            
            abs_num = (self.current_hoja - 1) * self.spaces_per_hoja + pos
            
            if abs_num in self.datos_coleccion:
                item = self.datos_coleccion[abs_num]
                nombre = item.get('nombre_completo', item.get('nombre', f"Item #{abs_num}"))
            else:
                nombre = f"Item #{abs_num}"
            
            key = (self.current_hoja, pos)
            if key in self.occupied_slots:
                del self.occupied_slots[key]
                status = "Desmarcado"
                color = "#e74c3c"
            else:
                self.occupied_slots[key] = True
                status = "Marcado"
                color = "#9b59b6"
            
            self.guardar_progreso()
            self.update_counter()
            self.draw_hoja()
            self.highlight_position(row, col, side)
            
            self.info_label.config(
                text=f"#{abs_num:03d} - {nombre} | Hoja {self.current_hoja}, Pos {pos} ({side}) | {status} | {len(self.occupied_slots)}/{self.total_slots} cartas",
                fg=color
            )
            
            self.current_position = (self.current_hoja, pos)
    
    def draw_hoja(self):
        #Dibuja la hoja actual
        self.canvas.delete("all")
        
        start = (self.current_hoja - 1) * self.spaces_per_hoja + 1
        end = min(self.current_hoja * self.spaces_per_hoja, self.total_slots)
        self.hoja_title.config(text=f"Hoja {self.current_hoja} - Cartas #{start} a #{end}")
        
        self.draw_grid_section("FRENTE", 60, 60)
        self.draw_grid_section("REVERSO", 60 + self.cell_size * self.cols_per_side + 60, 60)
        
        self.canvas.create_text(400, 40, text="CLICK para marcar/desmarcar", 
                              fill="#7f8c8d", font=("Arial", 9))
    
    def draw_grid_section(self, title, x_offset, y_offset):
        #Dibuja sección
        cell = self.cell_size
        
        self.canvas.create_text(
            x_offset + cell * self.cols_per_side / 2,
            y_offset - 20,
            text=title,
            fill="#2c3e50",
            font=("Arial", 12, "bold")
        )
        
        for row in range(self.rows_per_side):
            for col in range(self.cols_per_side):
                x1 = x_offset + col * cell
                y1 = y_offset + row * cell
                x2 = x1 + cell
                y2 = y1 + cell
                
                if title == "FRENTE":
                    pos = row * self.cols_per_side + col + 1
                else:
                    pos = row * self.cols_per_side + col + 1 + self.spaces_per_side
                
                is_occupied = (self.current_hoja, pos) in self.occupied_slots
                bg_color = "#bdc3c7" if is_occupied else "#ffffff"
                
                self.canvas.create_rectangle(
                    x1, y1, x2, y2,
                    fill=bg_color,
                    outline="#7f8c8d",
                    width=2
                )
                
                abs_num = (self.current_hoja - 1) * self.spaces_per_hoja + pos
                
                if abs_num <= self.total_slots and abs_num in self.datos_coleccion:
                    nombre = self.datos_coleccion[abs_num].get('nombre_completo', 
                              self.datos_coleccion[abs_num].get('nombre', f"Item #{abs_num}"))
                    if len(nombre) > 10:
                        nombre = nombre[:10] + "..."
                    
                    self.canvas.create_text(
                        x1 + cell/2,
                        y1 + cell/3,
                        text=nombre,
                        fill="#2c3e50" if not is_occupied else "#34495e",
                        font=("Arial", 9, "bold"),
                        width=cell - 10
                    )
                
                if abs_num <= self.total_slots:
                    numero_a_mostrar = self.datos_coleccion[abs_num].get('numero_mostrar', str(abs_num)) if abs_num in self.datos_coleccion else str(abs_num)
                    self.canvas.create_text(
                        x1 + cell/2,
                        y1 + cell/1.7,
                        text=f"#{numero_a_mostrar}",
                        fill="#7f8c8d" if is_occupied else "#95a5a6",
                        font=("Arial", 9)
                    )
                
                self.canvas.create_text(
                    x1 + 10,
                    y1 + 10,
                    text=str(pos),
                    fill="#7f8c8d",
                    font=("Arial", 7)
                )
    
    def highlight_position(self, row, col, side):
        #Resalta posición
        self.clear_highlight()
        
        cell = self.cell_size
        if side == "Frente":
            x_offset = 60
        else:
            x_offset = 60 + cell * self.cols_per_side + 60
        
        y_offset = 60
        
        x1 = x_offset + col * cell
        y1 = y_offset + row * cell
        x2 = x1 + cell
        y2 = y1 + cell
        
        self.highlight_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            fill="#3498db",
            outline="#2980b9",
            width=3,
            stipple="gray50"
        )
        self.canvas.tag_raise("all")
    
    def clear_highlight(self):
        if hasattr(self, 'highlight_rect'):
            self.canvas.delete(self.highlight_rect)
    
    def update_counter(self):
        total = len(self.occupied_slots)
        remaining = self.total_slots - total
        percent = (total / self.total_slots * 100) if self.total_slots > 0 else 0
        
        self.counter_label.config(
            text=f"Cartas: {total}/{self.total_slots} ({remaining} restantes)",
            fg="#2ecc71" if total > 0 else "#ecf0f1"
        )
        self.percent_label.config(
            text=f"{percent:.1f}% completado",
            fg="#f39c12" if percent < 50 else "#e74c3c" if percent < 90 else "#27ae60"
        )
    
    def find_and_mark(self):
        self.find_position()
        if self.current_position:
            hoja, pos = self.current_position
            key = (hoja, pos)
            if key not in self.occupied_slots:
                self.occupied_slots[key] = True
                self.guardar_progreso()
                self.update_counter()
                self.draw_hoja()
    
    def unmark_current(self):
        if self.current_position:
            hoja, pos = self.current_position
            key = (hoja, pos)
            if key in self.occupied_slots:
                del self.occupied_slots[key]
                self.guardar_progreso()
                self.update_counter()
                self.draw_hoja()
                
                abs_num = (hoja - 1) * self.spaces_per_hoja + pos
                if abs_num in self.datos_coleccion:
                    item = self.datos_coleccion[abs_num]
                    nombre = item.get('nombre_completo', item.get('nombre', f"Item #{abs_num}"))
                else:
                    nombre = f"Item #{abs_num}"
                
                self.info_label.config(
                    text=f"#{abs_num:03d} - {nombre} desmarcado | {len(self.occupied_slots)}/{self.total_slots} cartas",
                    fg="#e74c3c"
                )
    
    def clear_all_markers(self):
        if len(self.occupied_slots) == 0:
            messagebox.showinfo("Info", "No hay marcadores")
            return
        
        if messagebox.askyesno("Confirmar", f"¿Limpiar {len(self.occupied_slots)} marcadores?"):
            self.occupied_slots.clear()
            self.guardar_progreso()
            self.update_counter()
            self.draw_hoja()
            self.info_label.config(text=f"Todos limpiados | 0/{self.total_slots} cartas", fg="#e74c3c")
            self.current_position = None
    
    def prev_hoja(self):
        if self.current_hoja > 1:
            self.current_hoja -= 1
            self.hoja_var.set(str(self.current_hoja))
            self.update_hoja_controls()
            self.clear_highlight()
            self.draw_hoja()
            self.current_position = None
            self.info_label.config(text=f"Hoja {self.current_hoja} | {len(self.occupied_slots)}/{self.total_slots} cartas", fg="#bdc3c7")
    
    def next_hoja(self):
        if self.current_hoja < self.total_hojas:
            self.current_hoja += 1
            self.hoja_var.set(str(self.current_hoja))
            self.update_hoja_controls()
            self.clear_highlight()
            self.draw_hoja()
            self.current_position = None
            self.info_label.config(text=f"Hoja {self.current_hoja} | {len(self.occupied_slots)}/{self.total_slots} cartas", fg="#bdc3c7")
    
    def go_to_hoja(self):
        try:
            hoja = int(self.hoja_var.get())
            if 1 <= hoja <= self.total_hojas:
                self.current_hoja = hoja
                self.update_hoja_controls()
                self.clear_highlight()
                self.draw_hoja()
                self.current_position = None
                self.info_label.config(text=f"Hoja {self.current_hoja} | {len(self.occupied_slots)}/{self.total_slots} cartas", fg="#bdc3c7")
            else:
                # Si el valor no es válido, restaurar el actual
                self.hoja_var.set(str(self.current_hoja))
        except:
            self.hoja_var.set(str(self.current_hoja))
    
    def update_hoja_controls(self):
        self.prev_btn.config(state="normal" if self.current_hoja > 1 else "disabled")
        self.next_btn.config(state="normal" if self.current_hoja < self.total_hojas else "disabled")

def main():
    root = tk.Tk()
    app = BinderUniversal(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.guardar_progreso(), root.destroy()))
    root.mainloop()

if __name__ == "__main__":
    main()
