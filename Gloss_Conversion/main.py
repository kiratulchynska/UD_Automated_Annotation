import os
import sys
import re
import pandas as pd
import json
from tqdm import tqdm
import openpyxl

from tokenization import tokenization

CUR_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CUR_DIR)

PARENT_INPUT = os.path.join(PARENT_DIR, "input") # input directory of Automated Annotating with input file a google export file
OUTPUT_DIR = os.path.join(PARENT_DIR, "temp") # temp directory of Automated Annotating for output files

RPUNCT = r"[.,!?;:\"”“\(\)\[\]{}<>…'’/]" # maybe more

def choose_text_name(lang: str) -> tuple[str, set]:
    """
    Choose the name of the text from the Google export files.
        Args:
        lang (str): Language code to filter the files.
    Returns:
        tuple: A tuple containing the chosen text name and all annotated sentence references for that text.
    """
    all_annot_sent_refs = dict()
    xlsx_files = list_files(".xlsx", path=PARENT_INPUT)
    xlsx_files = [file for file in xlsx_files if file.startswith(lang)]
    for file in xlsx_files:
        file_sheet_names = openpyxl.load_workbook(os.path.join(PARENT_INPUT, file), data_only=True).sheetnames
        file_sheet_names = [sheet for sheet in file_sheet_names if not re.search(r"^(#|[A-Z]+$)", sheet)]
        for sheet in file_sheet_names:
            text_name, annot_sent_ref = get_annotated_info(os.path.join(PARENT_INPUT, file), sheet)
            all_annot_sent_refs[text_name] = annot_sent_ref
    text_name = choose_file(list(all_annot_sent_refs.keys()), "Text name:")
    if text_name == '':
        text_name = input("New text name (e.g., film_Bridge, conversation_Windhoek5, etc.): ")
    return text_name, all_annot_sent_refs.get(text_name, set())

def get_annotated_info(path: str, sheet_name: str) -> tuple[str, set]:
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

def process_input_temp(path: str) -> tuple[list, int]:
    """
    Process the input_temp file and return a list of glosses and the number of sentences.
    Args:
        path (str): Path to the input_temp file.
    Returns:
        tuple: A tuple containing a list of glosses and the number of sentences.
    """
    # Read the input_temp file
    required_line_types = {'ref', 'tx', 'fte', 'mb', 'ge'}
    additional_line_types = {'ps', 'nt'}

    with open(path, "r") as f:
        input_temp = f.read().split('\n')
        input_temp = [line.strip() for line in input_temp if line.strip()]
    sent_len = len(input_temp)

    if len(set(input_temp) - required_line_types - additional_line_types) != 0:
        print(f"""Unknown line types in input_temp: {set(input_temp) - required_line_types - additional_line_types}.\n
        Only the following line types are allowed: {required_line_types + additional_line_types}.""")
        exit(1)
    elif len(required_line_types - set(input_temp)) != 0:
        print(f"""Missing line types in input_temp: {required_line_types - set(input_temp)}.\n
        The following line types are required: {required_line_types}.""")
        exit(1)
    return input_temp, sent_len

def process_input(path: str, sent_len: int) -> list:
    """
    Process the input file and return a list of sentences.
    Args:
        path (str): Path to the input file.
        sent_len (int): Number of lines in each sentence.
    Returns:
        list: List of sentences, each sentence is a dictionary with keys "text" and "rows".
    """
    # Read the input file
    with open(path, "r") as f:
        lines = f.readlines()

    # for Chintang
    vowels = {"ã" : "ã", "ĩ" : "ĩ", "ũ" : "ũ"} 
    for k, v in {k: v for k, v in vowels.items() if k in lines}.items():
        lines = re.sub(k, v, lines)
    
    sentences = []
    for i, line in enumerate(lines):
        line = line.strip()
        if line == "" and '-' not in sentences[-1]["rows"]:
            # If the line is empty and the sentence doesn't have it's end, add it's end
            sentences[-1]["rows"] += f"-{i}"
        elif line != "":
            # If the line is not empty and the last sentence is not empty, add a new sentence
            if len(sentences) == 0 or re.search(r"\d+[-]\d+", sentences[-1]["rows"]):
                sentences.append({"text": [], "rows": str(i+1)})
            # Add the line to the current sentence
            sentences[-1]["text"].append(line)
    if lines[-1].strip() != "":
        sentences[-1]["rows"] += f"-{len(lines)}"
        # Remove the last sentence if it is empty
    if len(sentences) > 0 and sentences[-1]["text"] == []:
        sentences.pop()
    
    if sentences[0]["text"][0].startswith('file:'):
        sentences = sentences[1:]

    if [sentence for sentence in sentences if len(sentence['text']) != sent_len]:
        print(f"All sentences should have the same number of lines as input_temp: {sent_len}. Errors in sentences in lines:")
        for sentence in [sentence for sentence in sentences if len(sentence['text']) != sent_len]:
            print(f"Lines {sentence['rows']}:\n{'\n'.join(sentence['text'])}.\n")
        
        skip = input("Skip the sentences? (Y/n): ")
        if len(skip) > 0 and skip[0].lower() != 'y':
            print("Exiting.")
            exit()
        else:
            print("Skipping sentences with errors.\n")
            sentences = [sentence for sentence in sentences if len(sentence['text']) == sent_len]
    return sentences

