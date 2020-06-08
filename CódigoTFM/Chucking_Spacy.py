from StructuringClass import *
import spacy
from spacy.attrs import ORTH, LEMMA, NORM, POS
from spacy.tokenizer import Tokenizer
import re
import time
import sys

done = 'false'

PHI = {
    'NOMBRE_SUJETO_ASISTENCIA': 1,
    'EDAD_SUJETO_ASISTENCIA': 1,
    'SEXO_SUJETO_ASISTENCIA': 1,
    'FAMILIARES_SUJETO_ASISTENCIA': 1,
    'NOMBRE_PERSONAL_SANITARIO': 1,
    'FECHAS': 1,
    'PROFESION': 1,
    'CENTRO_SALUD': 1,
    'HOSPITAL': 1,
    'INSTITUCION': 1,
    'ID_TITULACION_PERSONAL_SANITARIO': 1,
    'ID_EMPLEO_PERSONAL_SANITARIO': 1,
    'IDENTIF_VEHICULOS_NRSERIE_PLACAS': 1,
    'IDENTIF_DISPOSITIVOS_NRSERIE': 1,
    'CALLE': 1,
    'TERRITORIO': 1,
    'PAIS': 1,
    'NUMERO_TELEFONO': 1,
    'NUMERO_FAX': 1,
    'CORREO_ELECTRONICO': 1,
    'ID_SUJETO_ASISTENCIA': 1,
    'ID_CONTACTO_ASISTENCIAL': 1,
    'NUMERO_BENEF_PLAN_SALUD': 1,
    'ID_ASEGURAMIENTO': 1,
    'URL_WEB': 1,
    'DIREC_PROT_INTERNET': 1,
    'OTRO_NUMERO_IDENTIF': 1,
    'OTROS_SUJETO_ASISTENCIA': 1
}


def read_folder_MEDDOCAN(folder, end_file=0, ini_file=0, extension=".txt"):
    # Diccionario vacio para introducir los documentos.
    informes = []
    listing = os.listdir(folder)
    if end_file == 0:
        end_file = len(listing)

    n = ini_file

    max_iter = 0
    search = True
    while search:
        while n < end_file and max_iter < len(listing):
            sys.stdout.write('\rLeyendo ' + folder + ' |')
            time.sleep(0.1)
            sys.stdout.write('\rLeyendo ' + folder + ' /')
            time.sleep(0.1)
            sys.stdout.write('\rLeyendo ' + folder + ' -')
            time.sleep(0.1)
            sys.stdout.write('\rLeyendo ' + folder + ' \\')
            time.sleep(0.1)

            if listing[max_iter].endswith(extension):
                url = folder + "/" + listing[max_iter]
                text = read_file(url)
                name = listing[max_iter].replace(extension, "")
                informes.append(DocumentMEDOCAN(name, text))
                n += 1
            max_iter += 1
        search = False
    print("Ultimo archivo leido: ", listing[max_iter - 1])
    print("Preparado(s)", len(informes), "documento(s)... \n")
    return informes


def read_file(file):
    try:
        with open(file, 'r', encoding="utf-8") as f:
            pag = f.read()
        f.close()
        return pag.lstrip()
    except UnicodeDecodeError:
        with open(file, 'r', encoding="latin-1") as f:
            pag = f.read()
        f.close()
        return pag.lstrip()


def adjustmentSpacy():
    # Modificar para que no separe Dr./Dra. en dos tokens: Dr./Dra y .
    nlp = spacy.load('es_core_news_sm')
    hyphen_re = re.compile(r'Dr\.\/Dra\.+')

    prefix_re = spacy.util.compile_prefix_regex(nlp.Defaults.prefixes)
    infix_re = spacy.util.compile_infix_regex(nlp.Defaults.infixes)
    suffix_re = spacy.util.compile_suffix_regex(nlp.Defaults.suffixes)
    nlp.tokenizer = Tokenizer(nlp.vocab, prefix_search=prefix_re.search,
                              infix_finditer=infix_re.finditer,
                              suffix_search=suffix_re.search, token_match=hyphen_re.match)

    # Añadiendo lemas norma y tag al token Dr./Dra.
    nlp.tokenizer.add_special_case('Dr./Dra.', [{ORTH: 'Dr./Dra.', LEMMA: 'Doctor', NORM: "doctor", POS: "PROPN"}])

    return nlp


