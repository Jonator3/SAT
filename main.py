
import os.path
import pickle
import socketserver
import csv

import eel
import threading
import subprocess


def get_free_port():
    with socketserver.TCPServer(("localhost", 0), None) as s:
        worker_port = s.server_address[1]
    return worker_port

modes = {
    "csv": {"delimiter": ","},
    "tsv": {"delimiter": "\t"}
}


class AnnotationTask(object):

    def __init__(self, file, shown_data, annotation_types, annotation_target=None, mode="csv", first_line_is_head=True, hotkeys=None, hints=None):
        self.ano_types = annotation_types
        self.ano_target = annotation_target
        self.shown_data = shown_data
        self.hints = hints
        if self.hints is None:
            self.hints = []
        while len(self.hints) < len(self.ano_types):
            self.hints.append("")
        self.hotkeys = hotkeys
        if self.hotkeys is None:
            self.hotkeys = []
        while len(self.hotkeys) < len(self.ano_types):
            self.hotkeys.append("None")
        reader = csv.reader(
            open(file, "r"),
            delimiter=modes.get(mode).get("delimiter")
        )
        self.annotated = []
        if first_line_is_head:
            row = reader.__next__()
            if annotation_target is None:
                row.append("Annotation")
            self.annotated.append(row)
        self.un_annotated = []
        for row in reader:
            self.un_annotated.append(row)

    def auto_repair(self):
        temp = None  # random target to check attribute existenz
        try:
            temp = self.hotkeys
        except AttributeError:
            self.hotkeys = []
            while len(self.hotkeys) < len(self.ano_types):
                self.hotkeys.append("None")
        try:
            temp = self.hints
        except AttributeError:
            self.hints = []
            while len(self.hints) < len(self.ano_types):
                self.hints.append("")

    def write_file(self, file, mode="csv"):
        writer = csv.writer(
            open(file, "w"),
            delimiter=modes.get(mode).get("delimiter")
        )
        writer.writerows(self.annotated)

    def save_state(self, file):
        pickle.dump(self, open(file, "bw+"))

    def annotate(self, ano_index):
        if len(self.un_annotated) <= 0:
            return
        ano = self.un_annotated[0]
        self.un_annotated = self.un_annotated[1:]
        if self.ano_target is not None:
            ano[self.ano_target] = self.ano_types[ano_index]
        else:
            ano.append(self.ano_types[ano_index])
        self.annotated.append(ano)

    def get_next_text(self):
        return self.un_annotated[0][self.shown_data].replace("\n", "<br>").replace("\\n", "<br>")


current_task: AnnotationTask = None


@eel.expose
def create_task(file, shown_data, annotation_types, annotation_target=None, mode="csv", first_line_is_head=True, hotkeys=None, hints=None):
    print("Creating new Task:", file, shown_data, annotation_types, annotation_target, mode, first_line_is_head, hotkeys, hints)
    shown_data = int(shown_data)
    annotation_target = int(annotation_target)
    file = os.path.expanduser(file)
    if annotation_target == -1:
        annotation_target = None
    global current_task
    current_task = AnnotationTask(file, shown_data, annotation_types, annotation_target, mode, first_line_is_head, hotkeys, hints)
    eel.redirect("annotate.html")


@eel.expose
def load_task(file):
    print("Loading Task:", file)
    file = os.path.expanduser(file)
    global current_task
    task = pickle.load(open(file, "rb"))
    if not type(task) == AnnotationTask:
        pass
        # TODO
    else:
        task.auto_repair()
        current_task = task
        eel.redirect("annotate.html")


@eel.expose
def save_task(file):
    print("Save Task:", file)
    file = os.path.expanduser(file)
    global current_task
    current_task.save_state(file)
    eel.redirect("annotate.html")


@eel.expose
def export_task(file, mode="csv"):
    print("Export Task:", file)
    file = os.path.expanduser(file)
    global current_task
    current_task.write_file(file, mode)
    eel.redirect("annotate.html")


@eel.expose
def annotate(ano_index):
    print("Annotate:", ano_index)
    global current_task
    current_task.annotate(ano_index)
    eel.set_text(current_task.get_next_text())


@eel.expose
def request_hkeys():
    global current_task
    eel.set_hkeys(current_task.hotkeys)


@eel.expose
def request_hints():
    global current_task
    eel.set_hints(current_task.hints)


@eel.expose
def request_ano_text():
    global current_task
    eel.set_text(current_task.get_next_text())


@eel.expose
def request_ano_classes():
    global current_task
    eel.set_ano_classes(current_task.ano_types)


@eel.expose
def request_file_info(path):
    path = os.path.expanduser(path)
    if not os.path.exists(path):
        eel.set_fnf("File not Found!")
    elif not os.path.isfile(path):
        eel.set_fnf("Path is not a File?")
    else:
        eel.set_fnf("")


def start_eel():
    eel.start("index.html", mode='custom', host='localhost', port=eel_port, block=True, cmdline_args=['echo', 'hello world'])


if __name__ == "__main__":
    eel.init('web')
    eel_port = get_free_port()

    server_thread = threading.Thread(target=start_eel)
    server_thread.daemon = True
    server_thread.start()

    subprocess.call([os.path.realpath("chromium/chrome"), '--app=http://localhost:'+str(eel_port)+'/index.html', '--no-sandbox'])
