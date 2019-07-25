#!/usr/bin/python

#TODO   Implement ECog functionality for all 3 tasks
#       Implement Scanner functionality for all 3 tasks    

VERSION=1.1

"""Creates the GUI for the MDT Suite. MDT, or Mnemonic Discrimination 
Task, is a type of experimental task that tests various aspects of a
subject's memory. The MDT Suite is a collection of these tasks
comprised of a Object, Spatial, and Temporal discrimination tasks.

class MainWindow: GUI frame that opens upon running this python script,
containing all parameter selections/entries, and a button to run a task
 
class InstrWindow: frame that opens upon selecting "Experiment
Instructions" from the Help Menu of the GUI. Contains a scrollable text
field displaying all of the information regarding the tasks / parameters
"""

import wx 
import os 
import sys
import re
from functools import partial

#Store present dir info before importing files that import psychopy
#Importing psychopy screws up present directory info
currentDir = os.getcwd()
includePath = os.path.join(currentDir, "include")
sys.path.append(includePath)

import mdtsuite


class InstrWindow(wx.Frame):
    """Window that pops up upon selecting "Experiment Instructions" from Help
    menu. The class reads in the "instructions.txt" file that should be present
    within the directory, and parses a defined set of rules to format the font
    of the text.
    """
    def __init__(self,parent,title):

        #Initiate frame in position relative to parent window's present position
        posPar = parent.GetPosition()
        sizePar = parent.GetSize()
        posX = (posPar[0] + sizePar[0] + 10)
        posY = posPar[1]

        #Non-resizable 600x500 frame
        wx.Frame.__init__(self,parent,title=title, pos=(posX,posY),
            size=(600,500), style= wx.DEFAULT_FRAME_STYLE)

        #Make a multiline rich text display, for read-only purposes
        textDisplay = wx.TextCtrl(self, wx.ID_ANY, 
            style=wx.TE_READONLY | wx.TE_MULTILINE | wx.TE_RICH)

        #Set font types for different parts of the instructions
        defaultFont = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                              wx.FONTWEIGHT_NORMAL)
        boldFont = wx.Font(9, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                           wx.FONTWEIGHT_BOLD)
        sectnFont = wx.Font(11, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_BOLD)
        topicFont = wx.Font(14, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL,
                            wx.FONTWEIGHT_BOLD)

        #Set text styles (add colors to fonts) for various parts
        defaultStyle = wx.TextAttr(colText='BLACK', font=defaultFont)
        paramStyle = wx.TextAttr(colText='BLUE', font=sectnFont)
        expStyle = wx.TextAttr(colText='DARK GREEN', font=sectnFont)
        logStyle = wx.TextAttr(colText='BROWN', font=boldFont)
        topicStyle = wx.TextAttr(colText='BLACK', font=topicFont)

        #List of formatting characters and associated styles
        formatList = [("<",">",topicStyle), ("(",")", paramStyle),
                      ("[","]", expStyle), ("{","}", logStyle)]

        instrFile = "include/instructions.txt"
        instrFilePath = os.path.join(currentDir, instrFile)
        f = open(instrFilePath, 'r')

        #If line starts with formatting character, format selection with
        #repsective style and append text to panel. Otherwise, write
        #text with default style.
        for line in f:
            foundFormat = False
            for group in formatList:
                if (line[0] == group[0]):
                    foundFormat = True
                    formatEnd = line.find(group[1])
                    lineStart = line[1:formatEnd]
                    lineEnd = line[formatEnd+1:]
                    textDisplay.SetDefaultStyle(group[2])
                    textDisplay.AppendText(lineStart)
                    textDisplay.SetDefaultStyle(defaultStyle)
                    textDisplay.AppendText(lineEnd)
            if (not foundFormat):
                textDisplay.SetDefaultStyle(defaultStyle)
                textDisplay.AppendText(line)

        textDisplay.SetInsertionPoint(0)
        self.Show(True)


