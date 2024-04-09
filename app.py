from flask import Flask, render_template, request, send_file, redirect, url_for, flash, jsonify
import os
import platform
import subprocess
import magic
import json
import uuid
import secrets
import zipfile
import datetime
import logging
import re

# Dynamically get the absolute path to the project's root directory
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

app=Flask(__name__)
app.secret_key = secrets.token_hex(16)

# Create constant variable for file type and path
ALLOWED_EXTENSIONS = {'json', 'pdf'}
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
RESULT_FOLDER = os.path.join(os.getcwd(), 'results')
TEMP_FOLDER = os.path.join(os.getcwd(), 'temp')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['TEMP_FOLDER'] = TEMP_FOLDER

# Create variable to store comparison progress
progress = {'current': 0, 'total': 0}
downloadFileName = 'output.zip'
filePairList = []

class RequestLogFormatter(logging.Formatter):
    def format(self, record):
        # Get IP address and browser information from the request object
        ip_address = request.remote_addr
        browser = request.user_agent

        # Add IP address and browser information to the log record
        record.clientip = ip_address
        record.useragent = browser

        # Format the log record
        formatted_record = super().format(record)
        return formatted_record
    
# Set up logging configuration
log_formatter = RequestLogFormatter('%(asctime)s | %(levelname)s | %(clientip)s | %(useragent)s | %(message)s')
log_handler = logging.FileHandler('action.log')
log_handler.setLevel(logging.DEBUG)
log_handler.setFormatter(log_formatter)

app.logger.addHandler(log_handler)
app.logger.setLevel(logging.DEBUG)

# Create a file pair class for json, pdf and output file
class FilePair:
    def __init__(self, file1, file2, result):
        self.file1 = file1
        self.file2 = file2
        self.result = result

# Check if the file type is json or pdf, ie: abc.json or abc.pdf
def allowed_file(filename):
    return '.'in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Check file type and return bool value
def check_file_type(file, allowed_type):
    # Use the magic module to determine the file's MIME type
    file_type = magic.from_buffer(file.read(1024), mime=True)
    # Rest the file pointer to the begining
    # Make sure the file always start reading from the begining
    file.seek(0)
    return file_type == allowed_type

# Check directory exists or not
def check_path_exist(directory):
    # Create directory if the directory not exist
    if not os.path.isfile(directory):
        os.makedirs(directory, exist_ok=True)

# Remove file in the directory
def remove_files_in_directory(directory):
    # Make sure directory exist
    check_path_exist(directory)

    # Get a list of all files in the directory
    files = os.listdir(directory)

    # Iterate over each file
    for file_name in files:
        file_path = os.path.join(directory, file_name)

        # Delete the item if it is file type
        if os.path.isfile(file_path):
            os.remove(file_path)
            # Update log report: Deleted 1 file
            app.logger.info(f"Removed file: [{file_path}]")
    # Update log report: Deleted all files
    app.logger.info(f"Removed all files under: [{directory}]")

# Check for json type file
def check_if_file_type_json(file):
    # check if the file's MIME type not always correctly identify JSON files
    file_content = file.read()
    try:
        # Try to parse the file_content as JSON
        json.loads(file_content)
        return True
    except ValueError:
        return False
    finally:
        # Rest the file pointer to the begining
        # Make sure the file always start reading from the begining
        file.seek(0)

# Route for root path, which is the home page or index.html
@app.route('/')
def index():
    # Get all message from URL query parameter. ie: abc.com/?message=hello&message=world -> ['hello', 'world']
    messages = request.args.getlist('message')
    return render_template('index.html', messages = messages)

