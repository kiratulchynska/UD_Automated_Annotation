import re

def segmentation(sent: dict, token_list: list, rpunct: str, transf: dict) -> list:
        """
        Splits tokens with clitics into separate words and assigns them IDs.
        Args:
            sent (dict): A dictionary containing the sentence information.
            token_list (list): A list of dictionaries representing the tokens in the sentence.
            rpunct (str): A regular expression pattern for punctuation.
            transf (dict): A dictionary for part of speech transformation.
        Returns:
            list: A list of dictionaries representing the segmented words with keys: form, id, misc, nt.
        """

        ps_cur_split = re.split(r"-|=|~|:|\s", sent["ps"])
        ps_cur_split = [transf.get(p, p) for p in ps_cur_split]
        splits = [a for a in sent["ps"] if re.search(r"-|=|~|:|\s", a)]
        ps = ps_cur_split.pop(0)
        for split in splits:
            ps += split + ps_cur_split.pop(0)   

        mb = re.split(r"\s+", sent["mb"])
        ge = re.split(r"\s+", sent["ge"])
        ps = re.split(r"\s+", ps)



        if len(set([len(mb), len(ge), len(ps)])) != 1:
            return [f"# Error: Number of morphemes in mb ({len(mb)}), ge ({len(ge)}), and ps ({len(ps)}) do not match in sentence {sent["ref"]}."]
    
        
        nonpunct_tokens = [t for t in token_list if not re.search(r"^" + rpunct + r"+$", t["form"])]
        mb_joined = []
        ge_joined = []
        ps_joined = []
        for morph, gloss, pos in zip(mb, ge, ps):
            i = len(ge_joined)
            if i > 0 and len(ge_joined[-1]) > 0 and ge_joined[-1][-1].endswith('='): # previous is proclitic
                mb_joined[-1].append(morph)
                ge_joined[-1].append(gloss)
                ps_joined[-1].append(pos)
            elif i > 0 and len(ge_joined[-1]) == 1 and len(nonpunct_tokens) >= i \
                and re.search(fr"^{re.escape(mb_joined[-1][0][:-1])}['’]", nonpunct_tokens[i-1]["form"].lower()): # previous is n' or ky' proclitic
                mb_joined[-1].append(morph)
                ge_joined[-1].append(gloss)
                ps_joined[-1].append(pos)
            # elif i > 0 and len(ge_joined[-1]) == 1 and len(nonpunct_tokens) >= i \
            #     and any([nonpunct_tokens[i-1]["form"].startswith(m1 + m2) for m1 in [mb_joined[-1][0], re.sub(r"^(ni|na)$", "n", mb_joined[-1][0])] for m2 in [re.sub(r"-$", "", morph), re.sub(r"^a-$", "y", morph)]]) \
            #     and re.search(r'^(\d+\.(GEN|REL)|when|if|COM)$', ge_joined[-1][0]): # e.g. owairai -> owa + irai
            #     mb_joined[-1].append(morph)
            #     ge_joined[-1].append(gloss)
            #     ps_joined[-1].append(pos)
            elif len(ge_joined) > 0 and len(ge_joined[-1]) > 0 and ge_joined[-1][-1].endswith('-'): # previous is prefix
                mb_joined[-1][-1] = mb_joined[-1][-1] + morph
                ge_joined[-1][-1] = ge_joined[-1][-1] + gloss
                ps_joined[-1][-1] = ps_joined[-1][-1] + pos
            elif not re.search(r'^[-~=]', morph): # new token
                mb_joined.append([morph])
                ge_joined.append([gloss])
                ps_joined.append([pos])
            elif morph.startswith('='): # enclitic
                mb_joined[-1].append(morph)
                ge_joined[-1].append(gloss)
                ps_joined[-1].append(pos)
            else:
                mb_joined[-1][-1] = mb_joined[-1][-1] + morph
                ge_joined[-1][-1] = ge_joined[-1][-1] + gloss
                ps_joined[-1][-1] = ps_joined[-1][-1] + pos

        mb_joined = [t for t in mb_joined if t]
        ge_joined = [t for t in ge_joined if t]
        ps_joined = [t for t in ps_joined if t]

        if len(mb_joined) != len(nonpunct_tokens):
            return [f"# Error: Number of words in tx ({len(nonpunct_tokens)}) and mb ({len(mb_joined)}) do not match in sentence {sent["ref"]}."]
        
        word_list = []
        cur_id = 1
        for token in token_list:
            if re.search(r"^" + rpunct + r"+$", token["form"]): # punctuation
                cur_word = token
                cur_word["id"] = str(cur_id)
                cur_word["nt"] = []
                word_list.append(cur_word)
                cur_id += 1
            else:
                mb_cur = mb_joined.pop(0)
                ge_cur = ge_joined.pop(0)
                ps_cur = ps_joined.pop(0)

                if len(mb_cur) == 1: # no clitics
                    cur_word = token
                    cur_word["id"] = str(cur_id)
                    cur_word["misc"]["MSeg"] = mb_cur[0]
                    cur_word["misc"]["Gloss"] = ge_cur[0]
                    cur_word["misc"]["POS"] = ps_cur[0]
                    cur_word["nt"] = []
                    word_list.append(cur_word)
                    cur_id += 1
                else:
                    form = token["form"]
                    proclitics = []
                    for i, mb_word in enumerate(mb_cur): # proclitics
                        if i == 0 and re.search(r"^\w+['’]", form) and mb_word.startswith(re.split(r"['’]", form)[0].lower()):
                                proclitics.append(re.search(r"^\w+['’]", form).group(0))
                                form = form[len(re.split(r"['’]", form)[0])+1:]
                        elif mb_word.endswith('='):
                            if form.startswith(mb_word[:-1]):
                                proclitics.append(mb_word[:-1])
                                form = form[len(mb_word)-1:]
                            else:
                                return [f"# Error: Cannot align clitic '{mb_word}' with form in sentence {sent["ref"]}."]
                        elif token["form"].startswith(mb_word) and "GEN" in ge_cur[i]:
                            proclitics.append(mb_word)
                            form = form[len(mb_word):]
                    enclitics = []
                    for mb_word in reversed(mb_cur): # enclitics
                        if mb_word.startswith('='):
                            if form.endswith(mb_word[1:]):
                                enclitics.insert(0, mb_word[1:])
                                form = form[:-len(mb_word)+1]
                            else:
                                return [f"# Error: Cannot align clitic '{mb_word}' with form in sentence {sent["ref"]}."]
                            
                    if form == "":
                        form_split = proclitics + enclitics
                    else:
                        form_split = proclitics + [form] + enclitics
                    
                    if len(form_split) != len(mb_cur):
                        return [f"# Error: Number of segmented forms ({len(form_split)}) does not match number of morphemes ({len(mb_cur)}) in {mb_cur}."]
                    
                    cur_word = token
                    cur_word["id"] = f"{cur_id}-{cur_id+len(form_split)-1}"
                    cur_word["nt"] = []
                    word_list.append(cur_word)

                    for i in range(len(form_split)):
                        cur_word = {"form": form_split[i],
                                    "id": str(cur_id),
                                    "misc": {"MSeg": mb_cur[i],
                                             "Gloss": ge_cur[i],
                                             "POS": ps_cur[i]},
                                    "nt": []}
                        word_list.append(cur_word)
                        cur_id += 1
        return word_list