#!/usr/bin/env python3

PY4WEBGUI_VERSION = '1.3.0'

import os, pathlib, platform, psutil, shutil, socket, subprocess, sys, time, tomlkit, webbrowser


try:
    import tkinter as tk
except ModuleNotFoundError:
    print('tkinter module not installed or not available')
    exit()

from tkinter import LEFT, ttk, messagebox, scrolledtext
from tkinter import PhotoImage 


Py4web_cmd = ''
Py4web_cwd = os.getcwd()

TOML_FILENAME = 'py4web-gui.toml'


def set_py4web_path():
    if platform.system() == "Darwin" and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): #running in a PyInstaller MacOs bundle
            running_path = pathlib.Path(os.path.dirname(os.path.abspath(__file__))) # it's a MacOs app, Framework dir
            running_path = running_path.parent # Contents dir
            running_path = running_path.parent # .app main dir
            py4web_path = running_path.parent # py4web main dir

            os.chdir(pathlib.Path(py4web_path))
            sys.path.insert(0, f'{py4web_path}/_internal') #needed for reading py4web version

class ToolTip(object):
    def __init__(self, widget):
        self.widget = widget
        self.tipwindow = None
        self.id = None
        self.x = self.y = 0

    def showtip(self, text):
        "Display text in tooltip window"
        self.text = text
        if self.tipwindow or not self.text:
            return
        x, y, _cx, cy = self.widget.bbox("insert")
        x = x + self.widget.winfo_rootx() + 25
        y = y + cy + self.widget.winfo_rooty() + 25
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(1)
        tw.wm_geometry("+%d+%d" % (x, y))
        label = tk.Label(tw, text=self.text, justify=tk.LEFT,
                         background="#ffffe0", relief=tk.SOLID, borderwidth=1,
                         font=("tahoma", "8", "normal"))
        label.pack(ipadx=1)

    def hidetip(self):
        tw = self.tipwindow
        self.tipwindow = None
        if tw:
            tw.destroy()

def create_tooltip(widget, text):
    tooltip = ToolTip(widget)
    def enter(event):
        tooltip.showtip(text)
    def leave(event):
        tooltip.hidetip()
    widget.bind('<Enter>', enter)
    widget.bind('<Leave>', leave)


def add_proc_info_from_cmd(proc_info, cmdline):
    proc_info["port"] = check_cmdline(cmdline, '-P', '--port', '8000')
    proc_info["ssl_cert"] = check_cmdline(cmdline, '--ssl_cert', False, False)
    if proc_info["ssl_cert"]:
        proc_info["protocol"]="https"
    else:
        proc_info["protocol"]="http"
    proc_info["ssl_key"] = check_cmdline(cmdline, '--ssl_key', False, False)
    proc_info["url_prefix"] = check_cmdline(cmdline, '-U', '--url_prefix', False)
    if not proc_info["url_prefix"]:
        proc_info["url_prefix"] = ''
    #proc_info["instance_name"] = ''
    if not proc_info.get("stopped") == True:
        proc_info["stopped"] = False
    errorlog = check_cmdline(cmdline, '--errorlog', False, False)
    if errorlog:
        if os.path.isdir(errorlog):
            log_file = os.path.join(errorlog, "server-py4web.log")
        else:
            log_file = errorlog
    else:
        log_file = False
    proc_info["errorlog"] = log_file
    proc_info["loglevel"] = check_cmdline(cmdline, '-L', '--logging_level', '30')
    proc_info["pw_file"] = check_cmdline(cmdline, '-p', '--password_file', 'password.txt')
    proc_info["host"] = check_cmdline(cmdline, '-H', '--host', '127.0.0.1')
    proc_info["server"] = check_cmdline(cmdline, '-s', '--server', 'default')
    proc_info["workers"] = check_cmdline(cmdline, '-w', '--number_workers', '0')
    proc_info["dash_mode"] = check_cmdline(cmdline, '-d', '--dashboard_mode', 'full')
    proc_info["watch"] = check_cmdline(cmdline, '--watch', False, 'lazy')
    proc_info["debug"] = check_cmdline(cmdline, '-D', '--debug', False)
    proc_info["app_names"] = check_cmdline(cmdline, '-A', '--app_names', 'all')

    return proc_info


