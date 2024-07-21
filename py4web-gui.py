#!/usr/bin/env python3

import psutil, socket, subprocess, time, webbrowser

try:
    import tkinter as tk
except ModuleNotFoundError:
    print('tkinter module not installed or not available')
    exit()

from tkinter import LEFT, ttk, messagebox, scrolledtext
from tkinter import PhotoImage 


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
            if 'PYTHON' in process_name.upper():
                # Check if the command line contains the command_substrings
                if any(command_substring1 in arg for arg in proc.info['cmdline']) and \
                    any(command_substring2 in arg for arg in proc.info['cmdline']):
                    # split cmdline also on '=' if needed
                    cmdline = [word for line in proc.info['cmdline'] for word in line.split('=')]
                    
                    #  -P, --port INTEGER            Port number  [default: 8000]
                    proc.info["port"] = check_cmdline(cmdline, '-P', '--port', '8000')
                    #   --ssl_cert PATH               SSL certificate file for HTTPS
                    if check_cmdline(cmdline, '--ssl_cert', False, False):
                        proc.info["protocol"]="https"
                    else:
                        proc.info["protocol"]="http"

                    # -U, --url_prefix TEXT         Prefix to add to all URLs in and out
                    proc.info["url_prefix"] = check_cmdline(cmdline, '-U', '--url_prefix', False)
                    if not proc.info["url_prefix"]:
                        proc.info["url_prefix"] = ''
                    
                    proc.info["app_name"] = ''
                    proc.info["stopped"] = False 

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

def check_default_process(processes):
    """
    Check if there is a py4web already running with default parameters
    """
    default_app = {
        'pid' : '',
        'name' : 'python3',
        'protocol' : 'http',
        'port':'8000',
        'url_prefix' : '',
        'cmdline': 'python3 ./py4web.py run apps'.split(),
        'cwd': '/home/nico/py4web',
        'app_name' : 'DEFAULT',
        'stopped' : True,
    }
    
    if not processes:
        return add_process(processes, default_app)

    # check if already running
    cmdline2= 'run'
    cmdline1= 'apps'
    for process in processes:
        if (cmdline1 == process['cmdline'][-1] and cmdline2 == process['cmdline'][-2]): # found
            process['app_name'] = 'DEFAULT'
            return processes            
        else:
            pass            
    return add_process(processes, default_app)
    

def add_process(processes, app):
    """
    Add a not-running process in the list, so it can be started
    """
    processes.append(app)
    return processes


def search_processes():
    processes = find_processes_by_name_and_command('py4web', 'run')
    # processes is a list of dictionaries, with cmdline as a list
    
    for widget in result_frame.winfo_children():
        widget.destroy()
    
    photo_start = tk.PhotoImage(file = "./docs/images/icon-start.png") 
    photo_stop = tk.PhotoImage(file = "./docs/images/icon-stop.png")
    photo_settings = tk.PhotoImage(file = "./docs/images/icon-gear.png")
     
    headers = ["                 Working Directory", "                                      Command Line", 
                 "Protocol", "Port", "  URL prefix", "      APP", " PID","    Action", "        ", "      "]
    
    processes = check_default_process(processes)


    for col, header in enumerate(headers):
        ttk.Label(result_frame, text=header, font=('Arial', 10, 'bold')).grid(row=0, column=col, padx=5, pady=5, sticky='nsew')

    for i, proc in enumerate(processes, start=1):


        cwd_text = tk.Text(result_frame, height=1, wrap='none', width=20)
        cwd_text.insert(tk.END, proc['cwd'] if proc['cwd'] else "N/A")
        cwd_text.config(state=tk.DISABLED)
        cwd_text.grid(row=i, column=0, padx=5, pady=2, sticky='nsew')
        create_tooltip(cwd_text, proc['cwd'] if proc['cwd'] else "N/A")

        cmd_text = tk.Text(result_frame, height=1, wrap='none', width=40)
        cmd_text.insert(tk.END, " ".join(proc['cmdline']))
        cmd_text.config(state=tk.DISABLED)
        cmd_text.grid(row=i, column=1, padx=5, pady=2, sticky='nsew')
        create_tooltip(cmd_text, " ".join(proc['cmdline']))
        
        ttk.Label(result_frame, text=proc['protocol']).grid(row=i, column=2, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['port']).grid(row=i, column=3, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['url_prefix']).grid(row=i, column=4, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['app_name']).grid(row=i, column=5, padx=5, pady=2, sticky='w')
        ttk.Label(result_frame, text=proc['pid']).grid(row=i, column=6, padx=5, pady=2, sticky='e')

        if proc['stopped']:
            #action_button = ttk.Button(result_frame, text="START", image = photo_start, command=lambda app_name=proc['app_name']: start_process(app_name))
            action_button = ttk.Button(result_frame, image = photo_start, command=lambda app_name=proc['app_name']: start_process(app_name))
            action_button.image = photo_start,  # Keep a reference to the image
            if is_port_in_use(proc['port']):
                create_tooltip(action_button, "PORT busy")
                action_button.config(state=tk.DISABLED)
            action_button.grid(row=i, column=7, padx=5, pady=2, sticky='nsew')
        else: 
            action_button = ttk.Button(result_frame, image = photo_stop, command=lambda pid=proc['pid']: stop_process(pid))
            action_button.image = photo_stop,  # Keep a reference to the image
            action_button.grid(row=i, column=7, padx=5, pady=2, sticky='nsew')
        
        dashboard_button = ttk.Button(result_frame, text="Dashboard", \
                                command=lambda protocol=proc['protocol'], port=proc['port'], prefix=proc["url_prefix"]: \
                                run_dashboard(protocol, port, prefix))
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
            #setting_button = ttk.Button(result_frame, image = photo_settings, command=lambda app_name=proc['app_name']: start_process(app_name))
            setting_button = ttk.Button(result_frame, image = photo_settings, command = lambda proc=proc: setting_process(proc))
            setting_button.image = photo_settings,  # Keep a reference to the image
            setting_button.grid(row=i, column=10, padx=5, pady=2, sticky='nsew')
        

    for col in range(6):
        result_frame.grid_columnconfigure(col, weight=1)




