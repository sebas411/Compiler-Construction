from tkinter import *
from tkinter.filedialog import asksaveasfilename, askopenfilename
import subprocess

compiler = Tk()
compiler.title('YaIDE')
file_path = ''
saved = False


def set_saved_false(key=None):
    if key.keysym == "F5":
        return
    global saved
    saved = False
    if file_path != '':
        compiler.title("●" + file_path.split("/")[-1].split("\\")[-1] + '- YaIDE')

def set_saved_true():
    global saved
    saved = True
    if file_path != '':
        compiler.title(file_path.split("/")[-1].split("\\")[-1] + '- YaIDE')


def set_file_path(path):
    global file_path
    file_path = path
    compiler.title(file_path.split("/")[-1].split("\\")[-1] + '- YaIDE')


def open_file(_=None):
    global saved
    path = askopenfilename(filetypes=[('Yapl Files', '*.yapl')])
    with open(path, 'r') as file:
        code = file.read()
        editor.delete('1.0', END)
        editor.insert('1.0', code)
        set_file_path(path)
    set_saved_true()


def save(_=None):
    global saved
    if file_path == '':
        path = asksaveasfilename(filetypes=[('Yapl Files', '*.yapl')])
    else:
        path = file_path
    with open(path, 'w') as file:
        code = editor.get('1.0', END)
        file.write(code)
        set_file_path(path)
    set_saved_true()


def save_as():
    global saved
    path = asksaveasfilename(filetypes=[('Yapl Files', '*.yapl')])
    with open(path, 'w') as file:
        code = editor.get('1.0', END)
        file.write(code)
        set_file_path(path)
    set_saved_true()


def compile(_=None):
    if file_path == '' or not saved:
        save_prompt = Toplevel()
        text = Label(save_prompt, text='Please save your code')
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



menu_bar = Menu(compiler)

file_menu = Menu(menu_bar, tearoff=0)
file_menu.add_command(label='Open', command=open_file)
file_menu.add_command(label='Save', command=save)
file_menu.add_command(label='Save As', command=save_as)
file_menu.add_command(label='Exit', command=exit)
menu_bar.add_cascade(label='File', menu=file_menu)

run_bar = Menu(menu_bar, tearoff=0)
run_bar.add_command(label='Compile', command=compile)
run_bar.add_command(label='Run', command=run)
menu_bar.add_cascade(label='Run', menu=run_bar)

compiler.config(menu=menu_bar)

editor = Text()
editor.bind("<Key>", set_saved_false)
editor.pack()

code_output = Text(height=10)
code_output.bind("<Key>", lambda e: "break")
code_output.pack()

compiler.bind("<Control-o>", open_file)
compiler.bind("<Control-s>", save)
compiler.bind("<F5>", compile)

compiler.mainloop()

