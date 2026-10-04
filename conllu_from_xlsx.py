# Script for preparing CoNLL-U files for automated annotation (training_file.conllu) from exported Google Sheets.
# This script processes Excel files (.xlsx), removing sentences marked with 'TODO' or 'skipped'.
# It generates individual CoNLL-U files for each Excel Sheet and combines them into a single training file.
# Input files must be located in the specified "input" directory.
# The language identifier (e.g., KKG, Suansu) can be provided as a command-line argument or entered manually.


import os
import re
import sys
from os.path import join, isdir
import openpyxl

INPUT = "input" 
CONLLU = "conllu_files" 
TEMP = "temp" 

def get_language():
    """
    Prompts the user or reads a command-line argument to determine the language identifier.
    Returns:
        str: The language identifier (e.g., 'Chintang', 'Ruuli', 'KKG', 'Suansu').
    """
    if len(sys.argv) > 1:
        return sys.argv[1]
    available_languages = ['Chintang', 'Ruuli', 'KKG', 'Suansu']
    lang = input(f'What is the language ({', '.join(available_languages)}): ')
    while lang not in available_languages:
        lang = input(f'The langue {lang} is not available. Please choose from {', '.join(available_languages)}: ')
    return lang

def initialize_language(lang):
    """
    Initializes the language identifier by appending an underscore.
    Args:
        lang (str): The language identifier.
    Returns:
        str: The initialized language identifier with an underscore appended (e.g., 'KKG_' for 'KKG').
    """
    return lang + '_'

def read_xlsx_file(file_path):
    """
    Reads an Excel (.xlsx) file and extracts the content of each sheet into a dictionary.
    Args:
        file_path (str): The path to the Excel file.
    Returns:
        dict: A dictionary where keys are sheet names and values are lists of rows (each row is a list of cell values).
    """
    wb = openpyxl.load_workbook(file_path, data_only=True)
    sheets = wb.sheetnames
    # Exclude sheets with only uppercase names (VOCAB, TEMPLATE, etc.) and starting qwith # (#Khomai_orig)
    sheets = [sheet for sheet in sheets if not re.search(r'^(#|[A-Z]+$)', sheet)] 
    texts = dict()
    for sheet in sheets:
        ws = wb[sheet]
        last_id = 0
        output = []
        for idx, row in enumerate(ws.iter_rows(values_only=True)):
            if idx == 0:
                continue  # Skip the header row
            output_row = ['' if cell is None else str(cell) for cell in row[:11]]
            output_row += [''] * (11 - len(output_row))  # Ensure there are 11 columns
            # output_row = [re.sub(r'^(\d+)\.0$', r'\1', cell) for cell in output_row]
            if any(re.search(r'[a-z]', cell) for cell in output_row):
                last_id = idx
            if last_id + 1 < idx:
                # i.e. at leat two empty rows
                break
            output.append(output_row)
        texts[sheet] = output
    return texts

def process_sentence(csv, conllu, file_name) -> tuple:
    """
    Processes a sentence's lines from the CSV data, updates the CoNLL-U content, and tracks errors.
    Args:
        csv (list): List of rows representing the sentence in CSV format.
        conllu (list): The list of strings representing the CoNLL-U content.
        file_name (str): The name of the file being processed.
    Returns:
        tuple: A tuple containing the updated CoNLL-U content and the exit status indicating if any errors were encountered during processing.
    """
    sentence_empty = {
        'take?': True, 'lines': '', 
        'textorig' : '', 'textsplit' : '', 'multiwordstart' : 0, 'multiwordend' : 0,
        '0s': 0, 'roots': 0,
        'maxid': 0, 'depmaxid': 0, 'lastid': 0, 'idsubq': True,
        'nodep': '', 'fullid': '', 'multiword' : ''
    }
    sentence = sentence_empty.copy()
    exit_status_sent = 0
    for line in csv:
        if line[0] == '' and sentence['lines'] != '':
            exit_status_temp = finalize_sentence(sentence, conllu, file_name)
            exit_status_sent = max(exit_status_temp, exit_status_sent)
            sentence = sentence_empty.copy()
        elif '# orig_sent_id' not in line[0]:
            sentence = process_line(line, sentence)

    if sentence['take?']:
        conllu.append(sentence['lines'] + '\n')
    
    if conllu[-1] == '\n':
        conllu = conllu[:-1]
    return conllu, exit_status_sent

