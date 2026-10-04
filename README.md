## Description

This project is designed to train a UDPipe model and annotate text using it. Additionally, it includes a gloss conversion module (`Gloss_Conversion`) for processing linguistic data, which can handle glosses, word segmentation, and morphological analysis.

---

## Prerequisites

- Python 3.8 or higher.
- Required Python libraries (see `requirements.txt`):
   - `et_xmlfile` and `openpyxl` for the main annotation process.
   - Additional libraries for the `Gloss_Conversion` module.
- `udpipe` (1) folder is inside the `Automated_Annotating` directory.

To set up the Python environment:
```bash
python -m venv .venv
pip install -r requirements.txt
```

---

## Directory Structure

```
Automated_Annotating/
├── annotate.sh                # Main script for annotation
├── glosses.sh                 # Script for converting glosses into .conllu format
├── input/                     # Directory for input files
├── output/                    # Directory for final output files
├── temp/                      # Temporary files directory
├── conllu_files/              # Intermediate .conllu files
├── Gloss_Conversion/          # Gloss conversion module
│   ├── LANGUAGE/              # Folder for each language
│   │   ├── glosses.json       # JSON file with gloss abbreviations
│   │   ├── input_temp.txt     # Input template for recognized values
│   │   ├── ps.json            # JSON mapping vocabulary `ps` labels to POS tags
│   │   ├── vocab.db           # Vocabulary database (SQLite)
│   │   ├── vocab.xlsx         # Vocabulary database (Excel format)
│   │   ├── word_segmentation.py # Script for word segmentation
│   │   ├── morphological_analysis.py # Script for morphological analysis
│   ├── main.py                # Main script for gloss conversion (tokenizing and tagging glosses)
│   ├── tokenization.py        # Tokenizes the input text 
│   ├── preparing_output.py    # Processes annotated output
│   ├── README.md              # Gloss conversion documentation
│   conllu_from_xlsx.py        # Converts .xlsx to .conllu
│   input_file.py              # Prepares input files
│   preparing_input.py         # Processes input files
│   preparing_output.py        # Processes annotated output
│   join_conllu.py             # Joins .conllu files
│   data_split.py              # Splits data into train, test and dev files
│   analyse.ipynb              # Info about annotated data (POS, Features and Values, Dependencies)
├── udpipe/                    # UDPipe binary and related files
│   ├── src/                   # Source files for UDPipe
│   ├── models/                # Pre-trained or trained models
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
\```

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alenawitzlack/Event_packaging.git
   ```

