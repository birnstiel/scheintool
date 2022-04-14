from datetime import datetime
import tkinter as tk
from tkinter import filedialog as fd
import csv
from tkinter import IntVar

currentDay = datetime.now().day
currentMonth = datetime.now().month
currentYear = datetime.now().year

# import orga_helper as oh

fields = [
    ['semester', 'Semester', 'SS' if currentMonth < 10 else 'WS'],
    ['year', 'Year', str(currentYear)],
    ['title_en', 'Title (ENG)', ''],
    ['title_de', 'Title (DEU)', ''],
    ['lecturer', 'Lecturer', ''],
    ['ECTS', 'ECTS', '6'],
    ['SWS', 'SWS', '4'],
    ['date', 'Date of certificate', f'{currentDay}.{currentMonth}.{currentYear}'],
]


def run(event):
    print('running')
    print(entries['title_en']['entry'].get())


def save(event):
    try:
        with fd.asksaveasfile(mode='w', title="Save the file", defaultextension=".txt", initialfile='config.txt') as fh:
            writer = csv.writer(fh)
            for field in fields:
                entry = entries[field[0]]['entry']
                writer.writerow([field[0], entry.get()])
            writer.writerow(['type', lecture_type.get()])
    except AttributeError:
        print('saving aborted')


def load(event):
    filename = fd.askopenfilename()
    if filename is not None:
        with open(filename, 'r') as fh:
            reader = csv.reader(fh)
            for row in reader:
                name = row[0]
                if name in entries:
                    entry = entries[name]['entry']
                    entry.delete(0, tk.END)
                    entry.insert(0, row[1])
                elif name == 'type':
                    lecture_type.set(int(row[1]))
                else:
                    raise ValueError(f'unknown entry: {row[0]}')
    else:
        print('saving aborted')


def add_entry(name, text1, text2='', row=0):

    label = tk.Label(text=text1)
    label.grid(row=row, column=0)

    entry = tk.Entry()
    entry.insert(0, text2)
    entry.grid(row=row, column=1)

    return label, entry


window = tk.Tk(className='Schein Tool')
window.rowconfigure(list(range(len(fields) + 2)), minsize=50, weight=1)
window.columnconfigure([0, 1], minsize=50, weight=1)


greeting = tk.Label(
    text="Schein-Tool by T. Birnstiel",
)
greeting.grid(column=0, row=0, columnspan=1)


row = 1
entries = {}
for name, title, default in fields:
    label, entry = add_entry(name, title, text2=default, row=row)

    entries[name] = {
        'title': title,
        'label': label,
        'entry': entry}
    row += 1


# add type of lecture
radio_frame = tk.Frame()
lecture_type = IntVar(value=1)
type1 = tk.Radiobutton(radio_frame, anchor='w', text='Vorlesung mit Übungen', variable=lecture_type, value='1')
type2 = tk.Radiobutton(radio_frame, anchor='w', text='Vorlesung', variable=lecture_type, value='2')
type3 = tk.Radiobutton(radio_frame, anchor='w', text='Seminar', variable=lecture_type, value='3')
type4 = tk.Radiobutton(radio_frame, anchor='w', text='Praktikum', variable=lecture_type, value='4')

type1.pack(fill='both')
type2.pack(fill='both')
type3.pack(fill='both')
type4.pack(fill='both')
radio_frame.grid(row=row, column=1)
row += 1

btn_frame = tk.Frame()
btn_save = tk.Button(master=btn_frame, text="Save config")
btn_load = tk.Button(master=btn_frame, text="Load config")
btn_run = tk.Button(master=btn_frame, text="Generate!")

btn_save.pack(side='left')
btn_load.pack(side='left')
btn_run.pack(side='left')

btn_frame.grid(column=1, row=row, sticky='se')

btn_save.bind("<Button-1>", save)
btn_load.bind("<Button-1>", load)
btn_run.bind("<Button-1>", run)


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
# type: 1: "Vorlesung mit Übung"
# 2: "Vorlesung"
# 3: "Seminar"
# 4: "Praktikum"
# date: date of the certificate, if set to None, uses today


window.mainloop()
