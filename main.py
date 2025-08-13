import os
import json
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from xboxunity_api import login_xboxunity, buscar_tus, descargar_tu, probar_conectividad
from xex_reader import obtener_info_juego

CONFIG_FILE = "config.json"

class XboxTUMApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Xbox 360 TU Manager")
        self.token = None
        self.api_key = None
        self.juegos = []

        # Login Frame
        login_frame = tk.LabelFrame(root, text="Login XboxUnity / API Key", padx=10, pady=10)
        login_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(login_frame, text="Username:").grid(row=0, column=0, sticky="e")
        tk.Label(login_frame, text="Password:").grid(row=1, column=0, sticky="e")
        tk.Label(login_frame, text="API Key:").grid(row=2, column=0, sticky="e")

        self.entry_user = tk.Entry(login_frame)
        self.entry_pass = tk.Entry(login_frame, show="*")
        self.entry_apikey = tk.Entry(login_frame)

        self.entry_user.grid(row=0, column=1, pady=2)
        self.entry_pass.grid(row=1, column=1, pady=2)
        self.entry_apikey.grid(row=2, column=1, pady=2)

        tk.Button(login_frame, text="Login", command=self.login).grid(row=0, column=2, rowspan=3, padx=5)

        # Games Frame
        juegos_frame = tk.LabelFrame(root, text="Detected Games", padx=10, pady=10)
        juegos_frame.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(juegos_frame, columns=("Game", "MediaID", "TitleID"), show="headings")
        self.tree.heading("Game", text="Game")
        self.tree.heading("MediaID", text="MediaID")
        self.tree.heading("TitleID", text="TitleID")
        self.tree.column("Game", width=200)
        self.tree.column("MediaID", width=100)
        self.tree.column("TitleID", width=100)
        self.tree.pack(fill="both", expand=True)

        # Buttons for copying IDs and export
        botones_copiar_frame = tk.Frame(juegos_frame)
        botones_copiar_frame.pack(fill="x", pady=5)
        
        tk.Button(botones_copiar_frame, text="Copy MediaID", command=self.copy_media_id, 
                 bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(botones_copiar_frame, text="Copy TitleID", command=self.copy_title_id,
                 bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(botones_copiar_frame, text="Export HTML List", command=self.exportar_lista_html,
                 bg="#FF9800", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        tk.Button(botones_copiar_frame, text="Prepare USB", command=self.preparar_usb_xbox360,
                 bg="#9C27B0", fg="white", font=("Arial", 10, "bold")).pack(side="left", padx=5)
        
        # Keep context menu as additional option
        self.menu_popup = tk.Menu(self.root, tearoff=0)
        self.menu_popup.add_command(label="Copy MediaID", command=self.copy_media_id)
        self.menu_popup.add_command(label="Copy TitleID", command=self.copy_title_id)
        self.tree.bind("<Button-3>", self.mostrar_menu)

        # Progress bar
        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate")
        self.progress.pack(fill="x", padx=10, pady=5)

        # Log text box
        self.log_text = tk.Text(root, height=10, state="disabled", bg="#222", fg="#eee")
        self.log_text.pack(fill="both", expand=True, padx=10, pady=(0,10))

        # Buttons
        botones_frame = tk.Frame(root)
        botones_frame.pack(fill="x", pady=5)

        tk.Button(botones_frame, text="Select Games Folder", command=self.select_folder).pack(side="left", padx=5)
        tk.Button(botones_frame, text="Search and Download TUs", command=self.buscar_y_descargar_tus).pack(side="left", padx=5)

        # Load config
        self.load_config()

    def save_config(self, username, password, api_key):
        with open(CONFIG_FILE, "w") as f:
            json.dump({"username": username, "password": password, "api_key": api_key}, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                self.entry_user.insert(0, data.get("username", ""))
                self.entry_pass.insert(0, data.get("password", ""))
                self.entry_apikey.insert(0, data.get("api_key", ""))
                if data.get("api_key"):
                    self.api_key = data.get("api_key")
                elif data.get("username") and data.get("password"):
                    self.login(auto=True)

    def delete_config(self):
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)

    def login(self, auto=False):
        username = self.entry_user.get().strip()
        password = self.entry_pass.get().strip()
        api_key = self.entry_apikey.get().strip()

        self.api_key = api_key if api_key else None

        if self.api_key:
            if not auto:
                self.save_config(username, password, api_key)
                self._log("API Key saved successfully.")
                # Test connectivity with API Key
                self._log("Testing connectivity with XboxUnity...")
                if probar_conectividad():
                    self._log("Connectivity verified successfully.")
                else:
                    self._log("WARNING: Connectivity issues with XboxUnity.")
            return

        if not username or not password:
            messagebox.showerror("Error", "Enter username and password or API Key")
            return

        if not auto:
            self._log("Testing connectivity with XboxUnity...")
            if not probar_conectividad():
                messagebox.showerror("Error", "Cannot connect to XboxUnity. Check your internet connection.")
                return

        self._log("Attempting to login...")
        token = login_xboxunity(username, password)
        if token:
            self.token = token
            if not auto:
                self.save_config(username, password, api_key)
                self._log("Login successful.")
        else:
            self.delete_config()
            if not auto:
                messagebox.showerror("Error", "Could not login to XboxUnity. Check your credentials.")

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select folder with games")
        if folder:
            # Execute in thread to avoid blocking GUI
            threading.Thread(target=self._process_games, args=(folder,), daemon=True).start()

    def _process_games(self, folder):
        self.juegos.clear()
        self.tree.delete(*self.tree.get_children())
        
        # Count XEX files first
        xex_files = []
        for root_dir, dirs, files in os.walk(folder):
            for file in files:
                if file.lower() == "default.xex":
                    xex_files.append(os.path.join(root_dir, file))
        
        if not xex_files:
            self._log("No default.xex files found in selected folder.")
            return
        
        total_files = len(xex_files)
        self._log(f"Reading MediaID...please wait ({total_files} games found)")
        self.progress["value"] = 0
        self.progress["maximum"] = total_files
        
        for idx, xex_path in enumerate(xex_files, 1):
            game_name = os.path.basename(os.path.dirname(xex_path))
            self._log(f"Reading information from '{game_name}'...")
            
            game_info = obtener_info_juego(xex_path)
            if game_info and (game_info["media_id"] or game_info["title_id"]):
                media_id = game_info["media_id"] or "N/A"
                title_id = game_info["title_id"] or "N/A"
                self.juegos.append({
                    "nombre": game_name, 
                    "media_id": game_info["media_id"], 
                    "title_id": game_info["title_id"]
                })
                self.tree.insert("", "end", values=(game_name, media_id, title_id))
            else:
                self._log(f"  ERROR: Could not read information from '{game_name}'")
            
            self.progress["value"] = idx
            self.root.update_idletasks()

        self.progress["value"] = 0
        self._log(f"Detected {len(self.juegos)} games with valid information.")

    def buscar_y_descargar_tus(self):
        if not self.juegos:
            messagebox.showerror("Error", "No games detected. Select the folder first.")
            return
        if not self.token and not self.api_key:
            messagebox.showerror("Error", "You must login or enter API Key")
            return

        carpeta_destino = filedialog.askdirectory(title="Select folder to save TUs")
        if not carpeta_destino:
            return

        # Execute in thread to avoid blocking GUI
        threading.Thread(target=self._procesar_tus, args=(carpeta_destino,), daemon=True).start()

    def _procesar_tus(self, carpeta_destino):
        total_juegos = len(self.juegos)
        juegos_con_tu = 0
        total_tus_descargados = 0
        errores = 0

        self._log("Starting TU search and download...\n")
        self.progress["value"] = 0
        self.progress["maximum"] = total_juegos

        for idx, juego in enumerate(self.juegos, 1):
            nombre = juego["nombre"]
            media_id = juego["media_id"]
            title_id = juego["title_id"]
            
            ids_info = []
            if media_id:
                ids_info.append(f"MediaID: {media_id}")
            if title_id:
                ids_info.append(f"TitleID: {title_id}")
            ids_str = ", ".join(ids_info)
            
            self._log(f"Searching TUs for '{nombre}' ({ids_str})...")

            tus = buscar_tus(media_id=media_id, title_id=title_id, token=self.token, api_key=self.api_key)
            if tus is None:
                self._log(f"  ERROR querying TUs for {nombre}.")
                errores += 1
                self.progress["value"] = idx
                self.root.update_idletasks()
                continue
            elif len(tus) == 0:
                self._log(f"  No TUs found for {nombre}.")
                self.progress["value"] = idx
                self.root.update_idletasks()
                continue

            juegos_con_tu += 1
            num_tus = len(tus)
            self._log(f"  Found {num_tus} TUs for {nombre}. Downloading...")

            # Crear carpeta para el juego
            nombre_carpeta = self._limpiar_nombre_archivo(nombre)
            carpeta_juego = os.path.join(carpeta_destino, nombre_carpeta)
            
            try:
                os.makedirs(carpeta_juego, exist_ok=True)
                self._log(f"  Folder created: {nombre_carpeta}")
            except Exception as e:
                self._log(f"  ERROR creating folder for {nombre}: {e}")
                errores += 1
                self.progress["value"] = idx
                self.root.update_idletasks()
                continue

            for tu in tus:
                filename = tu["fileName"]
                url = tu["downloadUrl"]
                destino = os.path.join(carpeta_juego, filename)

                def actualizar_progreso(descargado, total):
                    if total > 0:
                        porcentaje = (descargado / total) * 100
                        self.progress["value"] = porcentaje
                        self.root.update_idletasks()

                self._log(f"    Downloading {filename} to {nombre_carpeta}/...")
                exito = descargar_tu(url, destino, progreso_callback=actualizar_progreso)
                if exito:
                    self._log(f"    Downloaded {filename} successfully to {nombre_carpeta}/")
                    total_tus_descargados += 1
                else:
                    self._log(f"    ERROR downloading {filename}.")
                    errores += 1

            self.progress["value"] = idx
            self.root.update_idletasks()

        self._log("\nSummary:\n")
        self._log(f"Games processed: {total_juegos}")
        self._log(f"Games with TUs found: {juegos_con_tu}")
        self._log(f"TUs downloaded: {total_tus_descargados}")
        self._log(f"Errors: {errores}")
        self.progress["value"] = 0

        messagebox.showinfo("Process completed", "TU search and download has finished.")

    def copy_media_id(self):
        self._copy_id_from_tree(1, "MediaID")

    def copy_title_id(self):
        self._copy_id_from_tree(2, "TitleID")
    
    def _copy_id_from_tree(self, column_index, id_type):
        """Generic function to copy ID from tree view"""
        # Get selected item
        selected_items = self.tree.selection()
        if not selected_items:
            # If no selection, use focused item
            item = self.tree.focus()
            if not item:
                messagebox.showwarning("Warning", "Please select a game from the list")
                return
        else:
            item = selected_items[0]
        
        try:
            values = self.tree.item(item)["values"]
            if len(values) >= column_index + 1:
                id_value = str(values[column_index]).strip()
                if id_value and id_value != "N/A" and id_value != "":
                    self._copiar_al_portapapeles(id_value, id_type)
                else:
                    messagebox.showwarning("Warning", f"This game doesn't have {id_type} available")
            else:
                messagebox.showwarning("Error", "Could not get game information")
        except Exception as e:
            messagebox.showerror("Error", f"Error copying {id_type}: {e}")

    def _copiar_al_portapapeles(self, texto, tipo):
        """Helper function to copy text to clipboard robustly"""
        print(f"[DEBUG] Attempting to copy {tipo}: '{texto}'")
        
        try:
            # Clean and prepare text
            texto_limpio = str(texto).strip()
            if not texto_limpio:
                messagebox.showwarning("Error", f"The {tipo} is empty")
                return False
            
            # Method 1: Tkinter clipboard (most reliable)
            self.root.clipboard_clear()
            self.root.clipboard_append(texto_limpio)
            self.root.update()
            
            # Small pause to ensure it's copied
            import time
            time.sleep(0.1)
            
            # Verify it was copied correctly
            try:
                clipboard_content = self.root.clipboard_get()
                if clipboard_content == texto_limpio:
                    messagebox.showinfo("✅ Copied", f"{tipo}: {texto_limpio}\n\nCopied to clipboard successfully")
                    print(f"[DEBUG] Copied successfully: '{clipboard_content}'")
                    return True
                else:
                    print(f"[DEBUG] Verification failed. Expected: '{texto_limpio}', Got: '{clipboard_content}'")
                    raise Exception("Clipboard verification failed")
            except tk.TclError:
                # If can't verify, assume it worked
                messagebox.showinfo("✅ Copied", f"{tipo}: {texto_limpio}\n\nCopied to clipboard")
                return True
                
        except Exception as e:
            print(f"[DEBUG] Error in method 1: {e}")
            # Method 2: Use xclip as fallback (Linux)
            try:
                import subprocess
                print(f"[DEBUG] Trying xclip...")
                process = subprocess.Popen(['xclip', '-selection', 'clipboard'], 
                                         stdin=subprocess.PIPE, 
                                         stdout=subprocess.PIPE, 
                                         stderr=subprocess.PIPE)
                stdout, stderr = process.communicate(input=texto_limpio.encode('utf-8'))
                
                if process.returncode == 0:
                    messagebox.showinfo("✅ Copied", f"{tipo}: {texto_limpio}\n\nCopied to clipboard (xclip)")
                    print(f"[DEBUG] xclip successful")
                    return True
                else:
                    print(f"[DEBUG] xclip failed: {stderr.decode()}")
                    raise Exception("xclip failed")
            except FileNotFoundError:
                print("[DEBUG] xclip is not installed")
            except Exception as e2:
                print(f"[DEBUG] Error in xclip: {e2}")
            
            # Method 3: Show text for manual copying
            messagebox.showinfo("📋 Copy manually", 
                               f"Could not copy automatically.\n\n{tipo}: {texto_limpio}\n\n" +
                               "Select and copy this text manually (Ctrl+C)")
            return False

    def _limpiar_nombre_archivo(self, nombre):
        """Clean game name to use as folder name"""
        import re
        
        # Replace invalid characters for folder names
        nombre_limpio = re.sub(r'[<>:"/\\|?*]', '_', nombre)
        
        # Replace multiple spaces and underscores with single one
        nombre_limpio = re.sub(r'[_\s]+', '_', nombre_limpio)
        
        # Remove underscores at beginning and end
        nombre_limpio = nombre_limpio.strip('_')
        
        # Limit length to avoid filesystem issues
        if len(nombre_limpio) > 100:
            nombre_limpio = nombre_limpio[:100].rstrip('_')
        
        # If empty, use default name
        if not nombre_limpio:
            nombre_limpio = "Unknown_Game"
        
        return nombre_limpio

    def mostrar_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.menu_popup.post(event.x_root, event.y_root)

    def exportar_lista_html(self):
        """Export the game list to an HTML file"""
        if not self.juegos:
            messagebox.showwarning("Warning", "No games to export. First select a folder with games.")
            return
        
        # Request location to save the file
        archivo_destino = filedialog.asksaveasfilename(
            title="Save game list as HTML",
            defaultextension=".html",
            filetypes=[("HTML files", "*.html"), ("All files", "*.*")],
            initialfile="xbox360_games_list.html"
        )
        
        if not archivo_destino:
            return
        
        try:
            self._log("Generating HTML list...")
            
            # Generate HTML content
            html_content = self._generar_html_lista()
            
            # Write file
            with open(archivo_destino, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self._log(f"HTML list exported successfully: {archivo_destino}")
            messagebox.showinfo("Success", f"List exported successfully:\n{archivo_destino}\n\nTotal games: {len(self.juegos)}")
            
        except Exception as e:
            error_msg = f"Error exporting HTML list: {e}"
            self._log(error_msg)
            messagebox.showerror("Error", error_msg)
    
    def _generar_html_lista(self):
        """Generate HTML content for the game list"""
        from datetime import datetime
        
        # Get current date and time
        fecha_actual = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
        
        # HTML template
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Xbox 360 Games List - X360 TU Manager</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #4CAF50, #2196F3);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header p {{
            margin: 10px 0 0 0;
            opacity: 0.9;
            font-size: 1.1em;
        }}
        .stats {{
            background-color: #f8f9fa;
            padding: 20px;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            justify-content: space-around;
            flex-wrap: wrap;
        }}
        .stat-item {{
            text-align: center;
            margin: 10px;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #2196F3;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .table-container {{
            padding: 20px;
            overflow-x: auto;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        th, td {{
            padding: 12px 15px;
            text-align: left;
            border-bottom: 1px solid #e9ecef;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            position: sticky;
            top: 0;
            z-index: 10;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .game-name {{
            font-weight: 500;
            color: #2c3e50;
        }}
        .id-code {{
            font-family: 'Courier New', monospace;
            background-color: #e9ecef;
            padding: 4px 8px;
            border-radius: 4px;
            font-size: 0.9em;
            color: #495057;
        }}
        .copy-btn {{
            background-color: #6c757d;
            color: white;
            border: none;
            padding: 4px 8px;
            border-radius: 3px;
            cursor: pointer;
            font-size: 0.8em;
            margin-left: 5px;
        }}
        .copy-btn:hover {{
            background-color: #5a6268;
        }}
        .footer {{
            background-color: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            border-top: 1px solid #e9ecef;
        }}
        .search-box {{
            margin: 20px;
            padding: 10px;
            width: calc(100% - 40px);
            border: 2px solid #e9ecef;
            border-radius: 5px;
            font-size: 16px;
        }}
        .search-box:focus {{
            outline: none;
            border-color: #2196F3;
        }}
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2em;
            }}
            .stats {{
                flex-direction: column;
            }}
            th, td {{
                padding: 8px 10px;
                font-size: 0.9em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎮 Xbox 360 Games List</h1>
            <p>Generated by X360 TU Manager - {fecha_actual}</p>
        </div>
        
        <div class="stats">
            <div class="stat-item">
                <div class="stat-number">{len(self.juegos)}</div>
                <div class="stat-label">Games Detected</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len([j for j in self.juegos if j.get('media_id')])}</div>
                <div class="stat-label">With MediaID</div>
            </div>
            <div class="stat-item">
                <div class="stat-number">{len([j for j in self.juegos if j.get('title_id')])}</div>
                <div class="stat-label">With TitleID</div>
            </div>
        </div>
        
        <div class="table-container">
            <input type="text" class="search-box" id="searchBox" placeholder="🔍 Search games..." onkeyup="filterGames()">
            
            <table id="gamesTable">
                <thead>
                    <tr>
                        <th>#</th>
                        <th>🎮 Game Name</th>
                        <th>🆔 MediaID</th>
                        <th>🏷️ TitleID</th>
                        <th>📋 Actions</th>
                    </tr>
                </thead>
                <tbody>"""
        
        # Add game rows
        for i, juego in enumerate(self.juegos, 1):
            nombre = juego.get('nombre', 'Unknown')
            media_id = juego.get('media_id', 'N/A')
            title_id = juego.get('title_id', 'N/A')
            
            # Escape HTML characters and quotes for JavaScript
            nombre_escaped = nombre.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", "\\'")
            media_id_str = str(media_id) if media_id != 'N/A' else 'N/A'
            title_id_str = str(title_id) if title_id != 'N/A' else 'N/A'
            
            # Create copy buttons conditionally
            media_btn = f'<button class="copy-btn" onclick="copyText(\'{media_id_str}\')" title="Copy MediaID">📋</button>' if media_id != 'N/A' else ''
            title_btn = f'<button class="copy-btn" onclick="copyText(\'{title_id_str}\')" title="Copy TitleID">📋</button>' if title_id != 'N/A' else ''
            
            html_template += f"""
                    <tr>
                        <td>{i}</td>
                        <td class="game-name">{nombre}</td>
                        <td>
                            <span class="id-code">{media_id_str}</span>
                            {media_btn}
                        </td>
                        <td>
                            <span class="id-code">{title_id_str}</span>
                            {title_btn}
                        </td>
                        <td>
                            <button class="copy-btn" onclick="copyGame('{nombre_escaped}', '{media_id_str}', '{title_id_str}')" title="Copy complete information">📄 All</button>
                        </td>
                    </tr>"""
        
        # Cerrar HTML
        html_template += f"""
                </tbody>
            </table>
        </div>
        
        <div class="footer">
            <p><strong>X360 TU Manager</strong> - Tool for Xbox 360 Title Updates management</p>
            <p>List generated on {fecha_actual}</p>
        </div>
    </div>
    
    <script>
        function filterGames() {{
            const input = document.getElementById('searchBox');
            const filter = input.value.toUpperCase();
            const table = document.getElementById('gamesTable');
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {{
                const cells = rows[i].getElementsByTagName('td');
                let found = false;
                
                for (let j = 0; j < cells.length; j++) {{
                    if (cells[j].textContent.toUpperCase().indexOf(filter) > -1) {{
                        found = true;
                        break;
                    }}
                }}
                
                rows[i].style.display = found ? '' : 'none';
            }}
        }}
        
        function copyText(texto) {{
            navigator.clipboard.writeText(texto).then(function() {{
                showNotification('Copied: ' + texto);
            }}).catch(function(err) {{
                console.error('Copy error: ', err);
                // Fallback for older browsers
                const textArea = document.createElement('textarea');
                textArea.value = texto;
                document.body.appendChild(textArea);
                textArea.select();
                document.execCommand('copy');
                document.body.removeChild(textArea);
                showNotification('Copied: ' + texto);
            }});
        }}
        
        function copyGame(nombre, mediaId, titleId) {{
            const info = `Game: ${{nombre}}\\nMediaID: ${{mediaId}}\\nTitleID: ${{titleId}}`;
            copyText(info);
        }}
        
        function showNotification(mensaje) {{
            // Create temporary notification
            const notif = document.createElement('div');
            notif.textContent = mensaje;
            notif.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #4CAF50;
                color: white;
                padding: 10px 20px;
                border-radius: 5px;
                z-index: 1000;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            `;
            document.body.appendChild(notif);
            
            setTimeout(() => {{
                document.body.removeChild(notif);
            }}, 2000);
        }}
        
        // Real-time statistics
        function updateStatistics() {{
            const table = document.getElementById('gamesTable');
            const rows = table.getElementsByTagName('tr');
            let visibleCount = 0;
            
            for (let i = 1; i < rows.length; i++) {{
                if (rows[i].style.display !== 'none') {{
                    visibleCount++;
                }}
            }}
            
            // Update counter if filter is active
            const searchBox = document.getElementById('searchBox');
            if (searchBox.value.trim() !== '') {{
                document.title = `Xbox 360 List - Showing ${{visibleCount}} of {len(self.juegos)} games`;
            }} else {{
                document.title = 'Xbox 360 Games List - X360 TU Manager';
            }}
        }}
        
        // Actualizar estadísticas cuando se filtra
        document.getElementById('searchBox').addEventListener('input', actualizarEstadisticas);
    </script>
</body>
</html>"""
        
        return html_template

    def preparar_usb_xbox360(self):
        """Prepare USB structure for Xbox 360 with downloaded TUs"""
        if not self.juegos:
            messagebox.showwarning("Warning", "No games detected. First select a folder with games.")
            return
        
        # Request folder where TUs are downloaded
        carpeta_tus = filedialog.askdirectory(title="Select the folder where you downloaded the TUs")
        if not carpeta_tus:
            return
        
        # Check if there are downloaded TUs
        tus_encontrados = self._buscar_tus_descargados(carpeta_tus)
        if not tus_encontrados:
            messagebox.showwarning("Warning", "No downloaded TUs found in the selected folder.")
            return
        
        # Execute in thread to avoid blocking GUI
        threading.Thread(target=self._crear_estructura_usb, args=(carpeta_tus, tus_encontrados), daemon=True).start()
    
    def _buscar_tus_descargados(self, carpeta_base):
        """Search for downloaded .tu files in folder structure"""
        tus_encontrados = []
        
        try:
            for root, dirs, files in os.walk(carpeta_base):
                for file in files:
                    if file.endswith('.tu'):
                        ruta_completa = os.path.join(root, file)
                        
                        # Extract TitleID from filename
                        title_id = None
                        if '_' in file:
                            title_id = file.split('_')[0]
                        
                        # Find corresponding game in our list
                        juego_info = None
                        for juego in self.juegos:
                            if juego.get('title_id') == title_id:
                                juego_info = juego
                                break
                        
                        if juego_info:
                            tus_encontrados.append({
                                'archivo': file,
                                'ruta_completa': ruta_completa,
                                'title_id': title_id,
                                'media_id': juego_info.get('media_id'),
                                'nombre_juego': juego_info.get('nombre')
                            })
                            
            return tus_encontrados
            
        except Exception as e:
            self._log(f"[ERROR] Error searching TUs: {e}")
            return []
    
    def _crear_estructura_usb(self, carpeta_base, tus_encontrados):
        """Create USB structure for Xbox 360"""
        try:
            # Create USB_Xbox360 folder in the same directory
            carpeta_usb = os.path.join(carpeta_base, "USB_Xbox360")
            
            self._log("Starting USB structure preparation for Xbox 360...")
            self._log(f"Destination folder: {carpeta_usb}")
            
            # Create base structure
            content_path = os.path.join(carpeta_usb, "Content", "0000000000000000")
            os.makedirs(content_path, exist_ok=True)
            
            total_tus = len(tus_encontrados)
            self.progress["value"] = 0
            self.progress["maximum"] = total_tus
            
            tus_procesados = 0
            errores = 0
            
            for idx, tu_info in enumerate(tus_encontrados, 1):
                try:
                    title_id = tu_info['title_id']
                    archivo = tu_info['archivo']
                    ruta_origen = tu_info['ruta_completa']
                    nombre_juego = tu_info['nombre_juego']
                    
                    self._log(f"Processing TU for '{nombre_juego}' (TitleID: {title_id})...")
                    
                    # Create structure: Content/0000000000000000/[TitleID]/000B0000/
                    tu_path = os.path.join(content_path, title_id, "000B0000")
                    os.makedirs(tu_path, exist_ok=True)
                    
                    # Copy TU file
                    destino = os.path.join(tu_path, archivo)
                    
                    import shutil
                    shutil.copy2(ruta_origen, destino)
                    
                    self._log(f"  ✅ Copied: {archivo}")
                    tus_procesados += 1
                    
                except Exception as e:
                    self._log(f"  ❌ ERROR processing {tu_info['archivo']}: {e}")
                    errores += 1
                
                self.progress["value"] = idx
                self.root.update_idletasks()
            
            self.progress["value"] = 0
            
            self._log("\n" + "="*50)
            self._log("USB PREPARATION COMPLETED")
            self._log("="*50)
            self._log(f"Folder created: {carpeta_usb}")
            self._log(f"TUs processed: {tus_procesados}")
            self._log(f"Errors: {errores}")
            
            messagebox.showinfo(
                "USB Prepared", 
                f"USB structure created successfully:\n\n"
                f"📁 Location: {carpeta_usb}\n"
                f"🎮 TUs processed: {tus_procesados}\n"
                f"❌ Errors: {errores}\n\n"
                f"Now you can copy the 'Content' folder to your USB drive."
            )
            
        except Exception as e:
            error_msg = f"Error creating USB structure: {e}"
            self._log(error_msg)
            messagebox.showerror("Error", error_msg)

    def _log(self, texto):
        def actualizar_log():
            self.log_text.config(state="normal")
            self.log_text.insert("end", texto + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")
        
        # Si estamos en el hilo principal, actualizar directamente
        # Si no, usar after() para ejecutar en el hilo principal
        try:
            self.root.after(0, actualizar_log)
        except:
            actualizar_log()

if __name__ == "__main__":
    root = tk.Tk()
    app = XboxTUMApp(root)
    root.mainloop()