def process_vocab_db(path: str) -> tuple[pd.DataFrame, dict]:
        """
        Process the vocab file and return a DataFrame with the vocab information.
        Args:
            path (str): Path to the vocab file.
        Returns:
            tuple: A tuple containing a DataFrame with the vocab information and a dictionary with the part of speech transformation.
        """

        def transform_ps(ps, transf) -> str:
            """
            Transform the part of speech (ps) using a JSON file.
            Args:
                ps (str): The part of speech to transform.
                transf (dict): The transformation dictionary loaded from the JSON file.
            Returns:
                str: The transformed part of speech.
            """
            if ps in transf.keys():
                return transf[ps]
            else:
                return "X"

        def get_entry_info(entry) -> pd.DataFrame:
            """
            Process a single entry in the vocab file and return a dictionary with the entry information.
            Args:
                entry (str): A single entry from the vocab file.
            Returns:
                pd.DataFrame: DataFrame containing the entry information.
            """
            entry = entry.split("\n")
            entry_info = {"lex": "",
                        "alt": [],
                        "ps": "",
                        "ge": []}
            
            with open(os.path.join(LANG_DIR, "ps.json"), "r") as f:
                transf = json.load(f)

            for line in [line for line in entry if re.search(r"\\(\w+)\s(.*)$", line)]:
                tag, cell = re.search(r"\\(\w+)\s(.*)$", line).groups()
                if tag in ["lex", "alt"]:
                    vowels = {"ã" : "ã", "ĩ" : "ĩ", "ũ" : "ũ"}
                    for k, v in {k: v for k, v in vowels.items() if k in cell}.items():
                        cell = re.sub(k, v, cell)
                if tag == "lex":
                    entry_info[tag] = cell
                elif tag == "alt":
                    entry_info[tag].append(cell)
                elif tag == "ps":
                    entry_info[tag] = transform_ps(cell.strip(), transf)
                elif tag == "ge":
                    entry_info[tag] = re.split(r";\s", cell.lower().strip())
            return entry_info
        if not os.path.exists(path):
            return pd.DataFrame(columns=["lex", "alt", "ps", "ge"])
        with open(path, "r") as f:
            vocab = f.read().split("\n\n")
        vocab = [get_entry_info(entry) for entry in vocab]
        vocab = pd.DataFrame.from_dict(vocab)
        # print(vocab[1095:1105])
        return vocab

def process_vocab_xlsx(path: str) -> tuple[pd.DataFrame, dict]:
        """
        Process the vocab xlsx file and return a DataFrame with the vocab information.
        Args:
            path (str): Path to the vocab xlsx file.
        Returns:
            tuple: A tuple containing a DataFrame with the vocab information and a dictionary with the part of speech transformation.
        """

        def transform_ps(ps: str, transf: dict) -> str:
            """
            Transform the part of speech (ps) using a JSON file.
            Args:
                ps (str): The part of speech to transform.
                transf (dict): The transformation dictionary loaded from the JSON file.
            Returns:
                str: The transformed part of speech.
            """
            if ps in transf.keys():
                return transf[ps]
            else:
                return "X"
            
        vocab = pd.read_excel(os.path.join(LANG_DIR, "vocab.xlsx"))
        with open(os.path.join(LANG_DIR, "ps.json"), "r") as f:
            transf = json.load(f)
        vocab["pos"] = vocab["pos"].apply(lambda ps: transform_ps(ps, transf))

        # print(vocab.loc[[2661, 2662],["ID", "Lemma", "citation_plur", "pos", "NC"]])

        return vocab, transf

def process_glosses(path: str) -> dict:
        """
        Process the glosses file and return a dictionary with the glosses information.
        Args:
            path (str): Path to the glosses file.
        Returns:
            dict: Dictionary containing the glosses information.
        """
        with open(path, "r") as f:
            glosses = json.load(f)
        return glosses

