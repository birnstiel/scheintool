all: scheintool.py settings.py Makefile
	# use ; on windows instead of : 
	pyinstaller -y --onefile --windowed --add-data pdfs/:pdfs/ --icon icon.ico --hiddenimport=babel.numbers --hiddenimport=yaml Scheintool.py

requirements.txt : environment.yml Makefile
	cat environment.yml | grep "^[ ]*-[ ]*" | sed -e "s/^  - //g" > environment.txt

logo:
	convert Logo_LMU.svg -resize 256x256 icon.ico

clean:
	-rm -r build dist Scheintool.spec 