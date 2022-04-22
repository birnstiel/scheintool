# LMU Scheintool

Tool to generate certificates based on LSF data and a CSV/Excel file of Matrikelnumbers and grades.

## Building

To save size of the final file, create an environment with

    conda env create -f environment.yml

then activate it with

    conda activate scheintoo-env

then call `make`. On Windows, execute the command in the make file, but replace the `:` with `;`. The resulting apps should be build in the `dist/` folder.