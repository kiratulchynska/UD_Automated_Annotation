set -e

# Creating a temporal directory for the temporal files
echo "Deleting old temporal files"
rm -rf temp
mkdir -p temp
mkdir -p conllu_files
mkdir -p output

read -p "Language (Chintang, KKG, Ruuli, Suansu) or NONE if it is the only one in the inpute dir: " lang

echo "Preparing the training file"
source .venv/bin/activate
.venv/bin/python conllu_from_xlsx.py $lang

if [[ "$lang" == "Ruuli" || "$lang" == "Chintang" ]]; then
	read -p "Use gloss conversion algorithm? (Y/n): " input
	echo    # (optional) move to a new line
	input=${input:-y}
	if [[ $input =~ ^[Yy]$ ]]; then
		source glosses.sh "$lang"
		exit 0
	fi
fi


echo "Creating the input_file.txt"
python3 input_file.py $lang
echo "Preparing the input files"
python3 preparing_input.py $lang

read -p "Train the model? (Y/n): " input
echo    # (optional) move to a new line
input=${input:-y}
if [[ $input =~ ^[Yy]$ ]]
then
    # You can change parameters
	echo "Training the model"
	./udpipe/src/udpipe -train --tokenizer=epochs=100 temp/${lang}_model.output temp/${lang}_training_file.conllu
	cp temp/${lang}_model.output models/${lang}_model.output
fi

# You can change parameters
echo "Annotating"
input_num=$(ls temp | grep input_file_tx | wc -l)
for i in $(seq 1 $input_num)
do
    ./udpipe/src/udpipe --tokenize --tag --parse models/${lang}_model.output temp/input_file_tx-$i.txt > temp/output_file-$i.conllu
    if (( $i % 10 == 0 ))           # no need for brackets
    then
        echo "$i/$input_num"
    fi
done

echo "Preparing the output file"
python3 preparing_output.py
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