def find_processes_by_name_and_command(command_substring1, command_substring2):
    """
    List all processes that contain the given substrings in their name and command line arguments.

    :return: List of matching processes.
    """
    matching_processes = []
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'cwd']):
        try:
            # Check if the process name contains the python substring
            process_name = proc.info['name']
            if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): #running in a PyInstaller bundle
                py_bin = 'PY4WEB'
            else:
                py_bin = 'PYTHON'
            if py_bin in process_name.upper():
                # Check if the command line contains the command_substrings
                if any(command_substring1 in arg for arg in proc.info['cmdline']) and \
                    any(command_substring2 in arg for arg in proc.info['cmdline']):
                    # split cmdline also on '=' if needed
                    cmdline = [word for line in proc.info['cmdline'] for word in line.split('=')]
                    
                    proc.info = add_proc_info_from_cmd(proc.info, cmdline)
                    matching_processes.append(proc.info)
        
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue
    
    return matching_processes

def check_cmdline(cmdline, first_match, second_match, default):
    if first_match in cmdline:
        p_index = cmdline.index(first_match)
        if p_index + 1 < len(cmdline):
            return cmdline[p_index + 1]
        else:
            return default
    elif second_match:
        if second_match in cmdline:
            p_index = cmdline.index(second_match)
            if p_index + 1 < len(cmdline):
                return cmdline[p_index + 1]
            else:
                return default
        else:
            return default
    else: # no match
        return default  

def check_Py4web_cmd():
    """
    Check how py4web should be run and save it on Py4web_cmd global variable
    """
    
    global Py4web_cmd 

    # check Python executable
    if shutil.which('python3'):
        Py_run = 'python3'
    else:
        Py_run = 'python'

    if platform.system() == "Windows":
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): #running in a PyInstaller bundle
            Py4web_cmd = 'py4web'
        else:
            Py4web_cmd = f'{Py_run} py4web.py'
    else: # Linux and MacOS
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): #running in a PyInstaller bundle
            Py4web_cmd = './py4web'
        else:
            Py4web_cmd = f'{Py_run} ./py4web.py'
    

def name_running_instance(processes, instance_name, instance_command):
    """
    Find if there is a process already running with the same parameters as an
    instance defined in the toml file, and in this case add the instance name
    """
    already_running = False
    for process in processes:
        if process['cmdline'] ==  instance_command:
            process['instance_name'] =  instance_name
            already_running = True
    return (processes, already_running)

def add_stopped_instance(processes, instance_name, instance_command):
    """
    Add the instance name to the list of the running process
    """
    instance_to_add = {
        'cmdline': instance_command,
        'instance_name' : instance_name,
        'pid':'',
        'cwd': os.getcwd(),
        'stopped' : True,
    }

    proc_info = add_proc_info_from_cmd(instance_to_add, instance_command)
    return add_instance_to_processes(processes, proc_info)



def add_toml_processes(processes):
    """
    Add instances (as defined in the TOML file) to the list of the processes
    """
    
    with open(toml_file, mode="rt", encoding="utf-8") as fp:
            toml = tomlkit.load(fp)
    
    for key, value in toml.items():
        if isinstance(value, dict):
            instance_name = value['name']
            instance_command = (f'{Py4web_cmd} run ' + value['command']).split()

            if processes:
                processes, is_already_running = name_running_instance(processes, instance_name, instance_command)
                if not is_already_running:
                    processes = add_stopped_instance(processes, instance_name, instance_command)
            else:
                processes = add_stopped_instance(processes, instance_name, instance_command)

    minimal_app = {
        'pid' : '',
        'name' : 'python3',
        'protocol' : 'http',
        'port':'8000',
        'url_prefix' : '',
        'cmdline': f'{Py4web_cmd} run apps'.split(),
        'cwd': os.getcwd(),
        'pw_file': 'password.txt',
        'instance_name' : 'MINIMAL',
        'stopped' : True,
    }

    return processes
    

def add_instance_to_processes(processes, app):
    """
    Add a not-running process in the list, so it can be started
    """
    processes.append(app)
    return processes


