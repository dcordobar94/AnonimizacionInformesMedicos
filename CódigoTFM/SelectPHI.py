from ast import literal_eval
import sys, time

DOCLEIDOS = set()
PHI = {
    'NOMBRE_SUJETO_ASISTENCIA': "C-NOMS",
    'EDAD_SUJETO_ASISTENCIA': "C-EDADS",
    'SEXO_SUJETO_ASISTENCIA': "C-SEXOS",
    'FAMILIARES_SUJETO_ASISTENCIA': "C-FAMS",
    'NOMBRE_PERSONAL_SANITARIO': "C-NOMP",
    'FECHAS': "C-FECH",
    'PROFESION': "C-PROF",
    'CENTRO_SALUD': "C-CENT",
    'HOSPITAL': "C-HOSP",
    'INSTITUCION': "C-INST",
    'ID_TITULACION_PERSONAL_SANITARIO': "C-IDTIT",
    'ID_EMPLEO_PERSONAL_SANITARIO': "C-IDEMP",
    'IDENTIF_VEHICULOS_NRSERIE_PLACAS': "C-IDVEH",
    'IDENTIF_DISPOSITIVOS_NRSERIE': "C-IDDISP",
    'CALLE': "C-CALLE",
    'TERRITORIO': "C-TER",
    'PAIS': "C-PAIS",
    'NUMERO_TELEFONO': "C-NUMT",
    'NUMERO_FAX': "C-NUMF",
    'CORREO_ELECTRONICO': "C-EMAIL",
    'ID_SUJETO_ASISTENCIA': "C-IDSUJ",
    'ID_CONTACTO_ASISTENCIAL': "C-IDCONT",
    'NUMERO_BENEF_PLAN_SALUD': "C-NUMB",
    'ID_ASEGURAMIENTO': "C-IDASEG",
    'URL_WEB': "C-URL",
    'DIREC_PROT_INTERNET': "C-DIRECT",
    'OTRO_NUMERO_IDENTIF': "C-IDOTRO",
    'OTROS_SUJETO_ASISTENCIA': "C-OTROS"
}


def ModifyVectors(folder_vectors, files, CDI=False):
    # num_doc indican los documentos que se quieren analizar
    TotalSents = 0
    TotalSentsPHI = 0
    TotalDocLeidos = 0
    TotalDocSinPHI = 0
    TotalDocError = 0

    search = True
    while search:
        time.sleep(0.1)
        for file in files:
            with open(folder_vectors + "/" + file, "r") as f:
                for x in f:
                    sys.stdout.write('\rExtrayendo labels ' + ' |')
                    time.sleep(0.01)
                    sys.stdout.write('\rExtrayendo labels ' + ' /')
                    time.sleep(0.01)
                    sys.stdout.write('\rExtrayendo labels ' + ' -')
                    time.sleep(0.01)
                    sys.stdout.write('\rExtrayendo labels ' + ' \\')

                    try:
                        # print("linea: ", x)
                        keyvalue = x.split(":[[[")
                        key = keyvalue[0][1:]  # A partir de 1 para quitarle el {
                        # print("key:", keyvalue[0][1:], "Value: ", "[[[" + keyvalue[1][:-2])
                        value = keyvalue[1].replace("}\n", "}")
                        value = literal_eval("[[[" + value[:-1])  # Hasta -1 para quitarle el }
                        ruta = (folder_vectors + "/brat", key)
                        new_sents = AddLabel(ruta, value, CDI)
                        TotalDocLeidos += 1
                        if new_sents:
                            TotalSents += len(value)
                            TotalSentsPHI += len(new_sents)
                            yield ({key: new_sents})
                        else:
                            TotalDocSinPHI += 1
                    except Exception as e:
                        print("Error al leer el fichero", file, "\n\t Tipo error:", e)
                        TotalDocError += 1
                        pass
        search = False
    yield (TotalSentsPHI, TotalSents, TotalSentsPHI / TotalSents, TotalDocLeidos, TotalDocSinPHI, TotalDocError)


def ModifyVectorsHead(folder_vectors, file, CDI=False):
    # num_doc indican los documentos que se quieren analizar
    TotalSents = 0
    TotalSentsPHI = 0
    TotalDocLeidos = 0
    TotalDocSinPHI = 0
    TotalDocError = 0

    search = True
    while search:
        time.sleep(0.1)
        with open(folder_vectors + "/" + file, "r", encoding='utf-8') as f:
            for x in f:
                sys.stdout.write('\rExtrayendo labels ' + ' |')
                time.sleep(0.01)
                sys.stdout.write('\rExtrayendo labels ' + ' /')
                time.sleep(0.01)
                sys.stdout.write('\rExtrayendo labels ' + ' -')
                time.sleep(0.01)
                sys.stdout.write('\rExtrayendo labels ' + ' \\')
                # try:
                # print("linea: ", x)
                dicc = eval(x.replace("}\n", "}"))
                clave = list(dicc.keys())[0]
                informacion = ExtractLabel("MEDDOCAN_Files/train_set/train/brat", clave)
                dicc[clave] = TransformWord_Cabeza(dicc[clave], informacion, True)
                TotalDocLeidos += 1
                if dicc:
                    yield (dicc)
                else:
                    TotalDocSinPHI += 1

                # except Exception as e:
                #    print("Error al leer el fichero", file, "\n\t Tipo error:", e)
                #    TotalDocError += 1
                #    pass
        search = False


