import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

# Design System Colors (Matching RSS Deck)
COLOR_BG = "#080c14"
COLOR_CARD = "#0f1624"
COLOR_ACCENT = "#3b82f6"
COLOR_TEXT = "#f3f4f6"
COLOR_MUTED = "#9ca3af"
COLOR_SUCCESS = "#10b981"

class RSSDeckInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("Instalador - RSS Deck")
        self.root.geometry("640x520")
        self.root.configure(bg=COLOR_BG)
        self.root.resizable(False, False)

        # Style Configuration
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('.', background=COLOR_BG, foreground=COLOR_TEXT)
        self.style.configure('TLabel', background=COLOR_BG, foreground=COLOR_TEXT, font=('Inter', 10))
        self.style.configure('Header.TLabel', background=COLOR_BG, foreground=COLOR_TEXT, font=('Outfit', 16, 'bold'))
        self.style.configure('Sub.TLabel', background=COLOR_BG, foreground=COLOR_MUTED, font=('Inter', 9))
        self.style.configure('TCheckbutton', background=COLOR_BG, foreground=COLOR_TEXT, font=('Inter', 10))

        # Variables
        self.install_dir = tk.StringVar(value=os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "RSSDeck"))
        self.license_accepted = tk.BooleanVar(value=False)
        self.progress_val = tk.DoubleVar(value=0)

        # Build Frames
        self.frames = {}
        self.create_license_frame()
        self.create_directory_frame()
        self.create_installing_frame()
        self.create_finished_frame()

        self.show_frame("license")

    def show_frame(self, name):
        for frame in self.frames.values():
            frame.pack_forget()
        self.frames[name].pack(fill="both", expand=True, padx=20, pady=20)

    def create_license_frame(self):
        frame = tk.Frame(self.root, bg=COLOR_BG)
        self.frames["license"] = frame

        # Title
        header = ttk.Label(frame, text="Contrato de Licença de Software", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 5))

        desc = ttk.Label(frame, text="Por favor, leia e aceite os termos da Licença GPLv3 abaixo para continuar:", style="Sub.TLabel")
        desc.pack(anchor="w", pady=(0, 10))

        # License text area (Scrollable)
        text_frame = tk.Frame(frame, bg=COLOR_CARD, bd=1, relief="solid")
        text_frame.pack(fill="both", expand=True, pady=10)

        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side="right", fill="y")

        text_widget = tk.Text(text_frame, bg=COLOR_CARD, fg=COLOR_TEXT, insertbackground=COLOR_TEXT,
                              wrap="word", yscrollcommand=scrollbar.set, font=('Consolas', 9), bd=0, padx=10, pady=10)
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=text_widget.yview)

        # Load LICENSE file content
        license_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "LICENSE")
        if os.path.exists(license_path):
            with open(license_path, "r", encoding="utf-8") as f:
                text_widget.insert("1.0", f.read())
        else:
            text_widget.insert("1.0", "Arquivo LICENSE não encontrado na pasta de origem.")
        text_widget.config(state="disabled")

        # Bottom Checkbox and Button Row
        bottom_row = tk.Frame(frame, bg=COLOR_BG)
        bottom_row.pack(fill="x", pady=(10, 0))

        checkbox = ttk.Checkbutton(bottom_row, text="Eu aceito os termos da licença",
                                   variable=self.license_accepted, command=self.toggle_license_btn)
        checkbox.pack(side="left")

        self.license_next_btn = tk.Button(bottom_row, text="Avançar", bg=COLOR_MUTED, fg=COLOR_BG,
                                           font=('Inter', 10, 'bold'), state="disabled", relief="flat", padx=20, pady=5,
                                           command=lambda: self.show_frame("directory"))
        self.license_next_btn.pack(side="right")

    def toggle_license_btn(self):
        if self.license_accepted.get():
            self.license_next_btn.config(state="normal", bg=COLOR_ACCENT, fg=COLOR_TEXT, activebackground="#2563eb", cursor="hand2")
        else:
            self.license_next_btn.config(state="disabled", bg=COLOR_MUTED, fg=COLOR_BG, cursor="")

    def create_directory_frame(self):
        frame = tk.Frame(self.root, bg=COLOR_BG)
        self.frames["directory"] = frame

        # Title
        header = ttk.Label(frame, text="Escolha a Pasta de Destino", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 5))

        desc = ttk.Label(frame, text="O instalador copiará os arquivos do RSS Deck na seguinte pasta:", style="Sub.TLabel")
        desc.pack(anchor="w", pady=(0, 20))

        # Folder select input row
        input_frame = tk.Frame(frame, bg=COLOR_BG)
        input_frame.pack(fill="x", pady=10)

        entry = tk.Entry(input_frame, textvariable=self.install_dir, bg=COLOR_CARD, fg=COLOR_TEXT,
                         insertbackground=COLOR_TEXT, font=('Inter', 11), bd=1, relief="solid")
        entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 10))

        btn_browse = tk.Button(input_frame, text="Procurar...", bg=COLOR_CARD, fg=COLOR_TEXT,
                               font=('Inter', 10), relief="solid", bd=1, padx=15, pady=5, cursor="hand2",
                               command=self.browse_folder)
        btn_browse.pack(side="right")

        # Info details box
        info_box = tk.Label(frame, text="O aplicativo será configurado para rodar silenciosamente em segundo plano\n"
                                        "na bandeja do sistema. Um atalho de inicialização rápida será criado no Desktop.",
                            bg=COLOR_CARD, fg=COLOR_MUTED, font=('Inter', 9), justify="left", bd=1, relief="solid", padx=15, pady=15)
        info_box.pack(fill="x", pady=20)

        # Bottom controls row
        bottom_row = tk.Frame(frame, bg=COLOR_BG)
        bottom_row.pack(fill="x", side="bottom")

        btn_back = tk.Button(bottom_row, text="Voltar", bg=COLOR_CARD, fg=COLOR_TEXT,
                             font=('Inter', 10), relief="solid", bd=1, padx=20, pady=5, cursor="hand2",
                             command=lambda: self.show_frame("license"))
        btn_back.pack(side="left")

        btn_install = tk.Button(bottom_row, text="Instalar", bg=COLOR_ACCENT, fg=COLOR_TEXT,
                                font=('Inter', 10, 'bold'), relief="flat", padx=25, pady=5, cursor="hand2",
                                command=self.start_installation)
        btn_install.pack(side="right")

    def browse_folder(self):
        selected = filedialog.askdirectory(initialdir=self.install_dir.get(), title="Selecione a pasta de destino")
        if selected:
            # Standardize path slashes for Windows
            self.install_dir.set(os.path.normpath(selected))

    def create_installing_frame(self):
        frame = tk.Frame(self.root, bg=COLOR_BG)
        self.frames["installing"] = frame

        # Title
        header = ttk.Label(frame, text="Instalando RSS Deck", style="Header.TLabel")
        header.pack(anchor="w", pady=(0, 5))

        self.install_status_lbl = ttk.Label(frame, text="Aguardando início...", style="Sub.TLabel")
        self.install_status_lbl.pack(anchor="w", pady=(0, 30))

        # Progress bar
        progress_frame = tk.Frame(frame, bg=COLOR_BG)
        progress_frame.pack(fill="x", pady=20)
        
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_val, maximum=100, mode='determinate')
        self.progress_bar.pack(fill="x", ipady=4)

        self.progress_lbl = ttk.Label(frame, text="0%", font=('Inter', 10, 'bold'))
        self.progress_lbl.pack(pady=10)

    def create_finished_frame(self):
        frame = tk.Frame(self.root, bg=COLOR_BG)
        self.frames["finished"] = frame

        # Visual check indicator (styled text)
        check_lbl = tk.Label(frame, text="✓", font=('Outfit', 64), fg=COLOR_SUCCESS, bg=COLOR_BG)
        check_lbl.pack(pady=(20, 10))

        # Title
        header = tk.Label(frame, text="Instalação Concluída!", font=('Outfit', 18, 'bold'), fg=COLOR_TEXT, bg=COLOR_BG)
        header.pack(pady=10)

        desc = tk.Label(frame, text="O RSS Deck foi instalado com sucesso.\n"
                                    "O atalho na Área de Trabalho executará o programa silenciosamente na System Tray.",
                        font=('Inter', 10), fg=COLOR_MUTED, bg=COLOR_BG, justify="center")
        desc.pack(pady=10)

        # Run checkbox
        self.run_app_var = tk.BooleanVar(value=True)
        chk_run = ttk.Checkbutton(frame, text="Iniciar o RSS Deck agora", variable=self.run_app_var)
        chk_run.pack(pady=20)

        # Finish button
        btn_finish = tk.Button(frame, text="Concluir", bg=COLOR_ACCENT, fg=COLOR_TEXT,
                               font=('Inter', 10, 'bold'), relief="flat", padx=30, pady=8, cursor="hand2",
                               command=self.finish_installation)
        btn_finish.pack()

    def start_installation(self):
        self.show_frame("installing")
        self.root.update_idletasks()
        self.root.after(100, self.run_copy_files)

    def run_copy_files(self):
        dest = self.install_dir.get()
        source = os.path.dirname(os.path.abspath(__file__))
        
        try:
            self.update_progress(10, "Criando diretório de destino...")
            os.makedirs(dest, exist_ok=True)

            self.update_progress(20, "Copiando arquivos de código e recursos...")
            
            # Copy Python files
            shutil.copy2(os.path.join(source, "app.py"), os.path.join(dest, "app.py"))
            shutil.copy2(os.path.join(source, "LICENSE"), os.path.join(dest, "LICENSE"))
            shutil.copy2(os.path.join(source, "README.md"), os.path.join(dest, "README.md"))
            shutil.copy2(os.path.join(source, "dashboard.png"), os.path.join(dest, "dashboard.png"))
            shutil.copy2(os.path.join(source, "requirements.txt"), os.path.join(dest, "requirements.txt"))
            
            # Copy app icon if it exists, otherwise generate it
            icon_src = os.path.join(source, "app_icon.ico")
            icon_dest = os.path.join(dest, "app_icon.ico")
            if os.path.exists(icon_src):
                shutil.copy2(icon_src, icon_dest)
            else:
                try:
                    from PIL import Image, ImageDraw
                    image = Image.new('RGB', (64, 64), color=(15, 22, 36))
                    dc = ImageDraw.Draw(image)
                    dc.ellipse([8, 8, 56, 56], outline=(59, 130, 246), width=5)
                    dc.ellipse([20, 20, 44, 44], outline=(245, 158, 11), width=4)
                    dc.ellipse([28, 28, 36, 36], fill=(16, 185, 129))
                    image.save(icon_dest, format="ICO", sizes=[(64, 64), (32, 32), (16, 16)])
                    print("Generated app_icon.ico in installer dest.")
                except Exception as e:
                    print(f"Could not generate app_icon.ico in installer: {e}")

            # Copy Static folder recursively
            static_dest = os.path.join(dest, "static")
            if os.path.exists(static_dest):
                shutil.rmtree(static_dest)
            shutil.copytree(os.path.join(source, "static"), static_dest)

            # Copy existing SQLite DB if it exists to preserve current config
            db_source = os.path.join(source, "rss_deck.db")
            if os.path.exists(db_source):
                self.update_progress(40, "Importando banco de dados local existente...")
                shutil.copy2(db_source, os.path.join(dest, "rss_deck.db"))

            self.update_progress(50, "Instalando dependências via pip (isso pode levar alguns instantes)...")
            self.root.update()
            
            # Hide console window on Windows
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE

            # Determine python interpreter safely (sys.executable is installer.exe when frozen)
            python_exe = sys.executable
            if getattr(sys, 'frozen', False):
                python_exe = "python"
                try:
                    subprocess.run(["python", "--version"], startupinfo=startupinfo, capture_output=True)
                except Exception:
                    try:
                        subprocess.run(["py", "--version"], startupinfo=startupinfo, capture_output=True)
                        python_exe = "py"
                    except Exception:
                        pass

            # Run pip silently using appropriate Python environment
            pip_cmd = [python_exe, "-m", "pip", "install", "-r", "requirements.txt"]
            proc = subprocess.run(pip_cmd, cwd=dest, startupinfo=startupinfo, capture_output=True)
            if proc.returncode != 0:
                print(f"Pip warning/error code {proc.returncode}: {proc.stderr.decode('utf-8', errors='ignore')}")

            self.update_progress(80, "Criando atalho na Área de Trabalho...")
            self.create_desktop_shortcut(dest)

            self.update_progress(100, "Instalação concluída com sucesso!")
            self.root.after(500, lambda: self.show_frame("finished"))
            
        except Exception as e:
            messagebox.showerror("Erro de Instalação", f"Ocorreu um erro durante a instalação:\n{str(e)}")
            self.show_frame("directory")

    def update_progress(self, val, status):
        self.progress_val.set(val)
        self.progress_lbl.config(text=f"{int(val)}%")
        self.install_status_lbl.config(text=status)
        self.root.update()

    def create_desktop_shortcut(self, install_dir):
        import winreg
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
            desktop, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
            desktop = os.path.expandvars(desktop)
        except Exception:
            desktop = os.path.join(os.path.expanduser("~"), "Desktop")
            
        shortcut_path = os.path.join(desktop, "RSS Deck.lnk")
        
        # Get location of pythonw.exe inside current Python environment
        python_full_path = None
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
        startupinfo.wShowWindow = subprocess.SW_HIDE
        
        if getattr(sys, 'frozen', False):
            # Try running python / py to get absolute path
            for exe_name in ["python", "py"]:
                try:
                    proc = subprocess.run([exe_name, "-c", "import sys; print(sys.executable)"],
                                          startupinfo=startupinfo, capture_output=True, text=True, timeout=2)
                    if proc.returncode == 0:
                        python_full_path = proc.stdout.strip()
                        break
                except Exception:
                    pass
        else:
            python_full_path = sys.executable

        if python_full_path:
            python_dir = os.path.dirname(python_full_path)
            pythonw_path = os.path.join(python_dir, "pythonw.exe")
        else:
            pythonw_path = "pythonw.exe"

        if not os.path.exists(pythonw_path):
            pythonw_path = "pythonw.exe"  # Fallback to PATH resolution

        app_py_path = os.path.join(install_dir, "app.py")
        app_icon_path = os.path.join(install_dir, "app_icon.ico")
        
        # Clean path variables for PowerShell single/double quote injection safety
        app_py_path_clean = os.path.normpath(app_py_path)
        pythonw_path_clean = os.path.normpath(pythonw_path)
        install_dir_clean = os.path.normpath(install_dir)
        shortcut_path_clean = os.path.normpath(shortcut_path)
        app_icon_path_clean = os.path.normpath(app_icon_path)

        # PowerShell automation script to create COM WScript.Shell shortcut with icon
        ps_script = f"""
        $Shell = New-Object -ComObject WScript.Shell
        $Shortcut = $Shell.CreateShortcut("{shortcut_path_clean}")
        $Shortcut.TargetPath = "{pythonw_path_clean}"
        $Shortcut.Arguments = '"{app_py_path_clean}"'
        $Shortcut.WorkingDirectory = "{install_dir_clean}"
        $Shortcut.IconLocation = "{app_icon_path_clean}"
        $Shortcut.Save()
        """
        
        try:
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
            subprocess.run(["powershell", "-Command", ps_script], startupinfo=startupinfo, capture_output=True, check=True)
        except Exception as e:
            print(f"Error creating shortcut: {e}")

    def finish_installation(self):
        if self.run_app_var.get():
            dest = self.install_dir.get()
            python_dir = os.path.dirname(sys.executable)
            pythonw_path = os.path.join(python_dir, "pythonw.exe")
            if not os.path.exists(pythonw_path):
                pythonw_path = "pythonw.exe"
            
            app_py = os.path.join(dest, "app.py")
            
            # Start pythonw.exe app.py in background asynchronously
            try:
                subprocess.Popen([pythonw_path, app_py], cwd=dest, close_fds=True)
            except Exception as e:
                print(f"Could not start app: {e}")
                
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    # Ensure tk environment starts properly
    root = tk.Tk()
    app = RSSDeckInstaller(root)
    root.mainloop()
