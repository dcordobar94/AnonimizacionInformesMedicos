import pycrfsuite
from sklearn.model_selection import train_test_split
import numpy as np
from sklearn.metrics import classification_report, f1_score
from sklearn.preprocessing import LabelBinarizer, MultiLabelBinarizer
from itertools import chain
import ClassifierHead
from ClassifierFoot import *


def extract_feautures(sents):
    words = []
    labels = []
    for sent in sents:
        if type(sent[0]) == list:
            for word in sent:
                for caract in word:
                    if "idx=" in caract:
                        word.remove(caract)
                words.append(word[1:])
                labels.append(extract_label(word))
        else:
            for caract in sent:
                if "idx=" in caract:
                    sent.remove(caract)
            words.append(sent[1:])
            labels.append(extract_label(sent))

    return words, labels


#    print("word[1:]", word[1:])
#    words.append(word[1:])

def extract_label(word):
    label = word[0].replace("label=", "")
    return label


def bio_classification_report(y_true, y_pred):
    """
    Classification report for a list of BIO-encoded sequences.
    It computes token-level metrics and discards "O" labels.

    Note that it requires scikit-learn 0.15+ (or a version from github master)
    to calculate averages properly!
    """
    lb = LabelBinarizer()
    y_true_combined = lb.fit_transform(list(chain.from_iterable(y_true)))
    y_pred_combined = lb.transform(list(chain.from_iterable(y_pred)))

    tagset = set(lb.classes_)  # - {'I'}
    # print("tagset:", tagset)
    tagset = sorted(tagset, key=lambda tag: tag.split('-', 1)[::-1])
    class_indices = {cls: idx for idx, cls in enumerate(lb.classes_)}

    return classification_report(
        y_true_combined,
        y_pred_combined,
        labels=[class_indices[cls] for cls in tagset],
        target_names=tagset,
    )


if __name__ == '__main__':
    Tags = True
    folder = "MEDDOCAN_Files/train_set/train/VariablesWithLabel"
    file = "CuerpoDicc_CDI.txt"
    X = []
    Y = []
    print("Leyendo vectores etiquetados")
    with open(folder + "/" + file, "r") as f:
        for doc in f:
            doc = eval(doc)
            uniquekey = list(doc.keys())[0]
            for sents in doc.values():
                (x, y) = extract_feautures(sents)
                X.append((uniquekey, x))
                Y.append((uniquekey, y))
    print("X:\n", X[0])
    print("Y:\n", Y[0])

    print("Preparando modelo")
    X_trainBody, X_testBody, Y_trainBody, Y_testBody = train_test_split(X, Y, test_size=0.25)
    X_train = [sents for (doc, sents) in X_trainBody]
    X_test = [sents for (doc, sents) in X_testBody]
    Y_train = [sents for (doc, sents) in Y_trainBody]

    '''
    trainer = pycrfsuite.Trainer(verbose=False)

    # Submit training data to the trainer
    for xseq, yseq in zip(X_train, Y_train):
        trainer.append(xseq, yseq)

    print("Modelo preparado")
    # Set the parameters of the model
    trainer.set_params({
        # coefficient for L1 penalty
        'c1': 0.1,

        # coefficient for L2 penalty
        'c2': 0.001,

        # maximum number of iterations
        'max_iterations': 5000,

        # whether to include transitions that
        # are possible, but not observed
        'feature.possible_transitions': True
    })

    # Provide a file name as a parameter to the train function, such that
    # the model will be saved to the file when training is finished
    print("Entrenando modelo")
    start = time.time()
    trainer.train('crf.model')
    end = time.time()

    print("Finalizado entrenamiento en: ", end - start)
    '''
    print("Usando modelo crf.model para predecir")
    # Predict
    tagger = pycrfsuite.Tagger()
    tagger.open('crf.model012500')
    XY_predBody = [(xseq, tagger.tag(xseq)) for xseq in X_test]

    Y_predTotal = []
    Y_testTotal = []
    Y_predFoot = []
    Y_testFoot = []
    folderCleanHead = "MEDDOCAN_Files/train_set/train"
    fileHeadAnotation = "Head/HeadWithLaberls.txt"
    fileCleanHead = "Cabeza.txt"
    CleanHead = ClassifierHead.TransforFileInDicc(folderCleanHead, fileCleanHead)
    diccAnotadoHead = ClassifierHead.TransforFileInDicc(folderCleanHead, fileHeadAnotation)
    for v_testBodydoc, v_Body in zip(Y_testBody, XY_predBody):
        (x_predBody, v_predBody) = v_Body
        doc = v_testBodydoc[0]
        v_testBody = v_testBodydoc[1]
        PHIConfianza = []
        if doc in CleanHead.keys() and doc in diccAnotadoHead:
            v_testHead = ClassifierHead.ExtractAnotaciones(doc, diccAnotadoHead)
            x_predHead = ClassifierHead.VectorResults({doc: CleanHead[doc]})[0]
            v_predHead = ClassifierHead.VectorResults({doc: CleanHead[doc]})[1]

            PHIConfianza = Extract_Feautures_Head_ToFoot(x_predHead, v_predHead)
            PHIConfianza.extend(Extract_Feautures_Body_ToFoot(x_predBody, v_predBody))

            vectoresFoot = ClassifierFoot(doc, PHIConfianza)

            if vectoresFoot[1][0] and vectoresFoot[1][1]:  # si las predicciones del foot no vacia
                Y_testFoot.append(vectoresFoot[0][1])
                Y_predFoot.append(vectoresFoot[1][1])

            #print("x_predHead: ", x_predHead)
            #print("y_predHead: ", v_predHead)
            if len(v_predHead) == len(v_testHead):
                Y_testTotal.append(v_testBody)
                Y_testTotal[-1].extend(v_testHead)
                Y_predTotal.append(v_predBody)
                Y_predTotal[-1].extend(v_predHead)
                if vectoresFoot[1][0] and vectoresFoot[1][1]:  # si las predicciones del foot no vacia
                    Y_testTotal[-1].extend(vectoresFoot[0][1])
                    Y_predTotal[-1].extend(vectoresFoot[1][1])

    # print("Y_testTotal", Y_testTotal[0:10])
    # print("Y_predTotal", Y_predTotal[0:10])

    if not Tags:
        # Create a mapping of labels to indices
        labels = {"N": 1, "I": 0}

        # Convert the sequences of tags into a 1-dimensional array
        predictions = np.array([labels[tag] for row in Y_predTotal for tag in row])
        truths = np.array([labels[tag] for row in Y_testTotal for tag in row])

        # Print out the classification report
        print(classification_report(
            truths, predictions,
            target_names=["I", "N"]))

    else:
        print(bio_classification_report(Y_testTotal, Y_predTotal))
        binarizer = MultiLabelBinarizer()

        # This should be your original approach
        # binarizer.fit(your actual true output consisting of all labels)

        # In this case, I am considering only the given labels.
        binarizer.fit(Y_testTotal)

        #print("F1-score: ", f1_score(binarizer.transform(Y_testTotal), binarizer.transform(Y_predTotal), average='micro'))
