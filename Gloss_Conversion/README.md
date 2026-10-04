# Gloss Conversion Documentation

This document provides an overview of the `glosses.sh` script and the files in the `Gloss_Conversion` directory. The `Gloss_Conversion` module is designed to handle gloss conversion, word segmentation, and morphological analysis for linguistic data.

---

## Description

The `glosses.sh` script automates the gloss conversion process by utilizing the resources and scripts in the `Gloss_Conversion` directory. It processes linguistic data to generate glossed and annotated outputs.

---

## Prerequisites

- Python 3.8 or higher.
- Required Python libraries (see `requirements.txt`).
   - Libraries such as `json`, `sqlite3`, and `openpyxl` are used for gloss conversion and database handling.
- Ensure the `Gloss_Conversion` directory contains the necessary files (see below).

---

## Gloss Conversion Directory Structure

```
Gloss_Conversion/               # Gloss conversion module
├── LANGUAGE/                   # Folder for each language
│   ├── glosses.json            # JSON file with gloss abbreviations
│   ├── input_temp.txt          # Input template for recognized values
│   ├── ps.json                 # JSON mapping vocabulary `ps` labels to POS tags
│   ├── vocab.db                # Vocabulary database (SQLite)
│   ├── vocab.xlsx              # Vocabulary database (Excel format)
│   ├── word_segmentation.py    # Script for word segmentation
│   ├── morphological_analysis.py # Script for morphological analysis
│   ├── main.py                 # Main script for gloss conversion (tokenizing and tagging glosses)
├── tokenization.py             # Tokenizes the input text 
├── preparing_output.py         # Processes annotated output
├── README.md                   # Gloss conversion documentation
glosses.sh                      # Main script for gloss conversion
```

---

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/alenawitzlack/Event_packaging.git
   ```

2. Navigate to the `Gloss_Conversion` directory:
   ```bash
   cd PATH/Event_packaging/scripts/Automated_Annotating/Gloss_Conversion
   ```

3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r ../requirements.txt
   ```

---

## How to Run

1. **Prepare Input Files**  
   Place the following files into the `Gloss_Conversion/LANGUAGE` folder:

   - `glosses.json`: A JSON file containing gloss abbreviations. Each entry can include:
     - `"lemma"`: Corresponding lemma (e.g., `^??A/B` for disambiguation).
     - `"upostag"`: List of possible universal POS tags.
     - `"xpostag"`: Corresponding XPOSTAG.
     - `"feats"`: List of feature-value pairs (e.g., `[Feature, Value]`).

   - `input_temp.txt`: Input template specifying recognized values (`ref`, `tx`, `mb`, `ge`, `fte`).

   - `ps.json`: A JSON file mapping vocabulary `ps` labels to universal POS tags. Unspecified tags default to `X`.

   - `vocab.db` or `vocab.xlsx`: Vocabulary database containing word forms, glosses, and other linguistic information.

2. **Run the Gloss Conversion Script**  
   Navigate to the `Gloss_Conversion` directory in the terminal and execute the following command:

   ```bash
   bash glosses.sh LANGUAGE
   ```

   Replace `LANGUAGE` with the name of the folder containing the gloss conversion files (e.g., `Chintang`, `Ruuli`).

---

## Output

After running `glosses.sh`, the following outputs will be generated:

- **Glossed Output**: A file containing glossed sentences based on the input data and glosses.
- **Annotated Output**: A file with morphological analysis and word segmentation applied.

The output files will be saved in the `temp` in the parent directory.

---

## Parameters

You can customize the gloss conversion process by modifying the following files:

- `glosses.json`: Add or update gloss abbreviations, lemmas, POS tags, and features.
- `ps.json`: Update mappings of `ps` labels to universal POS tags.
- `input_temp.txt`: Adjust the input template to match the structure of your data.

---

## Notes

- Ensure that the `Gloss_Conversion/LANGUAGE` folder contains all required files before running the script.
- The `vocab.db` file is used for faster database queries, while `vocab.xlsx` is used for manual editing and updates.

---

## Example Workflow

1. Place the required files (`glosses.json`, `input_temp.txt`, `ps.json`, `vocab.db`) in the `Gloss_Conversion/LANGUAGE` folder.
2. Run the script:
   ```bash
   bash glosses.sh LANGUAGE
   ```
3. The glossed and annotated outputs will be saved in `temp` in the parent directory.
