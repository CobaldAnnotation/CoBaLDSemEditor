# CoBaLD Editor

#### Description

This is an annotation tool for [CoBaLD Annotation Project](https://github.com/CobaldAnnotation). Currently it allows one to annotate semantic part of the standard only, but future versions may include the ability to annotate morphosyntax as well. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/main.jpg"  width="800">

#### Features

- Annotation of semantic slots (SS) and semantic classes (SC); 
- The program doesn't allow to save incorrect SS or SC;
- Morphosyntactic information can be viewed but not edited;
- The program stores comments and 'checked' marks for each sentence in a project;
- One can share .cobald projects by sending them to whomever;
- A ready CONLL-U file can be exported at any time;
- Automatic translations of sentence text are available.

#### Requirements

```
pip install pyqt5 googletrans==3.1.0a0
```

PyQT5 is used for the GUI itself and googletrans is used for getting translations directly from Google Translate.

#### Compiled versions

A compiled .exe version can be downloaded [here](https://drive.google.com/file/d/13StDOV0t6MR7R9lAMBCUhrGT9d8yj9Ga/view?usp=drive_link). A MacOS version can be compiled on request.