def process_line(line, sentence):
    """
    Updates the current sentence's state based on the content of a single line.
    Args:
        line (list): The current line being processed.
        sentence (dict): The current sentence's state.
    Returns:
        dict: The updated sentence state.
    """
    if sentence['take?']:
        sentence['take?'] = not re.search(r'^TODO|^skipped', line[-1])
        enhanced_line = line.copy()
        if line[6] not in ['', '_'] and line[8] == '_':
            enhanced_line = line[:8] + [f'{line[6]}:{line[7]}'] + line[9:]
        if '|' in enhanced_line[5]:
            enhanced_line[5] = '|'.join(sorted(line[5].split('|')))
        if '|' in enhanced_line[8] :
            deps = enhanced_line[8].split('|')
            deps = sorted(deps, key=lambda x: int(x.split(':')[0]))
            enhanced_line[8] = '|'.join(deps)
        if '|' in enhanced_line[9] :
            enhanced_line[9] = '|'.join(sorted(enhanced_line[9].split('|')))
        sentence['lines'] += '\t'.join([col for col in enhanced_line[:-1] if col != '']) + '\n'
        if line[1] != '':
            sentence = update_sentence_stats(line, sentence)
        if line[0].startswith('# text = '):
            sentence['textorig'] = line[0].split(' = ')[1]   
    return sentence

def update_text(line, sentence):
    """
    Updates the text content of the sentence, including multiword tokens and whitespace.
    Args:
        line (list): The current line being processed.
        sentence (dict): The current sentence's state.
    Returns:
        dict: The updated sentence state.
    """
    def add_token(line):
        """
        Adds a token to the sentence text, including a space if needed."""
        text = line[1]
        if not re.search(r'(^|\|)SpaceAfter=No', line[9]):
            text += ' '
        return text
    
    if re.search(r'^\d+-\d+$', line[0]):
        sentence['multiwordstart'] = int(line[0].split('-')[0])
        sentence['multiwordend'] = int(line[0].split('-')[1])
        sentence['textsplit'] += add_token(line)
    elif re.search(r'^\d+$', line[0]):
        if int(line[0]) < sentence['multiwordstart'] or int(line[0]) > sentence['multiwordend']:
            sentence['textsplit'] += add_token(line)
    return sentence

def update_sentence_stats(line, sentence):
    """
    Updates sentence statistics, including IDs, dependencies, and structure validation.
    Args:
        line (list): The current line being processed.
        sentence (dict): The current sentence's state.
    Returns:
        dict: The updated sentence state.
    """
    sentence = update_text(line, sentence)

    id_split = line[0].split('-')
    if int(id_split[0]) > sentence['maxid']:
        sentence['maxid'] = int(id_split[0])

    if '-' in line[0] and any([item != '_' for item in line[2:9]]):
        sentence['multiword'] = sentence['multiword'] + line[0] + ' '

    if sentence['idsubq'] and int(id_split[0]) != sentence['lastid'] + 1:
        sentence['idsubq'] = False
    elif '-' not in line[0] and sentence['idsubq']:
        sentence['lastid'] = int(line[0])

    if line[6] == '0':
        sentence['0s'] += 1
    elif re.search(r'^\d+$', line[6]):
        sentence['depmaxid'] = max(sentence['depmaxid'], int(line[6]))

    if line[7] == 'root':
        sentence['roots'] += 1

    if '-' not in line[0] and not (re.search(r'\d', line[6]) and re.search(r'\w', line[7])):
        sentence['nodep'] += line[0] + ' '

    if any(line[i] == '' for i in range(10)):
        sentence['fullid'] += line[0]

    return sentence