def search_processes():

    global root
    global result_frame

    processes = find_processes_by_name_and_command('py4web', 'run')
    # processes is a list of dictionaries, with cmdline as a list
    

    try:
        for widget in result_frame.winfo_children():
            widget.destroy()
    except:
            exit(0)
    
    try:
        photo_start = tk.PhotoImage(file = "./docs/images/icon-start.png") 
        photo_stop = tk.PhotoImage(file = "./docs/images/icon-stop.png")
        photo_lens = tk.PhotoImage(file = "./docs/images/icon-lens.png")
    except:
        print("Cannot find icon png files")
        exit(1)

    headers = ["                 Working Directory", "                                      Command Line", 
                 "Protocol", "Port", "  URL prefix", " INSTANCE", " PID","    Action", "        ", "      "]
    
    # add / name instances as defined in the toml file
    processes = add_toml_processes(processes)


    for col, header in enumerate(headers):
        ttk.Label(result_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=col, padx=5, pady=5, sticky='nsew')

    for i, proc in enumerate(processes, start=1):

        # Working directory column
        cwd_text = tk.Text(result_frame, height=1, wrap='none', width=20)
        cwd_text.insert(tk.END, proc['cwd'] if proc['cwd'] else "N/A")
        cwd_text.config(state=tk.DISABLED)
        cwd_text.grid(row=i, column=0, padx=5, pady=2, sticky='nsew')
        create_tooltip(cwd_text, proc['cwd'] if proc['cwd'] else "N/A")

        # Command line column
        cmd_text = tk.Text(result_frame, height=1, wrap='none', width=40)
        cmd_text.insert(tk.END, " ".join(proc['cmdline']))
        cmd_text.config(state=tk.DISABLED)
        cmd_text.grid(row=i, column=1, padx=5, pady=2, sticky='nsew')
        create_tooltip(cmd_text, " ".join(proc['cmdline']))
        
        ttk.Label(result_frame, text=proc['protocol']).grid(row=i, column=2, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['port']).grid(row=i, column=3, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['url_prefix']).grid(row=i, column=4, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['instance_name']).grid(row=i, column=5, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['pid']).grid(row=i, column=6, padx=5, pady=2, sticky='e')

        # PID column
        if proc['stopped']:
            #action_button = ttk.Button(result_frame, text="START", image = photo_start, command=lambda instance_name=proc['instance_name']: start_process(instance_name))
            action_button = ttk.Button(result_frame, image = photo_start, command=lambda proc=proc: start_process(proc))
            action_button.image = photo_start,  # Keep a reference to the image
            if is_port_in_use(proc['port']):
                create_tooltip(action_button, f"Port {proc['port']} not available")
                action_button.config(state=tk.DISABLED)
            action_button.grid(row=i, column=7, padx=5, pady=2, sticky='nsew')
        else: 
            action_button = ttk.Button(result_frame, image = photo_stop, command=lambda pid=proc['pid']: stop_process(pid))
            action_button.image = photo_stop,  # Keep a reference to the image
            action_button.grid(row=i, column=7, padx=5, pady=2, sticky='nsew')
        
        print(f'{proc = }')
        
        dashboard_button = ttk.Button(result_frame, text="Dashboard", \
                                command=lambda protocol=proc['protocol'], port=proc['port'], prefix=proc["url_prefix"], \
                                    pw_file=proc["pw_file"], cwd=proc["cwd"]: \
                                run_dashboard(protocol, port, prefix, pw_file, cwd))
        if proc['stopped']:
            dashboard_button.config(state=tk.DISABLED)
        dashboard_button.grid(row=i, column=8, padx=5, pady=2, sticky='nsew')

        home_button = ttk.Button(result_frame, text="Homepage", \
                                command=lambda protocol=proc['protocol'], port=proc['port'], prefix=proc["url_prefix"]: \
                                run_home(protocol, port, prefix))
        if proc['stopped']:
            home_button.config(state=tk.DISABLED)
        home_button.grid(row=i, column=9, padx=5, pady=2, sticky='nsew')

        if not proc['stopped']:
            setting_button = ttk.Button(result_frame, image = photo_lens, command = lambda proc=proc: setting_process(proc))
            setting_button.image = photo_lens,  # Keep a reference to the image
            setting_button.grid(row=i, column=10, padx=5, pady=2, sticky='nsew')
        

    for col in range(6):
        result_frame.grid_columnconfigure(col, weight=1)




