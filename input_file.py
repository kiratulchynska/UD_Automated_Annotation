# the script for creating input_file.txt of Automated_Annotating from elan export
# it gets sentences that have DR in the status and are not already present in the annotated file
# the input shoud contain:
    # .txt file with elan export: refUD/ref, tx, fte, status (without tier labels)
    # .tsv or other tab separated export from google sheets with the UD annotation (optionaly)

import os
import re
import sys
import openpyxl

# Constants
INPUT = 'input'
TEMP = 'temp'
INPUT_FILE = 'input_file.txt'
INCLUDE_LAB = 'DR'

def get_language() -> str:
    """
    Prompts the user or reads a command-line argument to determine the language identifier.
    Returns:
        str: The language identifier.
    """

    def retrieve_language_list() -> list:
        """
        List languages in a directory
        Returns:
            list: List of languages
        """
        languages = [file.split('_')[0] for file in os.listdir(INPUT) if file.endswith('.xlsx')]
        languages = list(set(languages))
        languages.sort()
        return languages

    if len(sys.argv) > 1:
        return sys.argv[1]
    list_languages = retrieve_language_list()
    lang = input(f"What is the language ({", ".join(sorted(list_languages))}): ")
    while lang not in list_languages:
        lang = input(f"Language not found. What is the language ({", ".join(sorted(list_languages))}): ")
    return lang

def list_files(extension: str, path: str ='input') -> list:
    """
    List files in input directory with a specific extension
    Args:
        extension (str): File extension to filter by (e.g., ".txt", ".xlsx").
        path (str): Path to the input directory. Default is 'input'.
    Returns:
        list: Sorted list of file names with the specified extension.
    """
    files = [file for file in os.listdir(path) if file.endswith(extension)]
    files.sort()
    return files

def choose_file(files : list, prompt : str) -> str:
    """
    Choose a file from a list of files
    Args:
        files (list): List of file names to choose from.
        prompt (str): Prompt message to display to the user.
    Returns:
        str: The chosen file name or an empty string if no file is chosen.
    """    
    print('\n', prompt)
    files = sorted(files)
    for i, file in enumerate(files):
        print(f"  {i + 1}. {file}")
    file_idx = input(f"Choose the number of the file (0 if none): ")
    while not re.search(r'^\d+$', file_idx) or int(file_idx) < 0 or int(file_idx) > len(files):
        file_idx = input(f"Invalid input. Choose the number of the file (0 if none): ")
    file_idx = int(file_idx) - 1
    if file_idx != -1:
        return files[file_idx]
    else:
        return ''
    
def choose_input_file(path) -> str:
    """
    Choose an input .txt file from the input directory.
    Args:
        path (str): Path to the input directory.
    Returns:
        str: The chosen file name or an empty string if no file is chosen.
    """
    txt_files = list_files(".txt", path=path)
    input_file_name = choose_file(txt_files, "Glosses files:")
    if input_file_name == '':
        print("No glosses file selected, exiting.")
        exit(1)
    return input_file_name

def choose_text_name(lang: str) -> tuple:
    """
    Choose the name of the text from the Google export files.
        Args:
        lang (str): Language code to filter the files.
    Returns:
        tuple: A tuple containing the chosen text name and all annotated sentence references for that text.
    """
    all_annot_sent_refs = dict()
    xlsx_files = list_files(".xlsx", path=INPUT)
    xlsx_files = [file for file in xlsx_files if file.startswith(lang)]
    for file in xlsx_files:
        file_sheet_names = openpyxl.load_workbook(os.path.join(INPUT, file), data_only=True).sheetnames
        file_sheet_names = [sheet for sheet in file_sheet_names if not re.search(r"^(#|[A-Z]+$)", sheet)]
        for sheet in file_sheet_names:
            text_name, annot_sent_ref = get_annotated_info(os.path.join(INPUT, file), sheet)
            all_annot_sent_refs[text_name] = annot_sent_ref
    text_name = choose_file(all_annot_sent_refs.keys(), "Text name:")
    if text_name == '':
        text_name = input("New text name (e.g., film_Bridge, conversation_Windhoek5, etc.): ")
    return text_name, all_annot_sent_refs.get(text_name, set())
    
    
