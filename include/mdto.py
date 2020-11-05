"""MDTO, or MDT-Object, is a task run to test a subject's memory based on
object similarity. Objects are shown as images, and images are grouped into
2 categories as follows:

The first is a collection of image pairs. Each pair in this collection
consists of a "target" and "lure"; the lure is a similar image to the target
for each pair, and the level of similarilty can differ, known as the
"lure bin", rated on a scale of 1-2 (highest to lowest similarity)

The second is a collection of "singles" or unique / non-similar images.
During the task these are randomly split up into "repeats" - images that
are shown twice, and "foils", images that are shown only once.

The task consists of a study and test phase. In the study phase, a number 
of "targets" and "repeats" are shown to the subject. In the test phase,
"lures", "repeats", and "foils" are shown to the subject. In the test 
phase, the subject must determine which of the images being shown were also
previously shown in the study phase. Indeed, only the "repeats" have been
actually shown twice, while the lures exist to "trick" the subject, since
they are similar to the "targets" previously shown.
"""

#TODO: make pause (space) not count towards response if paused


from __future__ import division
import os, sys, math, random, numpy
from psychopy.visual import Window, ImageStim, TextStim, ShapeStim
from psychopy.event import clearEvents, getKeys, waitKeys
from psychopy.core import Clock, wait
from PIL import Image
import glob