def check_files() -> None:
    """
    Check if the lang and output directories exist, and if the required files are present in the lang directory.
    Returns:
        None
    """

    # Check if the lang directory exists
    if not os.path.exists(LANG_DIR):
        print(f"Grammar directory '{lang}' does not exist.")
        exit(1)

    file_names = ["glosses.json",
                  "input_temp.txt",
                  "ps.json"]
                  # + vocab

    for name in file_names:
        if not os.path.exists(os.path.join(LANG_DIR, name)):
             print(f"File {name} does not exist in the lang directory.")
             exit(1)
    if not os.path.exists(os.path.join(LANG_DIR, "vocab.db")) and not os.path.exists(os.path.join(LANG_DIR, "vocab.xlsx")):
        print(f"File vocab.db or vocab.xlsx does not exist in the lang directory.")
        exit(1)

    # Check if the output directory exists, if not create it
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR) 


def process_files(lang: str, input_file: str) -> tuple[list, list, pd.DataFrame, dict, dict]:
    """
    Process the grammar files and return the input_temp, sentences, vocab, and glosses.
    Args:
        lang (str): Language name.
        input_file (str): Name of the input file containing glosses.
    Returns:
        tuple: A tuple containing the input_temp, sentences, vocab, transf, and glosses.
    """
    
    # input_temp - glosses template
    input_temp, sent_len = process_input_temp(os.path.join(LANG_DIR, "input_temp.txt"))

    # input.txt - input glosses
    sentences = process_input(os.path.join(PARENT_INPUT, input_file), sent_len)

    # vocab.db/.xlsx - vocabulary data base
    if os.path.exists(os.path.join(LANG_DIR, "vocab.db")): 
        vocab, transf = process_vocab_db(os.path.join(LANG_DIR, "vocab.db"))
    else:
        vocab, transf = process_vocab_xlsx(os.path.join(LANG_DIR, "vocab.xlsx"))

    # glosses.json - json with glosses info
    glosses = process_glosses(os.path.join(LANG_DIR, "glosses.json"))

    return input_temp, sentences, vocab, transf, glosses

def process_sent(sent: list, vocab: pd.DataFrame, transf: dict, glosses: dict) -> tuple[str, str]:
    """
    Process a single sentence and return it in CoNLL-U format.
    Args:
        sent (list): List of sentences.
        vocab (pd.DataGrame): DataFrame of vocab
        transf (dict): dictionary of part of speech transformation
        glosses (dict): dictionary of glosses info
    Returns:
        tuple: A tuple containing the CoNLL-U formatted sentence and the notes.
    """

    conllu = ["# sent_id = " + sent["ref"], 
              "# text = " + sent["tx"],
              "# english = " + sent["fte"]]
    nt = conllu.copy()
    nt = [line + "\t" for line in nt] # add tabs to the end of each line for nt file

    token_list = tokenization(sent["tx"], RPUNCT)
    word_list = segmentation(sent, token_list, RPUNCT, transf)
    if len(word_list) == 1 and type(word_list[0]) == str and word_list[0].startswith("# Error:"):
        return "\n".join(conllu) + "\n" + word_list[0], "\n".join(nt) + "\n" + word_list[0]
    word_list = morphology(word_list, RPUNCT, vocab, glosses)
    
    columns = ["id", "form", "lemma", "upostag", "xpostag", "feats", "head", "deprel", "deps", "misc"]
    for word in word_list:
        if "misc" in word.keys() and word["misc"] != {}:
            word["misc"] = sorted([f"{k}={v}" for k, v in word["misc"].items()])
            word["misc"] = "|".join(word["misc"])
        else:
            word["misc"] = "_"
            
        if len(word["nt"]) > 0:
            word["nt"] = "TODO " + "; ".join(word["nt"])
        else:
            word["nt"] = ""
        conllu.append("\t".join([word.get(col, "_") for col in columns]))
        nt.append("\t".join([word.get(col, "_") for col in columns])+"\t"+word["nt"])
    conllu = "\n".join(conllu)
    nt = "\n".join(nt)
    return conllu, nt

def list_files(extension: str, path: str ='input') -> list:
    """
    List all files in the INPUT directory with the specified extension.
    Args:
        extension (str): File extension to filter by.
        path (str): Path to the directory.
    Returns:
        list: List of files with the specified extension.
    """
    if not os.path.exists(path):
        return []
    files = [file for file in os.listdir(path) if file.endswith(extension)]
    files.sort()
    return files

def choose_file(files: list, prompt: str) -> str:
    """
    Choose a file from a list of files
    Args:
        files (list): List of files to choose from.
        prompt (str): Prompt to display to the user.
    Returns:
        str: The chosen file name or an empty string if no file is chosen.
    """ 
    if len(files) == 0:
        print(f"No files found in the directory {prompt}.")
        return '' 
    print('\n', prompt)
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
    
def choose_input_file() -> str:
    """
    Choose a glosses file from the input directory.
    Returns:
        str: The chosen file name or an empty string if no file is chosen.
    """
    txt_files = list_files(".txt", path=PARENT_INPUT)
    input_file_name = choose_file(txt_files, "Glosses files:")
    if input_file_name == '':
        print("No glosses file selected, exiting.")
        exit(1)
    return input_file_name