def setting_process(proc):
    """
    Get info and logs for a given process
    """

    global root

    port = int(proc['port'])
    pid = int(proc['pid'])
    log_file_path = proc["errorlog"]
    cmdline=" ".join(proc['cmdline'])
    cwd=proc['cwd']
    protocol = proc['protocol']
    port = proc['port']
    url_prefix = proc["url_prefix"]
    homepage = f"{protocol}://localhost:{port}{url_prefix}"
    loglevel = str(proc["loglevel"])
    pw_file = str(proc["pw_file"])
    if os.path.isfile(pw_file):
        pw_file_existence = " (present)"
    else:        
        pw_file_existence = " (missing)"
    host = proc["host"]
    server = proc["server"]
    workers = proc["workers"]
    dash_mode = proc["dash_mode"]
    watch = proc["watch"] 
    debug = proc["debug"]
    if debug:
        debug = "Yes"
    else:
        debug = "No"
    app_names = proc["app_names"] 
    ssl_cert = proc["ssl_cert"]
    ssl_key = proc["ssl_key"]

    def resize(event):
        text_area.config(width=event.width, height=event.height)

    top = tk.Toplevel(root)
    top.title("Py4web process details")
    top.grab_set()  # Make the parent window inactive

    tk.Label(top, text=f"  PID: {pid}  -   Port: {port}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Command: {cmdline}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Path: {cwd}  -  Password file: {pw_file} {pw_file_existence}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Homepage: {homepage}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Host IP: {host}  -  Dashboard mode: {dash_mode}  -  Web Server: {server}  -  Workers: {workers}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  SSL certificate: {ssl_cert}  -  SSL key: {ssl_key}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Watch changes: {watch}  -  App names: {app_names}", anchor="w").pack(fill='both')
    
    separator = ttk.Separator(top, orient='horizontal')
    separator.pack(fill='x')

    tk.Label(top, text=f"  Logfile: {log_file_path}    -  Loglevel = {loglevel}  -  Debug = {debug}", anchor="w").pack(fill='both')

    text_area = scrolledtext.ScrolledText(top, wrap=tk.WORD)
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    if not log_file_path:
        text_msg='\n< logfile not specified >'
        text_area.insert(tk.END, text_msg)
    else:    
        if os.path.isfile(log_file_path):
            update_log(text_area, log_file_path)
        else:
            text_msg='\n< logfile not present >'
            text_area.insert(tk.END, text_msg)

    top.geometry("700x600")

    # FOCUS STUFF
    def on_close():
        top.destroy()
        root.grab_release()  # Re-enable the parent window
    top.protocol("WM_DELETE_WINDOW", on_close)
    top.transient(root)  # Set confirm window as transient for the root window
    top.focus_force()
    def focus_top(event=None):
        if top and top.winfo_exists():  # Check if child window exists
            top.deiconify()  # Ensure the window is not minimized
            top.lift()  # Bring to front
            top.focus_force()
    # Redirect focus to the confirm window when the root window is clicked
    root.bind("<FocusIn>", focus_top)

    top.bind('<Configure>', resize)

def update_log(text_area, log_file_path):
    with open(log_file_path, 'r') as file:
        content = file.read()
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, content)
        text_area.see(tk.END)  # Scroll to the end
    text_area.after(1000, update_log, text_area, log_file_path)  # Refresh every 1 second


def is_port_in_use(port):
    port = int(port)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0



def start_process(proc):
    global root
    global result_frame

    confirm_window = tk.Toplevel(root)
    confirm_window.title("Run confirmation")

    confirm_message = tk.Label(confirm_window, text=f"   Run the py4web instance {proc['instance_name']}?   ")
    confirm_message.pack(pady=10)

    open_new_box_var = tk.BooleanVar(value=True)
    open_new_box_check = tk.Checkbutton(confirm_window, text="Show py4web output on console", variable=open_new_box_var)
    if platform.system() == "Darwin" and getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'): #running in a PyInstaller MacOs bundle
            #open_new_box_check.config(state=tk.DISABLED)
            create_tooltip(open_new_box_check, f"On MacOS apps run with Finder you don't have a console")
    
    open_new_box_check.pack(pady=5)

    command = (proc['cmdline'])
    def on_yes():
        if open_new_box_var.get():
            confirm_window.destroy()
            subprocess.Popen(command)
            time.sleep(3)
            search_processes()
        else:
            confirm_window.destroy()
            subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            time.sleep(3)
            search_processes()

    def on_cancel():
        confirm_window.destroy()

    yes_button = tk.Button(confirm_window, text="Yes", command=on_yes)
    yes_button.pack(side=tk.LEFT, padx=20, pady=20)

    cancel_button = tk.Button(confirm_window, text="Cancel", command=on_cancel)
    cancel_button.pack(side=tk.RIGHT, padx=20, pady=20)

    # FOCUS STUFF
    def on_close():
        confirm_window.destroy()
        root.grab_release()  # Re-enable the parent window
    confirm_window.protocol("WM_DELETE_WINDOW", on_close)
    confirm_window.transient(root)  # Set confirm window as transient for the root window
    confirm_window.focus_force()
    def focus_confirm_window(event=None):
        if confirm_window and confirm_window.winfo_exists():  # Check if child window exists
            confirm_window.deiconify()  # Ensure the window is not minimized
            confirm_window.lift()  # Bring to front
            confirm_window.focus_force()
    # Redirect focus to the confirm window when the root window is clicked
    root.bind("<FocusIn>", focus_confirm_window)

    return