def UpdateCount(categoria):
    if categoria:
        if categoria in conteolabels:
            conteolabels[categoria] += 1
        else:
            conteolabels[categoria] = 1


def ReadFile(file):
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


def TransformCategoria(categoria):
    return PHI[categoria]


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


def UpdateInformacion(info, idx):
    if info[idx][1] is not None:
        idxs_to_update = [idx]
        idxs_to_update.extend(info[idx][1])
        for indice in idxs_to_update:
            info[indice][0] = "D" + info[indice][0][1:]
            info[indice][1] = None

    return info


def TransformWord(word, information, CDI):
    findLabel = False
    try:
        idx_word = int(word[0].replace("idx=", ""))
        if idx_word in information[0]:  # informacion = ({ind1, ind2,...},{ind1:[cat,[ind1,ind2,...]], ind2:...})
            word[0] = "label=" + information[1][idx_word][0]
            UpdateCount(word[0][6:])
            if CDI is True:
                information = (information[0], UpdateInformacion(information[1], idx_word))
            findLabel = True
        else:
            word[0] = "label=I"
    except Exception as e:
        print("Error al obtener el índice y etiquetar el vector ", word, " Error tipo: ", e)
        pass

    return word, findLabel


def TransformWord_Cabeza(dicc, information, CDI):
    for word in dicc:  # dicc = {idx:[text, PHI],...}
        idx_token = int(word)
        if idx_token in information[0]:  # informacion = ({ind1, ind2,...},{ind1:[cat,[ind1,ind2,...]], ind2:...})
            tokens = dicc[word][1].split()
            if len(tokens) == 1:
                dicc[word][1] = [[tokens[0], information[1][idx_token][0]]]
                UpdateCount(information[1][idx_token][0])
            else:
                if CDI is True:
                    categoria = information[1][idx_token][0]
                    dicc[word][1] = [[tokens[0], categoria]]
                    for i in range(1, len(tokens)):
                        dicc[word][1].append([tokens[i], "D-" + categoria[2:]])
                else:
                    categoria = information[1][idx_token][0]
                    dicc[word][1] = [[tokens[0], categoria]]
                    for i in range(1, len(tokens)):
                        dicc[word][1].append([tokens[i], categoria])
        else:
            dicc[word][1] = [[dicc[word][1], "I"]]
    return dicc


def AddLabel(ruta, vector, CDI=False):
    information = ExtractLabel(ruta[0], ruta[1])
    sents = vector
    new_sents = []
    for sent in sents:
        findPHI = False
        new_sent = []
        for word in sent:

            (new_word, findLabel) = TransformWord(word, information, CDI)
            new_sent.append(new_word)
            if findLabel is True:
                findPHI = True

        if findPHI is True:
            new_sents.append(new_sent)

    return new_sents


if __name__ == '__main__':
    conteolabels = {}
    CDI = True
    folder = "MEDDOCAN_Files/train_set/train"
    file = ["Variables_3.txt", "Variables.txt", "Variables_1.txt", "Variables_2.txt"]
    # fileHead = "Cabeza.txt"
    vectorslabel = ModifyVectors(folder, file, CDI)
    # fvariables = "VariablesWithLabel/CleanVariableNI_tags.txt"
    # headlabel = ModifyVectorsHead(folder, fileHead, True)
    gvariables = "VariablesWithLabel/CuerpoDicc_CDI.txt"
    # fdatos = "Head/DatosHead.txt"
    filevariables = open(folder + "/" + gvariables, "w")
    for dicc in vectorslabel:
        if type(dicc) != tuple:
            filevariables.write(str(dicc) + "\n")
        '''
        else:
            print("conteolabels: ", conteolabels)
            with open(folder + "/" + fdatos, "w") as filedatos:
                informacion = "Total frases obtenidas con PHI: " + str(vector[0]) + "\nTotal frases leidas: " + str(
                    vector[1]) + "\nFrecuencia relativa acumulada: " + str(
                    vector[2]) + "\nTotal Documentos leidos: " + str(
                    vector[3]) + "\nTotal Documentos sin PHI encontrados en el cuerpo: " + str(
                    vector[4]) + "\nTotal Documentos que han dado error: " + str(
                    vector[5]) + "\nTipos de PHI encontrados:\n" + str(conteolabels)
                filedatos.write(informacion)
        '''
    filevariables.close()

    print("\n")
    print("Guardado vectores etiquetados en ", gvariables)
    # print("Guardado datos de información recogida en ", fdatos)
