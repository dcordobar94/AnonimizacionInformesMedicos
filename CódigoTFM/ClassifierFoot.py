import re
from SelectPHI import *
from Chucking_Spacy import *


def findall(word, text):
    i = text.find(word)
    pos = [i]
    while i != -1:
        i = text.find(word, i + 1)
        if i != -1:
            pos.append(i)

    return pos

def CargaMunicipios():
    m = open('Tabla_Municipios 15 03 2019.txt', 'r')
    contents = m.read()
    municipios = eval(contents.lower())
    return municipios


def UpdateCountFoot(categoria, conteolabels):
    if categoria:
        if categoria in conteolabels:
            conteolabels[categoria] += 1
        else:
            conteolabels[categoria] = 1


def ExtractLabel(folderAnn, docname):
    categorias = {}
    indices = set()
    if docname not in DOCLEIDOS:
        DOCLEIDOS.update(docname)
        try:
            f = ReadFile(folderAnn + "/" + docname + ".ann").rstrip()
            lines = f.split("\n")
            for line in lines:
                columns = line.split()
                rango_indices = list(range(int(columns[2]), int(columns[3])))
                type_cat = TransformCategoria(columns[1])
                if type_cat != "I":
                    indxLabel = {ind: [type_cat, rango_indices] for ind in rango_indices}
                    categorias.update(indxLabel)
                    indices.update(rango_indices)

        except Exception as e:
            print("No pudo leerse el fichero: ", docname, ". \n\tTipo error: ", e, ". Fichero ignorado.")
            pass

    return indices, categorias


def extract_label(word):
    label = word[0].replace("label=", "")
    return label


def Extract_Feautures_Body_ToFoot(words, labels):
    PHIConfianzaBody = []
    comienzo = False
    for word, label in zip(words, labels):
        if type(word) == list and label in {'C-HOSP', 'C-INST'}:
            comienzo = True
            wordlower = ""
            for caract in word:
                if "word.lower=" in caract:
                    wordlower = caract[11:]
                    break
            PHIConfianzaBody.append([wordlower, label])
        elif label in {'D-HOSP', 'D-INST'} and comienzo and len(PHIConfianzaBody) > 0:
            wordlower = ""
            for caract in word:
                if "word.lower=" in caract:
                    wordlower = caract[11:]
                    break
            PHIConfianzaBody[-1][0] = PHIConfianzaBody[-1][0] + " " + wordlower
        else:
            if len(PHIConfianzaBody) > 0:
                if len(PHIConfianzaBody[-1][0]) < 4:
                    PHIConfianzaBody.pop()
            comienzo = False

    return PHIConfianzaBody


def Extract_Feautures_Head_ToFoot(words, labels):
    PHIConfianzaHead = []
    comienzo = False
    labelcomienzo = "I"
    for word, label in zip(words, labels):
        if label in {'C-HOSP', 'C-INST', 'C-CALLE', 'C-FECH', 'C-IDASEG', 'C-NOMP', 'C-NOMS', 'C-TER', 'C-PAIS',
                     'C-IDASEG', 'C-IDCONT', 'C-IDSUJ'} and comienzo == False:
            comienzo = True
            labelcomienzo = label[2:]
            wordlower = word.lower()
            PHIConfianzaHead.append([wordlower, label])
        elif label != "I" and comienzo and len(PHIConfianzaHead) > 0:
            wordlower = word.lower()
            if label[2:] == labelcomienzo and label[2:] != 'TER':
                PHIConfianzaHead[-1][0] = PHIConfianzaHead[-1][0] + " " + wordlower
            elif label in {'C-HOSP', 'C-INST', 'C-CALLE', 'C-FECH', 'C-IDASEG', 'C-NOMP', 'C-NOMS', 'C-TER', 'C-PAIS',
                           'C-IDASEG', 'C-IDCONT', 'C-IDSUJ'}:
                labelcomienzo = label[2:]
                PHIConfianzaHead.append([wordlower, label])
        else:
            if len(PHIConfianzaHead) > 0:
                if len(PHIConfianzaHead[-1][0]) < 4:
                    PHIConfianzaHead.pop()
            comienzo = False

    return PHIConfianzaHead


def TransformWord_Foot(token, ini, information, CDI=True):
    word = [token.text, "I"]
    try:
        idx_word = token.idx + ini
        if idx_word in information[0]:  # informacion = ({ind1, ind2,...},{ind1:[cat,[ind1,ind2,...]], ind2:...})
            word = [token.text, information[1][idx_word][0]]
            information = (information[0], UpdateInformacion(information[1], idx_word))

    except Exception as e:
        print("Error al obtener el índice y etiquetar el vector ", token.text, " Error tipo: ", e)
        pass

    return word