2. Navigate to the `Automated_Annotating` directory. Replace `PATH` with the location of the cloned directory:
   ```bash
   cd PATH/Event_packaging/scripts/Automated_Annotating
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

---

## How to Run

### 1. **Prepare Input Files**  
Place the following files into the `input` folder:

- **Input sentences**: These can be ELAN exports or files generated in other ways. The structure should follow one of these formats:
  1. `input_file.txt`: The file should consist of `ref`, `tx`, `fte` lines for each sentence (in this order, without tier labels), with an empty line between sentences.
  2. Other `.txt` files: These should consist of `ref`, `tx`, `fte`, `status` lines for each sentence (in this order, without tier labels), with an empty line between sentences. The `status` tier should include **DR** if the sentence requires annotation. This parameter can be modified in the `input_file.py` script by changing the `INCLUDE_LAB` constant.

- **Annotation exports**: `.xlsx` files containing annotations (e.g., from Google Sheets). Files for multiple languages can be included, with each file name starting with the language name followed by an underscore (e.g., `KKG_film.xlsx` > `Bridge` Sheet).

- **Gloss Conversion Files** (if using `Gloss_Conversion`):
  Place the following files in the `Gloss_Conversion/LANGUAGE` folder:
  - `glosses.json`: JSON file containing gloss abbreviations.
  - `input_temp.txt`: Input template specifying recognized values (`ref`, `tx`, `mb`, `ge`, `fte`).
  - `ps.json`: JSON file mapping vocabulary `ps` labels to universal POS tags.
  - `vocab.db` or `vocab.xlsx`: Vocabulary database.
  - Additional scripts for segmentation and analysis (e.g., `word_segmentation.py`, `morphological_analysis.py`).

### 2. **Run the Annotation Script**  
Navigate to the project folder in the terminal and execute the following command:

```bash
bash annotate.sh
```

## Output

After running `annotate.sh`, the `output` folder will contain:

- **_output_file.conllu_**: Annotated sentences.
- **_joined_output.conllu_** (if applicable): Combined annotated sentences from the input files.

After running `glosses.sh`, the `temp` folder will contain glossed and annotated outputs.

---

## Data Splitting: `data_split.py`

The `data_split.py` script is used to split a `.conllu` file into training, development, and testing datasets based on predefined rules for each language. This script ensures that the data is organized into appropriate subsets for model training and evaluation.

### Usage

1. Ensure the `.conllu` file for the desired language is in the `conllu_files/` directory.
2. Run the script:
   
   ```bash
   python3 data_split.py
   ```
3. The script will prompt you to select a language. Based on the selection, it will apply the appropriate splitting rules.
4. The resulting files will be saved in the `data_split/` directory.

### Example Output

For the KKG language, the script might produce the following files:
- `naq_kdt-ud-train.conllu`
- `naq_kdt-ud-dev.conllu`
- `naq_kdt-ud-test.conllu`

The script will also print statistics like this:
```
train:
    grammar_Cairo: 100
    film_Bridge: 200
    Sum: 300

dev:
    grammar_BivalTyp: 50
    Sum: 50

test:
    film_Titanic: 150
    Sum: 150
```

### Notes

- The splitting rules are defined in the script for each language. To modify the rules, update the `split` dictionary in the corresponding language function (e.g., `KKG`, `Suansu`).
- Ensure the `data_split/` directory exists before running the script. If it does not exist, the script will create it automatically.
- The script relies on the `conllu_from_xlsx.py` module to determine the language.

---

## Data Analysis: `analyse.ipynb`

The `analyse.ipynb` notebook is used for analyzing the usage of Universal Dependencies (UD) features in annotated `.conllu` files. It provides insights into the distribution and usage of POS tags, morphological features (`FEATS`), and dependency relations (`DEPREL`) in the data.

### Key Features

- **POS Analysis**:
  - Lists all unique POS tags (`UPOSTAG`) used in the dataset.
  - Counts occurrences of specific POS tags and identifies lemmas associated with them.

- **Morphological Features (`FEATS`)**:
  - Extracts and lists all unique features and their values.
  - Analyzes the relationship between features and POS tags.
  - Identifies features used only once and their corresponding sentences.

- **Dependency Relations (`DEPREL`)**:
  - Counts occurrences of dependency relations.
  - Lists all unique dependency relations, including subtypes.

### Usage

1. Update the `LANGUAGE` and `FILE_NAME` variables in the notebook to specify the `.conllu` file to analyze.
2. Run the notebook in a Jupyter environment.
3. The notebook will process the `.conllu` file and display analysis results.

### Output

The notebook provides detailed statistics and visualizations for POS tags, features, and dependency relations, helping to understand the structure and composition of the annotated data.

---

## Notes

- The `annotate.sh` script is designed for macOS due to the use of the `pbcopy` command for copying output to the clipboard. If you're using another operating system, you may need to modify this step.
- Temporary files are automatically deleted at the beginning of the `annotate.sh` run and after successful use of it.
- You can customize training and running parameters in the `annotate.sh` script.
- For gloss conversion, ensure all required files are present in the `Gloss_Conversion/LANGUAGE` folder before running the `glosses.sh` script.

---

## Additional Documentation

- **Gloss Conversion**: Refer to the `README.md` file in the `Gloss_Conversion` directory for detailed instructions on using the `glosses.sh` script and related files.