set -e

lang="$1"

echo "Tokenizing and tagging glosses"
.venv/bin/python Gloss_Conversion/main.py	

read -p "Train the model for parsing? (Y/n): " input
echo    # (optional) move to a new line
input=${input:-y}
if [[ $input =~ ^[Yy]$ ]]
then
    # You can change parameters
	echo "Training the model"
	./udpipe/src/udpipe -train --tokenizer=none --tagger=none temp/${lang}_parse_model.output temp/${lang}_training_file.conllu
	cp temp/${lang}_parse_model.output models/${lang}_parse_model.output
fi

# You can change parameters
echo "Parsing"
./udpipe/src/udpipe --parse models/${lang}_parse_model.output temp/input_file.conllu > temp/output_file.conllu

echo "Preparing the output file"
python3 Gloss_Conversion/preparing_output.py
# read -p "The name of the file in the input directory to join (e.g., KKG_BridgeOfSpies.tsv) or NONE if it is not needed: " fname
python3 join_conllu.py $lang

echo "Deleting temporal files"
rm -rf temp

echo "Copying the contents of joined_output_file.conllu to clipboard"
if [[ -f output/joined_output_file.conllu && -s output/joined_output_file.conllu ]]; then
    cat output/joined_output_file.conllu | pbcopy
else
    echo "No joined_output_file.conllu. Skipping clipboard copy."
fi

echo "Done!"

