import tkinter as tk
from tkinter.filedialog import asksaveasfilename, askopenfilename
from tkinter import messagebox
import subprocess

class TextLineNumbers(tk.Canvas):
    def __init__(self, *args, **kwargs):
        tk.Canvas.__init__(self, *args, **kwargs)
        self.textwidget = None

    def attach(self, text_widget):
        self.textwidget = text_widget
        
    def redraw(self, *args):
        '''redraw line numbers'''
        self.delete("all")

        i = self.textwidget.index("@0,0")
        while True :
            dline= self.textwidget.dlineinfo(i)
            if dline is None: break
            y = dline[1]
            linenum = str(i).split(".")[0]
            self.create_text(2,y,anchor="nw", text=linenum)
            i = self.textwidget.index("%s+1line" % i)


class CustomText(tk.Text):
    def __init__(self, *args, **kwargs):
        tk.Text.__init__(self, *args, **kwargs)

        # create a proxy for the underlying widget
        self._orig = self._w + "_orig"
        self.tk.call("rename", self._w, self._orig)
        self.tk.createcommand(self._w, self._proxy)

    def _proxy(self, *args):
        # let the actual widget perform the requested action
        cmd = (self._orig,) + args
        result = self.tk.call(cmd)

        # generate an event if something was added or deleted,
        # or the cursor position changed
        if (args[0] in ("insert", "replace", "delete") or 
            args[0:3] == ("mark", "set", "insert") or
            args[0:2] == ("xview", "moveto") or
            args[0:2] == ("xview", "scroll") or
            args[0:2] == ("yview", "moveto") or
            args[0:2] == ("yview", "scroll")
        ):
            self.event_generate("<<Change>>", when="tail")

        # return what the actual widget returned
        return result
    
class Editor(tk.Frame):
    def __init__(self, *args, **kwargs):
        tk.Frame.__init__(self, *args, **kwargs)
        self.text = CustomText(self)
        self.vsb = tk.Scrollbar(self, orient="vertical", command=self.text.yview)
        self.text.configure(yscrollcommand=self.vsb.set)
        self.text.tag_configure("bigfont", font=("Helvetica", "24", "bold"))
        self.linenumbers = TextLineNumbers(self, width=30)
        self.linenumbers.attach(self.text)
        
        self.vsb.pack(side="right", fill="y")
        self.linenumbers.pack(side="left", fill="y")
        self.text.pack(side="right", fill="both", expand=True)
        
        self.text.bind("<<Change>>", self._on_change)
        self.text.bind("<Configure>", self._on_change)
        
    
    def _on_change(self, event):
        self.linenumbers.redraw()
    
file_path = ''
saved = True


def set_saved_false(key=None):
    if key.keysym == "F5":
        return
    global saved
    saved = False
    if file_path != '':
        compiler.title("●" + file_path.split("/")[-1].split("\\")[-1] + ' - YaIDE')

def set_saved_true():
    global saved
    saved = True
    if file_path != '':
        compiler.title(file_path.split("/")[-1].split("\\")[-1] + ' - YaIDE')


def set_file_path(path):
    global file_path
    file_path = path
    compiler.title(file_path.split("/")[-1].split("\\")[-1] + ' - YaIDE')


def open_file(_=None):
    global saved
    path = askopenfilename(filetypes=[('Yapl Files', '*.yapl')])
    with open(path, 'r') as file:
        code = file.read()
        editor.text.delete('1.0', tk.END)
        editor.text.insert('1.0', code)
        set_file_path(path)
    set_saved_true()


def save(_=None):
    global saved
    if file_path == '':
        path = asksaveasfilename(filetypes=[('Yapl Files', '*.yapl')])
    else:
        path = file_path
    with open(path, 'w') as file:
        code = editor.text.get('1.0', tk.END)
        file.write(code)
        set_file_path(path)
    set_saved_true()


def save_as():
    global saved
    path = asksaveasfilename(filetypes=[('Yapl Files', '*.yapl')])
    with open(path, 'w') as file:
        code = editor.text.get('1.0', tk.END)
        file.write(code)
        set_file_path(path)
    set_saved_true()


def compile(_=None):
    if file_path == '' or not saved:
        save_prompt = tk.Toplevel()
        text = tk.Label(save_prompt, text='Please save your code')
        text.pack()
        return
    command = f'python3 driver.py {file_path}'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    code_output.delete('1.0', "end")
    code_output.insert('1.0', output.decode('UTF-8'))
    code_output.insert('1.0', error.decode('UTF-8'))

def run(_=None):
    command = f'echo "Execution not implemented yet..."'
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    code_output.delete("start", "end")
    code_output.insert('1.0', output.decode('UTF-8'))
    code_output.insert('1.0', error.decode('UTF-8'))
    
def on_closing():
    if saved or messagebox.askokcancel("Quit", "Are you sure you want to quit? There are unsaved changes."):
        compiler.destroy()




if __name__ == "__main__":
    compiler = tk.Tk()
    compiler.title('YaIDE')
    
    menu_bar = tk.Menu(compiler)

    file_menu = tk.Menu(menu_bar, tearoff=0)
    file_menu.add_command(label='Open', command=open_file)
    file_menu.add_command(label='Save', command=save)
    file_menu.add_command(label='Save As', command=save_as)
    file_menu.add_command(label='Exit', command=exit)
    menu_bar.add_cascade(label='File', menu=file_menu)

    run_bar = tk.Menu(menu_bar, tearoff=0)
    run_bar.add_command(label='Compile', command=compile)
    run_bar.add_command(label='Run', command=run)
    menu_bar.add_cascade(label='Run', menu=run_bar)
    
    compiler.config(menu=menu_bar)
    
    editor = Editor(compiler)
    editor.text.bind("<Key>", set_saved_false)
    editor.pack(side="top", fill="both", expand=True)
    
    code_output = tk.Text(height=10)
    code_output.bind("<Key>", lambda e: "break")
    code_output.pack(side="bottom", fill="x", expand=False)
    
    compiler.bind("<Control-o>", open_file)
    compiler.bind("<Control-s>", save)
    compiler.bind("<F5>", compile)
    
    compiler.protocol("WM_DELETE_WINDOW", on_closing)
    compiler.mainloop()