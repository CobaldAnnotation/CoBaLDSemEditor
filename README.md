# CoBaLD Editor

#### Description

This is an annotation tool for [CoBaLD Annotation Project](https://github.com/CobaldAnnotation). It allows to edit annotations in CoBaLD format. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/01.JPG"  width="800">

#### Features

- Editing morphosyntactic information;
- Adding or removing tokens (normally aimed at ellipsis restoration);
- Annotation of semantic slots (SS) and semantic classes (SC); 
- The program doesn't allow to save incorrect SS or SC;
- index and wordform information can be viewed but not edited directly;
- XPOS and misc information is hidden;
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

A compiled .exe version can be downloaded [here](https://drive.google.com/file/d/1uAoCYlK_Wl1uwAIVLi6zO9udczqpNwWi/view?usp=sharing). A MacOS version can be compiled on request.


