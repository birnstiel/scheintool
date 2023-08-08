import csv
import traceback
from pathlib import Path

import tkinter as tk
from tkinter import filedialog as fd
from tkinter import IntVar
from tkinter import StringVar
from tkinter import messagebox

from scheintool import settings


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
            try:
                with open(filename, 'r', encoding=settings.encoding) as fh:
                    reader = csv.reader(fh)
                    for row in reader:
                        name = row[0]
                        if name in self.entries:
                            entry = self.entries[name]['entry']
                            entry.delete(0, tk.END)
                            entry.insert(0, row[1])
                        elif name == 'type':
                            self.lecture_type.set(int(row[1]))
                        elif name == 'mb':
                            self.mb.set(row[1])
                        elif name == 'semester':
                            self.semester.set(row[1])
                        else:
                            raise ValueError(f'unknown entry: {row[0]}')
            except Exception as err:
                messagebox.showinfo(title='Error', message='Could not load configuration:\n' + str(err))
        else:
            print('loading aborted')

    def save(self, event):
        "stores the entries into a CSV file"
        try:
            with fd.asksaveasfile(mode='w', title="Save the file", defaultextension=".txt", initialfile='config.txt') as fh:
                writer = csv.writer(fh)
                for field in self.fields:
                    entry = self.entries[field[0]]['entry']
                    writer.writerow([field[0], entry.get()])
                writer.writerow(['type', self.lecture_type.get()])
                writer.writerow(['mb', self.mb.get()])
                writer.writerow(['semester', self.semester.get()])
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

        # start with radio button for summer/winter term
        radio_frame_semester = tk.Frame()
        self.semester = StringVar(value='SS' if settings.currentMonth < 10 else 'WS')
        tk.Radiobutton(radio_frame_semester, anchor='w', text='SS', variable=self.semester, value='SS').pack(fill='both', side='left')
        tk.Radiobutton(radio_frame_semester, anchor='w', text='WS', variable=self.semester, value='WS').pack(fill='both', side='left')
        radio_frame_semester.grid(row=1, column=1)
        row += 1

        # add all fields
        self.entries = {}
        for name, title, default in self.fields:
            label, entry = add_entry(title, content=default, row=row)

            self.entries[name] = {
                'title': title,
                'label': label,
                'entry': entry}
            row += 1

        # add type of lecture as Radio Button
        radio_frame_lecturetype = tk.Frame()
        self.lecture_type = IntVar(value=1)
        type1 = tk.Radiobutton(radio_frame_lecturetype, anchor='w', text='Vorlesung mit Übungen', variable=self.lecture_type, value='1')
        type2 = tk.Radiobutton(radio_frame_lecturetype, anchor='w', text='Vorlesung', variable=self.lecture_type, value='2')
        type3 = tk.Radiobutton(radio_frame_lecturetype, anchor='w', text='Seminar', variable=self.lecture_type, value='3')
        type4 = tk.Radiobutton(radio_frame_lecturetype, anchor='w', text='Praktikum', variable=self.lecture_type, value='4')

        type1.pack(fill='both')
        type2.pack(fill='both')
        type3.pack(fill='both')
        type4.pack(fill='both')
        radio_frame_lecturetype.grid(row=row, column=0)

        # add type of schein as Radio Button
        radio_frame_mb = tk.Frame()
        self.mb = StringVar(value='master')
        tk.Radiobutton(radio_frame_mb, anchor='w', text='Master', variable=self.mb, value='master').pack(fill='both')
        tk.Radiobutton(radio_frame_mb, anchor='w', text='Bachelor', variable=self.mb, value='bachelor').pack(fill='both')
        radio_frame_mb.grid(row=row, column=1)
        row += 1

        # add the buttons on the bottom

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

        self.window.mainloop()

    def set_lsf_file(self, event):
        """open dialogue to set lsf data"""
        filename = fd.askopenfilename()
        if filename != '' and Path(filename).is_file():
            self.lsf_file = filename
            self.btn_lsf.configure(fg="black")
            if hasattr(self, 'grade_file'):
                self.btn_run.configure(fg='green')
        elif filename == '' and not Path(filename).is_file():
            tk.messagebox.showinfo(title='Error', message='invalid file')

    def set_grade_file(self, event):
        """open dialogue to set grades data"""
        filename = fd.askopenfilename()
        if filename != '' and Path(filename).is_file():
            self.grade_file = filename
            self.btn_grades.configure(fg="black")
            if hasattr(self, 'lsf_file'):
                self.btn_run.configure(fg='green')
        elif filename == '' and not Path(filename).is_file():
            tk.messagebox.showinfo(title='Error', message='invalid file')

    def run(self, event):
        """Final Step: read the files, merge the information and create the scheins"""
        if not hasattr(self, 'lsf_file') and hasattr(self, 'grade_file'):
            tk.messagebox.showinfo(title='Error', message='Set LSF & Grade file first')
            return

        lsf = settings.read_LSF(self.lsf_file)
        grades = settings.read_grades(self.grade_file)

        data = lsf.merge(grades[['MNR', 'grade']], on='MNR')
        course_info = {'beisitzer': ''}

        for name, entry in self.entries.items():
            content = entry['entry'].get()

            course_info[name] = content

            if name in data:
                mask = (data[name] == "") | data[name].isna()
                data[name][mask] = content
            else:
                data[name] = content

        data['place'] = 'München'
        data['type'] = self.lecture_type.get()
        data['semester'] = self.semester.get()
        course_info['semester'] = self.semester.get()

        filename = fd.asksaveasfilename(defaultextension=".pdf", initialfile="scheine.pdf")
        if filename == '':
            return

        try:
            settings.fill_certificate(data, filename, degree=self.mb.get())
            schein_error = False
        except Exception as err:
            schein_error = True
            messagebox.showinfo(title='Error', message='Could not generate Schein:\n' + str(err))

        try:
            settings.write_grade_table(Path(filename).with_suffix('.xlsx'), data, course_info)
            table_error = False
        except Exception as err:
            table_error = True
            messagebox.showinfo(title='Error', message=f'Could not generate grade spread sheet:\n{err}\n{traceback.format_exc()}')

        messagebox.showinfo(
            title='Completed',
            message=f'Schein was {"not " * schein_error}created successfully!\n' +
            f'Grade table was {"not " * table_error}created successfully!'
        )


def start():
    m = main()
    m.start()


if __name__ == '__main__':
    start()
