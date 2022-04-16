import platform as ptf
from datetime import datetime
from pathlib import Path
import os
import yaml
import warnings
import subprocess

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
    ['semester', 'Semester', 'SS' if currentMonth < 10 else 'WS'],
    ['year', 'Year', str(currentYear)],
    ['title_en', 'Title (ENG)', ''],
    ['title_de', 'Title (DEU)', ''],
    ['lecturer', 'Lecturer', ''],
    ['ECTS', 'ECTS', '6'],
    ['SWS', 'SWS', '4'],
    ['date', 'Date of certificate', f'{currentDay}.{currentMonth}.{currentYear}'],
]

# handle settings

if platform in ['macos', 'linux']:
    config_file = Path('~').expanduser() / '.config' / 'scheintool.yaml'
elif platform == 'windows':
    config_file = Path(os.environ['APPDATA']) / 'scheintool' / 'scheintool.yaml'
    if not config_file.parent.is_dir():
        config_file.parent.mkdir()
else:
    raise ValueError('unknown architecture')

if not config_file.is_file():
    config_file.touch()

with open(config_file) as fh:
    config = yaml.safe_load(fh)


def convert_xls_xsls(filename, libreoffice_executable=None):
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

    result = subprocess.run([libreoffice_executable, '--convert-to', 'xlsx', '--headless', filename, '--outdir', outdir], capture_output=True)

    if result.returncode == 0:
        # return the output filename
        return result.stdout.split(b">")[1].split(b"using filter")[0].strip()
    else:
        warnings.warn('XLS->XLSX conversion failed. Message is : ' + result.stderr)
        return None
