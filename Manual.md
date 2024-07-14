## CoBaLD Editor Tutorial

The program allows one to annotate morphosyntactic and semantic information for the CoBaLD standard. This is how it looks with an imported .conllu:

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man00.JPG"  width="800">

#### Create new project

The program keeps its data in the form of projects: in order to start working, you must create a new project. A project is a file in .cobald format which stores your CONLL-U with all its annotation, the translations you get automatically, your comments and checkmarks (thus, its size may be twice as big as the size of the original .conllu).

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man01.JPG"  width="400">

In the File menu, choose 'New project' and in the opened dialogue window choose a place and a name for your future project. Afterwards, you have to import the CONLL-U: the dialogue window for importing will open automatically after you create a project. You may replace the .conllu in your project any time by manually importing it.

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man02.JPG"  width="600">

After you import your CONLL-U, it will load and you will see the first sentence. Note the columns: you cannot edit index and wordform, but you can edit morphosyntax (in a red border)  and semantics (in a blue border).

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man03.JPG"  width="800">

You can also add and remove tokens (but please do so only for elided heads with indices like 1.1 or such) by calling a context menu which appears when you right-click on any token wordform:

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man03.5.JPG"  width="200">

The program will then ask you to input the index of a token to add or to remove. If adding, it will automatically add the new '#NULL' token at a chosen position, if removing, it will try to remove a token with such index. If you accidentally have two tokens with the same index, it will remove the first one. 

If you try to add a token with an integer-type index, the program will allow you to do that and even re-numerate the rest of the tokens, but you won't be able to edit its wordform, so please don't do it. The same goes for deleting such tokens: if you try to delete an integer-indexed token with a non=#NULL form, the program will warn you about that.

#### Toolbars

Let's view the available toolbars. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man04.JPG"  width="400">


On the left, there are keys for undo and redo actions: feel free to use hotkeys `Ctrl+Z` and `Ctrl+Y`! These keys undo any changes you've made to almost any fields: they remember the initial state of a category and if you want to restore it, just undo it. There is also an option to restore the annotation as it was before your actions: it's the third key here. Mind that the reset action is irreversible, you'll lose all your edits if you reset! The program will ask you to confirm your choice. 

On this toolbar, there is also a checkbox to mark the sentence as viewed. Its state gets saved with the edits you'd made after you've moved to the next (or previous) sentence. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man05.JPG"  width="400">

Next, there are keys for navigation: you can go to the next sentence or return to the previous one; you can go to the first sentence marked as unchecked; if you wish to switch to a sentence with a certain number, you may enter this number in the box and press the 'Go to' key (or just press 'Enter').

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man06.JPG"  width="500">

Finally, there is the option to show morphological features (beware: these are long!) and to get automatic translation of your sentence. You have to choose the languages yourself, the program doesn't detect your language. As it gets its translations from Google Translate, you need to have an internet connection in order to make it work. 

#### Annotation process

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man07.JPG"  width="600">

Whenever you edit UPOS, XPOS, dependency relation, semantic slot and semantic class lines, the program will suggest variants for you. You may choose them with your mouse or press `Down` arrow on your keyboard and `Enter` whenever the needed variant is chosen. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man08.JPG"  width="600">

If you make a typo in a semantic slot or class, the program won't allow you to save your sentence annotation: it will warn you and highlight the error with red. It also won't allow to choose an unexistent head for base UD annotation. The program allows one to choose morphological features and dependency relations it doesn't know, but it will ask you to check them.

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man09.JPG"  width="300">

#### Export CONLL-U and share

If you want to share your comments and your annotation, you may just send the .cobald file to your colleague. This file stores all comments and 'Checked' marks. Mind that if you close and re-open the program, it will remember your last project and the sentence you were annotating and it will try to load them. If you just open someone else's project (or the project you've stopped working on), it will open on the first sentence. 

If something goes amiss and you want the program to 'forget' your current project and position, you may just delete the 'settings.bin' file from the 'inside' folder.

You may also export your CONLL-U without any comments and marks: the program will ask you to enter the name and choose the place for your CONLL-U. Your annotation will be exported in that CONLL-U, but if the source CONLL-U didn't have translations, your automatic ones won't be exported. 