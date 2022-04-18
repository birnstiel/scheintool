import csv
import os
import shutil
from pathlib import Path

import tkinter as tk
from tkinter import filedialog as fd
from tkinter import IntVar

import settings


def add_entry(label, content='', row=0):
    "adds a text entry with label"
    label = tk.Label(text=label)
    label.grid(row=row, column=0)

    entry = tk.Entry()
    entry.insert(0, content)
    entry.grid(row=row, column=1)

    return label, entry


class main():

    def __init__(self):
        self.entries = {}
        self.fields = settings.fields.copy()

    # start by defining the callback functions

    def load(self, event):
        "loads the entries from a CSV file"
        filename = fd.askopenfilename()
        if filename is not None:
            with open(filename, 'r') as fh:
                reader = csv.reader(fh)
                for row in reader:
                    name = row[0]
                    if name in self.entries:
                        entry = self.entries[name]['entry']
                        entry.delete(0, tk.END)
                        entry.insert(0, row[1])
                    elif name == 'type':
                        self.lecture_type.set(int(row[1]))
                    else:
                        raise ValueError(f'unknown entry: {row[0]}')
        else:
            print('saving aborted')

    def save(self, event):
        "stores the entries into a CSV file"
        try:
            with fd.asksaveasfile(mode='w', title="Save the file", defaultextension=".txt", initialfile='config.txt') as fh:
                writer = csv.writer(fh)
                for field in self.fields:
                    entry = self.entries[field[0]]['entry']
                    writer.writerow([field[0], entry.get()])
                writer.writerow(['type', self.lecture_type.get()])
        except AttributeError:
            print('saving aborted')

    def start(self):
        """This is the first window where the general settings are defined."""
        self.window = tk.Tk(className='Schein Tool')
        self.window.rowconfigure(list(range(len(self.fields) + 2)), minsize=50, weight=1)
        self.window.columnconfigure([0, 1], minsize=50, weight=1)

        greeting = tk.Label(
            text="Schein-Tool by T. Birnstiel",
        )
        greeting.grid(column=0, row=0, columnspan=1)

        row = 1
        self.entries = {}
        for name, title, default in self.fields:
            label, entry = add_entry(title, content=default, row=row)

            self.entries[name] = {
                'title': title,
                'label': label,
                'entry': entry}
            row += 1

        # add type of lecture as Radio Button
        radio_frame = tk.Frame()
        self.lecture_type = IntVar(value=1)
        type1 = tk.Radiobutton(radio_frame, anchor='w', text='Vorlesung mit Übungen', variable=self.lecture_type, value='1')
        type2 = tk.Radiobutton(radio_frame, anchor='w', text='Vorlesung', variable=self.lecture_type, value='2')
        type3 = tk.Radiobutton(radio_frame, anchor='w', text='Seminar', variable=self.lecture_type, value='3')
        type4 = tk.Radiobutton(radio_frame, anchor='w', text='Praktikum', variable=self.lecture_type, value='4')

        type1.pack(fill='both')
        type2.pack(fill='both')
        type3.pack(fill='both')
        type4.pack(fill='both')
        radio_frame.grid(row=row, column=1)
        row += 1

        btn_frame = tk.Frame()
        btn_save = tk.Button(master=btn_frame, text="Save config")
        btn_load = tk.Button(master=btn_frame, text="Load config")
        self.btn_lsf = tk.Button(master=btn_frame, fg='red', text="Set LSF file")
        self.btn_grades = tk.Button(master=btn_frame, fg='red', text="Set Grades file")
        self.btn_run = tk.Button(master=btn_frame, fg='gray', text="Generate!")

        btn_save.pack(side='left')
        btn_load.pack(side='left')
        self.btn_lsf.pack(side='left')
        self.btn_grades.pack(side='left')
        self.btn_run.pack(side='left')

        btn_frame.grid(column=0, columnspan=2, row=row, sticky='se')

        btn_save.bind("<Button-1>", self.save)
        btn_load.bind("<Button-1>", self.load)
        self.btn_lsf.bind("<Button-1>", self.set_lsf_file)
        self.btn_grades.bind("<Button-1>", self.set_grade_file)
        self.btn_run.bind("<Button-1>", self.run)

        # major: the subject in which the student is enrolled
        # firstname: first name
        # lastname: last name
        # place: current city
        # MNR: matrikel number
        # DOB: date of birth
        # POB: place of birth
        # semester: WS or SS
        # year
        # title_en: english name of lecture
        # title_de: german name of lecture
        # lecturer: lecturers name
        # ECTS: number of ECTS
        # SWS: number of semester hours
        # grade: the grade
        # examdate: date of the exam
        # 'type': 1: "Vorlesung mit Übung"
        # 2: "Vorlesung"
        # 3: "Seminar"
        # 4: "Praktikum"
        # date: date of the certificate, if set to None, uses today

        self.window.mainloop()

    def set_lsf_file(self, event):
        """open dialogue to set lsf data"""
        filename = fd.askopenfilename()
        if filename is not None and Path(filename).is_file:
            self.lsf_file = filename
            self.btn_lsf.configure(fg="black")
            if hasattr(self, 'grade_file'):
                self.btn_run.configure(fg='green')
        else:
            tk.messagebox.show(title='Error', message='invalid file')

    def set_grade_file(self, event):
        """open dialogue to set grades data"""
        filename = fd.askopenfilename()
        if filename is not None and Path(filename).is_file:
            self.grade_file = filename
            self.btn_grades.configure(fg="black")
            if hasattr(self, 'lsf_file'):
                self.btn_run.configure(fg='green')
        else:
            tk.messagebox.showinfo(title='Error', message='invalid file')

    def run(self, event):
        if hasattr(self, 'lsf_file') and hasattr(self, 'grade_file'):
            tk.messagebox.showinfo(title='Success', message='running')
            shutil.copy(settings.docs_dir / 'schein_master.pdf', Path(os.curdir) / 'new_schein.pdf')
        else:
            tk.messagebox.showinfo(title='Error', message='Set LSF & Grade file first')


if __name__ == '__main__':
    m = main()
    m.start()