"""
# Create different route for upload, process, download and clear history
# Upload route: POST method, Get all files to filePairList, display uploaded file, and return to root path
@app.route('/upload', methods=['POST'])
def upload():
    # Update log report
    app.logger.info('Upload button clicked.')
    global filePairList
    # Create an empty list to store messages
    messages = []
    # Create temporary directory if not exists
    temp_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(temp_dir, exist_ok=True)

    # Get all uploaded files
    files = request.files

    # Handle each uploaded files
    for filePair in range(1, 11):
        file1 = None
        file2 = None
        file1_check = False
        file2_check = False

        try:
            file1 = files['file1' + str(filePair)]
            file2 = files['file2' + str(filePair)]
        except:
            continue
        finally:
            if (not file1 and not file2):
                continue
        
        # Check file1 and file2 formats, is the format is incorrect, append error message list[] and log report 
        if file1 and allowed_file(file1.filename) and check_if_file_type_json(file1):
            file1_check = True
        else:
            error_messages = f"Pair[{filePair}] | File 1 | Invalid file format, Please upload a JSON file."
            messages.append(error_messages)
            app.logger.info(error_messages)

        if file2 and allowed_file(file2.filename) and check_file_type(file2, 'application/pdf'):
            file2_check = True
        else:
            error_messages = f"Pair[{filePair}] | File 2 | Invalid file format, Please upload a PDF file."
            messages.append(error_messages)
            app.logger.info(error_messages)

        # Rename and save the file to temp_dir if file pair (json + pdf) pass file type checking
        if file1_check and file2_check:
            json_file_name = f"{str(uuid.uuid4())}.{file1.filename.rsplit('.', 1)[1].lower()}"
            pdf_file_name =  f"{str(uuid.uuid4())}.{file2.filename.rsplit('.', 1)[1].lower()}"
            file1_save_path = os.path.join(temp_dir, json_file_name)
            file2_save_path = os.path.join(temp_dir, pdf_file_name)
            file1.save(file1_save_path)
            file2.save(file2_save_path)

        # Update message list and log report
        file1_save_message = f"Pair[{filePair}] | File 1 | Uploaded | File name: [{file1.name}] | Size(KB): [{os.path.getsize(file1_save_path)}]"
        file2_save_message = f"Pair[{filePair}] | File 2 | Uploaded | File name: [{file2.name}] | Size(KB): [{os.path.getsize(file2_save_path)}]"
        messages.append(file1_save_message)
        app.logger.info(file1_save_message)
        messages.append(file2_save_message)
        app.logger.info(file2_save_message)

        # Get current datetime
        current_datetime = datetime.datetime.now()
        # Format current_datetime to string
        datetime_string = current_datetime.strftime("%Y%m%d_%H%M%S")

        ouput_pdf_name = str(f"{file2.filename.rsplit('.', 1)[0]}_Result_{datetime_string}.pdf")
        filePairList.append(FilePair(json_file_name, pdf_file_name, ouput_pdf_name))
    
    if (len(filePairList) == 0):
        no_file_message = "Required files does not exist or error"
        flash(no_file_message, "error")
        app.logger.info(no_file_message)

    # Redirect back to the index page with the hint and messages
    print(filePairList)
    return redirect(url_for('index', messages = messages))
"""

@app.route('/upload', methods=['POST'])
def upload():
    # Update log report
    app.logger.info('Upload button clicked.')
    global filePairList
    # Create an empty list to store messages
    messages = []
    # Create temporary directory if not exists
    temp_dir = app.config['UPLOAD_FOLDER']
    os.makedirs(temp_dir, exist_ok=True)

    json_files = request.files.getlist('jsonFiles')
    pdf_files = request.files.getlist('pdfFiles')

    if len(json_files) != len(pdf_files):
        flash('Number of JSON and PDF should be the same.')
        return redirect(url_for('index'))

    # Handle each uploaded files
    for filePair in range(0, len(json_files)):
        file1 = None
        file2 = None
        file1_check = False
        file2_check = False

        try:
            file1 = json_files[filePair]
            file2 = pdf_files[filePair]
        except:
            continue
        finally:
            if (not file1 and not file2):
                continue

        # Check file1 and file2 formats, is the format is incorrect, append error message list[] and log report 
        if file1 and allowed_file(file1.filename) and check_if_file_type_json(file1):
            file1_check = True
        else:
            error_messages = f"Pair[{filePair + 1}] | File 1 | Invalid file format, Please upload a JSON file."
            messages.append(error_messages)
            app.logger.info(error_messages)

        if file2 and allowed_file(file2.filename) and check_file_type(file2, 'application/pdf'):
            file2_check = True
        else:
            error_messages = f"Pair[{filePair + 1}] | File 2 | Invalid file format, Please upload a PDF file."
            messages.append(error_messages)
            app.logger.info(error_messages)

        # Rename and save the file to temp_dir if file pair (json + pdf) pass file type checking
        if file1_check and file2_check:
            json_file_name = f"{str(uuid.uuid4())}.{file1.filename.rsplit('.', 1)[1].lower()}"
            pdf_file_name =  f"{str(uuid.uuid4())}.{file2.filename.rsplit('.', 1)[1].lower()}"
            file1_save_path = os.path.join(temp_dir, json_file_name)
            file2_save_path = os.path.join(temp_dir, pdf_file_name)
            file1.save(file1_save_path)
            file2.save(file2_save_path)

        # Update message list and log report
        file1_save_message = f"Pair[{filePair + 1}] | File 1 | Uploaded | File name: [{file1.name}] | Size(KB): [{os.path.getsize(file1_save_path)}]"
        file2_save_message = f"Pair[{filePair + 1}] | File 2 | Uploaded | File name: [{file2.name}] | Size(KB): [{os.path.getsize(file2_save_path)}]"
        messages.append(file1_save_message)
        app.logger.info(file1_save_message)
        messages.append(file2_save_message)
        app.logger.info(file2_save_message)

        # Get current datetime
        current_datetime = datetime.datetime.now()
        # Format current_datetime to string
        datetime_string = current_datetime.strftime("%Y%m%d_%H%M%S")

        ouput_pdf_name = str(f"{file2.filename.rsplit('.', 1)[0]}_Result_{datetime_string}.pdf")
        filePairList.append(FilePair(json_file_name, pdf_file_name, ouput_pdf_name))
    
    if (len(filePairList) == 0):
        no_file_message = "Required files does not exist or error"
        flash(no_file_message, "error")
        app.logger.info(no_file_message)

    # Redirect back to the index page with the hint and messages
    print(filePairList)
    return redirect(url_for('index', message = messages))
    

