import re
import os

CUR_DIR = os.path.dirname(__file__)
PARENT_DIR = os.path.dirname(CUR_DIR)

INPUT_DIR = os.path.join(PARENT_DIR, "temp")
OUTPUT_DIR = os.path.join(PARENT_DIR, "output")

def read_file(file_name: str) -> list:
    """
    Reads a file from the INPUT_DIR and returns its lines as a list.
    Args:
        file_name (str): The name of the file to read.
    Returns:
        list: A list of lines from the file.
    """
    with open(os.path.join(INPUT_DIR, file_name), "r") as file:
        return file.read().split("\n")



if __name__ == '__main__':
    conllu = read_file("output_file.conllu")[:-2] # Exclude the last two lines which are empty
    nt = read_file("nt.conllu")
    if len(nt) > len(conllu):
        input_file = read_file("input_file.conllu")
        if all([re.search(r"^#\s.+|^\s*$", line) for line in input_file[len(conllu):]]):
            conllu = conllu + input_file[len(conllu):]
    if len(nt) != len(conllu):
        raise ValueError("The number of lines in nt.txt does not match the number of lines in output_file.conllu (including).")
    conllu = [conllu[i] + "\t" + nt[i].split("\t")[-1] for i in range(len(nt))]
    with open(os.path.join(OUTPUT_DIR, "output_file.conllu"), "w") as file:
        file.write("\n".join(conllu))
