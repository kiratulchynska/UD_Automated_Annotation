import re
import pandas as pd


def morphology(word_list: list, rpunct: str, vocab: pd.DataFrame, glosses: dict) -> list:
    """
    Annotate the word list with lemma, upostag, xpostag, and feats based on the vocabulary and glosses.
    Args:
        word_list (list): The list of words to annotate.
        rpunct (str): The regular expression for punctuation.
        vocab (pd.DataFrame): The vocabulary DataFrame.
        glosses (dict): The glosses dictionary.
    Returns:
        list: The annotated word list. Each word is a dictionary with keys "id", "form", "lemma", "upostag", "xpostag", "feats", and "nt" (notes).
    """

    # POS-specific analysis functions

    def analyse_adj(word: dict, root: dict, vocab: pd.DataFrame) -> dict:
        """
        Analyse the adjective based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        word["upostag"] = "ADJ"
        word["lemma"] = root["mb"]

        if len(vocab[(vocab["pos"] == "ADJ") & (vocab["Lemma"] == word["lemma"])]) == 0:
            word["nt"].append("Lemma not found in the vocab")

        if "NounClass" not in word["feats"]:
            word["feats"]["NounClass"] = ["Bantu??"]
            word["nt"].append("No noun class found in the glosses")

        accepted_feats = {"NounClass", "Referent"}
        if not set(word["feats"].keys()) <= accepted_feats:
            word["nt"].append(f"Unusual features found in the glosses: {", ".join(set(word["feats"].keys()) - accepted_feats)}")
        return word
    
    def analyse_adp(word: dict, root: dict, vocab: pd.DataFrame) -> dict:
        """
        Analyse the adposition based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        word["upostag"] = "ADP"
        word["lemma"] = root["mb"]

        # Locative wo, ku, mu, yo are not analysed here, since they are automatically glossed in info_from_glosses and have their own entries in the glosses dictionary, so they will not be analysed here as adpositions but as their own POS.
        
        if len(vocab[(vocab["pos"] == "ADP") & (vocab["Lemma"] == word["lemma"])]) == 0:
            word["nt"].append("Lemma not found in the vocab")

        if len(word["feats"]) > 0:
            word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys())}")
        
        return word

    def analyse_adv(word: dict, root: dict, vocab: pd.DataFrame) -> dict:
        """
        Analyse the adverb based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        word["upostag"] = "ADV"

        # COM na is not analysed here, since it is automatically glossed in info_from_glosses and has its own entry in the glosses dictionary, so it will not be analysed here as an adverb but as its own POS.
        if root["ge"] == "with" and root["mb"] in ["na", "n'"]:
            word = analyse_COM(word)

        # non-agreeing interrogatives
        elif root["mb"] in ["ayi", "di", "kamekai", "lwaki"]:
            word["lemma"] = word["form"]
            word["feats"]["PronType"] = ["Int"]
            if not word["feats"].keys() <= {"PronType"}:
                word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys() - {'PronType'})}")

        # agreeing content interrogatives
        elif root["mb"] == "tyai" and root["ge"] == "how":
            word["lemma"] = root["mb"]
            word["feats"]["PronType"] = ["Int"]
            if "NounClass" not in word["feats"] and "Number" not in word["feats"]:
                word["feats"]["NounClass"] = ["Bantu??"]
                word["feats"]["Person"] = ["??"]
                word["nt"].append("No subject agreement found")                    
            if "Person" not in word["feats"] and "NounClass" in word["feats"]:
                word["feats"]["Person"] = ["3"]
            if not set(word["feats"].keys()) <= {"PronType", "NounClass", "Number", "Person"}:
                word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys() - {'PronType', 'NounClass', 'Number', 'Person'})}")

        # ereere "only", nkai "only"
        elif root["ge"] == "only" and root["mb"] in ["ereere", "nkai"]:
            word["lemma"] = root["mb"]
            if "NounClass" not in word["feats"] and "Number" not in word["feats"]:
                word["feats"]["NounClass"] = ["Bantu??"]
                word["nt"].append("Expected agreement")
                if "Person" not in word["feats"]:
                    word["feats"]["Person"] = ["??"]
            if "Person" not in word["feats"] and "NounClass" in word["feats"]:
                word["feats"]["Person"] = ["3"]
            if not set(word["feats"].keys()) <= {"NounClass", "Number", "Person", "Referent"}:
                word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys() - {'NounClass', 'Number', 'Person', 'Referent'})}")
        
        elif root["ge"] in ["here", "there"] and re.search(r"(ni|o|di)$", root["mb"]):
            word = analyse_DEM(word)
        
        else:
            word["lemma"] = root["mb"]
            # if len(vocab[(vocab["pos"] == "ADV") & (vocab["Lemma"] == root["mb"])]) == 0:
            #     word["nt"].append("Lemma not found in the vocab")
            if not set(word["feats"].keys()) <= {"PronType", "NounClass", "Number", "Person", "Referent"}:
                word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys() - {"PronType", "NounClass", "Number", "Person", "Referent"})}")
        return word
    
    def analyse_conj(word: dict, root: dict) -> dict:
        """
        Analyse the conjunction based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        # COM is analysed separately

        word["lemma"] = root["mb"]

        if root["mb"] == "na":
            word["upostag"] = "CCONJ"
            word["xpostag"] = "COM"
        # ADV
        elif root["mb"] in ["ale", "aleni", "ekyaligiremu", "ekyazwiremu", "kaisite", "kaleni", "kataide",
                          "kyonkai", "luzwanyuma", "nolwekyo", "obwo", "songa"]:
            word["upostag"] = "ADV"
        # CCONJ
        elif root["mb"] in ["ate", "atete", "baitu", "era", "kanda", "naye", "oba", "wabula", "yete"]:
            word["upostag"] = "CCONJ"
        # SCONJ
        elif root["mb"] in ["anti", "banga", "bucanga", "bukya", "buli", "gonze", "kasita", "kataide",
                            "kuba", "kubanga", "kuliga", "kusinga", "kusinziira", "kuzwa", "kwica", "kwikya",
                            "kwiyaku", "lwakubba", "nambu", "nga", "ni", "singa", "wade"]:
            word["upostag"] = "SCONJ"
        else:
            word["upostag"] = "??CONJ"
            word["nt"].append("Unexpected lemma for conjunction")

        if len(word["feats"]) > 0:
            word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys())}")

        return word

    def analyse_intj(word: dict, root: dict) -> dict:
        """
        Analyse the interjection based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        word["lemma"] = root["mb"]
        word["upostag"] = "INTJ"
        if root["ge"] == "no":
            word["feats"]["Polarity"] = ["Neg"]
        if not set(word["feats"].keys()) <= {"Polarity"}:
            word["nt"].append(f"Unusual features found in the glosses: {', '.join(word['feats'].keys() - {'Polarity'})}")
        return word

    def analyse_noun(word: dict, root: dict, vocab: pd.DataFrame) -> dict:
        """
        Analyse the noun based on the glosses and vocabulary to find the lemma and noun class.
        Args:            
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and noun class in feats.
        """
        word["upostag"] = root["ps"]
        if word["upostag"] == "NOUN" and re.search(r"^\d+\.[A-Z][a-z]+", root["ge"]) and re.search(r"[a-z]?[A-Z][a-z]+", root["mb"]):
            word["upostag"] = "PROPN"

        if 'NounClass' in word["feats"]:
            word["nt"].append(f"Noun class is found not on the root of the noun")
            return word
        if word["lemma"]:
            word["nt"].append(f"Lemma found not on the root of the noun")
            return word
        if "." not in root["ge"]:
            word["lemma"] = "??" + root["mb"]
            word["feats"]["NounClass"] = ["Bantu??"]
            word["nt"].append(f"No noun class found in the gloss")
            return word
        
        nc = root["ge"].split(".")[0]
        if not re.search(r'^\d+$', nc):
            word["lemma"] = "??" + root["mb"]
            word["feats"]["NounClass"] = ["Bantu??"]
            word["nt"].append(f"Not appropriate noun class: {nc}")
            return word
        
        nc = int(nc)
        word["feats"]["NounClass"] = ["Bantu" + str(nc)]

        if nc % 2 == 1 or nc == 12:
            word["lemma"] = root["mb"]
        else:
            lemmas_sg = vocab[(vocab["pos"] == "NOUN") 
                                & (vocab["citation_plur"].str.endswith(f"){root['mb']}"))
                                & (vocab["NC"].str.endswith(f"/{nc}"))]["Lemma"].unique()
            lemmas_pl = vocab[(vocab["pos"] == "NOUN")
                                & (vocab["Lemma"] == root["mb"])
                                & (vocab["NC"] == str(nc))]["Lemma"].unique()
            if len(lemmas_sg) == 0 and len(lemmas_pl) == 0:
                word["lemma"] = "??" + root["mb"]
                word["nt"].append("Lemma not found in the vocab")
            elif len(lemmas_sg) == 1:
                word["lemma"] = lemmas_sg[0]
            elif len(lemmas_pl) == 1:
                word["lemma"] = lemmas_pl[0] 
            else:
                word["lemma"] = "??" + root["mb"]
                word["nt"].append(f"Multiple lemmas found in the vocab: {', '.join(lemmas_sg)}")

        # Possessive
        if "Person[psor]" in word["feats"]:
            word["feats"]["Person"] = word["feats"]["Person[psor]"]
            del word["feats"]["Person[psor]"]
            if "Number[psor]" in word["feats"]:
                word["feats"]["Number"] = word["feats"]["Number[psor]"]
                del word["feats"]["Number[psor]"]
            # NounClass to leave is is
            word["feats"]["Poss"] = ["Yes"]
        
        if re.search(r"^[A-Z]+$", word["lemma"]):
            word["feats"]["Abbr"] = ["Yes"]

        accept_feats = {"Abbr", "NounClass", "NounClass[psor]", "Number", "Person", "Poss", "Referent"}

        if not set(word["feats"].keys()) <= accept_feats:
           word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - accept_feats)}")
        return word
    
    def analyse_num(word: dict, root: dict) -> dict:
        word["lemma"] = root["mb"]
        word["upostag"] = "NUM"
        word["feats"]["NumType"] = ["Card"]
        if re.search(r"\d+", root["mb"]):
            word["feats"]["NumForm"] = ["Digit"]
        elif re.search(r"[IVXLCDM]+", root["mb"]):
            word["feats"]["NumForm"] = ["Roman"]
        else:
                word["feats"]["NumForm"] = ["Word"]
        if not set(word["feats"].keys()) <= {"NumType", "NumForm", "NounClass"}:
            word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - {"NumType", "NumForm", "NounClass"})}")
        return word

    def analyse_pron(word: dict, root: dict) -> dict:
        """
        Analyse the pronoun/determiner based on the glosses to find the lemma, POS, and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
        Returns:
            dict: The analysed word with updated lemma, POS, and features.
        """
        # Demonstratives are analysed separately
        if root:
            # DET
            # Universal
            if root["mb"] in ["buli", "ona"]:
                word["lemma"] = root["mb"]
                word["upostag"] = "??DET/PRON"
                word["nt"].append(f"Choose POS")
                word["feats"]["PronType"] = ["Tot"]
                if not set(word["feats"].keys()) <= {"PronType", "NounClass"}:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - {'PronType', 'NounClass'})}")
            # Interrogative
            elif root["mb"] in ["ingai", "mekai"]:
                word["lemma"] = root["mb"]
                word["upostag"] = "DET"
                word["feats"]["PronType"] = ["Int"]
                if "NounClass" not in word["feats"]:
                    word["feats"]["NounClass"] = ["Bantu??"]
                    word["nt"].append("No noun class found in the glosses")
                if not set(word["feats"].keys()) <= {"PronType", "NounClass"}:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - {'PronType', 'NounClass'})}")
            # PRON
            # Occasionally agreeing interrogative
            elif root["mb"] in ["naani", "ki", "kiki"]:
                word["lemma"] = root["mb"]
                word["upostag"] = "??PRON/DET"
                word["feats"]["PronType"] = ["Int"]
                word["nt"].append(f"Choose POS")
                if not set(word["feats"].keys()) <= {"PronType", "NounClass", "Number", "Person"}:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - {'PronType', 'NounClass', 'Number', 'Person'})}")
            
            # indefinite
            elif root["mb"] in ["ndi", "mwe"]:
                word["lemma"] = root["mb"]
                if root["mb"] == "mwe": # could br "one"
                    word["upostag"] = "??DET/PRON/NUM"
                    feats = {"NumType": "Card", "NumForm": "Word"}
                    if "NounClass" in word["feats"]:
                        feats["NounClass"] = word["feats"]["NounClass"][0]
                    if "Referent" in word["feats"]:
                        feats["Referent"] = word["feats"]["Referent"][0]
                    feats = "|".join([f"{key}={value}" for key, value in sorted(list(feats.items()))])
                    word["nt"].append(f"Choose POS. If NUM, use features: {feats}")
                else:
                    word["upostag"] = "??DET/PRON"
                    word["nt"].append(f"Choose POS")
                word["feats"]["PronType"] = ["Ind"]
                if "NounClass" not in word["feats"]:
                    word["feats"]["NounClass"] = ["Bantu??"]
                    word["nt"].append("No noun class found in the glosses")
                if not set(word["feats"].keys()) <= {"PronType", "NounClass", "Referent"}:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - {'PronType', 'NounClass', 'Referent'})}")
                
                    
            else:
                word["nt"].append(f"Unexpected gloss for pronoun/determiner")
        else:
            # PRON
            # Personal pronouns
            if re.search(r"^(AUG-)?\d+(sg|pl)?$", word["misc"]["Gloss"]):
                word["lemma"] = word["misc"]["MSeg"].split("-")[-1]
                word["upostag"] = "PRON"
                word["feats"]["PronType"] = ["Prs"]
                if "NounClass" in word["feats"]:
                    word["feats"]["Person"] = ["3"]
                if not set(word["feats"].keys()) <= {"PronType", "NounClass", "Number", "Person", "Referent"}:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - {'PronType', 'NounClass', 'Number', 'Person', 'Referent'})}")
            # Possessive
            elif re.search(r"-\d+(sg|pl)?(\.)?POSS$", word["misc"]["Gloss"]):
                if not re.search(r"^(AUG-)?\d+-\d+(sg|pl)?(\.)?POSS$", word["misc"]["Gloss"]):
                    word["nt"].append(f"Unexpected possessive gloss")
                word["lemma"] = word["misc"]["MSeg"].split("-")[-1]
                word["upostag"] = "PRON"
                word["xpostag"] = "ASSOC"
                word["feats"]["PronType"] = ["Prs"]
                word["feats"]["Person[psed]"] = ["3"]
                if "NounClass" not in word["feats"]:
                    word["feats"]["NounClass[psed]"] = ["Bantu??"]
                    word["nt"].append("No possessed noun class found in the glosses")
                else:
                    word["feats"]["NounClass[psed]"] = word["feats"]["NounClass"]
                    del word["feats"]["NounClass"]
                poss_feats = {"PronType", "NounClass[psor]", "Number[psor]", "Person[psor]", "NounClass[psed]", "Person[psed]", "Poss", "Referent"}
                if not set(word["feats"].keys()) <= poss_feats:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - poss_feats)}")
            elif "-ASSOC-" in word["misc"]["Gloss"]:
                word["lemma"] = "".join(word["misc"]["MSeg"].split("-")[-2:])
                # already tagged as PRON and has PronType and POS, however prefix and suffix is not glossed as pror and psee
                # 1-ASSOC-1
                if len(word["feats"]["NounClass"]) == 2:
                    word["feats"]["NounClass[psor]"] = [word["feats"]["NounClass"][1]]
                    word["feats"]["NounClass[psed]"] = [word["feats"]["NounClass"][0]]
                    del word["feats"]["NounClass"]
                # 1-ASSOC-1SG
                elif len(word["feats"]["NounClass"]) == 1:
                    word["feats"]["NounClass[psed]"] = word["feats"]["NounClass"]
                    del word["feats"]["NounClass"]
                # 1-ASSOC-1
                if "Person" not in word["feats"]:
                    word["feats"]["Person[psed]"] = ["3"]
                    word["feats"]["Person[psor]"] = ["3"]
                # 1-ASSOC-1SG
                elif len(word["feats"]["Person"]) == 1:
                    word["feats"]["Person[psor]"] = [word["feats"]["Person"][0]]
                    word["feats"]["Person[psed]"] = ["3"]
                    del word["feats"]["Person"]
                
                if "NounClass[psed]" not in word["feats"] or "Person[psed]" not in word["feats"]:
                    word["feats"]["NounClass[psed]"] = ["Bantu??"]
                    word["feats"]["Person[psed]"] = ["3"]
                    word["nt"].append("No possessed agreement found in the glosses")
                if ("NounClass[psor]" not in word["feats"] and "Number[psor]" not in word["feats"]) \
                    or "Person[psor]" not in word["feats"]:
                    word["feats"]["NounClass[psor]"] = ["Bantu??"]
                    word["feats"]["Person[psor]"] = ["??"]
                    word["nt"].append("No possessor agreement found in the glosses")

                assoc_feats = {"PronType", "NounClass[psor]", "Number[psor]", "Person[psor]", "NounClass[psed]", "Person[psed]", "Poss", "Referent"}
                if not set(word["feats"].keys()) <= assoc_feats:
                    word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - assoc_feats)}")

            else:
                word["nt"].append(f"Unexpected gloss for pronoun/determiner")

        return word
    
    def analyse_verb(word: dict, root: dict, vocab: pd.DataFrame) -> dict:
        """
        Analyse the verb based on the glosses and vocabulary to find the lemma and features.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        word["upostag"] = "VERB"

        if word["upostag"] == "VERB":
            # lemma
            if ".PFV" in root["ge"]:
                word["feats"]["Aspect"] = ["Perf"]
                word["misc"]["Gloss"] = re.sub(".PFV", ":PFV", word["misc"]["Gloss"])
                root["ge"] = re.sub(".PFV", ":PFV", root["ge"])
            if ".APPL" in root["ge"]:
                word["feats"]["Voice"] = ["Appl"]
                word["misc"]["Gloss"] = re.sub(".APPL", ":APPL", word["misc"]["Gloss"])
                root["ge"] = re.sub(".APPL", ":APPL", root["ge"])

            if not ":" in root["ge"]: # no PFV or APPL
                lemma = re.sub(r"([^a])$", r"\1a", root["mb"]) # adding FV if not present
                word["lemma"] = lemma
            elif ":PASS" in root["ge"]:
                word["lemma"] = "??" + root["mb"]
                word["nt"].append("Could not determine lemma")
            elif re.search(r":[^(PFV|APPL]+", root["ge"]):
                # unknown suffix
                word["lemma"] = "??" + root["mb"]
                word["nt"].append(f"Unknown suffix in the gloss: {root['ge']}")
            elif "PFV" in root["ge"] and "APPL" in root["ge"]:
                # supposedly no change to lemma, just added -e/iire
                lemma = re.sub(r"[ei]ire$", "a", root["mb"])
                if lemma in vocab[vocab["pos"] == "VERB"]["Lemma"].values:
                    word["lemma"] = lemma
                else:
                    word["lemma"] = "??" + lemma
                    word["nt"].append("Lemma not found in the vocab")
            else:
                # APPL -> PFV
                if root["mb"].endswith("a") or root["mb"].endswith("e"):
                    pfv_root = root["mb"][:-1] + "e"
                else:
                    pfv_root = root["mb"] + "e"
                word_lemmas = vocab[(vocab["pos"] == "VERB") 
                                    & (vocab["PFV"] == pfv_root)]["Lemma"].unique()
                # word_lemmas = list(word_lemmas)
                if len(word_lemmas) == 0:
                    word["lemma"] = "??" + root["mb"]
                    word["nt"].append("Lemma not found in the vocab")
                elif len(word_lemmas) > 1:
                    word["lemma"] = "??" + root["mb"]
                    word["nt"].append(f"Multiple lemmas found in the vocab: {', '.join(word_lemmas)}")
                else:
                    word["lemma"] =word_lemmas[0]
        elif word["upostag"] == "AUX":
            word["lemma"] = root["mb"]
        else:
            word["lemma"] = "??" + root["mb"]
            word["nt"].append(f"Unexpected POS for verb: {word['upostag']}")

        # features
        accepted_feats = {"Aspect", "Aspect[add]", "Mood", "NounClass", "NounClass[obj]", 
                          "Number", "Number[obj]", "Person", "Person[obj]", "Polarity",
                          "Referent", "Tense", "VerbForm", "Voice", "Voice[add]"}
        if not set(word["feats"].keys()) <= accepted_feats:
            word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - accepted_feats)}")
        
        if "VerbForm" not in word["feats"]:
            word["feats"]["VerbForm"] = ["Fin"]

        if len(word["feats"].get("Voice", [])) == 2: 
            if "Rfl" in word["feats"]["Voice"]:
                word["feats"]["Voice[add]"] = ["Rfl"]
                word["feats"]["Voice"] = [v for v in word["feats"]["Voice"] if v != "Rfl"][0]
                word["nt"].append("If Rfl is licenced by verb lemma, change it to be the main one")
            else:
                word["feats"]["Voice[add]"] = word["feats"]["Voice"][1]
                word["feats"]["Voice"] = word["feats"]["Voice"][0]
        elif len(word["feats"].get("Voice", [])) > 2:
            word["feats"]["Voice"] = ["-".join(word["feats"]["Voice"])]
            word["nt"].append("More than 2 voices found in the glosses, decide on how to handle this")

        if set(word["feats"].get("Aspect", [])) == {"Prog", "Hab"}:
            word["feats"]["Aspect"] = ["Prog"]
            word["feats"]["Aspect[add]"] = ["Hab"]

        # infinitive
        if "Inf" in word["feats"]["VerbForm"]:
            vnoun_feats = {"NounClass": "Bantu15",
                           "VerbForm": "Vnoun"}
            for k in word["feats"]:
                if k.startswith("Voice"):
                    vnoun_feats[k] = word["feats"][k][0]
            vnoun_feats_str = "|".join([f"{k}={v}" for k, v in vnoun_feats.items()])
            word["nt"].append("Could be verbal noun: tag: NOUN; feats: " + vnoun_feats_str)
            return word
        # imperative
        if re.search(r"^(\d+\w{0,2}\.?O-)?\w+([:-]APPL)?-FV$", word['misc']['Gloss']):
            word["feats"]["Mood"] = ["Imp"]
            word["feats"]["Number"] = ["Sing"]
            word["feats"]["Person"] = ["2"]
            # Maybe INF
            inf_feats = {"NounClass": word["feats"].get("NounClass[obj]", [""])[0],
                         "Number": word["feats"].get("Number[obj]", [""])[0],
                         "Person": word["feats"].get("Person[obj]", [""])[0],
                         "VerbForm": "Inf",
                         "Referent": word["feats"].get("Referent", [""])[0]}
            for k in word["feats"]:
                if k.startswith("Voice"):
                    inf_feats[k] = word["feats"][k][0]
            inf_feats = {k: v for k, v in inf_feats.items() if v and v != "??"}
            word["nt"].append(f"Could be infinitive, feats: {'|'.join([f'{k}={v}' for k, v in inf_feats.items()])}")
            return word
        # indicative
        if "Mood" not in word["feats"]:
            word["feats"]["Mood"] = ["Ind"]
            if "Tense" not in word["feats"]:
                word["feats"]["Tense"] = ["Pres"]
        if "Person" not in word["feats"]:
            word["feats"]["Person"] = ["??"]
            word["nt"].append("Subject not found in the glosses")

        if word["lemma"] in ["bba", "aba", "iza", "yaba"] \
            and word["feats"].get("Mood", ["Ind"])[0] == "Ind" and word["feats"].get("VerbForm", ["Fin"])[0] == "Fin" and word["feats"].get("Voice", ["Act"])[0] == "Act":
            aux_feats = {"Aspect": word["feats"].get("Aspect", [""])[0],
                         "NounClass": word["feats"].get("NounClass", [""])[0],
                         "Number": word["feats"].get("Number", [""])[0],
                         "Person": word["feats"].get("Person", [""])[0],
                         "Polarity": word["feats"].get("Polarity", [""])[0],
                         "Referent": word["feats"].get("Referent", [""])[0],
                         "Tense": word["feats"].get("Tense", [""])[0]}  
            aux_feats = {k: v for k, v in aux_feats.items() if v}
            aux_feats_str = "|".join([f"{k}={v}" for k, v in aux_feats.items()])
            word["nt"].append("Could be AUX, feats: " + aux_feats_str)

        return word   
    
    def analyse_others(word: dict, root: dict, vocab: pd.DataFrame) -> dict:
        """
        Analyse words tagged X. Mostly interrogatives.
        Args:
            word (dict): The word to analyse.
            root (dict): The morphological annotation of the root to analyse, with keys "mb", "ge", and "ps".
            vocab (pd.DataFrame): The vocabulary DataFrame.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        # interrogative adverbs
        if root["mb"] in ["ayi", "di", "kamekai", "lwaki", "tyai"]:
            word = analyse_adv(word, root, vocab)
        # interrogative determiner/pronouns
        if root["mb"] in ["ingai", "mekai", "naani", "ki", "kiki"]: 
            word = analyse_pron(word, root)
        
        return word
                
    def analyse_COM(word: dict) -> dict:
        """
        Analyse the COM word based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        word["lemma"] = "na"
        word["upostag"] = "??ADP/CCONJ"
        word["xpostag"] = "COM"
        word["nt"].append("Choose POS for COM")
        return word
    
    def analyse_AUX(word: dict) -> dict:
        """
        Analyse the AUX word based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
        Returns:
            dict: The analysed word with updated lemma and features.
        """
        mb_split = word["misc"]["MSeg"].split("-")
        ge_split = word["misc"]["Gloss"].split("-")
        ps_split = word["misc"]["POS"].split("-")
        root_i = min([i for i, p in enumerate(ps_split) if "AUX" in p])
        root = {"mb": mb_split[root_i], "ge": ge_split[root_i], "ps": ps_split[root_i]}

        # copulas
        # negative copula -> ADV
        if root["ge"] == "NEG.COP":
            word["lemma"] = word["form"]
            return word 
        # li, ta, ni
        elif root["mb"] in ["li", "ta", "ni", "taa"] and root["ge"] == "COP":
            word["lemma"] = "ta" if root["mb"] == "taa" else root["mb"]
            word["upostag"] = "AUX"
            if root["mb"] == "ni":
                word["feats"]["InfStruct"] = ["Foc"]
            if set(word["feats"].get("Aspect", [])) == {"Prog", "Hab"}:
                word["feats"]["Aspect"] = ["Prog"]
                word["feats"]["Aspect[add]"] = ["Hab"] 
            if "Tense" not in word["feats"]:
                word["feats"]["Tense"] = ["Pres"]
            if "NounClass" not in word["feats"] and "Number" not in word["feats"]:
                word["feats"]["NounClass"] = ["Bantu??"]
                word["feats"]["Person"] = ["??"]
                word["nt"].append("No subject agreement found")
            if "Person" not in word["feats"] and "NounClass" in word["feats"]:
                word["feats"]["Person"] = ["3"]
            cop_feats = {"Aspect", "Aspect[Add]" "InfStruct", "NounClass", "Number", 
                         "Person", "Polarity", "Tense", "Referent"}
            if not set(word["feats"].keys()) <= cop_feats:
                word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - cop_feats)}")
        # semi-copula bba
        elif (root["mb"] == "bba" or root["mb"] == "bb") and root["ge"] == "COP":
            word = analyse_verb(word, root, pd.DataFrame())

        #auxiliary verbs, e.g. iza
        else:
            word["lemma"] = root["mb"]
            if not word["lemma"][-1] == 'a':
                word["lemma"] += "a"
            if "Tense" not in word["feats"]:
                word["feats"]["Tense"] = ["Pres"]
            if set(word["feats"].get("Apsect", [])) == {"Prog", "Hab"}:
                word["feats"]["Aspect"] = ["Prog"]
                word["feats"]["Aspect[add]"] = ["Hab"]
            if "NounClass" not in word["feats"] and "Number" not in word["feats"]:
                word["feats"]["NounClass"] = ["Bantu??"]
                word["feats"]["Person"] = ["??"]
                word["nt"].append("No subject agreement found")
            if "Person" not in word["feats"] and "NounClass" in word["feats"]:
                word["feats"]["Person"] = ["3"]
            aux_feats = {"Aspect", "Aspect[add]" "NounClass", "Number", "Person", "Polarity", "Tense"}
            if not set(word["feats"].keys()) <= aux_feats:  
                word["nt"].append(f"Unusual features found in the glosses: {', '.join(set(word['feats'].keys()) - aux_feats)}")
        
        return word
    
    def analyse_DEM(word: dict) -> dict:
        """
        Analyse the DEM word based on the glosses to find the lemma and features.
        Args:
            word (dict): The word to analyse.
        Returns:
            dict: The analysed word with updated lemma and features.
        """

        word["feats"]["PronType"] = ["Dem"]
        # DET or ADV
        if word["upostag"] == "ADV":
            word["lemma"] = word["form"].lower()
            adv_feats = {"wani": {"NounClass": ["Bantu16"], "Deixis": ["Prox"]},
                         "ani": {"NounClass": ["Bantu16"], "Deixis": ["Prox"]},
                         "awo": {"NounClass": ["Bantu16"], "Deixis": ["Med"]},
                         "wadi": {"NounClass": ["Bantu16"], "Deixis": ["Dist"]},
                         "adi": {"NounClass": ["Bantu16"], "Deixis": ["Dist"]},
                         "kuni": {"NounClass": ["Bantu17"], "Deixis": ["Prox"]},
                         "okwo": {"NounClass": ["Bantu17"], "Deixis": ["Med"]},
                         "kudi": {"NounClass": ["Bantu17"], "Deixis": ["Dist"]},
                         "muni": {"NounClass": ["Bantu18"], "Deixis": ["Prox"]},
                         "omwo": {"NounClass": ["Bantu18"], "Deixis": ["Med"]},
                         "mudi": {"NounClass": ["Bantu18"], "Deixis": ["Dist"]},
                         "eni": {"NounClass": ["Bantu23"], "Deixis": ["Prox"]},
                         "eyo": {"NounClass": ["Bantu23"], "Deixis": ["Med"]},
                         "edi": {"NounClass": ["Bantu23"], "Deixis": ["Dist"]},
                         }
            if word["form"].lower() in adv_feats:
                for feat, value in adv_feats[word["form"].lower()].items():
                    word["feats"][feat] = value
            else: 
                word["nt"].append(f"Unexpected lemma for DEM adverb")
        elif word["feats"]["NounClass"] in [["Bantu16"], ["Bantu17"], ["Bantu18"], ["Bantu23"]]:
            word["upostag"] = "??ADV/DET"
            word["lemma"] = f"??{word['form']}/{word["lemma"]}"
            word["nt"].append("Choose POS")
        # DET or PRON
        else:
            word["upostag"] = "??DET/PRON"
            word["nt"].append("Choose POS, if pronoun, then add Person=3")

        # if not word["form"].endswith(word["lemma"]):
        #         word["lemma"] = "??" + word["lemma"]
        #         word["nt"].append("Lemma does not match the form of the word")

        return word

    # -----------------

    # general functions:


    def info_from_glosses(annotation_split: list) -> tuple[dict, list]:
        """
        Get the lemma, upostag, xpostag, and feats from the glosses dictionary based on the morphological annotation.
        Args:
            annotation_split (list): The list of morphological annotations for each component of the word. Each annotation is a dictionary with keys "mb", "ge", and "ps".
        Returns:
            tuple: A tuple containing a dictionary with the lemma, upostag, xpostag, and feats, and a list of glosses that need to be further analysed.
        """ 
        glosses_info = {"feats": {},
                "lemma": "",
                "upostag": "",
                "xpostag": ""}
        to_analyse = []

        ge_split = [morph["ge"] for morph in annotation_split]
        ge_split = [re.split(r"\:", ge) for ge in ge_split]
        ge_split = [item for sublist in ge_split for item in sublist]
        
        for i, ge in enumerate(ge_split):
            if ge in glosses:
                if "feats" in glosses[ge]:
                    for fv in glosses[ge]["feats"]:
                        feat, value = fv[0], fv[1]
                        if feat not in glosses_info["feats"]:
                            glosses_info["feats"][feat] = []
                        glosses_info["feats"][feat].append(value)
                for key in ["lemma", "upostag", "xpostag"]:
                    if key in glosses[ge]:
                        if glosses_info[key]:
                            glosses_info[key] += "-"
                        glosses_info[key] += glosses[ge][key]
            else:
                to_analyse.append(annotation_split[i])
        return glosses_info, to_analyse
                        

    def split_morph(annotation: dict) -> list:
        """
        Split the morphological annotation into its components based on the delimiters '-' and '='.
        Args:
            annotation (dict): The morphological annotation to split. It should have keys "mb", "ge", and "ps".
        Returns:
            list: A list of dictionaries, each containing the split morphological annotation for each component.
        """
        morph_split = {}
        for key in annotation:
            joined_morph = ''.join(annotation[key])
            if '~' in joined_morph:
                red_split = re.split(r'~', joined_morph)
                if red_split[1] not in red_split or len(red_split) != 2:
                    return []
                joined_morph = red_split[0]
            morph_split[key] = re.split(r"-", joined_morph)
            morph_split[key] = [m for m in morph_split[key] if m]
        if len(set(len(morph_split[key]) for key in morph_split)) != 1:
            return []
        
        keys = list(morph_split.keys())
        annotation_split = []
        for i in range(len(morph_split[keys[0]])):
            annotation_split.append({key: morph_split[key][i] for key in keys})
        return annotation_split

    def annotate_word(word: dict, vocab: pd.DataFrame, glosses: dict) -> dict:
        """
        Annotate the word with lemma, upostag, xpostag, and feats.
        Args:
            word (dict): The word to annotate.
            vocab (pd.DataFrame): The vocab DataFrame.
            glosses (dict): The glosses dictionary.
        Returns:
            dict: The annotated word.
        """
        word["lemma"] = ""
        word["upostag"] = ""
        word["xpostag"] = ""
        word["feats"] = {}
        word["nt"] = []

        annotation = {"mb": word["misc"]["MSeg"], 
                      "ge": word["misc"]["Gloss"],
                      "ps": word["misc"]["POS"]}
        
        # if "?" in annotation["ge"] or "?" in annotation["ps"]:
        #     word["nt"].append("Question in glosses, unable to annotate")
        
        annotation_split = split_morph(annotation)
        if not annotation_split:
            word["nt"].append("Could not split the morphological annotation, unable to annotate")
            return word

        glosses_info, to_analyse = info_from_glosses(annotation_split)
        word["lemma"] = glosses_info["lemma"]
        word["upostag"] = glosses_info["upostag"]
        word["xpostag"] = glosses_info["xpostag"]
        word["feats"] = glosses_info["feats"]
        
        # root
        if len(to_analyse) == 1:
            if to_analyse[0]['ps'] == 'ADJ':
                word = analyse_adj(word, to_analyse[0], vocab)
            elif to_analyse[0]['ps'] == 'ADP':
                word = analyse_adp(word, to_analyse[0], vocab)
            elif to_analyse[0]['ps'] == 'ADV':
                word = analyse_adv(word, to_analyse[0], vocab)
            elif to_analyse[0]['ps'] == 'CCONJ':
                word = analyse_conj(word, to_analyse[0])
            elif to_analyse[0]['ps'] == 'DET' or to_analyse[0]['ps'] == 'PRON':
                word = analyse_pron(word, to_analyse[0])
            elif to_analyse[0]['ps'] == 'INTJ':
                word = analyse_intj(word, to_analyse[0])
            elif to_analyse[0]['ps'] == 'NOUN' or to_analyse[0]['ps'] == 'PROPN':
                word = analyse_noun(word, to_analyse[0], vocab)
            elif to_analyse[0]['ps'] == 'NUM':
                word = analyse_num(word, to_analyse[0])
            elif 'VERB' in to_analyse[0]['ps']:
                word = analyse_verb(word, to_analyse[0], vocab)
            elif to_analyse[0]['ps'] == 'X':
                word = analyse_others(word, to_analyse[0], vocab)
            else:
                word["nt"].append(f"Unknown gloss for the root: {to_analyse}")
        elif len(to_analyse) == 0:
            if word["misc"]["Gloss"] == "COM":
                word = analyse_COM(word)
            elif "AUX" in word["misc"]["POS"]:
                word = analyse_AUX(word)
            elif re.search(r"\b\d+\.(PROX|MED|DIST)\b", word["misc"]["Gloss"]):
                word = analyse_DEM(word)
            elif re.search(r"\bPRON\b", word["misc"]["POS"]):
                word = analyse_pron(word, dict())
            elif re.search(r"^=?FOC", word["misc"]["Gloss"]):
                word["lemma"] = re.sub("=", "", word["misc"]["MSeg"])
            elif word["misc"]["Gloss"] == "INTERJ":
                word = analyse_intj(word, {"mb": word["misc"]["MSeg"], "ge": word["misc"]["Gloss"], "ps": word["misc"]["POS"]})
            elif word["misc"]["Gloss"] == "NEG":
                word["lemma"] = word["misc"]["MSeg"]
                word["upostag"] = "ADV"
            elif word["misc"]["Gloss"] in ["COMPL", "QUOT"]:
                word["lemma"] = word["misc"]["MSeg"]
            elif word["misc"]["MSeg"] == "te" and word["misc"]["Gloss"] == "FOC":
               word["feats"]["InfStruct"] = ["Top"]
               word["misc"]["Gloss"] = "TOP"
            

        elif len(to_analyse) > 1:
            print(f"Warning: Multiple components to analyse for the word {word['misc']['MSeg']} ({word['misc']["Gloss"]}, {word['misc']["POS"]}): {to_analyse}")
            word["nt"].append(f"Multiple components to analyse: {', '.join([morph["ge"] for morph in to_analyse])}")
        
        if '~' in word["misc"]["MSeg"]:
            word["feats"]["Red"] = ["Yes"]

        if word["nt"] and ('?' in word["misc"]["Gloss"] or '?' in word["misc"]["POS"] or 'TODO' in word["misc"]["Gloss"] or 'TODO' in word["misc"]["POS"]):
            word["nt"] = ["Question in glosses, unable to annotate"] + word["nt"]
        
        for key in ["lemma", "upostag"]:
            if not word[key]:
                word[key] = "??"
                word["nt"].append(f"{key} not found from the glosses")
        if not word["xpostag"]:
            word["xpostag"] = "_"
        
        del word["misc"]["POS"]
        for key in ["MSeg", "Gloss"]:
            word["misc"][key] = re.sub(r'^=|=$', '', word["misc"][key])

        return word
    
    
    def finalise_feats(word: dict) -> dict:
        """
        Finalize the feats: if there are multiple values for a feat, join them with '-' and add '??' at the beginning, and add a note about it. If there are no feats, set it to '_'.
        Args:
            word (dict): The word to finalize the feats for.
        Returns:
            dict: The word with finalized feats.
        """

        if "feats" not in word or not word["feats"]:
            word["feats"] = "_"
            return word
        
        final_feats = []
        all_keys = list(word["feats"].keys())
        
        for feat in word["feats"].keys():
            feat_name = feat
            if '[' in feat:
                base_feat = feat.split('[')[0]
                if len([f for f in all_keys if f.startswith(base_feat)]) == 1:
                    feat_name = base_feat
            if len(word["feats"][feat]) > 1:
                value = '??' + '-'.join(word["feats"][feat])
                word["nt"].append(f"Multiple values for the feature {feat}: {', '.join(word['feats'][feat])}")
            else:
                value = word["feats"][feat][0]
            final_feats.append(f"{feat_name}={value}")
        word["feats"] = '|'.join(sorted(final_feats))

        return word
    
    def update_word_pairs(word1: dict, word2: dict) -> tuple[dict, dict]:
        """
        Update the features of two words based on their agreement. If one word has a feature that the other does not, add it to the other word with value '??' and add a note about it. If both words have the same feature but different values, add '??' at the beginning of the value and add a note about it.
        Args:
            word1 (dict): The first word (could be None).
            word2 (dict): The second word.
        Returns:
            tuple: The updated words.
        """
        # Verbal noun
        if word2['feats'].get('VerbForm', [''])[0] == 'Inf' and  word2['xpostag'] == 'GEN':
            word2['feats']['VerbForm'] = ['Vnoun']
            word2['feats']['NounClass'] = ['Bantu15']
            word2['nt'].delete("Check previous word")
            return word1, word2

        return word1, word2
        
    # prev_word = None
    for i, word in enumerate(word_list):
        if '-' not in word["id"] and re.search(r"^" + rpunct + r"+$", re.sub(r"^\?\?", "", word["form"])):
            word["lemma"] = word["form"]
            word["upostag"] = "PUNCT"
        elif '-' not in word["id"]:
            word = annotate_word(word, vocab, glosses)
            # if prev_word and "Check previous word" in word["nt"]:
            #     prev_word, word = update_word_pairs(prev_word, word)
            #     if prev_word:
            #         word_list[prev_word_id] = prev_word
            # prev_word = word
            # prev_word_id = i
        word_list[i] = word

    word_list = [finalise_feats(word) for word in word_list]

    return word_list 