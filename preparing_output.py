import re
from os.path import join

TEMP = "temp"
OUTPUT = "output"

def read_input_file() -> list:
    """
    Reads the input file and returns a list of lines.
    The input file is expected to be located in the TEMP directory and named 'input_file.txt'.
    Returns:
        list: A list of lines read from the input file located in the TEMP directory.
    """
    with open(join(TEMP,'input_file.txt'), 'r') as file:
        return file.readlines()

def create_sentence_list(lines: list) -> list:
    """
    Creates a list of sentences from the input lines. Each sentence is represented as a list of three lines: sentence_id, text, and english translation.
    Args:
        lines (list): A list of lines read from the input file.
    Returns:
        list: A list of sentences, where each sentence is a list of three lines (sentence_id, text, english translation). 
             The resulting list contains sublists, each representing a complete sentence with its associated metadata.
    """
    sentence_list = []
    sentence = []
    for line in lines:
        if line.startswith('# sent_id') or line.startswith('# text'):
            sentence.append(line)
        if line.startswith('# english'):
            sentence.append(line)
            sentence_list.append(sentence)
            sentence = []
    return sentence_list

def process_output_file(i: int) -> list:
    """
    Reads the output file corresponding to the given index, processes its lines by skipping the header and modifying specific tab patterns, and returns the processed lines.
    Args:
        i (int): The index of the output file to be processed.
    Returns:
        list: A list of processed lines from the specified output file. 
    """
    with open(join(TEMP, f'output_file-{i+1}.conllu'), 'r') as file:
        output_lines = file.readlines()[4:]  # Skip header lines
        output_lines = [re.sub(r'\t(\'|\")\t', r'\t\'\1\t', line) for line in output_lines]
    return output_lines

def combine_lines(sentence_list: list) -> list:
    """
    Combines the input annotations with the processed output lines for each sentence.
    For each sentence in the sentence list, it retrieves the corresponding processed output lines and concatenates them with the sentence metadata lines. 
    Args:
        sentence_list (list): A list of sentences, where each sentence is a list of three lines (sentence_id, text, english translation).
    Returns:
        list: A combined list of lines that includes the metadata lines for each sentence followed by the corresponding processed output lines. 
            The resulting list contains all the combined lines for all sentences in the input list.
    """
    lines_full = []
    for i, sentence in enumerate(sentence_list):
        output_lines = process_output_file(i)
        lines_full = lines_full + sentence + output_lines
    return lines_full

def save_combined_file(combined_lines: list):
    """
    Saves the combined lines to the specified output file.
    The combined lines are written to a new file named 'output_file.conllu' in the OUTPUT directory. 
    The file starts with a header line '# newdoc' followed by the combined lines.
    Args:
        combined_lines (list): A list of combined lines that includes the metadata lines for each sentence followed by the corresponding processed output lines. 
    """
    with open(join(OUTPUT, 'output_file.conllu'), 'w') as file:
        file.write('# newdoc\n')
        for item in combined_lines:
            file.write(item)

def main():
    """
    Main function that orchestrates reading input, processing files, combining lines, and saving the output to a new file.
    """
    input_lines = read_input_file()
    sentence_list = create_sentence_list(input_lines)
    combined_lines = combine_lines(sentence_list)
    save_combined_file(combined_lines)

if __name__ == '__main__':
    main()
