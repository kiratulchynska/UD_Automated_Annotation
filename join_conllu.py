# the script for creating new conllu + notes file (for google sheets) from 
    # the selection just annotated automaticaly sentences (e.g., marked DR)
    # and sentences (from the same text) that already were in the google sheets
# new sentences will be marked with 'TODO skipped' in the notes collumn
# all sentences will be joined in the ascending order by ref/sent_id 
# the input xhould contain:
    # .tsv or other tab separated export from google sheets with the UD annotation
    # output_file.conllu from Automated_Annotating

import os
import re
import openpyxl
from input_file import get_language, list_files, choose_file

# the following can be changed:
INPUT = 'input'
OUTPUT = 'output' 
OUTPUT_FILE = 'output_file.conllu' # in OUTPUT  

def choose_google_export_file(lang: str) -> tuple:
    """
    Prompts the user to choose a Google Sheets export file from the input directory.
    Args:
        lang (str): The language code to filter the files.
    Returns:
        tuple: A tuple containing the chosen file name and sheet name. If no file is chosen, returns ('', '').
    """
    xlsx_files = list_files(extension=".xlsx", path=INPUT)
    xlsx_files = [file for file in xlsx_files if file.startswith(lang)]
    file = choose_file(xlsx_files, "Choose the Google Sheets export file:")
    if file == '':
        return '', ''
    file_sheet_names = openpyxl.load_workbook(os.path.join(INPUT, file), data_only=True).sheetnames
    file_sheet_names = [sheet for sheet in file_sheet_names if re.search(r'[a-z]', sheet)]
    sheet = choose_file(file_sheet_names, "Choose the sheet with the data:")
    if sheet == '':
        return '', ''
    return file, sheet


def get_old_conllu() -> list:
    """
    Prompts the user to choose a file from the input directory, reads it, and writes the header to the joined file.
    Returns:
        list: A list of lists representing the rows and columns of the chosen file. If no file is chosen, returns a list with a header and an empty row. The header includes the columns
    """
    lang = get_language()
    google_export_file, google_export_sheet = choose_google_export_file(lang)
    if google_export_file != '' and google_export_sheet != '':
        old_conllu = openpyxl.load_workbook(os.path.join(INPUT, google_export_file), data_only=True)[google_export_sheet]
    else:
        print('No file choosen. Just adding notes.')
        wb = openpyxl.Workbook()
        old_conllu = wb.active
        old_conllu.title = "CoNLL-U header"
        old_conllu.append(["ID", "FORM", "LEMMA", "UPOSTAG", "XPOSTAG", "FEATS", "HEAD", "DEPREL", "DEPS", "MISC", "nt"])
        old_conllu.append(["# newdoc id", "", "", "", "", "", "", "", "", "", ""])
    old_conllu = [['' if cell.value is None else str(cell.value) for cell in row[:11]] for row in old_conllu.iter_rows()]

    with open(os.path.join(OUTPUT, 'joined_output_file.conllu'), 'w') as file:
        file.write('\t'.join(old_conllu[0]) + '\n' + '\t'.join(old_conllu[1]) + '\n') 

    return old_conllu

def get_new_conllu() -> list:
    """
    Reads the output file from the output directory and adds 'TODO skipped DR' to the notes column.
    Returns:
        list: A list of lists representing the rows and columns of the new conllu file. The notes column will have 'TODO skipped DR' for sentences that are not annotated.
    """
    with open(os.path.join(OUTPUT, OUTPUT_FILE), 'r') as file:
        new_conllu = file.read()
    new_conllu = new_conllu.split('\n')
    new_conllu = [line.split('\t') for line in new_conllu]

    for i, line in enumerate(new_conllu):
        if line[0] != '' and line[0].startswith('#'):
            new_conllu[i] = [line[0], "", "", "", "", "", "", "", "", "", "TODO skipped DR"]

    return new_conllu

def process_file(file: list, joined_conllu: dict) -> dict:
    """
    Processes the file and joins the sentences by id.
    Args:
        file (list): A list of lists representing the rows and columns of the file to be processed.
        joined_conllu (dict): A dictionary to store the joined sentences. The keys are the sentence ids and the values are the sentences as strings.
    Returns:
        dict: A dictionary with the joined sentences. The keys are the sentence ids and the values are the sentences as strings. 
    """
    id = '0'
    for line in file:
        line = [re.sub(r'^(\'|\")$', r"'\1", element) for element in line]
        if re.search(r'^# sent_id = \D', line[0]):
            line[0] = re.sub(r"_(0+)", "_", line[0])
            id = re.split(r'_|\.', line[0])[-1]
            if re.search(r'^(\w|\d)$', id) and re.search(r'^\d+(\w)?$', re.split(r'_|\.', line[0])[-2]):
                id = re.split(r'_|\.', line[0])[-2]
                if id in joined_conllu.keys():
                    joined_conllu[id] = joined_conllu[id] + '\n'
                else:
                    joined_conllu[id] = ''
                

        if line[0] != '':
            if id not in joined_conllu.keys():
                joined_conllu[id] = ''
            joined_conllu[id] = joined_conllu[id] + '\t'.join(line) + '\n'
    return joined_conllu

def get_joined() -> dict:
    """
    Joins the old and new conllu files.
    Returns:
        dict: A dictionary with the joined sentences. The keys are the sentence ids and the values are the sentences as strings. 
    """    
    joined_conllu = dict()

    old_conllu = get_old_conllu()
    joined_conllu = process_file(old_conllu[2:], joined_conllu)

    new_conllu = get_new_conllu()
    if 'newdoc' in new_conllu[0][0]:
        new_conllu = new_conllu[1:]  # skip the header if it is a newdoc
    joined_conllu = process_file(new_conllu, joined_conllu)

    return joined_conllu

def save_to_file(joined_conllu: dict):
    """
    Saves the joined conllu to a file.
    Args:
        joined_conllu (dict): A dictionary with the joined sentences. The keys are the sentence ids and the values are the sentences as strings.
    """
    if any([re.search(r'\w', idx) for idx in joined_conllu.keys()]):
        id_keys = [re.search(r'(\d+)(\w)?', idx).groups() for idx in joined_conllu.keys()]
        id_keys = [(idx[0], re.sub('None', '', str(idx[1]))) for idx in id_keys]
        max_len = max([len(idx[0]) for idx in id_keys])
        id_keys = sorted([(max_len - len(idx[0]))*'0'+idx[0]+idx[1] for idx in id_keys])
        id_keys = [re.sub(r'^0+', '', idx) for idx in id_keys]
    else:
        id_keys = joined_conllu.keys()
        id_keys = sorted([int(idx) for idx in id_keys])
        id_keys = [str(idx) for idx in id_keys]
    with open(os.path.join(OUTPUT, 'joined_output_file.conllu'), 'a') as file:
        for idx in id_keys:
            if joined_conllu[idx] != '':
                file.write(joined_conllu[str(idx)])
                file.write('\n')    

if __name__ == '__main__':
    joined_conllu = get_joined()
    save_to_file(joined_conllu)
