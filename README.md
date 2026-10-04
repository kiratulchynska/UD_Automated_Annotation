# UD Automated Annotation

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MPL%202.0-green)](https://mozilla.org/MPL/2.0/)

## Description

This project automates text annotation using a UDPipe model and includes a `Gloss_Conversion` module for linguistic data processing. It supports glosses, word segmentation, and morphological analysis.

---

## Features

- Train and use UDPipe models for text annotation.
- Convert glosses to `.conllu` format.
- Split annotated data into training, development, and testing subsets.
- Analyze Universal Dependencies (POS tags, features, and dependency relations).

---

## Prerequisites

- **Python**: 3.8 or higher.
- **Dependencies**: Install from `requirements.txt`.
- **UDPipe**: Place the `udpipe` folder in the `Automated_Annotating` directory.

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/alenawitzlack/Event_packaging.git
   ```

2. Navigate to the project directory:
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

## Directory Structure

```
Automated_Annotating/
├── annotate.sh                # Main annotation script
├── glosses.sh                 # Gloss conversion script
├── input/                     # Input files
├── output/                    # Annotated output files
├── temp/                      # Temporary files
├── conllu_files/              # Intermediate .conllu files
├── Gloss_Conversion/          # Gloss conversion module
│   ├── LANGUAGE/              # Language-specific resources
│   ├── main.py                # Main gloss conversion script
│   ├── tokenization.py        # Tokenization script
│   ├── preparing_output.py    # Output processing script
│   ├── README.md              # Gloss conversion documentation
├── udpipe/                    # UDPipe binaries and models
├── requirements.txt           # Python dependencies
├── README.md                  # Main documentation
```

---

## How to Run

### 1. Prepare Input Files

Place the following files in the `input` folder:

- **Input sentences**: `.txt` files with `ref`, `tx`, `fte` lines (or `status` if required).
- **Annotation exports**: `.xlsx` files with language-specific names (e.g., `KKG_film.xlsx`).
- **Gloss Conversion Files**: Place gloss-related files in `Gloss_Conversion/LANGUAGE`.

### 2. Run Annotation Script

Run the main annotation script:
```bash
bash annotate.sh
```

### 3. Gloss Conversion (Optional)

Run the gloss conversion script:
```bash
bash glosses.sh
```

---

## Output

- **Annotation**: Results are saved in the `output` folder as `.conllu` files.
- **Gloss Conversion**: Outputs are saved in the `temp` folder.

---

## Additional Tools

### Data Splitting: `data_split.py`

Split `.conllu` files into training, development, and testing datasets:
```bash
python3 data_split.py
```

### Data Analysis: `analyse.ipynb`

Analyze annotated `.conllu` files for POS tags, features, and dependency relations. Open the notebook in Jupyter and follow the instructions.

---

## Notes

- The `annotate.sh` script is macOS-specific (uses `pbcopy`). Modify for other OS if needed.
- Temporary files are cleaned automatically during script execution.
- Customize parameters in `annotate.sh` for training and running.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

## Acknowledgments

- UDPipe: [https://ufal.mff.cuni.cz/udpipe](https://ufal.mff.cuni.cz/udpipe)
- Universal Dependencies: [https://universaldependencies.org/](https://universaldependencies.org/)