def finalize_sentence(sentence, conllu, file_name):
    """
    Finalizes a sentence's processing, adds it to CoNLL-U content if valid, and logs errors if found.
    Includes the file name and the first line of the sentence in the logs.
    Args:
        sentence (dict): The current sentence's state.
        conllu (list): The list of strings representing the CoNLL-U content.
        file_name (str): The name of the file being processed.
    Returns:
        int: The exit status indicating if any errors were encountered during processing.
    """
    exit_status_temp = 0
    if sentence['take?']:
        conllu.append(sentence['lines'] + '\n')
        sent_id = sentence['lines'].split('\n')[0].split(' = ')[-1]
        if sentence['textorig'] != sentence['textsplit'][:-1]:
            print(f"\n{file_name} : {sent_id}\nText doesn't match\norig:  {sentence['textorig']}\nsplit: {sentence['textsplit']}\n")
        if sentence['0s'] != 1 or sentence['roots'] != 1:
            print(f"\n{file_name} : {sent_id}\nWrong number of roots\n0s: {sentence['0s']}\troots: {sentence['roots']}\n")
            exit_status_temp = 1
        if sentence['depmaxid'] > sentence['maxid']:
            print(f"\n{file_name} : {sent_id}\nDependency id is higher than the maximum id\n"
                  f"depmaxid: {sentence['depmaxid']}\tmaxid: {sentence['maxid']}\n")
            exit_status_temp = 1
        if not sentence['idsubq']:
            print(f"\n{file_name} : {sent_id}\nNot subsequent ids\nlastid: {sentence['lastid']}\n")
            exit_status_temp = 1
        if sentence['nodep']:
            print(f"\n{file_name} : {sent_id}\nNo dependency\nnodep: {sentence['nodep']}\n")
            exit_status_temp = 1
        if sentence['fullid']:
            print(f"\n{file_name} : {sent_id}\nDoesn't contain 10 columns\nfullid: {sentence['fullid']}\n")
            exit_status_temp = 1
        if sentence['multiword'] != '':
            print(f"\n{file_name} : {sent_id}\nHas non-empty multiword token\nmultiword: {sentence['multiword']}\n")
            exit_status_temp = 1
    return exit_status_temp
 
def write_conllu_file(output_path, conllu):
    """
    Writes the CoNLL-U formatted content to the specified output file.
    Args:
        output_path (str): The path to the output CoNLL-U file.
        conllu (list): The list of strings representing the CoNLL-U content.
    """
    with open(output_path, 'w') as file:
        file.writelines(conllu)

def process_files(lang):
    """
    Processes all input TSV files for the given language, converting them to CoNLL-U format.
    Args:
        lang (str): The language identifier used to filter input files.
    Returns:
        list: A list of dictionaries containing file names, sentence counts, and word counts.
        int: The exit status indicating if any errors were encountered during processing.
    """
    files = []
    exit_status = 0

    for file_name in os.listdir(INPUT):
        if not (file_name.startswith(lang) and file_name.endswith('.xlsx')):
            continue
        file_type = re.search(r'\w+_(\w+)\.xlsx$', file_name).group(1)
        xlsx_content = read_xlsx_file(join(INPUT, file_name))
        for text_name, text_data in xlsx_content.items():
            conllu = [text_data[0][0] + '\n']
            conllu, exit_status_sent = process_sentence(text_data[1:], conllu, file_name)
            exit_status = max(exit_status, exit_status_sent)
            output_file_name = f"{lang}{file_type}_{text_name}.conllu"
            write_conllu_file(join(CONLLU, output_file_name), conllu)
            files.append({'file_name' : output_file_name,
                        'sent_num' : len(re.findall('sent_id', ''.join(conllu))),
                        'word_num' : len(re.findall(r'\n\d+\t', ''.join(conllu)))})   
    files.sort(key=lambda x: x['file_name'])
    return files, exit_status

def write_training_file_to_conllu(files, lang):
    """
    Combines all individual CoNLL-U files into a single training file for the specified language.
    Args:
        files (list): List of file names to be combined.
        lang (str): The language identifier used in the training file name.
    """
    with open(join(CONLLU, f'{lang}training_file.conllu'), 'w') as outfile:
        for file_name in files:
            with open(join(CONLLU, file_name), 'r') as infile:
                outfile.write(infile.read())

def copy_training_file_to_temp(lang):
    """
    Copies the training file to the temporary directory if it exists.
    Args:
        lang (str): The language identifier used in the training file name.
    """
    if isdir(TEMP):
        with open(join(TEMP, f'{lang}training_file.conllu'), 'w') as outfile:
            with open(join(CONLLU, f'{lang}training_file.conllu'), 'r') as infile:
                outfile.write(infile.read())

def main(lang: str):
    if not os.path.exists(CONLLU):
        os.makedirs(CONLLU)
    if not os.path.exists(TEMP):
        os.makedirs(TEMP)

    files, exit_status = process_files(lang)

    if exit_status != 0:
        sys.exit(1)

    write_training_file_to_conllu([file['file_name'] for file in files], lang)
    copy_training_file_to_temp(lang)
    
    print()
    for file in sorted(files, key=lambda x: x['file_name']):
        print(f"{file['file_name']}\t| {file['sent_num']} sentences\t| {file['word_num']} words")
    print(f"\nTotal\t\t\t| {sum([file['sent_num'] for file in files])} sentences\t| {sum([file['word_num'] for file in files])} words\n")


if __name__ == "__main__":
    lang = initialize_language(get_language())
    main(lang)
    