def stop_process(pid):
# Function to show the stop process confirmation dialog

    global root

    answer = messagebox.askquestion("Delete process stop", "Are you sure you want to stop this py4web instance with PID = " + str(pid) + " ?", icon='warning')
    if not answer == 'yes':
        messagebox.showinfo("Result", "Operation cancelled")
        return

    # FOCUS STUFF
    def focus_confirm_window(event=None):
        if root.focus_get() is None:  # Check if no widget in the root window has focus
            root.focus_force()  # Force focus back to the root window
    root.bind("<FocusIn>", focus_confirm_window)


    try:
        process = psutil.Process(pid)
        process.terminate()  # or process.kill()
        process.wait(timeout=3)
        messagebox.showinfo("Process Terminated", f"Successfully terminated process {pid}.")
    except psutil.NoSuchProcess:
        messagebox.showerror("Error", f"No such process: {pid}.")
    except psutil.AccessDenied:
        messagebox.showerror("Error", f"Access denied to terminate process: {pid}.")
    except psutil.TimeoutExpired:
        messagebox.showerror("Error", f"Failed to terminate process {pid} within timeout.")
    finally:
        search_processes()


def open_password_window(password_file):
    password_window = tk.Toplevel(root)
    password_window.title("Password Confirmation")
    password_window.grab_set()  # Make the parent window inactive

    tk.Label(password_window, text=f"\n    Password file: {password_file}     \n").pack(pady=10)
    tk.Label(password_window, text="Enter Password:").pack(pady=5)
    password_entry = tk.Entry(password_window, show='*')
    password_entry.pack(pady=5)

    tk.Label(password_window, text="Confirm Password:").pack(pady=5)
    confirm_password_entry = tk.Entry(password_window, show='*')
    confirm_password_entry.pack(pady=5)

    def confirm_password(password_file):

        # FOCUS STUFF
        def focus_confirm_window(event=None):
            if root.focus_get() is None:  # Check if no widget in the root window has focus
                root.focus_force()  # Force focus back to the root window
        root.bind("<FocusIn>", focus_confirm_window)

        password = password_entry.get()
        confirm_password = confirm_password_entry.get()
        if password == confirm_password:
            subprocess.Popen(Py4web_cmd.split() + [ "set_password", "--password", password, "-p", password_file])
            messagebox.showinfo("Success", f"Passwords saved on {password_file}")
            password_window.destroy()
        else:
            messagebox.showerror("Error", "Passwords do not match!")
            return False
    def cancel():
        password_window.destroy()
        return False
    
    button_frame = tk.Frame(password_window)
    button_frame.pack(pady=20)
    tk.Button(button_frame, text="Confirm", command=lambda password_file=password_file: confirm_password(password_file)).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Cancel", command=cancel).pack(side=tk.LEFT, padx=5)

    # FOCUS STUFF
    def on_close():
        password_window.destroy()
        root.grab_release()  # Re-enable the parent window
    password_window.protocol("WM_DELETE_WINDOW", on_close)
    password_window.transient(root)  # Set confirm window as transient for the root window
    password_window.focus_force()
    def focus_password_window(event=None):
        if password_window and password_window.winfo_exists():  # Check if child window exists
            password_window.deiconify()  # Ensure the window is not minimized
            password_window.lift()  # Bring to front
            password_window.focus_force()
    # Redirect focus to the confirm window when the root window is clicked
    root.bind("<FocusIn>", focus_password_window)

    root.mainloop()

def run_dashboard(protocol='http', port='8000', url_prefix=None, pw_file=False, cwd=False):

    print(f'{pw_file = }')
    print(f'{cwd = }')

    if pw_file and cwd:
        pw_file_full = os.path.join(cwd, pw_file)
        if not os.path.isfile(pw_file_full):
            answer = messagebox.askquestion("Password file missing", "The Dashboard cannot run because the password file:\n" \
                                            + str(pw_file_full) + "\n is missing.\n\n" + \
                                            "Do you wanna create it now?", icon='warning')
            if not answer == 'yes':
                messagebox.showinfo("Result", "Operation cancelled")
                return
            else:
                open_password_window(pw_file_full)
            time.sleep(3)
            search_processes()
    else:
        messagebox.showerror("Error", f"Failed to identify password file")
        return

    try:
        url = f"{protocol}://localhost:{port}{url_prefix}/_dashboard"
        webbrowser.open(url, new=0, autoraise=True)
    except Exception as e:
        messagebox.showerror("Error", f"Failed to open browser: {e}")

