# Anonimización de Informes Médicos
Proyecto dedicado a la anonimización de los informes médicos obtenidos de la tarea MEDDOCAN (en español).

El proyecto se compone de:

1. Memoria del trabajo (MemoriaTFM.pdf). Se explica todo el proceso realizado para llevar a cabo la anonimización de informes médicos.

2. Archivos .py. Es el código realizado para el proyecto. 
  Se ha realizado en Python 3.7. Se apoya principalmente en la librería de spaCy para PLN que usa el corpus AnCora y WikiNER como entrenamiento para textos en español, y la librería CRFsuite para entrenamiento de un modelo de Conditional Random Field.
  2.1 - Chucking_Spacy.py: Se define la clase para procesar los documentos de entrada.
  2.2 - Chucking_Spacy_MEDDOCAN.py: Llama al fichero anterior. Recibe de entrada los documentos y devuelve un file con los documentos tokenizados y con información útil. 
  2.3 - 
