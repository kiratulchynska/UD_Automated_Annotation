import re
import sys
from os.path import join

INPUT = 'input'
TEMP = 'temp'
INPUT_FILE = 'input_file.txt'

def get_language() -> str:
    """
    Asks the user for the language of the input file. If the language is not specified, the user is prompted to enter it.
    Returns:
        str: The language code followed by an underscore (e.g., 'KKG_', 'Suansu_', 'Ruuli_'). 
            If the language is not specified, returns an empty string.
    """
    if len(sys.argv) > 1:
        lang = sys.argv[1]
    else:
        lang = input("Language (KKG, Suansu, Ruuli) or NONE if it is the only one in the inpute dir: ")


    if lang == 'NONE':
      return '' 
    else:
      return lang + '_'

def read_input_file(file_path: str) -> list:
    """
    Reads the input file and extracts the sentences.
    Args:
        file_path (str): The path to the input file.
    Returns:
        list: A list of sentences, where each sentence is a list of three lines (sentence_id, text, english translation). 
    """
    with open(file_path, 'r') as file:
        input_lines = file.readlines()

    if input_lines[0].startswith('file:'):
        input_lines = input_lines[3:]

    i = 0
    sent = []
    input_sentences = []
    while i < len(input_lines):
        if input_lines[i] != '\n':
            sent.append(input_lines[i])
        else:
            input_sentences.append(sent)
            sent = []
        i += 1
    return [sent for sent in input_sentences if len(sent) == 3]

def write_text_files(input_lines_tx: list):
    """
    Writes each extracted text sentence into a separate file named sequentially in the TEMP directory.
    The files are named 'input_file_tx-1.txt', 'input_file_tx-2.txt', etc., corresponding to the order of the sentences in the input list.
    Args:
        input_lines_tx (list): A list of text sentences extracted from the input file. Each sentence is expected to be a string. 
    """
    for i, item in enumerate(input_lines_tx):
        with open(join(TEMP, f'input_file_tx-{i+1}.txt'), 'w') as file:
            file.write(item)

def create_marked_input_file(input_sentences: list):
    """
    Creates a new input file where every sentence is marked with metadata lines (# sent_id, # text, # english).
    The marked sentences are written to a new file named 'input_file.txt' in the TEMP directory. Each sentence is separated by a blank line.
    Args:
        input_sentences (list): A list of sentences, where each sentence is a list of three lines (sentence id, text, english translation).
    """
    input_lines_marked = []
    for sent in input_sentences:
            input_lines_marked.append(f'# sent_id = {sent[0]}')
            input_lines_marked.append(f'# text = {sent[1]}')
            input_lines_marked.append(f'# english = {sent[2]}\n')

    with open(join(TEMP, 'input_file.txt'), 'w') as file:
        file.writelines(input_lines_marked)

def clean_training_file(lang: str):
    """
    Cleans the training file by removing extra tabs, empty tabbed lines, and stray '??'.
    The cleaned training file is saved with the same name in the TEMP directory, overwriting the original file.
    Args:
        lang (str): The language code used as a prefix for the training file name (e.g., 'KKG_', 'Suansu_', 'Ruuli_'). The training file is expected to be named '{lang}training_file.conllu' in the TEMP directory.
    """
    with open(join(TEMP, f'{lang}training_file.conllu'), 'r') as file:
        training = file.read()

    training = re.sub(r'\t+', '\t', training)
    training = re.sub(r'\t\n', '\n', training)
    training = re.sub(r'\?\?', '', training)

    with open(join(TEMP, f'{lang}training_file.conllu'), 'w') as file:
        file.write(training)    

if __name__ == "__main__":
    
    lang = get_language()

    input_sentences = read_input_file(join(TEMP, INPUT_FILE))

    input_lines_tx = [sent[1] for sent in input_sentences]
  
    write_text_files(input_lines_tx)
    create_marked_input_file(input_sentences)

    clean_training_file(lang)
