import platform as ptf
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from pathlib import Path
import sys
import os
import re
import yaml
import io
import warnings
import subprocess

import xlsxwriter
import pandas as pd
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm

import PyPDF2

from babel.dates import format_date

# determine the system we are on

platform = ptf.platform().lower().split('-')[0]
if platform not in ['windows', 'macos', 'linux']:
    raise ValueError(f'unknown platform {platform}')

# define current date

currentDay = datetime.now().day
currentMonth = datetime.now().month
currentYear = datetime.now().year

# define the fields that need to be set in the UI

fields = [
    ['year', 'Year', str(currentYear)],
    ['title_en', 'Title (ENG)', ''],
    ['title_de', 'Title (DEU)', ''],
    ['lecturer', 'Lecturer', ''],
    ['ECTS', 'ECTS', '6'],
    ['SWS', 'SWS', '4'],
    ['date', 'Date of certificate', f'{currentDay}.{currentMonth}.{currentYear}'],
    ['examdate', 'Date of exam', f'{currentDay}.{currentMonth}.{currentYear}'],
]

# define helper functions


def read_config(config_file):
    with open(config_file) as fh:
        config = yaml.safe_load(fh)
    return config


def write_config(config):
    "for windows systems, we avoid the newline at the end"
    with open(config_file, 'w') as f:
        dump = yaml.dump(config)
        if dump.endswith('\n'):
            dump = dump[:-1]
        f.write(dump)


def guess_path(platform):
    # we need to make a guess
    if platform == 'linux':
        try:
            guess = Path(subprocess.check_output('which soffice', shell=True).decode().strip())
        except subprocess.CalledProcessError:
            guess = Path('')
    elif platform == 'macos':
        guess = Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')
    elif platform == 'windows':
        guess = Path(r'C:\Program Files\LibreOffice\program\soffice.exe')

    if not guess.is_file():
        guess = None

    return guess


def ask_for_path():
    window = tk.Tk(className='Schein Tool')
    label = tk.Label(text="enter executable of libreoffice (soffice.bin, soffice.exe, ...)")
    entry = tk.Entry()
    label.pack()
    entry.pack()
    exec = ''

    def callback(event):
        nonlocal exec
        exec = entry.get()
        window.quit()

    button = tk.Button(text="Save path")
    button.bind("<Button-1>", callback)
    button.pack()
    window.mainloop()
    return exec


def read_grades(filename):
    """Read grades from csv or xlsx file.

    Parameters
    ----------
    filename : string | path
        Try to read "matrikelnumer" or MNR and "grade"|"grades"|"note" from file


    """
    filename = Path(filename)
    if filename.suffix.lower() == '.csv':
        grades = pd.read_csv(filename)
    elif filename.suffix.lower() == '.xlsx':
        grades = pd.read_excel(filename)
    else:
        messagebox.showerror(title="Unknown file type", message="File type needs to be 'csv' or 'xlsx'.")

    # now normalize column names

    for col in grades.columns:
        col = str(col)
        if col.lower() in ['note', 'noten', 'grade', 'grades'] and 'grade' not in grades.columns:
            grades.rename(columns={col.lower(): 'grade'}, inplace=True)
        elif col.lower() in ['mnr', 'matrikelnummer', 'matrikelnumber']:
            grades.rename(columns={col.lower(): 'MNR'}, inplace=True)

    return grades