def ExtractAnontationFoot(doc):
    informacion = ExtractLabel("MEDDOCAN_Files/train_set/train/brat", doc.name)
    processfoot = doc.nlp(doc.pie[0])
    ini = doc.pie[1]
    vector = []
    for token in processfoot:
        vector.append(TransformWord_Foot(token, ini, informacion))

    return vector


def get_tokens_for_char(doc, diccAnotaciones, cat, char_idx_ini, char_idx_fin):
    match = False
    for i, token in enumerate(doc):
        if char_idx_ini > token.idx:
            continue
        elif char_idx_ini == token.idx:
            if token.i in diccAnotaciones:
                break
            match = True
            diccAnotaciones[token.i] = [token, cat]
            cat = cat.replace("C-", "D-")
        elif char_idx_ini < token.idx and match is False:
            if doc[i - 1].i in diccAnotaciones:
                break
            match = True
            diccAnotaciones[doc[i - 1].i] = [doc[i - 1], cat]
            cat = cat.replace("C-", "D-")
        elif match is True:
            if char_idx_fin < token.idx:
                break
            else:
                if token.i in diccAnotaciones:
                    break
                diccAnotaciones[token.i] = [token, cat]

    return match


def SearchPHIConfianza(doc, diccAnotaciones, PHIConfianza):
    for phi in PHIConfianza:  # los PHI estan en minusculas ya
        posiciones = findall(phi[0], doc.text.lower())
        if posiciones[0] != -1:
            for pos_ini in posiciones:
                indice_fin = pos_ini + len(phi[0]) - 1
                get_tokens_for_char(doc, diccAnotaciones, phi[1], pos_ini, indice_fin)


def SearchInDicc(doc, diccAnotaciones, dicc):
    for token in doc:
        if len(token.text) > 3 and token.i not in diccAnotaciones:
            if token.text.lower() in dicc:  # dicc ya esta en minusculas
                diccAnotaciones[token.i] = [token.text, "C-TER"]


def SearchEmail(doc, diccAnotaciones, pattern):
    emails = re.findall(pattern, doc.text)
    if emails:
        for email in emails:
            if len(email) > 3:
                pos_ini = doc.text.find(email)
                if pos_ini != -1:
                    indice_fin = pos_ini + len(email) - 1
                    get_tokens_for_char(doc, diccAnotaciones, "C-EMAIL", pos_ini, indice_fin)


def SearchFax(doc, diccAnotaciones):
    for token in doc:
        if "Fax" in token.text or "fax" in token.text:
            if doc[token.i + 1].text == ":":
                n_fax = 1
            else:
                n_fax = 0
            comienzo = True
            while doc[token.i + 1 + n_fax].is_digit or doc[token.i + 1 + n_fax].text in {"(", ")"}:
                if comienzo is True:
                    diccAnotaciones[doc[token.i + 1 + n_fax].i] = [doc[token.i + 1 + n_fax].text, "C-NUMF"]
                else:
                    if comienzo is True:
                        diccAnotaciones[doc[token.i + 1 + n_fax].i] = [doc[token.i + 1 + n_fax].text, "D-NUMF"]
                n_fax += 1


def SearchTelefonos(doc, diccAnotaciones, pattern):
    telefonos = re.findall(pattern, doc.text)
    if telefonos:
        for tlf in telefonos:
            if len(tlf) > 3:
                pos_ini = doc.text.find(tlf)
                if pos_ini != -1:
                    indice_fin = pos_ini + len(tlf) - 1
                    get_tokens_for_char(doc, diccAnotaciones, "C-NUMT", pos_ini, indice_fin)