def copy_input_file(filepath : str, destination : str) :
    """
    Copy input.txt to a destination
    Args:
        filepath (str): Path to the input file.
        destination (str): Path to the destination file.
    """
    with open(filepath, 'r') as file:
        input_file = file.read().split('\n\n')
    input_file = [sent.strip().split('\n') for sent in input_file if len(sent.strip().split('\n')) == 3]
    print("No ELAN export file selected, copying the existing input_file.txt to temp folder")
    print(f"\nNumber of sentences to annotate: {len(input_file)}\n")
    with open(destination, 'w') as file:
        for sent in input_file:
            file.write(f"{sent[0]}\n{sent[1]}\n{sent[2]}\n\n")

def read_file(filepath : str) -> list:
    """
    Read a file and return its content as a list of lines
    Args:
        filepath (str): Path to the file.
    Returns:
        list: List of lines in the file.
    """
    with open(filepath, 'r') as file:
        return file.read().split('\n')

def get_document_name(cell: str) -> str:
    """
    Get the document name from the conllu file
    Args:
        cell (str): The content of the first cell in the conllu file.
    Returns:
        str: The document name.
    """
    if re.search(r"^# newdoc( id)?\s*=\s*.+", cell):
        if 'id' not in cell:
            print(f'\n Warning: The document name field doesn\'t contain \'id\': {cell}')
        newdoc = cell
        return re.split(r"\s*=\s*", newdoc)[-1]
    else:
        print('\nCouldn\'t get the document name')
    return input("\nWhat should be the document name? \n film_Bridge, conversation_Windhoek5, etc.: ")

def not_paral(text : str):
    """
    Check if a sentence is not parallel
    Args:
        text (str): The text to check.
    Returns:
        bool: True if the text is not parallel, False otherwise.
    """
    i = 0
    text_clean = ''
    for a in text:
        if a == '[':
            i += 1
        elif a == ']':
            i -= 1
        elif i == 0 and a != ' ':
            text_clean += a
    return len(text_clean) > 0

def extract_sentences(elan : list, text_name : str, include_status : bool = False) -> list:
    """
    Extract sentences from the elan export file
    Args:
        elan (list): List of lines from the elan export file.
        text_name (str): Document name to prefix the sentence refs.
        include_status (bool): Whether the elan export includes status tier.
    Returns:
        list: List of dictionaries with keys 'ref', 'tx', 'fte', and '
    """
    sentences = []
    elan = [''] + elan
    for i, line in enumerate(elan):
        if line == '' and i < len(elan) - 3:
            if elan[i + 1] != '' and not_paral(elan[i + 2]) and not_paral(elan[i + 3]):
                if re.search(r'^\w+.+[\d|\w]+\.\d+(\.[\d|\w])?$', elan[i + 1]):
                    ref = text_name + '_' + '_'.join(elan[i + 1].split('.')[1:])
                elif re.search(r'\w+.+[\d|\w]+_\d+([_\d|_\w|\w])?$', elan[i + 1]):
                    ref = text_name
                    for part in elan[i + 1].split('_')[1:]:
                        if re.search(r'^\d+$', part) or re.search(r'^\d*\w$', part):
                            ref = ref + '_' + part
                sentences.append({
                        'ref': re.sub(r"_(0+)", "_", ref),
                        'tx': re.sub(r'\(([^\s]+)\)([^\s])', r'\1\2', elan[i + 2]),
                        'fte': elan[i + 3],
                        'status': elan[i + 4]
                    })
                # print(elan[i + 1], sentences[-1]['ref'])
    if not include_status:
        for sentence in sentences:
            sentence['status'] = 'DR'
    return sentences

def filter_dr_sentences(sentences : list) -> list:
    """
    Filter sentences that have DR in the status
    Args:
        sentences (list): List of dictionaries with keys 'ref', 'tx', 'fte', and 'status'.
    Returns:
        list: Filtered list of sentences with DR in the status.
    """
    dr = []
    for sentence in sentences:
        if re.search(r'_a$', sentence['ref']) and INCLUDE_LAB in sentence['status']:
            dr.append({
                'ref': sentence['ref'][:-2],
                'tx': re.sub(r"\s*\.\.\.\s*$", "", sentence['tx']),
                'fte': re.sub(r"\s*\.\.\.\s*$", "", sentence['fte'])
            })
        elif re.search(r'_[b-z]$', sentence['ref']) and dr[-1]['ref'] == sentence['ref'][:-2]:
            if INCLUDE_LAB in sentence['status']:
                dr[-1] = {
                    'ref': dr[-1]['ref'],
                    'tx': dr[-1]['tx'] + ' ' + re.sub(r"\s*\.\.\.\s*", "", sentence['tx']),
                    'fte': dr[-1]['fte'] + ' ' + re.sub(r"\s*\.\.\.\s*", "", sentence['fte'])
                }
            else:
                dr = dr[:-1]
        elif not re.search(r'_[b-z]$', sentence['ref']) and INCLUDE_LAB in sentence['status']:
            dr.append(sentence)
    return dr

