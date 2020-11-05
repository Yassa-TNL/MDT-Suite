"""MDTT, or MDT-Temporal, is a task run to test a subject's memory based on
sequencing, or the order in which objects appear. In this task, multiple 
"blocks" consisting of study and test phases are run. In each study phase,
a series of 32 images are shown. In the test phase, two images are shown side
by side, both of which were shown in the preceding study phase.

In each test phase, the subject must determine which image (the one on the left
or right) was shown first in the preceding study phase. Four "types" of 
trials can be shown during the test phase, each based on the relative
positioning of the objects in the sequence of the preceding study phase: images
that were next or adjacent to eachother, images shown between 7-9 images apart,
images shown between 15-17 images apart, and the first 4 vs last 4 images
shown.

The task keeps track of the subject's responses to each trial, and writes their
scores to a logfile at the completion of the task.
"""

from __future__ import division
import os,sys,math,random
from psychopy.visual import Window, ImageStim, TextStim
from psychopy.event import clearEvents, getKeys, waitKeys
from psychopy.core import Clock, wait
import numpy as np

class MDTT(object):

    def __init__(self, logfile, imgDir, subjectNum, screenType, numStim, 
                 numBlocks, trialDuration, ISI, selfPaced, runPractice, inputButtons, pauseButton):

        self.logfile = logfile
        self.imgDir = imgDir
        self.subjectNum = subjectNum
        self.numStim = numStim
        self.numBlocks = numBlocks
        self.trialDuration = trialDuration
        self.selfPaced = selfPaced
        self.ISI = ISI
        self.numCats = 4
        self.trialsPer = int((self.numStim / self.numCats) / 2)
        self.runPractice = runPractice
        self.leftButton  = inputButtons[0]
        self.rightButton = inputButtons[1]
        self.pauseButton = pauseButton

        #Set up window, center, left and right image sizes + positions

        if (screenType == 'Windowed'):
            screenSelect = False
        elif (screenType == 'Fullscreen'):
            screenSelect = True

        self.window = Window(fullscr=screenSelect,units='pix', 
                             color='White',allowGUI=False)
        self.imageWidth = self.window.size[1]/5.5
        self.centerImage = ImageStim(self.window)
        self.centerImage.setSize((self.imageWidth,self.imageWidth))
        self.leftImage = ImageStim(self.window)
        self.leftImage.setPos((-1.5 * self.imageWidth,0))
        self.leftImage.setSize((self.imageWidth,self.imageWidth))
        self.rightImage = ImageStim(self.window)
        self.rightImage.setPos((1.5 * self.imageWidth,0))
        self.rightImage.setSize((self.imageWidth,self.imageWidth))
        self.clock = Clock()

        #Init score list for 4 categories: [correct,incorrect,response]
        self.scoreList = []
        for i in range(0,4):
            self.scoreList.append([0,0,0])

    def SplitRange(self, rangeMin, rangeMax, start=0):
        """Creates a pair of indexes separated by a value. The value itself
        can be between a min-max range. Neither index can be an index that is
        in a list of already used indexes.

        rangeMin: minimum amount that indexes can be separated by
        rangeMax: maximum amount that indexes can be separated by
        start: start index of used list 
        return: a pair of indexes (index1,index2)
                (-1,-1) if range split failed
        """

        #Search through list of used indexes to ensure no duplicates
        #Ignore start/end of list, as it's already used by primacy/recency
        for i in range(0, self.numStim):
            if (i in self.usedList):
                continue
            added = random.randint(rangeMin, rangeMax)
            startPt = added
            searchedRange = False
            #Loop through the min to max range of added values
            while not searchedRange:
                if ((i+added<self.numStim) and (i+added not in self.usedList)):
                    self.usedList.append(i)
                    self.usedList.append(i+added)
                    return (i, i+added)    
                if (added > rangeMin):
                    added -= 1
                else:
                    added = rangeMax
                if (added == startPt):
                    searchedRange = True
        return (-1,-1)    


    def CreatePairsSpaced(self):
        """Creates a list, each element containing two indexes as well as a
        trial type. The trial type is based upon the spacing of the indexes as
        follows:

        adjacent (1): numbers next to eachother e.g. (3,4) or (8,9)
        eightish (2): numbers separated by between 7-9 e.g. (5,12) or (14,23)
        sixteenish (3): numbers separated by between 15-17 e.g. (3,18) or (8,25)
        primacy/recency: (4): start and end of list numbers e.g. (1,30) or (0,31)

        Occassionally, the list will fail to successfully split into index pairs.
        (SplitRange() returns (-1,-1) when this happens). The function will retry 
        the index splitting until all indexes are used

        return: list containing elements each with: (index1,index2,trialType)
        """

        startList = range(0,self.trialsPer)
        endList = range(self.numStim - self.trialsPer,self.numStim)
        trialOrder = range(0,(self.trialsPer * 3)) #3 categories besides P/R
        random.shuffle(startList)
        random.shuffle(endList)

        #Attempt to split 0-31 range into 4 index categories
        #Split fails if any one of the index pairs is (-1,-1) at end
        def AttemptSplit():

            # 3 categories besides P/R
            trialOrder = range(0,(self.trialsPer * 3)) 
            random.shuffle(trialOrder)
            self.usedList = []    
            attemptList = []
            finalList = []

            #Add edge index pairs (primacy/recency) 
            for i in range(0, self.trialsPer):
                finalList.append((startList[i],endList[i],4))
                self.usedList.append(startList[i])
                self.usedList.append(endList[i])        

            #Add spaced (separated) pairs of indexes to list 
            for trial in trialOrder:
                if (trial % 3 == 0):                            #Adjacent
                    (idxOne, idxTwo) = self.SplitRange(1,1)
                    attemptList.append((idxOne, idxTwo, 1))        
                elif (trial % 3 == 1):                            #Eightish
                    (idxOne, idxTwo) = self.SplitRange(7,9)
                    attemptList.append((idxOne, idxTwo, 2))
                elif (trial % 3 == 2):                            #Sixteenish
                    (idxOne, idxTwo) = self.SplitRange(15,17)
                    attemptList.append((idxOne, idxTwo, 3))

            #Ensures PR trials (type 4) occur first. Randomize successive trials
            random.shuffle(attemptList)
            finalList.extend(attemptList)
            return finalList

        #Try AttemptSplit() until index split is successful
        splitSuccess = False
        while (not splitSuccess):
            splitList = AttemptSplit()
            foundError = False
            for pair in splitList:
                if ((pair[0] == -1) or (pair[1] == -1)):
                    foundError = True
            if (foundError == True):
                continue
            else:
                splitSuccess = True

        return splitList


    def RunTrialSingle(self, img):
        """Displays a single image at the center of the screen for a period of
        time, and captures keypresses and their respective reaction times.

        img: the image to Displays
        return: a list of keypresses and respective reaction times
        """
        self.centerImage.setImage(self.imgDir + "/%s" %(img))
        self.centerImage.draw(self.window)
        clearEvents()
        self.window.flip()
        self.clock.reset()
        keyPresses = []
        if (self.selfPaced == False):
            wait(self.trialDuration,self.trialDuration)
            keyPresses = getKeys(keyList=[self.leftButton,self.rightButton,self.pauseButton,"escape"],timeStamped=self.clock)
        elif (self.selfPaced == True):
            keyPresses = waitKeys(keyList=[self.leftButton,self.rightButton,self.pauseButton,"escape"],timeStamped=self.clock)
        self.window.flip()
        wait(self.ISI)
        return keyPresses


    def RunTrialDual(self, leftImg, rightImg):
        """Displays two images on the screen for a period of time, and captures
        keypresses and their respective reaction times.

        leftimg: the image to display on the left
        rightimg: the image to display on the right
        return: a list of keypresses and respective reaction times
        """
        self.leftImage.setImage(self.imgDir + "/%s" %(leftImg))
        self.rightImage.setImage(self.imgDir + "/%s" %(rightImg))
        self.leftImage.draw(self.window)
        self.rightImage.draw(self.window)
        clearEvents()
        self.window.flip()
        self.clock.reset()
        if (self.selfPaced == False):
            wait(self.trialDuration,self.trialDuration)
            keyPresses = getKeys(keyList=[self.leftButton,self.rightButton,self.pauseButton,"escape"],timeStamped=self.clock)
        elif (self.selfPaced == True):
            keyPresses = waitKeys(keyList=[self.leftButton,self.rightButton,self.pauseButton,"escape"],timeStamped=self.clock)
        self.window.flip()
        wait(self.ISI)
        return keyPresses


    def RunStudy(self, imageBlock, session):
        """Runs the study, i.e. the first half of each experimental block.
        Writes all relevant information about the study to a logfile.

        imageBlock: List of images to display during the study
        session: the number of the session (block number) that is running
        """
        studyPrompt = ("Test Session {}/{}: Are the following objects indoor or outdoor?\n\n('{}' to continue)".format(session, 10, self.pauseButton))
        studyText = TextStim(self.window,studyPrompt,color='Black')
        studyText.draw(self.window)
        self.window.flip()
        continueKey = waitKeys(keyList=[self.pauseButton,'escape'])

        if (continueKey[0] == 'escape'):
            self.logfile.write("\n\n\nStudy Not Run Early\n\n\n")
            return 

        self.logfile.write("\nBegin Study %d\n" %(session))
        self.logfile.write("{h1:<6}{h2:<23}{h3:<10}{h4}\n".format(
            h1="Trial",h2="Image",h3="Response",h4="RT"))
        
        #Run trial for each image in the image block
        for i in range(0, len(imageBlock)):
            keyPresses = self.RunTrialSingle(imageBlock[i])
            if (keyPresses == []):
                respKey = ''
                respRT = 0
            else:
                respKey = keyPresses[0][0]
                respRT = keyPresses[0][1]
            if (respKey == "escape"):
                self.logfile.write("\n\n\nStudy block terminated early\n\n\n")
                break
            elif (respKey == self.pauseButton):
                self.Pause()
                
            self.logfile.write("{:^5}{:<23}{:^11}{:<1.3f}\n".format(
                i+1,imageBlock[i],respKey,respRT))

        return


    def RunTest(self, imageBlock, pairList, session):
        """Runs the test, i.e. the second half of each experimental block.
        Wites all relevant information about the test to a logfile

        imageBlock: List of images to display during the test
        pairList: List of paired image indexes w/ trial type
        session: the number of the session (block number) that is running
        """
        testPrompt = ("In this phase, the same series of objects will be shown\n\nWhich came first: Left or Right?\n\n('{}' to continue)".format(self.pauseButton))
        testText = TextStim(self.window,testPrompt,color='Black')
        testText.draw(self.window)
        self.window.flip()
        continueKey = waitKeys(keyList=[self.pauseButton,'escape'])

        if (continueKey[0] == 'escape'):
            self.logfile.write("\n\n\nTest Not Run\n\n\n")
            return 0

        self.logfile.write("\nBegin Test %d\n" %(session))
        lghead = "{a:<7}{b:<7}{c:<23}{d:<23}{e:<7}{f:<7}{g:<10}{h:<7}{i}\n".format(
            a="Trial",b="TType",c="LeftImage",d="RightImage",e="LNum",
            f="RNum",g="CorResp",h="Resp",i="RT")
        self.logfile.write(lghead)

        #Randomize if pair is shown: (bef > aft) or (aft > bef) order
        sideOrder = range(0,len(pairList))
        random.shuffle(sideOrder)
        correct = ''
        keyPresses = []

        #Run dual image trial for each pair in the pairlist
        for i in range(0,len(pairList)):
            trialNum = i + 1
            trialType = pairList[i][2]
            firstIdx = pairList[i][0]
            secondIdx = pairList[i][1]
            firstImg = imageBlock[pairList[i][0]]
            secondImg = imageBlock[pairList[i][1]]
            
            #Preserve the order images were shown in
            if (sideOrder[i] % 2 == 0):
                correct = self.leftButton
                leftIdx = firstIdx
                rightIdx = secondIdx
                leftImg = firstImg
                rightImg = secondImg
                keyPresses = self.RunTrialDual(leftImg, rightImg)
            #Reverse order images were shown
            elif (sideOrder[i] % 2 == 1):
                correct = self.rightButton
                leftIdx = secondIdx
                rightIdx = firstIdx
                leftImg = secondImg
                rightImg = firstImg
                keyPresses = self.RunTrialDual(leftImg, rightImg)

            #Get first response, or set to none if no response
            if (keyPresses == []):
                respKey = ''
                respRT = 0
            else:
                respKey = keyPresses[0][0]
                respRT = keyPresses[0][1]
            #Break out of image block with escape, break out of program with f5
            if (respKey == 'escape'):
                self.logfile.write("\n\nTest block terminated early\n\n")
                break     
            elif (respKey == self.pauseButton):
                self.Pause()
                
            #Keep track of score
            if (respKey):
                self.scoreList[pairList[i][2]-1][2] += 1
                if (respKey == correct):
                    self.scoreList[pairList[i][2]-1][0] += 1
                else:
                    self.scoreList[pairList[i][2]-1][1] += 1

            #Write info to logfile
            lgspace = "{:^5}{:^9}{:<23}{:<23}{:<7}{:<10}{:<8}{:<6}{:<1.3f}\n"
            lgform = (lgspace.format(trialNum,trialType,leftImg,rightImg,
                                     leftIdx,rightIdx,correct,respKey,respRT))
            self.logfile.write(lgform)

        return 1

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

    def SegmentPracticeImages(self, images):
        '''
        Return the indexes for the test, it will index the image list from study:
            [[index_left_image, index_right_image, trialType]]
        '''
        # Since we know that the images are already randomized, we can just iterate over them
        # In order for the code to work, we want 4 practice images per practice block
        if len(images) != 4:
            print "Assertion error: length of practice images is not equal to 4"
            self.window.close()
            sys.exit()
        
        # Trial type of 4 means long distance
        large_dist = (0,3,4) if random.random() > .5 else (3,0,4)
        mid_dist_1 = (0,2,2) if random.random() > .5 else (2,0,2)
        mid_dist_2 = (1,3,2) if random.random() > .5 else (3,1,2)
        adjacent   = (0,1,1) if random.random() > .5 else (1,0,1)
        adjacent_2 = (1,2,1) if random.random() > .5 else (2,1,1)
        adjacent   = adjacent if random.random() > .5 else adjacent_2
        
        all = [large_dist, mid_dist_1, mid_dist_2, adjacent]
        random.shuffle(all)
        
        return all
        
    def ShowPromptAndWaitForSpace(self, prompt, keylist=['space', 'escape']):
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
        
    def RunSinglePractice(self, practiceBlock, imgs):
        '''
        Read in the images we want, and run the practice block for this subject
        Run encoding and test, and write to the logs 
        
        Return:
           float: ratio correct
        '''
        random.shuffle(imgs)

        ### Encoding
        # imgs = [[img, trialType, Study(x,y), Test(x,y)]]
        testIdxs = self.SegmentPracticeImages(imgs)
        
        self.ShowPromptAndWaitForSpace(" Indoor or Outdoor?\n\n('{}' to continue)".format(self.pauseButton))
        
        self.logfile.write("\nBegin Practice Study {}\n".format(practiceBlock))
        self.logfile.write("{h1:<6}{h2:<23}{h3:<10}{h4}\n".format(
            h1="Trial",h2="Image",h3="Response",h4="RT"))
        
        # Run the trial for each encoding trial
        for i in range(0, len(imgs)):
            keyPresses = self.RunTrialSingle(imgs[i])
            if (keyPresses == []):
                respKey = ''
                respRT = 0
            else:
                respKey = keyPresses[0][0]
                respRT = keyPresses[0][1]
            if (respKey == "escape"):
                self.logfile.write("\n\n\nStudy block terminated early\n\n\n")
                break
            elif (respKey == self.pauseButton):
                self.Pause()
                
            self.logfile.write("{:^5}{:<23}{:^11}{:<1.3f}\n".format(
                i+1,imgs[i],respKey,respRT))
                
                
        ### Test
        self.ShowPromptAndWaitForSpace(" Which came first? Left or right? ('{}' to continue)".format(self.pauseButton))
        
        self.logfile.write("\nBegin Practice Test {}\n".format(practiceBlock))
        self.logfile.write("{a:<7}{b:<7}{c:<23}{d:<23}{e:<7}{f:<7}{g:<10}{h:<7}{i}\n".format(
            a="Trial",b="TType",c="LeftImage",d="RightImage",e="LNum",
            f="RNum",g="CorResp",h="Resp",i="RT"))
        
        # Keep track of the total number they got correct
        totalCorrect = 0
        for trialNum, idxes in enumerate(testIdxs):
            leftImgIdx, rightImgIdx, trialType = idxes
            
            leftImg = imgs[leftImgIdx]
            rightImg = imgs[rightImgIdx]
            
            keyPresses = self.RunTrialDual(leftImg, rightImg)
            correct = self.leftButton if leftImgIdx < rightImgIdx else self.rightButton

            #Get first response, or set to none if no response
            if (keyPresses == []):
                respKey = ''
                respRT = 0
            else:
                respKey = keyPresses[0][0]
                respRT = keyPresses[0][1]
            #Break out of image block with escape, break out of program with f5
            if (respKey == 'escape'):
                self.logfile.write("\n\nPractice block terminated early\n\n")
                self.logfile.close()
                sys.exit()
             
            #Write info to logfile
            lgspace = "{:^5}{:^9}{:<23}{:<23}{:<7}{:<10}{:<8}{:<6}{:<1.3f}\n"
            lgform = (lgspace.format(trialNum+1,trialType,leftImg,rightImg,
                                     leftImgIdx,rightImgIdx,correct,respKey,respRT))
            self.logfile.write(lgform)
            
            if respKey == correct:
                totalCorrect += 1
            
        # Return the percentage correct
        return totalCorrect / len(imgs)

    def RunPractice(self):
        '''
        Runs three rounds of practice trials. 
        If the participant gets a certain amount correct, they move on to the real test.
        '''
        
        dirFiles = os.listdir(self.imgDir)
        practiceImages = [img for img in dirFiles if "PR_" in img]
        if len(practiceImages) == 0:
            print "No practice images found"
            self.window.close()
            sys.exit()
            
        random.shuffle(practiceImages)
        
        # Split the practice images into three sets
        practiceImages = np.array_split(practiceImages, 3)

        # Run each practice session
        for i in range(3):
            practicePrompt = "Let's practice\n\n('{}' to continue)".format(self.pauseButton)
            self.ShowPromptAndWaitForSpace(practicePrompt)
            
            results = self.RunSinglePractice(i+1, [img for img in practiceImages[i]])
            
            # If they get a certain percentage correct, then stop the practice
            self.ShowPromptAndWaitForSpace("You got {}% correct! ('{}' to continue)".format(int(results*100), self.pauseButton))
            if results > .6:
                return

    def RunExp(self):
        """Runs through an instance of the MDT-T experiment, which includes
        arranging the images into lists/sublists, running through a given
        number of study/test blocks, and writing the scores to a logfile. 
        """

        #Print task ending message to the screen; wait for user to press escape
        def EndExp():
            exitPrompt = ("This concludes the session. Thank you for "
                          "participating!\n\nPress Escape to quit")
            exitText = TextStim(self.window,exitPrompt,color='Black')
            exitText.draw(self.window)
            self.window.flip()
            waitKeys(keyList=['escape'])
            self.window.close()

        # Run practice
        if self.runPractice:
            self.RunPractice()

        #Put image files from folder into list
        imageList = []
        for img in os.listdir(self.imgDir):
            if ( img[-4:] == ".jpg" and "PR_" not in img): # Make sure that PR (practice image) is not included for study/tests
                imageList.append(img)
        random.shuffle(imageList)

        #Divide imagelist into <numBlocks> # of lists, put into one list
        #Each sublist contains <numStim> # of stimuli
        imageBlockList = []
        for i in range(0,self.numBlocks):
            block = []
            for j in range(i*self.numStim, self.numStim + (i*self.numStim)):
                block.append(imageList[j])
            imageBlockList.append(block)

        #Run through each study/test block
        blockOrder = range(0, self.numBlocks)
        random.shuffle(blockOrder)
        writeScores = True
        for i in range(0,len(blockOrder)):
            pairList = self.CreatePairsSpaced()
            self.RunStudy(imageBlockList[i], i+1)
            testFinished = self.RunTest(imageBlockList[i], pairList, i+1)
            if not testFinished:
                writeScores = False
                continue

        EndExp()
        #Return logfile and scorelist if all study/test blocks gone through
        if writeScores:
            return (self.logfile, self.scoreList)
        else:
            return (-1, -1)
        
