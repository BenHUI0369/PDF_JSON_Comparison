# setup environment (MAC OS / LINUX)

```bash
$ python3 -m venv venv
. venv/bin/activate
```

## install pip

```bash
pip install -r requirements_linux.txt
```

# setup environment (WINDOWS)

```bash
python -m venv venv
venv\Scripts\activate
```

## install pip

```bash
pip install -r requirements_windows.txt
```

# setup (COMMON)

<!-- .env.example -->

copy .env.example then rename to .env, use default or edit what you want

```bash
HOST=0.0.0.0
PORT=8099
URL_SCHEME=https
```

## start development

```bash
python app.py
```

## start server

```bash
python wsgi.py
```

## general Requirements txt file if any NEW library/package updated or used

```bash
# if MAC / LINUX
pip freeze > requirements_linux.txt
# if WINDOWS
pip freeze > requirements_windows.txt
```

# Build .exe

# make sure put all built .exe in same directory

```bash
pip install pyinstaller
pyinstaller --onefile main_all.py
pyinstaller --name name_your_want wsgi.py
```

# program flow

1. upload your JSON and PDF file, there are 10 pairs
2. click "Upload" button, program will upload the files pair by pair
3. click "Click to compare" button, program will start comparing, pair by pair
4. after all comparisons are completed, a message will be showed
5. click "Download result" button, program will zip all result and start downloading
6. after your work is completed, better to click "Clear History" button to clear all historical files

# file description

- wsgi.py // env config
- app.py // development env
- main_all.py // provide comparing function
- templates/index.html // html view
- uploads // storing all upload files
- results // storing all results from comparing
- temp // storing .zip file for download
- requirements_linux.txt // MAC or LINUX use, storing library and version
- requirements_windows.txt // WINDOWS use, storing library and version
- action.log // logging the action from user

# Log format

```bash
logging.debug('This is a debug message')
logging.info('This is an info message')
logging.warning('This is a warning message')
logging.error('This is an error message')
logging.critical('This is a critical message')
```
