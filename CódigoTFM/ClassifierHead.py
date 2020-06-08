from TrainingCRF import bio_classification_report

DATOS = {}

ANOTACIONES = {
    'nombre': 'C-NOMS',
    'apellidos': 'C-NOMS',
    'nhc': 'C-IDSUJ',
    'nass': 'C-IDASEG',
    'domicilio': 'C-CALLE',
    'localidad/ provincia': 'C-TER',
    'localidad/provincia': 'C-TER',
    'localidad': 'C-TER',
    'provincia': 'C-TER',
    'cp': 'C-TER',
    'fecha de nacimiento': 'C-FECH',
    'país': 'C-PAIS',
    'pais': 'C-PAIS',
    'edad': 'C-EDADS',
    'sexo': 'C-SEXOS',
    'fecha de ingreso': 'C-FECH',
    'médico': 'C-NOMP',
    'medico': 'C-NOMP',
    'nºcol': 'C-IDTIT',
    'ncol': 'C-IDTIT',
    'episodio': 'C-IDCONT',
    'país de nacimiento': 'C-PAIS',
    'pais de nacimiento': 'C-PAIS'
}


def ExtractInfo(dicc):
    uniqueKey = list(dicc.keys())[0]
    for sent in dicc[uniqueKey].values():
        if sent:
            sent[0] = sent[0].replace("\ufeff", "")
            if sent[0] in DATOS.keys():
                find = False
                i = 0
                for type in DATOS[sent[0]]:
                    if sent[1][0][1] == type[0]:
                        DATOS[sent[0]][i][1] += 1
                        find = True

                if find == False:
                    if uniqueKey != 'S0212-16112007000800012-1' and uniqueKey != 'S1137-66272014000100019-1' and uniqueKey != 'S1130-05582007000600003-1' and uniqueKey != 'S1130-01082009000500012-1':
                        DATOS[sent[0]].append([sent[1][0][1], 1])

            else:
                DATOS[sent[0]] = [[sent[1][0][1], 1]]


def ClasificadorHead(token_sent, CDI=True):
    # token_sent [Nombre,Ernesto] o [Apellidos,Garcia Bueno]
    word = token_sent[0].lower().lstrip().rstrip()
    anotacion = []
    vector_words = []
    if word in ANOTACIONES:
        tokens = token_sent[1].split()
        if len(tokens) == 1:

            anotacion = ([ANOTACIONES[word]])
            vector_words = tokens
        else:
            if len(tokens) == 0:
                anotacion = ["I"]
                vector_words = [""]
            else:
                anotacion = [ANOTACIONES[word]]
                vector_words = [tokens[0]]
                if CDI is True:
                    for i in range(1, len(tokens)):
                        anotacion.extend(["D-" + ANOTACIONES[word][2:]])
                        vector_words.append(tokens[i])
                else:
                    for i in range(1, len(tokens)):
                        anotacion.extend(ANOTACIONES[word])
                        vector_words.append(tokens[i])
    else:
        tokens = token_sent[1].split()
        if len(tokens) == 1:
            anotacion = (["I"])
            vector_words = tokens
        else:
            if len(tokens) == 0:
                anotacion = ["I"]
                vector_words = [""]
            else:
                if CDI is True:
                    for i in range(1, len(tokens)):
                        anotacion.extend(["I"])
                        vector_words.append(tokens[i])
                else:
                    for i in range(1, len(tokens)):
                        anotacion.extend("I")
                        vector_words.append(tokens[i])
    return (vector_words, anotacion)


def VectorResults(dicc):
    # dicc = {doc:{idx:[Nombre,Apellidos] }
    doc = list(dicc.keys())[0]
    v_pred = []
    x_pred = []
    for token_sents in dicc[doc].values():
        x_pred.extend(ClasificadorHead(token_sents)[0])
        v_pred.extend(ClasificadorHead(token_sents)[1])

    return (x_pred, v_pred)


def ExtractAnotaciones(doc, diccAnotaciones):
    y_real = []
    if doc in diccAnotaciones.keys():
        dicc = diccAnotaciones[doc]
        for token_sents in dicc.values():
            info = token_sents[1]
            if len(info) == 1:
                y_real.append(info[0][1])
            else:
                for word in info:
                    y_real.append(word[1])
    return y_real


def TransforFileInDicc(folder, file):
    try:
        with open(folder + "/" + file, "r", encoding="utf8") as f:
            dicc = ""
            for x in f:
                x = x.replace("\ufeff", "")
                line = x.replace("\n", "")[1:]
                dicc += line.replace("}}", "},")

            dicc = "{" + dicc[:-1] + "}"
            diccAnot = eval(dicc)

        return diccAnot

    except UnicodeDecodeError:
        with open(folder + "/" + file, "r") as f:
            dicc = ""
            for x in f:
                x = x.replace("\ufeff", "")
                line = x.replace("\n", "")[1:]
                dicc += line.replace("}}", "},")

            dicc = "{" + dicc[:-1] + "}"
            diccAnot = eval(dicc)

        return diccAnot



def ProcessHead():
    folder = "MEDDOCAN_Files/train_set/train"
    data = "Cabeza.txt"
    DocAnotaciones = "Head/HeadWithLaberls.txt"
    Y_pred = []
    X_pred = []
    Y_real = []
    diccAnotado = TransforFileInDicc(folder, DocAnotaciones)
    with open(folder + "/" + data, "r", encoding='utf-8') as f:
        for x in f:
            dicc = eval(x.replace("}\n", "}"))
            doc = list(dicc.keys())[0]
            yreal = ExtractAnotaciones(doc, diccAnotado)
            if yreal:
                ypred = VectorResults(dicc)[1]
                xpred = VectorResults(dicc)[0]
                if len(yreal) == len(ypred):
                    Y_pred.append(ypred)
                    X_pred.append(xpred)
                    Y_real.append(yreal)

    return (X_pred, Y_pred), Y_real
