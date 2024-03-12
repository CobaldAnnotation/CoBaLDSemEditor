## CoBaLD Editor Tutorial

#### Create new project

The program keeps its data in the form of projects: in order to start working, you must create new project. A project is a file in .cobald format which stores your CONLL-U with all its annotation, the translations you get automatically, your comments and checkmarks. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man01.JPG"  width="400">

In the File menu, choose 'New project' and in the opened dialogue window choose a place and a name for your future project. Afterwards, you have to import the CONLL-U: choose the corresponding option in the File menu and find the CONLL-U you want to work at.

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man02.JPG"  width="600">

After you import your CONLL-U, it will load and you will see the first sentence.

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man03.JPG"  width="800">

#### Toolbars

Let's view available toolbars. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man04.JPG"  width="400">


On the left, there are keys for undo and redo actions: feel free to use hotkeys `Ctrl+Z` and `Ctrl+Y`! These keys undo any changes you've made to the semantic slots or classes: they remember the initial state of a category and if you want to restore it, just undo it. There is also an option to restore the annotation as it was before your actions: it's the third key here. Mind that the reset action is irreversible, you'll lose all your edits if you reset! The program will ask you to confirm your choice. 

On this toolbar, there is also a checkbox to mark the sentence as viewed. Its state gets saved with the edits you'd made after you've moved to the next (or previous) sentence. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man05.JPG"  width="400">

Next, there are keys for navigation: you can go to the next sentence or return to the previous one; if you wish to switch to a sentence with a certain number, you may enter this number in the box and press the 'Go to' key. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man06.JPG"  width="500">

Finally, there is the option to show morphological features (beware: these are long!) and to get automatic translation of your sentence. You have to choose the languages yourself, the program doesn't detect your language. As it gets its translations from Google Translate, you need to have an internet connection in order to make it work. 

#### Annotation process

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man07.JPG"  width="600">

Whenever you edit semantic slot and semantic class lines, the program will suggest variants for you. You may choose them with your mouse or press `Down` arrow on your keyboard and `Enter` whenever the needed variant is chosen. 

<img src="https://github.com/fortvivlan/CoBaLDSemEditor/blob/main/img/man08.JPG"  width="600">

If you make a typo, the program won't allow you to save your sentence annotation: it will warn you and highlight the error with red. 

#### Export CONLL-U and share

If you want to share your comments and your annotation, you may just send the .cobald file to your colleague. This file stores all comments and 'Checked' marks. Mind that if you close and re-open the program, it will remember your last project and the sentence you were annotating and it will try to load them. If you just open someone else's project (or the project you've stopped working on), it will open on the first sentence. 

If something goes amiss and you want the program to 'forget' your current project and position, you may just delete the 'settings.bin' file from the 'inside' folder.

You may also export your CONLL-U without any comments and marks: the program will ask you to enter the name and choose the place for your CONLL-U. Your annotation will be exported in that CONLL-U, but if the source CONLL-U didn't have translations, your automatic ones won't be exported. 