def update_log(text_area, log_file_path):
    with open(log_file_path, 'r') as file:
        content = file.read()
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, content)
        text_area.see(tk.END)  # Scroll to the end
    text_area.after(1000, update_log, text_area, log_file_path)  # Refresh every 1 second

def setting_process(proc):
    port = int(proc['port'])
    pid = int(proc['pid'])
    log_file_path = './error.log'  # TODO
    cmdline=" ".join(proc['cmdline'])
    cwd=proc['cwd']
    protocol = proc['protocol']
    port = proc['port']
    url_prefix = proc["url_prefix"]
    homepage = f"{protocol}://localhost:{port}{url_prefix}"
    
    def resize(event):
        text_area.config(width=event.width, height=event.height)

    top = tk.Toplevel(root)
    top.title("Py4web process details")

    #tk.Label(top, text=f"PID: {pid}, Port: {port}", anchor="w").pack(pady=10)
    tk.Label(top, text=f"  PID: {pid}  -   Port: {port}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Path: {cwd}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Command: {cmdline}", anchor="w").pack(fill='both')
    tk.Label(top, text=f"  Homepage: {homepage}", anchor="w").pack(fill='both')

    text_area = scrolledtext.ScrolledText(top, wrap=tk.WORD)
    text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    update_log(text_area, log_file_path)

    top.geometry("600x200")
    top.bind('<Configure>', resize)



def is_port_in_use(port):
    port = int(port)
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0


def start_process(app_name):
    if app_name == 'DEFAULT':
        subprocess.Popen(["./py4web.py", 'run', 'apps'])
        time.sleep(3)
        search_processes()
    return

def stop_process(pid):
# Function to show the stop process confirmation dialog

    answer = messagebox.askquestion("Delete process stop", "Are you sure you want to stop this py4web instance with PID = " + str(pid) + " ?", icon='warning')
    if not answer == 'yes':
        messagebox.showinfo("Result", "Operation cancelled")
        return

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

def run_dashboard(protocol='http', port='8000', url_prefix=None):
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
    messagebox.showinfo("About", "Py4web-GUI\n\nVersion 1.0\nDeveloped by nicozanf@gmail.com")


# Setup Tkinter window
root = tk.Tk()
root.title("Py4web GUI")


# Load the image
image = PhotoImage(file='docs/images/logo_with_py4web.png')

# Create a Label widget to display the image
image_label = ttk.Label(root, image=image)
image_label.grid(row=0, column=0, padx=5, pady=5, sticky='nw')


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