def is_Ini(doc, token, firstword):
    Ini = False
    if token.i == 0:
        Ini = True
    elif token.idx == firstword:
        Ini = True
    elif token.pos_ == 'PUNCT' and token.text not in '.':
        # No admitimos que un signo sea fin de frase, nos interesa las palabras
        Ini = False
    else:
        token_previo = doc[token.i - 1]
        if token_previo.pos_ == 'SPACE':
            if '\n' in token_previo.text:
                Ini = True
            else:  # Si no, puede que el token sea un espacio
                Ini = is_Ini(doc, doc[token_previo.i], firstword)
        if token_previo.pos_ == 'PUNCT':
            if token_previo.text in '.':
                Ini = True
            else:  # Puede que sea un paréntesis o un guion.
                Ini = is_Ini(doc, doc[token_previo.i], firstword)

    return Ini


def is_Fin(doc, token, lastword):
    Fin = False
    if token.i >= doc[-1].i:
        Fin = True
    elif token.idx == lastword:
        Fin = True
    else:
        token_post = doc[token.i + 1]
        if token_post.pos_ == 'SPACE':
            if '\n' in token_post.text:  # Puede que no termine en punto la frase (ejemplo de la "Anamnesis")
                Fin = True
            else:
                Fin = is_Fin(doc, doc[token_post.i], lastword)
        if token_post.pos_ == 'PUNCT':
            if token_post.text == '.':
                Fin = True
            else:  # Puede que sea un paréntesis o dos puntos seguido de un salto linea.
                Fin = is_Fin(doc, doc[token_post.i], lastword)
    return Fin


def Separate_sents(tags):
    sents = [[]]
    for word in tags:
        if 'FDO=True' not in word:
            sents[-1].append(word)
        else:
            if len(sents[-1]) > 0:
                sents[-1].append(word)
                sents.append([])
    try:
        sents.remove([])

    except:
        pass

    return sents


