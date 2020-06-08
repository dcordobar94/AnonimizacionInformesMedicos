from Chucking_Spacy import *


def WriteAnnotations(document, lista, folder, file):
    try:
        with open(folder + file, "a") as g:
            g.write("{" + document.name + ":")
            g.write(str(lista))
            g.write("}\n")
    except Exception as e:
        WriteError(document, e, folder, file)


def WriteError(document, e, folder, FileError):
    try:
        with open(folder + FileError, "a") as g:
            g.write(document.name)
            g.write("\n\t")
            g.write("Error: " + str(e))
    except:
        pass


if __name__ == '__main__':
    nlp = adjustmentSpacy()
    FileError_Cabeza = "/DocumentError.txt"
    file_Cabeza = "/Cabeza.txt"
    origins = read_folder_MEDDOCAN("MEDDOCAN_Files/train_set/train/brat")
    print('Ultimo documento leido: ', origins[-1].name)

    # analisis = DocumentsAnalysis()

    X = []
    Y = []
    folder = "C:/Users/dcord/OneDrive/Escritorio/Cursos/2017-18/TFM/MEDDOCAN_Files/train_set/train"
    open(folder + file_Cabeza, 'w').close()
    open(folder + FileError_Cabeza, 'w').close()
    f = open(folder + file_Cabeza, 'w', encoding='utf-8')
    for origin in origins:
        indx = origin.RecoverIndexsToAnnotationsFile("MEDDOCAN_Files/train_set/train/brat")
        try:
            cabeza = origin.ProcessCabeza()
            if cabeza[origin.name]:
                f.write(str(cabeza))
                f.write("\n")
            else:
                WriteError(origin, "Vacío", folder, FileError_Cabeza)

        # WriteAnnotations(origin, sents, folder)
        except Exception as e:

            WriteError(origin, e, folder, FileError_Cabeza)
            continue

    f.close()
