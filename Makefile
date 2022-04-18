all: scheintool.py settings.py Makefile
	# use ; on windows instead of : 
	pyinstaller -y --onefile --windowed --add-data docs/:docs/ --icon icon.ico scheintool.py

logo:
	convert Logo_LMU.svg -resize 256x256 icon.ico

clean:
	-rm -r build dist scheintool.spec 