@app.route('/process')
def process():
    # Update log report
    app.logger.info('Compare button clicked.')
    global filePairList

    # Iterate filePairList and call the main.py script using subprocess to start comparison
    for file_pair in filePairList:
        compare_message = f"Comparing: File1 [{file_pair.file1}] with File2[{file_pair.file2}] generating Result: [{file_pair.result}]"
        PY_ENV_PATH_WINDOWS = os.path.join(os.getcwd(),'venv\Scripts\python.exe')
        PY_ENV_PATH_MAC = os.path.join(os.getcwd(),'venv/bin/python.exe')
        # Switch PY_ENV_PATH for Windows and Mac system
        PY_ENV_PATH = PY_ENV_PATH_WINDOWS if platform.system() == 'Windows' else PY_ENV_PATH_MAC
        MAIN_PY = 'main.py'
        MAIN_EXE = 'main.exe'
        try:
            # Update log report of starting the JSON-PDF comparison
            app.logger.info(compare_message)
            subprocess.run([PY_ENV_PATH, MAIN_PY, file_pair.file1, file_pair.file2, file_pair.result])
            # if main.py become exe 
            # subprocess.run([MAIN_EXE, file_pair.file1, file_pair.file2, file_pair.result])
            # Update log report of finishing the comparison
            app.logger.info('Finished JSON-PDF comparison')
        except Exception as e:
             # Update log report of getting error
            app.logger.error(compare_message)
            # Update log report of the detail error message
            app.logger.error(str(e))
            # Keep process the Iterate even the Exception happen
            continue

    # Check the length of filePairList
    if (len(filePairList) > 0):
        flash("Finished JSON-PDF comparison, click download to download all result files.")
    else:
        flash("No file in file pair list")
    return redirect(url_for('index'))

@app.route('/download')
def download():
    # Update log report of downloading all the result files
    app.logger.info(f"Download button clicked")
    global downloadFileName, filePairList

    # Set the path for the temporary directory from the app's configuration and ensure it exists
    temp_dir = app.config['TEMP_FOLDER']
    check_path_exist(temp_dir)

    # Set the path for the directory where result files are stored and ensure it exists
    result_dir = app.config['RESULT_FOLDER']
    check_path_exist(result_dir)
    # Define the path for the output ZIP file within the temporary directory
    output_path = os.path.join(temp_dir, downloadFileName)

    # Get a list of all files within the result directory
    file_list = os.listdir(app.config['RESULT_FOLDER'])
    # Check if the result directory is empty and handle the case by flashing a message and redirecting
    if (len(file_list) == 0):
        no_file_message = f"File not found."
        flash(no_file_message)
        app.logger.error(no_file_message)
        return redirect(url_for('index'))  
    
    # Create a ZIP file and add all result files into it
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Walk through the result directory and its subdirectories
        for root, _, files in os.walk(result_dir):
            for file in files:
                # Construct the full path for each file
                file_path =os.path.join(root, file)
                app.logger.info(f"File found: [{file_path}]")
                # Add the file to the ZIP, using a relative path
                zipf.write(file_path, os.path.relpath(file_path, result_dir))
    app.logger.info(f"File Downloaded from [{output_path}]")
    # Send the prepared ZIP file to the user as a downloadable attachment
    return send_file(output_path, as_attachment=True)

@app.route('/clear')
def clear():
    # Update log report of clearing all files
    app.logger.info(f"Clear button clicked")
    global filePairList
    filePairList.clear()
    
    # Remove all files within the upload, result, and temp directory.
    remove_files_in_directory(app.config['UPLOAD_FOLDER'])
    remove_files_in_directory(app.config['RESULT_FOLDER'])
    remove_files_in_directory(app.config['TEMP_FOLDER'])

    # Show a message to the user indicating that all history has been cleared.
    flash("All history files are cleared.")
    
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(port=8080, debug=True)