def get_annotated_sentences(conllu : list, text_name : str = '') -> list:
    """
    Get refs of sentences that are already annotated from the conllu file
    Args:
        conllu (list): List of lines from the conllu file.
        text_name (str): Document name to prefix the sentence refs.
    Returns:
        list: List of refs of annotated sentences.
    """
    annotated = []
    for line in conllu:
        if re.search(r'^# sent_id = ' + text_name + r'_([^\s]+)', line):
            ref = re.search(r'^# sent_id = ' + text_name + r'_([^\s]+)\t', line).group(1)
            parts = re.split(r'_', ref)
            annotated.append(text_name + '_' + parts[0])
            if len(parts) == 2 and re.search(r'^\d+$', parts[0]) and re.search(r'^\d+$', parts[1]) and int(parts[0]) < int(parts[1]): #_201_202
                for i in range(int(parts[0]) + 1, int(parts[1]) + 1):
                    annotated.append(text_name + '_' + str(i))            
    return annotated

def write_to_file(filepath : str, sentences : list):
    """
    Write sentences to a file
    Args:
        filepath (str): Path to the output file.
        sentences (list): List of dictionaries with keys 'ref', 'tx', and 'fte'.
    """
    with open(filepath, 'w') as file:
        for sentence in sentences:
            file.write(f"{sentence['ref']}\n{sentence['tx']}\n{sentence['fte']}\n\n")
    print(f"\nNumber of sentences to annotate: {len(sentences_to_annotate)}\n") 


def get_annotated_info(path: str, sheet_name: str) -> tuple:
    """
    Get the document name and the set of refs of annotated sentences from the Google export file.
    Args:
        path (str): Path to the Google export file.
        sheet_name (str): Name of the sheet in the Google export file.
    Returns:
        tuple: A tuple containing the document name and the set of refs of annotated sentences.
    """
    sheet = openpyxl.load_workbook(path, data_only=True)[sheet_name]

    text_name = get_document_name(sheet['A2'].value)

    sent_ref = [cell.value for cell in sheet['A'] if cell.value and re.search(r"^# sent_id = ", cell.value)]
    sent_ref = [ref for ref in sent_ref if ref.startswith(f"# sent_id = {text_name}_")]
    sent_ref = [re.sub(r"^# sent_id = ", "", ref).strip() for ref in sent_ref]
    sent_ref_fin = []
    for ref in sent_ref:
        if re.search(fr'{text_name}_\d+[a-z]?$', ref):
            sent_ref_fin.append(ref)
        elif re.search(fr'{text_name}_\d+_\d+$', ref):
            parts = re.split(r'_', re.sub(fr'{text_name}_', '', ref))
            parts = [int(part) for part in parts]
            if parts[0] < parts[1]:
                for i in range(parts[0], parts[1] + 1):
                    sent_ref_fin.append(f"{text_name}_{i}")
            else:
                sent_ref_fin.append(re.sub(r'_\d+$', '', ref))
        elif re.search(fr'{text_name}_\d+[a-z]_\d$', ref):
            sent_ref_fin.append(re.sub(r'_\d$', '', ref))
        elif re.search(fr'{text_name}_\d+_[a-z]$', ref):
            sent_ref_fin.append(re.sub(r'_[a-z]$', '', ref))
        else:
            print(f"Warning: couldn't process the sentence reference: {ref}")
    sent_ref = sent_ref_fin
    
    return text_name, set(sent_ref)

if __name__ == "__main__":
    lang = get_language()

    # Choose the txt file to annotate
    input_file_name = choose_input_file(INPUT)
    if input_file_name == '':
        copy_input_file(os.path.join(INPUT, INPUT_FILE), os.path.join(TEMP, INPUT_FILE))
        exit()
    elan = read_file(os.path.join(INPUT, input_file_name)) + ['']
    include_status = input("ELAN export includes status tier? (y/N): ").lower() == 'y'

    # Choose the text name
    text_name, annot_sent_ref = choose_text_name(lang)

    # Extract and filter sentences
    sentences = extract_sentences(elan, text_name, include_status) 
    dr_sentences = filter_dr_sentences(sentences)
    sentences_to_annotate = [sentence for sentence in dr_sentences if sentence['ref'] not in annot_sent_ref]

    # Write to file
    write_to_file(os.path.join(TEMP, INPUT_FILE), sentences_to_annotate)
    