def run_home(protocol='http', port='8000', url_prefix=None):
    try:
        url = f"{protocol}://localhost:{port}{url_prefix}"
        webbrowser.open(url, new=0, autoraise=True)

    except Exception as e:
        messagebox.showerror("Error", f"Failed to open browser: {e}")


def show_about():
    messagebox.showinfo("About", f"Py4web-GUI\n\nVersion {PY4WEBGUI_VERSION}\nDeveloped by nicozanf@gmail.com")


def initialize_toml():

    global toml_file

    toml_file = pathlib.Path(Py4web_cwd).joinpath(TOML_FILENAME)

    if not toml_file.exists():
        try:
            toml_file.touch()
        except:
            print(f"ERROR: cannot create {str(toml_file)}")

        # py4web_gui_toml = tomlkit.loads(open(toml_file).read())

        content = tomlkit.document()
        content.add(tomlkit.comment("Py4web-gui content configuration with toml."))
        content.add(tomlkit.nl())
        content.add('title', 'py4web-gui')
        content.add('version', 1)
        content.add(tomlkit.nl())
        with open(toml_file, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(content, fp)

    with open(toml_file, mode="rt", encoding="utf-8") as fp:
        toml = tomlkit.load(fp)
    if not 'MINIMAL' in toml:
        instance = tomlkit.table()
        instance.add("name", "MINIMAL")
        instance.add("command", "apps")
        toml.add("MINIMAL", instance)
        with open(toml_file, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(toml, fp)

    if not 'STANDARD' in toml:
        instance = tomlkit.table()
        instance.add("name", "STANDARD")
        instance.add("command", "apps -L 20")
        toml.add("STANDARD", instance)
        with open(toml_file, mode="wt", encoding="utf-8") as fp:
            tomlkit.dump(toml, fp)

    return            

def main():
    # Main program

    global root
    global result_frame

    set_py4web_path()
    check_Py4web_cmd()
    initialize_toml()

    # Setup Tkinter window

    root = tk.Tk()
    root.title("Py4web GUI")


    # Load the image

    try:
        image = PhotoImage(file='./docs/images/logo_with_py4web.png')
    except:
        print("Cannot find logo_with_py4web.png")
        exit(1)

    # Create a Label widget to display the image
    image_label = ttk.Label(root, image=image)
    image_label.grid(row=0, column=0, padx=5, pady=5, sticky='nw')


    try:
        from py4web import __version__ 
    except:
        __version__ = "N/A"
    py4web_version = __version__
    python_version = sys.version.split()[0] + " "

    info_label = ttk.Label(root, text=f"  Py4web-gui {PY4WEBGUI_VERSION} with Py4web {py4web_version} on Python {python_version}", \
                        foreground="blue", background="#93c9d9", relief=tk.SOLID, borderwidth=1, font=("tahoma", "14", "bold"))
    info_label.grid(row=0, column=0, padx=5, pady=5, sticky='se')

    # Create a menu bar
    menu_bar = tk.Menu(root)
    root.config(menu=menu_bar)

    # Add "Help" menu with "About" option
    help_menu = tk.Menu(menu_bar, tearoff=0)
    menu_bar.add_cascade(label="Help", menu=help_menu)
    help_menu.add_command(label="About", command=show_about)

    mainframe = ttk.Frame(root, padding="10 10 120 100")
    mainframe.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    root.columnconfigure(0, weight=1)
    root.rowconfigure(1, weight=1)


    style = ttk.Style()
    style.configure('W.TButton', font =
                ('calibri', 10, 'bold', 'underline'),
                    foreground = 'green')

    search_button = ttk.Button(mainframe, text="REFRESH", style='W.TButton',  command=search_processes)
    search_button.grid(row=3, column=0, ipady=30, ipadx=30, padx=5, pady=10, sticky='e')


    result_frame = ttk.Frame(mainframe)
    result_frame.grid(row=1, column=0, padx=5, pady=5, sticky='nsew')
    mainframe.rowconfigure(1, weight=1)
    mainframe.columnconfigure(0, weight=1)
    search_processes()

    # Start the Tkinter event loop
    root.mainloop()


if __name__ == "__main__":
    main()