class MainWindow(wx.Frame):
    """Class for the main window of the experiment, which includes all input 
    and selection fields for parameters, as well as a method for running the
    selected experiment with the inputted parameters. This window pops up
    upon initially running the application.
    """
    def __init__(self,parent,title):

        #Create non-adjustable frame with minimize and close buttons
        wx.Frame.__init__(self,parent,title=title,
            style = wx.MINIMIZE_BOX | wx.CLOSE_BOX | wx.SYSTEM_MENU | wx.CAPTION)

        self.tempSelect = False

        defaultLogLoc = "logs"
        defaultLogDir = os.path.join(currentDir, defaultLogLoc)

        self.panel = wx.Panel(self, wx.ID_ANY)
        self.StatusBar =self.CreateStatusBar()

        helpMenu = wx.Menu()
        menuInstr = helpMenu.Append(wx.ID_HELP_CONTENTS, 
            "Experiment Instructions",
            "Detailed information about running this task suite")
        menuAbout = helpMenu.Append(wx.ID_ABOUT, "About", 
            "Information about this program")

        #Create the menubar
        menuBar = wx.MenuBar()
        menuBar.Append(helpMenu, "&Help")
        self.SetMenuBar(menuBar)

        #Create elements to put within the frame
        self.expRadioList = ['Object', 'Spatial', 'Temporal']
        self.expRB = wx.RadioBox(self.panel, label='Choose Experiment Type',
                                 choices=self.expRadioList, majorDimension=1)
        self.screenSelList = ['Fullscreen', 'Windowed', 'Scanner']
        self.screenRB = wx.RadioBox(self.panel, choices=self.screenSelList,
                                    majorDimension=1, label="Monitor")
        self.variantList = ['Normal','ECog']
        self.variantRB = wx.RadioBox(self.panel, choices=self.variantList,
                                    majorDimension=1, label="Task Context")
                                    

        self.inputIDText = wx.StaticText(self.panel, wx.ID_ANY, 'Subject ID')
        self.inputIDEntry = wx.TextCtrl(self.panel, wx.ID_ANY, '999' )
        self.inputSetText = wx.StaticText(self.panel, wx.ID_ANY, 
                                          'Set Choice (1-10)')
        self.inputSetEntry = wx.TextCtrl(self.panel, wx.ID_ANY, '1')
        self.inputDurText = wx.StaticText(self.panel, wx.ID_ANY, 'Trial Duration')
        self.inputDurEntry = wx.TextCtrl(self.panel, wx.ID_ANY, '2.0')
        self.chkSelfPaced = wx.CheckBox(self.panel, wx.ID_ANY, 'Self Paced')
        self.chkPracticeTrials = wx.CheckBox(self.panel, wx.ID_ANY, 'Practice Trials')
        self.chkPracticeTrials.SetValue(True)
        self.chkButtonDiagnostic = wx.CheckBox(self.panel, wx.ID_ANY, 'Button Diagnostic')
        self.chkButtonDiagnostic.SetValue(True)
        self.inputISIText = wx.StaticText(self.panel, wx.ID_ANY, 'ISI')
        self.inputISIEntry = wx.TextCtrl(self.panel, wx.ID_ANY, '0.5')
        self.inputButtonsText = wx.StaticText(self.panel, wx.ID_ANY, 'Input Buttons (separate with comma)')
        self.inputButtonsEntry = wx.TextCtrl(self.panel, wx.ID_ANY, 'z,m')
        self.pauseButtonText = wx.StaticText(self.panel, wx.ID_ANY, 'Pause button')
        self.pauseButtonEntry = wx.TextCtrl(self.panel, wx.ID_ANY, 'p')
        self.trialText = wx.StaticText(self.panel, wx.ID_ANY, 'Trials/Condition')
        self.trialList = ['20','30','40']
        self.trialRB = wx.RadioBox(self.panel, choices=self.trialList,
                                   majorDimension=0, label="")

        self.blockText = wx.StaticText(self.panel, wx.ID_ANY, 'Blocks to run')
        self.blockList = ['6','8','10']
        self.blockRB = wx.RadioBox(self.panel, choices=self.blockList,
                                   majorDimension=0, label="")
        '''
        self.blockRB = wx.ComboBox(self.panel, wx.ID_ANY, 
                                      choices=self.blockList, 
                                      style=wx.CB_DROPDOWN | wx.CB_READONLY,
                                      value='3')
        '''
        self.btnLogOutput = wx.Button(self.panel, wx.ID_ANY, 'Logfile Dir')
        self.dispLogOutput = wx.TextCtrl(self.panel, wx.ID_ANY,
                                         defaultLogDir, size=(200,0))
        self.runButton = wx.Button(self.panel, wx.ID_ANY, 'Run Experiment')
        self.quitButton = wx.Button(self.panel, wx.ID_ANY, 'Close')

        #Initialize element starting properties
        self.trialRB.SetSelection(self.trialRB.FindString('40'))
        self.blockRB.SetSelection(self.blockRB.FindString('10'))
        self.blockText.Disable()
        self.blockRB.Disable()

        #Shorthands for sizer styling
        lft = wx.LEFT
        rgt = wx.RIGHT
        cnt = wx.CENTER
        top = wx.TOP
        bot = wx.BOTTOM
        exp = wx.EXPAND 
        ach = wx.ALIGN_CENTER_HORIZONTAL

        #Create sizers - main sizer aligns all horizontal sizers vertically
        mainSizer          = wx.BoxSizer(wx.VERTICAL)
        expRadioSizer      = wx.BoxSizer(wx.HORIZONTAL)
        choiceRadioSizer   = wx.BoxSizer(wx.HORIZONTAL)
        inputIDSizer       = wx.BoxSizer(wx.HORIZONTAL)
        inputSetSizer      = wx.BoxSizer(wx.HORIZONTAL)
        inputDurSizer      = wx.BoxSizer(wx.HORIZONTAL)
        inputISISizer      = wx.BoxSizer(wx.HORIZONTAL)
        inputButtonsSizer      = wx.BoxSizer(wx.HORIZONTAL)
        pauseButtonSizer      = wx.BoxSizer(wx.HORIZONTAL)
        trialSizer         = wx.BoxSizer(wx.HORIZONTAL)
        blockSizer         = wx.BoxSizer(wx.HORIZONTAL)
        checkSizer         = wx.BoxSizer(wx.HORIZONTAL)
        practiceTrialSizer = wx.BoxSizer(wx.HORIZONTAL)
        buttonDiagnosticSizer = wx.BoxSizer(wx.HORIZONTAL)
        logDirSizer        = wx.BoxSizer(wx.HORIZONTAL)
        runQuitSizer       = wx.BoxSizer(wx.HORIZONTAL)

        #Add elements to respective rows (horizontal sizers)
        expRadioSizer.Add(self.expRB, 0, top, 15)
        expRadioSizer.AddStretchSpacer(1)
        choiceRadioSizer.AddSpacer(10)
        choiceRadioSizer.Add(self.screenRB, 0, top, 15)
        choiceRadioSizer.AddSpacer(10)
        choiceRadioSizer.Add(self.variantRB, 0, top, 15)
        expRadioSizer.Add(choiceRadioSizer)
        inputIDSizer.Add(self.inputIDText, 0, lft, 5)
        inputIDSizer.AddStretchSpacer(1)
        inputIDSizer.Add(self.inputIDEntry, 0, lft,  5)
        inputIDSizer.AddSpacer((90,0))
        inputSetSizer.Add(self.inputSetText, 0, lft, 5)
        inputSetSizer.AddStretchSpacer(1)
        inputSetSizer.Add(self.inputSetEntry, 0, lft, 5)
        inputSetSizer.AddSpacer((90,0))
        inputDurSizer.Add(self.inputDurText, 0, lft, 5)
        inputDurSizer.AddStretchSpacer(1)
        inputDurSizer.Add(self.inputDurEntry, 0, lft, 5)
        inputDurSizer.AddSpacer((90,0))
        inputISISizer.Add(self.inputISIText, 0, lft, 5)
        inputISISizer.AddStretchSpacer(1)
        inputISISizer.Add(self.inputISIEntry, 0, lft, 5)
        inputISISizer.AddSpacer((90,0))
        pauseButtonSizer.Add(self.pauseButtonText, 0, lft, 5)
        pauseButtonSizer.AddStretchSpacer(1)
        pauseButtonSizer.Add(self.pauseButtonEntry, 0, lft, 5)
        pauseButtonSizer.AddSpacer((90,0))
        inputButtonsSizer.Add(self.inputButtonsText, 0, lft, 5)
        inputButtonsSizer.AddStretchSpacer(1)
        inputButtonsSizer.Add(self.inputButtonsEntry, 0, lft, 5)
        inputButtonsSizer.AddSpacer((90,0))
        
        trialSizer.Add(self.trialText, 0, lft, 5)
        trialSizer.AddStretchSpacer(1)
        trialSizer.Add(self.trialRB, 0, lft, 5)
        trialSizer.AddSpacer((90,0))
        blockSizer.Add(self.blockText, 0, lft, 5)
        blockSizer.AddStretchSpacer(1)
        blockSizer.Add(self.blockRB, 0, lft, 5)
        blockSizer.AddSpacer((90,0))
        checkSizer.Add(self.chkSelfPaced, 0, lft, 5)
        checkSizer.AddStretchSpacer(1)
        practiceTrialSizer.Add(self.chkPracticeTrials, 0, lft, 5)
        practiceTrialSizer.AddStretchSpacer(1)
        buttonDiagnosticSizer.Add(self.chkButtonDiagnostic, 0, lft, 5)
        buttonDiagnosticSizer.AddStretchSpacer(1) 
        
        
        logDirSizer.Add(self.btnLogOutput, 0, wx.ALL, 5)
        logDirSizer.Add(self.dispLogOutput, 1, wx.ALL | exp, 5)
        runQuitSizer.Add(self.runButton, 0, wx.ALL, 5)
        runQuitSizer.Add(self.quitButton, 0, wx.ALL, 5)

        #Add rows (sizers) to the main (vertical) sizer
        mainSizer.Add(expRadioSizer, 0, bot | ach, 25)
        mainSizer.Add(inputIDSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(inputSetSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(inputDurSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(inputISISizer, 0, lft | bot | exp, 5)
        mainSizer.Add(inputButtonsSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(pauseButtonSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(trialSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(blockSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(checkSizer, 0, lft | top | bot | exp, 5)
        mainSizer.Add(practiceTrialSizer, 0, lft | top | bot | exp, 5)
        mainSizer.Add(buttonDiagnosticSizer, 0, lft | top | bot | exp, 5)
        mainSizer.Add(logDirSizer, 0, lft | bot | exp, 5)
        mainSizer.Add(runQuitSizer, 0, lft | bot | exp, 5)

        #Set event bindings for mouse clicks on elements
        self.Bind(wx.EVT_MENU, self.OnInstr, menuInstr)
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_RADIOBOX, self.OnExpSelect, self.expRB)
        self.Bind(wx.EVT_RADIOBOX, self.OnVariantSelect, self.variantRB)
        self.Bind(wx.EVT_CHECKBOX, self.OnPaceCheck, self.chkSelfPaced)
        self.Bind(wx.EVT_BUTTON, self.OnDirSelect, self.btnLogOutput)
        self.Bind(wx.EVT_BUTTON, self.OnRunExp, self.runButton)
        self.Bind(wx.EVT_BUTTON, self.OnExit, self.quitButton)

        #Event bindings for mouse hovering -> display hint on status bar
        #Use partials to derive new func for each different message
        self.inputIDEntry.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="Participant ID Number"))
        self.inputDurEntry.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="Length of time of each trial"))
        self.inputISIEntry.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="Inter Stimulus Interval (ISI) - Wait time between trials"))
        self.trialRB.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="Obj/Sptl only - # of trials per each of 4 conditions"))
        self.blockRB.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="Temporal only: # of (Study/Test) blocks to run in task"))
        self.chkSelfPaced.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="If checked, trial runs until user gives input"))
        self.btnLogOutput.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter,
            txt="Select directory for logfile output"))
        self.runButton.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter, 
            txt="Run experiment with given parameters"))
        self.quitButton.Bind(wx.EVT_ENTER_WINDOW, partial(self.OnMouseEnter, 
            txt="Quit Program"))

        #Event bindings for mouse leaving area -> clear status bar
        self.inputIDEntry.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.inputDurEntry.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.inputISIEntry.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.trialRB.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.blockRB.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.chkSelfPaced.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.chkSelfPaced.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.btnLogOutput.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.runButton.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.quitButton.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        self.panel.SetSizer(mainSizer)
        mainSizer.Fit(self)
        self.Show(True)

    def OnMouseEnter(self,e,txt):
        """Sets the status bar text when mouse is hovered over a
        particular window element. 
        """
        self.StatusBar.SetStatusText(txt)
        e.Skip()

    def OnMouseLeave(self,e):
        """Clears the status bar text to a blank line when the mouse leaves
        the area of a particular window element
        """    
        self.StatusBar.SetStatusText('')
        e.Skip()

    def OnInstr(self,e):
        """Creates the pop up frame that contains the instructions for the 
        task suite. 
        """
        instrMsgTitle = "MDT Suite Task Instructions"
        frame2 = InstrWindow(self, instrMsgTitle)
        
    def OnAbout(self,e):
        aboutMsgText = "Testing about dialog!"
        aboutMsgTitle = "About MDT Suite"
        dlg = wx.MessageDialog(self, aboutMsgText, aboutMsgTitle, wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def OnPaceCheck(self,e):
        """Disables the trial duration text/entry elements if the self pace
        button is checked, and re-enables them if the button is unchecked. 
        """
        if (e.Checked()):
            self.inputDurText.Disable()
            self.inputDurEntry.Disable()
        else:
            self.inputDurText.Enable()
            self.inputDurEntry.Enable()

    def OnVariantSelect(self,e):
        """Auto sets certain parameter values, and disables the capability to
        edit them, if the "ECog" variant of the task is selected. If ECog is
        not selected, the fields are re-enabled to allow editing. 

        Note: hard coded ECog values are the paradigm for now, but may need to
        be modified later, so this function may not exist in later iterations.
        """
        expVariant = self.variantRB.GetString(self.variantRB.GetSelection())
        if (expVariant == "ECog"):
            self.inputDurEntry.SetValue("2.0")
            self.inputISIEntry.SetValue("0.5")
            self.chkSelfPaced.SetValue(True)

    def OnExpSelect(self,e):
        """Enables or disables parameter entry sections depending on which
        type of task was chosen. If temporal was chosen, it will enable the
        "block" parameter entry, and if any other task was chosen, it will
        enable the "number of trials" parameter entry.
        """
        expType = self.expRB.GetString(self.expRB.GetSelection())
        if (expType == "Temporal"):
            self.trialText.Disable()
            self.trialRB.Disable()
            self.blockText.Enable()
            self.blockRB.Enable()
        else:
            self.blockText.Disable()
            self.blockRB.Disable()
            self.trialText.Enable()
            self.trialRB.Enable()

    def OnDirSelect(self,e):
        """Opens a directory dialog, allowing selection for choice of where
        to output the logfile. Also writes the path of the directory as text
        in an adjacent text field.
        """
        logDir = ''
        dlg = wx.DirDialog(self, "Choose logfile output directory...", "")
        if dlg.ShowModal() == wx.ID_OK:
            logDir = dlg.GetPath()
        self.dispLogOutput.Clear()
        self.dispLogOutput.WriteText(logDir)


    def OnRunExp(self,e):
        """Grabs all of the inputted / selection parameter information,
        ensures that each entry is of a valid context, and runs the 
        selected task with those parameters if those entries turn out
        to be valid.

        If any part of the inputted / selected parameters are of invalid
        context, a message dialog box appears, which reports any and all 
        errors in parameter entry, and prevents the task from running.
        """

        #Grab all set parameter info
        expType = self.expRB.GetStringSelection()
        screenType = self.screenRB.GetStringSelection()
        expVariant = self.variantRB.GetStringSelection()
        subjectID = self.inputIDEntry.GetLineText(0)
        subset = self.inputSetEntry.GetLineText(0)
        trialDur = self.inputDurEntry.GetLineText(0)
        ISI = self.inputISIEntry.GetLineText(0)
        inputButtons = self.inputButtonsEntry.GetLineText(0)
        pauseButton = self.pauseButtonEntry.GetLineText(0)
        
        if (expType == "Temporal"):
            expLenVar = self.blockRB.GetStringSelection()
        else:
            expLenVar = self.trialRB.GetStringSelection()
        selfPaced = self.chkSelfPaced.IsChecked()
        practiceTrials = self.chkPracticeTrials.IsChecked()
        buttonDiagnostic = self.chkButtonDiagnostic.IsChecked()
        logDir = self.dispLogOutput.GetLineText(0) 
        #List of error messages
        errorMsgs = ""
        idErrorText = "- Subject ID must contain numbers only\n"
        setErrorText = "- Set Choice must be a number 1-10\n"
        durErrorText1 = "- Trial duration must be an integer or decimal number\n"
        durErrorText2 = "- Trial duration must be greater than 0\n"
        ISIErrorText1 = "- ISI must be an integer or decimal number\n"
        ISIErrorText2 = "- ISI must be greater than 0\n"
        logErrorText = "- Logfile output directory does not exist\n"
        buttonErrorText = " - Buttons must be separated by comma, with only 2 buttons\n"
        pauseButtonErrorText = " - Pause button must be 1 key"
    
        #Add errors to error message if they occur
        if "," not in inputButtons or len(inputButtons.split(",")) != 2:
            errorMsgs += buttonErrorText
        else:
            inputButtons = [str(inputButton.strip().lower()) for inputButton in inputButtons.split(",")]
        if len(pauseButton) != 1:
            errorMsgs += pauseButtonErrorText
        if (subjectID.isdigit() == False):
            errorMsgs += idErrorText
        if not subset.isdigit():
            errorMsgs += setErrorText
        elif int(subset) < 1 or int(subset) > 10:
            errorMsgs += setErrorText
        if (not selfPaced):
            try:
                if (float(trialDur) <= 0):
                    errorMsgs += durErrorText2
            except ValueError:
                errorMsgs += durErrorText1        
        try:
            if (float(ISI) <= 0):
                errorMsgs += ISIErrorText2
        except ValueError:
            errorMsgs += ISIErrorText1    
        if (os.path.isdir(logDir) == False):
            errorMsgs += logErrorText
        if errorMsgs:
            errorDlg = wx.MessageDialog(self, errorMsgs, "Error", wx.OK)
            errorDlg.ShowModal()
            errorDlg.Destroy()
        #Run the experiment if no errors in parameter entry    
        else:
            expMDT = mdtsuite.MDTSuite(expType, subjectID, int(subset),
                        float(trialDur), float(ISI), int(expLenVar), 
                        selfPaced, currentDir, logDir, expVariant, 
                        screenType, practiceTrials, buttonDiagnostic, 
                        inputButtons, pauseButton)
            expMDT.RunSuite(VERSION)


    def OnExit(self,e):
        """Closes the application
        """
        self.Close()


if __name__ == "__main__":
    app = wx.App(False)
    frame = MainWindow(None, "MDT Suite")
    app.MainLoop()
