import csv

import tkinter as tk
from tkinter import filedialog as fd
from tkinter import IntVar

from settings import fields


def main():

    # start by defining the callback functions

    def run(event):
        "Continues after the entries are set"
        print('running')
        print(entries['title_en']['entry'].get())

    def load(event):
        "loads the entries from a CSV file"
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

    def save(event):
        "stores the entries into a CSV file"
        try:
            with fd.asksaveasfile(mode='w', title="Save the file", defaultextension=".txt", initialfile='config.txt') as fh:
                writer = csv.writer(fh)
                for field in fields:
                    entry = entries[field[0]]['entry']
                    writer.writerow([field[0], entry.get()])
                writer.writerow(['type', lecture_type.get()])
        except AttributeError:
            print('saving aborted')

    def add_entry(label, content='', row=0):
        "adds a text entry with label"
        label = tk.Label(text=label)
        label.grid(row=row, column=0)

        entry = tk.Entry()
        entry.insert(0, content)
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
        label, entry = add_entry(title, content=default, row=row)

        entries[name] = {
            'title': title,
            'label': label,
            'entry': entry}
        row += 1

    # add type of lecture as Radio Button
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
    # 'type': 1: "Vorlesung mit Übung"
    # 2: "Vorlesung"
    # 3: "Seminar"
    # 4: "Praktikum"
    # date: date of the certificate, if set to None, uses today

    window.mainloop()


if __name__ == '__main__':
    main()