def SearchRest(doc, diccAnotaciones, patterns):
    codigopost = re.findall(patterns['CP'], doc.text)

    if codigopost:
        codigopost = codigopost[0]

        pos_ini = doc.text.find(codigopost)
        if pos_ini != -1:
            indice_fin = pos_ini + len(codigopost) - 1
            get_tokens_for_char(doc, diccAnotaciones, "C-TER", pos_ini, indice_fin)

    cp = False
    street = False
    for value in diccAnotaciones.values():
        if "TER" in value[1]:
            cp = True
            break

    if cp is True:
        calle = re.findall(patterns['calle'], doc.text)

        if calle:
            calle = calle[0]

            pos_ini = doc.text.find(calle)
            if pos_ini != -1:
                indice_fin = 1000
                get_tokens_for_char(doc, diccAnotaciones, "C-CALLE", pos_ini, indice_fin)
                street = True

    if street:
        hospital = re.findall(patterns['hospital'], doc.text)
        if hospital:
            hospital = hospital[0]
            if len(hospital) > 3:
                pos_ini = doc.text.find(hospital)
                if pos_ini != -1:
                    indice_fin = 1000
                    get_tokens_for_char(doc, diccAnotaciones, "C-HOSP", pos_ini, indice_fin)

            inst = re.findall(patterns['institucion'], doc.text)

            if inst:
                inst = inst[0]
                if len(inst) > 3:
                    pos_ini = doc.text.find(inst)
                    if pos_ini != -1:
                        indice_fin = 1000
                        get_tokens_for_char(doc, diccAnotaciones, "C-INST", pos_ini, indice_fin)


def OrderDicc(doc, diccAnotaciones):
    result_x = []
    result_y = []
    for token in doc:
        result_x.append(token.text)
        if token.i in diccAnotaciones:
            result_y.append(diccAnotaciones[token.i][1])
        else:
            result_y.append("I")

    return result_x, result_y


def ClassifierFoot(file, PHIConfianza):
    document = read_file("MEDDOCAN_Files/train_set/train/brat/" + file + ".txt").rstrip()
    docum = DocumentMEDOCAN(file, document)

    vector = ExtractAnontationFoot(docum)
    x_test = [x[0] for x in vector]
    y_test = [x[1] for x in vector]

    doc = docum.nlp(docum.pie[0])

    diccAnotaciones = {}

    # Encontrar email
    emailPattern = '[\w\.-]+@[\w\.-]+'

    # Encontrar telefonos
    sep = '[\:\s\.\-\(\)\/]*'
    prefIntern = '(?:00\d{2}|(?:\+\s*?\d{2,4}?))'
    telForm1 = sep.join(['[69]\d{2}', '\d{2}', '\d{2}', '\d{2}', '\d{2}'])
    telForm2 = sep.join(['[69]\d{1}', '\d{3}', '\d{3}', '\d{2}', '\d{2}'])
    telForm3 = sep.join(['[69]\d{2}', '\d{3}', '\d{3}'])
    telForm4 = sep.join(['[69]\d{1}', '\d{2}', '\d{3}', '\d{2}'])
    telForm5 = sep.join(['[69]\d{3}', '\d{3}', '\d{3}'])
    telForm6 = sep.join(['\d{3}', '\d{2}', '\d{2}', '\d{2}'])
    telefonoPattern = prefIntern + '?' + sep + '(?:(?:' + telForm1 + ')|(?:' + telForm2 + ')|(?:' \
                      + telForm3 + ')|(?:' + telForm4 + ')|(?:' + telForm5 + ')|(?:' + telForm6 + '))'

    # Encontrar Calles
    pattCalle = '(?:(?:Avenida)|(?:Calle)|(?:avenida)|(?:calle)|(?:c\/)|(?:C\/)|(?:Carretera)|(?:carretera)|(?:Av\.)' \
                '|(?:av\.)|(?:avda\.)|(?:Avda\.)|(?:Carrer)|(?:carrer)|(?:Travesía)|(?:travesía)|(?:Paseo)|(?:paseo))'

    # Encontrar Hospital
    pattHospital = '(?:(?:Hospital)|(?:Centro Penitenciario)|(?:Centro de))'

    # Institución
    pattInstitucion = '(?:(?:Facultad)|(?:Universidad)|(?:Escuela universitaria)|(?:Clínica)|(?:Instituto))'

    pattCP = '(?:0[1-9]\d{3}|[1-4]\d{4}|5[0-2]\d{3})'

    patterns = {'calle': pattCalle, 'hospital': pattHospital, 'institucion': pattInstitucion, 'CP': pattCP}

    SearchPHIConfianza(doc, diccAnotaciones, PHIConfianza)
    dicc = CargaMunicipios()
    SearchEmail(doc, diccAnotaciones, emailPattern)
    SearchFax(doc, diccAnotaciones)
    SearchTelefonos(doc, diccAnotaciones, telefonoPattern)
    SearchInDicc(doc, diccAnotaciones, dicc)
    SearchRest(doc, diccAnotaciones, patterns)
    vector = OrderDicc(doc, diccAnotaciones)

    return (x_test, y_test), vector