def read_LSF(filename):
    """Read grades from csv or xlsx file.

    Parameters
    ----------
    filename : string | path
        data file to read from


    """
    filename = Path(filename)
    if filename.suffix.lower() == '.csv':
        LSF = pd.read_csv(filename)
    elif filename.suffix.lower() == '.xlsx':
        LSF = pd.read_excel(filename, skiprows=[0, 1])  # , usecols=range(8), dtype=str)
    elif filename.suffix.lower() == '.xls':
        LSF = read_LSF(convert_xls_xsls(filename, libreoffice_executable=libreoffice_exec))
        return LSF
    else:
        messagebox.showerror(title="Unknown file type", message="File type needs to be 'csv' or 'xlsx'.")

    # now normalize column names

    renaming = {
        'Mtknr': 'MNR',
        'Nachname': 'lastname',
        'Vorname': 'firstname',
        'Geschlecht': 'gender',
        'Anschrift': 'address',
        'Geburtstag/-ort': 'dob',
        'E-Mail': 'email',
        'Studiengänge': 'major'}

    LSF.rename(columns=renaming, inplace=True)

    # reformat the major (get rid of stuff behind the brackets), split dob in place and date

    LSF['major'] = LSF.apply(lambda row: row['major'].split('(')[0], axis=1)
    LSF['pob'] = LSF.apply(lambda row: re.split(r'\sin\s', row.dob)[1], axis=1)
    LSF['dob'] = LSF.apply(lambda row: re.split(r'\sin\s', row.dob)[0], axis=1)

    return LSF


def convert_xls_xsls(filename, libreoffice_executable=None, encoding='latin-1'):
    """Converts a LSF-generated XLS table to a modern XLSX format.

    Conversion uses `soffice` by libreoffice, by default located in the `LibreOffice.app` on mac.
    Specify the executable as keyword otherwise.

    Parameters
    ----------
    filename : str
        path to the XLS file to be converted
    libreoffice_executable : str, optional
        path to the libreoffice executable used for the conversion, by default None

    Returns
    -------
    str
        The filename of the converted file. Returns `None` if there was an error.
    """
    if not Path(filename).is_file():
        raise FileNotFoundError('input file does not exist')
    if libreoffice_executable is None:
        libreoffice_executable = '/Applications/LibreOffice.app/Contents/MacOS/soffice'

    outdir = str(Path(filename).expanduser().parent)

    # non-breaking spaces can cause issues: remove them
    tempfile = Path(filename)
    tempfile = tempfile.with_name(tempfile.stem + '_' + tempfile.suffix)
    res = None
    try:
        with open(filename, 'r', encoding=encoding) as fh:
            content = fh.read()
            content = re.sub(r'\s', ' ', content)
        with open(tempfile, mode='w', encoding=encoding) as fh:
            fh.write(content)

        result = subprocess.run([libreoffice_executable, '--convert-to', 'xlsx', '--headless', filename, '--outdir', outdir], capture_output=True)

        if result.returncode == 0:
            # return the output filename:
            # some libreoffice instances return text, others don't
            if result.stdout:
                res = result.stdout.split(b">")[1].split(b"using filter")[0].strip()
                if isinstance(res, bytes):
                    res = res.decode()
            else:
                # if there is no output, we construct the result name
                res = Path(outdir) / filename
                res = str(res.with_suffix('.xlsx').absolute())
        else:
            warnings.warn('XLS->XLSX conversion failed. Message is : ' + result.stderr)
    finally:
        if tempfile.is_file():
            tempfile.unlink()
        return res


