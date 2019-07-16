"""MDTS, or MDT-Spatial, is a task run to test a subject's memory based on
object positioning. In this task, a series of images shown to the subject
two times, once in a study phase, and again in a test phase. From the
study to test phase, an image's location on screen can change, by varying
degrees: it can either stay in the same position, move a slight amount,
move a larger amount, or move the maximum distance (from corner to opposite
corner of the window).

During the test phase, the subject is asked to determine whether the image
has moved or stayed in the same position. The general idea is that the closer
the image was to its starting position, the more difficult it will be for
the subject to determine if it was actually in the same position. The task 
keeps track of the subject's responses, and writes their score to a logfile
at the completion of the task.
"""

from __future__ import division
import os,sys,math,random
from psychopy.visual import Window, ImageStim, TextStim, Circle, ShapeStim
from psychopy.event import clearEvents, getKeys, waitKeys
from psychopy.core import Clock, wait
import numpy as np

class MDTS(object):

    def __init__(self, logfile, imgDir, screenType, 
                 trialDuration, ISI, trialsPer, selfPaced, practiceTrials, inputButtons):

        self.logfile = logfile
        self.trialDuration = trialDuration
        self.selfPaced = selfPaced
        self.ISI = ISI
        self.trialsPer = trialsPer
        self.numTrials = (self.trialsPer * 4)  #Trials/phase = 4x trials/cond
        self.imgDir = imgDir
        self.imgIdx = 0
        self.runPracticeTrials = practiceTrials
        self.leftButton  = inputButtons[0]
        self.rightButton = inputButtons[1]


        if (screenType == 'Windowed'):
            screenSelect = False
        elif (screenType == 'Fullscreen'):
            screenSelect = True
        self.window = Window(fullscr=screenSelect,units='pix', 
                             color='White',allowGUI=False)
        self.imageWidth = self.window.size[1]/6

        #Window must be set up before imgs, as img position based on window size
        self.imageList = self.SegmentImages()
        self.clock = Clock()

        #Initialize scorelist for 4 categories;; [correct,inc,resp]
        self.scoreList = []
        for i in range(0,4):
            self.scoreList.append([0,0,0])


    def CreatePosPair(self, moveType):
        """Generates two (x,y) coordinates to be associated with a particular
        image - the first being the study phase position, and second being the
        test phase position, which is a translation in any direction by 4
        degrees of distances - none, small, big, corner.

        moveType: the amount of relative distance across the screen to move
            -0: Non move (xA,yA) = (xB,yB)
            -1: Lure High: Max Distance / 3
            -2: Lure Low: (Max Distance*2) / 3
            -3: Opposite Corners: Max Distance
        return: a tuple of two coordinate pairs ((xA,yA),(xB,yB))
                (start position of img, end position of img) 
        """

        #Map a bottom left oriented coordinate system to a center oriented one
        def CoordMap(x,y):
            xM = int(x - winL/2)
            yM = int(y - winH/2)
            return (xM,yM)

        #Checks whether (x,y) coordinate is near corner
        def IsNearCorner(xTest,yTest):
            if ((xTest <= (x1+imgDis) and yTest <= (y1+imgDis)) or
                (xTest <= (x1+imgDis) and yTest >= (y2-imgDis)) or
                (xTest >= (x2-imgDis) and yTest <= (y1+imgDis)) or
                (xTest >= (x2-imgDis) and yTest >= (y2-imgDis))):
                return True
            else:
                return False

        #Generates a random point on a circle about (xA,yA) with a given radius
        def GenCoordMove(xA,yA,radius):
            deg = random.randint(0,359)
            rad = math.radians(deg)
            vecX = math.cos(rad)
            vecY = math.sin(rad)
            xR = int(radius * vecX)
            yR = int(radius * vecY)
            xB = xA + xR
            yB = yA + yR
            return (xB,yB)

        #Standard distance formula - use for diagnostics
        def Dist(x1,y1,x2,y2):
            return (math.sqrt(math.pow(x2-x1,2) + math.pow(y2-y1,2)))

        #Calculate the length, in pixels, of the small/large moves
        winL = self.window.size[0]
        winH = self.window.size[1]
        midDis = self.imageWidth / 2
        imgDis = self.imageWidth
        x2 = math.ceil(winL - midDis)
        x1 = math.floor(0 + midDis)
        y2 = math.ceil(winH - midDis)
        y1 = math.floor(0 + midDis)
        maxDis = math.sqrt(math.pow(x2-x1,2) + math.pow(y2-y1,2))
        distSmall = math.floor(maxDis / 4)
        distLarge = math.floor((maxDis*2) / 4)

        #Opposite corner condition: randomly choose 1 of 4 corner moves
        if (moveType == 3):
            corner = random.randint(0,3)
            if (corner == 0):   return (CoordMap(x2,y2),CoordMap(x1,y1))
            elif (corner == 1): return (CoordMap(x1,y2),CoordMap(x2,y1))
            elif (corner == 2): return (CoordMap(x1,y1),CoordMap(x2,y2))
            elif (corner == 3): return (CoordMap(x2,y1),CoordMap(x1,y2))

        #If not corner, generate random starting position and create
        #ending position based on 
        else:
            while(1):
                xT = random.randint(x1,x2)
                yT = random.randint(y1,y2)

                #Check that starting coorindates are not near corner
                if (IsNearCorner(xT,yT)): 
                    continue
                else: 
                    (xA,yA) = (xT,yT)
                
                if (moveType == 0):      #moveType (0): maintain same position
                    (xB,yB) = (xA,yA)
                elif (moveType == 1):    #moveType (1): small move (1/3 max dist)
                    (xB,yB) = GenCoordMove(xA,yA,distSmall)
                elif (moveType == 2):    #moveType (2): large move (2/3 max dist)
                    (xB,yB) = GenCoordMove(xA,yA,distLarge)

                #Redo random generation if ending coordinates are near corner
                if (IsNearCorner(xB,yB)): 
                    continue
                #Redo random generation if ending coordinates are out of bounds
                if ((xB<x1) or (xB>x2) or (yB<y1) or (yB>y2)): 
                    continue
                else:
                    return (CoordMap(xA,yA),CoordMap(xB,yB))


    def SegmentImages(self):
        """Shuffles images in a folder into a list, then successively adds
        two coordinate pairs to each image. The image list is divided into 4
        sections, one for each type of trial (repeat, move small, move big, and
        opposite corners). For each section of images, the images are given a
        corresponding type of coordinate pair as governed by createPosPair()

        return: createdList, each element as: [image,<study(x,y)>,<test(x,y)>]
        """    

        #Nested function - populates each division of the image list
        def SegmentFill(imageList, addingList, moveType):

            order = range(0,self.trialsPer)
            random.shuffle(order)
            for i in order:
                pospair = self.CreatePosPair(moveType)
                addingList.append([imageListSec[self.imgIdx],
                                   pospair[0],pospair[1]])
                self.imgIdx += 1
            return addingList

        imageListFull = []
        imageListSec = []
    
        #First put all available images into list and shuffle
        for i in os.listdir(self.imgDir):
            if i.lower().find('.jpg') != -1 and i.lower().find('PR_') == -1:
                imageListFull.append(i)
        random.shuffle(imageListFull)

        #Fill another list with the number of images per phase using prev list
        for j in range(0, self.numTrials):
            imageListSec.append(imageListFull[j])

        #Successively add each group of trials to madeImgList
        madeImgList = []
        addRepeatList = SegmentFill(imageListSec, madeImgList, 0)
        addLureSmall = SegmentFill(imageListSec, addRepeatList, 1)
        addLureLarge = SegmentFill(imageListSec, addLureSmall, 2)
        addCorners = SegmentFill(imageListSec, addLureLarge, 3)
        createdList = addCorners
        
        return createdList

    def ImageDiagnostic(self):
        """Draws colored dots onto the window. The dots' positions represent
        the respective location of where images will be placed throughout the
        course of the task.

        This function is to only be used as a diagnostic tool, so that one can
        get a general sense of where images might appear, without having to 
        actually run through the task. To use this function properly:
            taskSpatial = mdts.MDTS(...)
            taskSpatial.ImageDiagnostic
            #taskSpatial.RunExp()
        """
        win = self.window
        cRad = 50
        tp = self.trialsPer
        ls = self.imageList
        shapes = []
        leng = len(ls)
        for i in range(0,leng):
            color = "black"
            #print "{:<24}{:<15}{:<15}".format(img[0],img[1],img[2])
            img = ls[i]
            if i < tp:
                color = "black"
            elif (i > tp) and (i < tp*2):
                color = "blue"
            elif (i > tp*2) and (i < tp*3):
                color = "orange"
            elif i > tp*3:
                color = "green"

            shapes.append(Circle(win, radius=cRad, pos=img[1], fillColor=color))
            shapes.append(Circle(win, radius=cRad, pos=img[2], fillColor=color))
            shapes.append(ShapeStim(win, units='pix', lineWidth=5,
                lineColor=color, vertices=(img[1], img[2])))

            for shape in shapes:
                shape.draw(self.window)
            
            self.window.flip()
        waitKeys(keyList=['escape'])
        self.window.close()
        

    def RunTrial(self, image, pos):
        """Runs a particular trial, which includes displaying the image to the
        screen, and gathering the keypresses and their respective response times. 

        image: The filename of the image to display
        pos: Coordinates (on 6x4 grid) where image will be displayed
        return: tuple of first keypress info: (keyPress, reactionTime)
        """
        ShownImage = ImageStim(self.window)
        ShownImage.setPos(pos)
        ShownImage.setSize((self.imageWidth,self.imageWidth))
        ShownImage.setImage(self.imgDir + '/%s' %(image))
        ShownImage.draw(self.window)
        self.window.flip()
        clearEvents()
        self.clock.reset()
        keypresses = []
        if (self.selfPaced == False):
            wait(self.trialDuration,self.trialDuration)
            keypresses = getKeys(keyList=[self.leftButton,self.rightButton,"escape"],timeStamped=self.clock)
        elif (self.selfPaced == True):
            keypresses = waitKeys(keyList=[self.leftButton,self.rightButton,"escape"],timeStamped=self.clock)
        self.window.flip()
        wait(self.ISI)
        if len(keypresses) <1:
            return '',0
        return keypresses[0][0],keypresses[0][1]

    def ShowPromptAndWaitForSpace(self, prompt, keylist=['space']):
        '''
        Show the prompt on the screen and wait for space, or the keylist specified
        returns the key pressed
        '''
        text = TextStim(self.window,prompt,color='Black')
        text.draw(self.window)
        self.window.flip()
        continueKey = waitKeys(keyList=keylist)
        return continueKey

    def RunPhase(self, phaseType):
        """Runs a phase (study or test) of the task, which includes randomizing a 
        list of images, running trials for each of those images, writing
        trial information to a logfile for each trial ran, and keeping track of
        a subject's score, based on their response to each trial. 

        phaseType: 0 -> Run Study (use starting position of image)
                   1 -> Run Test (use ending position of image)
        return: 0 -> task terminated early
                1 -> task ran to completion 
        """

        studyPrompt = ("In the following phase, a sequence of images will be "
                       "shown.\n\n-Press the blue button if the image is of an indoor "
                       "object.\n\n-Press the red button if the image is of an outdoor "
                       "object.\n\n\nPress space to begin"
                       )
        testPrompt = ("In the following phase, another sequence of images will "
                      "be shown.\n\n-Press the blue button if the image is in the same "
                      "location as it was in the last phase.\n\nPress the red button if "
                      "the image is in a different location than it was in the "
                      "last phase.\n\n\nPress space to begin"
                       )
        studyText = TextStim(self.window,studyPrompt,color='Black')
        testText = TextStim(self.window,testPrompt,color='Black')

        if (phaseType == 0):
            studyText.draw(self.window)  #phaseType = 0 -> Study Phase
            self.window.flip()
            self.logfile.write("\nBegin Study\n")
        elif (phaseType == 1):
            testText.draw(self.window)   #phaseType = 1 -> Test Phase
            self.window.flip()
            self.logfile.write("\nBegin Test\n")

        log = self.logfile
        log.write("{a:<22}{b:<12}{c:<14}{d:<11}{e:<9}{f:<8}{g}\n".format(
            a='Image',b='Type',c='Start',d='End',e='Correct',f='Resp',g='RT'))

        continueKey = waitKeys(keyList=['space','escape'])
        if (continueKey[0] == 'escape'):
            self.logfile.write("\n\n\nPhase Not Run\n\n\n")
            return 0
            
        imgs = self.imageList
        trialOrder = range(0,len(imgs))
        random.shuffle(trialOrder)

        #Run through each trial
        for i in range(0, len(trialOrder)):

            imgIdx = trialOrder[i]
            correct = ""
            #Divide image index by the trials/cond, take floor for trial type
            trialFactor = int(math.floor(imgIdx/self.trialsPer))
            trialType = ""
            if (trialFactor == 0):
                trialType = "Same"
                if (phaseType == 1):
                    correct = self.leftButton
            elif (trialFactor == 1):
                trialType = "Small"
                if (phaseType == 1):
                    correct = self.rightButton
            elif (trialFactor == 2):
                trialType = "Large"
                if (phaseType == 1):
                    correct = self.rightButton
            elif (trialFactor == 3):
                trialType = "Crnr"
                if (phaseType == 1):
                    correct = self.rightButton

            #Display image in start position in study, end position in test
            if (phaseType == 0):
                (response, RT) = self.RunTrial(imgs[imgIdx][0],imgs[imgIdx][1])
            elif (phaseType == 1):
                (response, RT) = self.RunTrial(imgs[imgIdx][0],imgs[imgIdx][2])

            if (response == "escape"):
                self.logfile.write("\n\nPhase terminated early\n\n")
                break

            #Write formatted info about trial to logfile
            log.write("{:<22}{:<9}{:<14}{:<17}{:<7}{:<6}{:>0.3f}\n".format(
                imgs[imgIdx][0],trialType,imgs[imgIdx][1],imgs[imgIdx][2],
                correct,response, RT))
          
            #If in test phase, tally responses, correct + incorrect answers
            if (phaseType == 1):
                if (response):
                    if (trialType == 'Same'):
                        self.scoreList[0][2] += 1
                        if (response == correct):
                            self.scoreList[0][0] += 1
                        else:
                            self.scoreList[0][1] += 1
                    elif (trialType == 'Small'):
                        self.scoreList[1][2] += 1
                        if (response == correct):
                            self.scoreList[1][0] += 1
                        else:
                            self.scoreList[1][1] += 1
                    elif (trialType == 'Large'):
                        self.scoreList[2][2] += 1
                        if (response == correct):
                            self.scoreList[2][0] += 1
                        else:
                            self.scoreList[2][1] += 1
                    elif (trialType == 'Crnr'):
                        self.scoreList[3][2] += 1
                        if (response == correct):
                            self.scoreList[3][0] += 1
                        else:
                            self.scoreList[3][1] += 1

        #Implies test phase ran through to completion
        return 1
        
        
    def SegmentPracticeImages(self, images):
        '''
        Segment practice image list into the 4 conditions and
        add two coordinate pairs to each image. Add a study coordinate location
        and test coordinate location
        
        Return:
            List [image, trialType, studyCoord(x,y), testCoord(x,y)]
        '''
        images = np.array_split(images, 4)
        allImages = []
        
        for idx, imageType in enumerate([0, 1, 2, 3]):
            for img in images[idx]:
                xyStudy, xyTest = self.CreatePosPair(imageType)
                allImages.append([img, imageType, xyStudy, xyTest])
        return allImages
        
    def RunSinglePractice(self, practiceBlock, images):
        '''
        Read in the images we want, and run the practice block for this subject
        Run encoding and test, and write to the logs 
        
        Return:
           float: ratio correct
        '''
        ### Encoding
        
        # imgs = [[img, trialType, Study(x,y), Test(x,y)]]
        imgs = self.SegmentPracticeImages(images)
        
        self.ShowPromptAndWaitForSpace(" Outdoor or Indoor? (space to continue)")
        random.shuffle(imgs)
        
        self.logfile.write("\nBegin Practice Encoding {}\n\n".format(practiceBlock))
        self.logfile.write("{a:<22}{b:<12}{c:<14}{d:<11}{e:<9}{f:<8}{g}\n".format(
            a='Image',b='Type',c='Start',d='End',e='Correct',f='Resp',g='RT'))
        
        # Run the trial for each encoding trial
        for i, trial in enumerate(imgs):
            img, trialType, studyCoord, testCoord = trial
            response, RT = self.RunTrial(img, studyCoord)
                
            if (response == "escape"):
                self.logfile.write("\n\n Practice terminated early\n\n")
                self.logfile.close()
                sys.exit()
            elif (response == "space"):
                self.Pause()

            trialTypeMap = {0: 'Same', 1: 'Small', 2: 'Large', 3: 'Crnr'}
            
            trialTypeStr = trialTypeMap[trialType]
            correct = ""
                
            self.logfile.write("{:<22}{:<9}{:<14}{:<17}{:<7}{:<6}{:>0.3f}\n".format(
                img,trialTypeStr,studyCoord,testCoord,correct,response, RT))
        
        ### Test
        self.ShowPromptAndWaitForSpace(" Same or different? (space to continue)")
        random.shuffle(imgs)

        self.logfile.write("\nBegin Practice Test {}\n\n".format(practiceBlock))
        self.logfile.write("{a:<22}{b:<12}{c:<14}{d:<11}{e:<9}{f:<8}{g}\n".format(
            a='Image',b='Type',c='Start',d='End',e='Correct',f='Resp',g='RT'))
        
        # Keep track of the total number they got correct
        totalCorrect = 0
        for i, trial in enumerate(imgs):
            img, trialType, studyCoord, testCoord = trial
            response, RT = self.RunTrial(img, testCoord)
                
            if (response == "escape"):
                self.logfile.write("\n\n Practice terminated early\n\n")
                self.logfile.close()
                sys.exit()
            elif (response == "space"):
                self.Pause()

            trialTypeMap = {0: 'Same', 1: 'Small', 2: 'Large', 3: 'Crnr'}
            trialTypeStr = trialTypeMap[trialType]
            correct = self.leftButton if trialType == 0 else self.rightButton # It should only be correct if its 'Same'
           
            self.logfile.write("{:<22}{:<9}{:<14}{:<17}{:<7}{:<6}{:>0.3f}\n".format(
                img,trialTypeStr,studyCoord,testCoord,correct,response, RT))
            if correct == response:
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
        random.shuffle(practiceImages)
        
        # Split the practice images into three sets
        practiceImages = np.array_split(practiceImages, 3)

        # Run each practice session
        for i in range(3):
            practicePrompt = "Let's practice"
            self.ShowPromptAndWaitForSpace(practicePrompt)
            
            results = self.RunSinglePractice(i+1, [img for img in practiceImages[i]])
            
            # If they get a certain percentage correct, then stop the practice
            self.ShowPromptAndWaitForSpace("You got {}% correct! (space to continue)".format(int(results*100)))
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

        def EndExp():
            exitPrompt = ("This concludes the session. Thank you for "
                          "participating!\n\nPress Escape to quit")
            exitText = TextStim(self.window, exitPrompt, color='Black')
            exitText.draw(self.window)
            self.window.flip()
            waitKeys(keyList=['escape'])
            self.window.close()

        # Show main welcome window
        welcomePrompt = "Thank you for participating in our study! Press space to begin"
        self.ShowPromptAndWaitForSpace(welcomePrompt)
        
        # If run practice trials, then RunPractice
        if self.runPracticeTrials:
            self.RunPractice()
        
        self.RunPhase(0)
        testFinished = self.RunPhase(1)
        if (testFinished):
            EndExp()
            return(self.logfile, self.scoreList)
        else:
            EndExp()
            self.logfile.close()
            return(-1,-1)
