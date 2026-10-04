import os
import re
from conllu_from_xlsx import get_language

INPUT_PATH = 'conllu_files'
OUTPUT_PATH = 'data_split'

def transform_split(split: dict) -> dict:
    """
    Transform the split dictionary to a flat dictionary with keys as text_id and values as dataset.
    If the end is -1, it means from start to the end of the file.
    split: dictionary with keys as text and values as dictionary with keys as dataset and values as (start, end)
    return: flat dictionary with keys as text_id and values as dataset
    """
    flat_split = {}
    for text in split:
        for dataset in split[text]:
            start, end = split[text][dataset]
            if end == -1:
                flat_split[text + '_x'] = dataset
            else:
                for id in range(start, end + 1):
                    flat_split[f'{text}_{id}'] = dataset

    return flat_split

def save_dataset(dataset_dict: dict, dataset: str, text_order: list):
    """
    Save the dataset to a file.
    dataset_dict: dictionary with keys as newdoc_id and values as list of lines
    dataset: name of the dataset
    text_order: order of texts to save
    """
    datatset_lines = []
    for text_id in text_order:
        datatset_lines.extend(dataset_dict.get(text_id, []))
    with open(os.path.join(OUTPUT_PATH, f'{output_prephix}-{dataset}.conllu'), 'w') as f:
        f.write('\n'.join(datatset_lines) + '\n')

def KKG():
    """
    KKG function to get the KKG language.
    return: tuple of input file, output prefix and split
    """
    input_file = 'KKG_training_file.conllu'
    output_prephix = 'naq_kdt-ud'
        
    # (start, end) sent_id of start and end, both including
    # (start, -1) means from [start] to the end of the file
    split = {'grammar_Cairo' : {'train': (1, -1)},
         'grammar_BivalTyp' : {'train': (71, -1), 'dev': (61, 70), 'test': (1, 60)},
         'film_Bridge' : {'train': (173, -1), 'dev': (1, 172)},
         'film_Titanic' : {'test': (1, -1)},
         'book_Khomai_2' : {'train': (1, -1)},
         'book_Khomai_4' : {'test': (1, -1)},
         'book_Khomai_5' : {'test': (1, -1)},
         'book_Khomai_6' : {'test': (1, -1)},
         'book_Khomai_7' : {'train': (1, -1)},
         'book_Khomai_9' : {'test': (1, -1)},
         'book_Khomai_10' : {'test': (1, -1)},
         'book_Khomai_11' : {'test': (1, -1)},
         'book_Khomai_15' : {'train': (1, -1)},
         'book_Khomai_17' : {'test': (1, -1)},
         'book_Khomai_21' : {'test': (1, -1)},
         'book_Khomai_23' : {'test': (1, -1)},
         'book_Khomai_25' : {'train': (1, -1)},
         'book_Khomai_26' : {'test': (1, -1)},
         'book_Khomai_27' : {'test': (1, -1)},
         'conversation_Windhoek5' : {'train' : (401, -1), 'dev' : (351, 400), 'test': (1, 350)},
    }
    return input_file, output_prephix, split


def Suansu():
    """
    Suansu function to get the Suansu language.
    return: tuple of input file, output prefix and split
    """ 
    input_file = 'Suansu_training_file.conllu'
    output_prephix = 'nmf_suansu-ud'

    # (start, end) sent_id of start and end, both including
    # (start, -1) means from [start] to the end of the file
    split = {
        'grammar_Cairo' : {'train': (1, -1)},
        'grammar_BivalTyp' : {'test': (1, -1)},
        'grammar_ValPal' : {'test': (1, -1)},
        'film_Bridge' : {'test': (1, -1)},
    }
    return input_file, output_prephix, split