class DocumentMEDOCAN(object):
    '''
    Esta clase recibe un texto y el nombre del texto. La clase genera los atributos
        1. Nombre del documento.
        2. Texto instanciado a su vez de la clase nlp que usa la librería de spaCy.
        3. Si se le pasa el documento de anotaciones de PHI, genera un vector que los contiene junto con las posiciones
            donde se encuentran.
        4. Cabecera del documento.
        5. Pie del documento.
        6. Cuerpo del documento.
    Además, contiene algunos métodos para extraer características de las palabras que se encuentran en el cuerpo
    del documento.
    '''
    def __init__(self, name, text, categories=None, label=None):
        self.name = name
        self.text = text
        self.categories = categories
        self.label = label
        self.nlp = spacy.load('es_core_news_sm')

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, text):
        if not isinstance(text, str):
            raise ValueError("’text’ debe ser un string")
        self._text = text

    @property
    def textprocess(self):
        return self.nlp(self.text)

    def AddCategories(self, categories):
        self.categories = categories

    @property
    def body(self):
        ini_sent = self.text.find("Médico:")

        if ini_sent == -1:
            # Si no encuentra nada que coja desde el ppio
            ini = 0
        else:
            ini = self.text.find("\n", ini_sent) + 1
        fin = self.text.find("Remitido por:")
        if fin == -1:
            fin = self.text.find("Responsable clínico:")
        if fin == -1:
            # Si no encuentra ninguna de las dos opciones que coja all
            fin = len(self.text)
        cuerpo = self.text[ini:fin]
        b = (cuerpo.lstrip(), ini, fin)
        return b

    @property
    def cabeza(self):
        fin_sent = self.text.find("Médico:")

        if fin_sent == -1:
            fin = 0
        else:
            # Si no encuentra nada que no coja nada porque esta en el cuerpo -> fin = 0 sino:
            fin = self.text.find("\n", fin_sent)
        cabeza = self.text[:fin]
        c = (cabeza.lstrip(), 0, fin)
        return c

    @property
    def pie(self):
        ini_sent = self.text.find("Remitido por:")
        ini = ini_sent
        if ini_sent == -1:
            ini = self.text.find("Responsable clínico:")
        if ini == -1:
            # Si no encuentra ninguna de las dos opciones que no coja nada porque estara en el cuerpo
            ini = len(self.text)
        cuerpo = self.text[ini:]
        p = (cuerpo.lstrip(), ini, len(self.text))
        return p

    def RecoverIndexsToAnnotationsFile(self, folder, ini=0, len=0):
        if ini == 0 and len == 0:
            ini = self.body[1]
            len = self.body[2]

        namefile = folder + "/" + self.name + ".ann"
        textfile = read_file(namefile).rstrip()
        lines = textfile.split("\n")
        indices = set()
        categorias = {}
        for line in lines:
            columns = line.split()
            if int(columns[2]) > ini and int(columns[3]) < len:
                rango_indices = range(int(columns[2]), int(columns[3]))
                indices.update(rango_indices)
                categorias.update({ind: columns[1] for ind in rango_indices})
                # categorias.append((' '.join(columns[4:]), columns[1]))

        self.AddCategories(categorias)
        return indices

    def Extract_Indexs(self):
        indices = set()
        print('categorias: ', self.categories)
        for key in self.categories:
            indices.add(key)
        return indices

    def IsLabel(self, token, indexs):
        islabel = 0
        if token.idx in indexs:
            if self.label is None:
                islabel = 1
            elif self.categories[token.idx] == self.label:
                islabel = self.label
        return islabel

    def tagTokenPrevio(self, token, indexs):
        doc = self.textprocess
        tag = None
        if not is_Ini(doc, token, self.body[1]):
            token_previo = doc[token.i - 1]
            if token_previo.pos_ in ['SPACE']:  # Antes ['SPACE', 'PUNT']
                tag = self.tagTokenPrevio(token_previo, indexs)
            else:
                islabel = self.IsLabel(token_previo, indexs)
                tag = {
                    'idx': token_previo.idx,
                    'word.lower': token_previo.text.lower(),
                    'postag': token_previo.pos_,
                    'dependence': token_previo.dep_,
                    'word.isalpha': token_previo.is_alpha,
                    'word.isupper': token_previo.is_upper,
                    'word.istitle': token_previo.is_title,
                }
        return tag

    def tagTokenPost(self, token, indexs):
        doc = self.textprocess
        tag = None
        if not is_Fin(doc, token, self.body[2] - 1):
            token_post = doc[token.i + 1]
            if token_post.pos_ in ['SPACE']:  # ['PUNT']
                tag = self.tagTokenPost(token_post, indexs)
            else:
                islabel = self.IsLabel(token_post, indexs)
                tag = {
                    'idx': token_post.idx,
                    'word.lower': token_post.text.lower(),
                    'postag': token_post.pos_,
                    'dependence': token_post.dep_,
                    'word.isalpha': token_post.is_alpha,
                    'word.isupper': token_post.is_upper,
                    'word.istitle': token_post.is_title,
                }
        return tag

    def Features(self, label=None, body=True):
        doc = self.textprocess
        tags = []
        indexs = self.Extract_Indexs()
        termina = False
        for token in doc:
            if body is True:
                inicio_text = self.body[1]
                fin_text = self.body[2]
            else:
                inicio_text = self.body[2] + 1
                fin_text = len(self.text)
            if inicio_text <= token.idx < fin_text:
                empieza = is_Ini(doc, token, inicio_text)
                termina_previo = termina
                if not empieza and termina_previo:
                    empieza = True
                termina = is_Fin(doc, token, fin_text - 1)
                if not (empieza and (
                        token.pos_ == 'SPACE' or token.text.lower().replace(u'\ufeff', '') == '.')) or token.idx == \
                        self.body[1]:
                    # Inicializamos lista a None. Debemos diferenciar entre None = No se ha encontrado info; de 0 = False
                    # [info sensible, text, lema, pos, dep, alpha, upper, tittle, inicio, fin,
                    # (anterior, pos, dep, sensible), (posterior, pos, dep, sensible), entity]
                    # Aniadimos labels:
                    tag = []
                    tagprev = self.tagTokenPrevio(token, indexs)
                    tagpost = self.tagTokenPost(token, indexs)
                    islabel = self.IsLabel(token, indexs)
                    tag.extend([
                        'idx=%s' % token.idx,
                        'word.lower=' + token.text.lower().replace(u'\ufeff', ''),
                        'lemma=' + token.lemma_.replace(u'\ufeff', ''),
                        'postag=' + token.pos_,
                        'dependence=' + token.dep_,
                        'word.isalpha=%s' % token.is_alpha,
                        'word.isupper=%s' % token.is_upper,
                        'word.istitle=%s' % token.is_title,
                        'word.isentity=%s' % False if token.ent_type_ == '' else 'word.isentity=%s' % True
                    ])

                    if empieza:
                        # Indicamos que es el "Comiendo De una Oracion"
                        tag.extend(['CDO=True'])
                    else:
                        tag.extend([
                            '-1:idx=%s' % tagprev['idx'],
                            u'-1:word.lower=' + tagprev['word.lower'].replace(u'\ufeff', ''),
                            '-1:postag=' + tagprev['postag'],
                            '-1:dependence=' + tagprev['dependence'],
                            # '-1:word.isalpha=%s' % tagprev['word.isalpha'],
                            # '-1:word.isupper=%s' % tagprev['word.isupper'],
                            # '-1:word.istitle=%s' % tagprev['word.istittle'],
                        ])

                    if termina:
                        # Indicamos que es el "Final De una Oracion"
                        tag.extend(['FDO=True'])
                    else:
                        tag.extend([
                            '+1:idx=%s' % tagpost['idx'],
                            u'+1:word.lower=' + tagpost['word.lower'].replace(u'\ufeff', ''),
                            '+1:postag=' + tagpost['postag'],
                            '+1:dependence=' + tagpost['dependence'],
                            # '+1:word.isalpha=%s' % tagpost['word.isalpha'],
                            # '+1:word.isupper=%s' % tagpost['word.isupper'],
                            # '+1:word.istitle=%s' % tagpost['word.istitle'],
                        ])
                    tags.append(tag)
        return tags

    def ProcessCabeza(self):
        text = self.cabeza[0]
        sents = self.cabeza[0].split("\n")
        dicc = {}
        ini = 0
        fin = 0
        count_len = 0
        for sent in sents:
            if sent != "\n" and sent != "":
                sent.replace("\n", "")
                info = sent.split(":")
                if len(info) == 1:
                    continue
                elif len(info) == 2:
                    word = info[1][:-1].lstrip().rstrip()
                    ini = text.find(word) + count_len
                    fin = ini + len(word)
                    text = text[fin - count_len:]
                    count_len = fin
                    dicc[ini] = [info[0].lstrip().rstrip(), word]  # Para quitarle el punto final
                elif len(info) > 2:
                    separar = info[1].split()
                    siguiente = separar[-1]
                    juntar = " ".join(separar[:-1])
                    word = juntar.lstrip().rstrip()
                    ini = text.find(word) + count_len
                    fin = ini + len(word)
                    text = text[fin - count_len:]
                    count_len = fin
                    dicc[ini] = [info[0].lstrip().rstrip(), word]
                    if "." in info[2]:
                        word = info[2][:-1].lstrip().rstrip()
                        ini = text.find(word) + count_len
                        fin = ini + len(word)
                        text = text[fin - count_len:]
                        count_len = fin
                        dicc[ini] = [siguiente.lstrip().rstrip(), word]  # Para quitarle el punto final
                    else:
                        word = info[2].lstrip().rstrip()
                        ini = text.find(word) + count_len
                        fin = ini + len(word)
                        text = text[fin - count_len:]
                        count_len = fin
                        dicc[ini] = [siguiente.lstrip().rstrip(), word]
                    if len(info) > 4:
                        word = info[4][:-1].lstrip().rstrip()
                        ini = text.find(word) + count_len
                        fin = ini + len(word)
                        text = text[fin - count_len:]
                        count_len = fin
                        dicc[ini] = [info[3].lstrip().rstrip(), word]

        return {self.name: dicc}


if __name__ == '__main__':
    nlp = adjustmentSpacy()