def fill_certificate(data, filename, degree='master'):
    """Fills out an LMU master or bachelor certificate.

    For every row in the table `data`, a certificate is created and this is
    stored in file `filename`.

    data : DataFrame
        needs the following columns:
        - major: the subject in which the student is enrolled
        - firstname: first name
        - lastname: last name
        - place: current city
        - MNR: matrikel number
        - DOB: date of birth
        - POB: place of birth
        - semester: WS or SS
        - year
        - title_en : english name of lecture
        - title_de : german name of lecture
        - lecturer : lecturers name
        - ECTS: number of ECTS
        - SWS: number of semester hours
        - grade: the grade
        - examdate: date of the exam
        - type: 1: "Vorlesung mit Übung"
                2: "Vorlesung"
                3: "Seminar"
                4: "Praktikum"
        - date: date of the certificate, if set to None, uses today

    filename : str | PosixPath
        into with file to write the certificates

    degree : str
        'master', or 'bachelor'

    """
    # define sizes: we use a fixed font size and an x and y offset in cm. Then
    # we scale all lengths with the factor `scale` such that we can rescale
    # things easily.

    today = format_date(datetime.today(), format="long", locale='de_DE')

    fontsize = 12
    x_off = 2.54 * cm      # left margin
    y_off = 0.761 * A4[1]  # distance from bottom to first line
    xscale = cm             # scale for the horizontal direction
    yscale = 0.98 * cm      # scale for the vertical direction

    if degree not in ['bachelor', 'master']:
        raise ValueError('degree must be bachelor or master')

    def print(x, y, text):
        can.drawString(x * xscale, - y * yscale, str(text))

    # get the schein

    cert = str(docs_dir / f'schein_{degree}.pdf')

    # create the output PDF file

    output = PyPDF2.PdfFileWriter()

    # we loop over each dictionary

    for i, row in data.iterrows():

        packet = io.BytesIO()

        # create a new PDF with Reportlab

        can = canvas.Canvas(packet, pagesize=A4)
        can.setFont("Helvetica", fontsize)

        can.translate(x_off, y_off)

        print(6.75, 0, row.major)  # noqa
        print(2,    1, row.firstname + ' ' + row.lastname)  # noqa
        print(1,    2, row.place)  # noqa
        print(11.3, 2, row.MNR)  # noqa
        print(2.5,  3, row.dob)  # noqa
        print(7.0,  3, row.pob)  # noqa

        if row.semester == 'SS':
            print(1.425, 4.2, 'x')
        elif row.semester == 'WS':
            print(3.75, 4.2, 'x')
        else:
            raise ValueError('semester needs to be SS or WS')

        print(7.5, 4.2, row.year)

        print(3, 6.75, row.title_de)
        print(3, 8.75, row.title_en)

        print(1.5, 10.75, row.lecturer)

        print(10, 11.75, row.SWS)
        print(14, 11.75, row.ECTS)
        print(8, 12.75, row.grade)

        print(5, 13.75, row.examdate)

        print(5.05, 14.16 + row.type * 0.82, 'x')

        print(2.5, 19, row.date or today)

        can.save()

        # move to the beginning of the StringIO buffer
        packet.seek(0)
        new_pdf = PyPDF2.PdfFileReader(packet)

        # add the "watermark" (which is the new pdf) on the existing page
        # we need to re-open the schein otherwise, we will overwrite all data
        # on all the pdfs
        schein = PyPDF2.PdfFileReader(open(cert, 'rb'))
        page = schein.getPage(0)
        page.mergePage(new_pdf.getPage(0))
        output.addPage(page)

    # finally, write "output" to a real file
    outputStream = open(filename, "wb")
    output.write(outputStream)
    outputStream.close()