def Chintang():
    """
    Chintang function to get the Chintang language.
    return: tuple of input file, output prefix and split
    """ 
    input_file = 'Chintang_training_file.conllu'
    output_prephix = 'ctn_ctntb-ud'

    # (start, end) sent_id of start and end, both including
    # (start, -1) means from [start] to the end of the file
    split = {
        'grammar_Introduction' : {'test': (1, -1)},
        'grammar_Morphology' : {'test': (1, -1)},
        'grammar_Syntactic' : {'test': (1, -1)},
        'grammar_Tmap' : {'test': (1, -1)},
        'grammar_Reference' : {'test': (1, -1)},
        'grammar_Information' : {'test': (1, -1)},
        'grammar_Complex' : {'test': (1, -1)}
    }
    return input_file, output_prephix, split

def Ruuli():
    """
    Ruuli function to get the Ruuli language.
    return: tuple of input file, output prefix and split
    """ 
    input_file = 'Ruuli_training_file.conllu'
    output_prephix = 'ruc_rdt-ud'

    # (start, end) sent_id of start and end, both including
    # (start, -1) means from [start] to the end of the file
    split = {
        'books_Aniinire' : {'train': (1, -1)},
        'conversations_Gweero' : {'train': (1, -1)},
        'conversations_Nakasongola1' : {'train': (1, -1)},
        'conversations_Nakasongola1b' : {'train': (1, -1)},
        'conversations_Nakasongola2' : {'train': (1, -1)},
        'conversations_Sokoso' : {'train': (1, -1)},
        'films_Inception' : {'train': (1, -1)},
        'grammar_Syntax' : {'test': (1, -1)},
    }
    return input_file, output_prephix, split
    

if __name__ == '__main__':
    language = get_language()
    if language == 'KKG':
        input_file, output_prephix, split = KKG()
    elif language == 'Suansu':
        input_file, output_prephix, split = Suansu()
    elif language == 'Chintang':
        input_file, output_prephix, split = Chintang()
    elif language == 'Ruuli':
        input_file, output_prephix, split = Ruuli()
    else:
        raise ValueError('Language not supported')
    
    text_order = split.keys()

    if not os.path.exists(OUTPUT_PATH):
        os.makedirs(OUTPUT_PATH)
    with open(os.path.join(INPUT_PATH, input_file), 'r') as f:
        orig_conllu = f.read().splitlines()

    flat_split = transform_split(split)

    new_conllu = {'train': dict(), 'dev': dict(), 'test': dict()}
    newdoc = {'train' : True, 'dev': True, 'test': True}
    stats = {'train': {'Sum' : 0}, 'dev': {'Sum' : 0}, 'test': {'Sum' : 0}}

    for line in orig_conllu:
        if line.startswith('# newdoc'):
            newdoc['train'] = True
            newdoc['dev'] = True
            newdoc['test'] = True
            newdoc_id = line.split('\t')[0].split('# newdoc id = ')[1]
        else:
            if line.startswith('# sent_id = '):
                sent_id = line.split('\t')[0].split('# sent_id = ')[1]
                if sent_id in flat_split or '_'.join(sent_id.split('_')[-1]) in flat_split:
                    dataset = flat_split[sent_id]
                elif newdoc_id + '_x' in flat_split:
                    dataset = flat_split[newdoc_id + '_x']
                else:
                    exit(f'No dataset found for {sent_id}')

                if newdoc_id not in new_conllu[dataset].keys():
                    new_conllu[dataset][newdoc_id] = []
                if newdoc[dataset]:
                    newdoc[dataset] = False
                    new_conllu[dataset][newdoc_id].append(f'# newdoc id = {newdoc_id}')
            if line.split('\t')[0] != '' or new_conllu[dataset][newdoc_id][-1].split('\t')[0] != '':
                new_conllu[dataset][newdoc_id].append(line)

            if newdoc_id not in stats[dataset]:
                stats[dataset][newdoc_id] = 0
            if re.search(r'^\d+\t', line):
                stats[dataset][newdoc_id] += 1
                stats[dataset]['Sum'] += 1

    for dataset in new_conllu:
        save_dataset(new_conllu[dataset], dataset, text_order)
        print(f'{dataset}:')
        for doc in text_order:
            if doc in stats[dataset]:
                print(f'\t{doc}: {stats[dataset][doc]}')
        print(f'\tSum: {stats[dataset]["Sum"]}')
        print()

