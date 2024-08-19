import pickle

class Sentence:
    """Storage for sentence"""
    def __init__(self, idx):
        self.idx = idx
        self.text = None 
        self.translation = None 
        self.checked = False 
        self.comment = ''
        self.tokens = []

class FailedToken(Exception):
    """Exception if token line doesn't contain 12 positions"""
    def __init__(self, num):
        self.num = num
    def __str__(self):
        return f'Token length is {self.num} instead of 12'
    
class Token:
    """Storage for token"""
    def __init__(self, line):
        tok = line.strip().split('\t')
        if len(tok) != 12:
            raise FailedToken(len(tok))
        self.idx, self.form, self.lemma, self.upos, self.xpos, self.feats, self.head, self.deprel, self.deps, self.misc, self.semslot, self.semclass = tok 
    
    def __str__(self):
        return '\t'.join([self.idx, self.form, self.lemma, self.upos, self.xpos, self.feats, self.head, self.deprel, self.deps, self.misc, self.semslot, self.semclass]) + '\n'

class Conllu:
    """Main class for handling conllu data"""
    def __init__(self, translang='en'):
        self.data = {} # sents: text, translation, token list
        self.ready = False
        self.len = 0
        self.current = 1 # current open sentence
        self.translang = translang
        self.hastranslations = False
    
    def read(self, path):
        """Reading file"""
        key = 0 # sentence number
        with open(path, 'r', encoding='utf8') as file:
            for line in file:
                if line.startswith('# sent_id = '):
                    idx = line.strip() # sentence id in conllu
                    self.len += 1
                    key += 1
                    self.data[key] = Sentence(idx)
                # sentence text
                if line.startswith('# text = ') and not self.data[key].text:
                    self.data[key].text = line.strip()[len('# text = '):]
                # sentence translation in text?
                elif line.startswith('# text'):
                    trans = line.strip().split(' = ')
                    if len(trans) == 2:
                        trans = trans[1]
                    elif len(trans) > 2:
                        self.hastranslations = True
                        trans = ' = '.join(trans[1])
                    self.data[key].translation = trans
                if line[0].isdigit():
                    try:
                        self.data[key].tokens.append(Token(line))
                    except FailedToken:
                        return 'BAD'
        if len(self.data) != 0:
            self.ready = True
        else:
            return 'EMPTY'
    
    def write_conllu(self, path):
        with open(path, 'w', encoding='utf8') as file:
            print('# global.columns = ID FORM LEMMA UPOS XPOS FEATS HEAD DEPREL DEPS MISC SEMSLOT SEMCLASS', file=file)
            for key, sent in self.data.items():
                print(sent.idx, file=file)
                if sent.text:
                    print(f"# text = {sent.text}", file=file)
                if sent.translation and self.hastranslations:
                    print(f'# text_{self.translang} = {sent.translation}', file=file)
                for token in sent.tokens:
                    file.write(token)
                print(file=file)

    def save(self, path):
        if path:
            pickle.dump((self.data, self.hastranslations, self.translang), open(path, 'wb'))

    def load(self, path):
        self.data, self.hastranslations, self.translang = pickle.load(open(path, 'rb'))
        if len(self.data) > 0:
            self.ready = True
            self.len = len(self.data)

    def __len__(self):
        return self.len
    