def write_grade_table(fname, data, course_info):
    """Writes the grades to Excel file following the LMU physics template.

    fname : str
        file name to write to

    data : DataFrame
        needs to contain:
        - MNR
        - lastname
        - firstname
        - major
        - grade
        - examdate

        if it does not contain `beisitzer` or `examdate`, those are
        taken from `course_info`

    course_info : dict-like
        needs to contain:
        - title_de: course title in German
        - semester: SS or WS
        - year: e.g. 19/20 or 2020 or 20
        - examdate: date of the examination
        - lecturer: lecturer
        - beisitzer: beisitzer

    """

    # Create a workbook and add a worksheet.

    with xlsxwriter.Workbook(fname) as workbook:
        worksheet = workbook.add_worksheet()

        # Add a bold format to use to highlight cells.

        greyboldborder = workbook.add_format({'bold': True, 'border': 1, 'bg_color': '#BFBFBF', 'border_color': '#000000'})
        greyboldnoborder = workbook.add_format({'bold': True, 'bg_color': '#BFBFBF', 'border': 0})
        wrap = workbook.add_format({'text_wrap': True})

        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 30)
        worksheet.set_column(2, 3, 20)
        worksheet.set_column(4, 5, 10)
        worksheet.set_column(6, 6, 20)

        worksheet.merge_range('C1:G5', '', greyboldnoborder)

        # write course info

        worksheet.write(0, 0, 'Name der Veranstaltung:', greyboldborder)
        worksheet.write(1, 0, 'Semester:', greyboldborder)
        worksheet.write(2, 0, 'Datum der Prüfung:', greyboldborder)
        worksheet.write(3, 0, '1. Prüfer:', greyboldborder)
        worksheet.write(4, 0, '2.Prüfer:', greyboldborder)

        worksheet.write(0, 1, course_info['title_de'], greyboldnoborder)
        worksheet.write(1, 1, course_info['semester'] + course_info['year'], greyboldnoborder)
        if 'examdate' in course_info:
            worksheet.write(2, 1, course_info['examdate'], greyboldnoborder)
        else:
            worksheet.write(2, 1, 's.u.', greyboldnoborder)
        worksheet.write(3, 1, course_info['lecturer'], greyboldnoborder)

        if 'beisitzer' in course_info:
            worksheet.write(4, 1, course_info['beisitzer'], greyboldnoborder)
        else:
            worksheet.write(4, 1, 's.u.', greyboldnoborder)

        # Write headers

        worksheet.write(11, 0, 'Matrikelnumber', greyboldborder)
        worksheet.write(11, 1, 'Nachname', greyboldborder)
        worksheet.write(11, 2, 'Vorname', greyboldborder)
        worksheet.write(11, 3, 'Studiengang', greyboldborder)
        worksheet.write(11, 4, 'Note', greyboldborder)
        worksheet.write(11, 5, 'BE/NB', greyboldborder)
        if 'examdate' not in course_info:
            worksheet.write(11, 6, 'Datum der Prüfung', greyboldborder)
        if 'beisitzer' not in course_info:
            worksheet.write(11, 7, 'Beisitzer', greyboldborder)

        # mimic template

        worksheet.write('A7', 'Bitte schicken Sie die Liste via Email an')
        worksheet.write('B8', 'notenlisten@physik.uni-muenchen.de')
        worksheet.write('A9', 'und eine unterschrieben Liste an')
        worksheet.write('B10', 'Fakultät für Physik\nPrüfungsamt\nSchellingstr. 4\nD-80799 München', wrap)

        # Start from the first cell. Rows and columns are zero indexed.
        row = 12
        col = 0

        # Iterate over the data and write it out row by row.
        for i, pdrow in data.iterrows():
            BENB = float(pdrow.grade) <= 4.0
            BENB = int(BENB) * 'BE' + int(not BENB) * 'NB'

            worksheet.write(row, col, pdrow.MNR)
            worksheet.write(row, col + 1, pdrow.lastname)
            worksheet.write(row, col + 2, pdrow.firstname)
            worksheet.write(row, col + 3, pdrow.major)
            worksheet.write(row, col + 4, pdrow.grade)
            worksheet.write(row, col + 5, BENB)
            if 'examdate' not in course_info:
                worksheet.write(row, col + 6, pdrow.examdate)
            if 'beisitzer' not in course_info:
                worksheet.write(row, col + 7, pdrow.beisitzer)
            row += 1


# continue configuration

# set config file name and create if it doesn't exist


if platform in ['macos', 'linux']:
    config_file = Path('~').expanduser() / '.config' / 'scheintool.yaml'
    encoding = 'utf8'
elif platform == 'windows':
    encoding = 'latin-1'
    config_file = Path(os.environ['APPDATA']) / 'scheintool' / 'scheintool.yaml'
    if not config_file.parent.is_dir():
        config_file.parent.mkdir()
else:
    raise ValueError('unknown architecture')

if not config_file.is_file():
    config_file.touch()

config = read_config(config_file)

if config is None or 'libreoffice_exec' not in config or 'encoding' not in config:
    guess = guess_path(platform)
    if guess is None:
        guess = ask_for_path()
    write_config({
        'libreoffice_exec': str(guess),
        'encoding': encoding
    })

config = read_config(config_file)
libreoffice_exec = config['libreoffice_exec']
encoding = config['encoding']

# data files


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


docs_dir = Path(resource_path('pdfs'))