def clean_para(sentences: list) -> list:
    """
    Clean sentences from paralinguistic items
    Args:
        sentences (list): List of sentences, each sentence is a dictionary with keys "text" and "rows".
    Returns:
        list: List of cleaned sentences, each sentence is a dictionary with keys "text" and "
    """
    cleaned_sentences = []
    for sent in sentences:
        for key in sent.keys():
            if key == "ref":
                continue
            line = sent[key]
            if '[' in line:
                line = re.sub(r"\[[^\]]+\]\s*", "", line).strip()
                sent[key] = line
            if '***' in line:
                line = re.sub(r"\*\*\*\s*", "", line).strip()
                sent[key] = line
            if "para" in line:
                line = re.sub(r"\bpara\s*", "", line).strip()
                sent[key] = line
            
        if all(line != "" for line in sent.values()):
            cleaned_sentences.append(sent)
    return cleaned_sentences

def annotate_input(lang: str, text_name: str, annot_sent_ref: set, input_file_name: str) -> None:
    """
    Process the input sentences and write them to the output files in CoNLL-U format.
    Args:
        lang (str): Language name.
        text_name (str): Name of the text.
        annot_sent_ref (set): Set of refs of annotated sentences.
        input_file_name (str): Name of the input file containing glosses.
    Returns:
        None
    """
    input_temp, sentences, vocab, transf, glosses = process_files(lang, input_file_name)

    conllu = []
    nt = []
    n_errors = 0
    # n_done = 0
    print()
    sentences = [{line_type: sent["text"][i] for i, line_type in enumerate(input_temp)} for sent in sentences]
    sentences = clean_para(sentences)
    sentences = [sent for sent in sentences if all(line != "" for line in sent.values())]
    for sent in sentences:
        sent["ref"] = text_name + '_' + re.search(r"^.*\.(\d.*)$", sent["ref"]).group(1)
        sent["ref"] = re.sub(r'_0+', '_', sent["ref"])
    sentences = [sent for sent in sentences if sent['ref'] not in annot_sent_ref]
    print(f"Number of already annotated sentences: {len(annot_sent_ref)}")
    print(f"Number of sentences to annotate: {len(sentences)}\n")

    for sent in tqdm(sentences):
        sent, sent_nt = process_sent(sent, vocab, transf, glosses)
        if len(conllu) > 0 and re.search(r"\n# Error:[^\n]+$", conllu[-1]) and len(sent) > 0:
            conllu[-1] += "\n" + sent
            nt[-1] += "\n" + sent_nt
            n_errors += 1
        elif len(sent) > 0:
            conllu.append(sent)
            nt.append(sent_nt)
        # else:
        #     n_done += 1

    with open(os.path.join(OUTPUT_DIR, "input_file.conllu"), "w") as f:
        f.write("\n\n".join(conllu))
    with open(os.path.join(OUTPUT_DIR, "nt.conllu"), "w") as f:
        f.write("\n\n".join(nt))
    # print(f"Tokenized abd tagged input written to {os.path.join(OUTPUT_DIR, "input_file.conllu")}.")
    print("\nNumber of sentences to parse: ", len(sentences)-n_errors)
    print("Number of sentences skipped because of errors: ", n_errors, '\n')

def copy_input_file(filepath: str, destination: str) -> None:
    """
    Copy the input_file.txt to the temp folder if no ELAN export file is selected.
    Args:
        filepath (str): Path to the input_file.txt.
        destination (str): Path to the destination file in the temp folder.
    Returns:
        None
    """
    with open(filepath, 'r') as file:
        input_file = file.read().split('\n\n')
    input_file = [sent.strip().split('\n') for sent in input_file if len(sent.strip().split('\n')) == 3]
    print("No glosses file selected, copying the existing input_file.txt to temp folder")
    print(f"\nNumber of sentences to annotate: {len(input_file)}\n")
    with open(destination, 'w') as file:
        for sent in input_file:
            file.write(f"{sent[0]}\n{sent[1]}\n{sent[2]}\n\n")

if __name__ == "__main__":
    lang = sys.argv[1] if len(sys.argv) > 1 else 'Ruuli'
    LANG_DIR = os.path.join(CUR_DIR, lang)
    check_files()

    if lang == 'Chintang':
        from Chintang.word_segmentation import segmentation
        from Chintang.morphological_analysis import morphology
    elif lang == 'Ruuli':
        from Ruuli.word_segmentation import segmentation
        from Ruuli.morphological_analysis import morphology
    else:
        print(f"Language '{lang}' not supported.")
        exit(1)

    # Choose the txt file to annotate
    input_file_name = choose_input_file()

    text_name, annot_sent_ref = choose_text_name(lang)

    annotate_input(lang, text_name, annot_sent_ref, input_file_name)
    