class MDTO(object):

    def __init__(self, logfile, imgDir, screenType, expVariant,
                trialDuration, ISI, trialsPer, selfPaced, practiceTrials, inputButtons, pauseButton):

        self.logfile = logfile
        self.expVariant = expVariant
        self.trialDuration = trialDuration
        self.selfPaced = selfPaced
        self.ISI = ISI
        self.trialsPer = trialsPer
        self.imgDir = imgDir
        self.leftOvers = []
        self.splitLures = self.SplitLures()
        self.splitSingles = self.SplitSingles()
        self.runPracticeTrials = practiceTrials
        self.leftButton  = inputButtons[0]
        self.rightButton = inputButtons[1]
        self.pauseButton = pauseButton

        if (screenType == 'Windowed'):
            screenSelect = False
        elif (screenType == 'Fullscreen'):
            screenSelect = True

        self.window = Window(fullscr=screenSelect,units='pix', 
                             color='White',allowGUI=False)
        self.imageWidth = self.window.size[1]/3

        #Define the black box that appears in the lower left, to signal EEG
        rW = 110    #Width 
        rH = 60     #Height
        rectVertices = [[rW,-rH],[-rW,-rH],[-rW,rH],[rW,rH]]
        rectCenter = [(-self.window.size[0]/2 + rW),(-self.window.size[1]/2) + rH]
        self.blackBox = ShapeStim(self.window, fillColor='black', 
            units='pix', fillColorSpace='rgb', vertices=rectVertices, 
            closeShape=True, interpolate=True, pos=rectCenter)
        self.rangeITI = numpy.arange(1, 1.4, .001)

        self.clock = Clock()

        #Initialize scorelist for 4 categories|| [correct,incorrect,response]
        self.scoreList = []
        for i in range(0,4):
            self.scoreList.append([0,0,0])

    def GrabFileType(self, fileList, exts):
        """Takes an inputted list, as well as extension, and returns a list with
        the elements in the original list that have the desired extension.

        fileList: The list of files to search through
        ext: string containing the extension type, e.g. ".jpg", ".png"

        return: a new list, containing files only of ext type
        """
        fileListofType = []

        for aFile in fileList:
            for ext in exts:
                ftLen = len(ext)
                if (aFile[-ftLen:] == ext):
                    fileListofType.append(aFile)
                    break

        return fileListofType


    def SplitLures(self):
        """Creates and returns a list of image lures. Lures are taken from
        both the lure high and lure low directory, and an equal amount of 
        each are put into the list. Each element in the returned list has 2
        elements: [imgA,imgB] and a number, pertaining to the difficulty of
        the lure, i.e. the  degree of apparent difference between the two images.

        Return: a list, each element being: [[imgA,imgB], lureNum]
        """
        dirFiles = os.listdir(self.imgDir)
        imgTypes = ['.jpg', '.jpeg', '.JPG']
        allImgs = self.GrabFileType(dirFiles, imgTypes)
        allImgs = [img for img in allImgs if "PR" not in img]
        lureLowImgs = []
        lureHighImgs = []
        for img in allImgs:
            if (img[5] == "1"):
                lureHighImgs.append(img)
            elif (img[5] == "2"):
                lureLowImgs.append(img)

        #Sort images by name
        lureHighImgs.sort()
        lureLowImgs.sort()

        #Return a list of lures as a list w/: [[imgA,imgB],lureType]
        def LureListGroup(imgList):
            lureList = []
            for i in range(0, int(len(imgList)/2)):
                imgA = imgList[i*2]
                imgB = imgList[(i*2)+1]
                highSet = [imgA,imgB]
                lureList.append(highSet)
            return lureList

        #Create list of lures with embedded structure, then shuffle
        lureHighList = LureListGroup(lureHighImgs)
        lureLowList = LureListGroup(lureLowImgs)
        random.shuffle(lureHighList)
        random.shuffle(lureLowList)

        #Put number (num of trials) of list items from both lists into list
        selectedList = []
        for i in range(0, self.trialsPer):
            selectedList.append(lureHighList[i])
            selectedList.append(lureLowList[i])

        #Unused "leftover" A images will be used as singles
        #Probably want to use other method while seeded rand unimplemented
        #OK for now
        for i in range(self.trialsPer+1, len(lureHighList)):
            try:
                self.leftOvers.append(lureHighList[i][0])
            except IndexError:
                pass
            try:
                self.leftOvers.append(lureLowList[i][0])
            except IndexError:
                pass

        random.shuffle(selectedList)
        return selectedList
        
    def SplitSingles(self):
        """Creates and returns a list of image "singles". Each item in the
        list is an image, followed by either "sF" (single Foil) or "sR"
        (single repeat), indicating if it is to be shown once or twice.

        return: list composed of [imageFileName, type]
                type: "sR" or "sF"
        """
        singles = self.leftOvers
        targetsFoils = []
        for i in range(0, self.trialsPer*2):
            if (i % 2 == 0):
                targetsFoils.append([singles[i],"sR"])
            else:
                targetsFoils.append([singles[i],"sF"])

        random.shuffle(targetsFoils)
        return targetsFoils

    def Pause(self):
        """Pauses the task, and displays a message waiting for a spacebar
        input from the user before continuing to proceed.
        """
        pauseMsg = "Experiment Paused\n\nPress '{}' to continue".format(self.pauseButton)
        pauseText = TextStim(self.window, text=pauseMsg, color='Black', height=40)
        pauseText.draw(self.window)
        self.window.flip()
        waitKeys(keyList=[self.pauseButton])
        clearEvents()


    def ScaleImage(self, image, maxSize = 350):
        """Scales the size of the image to fit as largely as it can within the 
        window of the defined maxSize, while preserving its aspect ratio.

        image: the filename of the image to be scaled
        maxSize: maximum size, in pixels of image
        return: maximum scaling of image
        """
        im = Image.open(image)
        larger = im.size[0]
        if (im.size[0] < im.size[1]):
            larger = im.size[1]
        scale = larger / maxSize
        scaledSize = (im.size[0]/scale, im.size[1]/scale)
        return scaledSize

    def RunTrialECog(self, image, phase):
        """Runs a particular trial for an ECog (Electrocorticography) based 
        task. An ECog trial runs as follows: display the image along with
        the black box for <trial duration> amount of time, clear the screen
        for <ISI> amount of time, then asking for and getting subject input
        for <ITI> amount of time.

        image: the stimuli to display on screen
        phase: 0 (Study Phase) - prompts user "Indoor / Outdoor"
               1 (Test Phase) - prompts user "Old / New"
        return: [keyPress, reactionTime]
        """
        theImage = ImageStim(self.window)
        #Set the full path of the image, based on the image's lure type
        if (image[0][5] == "3"):
            image = (self.imgSnglDir + '%s' %(image[0]))
        elif ((image[0][5] == "1") or (image[0][5] == "2")):
            image = (self.lureHighDir + '%s' %(image[0]))
        elif ((image[0][5] == "4") or (image[0][5] == "5")):
            image = (self.lureLowDir + '%s' %(image[0]))

        theImage.setImage(image)
        imageSize = self.ScaleImage(image, self.imageWidth)
        theImage.setSize(imageSize)

        ecogISI = 0.5
        posLeftText = (-(self.window.size[0]/8), 0)
        posRightText = ((self.window.size[0]/8), 0)
        if (phase == 0):
            ecogTrialDur = 2.0
            leftMsg = "Indoor\n\n    1"
            rightMsg = "Outdoor\n\n     2"
        else:
            ecogTrialDur = 1.0
            leftMsg = "Old\n\n  1"
            rightMsg = "New\n\n  2"

        theImage.draw(self.window)
        self.blackBox.draw(self.window)
        self.window.flip()
        wait(ecogTrialDur,ecogTrialDur)
        self.window.flip()
        wait(ecogISI, ecogISI)
        textLeft = TextStim(self.window, text=leftMsg, pos=posLeftText, 
                            color='Black', height=50)
        textRight = TextStim(self.window, text=rightMsg, pos=posRightText,
                             color='Black', height=50)
        textLeft.draw(self.window)
        textRight.draw(self.window)
        self.window.flip()
        clearEvents()
        self.clock.reset()
        keyPresses = waitKeys(keyList=['1','2','space','escape'],
                              timeStamped=self.clock, maxWait=1.5)
        self.window.flip()
        random.shuffle(self.rangeITI)
        wait(self.rangeITI[0],self.rangeITI[0])

        if (not keyPresses):
            return '',0
        return keyPresses[0][0],keyPresses[0][1]

    def RunTrial(self, image):
        """Runs a particular trial, which includes displaying the image to the
        screen, and gathering the keypresses and their respective response times. 

        image: the image (filename) to display
        returns: [keyPress, reaction time]
        """
        theImage = ImageStim(self.window)
        imagePath = os.path.normpath(self.imgDir + "/%s" %(image))

        theImage.setImage(imagePath)
        imageSize = self.ScaleImage(imagePath, self.imageWidth)
        theImage.setSize(imageSize)
        theImage.draw(self.window)
        self.window.flip()
        clearEvents()
        self.clock.reset()
        keyPresses = []
        if (self.selfPaced == False):
            wait(self.trialDuration,self.trialDuration)
            keyPresses = getKeys(keyList=[self.leftButton, self.rightButton,self.pauseButton,'escape'],
                                 timeStamped=self.clock)
        elif (self.selfPaced == True):
            keyPresses = waitKeys(keyList=[self.leftButton, self.rightButton,self.pauseButton,'escape'],
                                timeStamped=self.clock)
        self.window.flip()
        wait(self.ISI)
        if (not keyPresses):
            return '',0
        return keyPresses[0][0],keyPresses[0][1]
        
    def RunStudy(self):
        """Runs the first part of the MDT-O experiment, or the Study phase.
        In this phase, all target versions of the image pairs are shown, as
        well as half of the "singles" images. Keypresses and their repsective
        reaction times are recorded during this period, and no "right or
        wrong" answers are graded.
        """
        ecog = False if self.expVariant != "ECog" else True
        studyPromptN = ("Let's do the real test. \n\n Are the following objects indoor or outdoor? \n\n Press 'p' to continue"
                       )
        '''
        studyPromptE = ("In the following phase, a sequence of images will be "
                        "shown.\n\n-Press '1' if the image is of an indoor "
                        "object.\n\n-Press '2' if the image is of an outdoor "
                        "object.\n\n\nPress space to begin"
                       )
        ''' 
        studyText = TextStim(self.window,studyPromptN,color='Black')
        if ecog:
            studyText = TextStim(self.window,studyPromptE,color='Black')
        studyText.draw(self.window)
        self.window.flip()
        continueKey = waitKeys(keyList=[self.pauseButton,'escape'])
        if (continueKey[0] == 'escape'):
            self.logfile.write("\n\n\nStudy Not Run\n\n")
            return 0

        self.logfile.write("\nBegin Study\n\n")
        logStudyFormat = '{:<7}{:<12s} {:<10s} {:<10s} {:<4s}\n'.format(
                         'Trial','Image','ImageType','Response','RT')
        self.logfile.write(logStudyFormat)
        
        #Create list for study: "A" pairs (targets), and repeat singles
        studyImgList = []
        for pair in self.splitLures:
            studyImgList.append([pair[0],pair[0][5]])
        for img in self.splitSingles:
            if (img[1] == "sR"):
                studyImgList.append(img)

        #Shuffle study list
        random.shuffle(studyImgList)

        #Run trial for each study image
        for i in range(0, len(studyImgList)):
            if not ecog:
                (response, RT) = self.RunTrial(studyImgList[i][0])
            else:
                (response, RT) = self.RunTrialECog(studyImgList[i][0], 0)
            if (response == "escape"):
                self.logfile.write("\n\nStudy terminated early\n\n")
                return 0
            elif (response == self.pauseButton):
                self.Pause()

            trialFormat = '{:<7}{:<17s}{:<10s}{:<6s}{:<4.3f}\n'.format(
                    i+1, studyImgList[i][0],studyImgList[i][1],response,RT)
            self.logfile.write(trialFormat)
        
        return 1
        
    def RunTest(self):
        """Runs the second part of the MDT-O experiment, or the Test phase.
        In this phase, high and low "lures" are shown, as well as all of the
        "singles" shown in the study phase, as well as entirely new images
        known as "foils".

        All keypresses and their respective reaction times are recorded during
        this period. Additionally, a tally is kept of whether the subjects
        answer was wrong or right, with a separate score for "pair" answers.
        """
        ecog = False if self.expVariant != "ECog" else True
        testPromptN = ("In this phase, another sequence of images will be shown"
                      "\n\nAre the objects old or new?\n\n Press 'p' to continue."
                      )
        '''testPromptE = ("In this phase, another sequence of images will be shown."
                      "\n\n-Press '1' if the image presented was also shown "
                      "in the previous phase. (Old Image)\n\n-Press '2' if the" 
                      "image presented was not shown in the previous phase."
                      " (New Image)\n\n\nPress space to begin"
                      )
        '''
        testText = TextStim(self.window,text=testPromptN,color='Black')
        if ecog:
            testText = TextStim(self.window,text=testPromptE,color='Black')
        
        testText.draw(self.window)
        self.window.flip()
        continueKey = waitKeys(keyList=[self.pauseButton,'escape'])
        if (continueKey[0] == 'escape'):
            self.logfile.write("\n\n\nTest Not Run\n\n")
            return 0

        self.logfile.write("\nBegin Test\n\n")
        logTestFormat = '{:<7}{:<12}{:<11}{:<9}{:<10}{:<4}\n'.format(
            'Trial','Image','ImageType','CorResp','Response','RT')
        self.logfile.write(logTestFormat)

        #Create trial list for test: B and C lures, and all singles
        testImgList = []
        for pair in self.splitLures:
            testImgList.append([pair[1],pair[1][5]])
        for img in self.splitSingles:
            testImgList.append(img)

        #Shuffle trial list
        random.shuffle(testImgList)

        #Run trial for each image in list, get responses
        for i in range(0, len(testImgList)):

            correct = self.rightButton
            trialType = testImgList[i][1]
            if (trialType == "sR"):
                correct = self.leftButton
            if not ecog:
                (response, RT) = self.RunTrial(testImgList[i][0])
            else:
                (response, RT) = self.RunTrialECog(testImgList[i][0], 1)
            if (response == "escape"):
                self.logfile.write("\n\nTest terminated early\n\n")
                break
            elif (response == self.pauseButton):
                self.Pause()

            trialFormat = '{:<7}{:<15}{:<11}{:<9}{:<6}{:<4.3f}\n'.format(
                i+1,testImgList[i][0],testImgList[i][1],correct,response,RT)
            self.logfile.write(trialFormat)

            #Tally scores of correct/responses
            if (response):
                if (trialType == "sR"):
                    self.scoreList[0][2] += 1
                    if (response == correct):
                        self.scoreList[0][0] += 1
                    else:
                        self.scoreList[0][1] += 1
                elif (trialType == "1"):
                    self.scoreList[1][2] += 1
                    if (response == correct):
                        self.scoreList[1][0] += 1
                    else:
                        self.scoreList[1][1] += 1
                elif (trialType == "2"):
                    self.scoreList[2][2] += 1
                    if (response == correct):
                        self.scoreList[2][0] += 1
                    else:
                        self.scoreList[2][1] += 1
                elif (trialType == "sF"):
                    self.scoreList[3][2] += 1
                    if (response == correct):
                        self.scoreList[3][0] += 1
                    else:
                        self.scoreList[3][1] += 1

        return 1
    

    def ShowPromptAndWaitForSpace(self, prompt, keylist=['p', 'escape']):
        '''
        Show the prompt on the screen and wait for space, or the keylist specified
        returns the key pressed
        '''
        keylist = [self.pauseButton, 'escape']
        text = TextStim(self.window,prompt,color='Black')
        text.draw(self.window)
        self.window.flip()
        continueKey = waitKeys(keyList=keylist)
        if len(continueKey) != 0 and continueKey[0] == 'escape':
            self.logfile.write("Terminated early.")
            self.logfile.close()
            sys.exit()
        return continueKey

    def RunSinglePractice(self, practiceBlock, images):
        '''
        Read in the images we want, and run the practice block for this subject
        
        Run encoding and test, and write to the logs 
        
        Return:
           float: ratio correct
        '''
        imgPairs = []
        for i in range(0, len(images)-1, 2):
            if "foil" in images[i]:
                t = "sF"
            elif "target" in images[i]:
                t = "sR"
            elif "high" in images[i]:
                t = "2"
            elif "low" in images[i]:
                t = "1"
            imgPairs.append([images[i],images[i+1], t])

        ### Encoding
        self.ShowPromptAndWaitForSpace(" Outdoor or Indoor? ('{}' to continue)".format(self.pauseButton))
        random.shuffle(imgPairs)
        
        self.logfile.write("\nBegin Practice Encoding {}\n\n".format(practiceBlock))
        logPracticeFormat = '{:<7}{:<17}{:<11}{:<9}{:<10}{:<4}\n'.format(
            'Trial','Image','ImageType','CorResp','Response','RT')
        self.logfile.write(logPracticeFormat)
        
        # Run the trial for each encoding trial
        for i, trial in enumerate(imgPairs):
            imgA, imgB, trialType = trial
            if trialType != 'sF':
                response, RT = self.RunTrial(imgA)
                
                if (response == 'escape'):
                    self.logfile.write("\n\nPractice block terminated early\n\n")
                    self.logfile.close()
                    sys.exit()
                elif (response == self.pauseButton):
                    self.Pause()

                trialFormat = '{:<7}{:<17}{:<11}{:<9}{:<6}{:<4.3f}\n'.format(
                    i+1,imgA,trialType,'',response,RT)
                self.logfile.write(trialFormat)


        ### Test
        self.ShowPromptAndWaitForSpace(" Old or new? ('{}' to continue)".format(self.pauseButton))
        random.shuffle(imgPairs)

        self.logfile.write("\nBegin Practice Test {}\n\n".format(practiceBlock))
        self.logfile.write(logPracticeFormat)

        # Keep track of the total number they got correct
        totalCorrect = 0
        for i, trial in enumerate(imgPairs):
            imgA, imgB, trialType = trial
            if trialType == 'sR' or trialType == 'sF':
                response, RT = self.RunTrial(imgA)
            else:
                response, RT = self.RunTrial(imgB)
                    
            correct = self.leftButton if trialType == 'sR' else self.rightButton
            if response == correct:
                totalCorrect += 1
            if (response == "escape"):
                self.logfile.write("\n\nPractice terminated early\n\n")
                return -1
            elif (response == self.pauseButton):
                self.Pause()

            trialFormat = '{:<7}{:<17}{:<11}{:<9}{:<6}{:<4.3f}\n'.format(
                i+1,imgA,trialType,correct,response,RT)
            self.logfile.write(trialFormat)
            
        # Return the percentage correct
        return totalCorrect / len(imgPairs)

    def RunPractice(self):
        '''
        Runs three rounds of practice trials. 
        If the participant gets a certain amount correct, they move on to the real test.
        '''
        
        dirFiles = os.listdir(self.imgDir)
        practiceImages = [img for img in dirFiles if "PR" in img]
        
        # Run each practice session
        for i in range(3):
            practicePrompt = "Let's practice. ('{}' to continue)".format(self.pauseButton)
            self.ShowPromptAndWaitForSpace(practicePrompt)
            
            imagesThisPracticeSession = sorted([img for img in practiceImages if "Set_{}".format(i+1) in img])
            results = self.RunSinglePractice(i+1, imagesThisPracticeSession)
            
            # If they get a certain percentage correct, then stop the practice
            self.ShowPromptAndWaitForSpace("You got {}% correct! ('{}' to continue)".format(int(results*100), self.pauseButton))
            if results > .6:
                return


    def RunExp(self):
        """Run through an instance of the task, which includes the study and test
        phases. Also prints the exit message at the end, and closes the logfile
        if scores are not being written to it.

        return: (logfile, scorelist) if the test was run through. Assuming this
                happens, scores will be written to the logfile
        return: (-1,-1) if the task was quit prior to the completion of the
                study phase, meaning scores will not be writtent to the logfile
        """

        #Print task ending message to the screen, and wait escape to be prssed
        def EndExp():
            exitPrompt = ("This concludes the session. Thank you for "
                          "participating!\n\nPress Esc to quit")
            exitText = TextStim(self.window, exitPrompt, color='Black')
            exitText.draw(self.window)
            self.window.flip()
            waitKeys(keyList=['escape'])
            self.window.close()

        # Show main welcome window
        welcomePrompt = "Thank you for participating in our study! Press '{}' to begin".format(self.pauseButton)
        self.ShowPromptAndWaitForSpace(welcomePrompt)
        
        # If run practice trials, then RunPractice
        if self.runPracticeTrials:
            self.RunPractice()
        
        #Run study, terminate if user exits early
        studyFinished = self.RunStudy()
        testFinished = self.RunTest()

        if (not studyFinished):
            EndExp()
            self.logfile.close()
            return (-1,-1)

        EndExp()
        return (self.logfile, self.scoreList)
