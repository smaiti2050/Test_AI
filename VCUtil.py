"""#========================================================================
#-- Auto report Command Template Utility Package
    #-- Set of Utility functions to run coomands from a file to create viewpoints
#--- Version 1.0 => 30 May 2021
#--- KGS modified to support Line by line processing of commands
#--- KGS fixed Select Result Instance bug and added LABEL_PRECISION command
#============================================================================"""
import _VCollabAPI # VCollab Python API object Link
# Load python system files
import sys, os, traceback, math
import glob,re,time,importlib
from fnmatch import fnmatch;
from pathlib import Path
import PySimpleGUI as sg
sg.theme('LightGrey3');
sg.SetOptions(font='Times 14');
numeric_const_pattern = '[-+]? (?: (?: \d* \. \d+ ) | (?: \d+ \.? ) )(?: [Ee] [+-]? \d+ ) ?';
RE_getFloats = re.compile(numeric_const_pattern, re.VERBOSE);
def GetFloatsInString(sLine):
    '''
    Returns the float values in a string
    
        Parameters:
            sLine(string): A string
        Returns:
            String 
    '''
    return RE_getFloats.findall(sLine);
bGUIMode = _VCollabAPI.xIsGUIMode();
NULLSTR = u"";
sTmpFilePath = os.path.dirname(_VCollabAPI.xGetLogPath());
sPyFolder = os.path.dirname(os.path.realpath(__file__));
bDebugMode = False
#=========== Default Parameters =============================
#----------------------------------------------------------------------------------------
#--- Default Parameters ----
igMaxHostSpots = 5; # Nomber of Hotspots
CurVPathName=u"Report Views" ;  # ViewPath Name
iLabelArrangeMode = 2; #1=>Top-Bot, 2=>Compact, 3=>Circular 4=> Silhouette, 5=>Rectangular
igInstanceFlag = 0; # 0=> Last Instance; 1=> Max Instance; 2=> Min Instance; 3=> AllInstances
sg_DefFType=".html";
sg_OutFileName = u"";
sModel="";
#---
Winsize = _VCollabAPI.pxGetWindowSize();
gPopX=50;gPopY=Winsize[1]-50;
#================ Some Utility functions ============
def OpenLogFiles(sFilePath=None,bCheck=False,sMode ='w'):
    '''
    Opens a log file 
    
        Parameters:
            sFilePath: Filepath for the log file (optional)
            bCheck(boolean): If True uses existing stdout (optional)
            sMode(string):  Access mode w-wriging; r-reading; a-appending (optional)
        
        Returns:
            None
    '''
    try:
        if sys.stdout!= None: 
            if bCheck == True: return False; # use existing stdout
            sys.stdout.close();
        if sys.stderr!= None and sys.stderr != sys.stdout: sys.stderr.close();
        sys.stderr = None; sys.stdout = None;
        if sFilePath == None: 
            sFilePath = os.path.join(sTmpFilePath,'ProPyAPI_stdlog.log');
        sys.stdout = open(sFilePath,sMode,encoding='utf-8',errors='ignore')
        sys.stderr = sys.stdout;
        return True;
    except :
        sTB = traceback.format_exc();
        _VCollabAPI.xMessageBox(u"Error Trace!!! "+sTB,True);
    return False;
#---------------------- 
def CloseLogFiles():
    '''
    Closes opened log file 
    
        Parameters:
            None
        
        Returns:
            None
    '''
    if sys.stdout!= None: sys.stdout.close();
    if sys.stderr!= None and sys.stderr != sys.stdout: sys.stderr.close();
    sys.stderr = None; sys.stdout = None;
    return;
#============================================================
def sgPopAutoClose(sMsg,xPos=gPopX,yPos=gPopY,bPopOn = bGUIMode):
    #sg.SystemTray.notify(sTitle,sMsg);return;
    if sys.stdout != None:
        print('PopMessage:',sMsg);sys.stdout.flush();
    if bPopOn:
        sg.popup_auto_close(sMsg,keep_on_top=True, no_titlebar = True,location=(xPos,yPos),grab_anywhere = True);
    return;
#----------------------------------------------
iMinWait = 0;
def sgNotify(sTitle='Message',sMsg="",iwait=iMinWait):
    '''
        Pop up notification dialog box for GUI mode
    
        Parameters:
            sTitle: Title for the dialog box (optional)
            sMsg: Text message to show in the pop-up dialog box (optional)
            iwait: Time in sec to display the dialog box (optional)
        Returns:
            True: If successful
            False: If not successful
    '''
    if sMsg == None: sMsg = "";
    if sTitle == None : sTitle = "";
    sTitle = str(sTitle); sMsg = str(sMsg)
    if len(sMsg) < 1: #-- Only Title String?
        if len(sTitle) < 1: return False;
        sMsg = sTitle; sTitle = "";
    elif len(sTitle) < 1: # only message
        sTitle = "";
    #---
    if sys.stdout != None:
        print(sTitle,sMsg);sys.stdout.flush();
    if bGUIMode == False or iwait < 1: return False;
    #---
    sColor = '#CCEEFF'; txtbgColor = '#EFFFFF';
    sWinTitle = "Message Dialog";bCustomTitle=False
    if sTitle.upper().find("ERR") >= 0: sColor = '#FFCCCC';
    #--
    #- sg.popup(f"{sTitle}\n{sMsg}")
    gui_rows = [];
    if len(sTitle) > 4:
        nline = min(int(len(sTitle)/60+1),5);
        gui_rows = [[sg.Text(sTitle,size=(60, nline),background_color=sColor)]];
    else:
        sWinTitle = sTitle;bCustomTitle=True;
    if len(sMsg) > 0:
        nline = min(int(len(sMsg)/60+2),10);
        gui_rows.append([sg.Multiline(sMsg,size=(60, nline),background_color=txtbgColor,expand_x=True)]);
    if iwait > 10: gui_rows.append([sg.Ok(size=(10,1)),sg.Cancel(size=(10,1))]);
    # window = sg.Window(sWinTitle, gui_rows,use_custom_titlebar=bCustomTitle,titlebar_background_color = sColor, 
        # font = ('Times',12), resizable=True, keep_on_top=True,location=(25,500),finalize=True);
    window = sg.Window(sWinTitle, gui_rows, font = ('Times',12), resizable=True, 
        keep_on_top=True,location=(25,500),finalize=True);
    start = int(round(time.time()*1000));
    iwait = iwait*1000;
    try:
        while (True):
            window.BringToFront()
            # This is the code that reads and updates your window
            event, values = window.read(timeout=2)
            if event in (None,'Quit','Cancel'):
                window.close();del window;
                return False;
            if event == 'Ok':
                window.close();del window;
                return True;
            now = int(round(time.time()*1000));
            if (now-start) > iwait: 
                window.close();del window;
                return False;
        window.close();
        return False;
    except:
        window.close();
        pass;
        #return None
    return False;
#==================================================
start_time = time.time();
def GetTimeString(start_time,end):
    '''
        Gives elased time in Hr:Min:Sec format
    
        Parameters:
            start_time: Start time
            end : End time
        Returns:
            sTimeString (string): Elapsed time in Hr:Min:Sec format as a string
            
    '''
    millis = int((end - start_time)*1000);
    seconds = int((millis/1000)%60);
    minutes = int((millis/(1000*60)%60));
    hours = int((millis/(1000*60*60))%24);
    ms = int(millis - (hours * 60*60*1000 + minutes * 60 *1000 + seconds * 1000));
    sTimeString = f"{hours} h: {minutes} m: {seconds} s: {ms}"
    return sTimeString;
#-----------------------------------
def ReportTime(startTime=None,msg="",bReSet=False):
    ''' Prints the time in H:Min:Sec format
    
        Parameters:
            startTime: If start time is given it takes the differences and reports the time taken (optional)
            msg: Message to be printed (optional)
            bReSet (boolean): If True it resets the time (optional)
        Returns:
            Return the end time
    '''
    global start_time;
    if bReSet :
        start_time = time.time();
        PrintMessage(f"{msg} - Timer Started");
        return start_time;
    if startTime != None: start_time = startTime;
    end = time.time();
    millis = int((end - start_time)*1000);
    seconds = int((millis/1000)%60);
    minutes = int((millis/(1000*60)%60));
    hours = int((millis/(1000*60*60))%24);
    ms = int(millis - (hours * 60*60*1000 + minutes * 60 *1000 + seconds * 1000));
    sTimeString = f"{hours} h: {minutes} m: {seconds} s: {ms}";
    PrintMessage(f"{msg} Time: {sTimeString}");
    start_time = end;
    return end;
#---------------------------------------
##----  Display Error Messages
def PrintErrorMessage(sMessage,MsgPre=u"",MsgPost=u""):
    '''
        Prints error message on the screen or in VCollab message box depending on the GUI mode
        
        Parameters:
            sMessage: Message to be printed output
            MsgPre: Prefix to the message (optional)
            MsgPost: Postsfix to the message (optional)        
            
        Returns:
            Nones            
    '''
    if bGUIMode == False :
        print(u"Error: "+str(MsgPre)+u" : "+str(sMessage)+u" , "+str(MsgPost));
        if sys.stdout!= None: sys.stdout.flush();
    else :
        _VCollabAPI.xMessageBox(u"Error:\n "+str(MsgPre)+u" : "+str(sMessage)+u" , "+str(MsgPost),True);
    return;
def PrintDebugMessage(sMessage,MsgPre=u"",MsgPost=u""):
    '''
        Prints debug message on the screen or in VCollab message box depending on the GUI mode
        
        Parameters:
            sMessage: Debug message to be printed output
            MsgPre: Prefix to the message (optional)
            MsgPost: Postsfix to the message (optional)        
            
        Returns:
            Nones            
    '''
    if bDebugMode == False :
        print(u"Error: "+str(MsgPre)+u" : "+str(sMessage)+u" , "+str(MsgPost));
    else :
        _VCollabAPI.xMessageBox(u"Error:\n "+str(MsgPre)+u" : "+str(sMessage)+u" , "+str(MsgPost),True);
    return;
##----  Display Messages - Used for testing only
def PopMessage(sMessage,MsgPre=u"",MsgPost=u""):
    '''
        Prints message on the screen or in message box depending on the GUI mode
        
        Parameters:
            sMessage: Message to be printed output
            MsgPre: Prefix to the message (optional)
            MsgPost: Postsfix to the message (optional)        
            
        Returns:
            Nones            
    '''
    if bGUIMode == False:
        print(str(MsgPre)+u" : "+str(sMessage)+u" , "+str(MsgPost));
    else :
        sgNotify(f"!! Msg => {str(MsgPre)} ",f"{str(sMessage)} {str(MsgPost)}",5);
    return;
def PrintMessage(sMessage,MsgPre=u"",MsgPost=u""):
    '''
        Prints  message on the screen
        
        Parameters:
            sMessage: Message to be printed output
            MsgPre: Prefix to the message (optional)
            MsgPost: Postsfix to the message (optional)        
            
        Returns:
            Nones            
    '''
    print(str(MsgPre)+u" : "+str(sMessage)+u" , "+str(MsgPost));
    if sys.stdout != None: sys.stdout.flush();
    return;
#=================================================================================
def IsFloat(string):
    '''
    Checks whether if a string is float 
    
        Parameters:
            string(string): string 
        
        Returns:
            boolean
    '''
    try:
        float(string)
        return True
    except (ValueError,TypeError):
        return False
def GetFloat(string,fDefault=0.0):
    '''
    Converts string to float for non float entities returns the default value
    
        Parameters:
            string(string): string 
            fDefault: return value if the string is not float (Default = 0.0) (optional)
        
        Returns:
            float
    '''
    try:
        fValue = float(string)
        return fValue
    except (ValueError,TypeError):
        return fDefault;
#-----------------------------
def IsInt(string):
    '''
    Checks whether if a string is integer 
    
        Parameters:
            string(string): string 
        
        Returns:
            boolean
    '''
    try:
        int(string)
        return True
    except (ValueError,TypeError):
        return False
def GetInt(string,iDefault=0):
    '''
    Converts a string to integer
    
        Parameters:
            string(string): string 
            iDefault: return value if the string is not integer (Default = 0) (optional) 
        
        Returns:
            integer
    '''
    try:
        iValue = int(string)
        return iValue
    except (ValueError,TypeError):
        return iDefault;
#----------------------------------------
def IsWildString(sName):
    '''
        Checks if a string has wild card character ("*" and "?") in it 
        Parameters:
            sName: string 
        
        Returns:
            boolean
    '''
    if sName.find('*') >= 0: return True;
    if sName.find('?') >= 0: return True;
    return False;
#---------------------------------------------
def IsSameString(sName1,sName2):
    '''
        Compares both the strings are same
        Parameters:
            sName1: String 1
            sName2: String 2
        
        Returns:
            boolean
    '''
    sNameA = sName1.strip().upper();
    sNameB = sName2.strip().upper();
    if sNameA == sNameB : return True;
    return False;
#------------------------------------------------------
def IsSubString(aPart,sPartName,bWild = False):
    '''
        Checks if a string is sub string of a main string
        Parameters:
            aPart: sub string
            sPartName: main string
            bWild: Wild card character (optional)
        
        Returns:
            boolean
    '''
    if bWild :
        return fnmatch(aPart.upper(), sPartName.upper());
    #else
    return (aPart.upper().find(sPartName.upper()) >= 0);
#----------------Convert Float to formatted String based on precision-----
def GetFloatString(fRangeMax,iPrecision=4):
    '''
        Formats the number based on the limit  (1.0e-3 to 1.0e5)
        Parameters:
            fRangeMax: Number to be formatted
            iPrecision: Precision for the number (optional)
        
        Returns:
            sRefRes (string): Formatted number 
    '''
    if (abs(fRangeMax) < 1.0e-3 or abs(fRangeMax) > 1.0e5 ):
        sFormat= "{:.%de}" % iPrecision;
    else:
        sFormat= "{:.%df}" % iPrecision;
    sRefRes = sFormat.format(fRangeMax);
    return sRefRes;
#----------------Convert Float to formatted String based on precision-----
def Float2String(fValue):
    '''
        Formats the number based on the limit
            number < 1.0E-10 : returns 0.0
            1.0e5 > number < 1.0E-10 : Precision = 4
            number < 0.01 : Precision = 4
            number > 10 : Precision = 2
            number > 1000 : Precision = 1
            number > 1.0E4 : Precision = 0
        Parameters:
            fValue: Number to be formatted
        Returns:
            Formatted number (string)
    '''
    # Scientific Precision
    absVal = abs(fValue);
    if absVal < 1.0E-10 : return "0.0";
    if absVal < 1.0e-4 : # Small Value
        iPrecision = 4;
        sFormat= "{:.%de}" % iPrecision;
        return sFormat.format(fValue);
    if absVal > 1.0e5 : # Large Value
        iPrecision = 4;
        sFormat= "{:.%de}" % iPrecision;
        return sFormat.format(fValue);
    # -----------------------
    iPrecision = 3;
    if absVal < 0.01 : iPrecision = 4;
    if absVal > 10 : iPrecision = 2;
    if absVal > 1000 : iPrecision = 1;
    if absVal > 1.0E4 : iPrecision = 0;
    if (abs(fValue) < 1.0e-4 or abs(fValue) > 1.0e6 ):
        sFormat= "{:.%de}" % iPrecision;
    else:
        sFormat= "{:.%df}" % iPrecision;
    sVal = sFormat.format(fValue);
    return sVal;
#=======================================================
#====== File access ==============
def CheckFileWriteAccess(sFilePath):
    '''
        Checks if absolute file path has write access 
        Parameters:
            sFilePath: File path
        
        Returns:
            boolean
    '''
    try:
        if sFilePath == None or len(sFilePath) < 2: return False;
        if os.path.isabs(sFilePath) == False: return False;
        if os.path.isdir(sFilePath) == False: 
            #PrintMessage(f"Error in Write Acccess check?: {sFilePath} is not a valid dir ");
            #return False;
            sFilePath = os.path.dirname(sFilePath);
            if os.path.isdir(sFilePath) == False: 
                PrintMessage(f"Error in Write Acccess check?: {sFilePath} is not a valid dir ");
                return False;
        sstime = time.time();
        filename = os.path.join(sFilePath,f"_wtestcase{sstime}.gol")
        if os.path.exists(filename) : os.remove(filename)
        f = open(filename,"w",encoding='utf-8',errors='ignore')
        f.close()
        os.remove(filename)
        return True
    except Exception as e:
        pass;
        print(f'{e}');
        return False;
    except:
        sTB = traceback.format_exc();
        print(f"======= WriteAccess Error catch ================ \n{sTB}\n")
        _VCollabAPI.xMessageBox(u"Error Trace!!! "+sTB,bGUIMode);
    return False;
#=================================================================================
def IsFileExists(sFilePath):
    '''
        Checks if the specified file path exists
        Parameters:
            sFilePath: File path
        
        Returns:
            boolean
    '''
    if sFilePath == None or len(sFilePath) < 3:
        return False;
    if os.path.isabs(sFilePath) == False: return False;
    if os.path.exists(sFilePath) == False:
        #PrintMessage(sFilePath+u" File Not found ");
        return False;
    return True;
#-----------------------------------------
def IsValidFile(sFile,fsize=1):
    '''
        Checks the size of specified path is valid
        Parameters:
                sFile: File path
                fsize: File path size (optional)
        
        Returns:
            boolean
    '''
    if sFile == None : return False;
    if len(sFile) < 1: return False;
    if os.path.isabs(sFile) == False: return False;
    if os.path.exists(sFile) == False: return False;
    if fsize < 1 : return True;
    try : 
        size = os.path.getsize(sFile);
        if size > fsize: return True;
    except OSError : 
        PrintMessage(f"Error: Getsize Failed for {sFile}");
    return False;
#----------------------------------------------------
def DeleteFile(filename): #New function
    """if exists, delete it else show message on screen"""
    if os.path.exists(filename):
        try:
            os.remove(filename);
            return True;
        except OSError as e:
            PrintErrorMessage("Error: {:s} - {:s}.".format(e.filename,e.strerror));
            return False;
    PrintMessage("File {:s} Not Found".format(filename));
    return False;
#=========================================================================
def IsFileOpenReady(sFileName,bWait=True):
    '''
        Checks if the file is opened or closed
        Parameters:
            sFileName: File path
            bWait: Does not display pop up message if the file is opened (optional)
        
        Returns:
            boolean
    '''
    try:
        myfile = open(sFileName, "a+",encoding='utf-8',errors='ignore') ; #--- r+, w etc...
        myfile.close();
        return True;
    except IOError:
        print(f"Could not open file: {sFileName} \n Please close it");
    if bWait == False: return False;
    return sgNotify("Error: Pl Close File",sFileName,200);
#=============================================================
def IsValidOutputPath(sFileName,bWait=False,iTime=20):
    '''
        Checks if the specified file path is valid
        Parameters:
            sFileName: File path
            bWait: Does not display pop up message if the file is opened (optional)
            iTime: Wait time for the pop up message box (optional)
        
        Returns:
            boolean
    '''
    if sFileName== None or len(sFileName) < 3 or os.path.isabs(sFileName) == False: return False;
    try:
        myfile = open(sFileName, "a+",encoding='utf-8',errors='ignore') ; #--- r+, w etc...
        myfile.close();
        os.remove(sFileName);
        return True;
    except IOError:
        print(f"Could not open file: {sFileName} \n Please close it");
    if bWait == False: return False;
    return sgNotify("Error: Output FilePath",sFileName,iTime);
#-------------------------------------------------------------
def GetFileFullPath(sFolder,sFileNameRef):
    '''
        Gets the absolute file path from a folder 
        Parameters:
            sFolder: Folder path
            sFileNameRef: Reference file name
        
        Returns:
            FileList: Absolute file path
            None: Invalid file 
    '''
    sFileName = sFileNameRef;
    if os.path.isabs(sFileName) == False:
        sFileName = os.path.join(sFolder,sFileName);
    FileList = glob.glob(sFileName);
    if len(FileList) > 0: return FileList[0];
    if os.path.isabs(sFileNameRef) == False:
        sFileName = os.path.join(sPyFolder,sFileNameRef);
        FileList = glob.glob(sFileName);
        if len(FileList) > 0: return FileList[0];
    return None;
#-------------------------------------------------------------
def GetAllFiles(sFolder,sFileName):
    '''
        Gets absolute file paths of the reference file name
        Parameters:
            sFolder: Folder path
            sFileNameRef: Reference file name
        
        Returns:
            FileList: Absolute file path
            None: Invalid file             
    '''
    if os.path.isabs(sFileName) == False:
        sFileName = os.path.join(sFolder,sFileName);
    FileList = glob.glob(sFileName);
    if len(FileList) > 0: return FileList;
    return None;
#===================================================
def GetOutputFilePathName(sModel,sFName=None):
    '''
        Gets the valid file path from the cax folder
        Parameters:
            sModel: Loaded cax model name 
            sFName: File name (optional)
        
        Returns:
            sOutputFileName:
    '''
    # -----Get Model CAX file Name ------------------------------
    sCaxPath = _VCollabAPI.xGetFileName(sModel);
    sCaxFolder = os.path.dirname(sCaxPath);
    sCaxFileName= os.path.basename(sCaxPath);
    # -----Set output file Path ------------------------------
    sOutputFilePath = sCaxFolder; # --- Try Model file path
    if CheckFileWriteAccess(sOutputFilePath) == False:
        sOutputFilePath = os.path.dirname(_VCollabAPI.xGetLogPath()); # Use Temp File Path
    #----------Set File Name -----------------
    sFileName = sFName;
    if sFName == None:
        sFileName = sCaxFileName[:-4];
    #sFileName = os.path.splitext(sCaxFileName)
    sOutputFileName = os.path.join(sOutputFilePath , sFileName);
    return sOutputFileName;
#================================================
def Dialog_GetOpenFileName(sTitle=u"File Name",sFileName="",sFileType=""):
    '''
        Opens the file browser dialog box
        Parameters:
            sTitle: Title for the file browser (optional)
            sFileName: File path to be displayed (optional)
            sFileType: File types to show in the file browser (optional)
        
        Returns:
            sFile: File path
            None: If the the file path is invalid
    '''
    sFileTypeL = [('all files', '*.*')];
    if len(sFileType) < 1:
        if len(sFileName) > 1:
            sBaseName=os.path.basename(sFileName);
            sFtype = os.path.splitext(sBaseName)[1][1:].strip();
            #sg.popup(sBaseName,sFtype)
            if len(sFtype) > 1:
                sFileTypeL = [(sFtype+u' files',u'.'+sFtype),('all files', '*.*')];
    else:
        if type(sFileType) is list:
            sFileTypeL = sFileType;
        else:
            sFileTypeL = [sFileType];
    #----------------------
    # sg.popup(sFileTypeL)
    sFolder = os.path.dirname(sFileName);
    if os.path.exists(sFileName) == False: sFileName = "";
    layout = [[sg.Text(sTitle, size=( len(sTitle)+1, 1)), sg.Input(sFileName,key='_FILE1_',size=(40, 1)),sg.FileBrowse(file_types=sFileTypeL,initial_folder=sFolder)],
              [sg.Ok(size=(8,1)), sg.Cancel(size=(8,1))]];
    window = sg.Window('Get File Dialog',layout,keep_on_top=True,finalize=True);
    while True:
        window.BringToFront()
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            window.close();del window;
            return None;
        if event == 'Ok':
            sFile = values['_FILE1_'];
            window.close();del window;
            return sFile;
    window.close();
    return None;
#============================================================
def Dialog_GetFolderName(sTitle=u"Folder Name",sFileName=""):
    '''
        Opens the folder browser dialog box
        Parameters:
            sTitle: Title for the folder browser (optional)
            sFileName: Folder path to be displayed (optional)
        
        Returns:
            sFolderPath: Folder path
            None: If the the folder path is invalid
    '''
    if sFileName == None or len(sFileName) < 3:
        sFolderName = "";
    else:
        if os.path.isdir(sFileName) : 
            sFolderName = sFileName
        else:
            sFolderName = os.path.dirname(sFileName)
        if os.path.exists(sFolderName) == False:
            sFolderName = "";
    layout = [[sg.Text(sTitle, auto_size_text=True)],
              [sg.InputText(default_text=sFolderName, size=(40,1), key='_INPUT_'),
               sg.FolderBrowse(initial_folder=sFolderName)],
              [sg.Button('Ok', size=(8, 1)), sg.Button('Cancel', size=(8, 1))]]
    window = sg.Window('Get Folder Dialog', layout,keep_on_top=True,finalize=True);
    while True:
        window.BringToFront()
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            window.close();del window
            sgNotify("Cancel?",iwait=2);
            return None;
        if event == 'Ok':
            sFolderPath = values['_INPUT_'];
            window.close();del window
            return sFolderPath;
    window.close();del window
    return None;
#=============================================
#================================================
def Dialog_GetSaveFilePath(sTitle=u"File Name",sFileName="",sFileTypes=""):
    '''
        Opens the file save dialog box
        Parameters:
            sTitle: Title for the file save dialog box(optional)
            sFileName: File path to be displayed (optional)
            sFileType: File types to show in the file browser (optional)
        Returns:
            sFile: File path
            None: If the the file path is invalid            
    '''
    sFolderName = "";sExt="";
    if len(sFileName) > 0:
        if os.path.isdir(sFileName):
            sFolderName = sFileName;
            sBaseName = "";
        else:
            sBaseName=os.path.basename(sFileName);
            sFolderName = os.path.dirname(sFileName);
            sExt = sBaseName.split('.')[-1];
    isFolder = False;
    if len(sFileTypes) < 1:
        if len(sExt) > 1:
            sFileTypes = (f".{sExt}");
        else:
            isFolder = True;
    #----------------------
    if isFolder == False:
        layout = [[sg.Text(sTitle, size=(len(sTitle)+1, 1)), sg.Input(sFileName,key='_FILE1_',size=(40, 1)),sg.FileSaveAs(file_types=sFileTypes,initial_folder=sFolderName)]];
    else:
        layout = [[sg.Text(sTitle, size=(len(sTitle)+1, 1)), sg.Input(sFolderName,key='_FILE1_',size=(40, 1)),sg.FolderBrowse(initial_folder=sFolderName)]];
    layout.append([sg.Ok(size=(10,1)), sg.Cancel(size=(10,1))]);
    window = sg.Window('Get Save File/Folder Dialog',layout,keep_on_top=True,finalize=True);
    while True:
        window.BringToFront()
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            window.close();del window;
            return None;
        if event == 'Ok':
            sFile = values['_FILE1_'];
            window.close();del window;
            return sFile;
    window.close();del window;
    return None;
#==================================================
def GetStringsDialog(msgs=["String 1"],sVals=[],title="Get Strings Dialog"):
    '''
        Opens the input string dialog box based on the string length
        Parameters:
            msgs:   Number of input boxes (optional)
            sVals:  Default values for the input box (optional)
            title:  Title for the input string dialog box (optional)
        Returns:
            sfVals: List of the strings from the input box
            None: If the values are invalid
             
    '''
    layout=[];maxkeylen = 10;
    for key in msgs:
            if len(key) > maxkeylen: maxkeylen = len(key);
    maxvallen=20;
    for key in sVals:
            if len(key) > maxvallen: maxvallen = len(key);
    maxkeylen = min(maxkeylen,60);
    nVals = len(sVals);
    for i,key in enumerate(msgs):
        val = "";
        if i<nVals: val = str(sVals[i]);
        layout.append([sg.Text(key,size=(maxkeylen,1),justification="left"),sg.Input(val,key=f"_{i+1}_",size=(maxvallen, 1))]);
    layout.append([sg.Ok(size=(12, 1)),sg.Cancel(size=(12, 1))]);
    window = sg.Window(title, layout,keep_on_top=True,location=(25,400),finalize=True);
    while True:
        window.BringToFront()
        event, values = window.read()
        if event in (None, 'Cancel'):   # if user closes window or clicks cancel
            window.close(); del window
            return None;
        if event == 'Ok':
            sfVals=[];
            for i,msg in enumerate(msgs):
                key = f"_{i+1}_";
                sfVals.append(values[key].strip());
            window.close(); del window
            return sfVals;
    window.close(); del window
    return None;
#=====================================================
def SplitPath(sRefFile):
    '''
        Gives the folder name, file name and the file extension
        Parameters:
            sRefFile: Absolute file path
        Returns:
             A list consists of folder name, file name and file extension
    '''
    sOutFileDir = os.path.dirname(sRefFile);
    sBasePath = Path(os.path.basename(sRefFile));
    sType = sBasePath.suffix;
    fname = sBasePath.stem
    return [sOutFileDir,fname,sType];
#-----------------------------------------
def GetTempOutputFile(sRefFile,sExt='_TmpVC',sType=None):
    '''
        Gives a new absolute file path with new file name
        Parameters:
            sRefFile: Absolute file path
            sExt: New file append name (optional)
            sType: File extension (optional)
        Returns:
             Absolute file path
    '''
    sOutFileDir = os.path.dirname(sRefFile);
    sBasePath = Path(os.path.basename(sRefFile));
    if sType == None: sType = sBasePath.suffix;
    fname = sBasePath.stem
    if CheckFileWriteAccess(sOutFileDir) == False:
        sOutFileDir = os.path.dirname(_VCollabAPI.xGetLogPath());
    #sgNotify("Test",f'{[sOutFileDir,fname,sExt,sType]}',10);
    return os.path.join(sOutFileDir,fname+sExt+sType);
#=================================================
def SearchValidFile(sFile,pathlist=[]):
    '''
        Searches for the file name in the given paths 
        Parameters:
            sFile: File name to be searched
            pathlist (List): Paths for searching the file (optional)
        Returns:
             sFile: File path if the path is valid
             None: If the file path is invalid
    '''
    if os.path.isabs(sFile):
        if IsValidFile(sFile): return os.path.abspath(sFile);
        sgNotify("fError",f"{sFile} not valid",0);
        return None;
    if len(pathlist) < 1:
        pathlist = [sDefFolder,os.getcwd(),os.path.dirname(sPyFolder),sPyFolder];
    for sFolder in pathlist:
        sFileName = os.path.join(sFolder,sFile);
        if IsValidFile(sFileName) : return os.path.abspath(sFileName);
    sgNotify("fError",f"{sFileName} not valid",0);
    return None;
#----------------------------------------------------
def ImportPyModule(sName):
    importlib.invalidate_caches()
    if sName in sys.modules:  # Reload
        module = importlib.reload(sys.modules[sName]);
    else: #Import
        module = importlib.import_module(sName);
    importlib.invalidate_caches()
    return module;
#=================================================
#---- Display Mode Related Functions
#===================================================
def SetModelRandomColor(aModel="",sPart=None,iType=0):
    '''
        Sets the random diffuse color for the parts
        Parameters:
            aModel: Cax model name (optional)
            sPart: Part name (optional)
            iType: Object type indicator.0 for assembly. 1 for a part (optional)
        Returns:
             None
    '''
    if sPart != None:
        _VCollabAPI.xSetRandomColor(aModel,sPart,iType);
        return;
    assmlist = _VCollabAPI.xGetAssemblyList(aModel,u"",0);
    assmlist = assmlist.split(";");
    for sAsm in assmlist:
        _VCollabAPI.xSetRandomColor(aModel,sAsm,0);
    return;
#-------------------------------------------------------
def SetModelDisplayMode(aModel,iDspMode):
    '''
        Sets the display mode for the model
        Parameters:
            aModel: Cax model name
            iDspMode: Display mode (0 for Shaded; 1 for Shaded Mesh; 2 for WireFrame; 3 for Hidden Line Removal; 4 for Point; 5 for Transparent;)
        Returns:
             None
    '''
    assmlist = _VCollabAPI.xGetAssemblyList(aModel,u"",0);
    assmlist = assmlist.split(";");
    for sAsm in assmlist:
        _VCollabAPI.xSetAssemblyDisplayMode(aModel,sAsm,iDspMode);
    return;
#-------------------------------------------------------------
def SetModelColorPlot(aModel,bFlag):
    '''
        Turns ON/OFF the color plot 
        Parameters:
            aModel: Cax model name
            bFlag (boolean): True to enable color plot, False to disable color plot
        Returns:
             None
    '''
    assmlist = _VCollabAPI.xGetAssemblyList(aModel,u"",0);
    assmlist = assmlist.split(";");
    for sAsm in assmlist:
        _VCollabAPI.xSetColorPlotEx(aModel,sAsm,0,bFlag);
    return;
#-------------------------------------------------------------
#=============================================
#--- Viewpoint Related Fuctions
#=======================================================
#------ Set View Orientation from Camera direction (fDX,fDY,fDZ) and Up-Vector (fUX,fUY,fUZ);
def SetCameraView(fDX=1.0,fDY=1.0,fDZ=1.0,fUX=0.0,fUY=1.0,fUZ=0.0,bFit = True):
    '''
    sets the current camera
    Parameters:
        fDX (float): Camera X direction (optional)
        fDY (float): Camera Y direction (optional)
        fDZ (float): Camera Z direction (optional)
        fUX (float): Camera X up vector direction (optional)
        fUY (float): Camera Y up vector direction (optional)
        fUZ (float): Camera Z up vector direction (optional)
        bFit (boolean): Zooms in/out to fit current scene in the viewer window (optional)
        
    Returns:
         None
    '''
    fCameraList = _VCollabAPI.pxGetCamera();
    fPosX=fCameraList[0]; fPosY=fCameraList[1]; fPosZ=fCameraList[2];
    fFOVy=fCameraList[9]; fAspect=fCameraList[10];
    fNear=fCameraList[11]; fFar=fCameraList[12];
    _VCollabAPI.xSetCamera(fPosX,fPosY,fPosZ,fDX, fDY,fDZ, fUX, fUY,fUZ,fFOVy, fAspect,fNear,fFar);
    if bFit : _VCollabAPI.xFitView();
    return;
#---------------------------------------------------------
#CAMERA_XYAXIS,Camera X-Axis ,Camera Y-Axis => Example:CAMERA_XYAXIS,1,0,0,0,0,1
def SetCameraXYCMD(XVec=[1,0,0],YVec=[0,1,0]):
    ZVec = CrossVec(XVec,YVec); ZVec = NormVec(ZVec);
    YVec = CrossVec(ZVec,XVec); YVec = NormVec(YVec);
    SetCameraView(-ZVec[0],-ZVec[1],-ZVec[2],YVec[0],YVec[1],YVec[2]);
    return;
#----------------------------------------------------------
#Set View Orientation from Camera direction and adds zoom factor
def SetCameraViewZoom(fDX=1.0,fDY=1.0,fDZ=1.0,fUX=0.0,fUY=1.0,fUZ=0.0,fZoom=-0.1):
    '''
    sets the current camera and zooms in/out 
    Parameters:
        fDX (float): Camera X direction (optional)
        fDY (float): Camera Y direction (optional)
        fDZ (float): Camera Z direction (optional)
        fUX (float): Camera X up vector direction (optional)
        fUY (float): Camera Y up vector direction (optional)
        fUZ (float): Camera Z up vector direction (optional)
        float (float): Zoom factor (optional)
        
    Returns:
         None
             
    '''
    fCameraList = _VCollabAPI.pxGetCamera();
    fPosX=fCameraList[0]; fPosY=fCameraList[1]; fPosZ=fCameraList[2];
    fFOVy=fCameraList[9]; fAspect=fCameraList[10];
    fNear=fCameraList[11]; fFar=fCameraList[12];
    _VCollabAPI.xSetCamera(fPosX,fPosY,fPosZ,fDX, fDY,fDZ, fUX, fUY,fUZ,fFOVy, fAspect,fNear,fFar);
    _VCollabAPI.xFitView();
    if fZoom>0.8: fZoom = 0.8;
    if fZoom < -1.0: fZoom = -1.0;
    delta = 1.0-2.0*fZoom;
    if delta > 3.0: delta = 3.0;
    if delta < 0.25: delta = 0.25;
    _VCollabAPI.xZoomScreenRect(fZoom,fZoom,delta,delta);
    return;
#--------------------------------------------
def FitViewCMD(fZoom=-0.1):
    '''
        Fits current scene in the viewer window
        Parameters:
            fZoom: zoom factor (optional)
        Returns:
            None             
    '''
    _VCollabAPI.xFitView();
    if fZoom>0.8: fZoom = 0.8;
    if fZoom < -1.0: fZoom = -1.0;
    delta = 1.0-2.0*fZoom;
    if delta > 3.0: delta = 3.0;
    if delta < 0.25: delta = 0.25;
    _VCollabAPI.xZoomScreenRect(fZoom,fZoom,delta,delta);
    return;
#-------------------------------------------------
#--EXPLODE_VIEW,Y/N, Percentage (0-100)
def ExplodeViewCMD(nVals,sVals):
    '''
        Sets parts in exploded view
        Parameters:
            nVals (int): The percentage value of current explode; It should be positive and less than or equal to 100.
            sVals (string): Y/N.Y for explode and N for reset
        Returns:
             None
    '''
    bExplode = False;iPercent=50;
    if sVals[0] == 'Y': 
        bExplode = True;
        if nVals > 1:
            iPercent = GetInt(sVals[1],50);
    _VCollabAPI.xExplode(bExplode,iPercent,False,1);
    return;
#--------------------------------------
def SetBlankView():
    '''
        Sets blank view
        Parameters:
            None
        Returns:
             None
    '''
    #Hide Parts and Legend
    sAll=u"";
    _VCollabAPI.xShowAll(sAll);
    _VCollabAPI.xInvertShow(sAll);
    _VCollabAPI.xShowCAELegend(sAll,False);
    _VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xDeleteXYPlot(sAll);
    _VCollabAPI.xDeleteSymbolPlot(sAll,sAll);
    _VCollabAPI.xShowAxis(False);
    _VCollabAPI.xShowCAEHeaderLegend(u"",False,True);
    _VCollabAPI.xSetCAEProbeTemplateAbbreviation(u"",False);
    return;
#=================================================
#-- imode= 0:Center, 1:Stretch, 2:Tile, 3:fitview
def SetImageView(sImagePath,iMode=1,sVPName=None):
    '''
        Sets image as background and adds viewpoint if the viewpoint name is provided
        Parameters:
            sImagePath: Path of the image to be set as background
            iMode (int): Sets Texture mode. Range 0 to 2; 0 for Center, 1 for Stretch, 2 for Tile (optional)
            sVPName: Viewpoint name (optional)
        Returns:
             None
    '''
    _VCollabAPI.xSetImage(sImagePath,iMode,False);
    _VCollabAPI.xSetBackgroundMode(2);
    if sVPName == None or len(sVPName) < 1: return;
    AddVP_HF(sVPName,CurVPathName,-1);
    return;
#=================================================================
igNoOfVPs = 0;
def AddVP_HF(vpName,sVPathName,VPIndex=-1,count=1):
    '''

        Parameters:
            vpName: Viewpoint name
            sVPathName: Viewpath name
            VPIndex: Viewpath index (optional)
            count: Viewpoint count (optional)
        Returns:
             boolean
    '''
    global igNoOfVPs;
    if len(vpName) < 1 or vpName.upper() == u"NA": return;
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    bRetFlag = _VCollabAPI.xAddViewPoint(vpName,sVPathName,VPIndex);
    if bRetFlag : 
        igNoOfVPs = igNoOfVPs + count;
    PrintMessage(f"AddVP {bRetFlag}: {vpName}, {igNoOfVPs}");
    return bRetFlag;
#---------------------------------------------------------------
def SetViewPathByName(sViewPathName):
    '''
        Sets current viewpath
        Parameters:
            sViewPathName: View path name
        Returns:
            If the viewpath is not set returns -1
            If current viewpath is set it returns viewpath id
             
    '''
    sViewPathList = _VCollabAPI.pxGetViewPathList();
    iPathId = 0;
    for sPathName in sViewPathList:
        if (sViewPathName == sPathName) :
            _VCollabAPI.xSetCurrentViewPath(iPathId);
            return iPathId;
        iPathId = iPathId + 1;
    #
    PrintMessage(f"Error ViewPath not found : {sViewPathName}");
    return -1;
#==========================================================
def SaveAsHTMLorWCAX(sOutputPath, sExt = '.html', iViewPoint = 1):
    '''
        Saves the viewpoints as HTML or WCAX
        Parameters:
            sOutputPath: File path for HTML or WCAX
            sExt: Save as .hmtl or .wcax (optional)
            iViewPoint: 1=>Current View Path, 2=> Current viewpoint, 3=> Current Display (optional)
        Returns:
             boolean : True if successful and False if not successful
    '''
    # iViewPoint 1=>Current View Path 2=> Current viewpoint 3=> Current Display
    bRtnFlag = False;
    if sOutputPath.lower().endswith('.html') :
        bRtnFlag = _VCollabAPI.xExportHTML(sOutputPath,iViewPoint,True,False,u"");
    elif sOutputPath.lower().endswith('.wcax') :
        bRtnFlag = _VCollabAPI.xExportWCax(sOutputPath,iViewPoint,True,False,u"");
    elif sExt.upper() == '.HTML':
        sOutputFileName = sOutputPath+u".html";
        bRtnFlag = _VCollabAPI.xExportHTML(sOutputFileName,iViewPoint,True,False,u"");
    else:
        sOutputFileName = sOutputPath+u".wcax";
        bRtnFlag = _VCollabAPI.xExportWCax(sOutputFileName,iViewPoint,True,False,u"");
    
    if bRtnFlag:
        sgNotify('Message',f"{sOutputPath}, Saved ",3);
        return True;
    sgNotify('Error',f"{sOutputPath}, Save Failed ",5);
    return False
#=============================================================
def SaveOutput(sOutFileName):
    '''
        Saves CAX/HTML/WCAX file based on the file extension
        Parameters:
            sOutFileName: Output file path
        Returns:
             boolean : True if successful and False if not successful
    '''
    if os.path.isabs(sOutFileName) == False:
        sOutFileName = GetOutputFilePathName(sModel,sOutFileName);
    else:
        sFolder = os.path.dirname(sOutFileName);
        if CheckFileWriteAccess(sFolder) == False: 
            sgNotify("Save Error",f"{sOutFileName} Write Access Error");
            return False;
    #--
    sName, ext = os.path.splitext(os.path.basename(sOutFileName))
    if ext.upper() == '.CAX':
        _VCollabAPI.xFileSave(sOutFileName);
        sgNotify('Message', f"Cax file {sOutFileName} saved")
        return;
    if ext.upper() == '.WCAX':
        return SaveAsHTMLorWCAX(sOutFileName);
    if ext.upper() == '.HTML':
        return SaveAsHTMLorWCAX(sOutFileName);
    sgNotify("Save Error",f"{ext} Type not supported");
    return False;
#---------------------------------------------
def ExportHTML_Clipped(sFileName,center=None,Dxyz=[50,50,50]):
    if center == None:
        probIDList = _VCollabAPI.pxGetAllProbeTableIDs(sModel);
        if len(probIDList) < 1: 
            sgNotify("HTML Export Error","Failed to get center point from hotspot",1);
        return False;
        pID = probIDList[0];
        center = _VCollabAPI.pxGetProbeTableLocation(pID);
    #-------
    if len(Dxyz) > 5:
        clipbox = [center[0]+Dxyz[0], center[1]+Dxyz[1], center[2]+Dxyz[2],center[0]+Dxyz[3], center[1]+Dxyz[4], center[2]+Dxyz[5]];
    else:
        clipbox = [center[0]-Dxyz[0], center[1]-Dxyz[1], center[2]-Dxyz[2],center[0]+Dxyz[0], center[1]+Dxyz[1], center[2]+Dxyz[2]];
    _VCollabAPI.xSetClippingPlanes(clipbox);
    if sFileName[:-4] == 'wcax':
        retFlag = _VCollabAPI.xExportWCAX(sFileName,4,False,False,"",False,False);
    else:
        retFlag = _VCollabAPI.xExportHTML(sFileName,4,False,False,"",False,False);
    _VCollabAPI.xClearClippingPlanes();
    return retFlag;
#=============================================================
def CreateCutSection(Loc=None,Eqn=[1,0,0,0]):
    if Loc == None:
        spInfo = _VCollabAPI.pxGetSpericalBounds(sModel,"");
        Loc = list(spInfo[0:3]);
    
    dvec = NormVec(Eqn[:3]);
    offset = -(dvec[0] * Loc[0] + dvec[1] * Loc[1] + dvec[2] * Loc[2] )
    
    _VCollabAPI.xSetSectionPlane(dvec[0],dvec[1],dvec[2],offset);
    _VCollabAPI.xShowSection(True);
    return;
#-----------------------------------------------------------------------
#=============================================================
#----- Legend Related Functions ----
#=============================================================
def SetCustomLegend(bIsGrey=False,nColors=11,bReverse=False):
    '''
        Sets the legend palette 
        Parameters:
            bIsGrey (boolean): Sets grey color for bottom value (optional)
            nColors (int): Number of legend palette colors (optional)
            bReverse (boolean): Reverse the legend (optional)
        Returns:
             None
    '''
    bRevLeg = _VCollabAPI.xGetCAEReverseLegend(sModel);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    fLegColorsList = list(_VCollabAPI.pxGetCAELegendColors(sModel));
    nColorsRef = int(len(fLegColorsList)/3);
    if nColors > 0 and nColorsRef != nColors : 
        if nColors < 2: nColors = 0;
        if nColors > 32: nColors = 11;
        _VCollabAPI.xSetCAELegendDefaultColors(sModel,0);
        _VCollabAPI.xSetCAELegendDefaultColors(sModel,nColors);
        fLegColorsList = list(_VCollabAPI.pxGetCAELegendColors(sModel));
        nColorsRef = int(len(fLegColorsList)/3);
    #------
    if bIsGrey:
        fLegColorsList[-1]=0.8;fLegColorsList[-2]=0.8;fLegColorsList[-3]=0.8;
        _VCollabAPI.xSetCAELegendColors(sModel,fLegColorsList);
    if bReverse : bRevLeg = True; 
    if bRevLeg : _VCollabAPI.xSetCAEReverseLegend(sModel,bRevLeg);
    return;
#--------------------------------------------------------------
def SetCustomLegend_UserColor(bIsGrey=False):
    '''
        Sets custom legend (Number of palette colors = 9)
        Parameters:
            bIsGrey (boolean): If True set the grey color for bottom value (optional)
        Returns:
             None
    '''
    import array;
    fColorVec = array.array('f');
    nColors = 9;
    #Initialise to 0.0
    for i in range(0,nColors*3): fColorVec.append(0.0);
    #Set specific Values
    i=0;
    fColorVec[i]=1.0;fColorVec[i+1]=0.0;fColorVec[i+2]=0.0; i=i+3; # Red

    fColorVec[i]=0.96;fColorVec[i+1]=0.6;fColorVec[i+2]=0.0; i=i+3;
    fColorVec[i]=0.9;fColorVec[i+1]=0.9;fColorVec[i+2]=0.0; i=i+3;
    fColorVec[i]=0.6;fColorVec[i+1]=0.96;fColorVec[i+2]=0.0; i=i+3;

    fColorVec[i]=0.0;fColorVec[i+1]=1.0;fColorVec[i+2]=0.0; i=i+3; # Green

    fColorVec[i]=0.0;fColorVec[i+1]=0.96;fColorVec[i+2]=0.6; i=i+3;
    fColorVec[i]=0.0;fColorVec[i+1]=0.9;fColorVec[i+2]=0.9; i=i+3;
    fColorVec[i]=0.0;fColorVec[i+1]=0.6;fColorVec[i+2]=0.96; i=i+3;
    if bIsGrey :
        fColorVec[i]=0.9;fColorVec[i+1]=0.9;fColorVec[i+2]=0.9; i=i+3; # Grey
    else:
        fColorVec[i]=0.0;fColorVec[i+1]=0.0;fColorVec[i+2]=1.0; i=i+3; # Blue
    
    _VCollabAPI.xSetCAELegendColors(sModel,fColorVec);
      
    return;
#--------------------------------------------------------------
def SetLabelPrecision(sModel,iprecision,bScientific):
    _VCollabAPI.xSetCAEProbeLabelDefaultNumericalFormat(sModel,iprecision,bScientific);
    _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,bScientific,iprecision); #Column Precision
    return
def SetLegendPrecisionMaxMin(sModel,fMax,fMin):
    '''
        Sets legend precision 
        Parameters:
            sModel: Cax model name
            fMax: Maximum legend value
            fMin: Minimum legend value
        Returns:
             None
    '''
    iprecision = -1;
    fabsMax = max(abs(fMax),abs(fMin));
    if fabsMax > 1.0E6 or fabsMax < 1.0E-4 or abs(fMax-fMin) < 1.0E-3 :
        _VCollabAPI.xSetCAELegendNumeric(sModel,True,4);
        _VCollabAPI.xSetCAEProbeLabelDefaultNumericalFormat(sModel,iprecision,True);
        _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,True,iprecision); #Column Precision
        return;
    iprecision = 3;
    if fabsMax < 0.01 : iprecision = 4;
    if fabsMax > 10 : iprecision = 2;
    if fabsMax > 1.0E3 : iprecision = 0;
    if abs(fMax-fMin) < 0.01 : iprecision = 3;
    _VCollabAPI.xSetCAELegendNumeric(sModel,False,iprecision);
    #
    _VCollabAPI.xSetCAEProbeLabelDefaultNumericalFormat(sModel,iprecision,False);
    _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,False,iprecision); #Column Precision
    return;
#-------------------------------------------------------------------------------------
def SetLegendLimits(fMatLimit=250,fResLimit=None,nColors=0):
    '''
        Set legend limits
        Parameters:
            fMatLimit: Premax legend value (optional)
            fResLimit: User range max value (optional)
            nColors: Number of palette colors (optional)
        Returns:
             None
    '''
    if nColors > 3:
        bReverse = _VCollabAPI.xGetCAEReverseLegend(sModel);
        _VCollabAPI.xSetCAEReverseLegend(sModel,False);
        if hasattr(_VCollabAPI,'xSetCAELegendDefaultColors'):
            _VCollabAPI.xSetCAELegendDefaultColors(sModel,nColors);
        else:
            SetCustomLegend();
        _VCollabAPI.xSetCAEReverseLegend(sModel,bReverse);
    #--
    bAllInst = True;bUserMax=True;bUserMin=True;
    if fResLimit == None:
        fUserMax = fMatLimit*2.0;
    else:
        fUserMax = fResLimit;
    if fMatLimit > fUserMax : fUserMax = fMatLimit*2.0;
    fUserMin = 0.0;
    _VCollabAPI.xSetCAELegendRangeEx(sModel,bAllInst,bUserMax,fUserMax,bUserMin,fUserMin,False);
    _VCollabAPI.xSetCAELegendDynamicRangeEx(sModel,0.0,fMatLimit);
    _VCollabAPI.xSetCAELegendNumeric(sModel,False,0);
    if hasattr(_VCollabAPI,'xSetCAEProbeLabelDefaultNumericalFormat'):
        _VCollabAPI.xSetCAEProbeLabelDefaultNumericalFormat(sModel,0,False);
    _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,False,0); #Column Precision
    return;
#---------------------------------------------------------------------------------
def SetLegendParams(CustMax=None,CustMin=None,LegMax=None,LegMin=None,iPrecision=-1,bDiscrete=-1,bReverse=-1,nColors=0):
    '''
    Sets custom legend  
    Parameters:
        CustMax: Pre max legend value (optional)
        CustMin: Pre min legend value (optional)            
        LegMax: User max legend value (optional)
        LegMin: User min legend value (optional)            
        iPrecision: Legend precision value (optional)
        bDiscrete: Discrete legend (optional)
        bReverse: Reverse legend (optional)
        nColors: Number of colors (optional)
    Returns:
         None
    '''
    bAllInst = True;
    if nColors > 2:
        bReverse = _VCollabAPI.xGetCAEReverseLegend(sModel);
        _VCollabAPI.xSetCAEReverseLegend(sModel,False);
        _VCollabAPI.xSetCAELegendDefaultColors(sModel,nColors);
        _VCollabAPI.xSetCAEReverseLegend(sModel,bReverse);
        
    if bDiscrete >= 0 :
        bFlag = True;
        if bDiscrete == 0 : bFlag = False;
        _VCollabAPI.xSetCAEDiscreteLegend(sModel,bFlag);
        
    if bReverse >= 0 :
        bFlag = False;
        if bDiscrete > 0 : bFlag = True;
        _VCollabAPI.xSetCAEReverseLegend(sModel,bFlag);
    #-Modified on 05 Sep 2021
    SetDynamicLegend(CustMax,CustMin,LegMax,LegMin,bAllInst);
    if iPrecision >= 0:
        fLegendInfo = _VCollabAPI.pxGetCAELegendRange(sModel);
        fLGDMax = fLegendInfo[1];fLGDMin = fLegendInfo[3];
        iP = iPrecision;
        _VCollabAPI.xSetCAELegendAutoFormatMode(sModel,False);
        bScientific = False; MaxVal = 1.0E4;
        if iP > 3 : MaxVal = pow(10.0,iP);
        MinVal = 1.0/MaxVal;
        if (fLGDMax-fLGDMin) > MaxVal or (fLGDMax-fLGDMin) < MinVal :
            bScientific = True;
        _VCollabAPI.xSetCAELegendNumeric(sModel,bScientific,iP);
        if hasattr(_VCollabAPI,'xSetCAEProbeLabelDefaultNumericalFormat'):
            _VCollabAPI.xSetCAEProbeLabelDefaultNumericalFormat(sModel,iP,bScientific);
        _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,bScientific,iP); #Column Precision
    return;
#==================================================================
def SetDefaultAttributes():
    '''
    Sets the probe label and notes font, font size and background color
    Parameters:
        None
    Returns:
         None
    '''
    #-----Set 2D Note Fonts-----
    sFontName = u"Arial Bold";
    iFontSize = 18;
    iR = 0;iG=0;iB=0; 
    _VCollabAPI.xSetNotesFont(sFontName,iFontSize,iR,iG,iB);
    iR = 255;iG=255;iB=230;
    _VCollabAPI.xSetNotesBackground(True,iR,iG,iB);
    #-------Set hotspot Label arrange mode
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);# Compact Mode
    #-----------------
    _VCollabAPI.xSetCAEProbeType(sModel,1); #1 for CurrentResult-Derived
    sFontName = u"Arial Narrow Bold";
    iFontSize = 16;
    _VCollabAPI.xSetCAEProbeLabelFont(sModel,sFontName,iFontSize);
    #-------
    _VCollabAPI.xShowCAEVectorPlot (sModel,False);
    _VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xDeleteXYPlot(u"");
    #-----------------
    global fgDefZoneRadius;
    fgDefZoneRadius = GetZoneRadius();
    return;
#==================================================================
#-- Functions for SHOW/Hide Parts
#=============================================================
def HideAllParts():
    '''
    Hides all the part
    Parameters:
        None
    Returns:
         None
    '''
    _VCollabAPI.xShowAll(sModel);
    _VCollabAPI.xInvertShow(sModel);
    _VCollabAPI.xRefreshDialogs();
    return;
#=============================================
def ShowOnePart(sPart,bFitView=False):
    '''
    Shows one part
    Parameters:
        sPart: Part name (wild card char * can be used for part names)
        bFitView (boolean): Fit the displayed part to the screen
    Returns:
         sPart: If the part is available
         None: If part not available 
    '''
    _VCollabAPI.xShowAll(sModel);
    sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
    for aPart in  sPartList:
        if IsSubString(aPart,sPart,True):
            _VCollabAPI.xDisplayOnePart(sModel,aPart,bFitView);
            return aPart;
    return None;
def ShowOnlyPartList(sPartList):
    '''
    Shows only the listed part (Exact part name is required)
    Parameters:
        sPartList (list): Parts list to be displayed
    Returns:
         None  
    '''
    _VCollabAPI.xShowAll(sModel);
    _VCollabAPI.xInvertShow(sModel); # Hide All Parts
    for aPart in  sPartList:
        _VCollabAPI.xShowPart(sModel,aPart,True);
    #-- end for
    return;
#-------------------------------------------------
def ShowTheseParts(sInpParts,bFlag=True):
    '''
    Shows only the listed part
    Parameters:
        sInpParts (list): Parts list to be displayed (wild card char * can be used for part names)
        bFlag: Show/Hide parts (optional)
    Returns:
         None
    '''
    _VCollabAPI.xShowAll(sModel);
    sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
    _VCollabAPI.xInvertShow(sModel);
    for aPart in  sPartList:
        for sPart in sInpParts:
            if IsSubString(aPart,sPart,True):
                _VCollabAPI.xShowPart(sModel,aPart,bFlag);
    #-- end for
    _VCollabAPI.xDeselectAll(sModel);
    return None;
#-------------------------------------
def GetValidParts(sPartString,bShowFlag = False,bOnly=False):
    '''
    Returns a full part name of a part and shows only that part
    Parameters:
        sPartString: Part name (wild card char * can be used for part names)
        bShowFlag (boolean): Show the selected part (optional)
        bOnly (boolean): Hides all the parts (optional)
    Returns:
         sSelectedParts (list): Full part name of the selected part 
    '''
    sPartList = _VCollabAPI.pxGetPartsList(sModel,"",0);
    sSelectedParts = [];
    if bOnly : 
        _VCollabAPI.xShowAll(sModel);
        _VCollabAPI.xInvertShow(sModel);
    for aPart in  sPartList:
        if IsSubString(aPart,sPartString,True):
            sSelectedParts.append(aPart);
            if bShowFlag : _VCollabAPI.xShowPart(sModel,aPart,True);
    return sSelectedParts;
#----------------------------------------------------
def GetValidPartsList(sWildPartsList,bShowFlag = False,bOnly=False):
    '''
    Returns a full part name of the parts and shows only those parts
    Parameters:
        sWildPartsList (list): Parts list to be displayed (wild card char * can be used for part names)
        bShowFlag (boolean): Show the selected parts (optional)
        bOnly (boolean): Hides all the parts (optional)
    Returns:
         sSelectedParts (list): Full part name of the selected parts 
    '''
    sPartList = _VCollabAPI.pxGetPartsList(sModel,"",0);
    sSelectedParts = [];
    if bOnly : 
        _VCollabAPI.xShowAll(sModel);
        _VCollabAPI.xInvertShow(sModel);
    for aPart in  sPartList:
        for sPartString in sWildPartsList:
            if IsSubString(aPart,sPartString,True):
                sSelectedParts.append(aPart);
                if bShowFlag : _VCollabAPI.xShowPart(sModel,aPart,True);
                break;
    return sSelectedParts;
#--------------------------------------------------------
def GetValidPartsCMD(sVals,bShowFlag = True,bOnly=True):
    '''
    Returns a full part name of the parts and shows only those parts
    Parameters:
        sVals (list): Parts list to be displayed (wild card char * can be used for part names)
        bShowFlag (boolean): Show the selected parts (optional)
        bOnly (boolean): Hides all the parts (optional)
    Returns:
         sSelectedParts (list): Full part name of the selected parts 
    '''
    sPartList = _VCollabAPI.pxGetPartsList(sModel,"",0);
    sSelectedParts = [];
    #icount = 0;
    if bOnly : # Hide All Parts
        _VCollabAPI.xShowAll(sModel);
        _VCollabAPI.xInvertShow(sModel);
    for sPartString in sVals:
        for aPart in  sPartList:
            if IsSubString(aPart,sPartString,True):
                sSelectedParts.append(aPart);
                if bShowFlag : _VCollabAPI.xShowPart(sModel,aPart,True);
    return sSelectedParts;
#-------------------------------------------------------
#FILTER_PARTS,fMin,fMax,bFitView
def CAEFilterPartsCMD(sVals):
    nVals = len(sVals);
    fRangeMin = None; fRangeMax = None;
    if nVals > 0: fRangeMin = GetFloat(sVals[0],None);
    if nVals > 1: fRangeMax = GetFloat(sVals[1],None);
    bFitView = True;
    if nVals > 2 and sVals[2] != 'Y' : bFitView = False;
    bEnableRangeMin=True;
    if fRangeMin == None : 
        bEnableRangeMin=False; fRangeMin = 0.0;
    bEnableRangeMax=True;
    if fRangeMax == None : 
        bEnableRangeMax=False; fRangeMax = fRangeMin + 1.0;
    #
    _VCollabAPI.xSetCAELegendRange(sModel,bEnableRangeMax,fRangeMax,bEnableRangeMin,fRangeMin,False);
    _VCollabAPI.xFilterCAEParts(sModel);
    if bFitView: _VCollabAPI.xFitView();
    _VCollabAPI.xSetCAELegendRange(sModel,False,0.0,False,1.0,False);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return;
#--------------------------------------------------------
#=======================================================
#=======================================================
def GetModelRealName(sModel):
    '''
    Returns the model file attribute of the cax model
    Parameters:
        sModel: CAX model name
    Returns:
         ModelFileName: Model file attribute
    '''
    sCaxPath = _VCollabAPI.xGetFileName(sModel);
    ModelFileName = os.path.basename(sCaxPath);
    MoAtt = _VCollabAPI.pxGetModelAttribKeys(sModel);
    for att in MoAtt:
        flag = att.find(u"Model File")
        if flag >= 0 :
            ModelFileName = _VCollabAPI.xGetModelAttribValue(sModel, att);
            break;
    #---
    return ModelFileName;
#=======================================================
#--- Result Related Functions ---
#=======================================================
def IsResultPresent(aModel,sNewRes):
    '''
    Checks if the is result is available in the given model
    Parameters:
        aModel: Cax model name
        sNewRes: Exact result name
    Returns:
         boolean: True if the result is available
    '''
    sResultList = _VCollabAPI.pxGetCAEResultsList(aModel);
    for sResult in sResultList:
        if IsSameString(sResult,sNewRes):
            return True;
    return False;
#===================================================
def SelectResult(aModel,sRefName="*Stress*Von*",bSetResult=True,nIns=0):
    '''
    Sets the selected result as current result and returns the full result name
    Parameters:
        aModel: Cax model name
        sRefName: Result name (optional) (Wild card char * can be used for result name)
        bSetResult (boolean): If True sets the selected result as current result (optional)
        nIns : Instance number (0=first or -1 = last)
    Returns:
         sResult: Full result name
         None: If the selected result is not found
    '''
    sResRef = sRefName;
    if sResRef[0] != '*' : sResRef = '*'+sResRef;
    if sResRef[-1] != '*' : sResRef = sResRef+'*';
    sResultList = _VCollabAPI.pxGetCAEResultsList(aModel);
    for sResult in sResultList:
        if IsSubString(sResult,sResRef,True):
            if bSetResult:
                sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(aModel,sResult);
                sInstanceList = _VCollabAPI.pxGetCAEInstanceList(aModel,sResult);
                sCurInst = sInstanceList[nIns];
                _VCollabAPI.xSetCAEResult(aModel,sResult,sCurInst,sDerived);
            return sResult;
            break;
    #--- End for
    return None;
#==============================================================
def SetCurResult(aModel,sResult,sDerived=None,InstId=0):
    '''
    Sets selected result as the current result
    Parameters:
        aModel: Cax model name
        sResult: Result name
        sDerived: Derived result name (optional)
        InstId (int): Instance Id (optional)
    Returns:
         boolean: True if successfully set the selected result as current result
         None: If the selected result is not found
    '''
    if sDerived == None:
        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(aModel,sResult);
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(aModel,sResult);
    if len(sInstanceList) < 1:
        sgNotify("Error",f"RResult {sResult} not found?",15);return;
    if abs(InstId) >= len(sInstanceList) : InstId = -1;
    sCurInst = sInstanceList[InstId];
    return _VCollabAPI.xSetCAEResult(aModel,sResult,sCurInst,sDerived);
#==========================================================
def SearchResults(aModel,sRefName="*Stress*",bAllResult=False,iTypes = []):
    '''
    Searches for a result and returns the result name
    Parameters:
        aModel: Cax model name
        sRefName: Result name (optional) (Wild card char * can be used for result name)
        bAllResult (boolean): True for all results (optional)
        iTypes (list): Result type index (optional)
                        case 0 - NODAL_SCALAR
                        case 1 - NODAL_VECTOR
                        case 2 - NODAL_SIXDOF
                        case 3 - NODAL_TENSOR
                        case 4 - ELEMENTAL_SCALAR
                        case 5 - ELEMENTAL_VECTOR
                        case 6 - ELEMENTAL_SIXDOF
                        case 7 - ELEMENTAL_TENSOR
                        case 8 - ELEMENT_NODAL_SCALAR
                        case 9 - ELEMENT_NODAL_VECTOR
                        case 10- ELEMENT_NODAL_SIXDOF
                        case 11- ELEMENT_NODAL_TENSOR
    Returns:
        sSelected (list): Full Result name 
    '''
    sgResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
    sSelected = [];
    bTypeCheck = False;
    if len(iTypes) > 0 : bTypeCheck = True;
    for sResult in sgResultList:
        if bTypeCheck:
            resType = _VCollabAPI.xGetCAEResultType(sModel,sResult);
            bFlag = False;
            for itype in iTypes:
                if itype == resType :
                    bFlag = True;break;
            if bFlag == False : continue;
        if IsSubString(sResult,sRefName,True):
            sSelected.append(sResult);
            if bAllResult == False :
                return sSelected;
    #--- End for
    return sSelected;
#================================================================
def GetDerivedResult(sModel,sResult):
    '''
    Gets the derived result for the given result name
    Parameters:
        sModel: Cax model name
        sResult: Result name
    Returns:
         Derived result name
    '''
    sDefDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
    if len(sgDerivedType) < 1 : return sDefDerived;
    if IsSubString(sDefDerived,sgDerivedType,True) : return sDefDerived;
    sDerivedList = _VCollabAPI.pxGetCAEDerivedResults(sModel,sResult);
    for sDerived in sDerivedList:
        if IsSubString(sDerived,sgDerivedType,True) == False : continue;
        return sDerived;
    return sDefDerived;
#========================================================
def SetResultPrecisionMaxMin(sModel,fMax,fMin):
    '''
    Sets precision for legend and probe tables basesd on the result value
    if Max value > 1.0E6 or Min value < 1.0E-3 : precision = 3
    if Max value < 0.01 : precision = 4;
    if Max value > 10 : precision = 2;
    if Max value > 1.0E4 : precision = 1;
    
    Parameters:
        sModel: Cax model name
        fMax: Maximum result value
        fMin: Minimum result value
    Returns:
         None
    '''
    _VCollabAPI.xSetCAELegendAutoFormatMode(sModel,False);
    iprecision = -1;
    fAMax = abs(fMax);#fAMin = abs(fMin);
    if fAMax > 1.0E6 or fAMax < 1.0E-3 or abs(fMax-fMin) < 1.0E-3 :
        _VCollabAPI.xSetCAELegendNumeric(sModel,True,3);
        _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,True,3);
        return;
    iprecision = 3;
    if fAMax < 0.01 : iprecision = 4;
    if fAMax > 10 : iprecision = 2;
    if fAMax > 1.0E4 : iprecision = 1;
    _VCollabAPI.xSetCAELegendNumeric(sModel,False,iprecision);
    _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,False,iprecision);
    return;
#=============================================================================
#
def GetMaxMinInstanceForResult(sModel,sResult=None,sDerived=None):
    '''
    Gets the maximum and minimum result instances of the selected result or current result
    Parameters:
        sModel: Cax model name
        sResult: Result name (optional)
        sDerived: Derived result name (optional)
    Returns:
         sMaxInst,sMinInst : Maximum instance name and Minimum instance name
    '''
    if sResult == None : # Use current Result
        sResList = _VCollabAPI.pxGetCAECurrentResult(sModel);
        sResult = sResList[0];
        if sDerived == None : sDerived = sResList[2];
    #
    if sDerived == None : # Get Default Derived result
        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(u"",sResult);
    #
    PrintMessage(u"In GetMaxMinInstance " + sResult + u" " + sDerived);
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    icount = len(sInstanceList);
    sMaxInst = u""; fInstMax = -1.0E15;fInstMin=1.0E15;sMinInst = u"";
    if icount < 1 : # Error?
        return sMaxInst,sMinInst;
    sMaxInst = sInstanceList[0]; sMinInst= sInstanceList[0];
    if icount == 1 :
        return sMaxInst,sMinInst;
    icount = 0; sInst = u"";
    for icount in range(0,len(sInstanceList)):
        fMax = 0.0; fMin = 0.0; 
        sInst = sInstanceList[icount];
        fMinMaxList = _VCollabAPI.pxGetResultMinMax(u"",sResult,sInst,sDerived);
        if len(fMinMaxList) < 2: #Error
            PrintMessage(u"pxGetResultMinMax Failed " + sResult + u" " + sInst + u" " + sDerived);
            continue;
        fMax = fMinMaxList[1]; fMin = fMinMaxList[0];
        if fMax > fInstMax :
            fInstMax = fMax; sMaxInst = sInst;
        if fMin < fInstMin :
            fInstMin = fMin; sMinInst = sInst;
    #
    #PrintMessage(u"Max Instance for " + sResult + u" " + sMaxInst + u" "+ str(fInstMax));
    return sMaxInst, sMinInst;
#================================================================
def SelectInstance(sModel,sResult = None,sDerived = None,InstFlag=0):
    '''
    Gets the instance name for the selected instance 
    Parameters:
        sModel: Cax model name
        sResult: Result name (optional)
        sDerived: Derived result name (optional)
        InstFlag: 0 => Last Instance, 1 => Max Instance, 2 => Min Instance, 3 => First Instance, else current Instance (optional)
    Returns:
         Null string: If the selected result does not have any instance or for invalid result name
         return the instance name
    '''
    #--- InstFlag= 0 => Last Instance, 1 => Max Instance, 2 => Min Instance, 
    #---           3 => First Instance, else current Instance
    if sResult == None or len(sResult) < 1:
        PrintErrorMessage("SelectInstance Failed, No Result Name?");
        return "";
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    icount = len(sInstanceList);
    if icount < 1:
        PrintErrorMessage(sResult+" has No Instances?, Result not valid");
        return "";
    if icount == 1:
        return sInstanceList[0];
    if InstFlag == 0: # Last Instance
        return sInstanceList[-1];
    if InstFlag == 3: # First Instance
        return sInstanceList[0];
    if InstFlag > 4 : # Current Instance?
        sResList = _VCollabAPI.pxGetCAECurrentResult(sModel);
        return sResList[1];
    if sDerived == None : # Get Default Derived result
        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
    #-- Search for Max, Min Instance-----
    fInstMax = -1.0E15;fInstMin=1.0E15;
    sMaxInst = sInstanceList[0]; sMinInst= sInstanceList[0];
    fMinMaxList = _VCollabAPI.pxGetResultMinMax(sModel,sResult,sMaxInst,sDerived);
    if len(fMinMaxList) >= 2:
        fInstMax = fMinMaxList[1]; fInstMin = fMinMaxList[0];
    icount = 0; sInst = u"";
    for icount in range(1,len(sInstanceList)):
        fMax = 0.0; fMin = 0.0; 
        sInst = sInstanceList[icount];
        fMinMaxList = _VCollabAPI.pxGetResultMinMax(u"",sResult,sInst,sDerived);
        if len(fMinMaxList) < 2: #Error
            PrintMessage(u"pxGetResultMinMax Failed " + sResult + u" " + sInst + u" " + sDerived);
            continue;
        fMax = fMinMaxList[1]; fMin = fMinMaxList[0];
        if fMax > fInstMax :
            fInstMax = fMax; sMaxInst = sInst;
        if fMin < fInstMin :
            fInstMin = fMin; sMinInst = sInst;
    #----end for
    #PrintDebugMessage(u"Max Instance for " + sResult + u" " + sMaxInst + u" "+ str(fInstMax));
    if InstFlag == 1:
        return sMaxInst;
    if InstFlag == 2:
        return sMinInst;
    return sMaxInst;
#-----------------------------------------
ig_FirstInstance=None;ig_LastInstance = None;
#-------------------------------------------------------------
def GetInstanceList(sResult):
    '''
    Gets the instances list for the selected result
    Parameters:
        sResult: Result name
    Returns:
         lgLoadCaseList (list): List of instances name
    '''
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    lgLoadCaseList =[];
    nInst = 0;
    for sInst in sInstanceList:
        nInst = nInst+1;
        if ig_FirstInstance!= None:
            if ig_FirstInstance > nInst: continue;
        if ig_LastInstance!= None:
            if ig_LastInstance < nInst: break;
        lgLoadCaseList.append(sInst);
    return lgLoadCaseList;
#-------------------------------------------------------
def GetMachingInstanceList(sResult,sMatch="L*M*"):
    '''
    Gets the matching instances
    Parameters:
        sResult: Result name
        sMatch: Instance name (Wild card char * can be used for the instance name)(optional)
    Returns:
         lgLoadCaseList (list): Instances list
    '''
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    lgLoadCaseList =[];
    nInst = 0;
    for sInst in sInstanceList:
        nInst = nInst+1;
        if IsSubString(sInst,sMatch,True) == False: continue;
        lgLoadCaseList.append(sInst);
    return lgLoadCaseList;
#-------------------------------------------------------
def CreateEnvelopResult(sResultStr,sDerived,bMax=True):
    '''
    Creates Max/Min envelope result
    Parameters:
        sResultStr: Result name (Wild card char * can be used for result name)
        sDerived: Derived result name
        bMax (boolean): True for max envelope, False for min envelope (optional)
    Returns:
         sEnvResult: Selected result full name 
         None: If the selected result does not exists
    '''
    if bMax:
        sEnvResult = SelectResult(sModel,'*Max*Envelop*'+sResultStr,False);
    else:
        sEnvResult = SelectResult(sModel,'*Min*Envelop*'+sResultStr,False);
    if sEnvResult!= None:
        PrintMessage("Envelop Result "+ sEnvResult + " Exists");
        return sEnvResult;
    sResult = SelectResult(sModel,sResultStr,True);
    if sResult == None:
        PrintErrorMessage(sResultStr,"Not Found Result=");
        return None;
    _VCollabAPI.xRefreshDialogs();
    #sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    if len(sDerived) < 1 or sDerived.upper() == 'N':
        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
    #PopMessage(sCurResInfo,[sResult,sDerived,bMax]);
    if bMax:
        _VCollabAPI.xCreateCAEEnvelopeResult(sModel,sResult,sDerived,True,False);
    else:
        _VCollabAPI.xCreateCAEEnvelopeResult(sModel,sResult,sDerived,False,True);
    if bMax:
        sEnvResult = SelectResult(sModel,'*Max*Envelop*'+sResultStr,False);
    else:
        sEnvResult = SelectResult(sModel,'*Min*Envelop*'+sResultStr,False);
    _VCollabAPI.xRefreshDialogs();
    return sEnvResult;
#-----------------------------------------------------------
#========================================================
#-- Modal Result Related Functions ----
#=================== For Modal Views =========================
def GetCAEModalFrequency(sResult,sInst):
    '''
    Gets the frequency values for the selected instance
    Parameters:
        sResult: Result name 
        sInst: Instance name
    Returns:
         sValue (float): Frequency value
         0.0 (float): if the frequency value is less than 1 
    '''
    sKey = u"Frequency"; 
    sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
    if len(sValue) < 1 : return 0.0;
    return float(sValue);
def GetCAEModalEigenValue(sResult,sInst):
    '''
    Gets the eigen values for the selected instance
    Parameters:
        sResult: Result name 
        sInst: Instance name
    Returns:
         sValue (float): Eigen value
         0.0 (float): if the eigen value is less than 1 
    '''
    sKey = u"Eigenvalue"; 
    sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
    if len(sValue) < 1 : return 0.0;
    return float(sValue);
#-----------------------------------------------------
#-----------------------------------------------------
sModalResultName = "Displacement";
igEigenMode = 1;
def IsModalResult():
    '''
    Checks if the result is modal result
    Parameters:
        None
    Returns:
         boolean: True if its modal result, False if its not modal result
    '''
    global sModalResultName;
    global igEigenMode;
    igEigenMode=0;
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];sInst = sCurResInfo[1];
    if IsSubString(sResult,"DISP") == False :
        sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
        sResult = u"";
        for aResult in sResultList:
            if IsSubString(aResult,"DISP"):
                sResult = aResult;
                break;
            if IsSubString(aResult,"VELOCITY"):
                sResult = aResult;
                break;
            if IsSubString(aResult,"ACCELERATION"):
                sResult = aResult;
                break;
    #-------------------
    if len(sResult) < 1:
        PrintMessage("Displacement Result Not Found");
        return False;
    if len(sInst) < 1:
        sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
        sInst = sInstanceList[-1]; # Last Instance
    sKey = u"Frequency"; 
    sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
    igEigenMode = 1;
    if len(sValue) < 1 : 
        igEigenMode = 2;
        sKey = u"Eigenvalue"; 
        sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
        if len(sValue) < 1 :
            igEigenMode = 0;
            return False;
    sModalResultName = sResult;
    return True;
#----------------------------------------------
def IsModalResultOld():
    '''
    Checks if the result is modal result
    Parameters:
        None
    Returns:
         boolean: True if its modal result, False if its not modal result
    '''
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];sInst = sCurResInfo[1];
    if IsSubString(sResult,"DISP") == False :
        sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
        sResult = u"";
        for aResult in sResultList:
            if IsSubString(aResult,"DISP"):
                sResult = aResult;
                break;
    #-------------------
    if len(sResult) < 1:
        PrintMessage("Displacement Result Not Found");
        return False;
    if len(sInst) < 1:
        sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
        sInst = sInstanceList[-1]; # Last Instance
    sKey = u"Frequency"; 
    sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
    if len(sValue) < 1 : return False;
    return True;
#--------------------------------------------------
def DisplayFrequencyLabel(sText,fValue,fPosX=0.35,fPosY=0.08):
    '''
    Adds a frequency label 
    Parameters:
        sText: Text to add to the label
        fValue: Frequency value to add to the label
        fPosX: Screen X position for the label (optional)
        fPosY: Screen Y position for the label (optional)
    Returns:
         None
    '''
    sNoteString = sText+u"Frequency = " + Float2String(fValue);
    _VCollabAPI.xAdd2DNotes(sNoteString,fPosX,fPosY,True);
    return;
def DisplayEigenLabel(sText,fValue,fPosX=0.35,fPosY=0.08):
    '''
    Adds a Eigen value label 
    Parameters:
        sText: Text to add to the label
        fValue: Eigen value to add to the label
        fPosX: Screen X position for the label (optional)
        fPosY: Screen Y position for the label (optional)
    Returns:
         None
    '''
    sNoteString = sText+u"EigenValue = " + Float2String(fValue);
    _VCollabAPI.xAdd2DNotes(sNoteString,fPosX,fPosY,True);
    return;
def DisplayFrequencyLabels(sText,fValue1,fValue2,fPosX=0.35,fPosY=0.08):
    '''
    Adds a frequency and Eigen value label 
    Parameters:
        sText: Text to add to the label
        fValue: Frequency value to add to the label
        fPosX: Screen X position for the label (optional)
        fPosY: Screen Y position for the label (optional)
    Returns:
         None
    '''
    if(fValue2) > 1E-10:
        sNoteString = sText+u"Frequency = " + Float2String(fValue1)+"  ,  "+u"EigenValue = " + Float2String(fValue2);
    else:
        sNoteString = sText+u"Frequency = " + Float2String(fValue1);
    _VCollabAPI.xAdd2DNotes(sNoteString,fPosX,fPosY,True);
    return;
#--------------------------------------------
def SetModalAnimation(iType = 3,bStaticFringe=False):
    '''
    Sets modal animation
    Parameters:
        iType (Valid Range 0-3): Sets animation type (optional)                
                0-LINEAR
                1-TRANSIENT
                2-RESULTS
                3-EIGEN_VECTOR

        bStaticFringe (boolean): Sets static fringe flag (optional)
    Returns:
         None    
    '''
    sModel = _VCollabAPI.xGetCurCAEModelName();
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xSetCAEDiscreteLegend(sModel,False);
    iNoOfFrames = 24;
    #iType = 3; #linear,transient,result,harmonic
    bHarmonic = False; bSwing = False;
    sSelectedFrames = u"";
    sSelectedFrames = u"Displacement";
    bReserved1 = False; bReserved2 = False;
    _VCollabAPI.xSetCAEDeformBoundPercentage(6.0);
    _VCollabAPI.xSetCAEAnimationSpeed(sModel,40);
    _VCollabAPI.xSetCAEAnimationSettings(sModel,iType,iNoOfFrames,bHarmonic,bSwing,bStaticFringe,
                                         sSelectedFrames,bReserved1,bReserved2);
    _VCollabAPI.xRefreshDialogs();
    return;
#----------------------------------------------
#--------- Create Specific Modal views ----
def CreateModalViews(nCount=5,bTableView=False):
    '''
    Creates the modal views
    Parameters:
        nCount (int): The number of modal views (optional)
        bTableView (boolean): If True adds the mode table (optional)
    Returns:
       None      
    '''
    #Set CAE Display Settings
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xShowCAELegend(sModel,True);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    _VCollabAPI.xSetCAEDiscreteLegend(sModel,False);
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);
    sResName = u"Displacement";
    sModeList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResName);
    sDefDerivedResult = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResName);
    #
    sViewPathName = u"ModeShape Report"
    #_VCollabAPI.xShowAll(sModel);
    _VCollabAPI.xRefreshDialogs();
    fRefValue = 0.0;
    count = 1;
    for sModeName in sModeList:
        sMode = u"Mode" + str(count);
        bRtnFlag = _VCollabAPI.xSetCAEResult(sModel,sResName,sModeName,sDefDerivedResult);
        if bRtnFlag == False: 
            PrintMessage(_VCollabAPI.xGetLastError(),"xSetCAEResult Failed");
            continue;
        fValue = GetCAEModalFrequency(sResName,sModeName);
        if abs(fValue - fRefValue) < 0.1: continue;
        fRefValue = fValue;
        _VCollabAPI.xDeleteAllLabels();
        fEigen = GetCAEModalEigenValue(sResName,sModeName);
        DisplayFrequencyLabel("Mode shape:",fRefValue);
        # Create Viewpoint
        sViewPointName = u"VP - " + sMode.replace(':','-');
        SetModalAnimation(3,True);
        _VCollabAPI.xAddViewPoint(sViewPointName,sViewPathName,-1);
        _VCollabAPI.xSetCAEAnimationInCurViewPoint(True);
        count = count + 1;
        if count > nCount : break; 
    #================================================================
    if bTableView == False : return;
    fRefValue = 0.0;
    count = 1;
    dx=0.30;dy=0.08;
    _VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xHideAllParts(sModel);
    _VCollabAPI.xShowCAELegend(sModel,False);
    _VCollabAPI.xAdd2DNotes("Mode Shapes Table" ,dx,dy,True);
    dy = dy + 0.1;
    for sModeName in sModeList:
        sMode = u"Mode" + str(count);
        bRtnFlag = _VCollabAPI.xSetCAEResult(sModel,sResName,sModeName,sDefDerivedResult)
        if bRtnFlag == False: 
            PrintMessage(_VCollabAPI.xGetLastError(),"Error from xSetCAEResult");
            continue
        fValue = GetCAEModalFrequency(sResName,sModeName);
        if abs(fValue - fRefValue) < 0.1: continue;
        fRefValue = fValue;
        fEigen = GetCAEModalEigenValue(sResName,sModeName);
        DisplayFrequencyLabels(sMode+" ",fRefValue,fEigen,dx,dy);
        dy = dy + 0.04;
        count = count + 1;
        if count > nCount : break; 
    # Create Viewpoint
    sViewPointName = u"VP - " + "Table";
    AddVP_HF(sViewPointName,sViewPathName,-1);
    return;
#===========================End of Modal Report ==========================
#==================================================================
# --- Node set Related Functions -----
#===================================================================
def GetNodeSetList(sNodeSetString):
    '''
    Return the list of nodesets matching with the nodeset name
    Parameters:
        sNodeSetString: Nodeset name
    Returns:
         SelectedNodeSetList (list): List of nodesets
    '''
    SelectedNodeSetList = [];
    sNodeSetList = _VCollabAPI.pxGetCAENodeSetList(sModel);
    for aNodeSet in  sNodeSetList:
        if IsSubString(aNodeSet,sNodeSetString,True):
            SelectedNodeSetList.append(aNodeSet);
    return SelectedNodeSetList;
#-----------------------------------------------------
def CreatePartNodeSet(sNodeSetName,sPartList,sRefPartList=[]):
    '''
    Creates or adds nodes to the nodeset from the part list provided 
    Parameters:
        sNodeSetName: Name of the nodeset
        sPartList (list): List of part names to be added to the nodeset
        sRefPartList (list): List of part names to be added to the node set, if its empty adds visible parts (optional)
    Returns:
         None:    
    '''
    if sRefPartList == None or len(sRefPartList) < 1:
        sRefPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
        if len(sRefPartList) < 1 : return False;
    #Select All Mask Parts in List
    for sPart in sPartList:
        _VCollabAPI.xSelectNodeEx(sModel,sPart, 0, 1);
        #_VCollabAPI.xShowPart(sModel,sPart,True);
    _VCollabAPI.xSetNodeSetPreviewMode(False);
    sDummy = "__DummyNodeSet";
    _VCollabAPI.xCreateNodeSetFromSelectedParts(sModel, sDummy);
    NodeList = _VCollabAPI.pxGetNodeIDsFromNodeSet(sModel,[],sDummy);
    _VCollabAPI.xDeselectAll(sModel);
    _VCollabAPI.xNodeSetDelete(sModel,sDummy);
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xAddNodeIDsToNodeSet(sModel,sRefPartList,sNodeSetName,NodeList);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xSetNodeSetPreviewMode(True);
    return;
#--------------------------------------------------
# Create Nodesset from Selected parts nodes
#FlexMask,*FLEX*EXCLUDE,NA,1
def CreatePartMask(sVals):
    '''
    Creates nodeset from the selected parts 
    Parameters:
        sVals (list): 
            sVals[1] - Node set name
            sVals[2] - Part name to be added to the nodeset
            sVals[3] - Proximity of the nodes to be added to the nodeset
            sVals[4] - Number of adjacent layer to be masked
    Returns:
         True: If the nodeset is created
         None: If the the selected parts are invalid
    '''
    sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
    if len(sPartList) < 1 : return None;
    # aPart = sPartList[0]
    # ShowOnePart(aPart);
    #PopMessage(sPartList);
    nVals = len(sVals);
    if nVals < 5: return None;
    sMaskName = sVals[1]; 
    sMaskPartName = sVals[2]; # part name
    sSelectedParts = GetValidParts(sMaskPartName);
    if len(sSelectedParts) < 1: return None;
    #PopMessage(sSelectedParts,'sSelectedParts');
    fProximity = 0.1;
    if IsFloat(sVals[3]):
        fProximity = float(sVals[3]);
    nAdjElms = 0;
    if IsFloat(sVals[4]):
        nAdjElms = int(sVals[4]);
    # Create Nodesset from Selected parts nodes
    for aPart in sSelectedParts:
        _VCollabAPI.xSelectNodeEx(sModel,aPart, 0, 1);
        _VCollabAPI.xShowPart(sModel,aPart,True);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xLockRefresh(False);
    _VCollabAPI.xSetNodeSetPreviewMode(False);
    if hasattr(_VCollabAPI,'xAddNodeSetToNodeSet'):
        sNodeSetName = '_tmp'+ sMaskName;
    else:
        sNodeSetName = sMaskName;
    #sDummySet = sMaskName+'Tmp';
    _VCollabAPI.xCreateNodeSetFromSelectedParts(sModel, sNodeSetName);
    if fProximity > 0.0:
        flag=_VCollabAPI.xNodeSetsAddProximity(sModel,sNodeSetName,fProximity,True,False);
    #-- Hide Others
    _VCollabAPI.xDeselectAll(sModel);
    _VCollabAPI.xRefreshViewer();
    for aPart in sSelectedParts:
        _VCollabAPI.xShowPart(sModel,aPart,False);
    #
    if hasattr(_VCollabAPI,'xAddNodeSetToNodeSet'):
        flag=_VCollabAPI.xAddNodeSetToNodeSet(sModel,sPartList,sNodeSetName,sMaskName);
        _VCollabAPI.xNodeSetDelete(sModel,sNodeSetName);
    _VCollabAPI.xRefreshDialogs();
    flag = True;
    if flag == True :
        for i in range(nAdjElms):
            _VCollabAPI.xNodeSetsAddAdjacency(sModel,sMaskName);
        _VCollabAPI.xSetNodesetVisiblity(sModel,sMaskName,False);
    else:
        sMaskName = None;
    _VCollabAPI.xLockRefresh(False);
    _VCollabAPI.xClearNodeSetSelection(sModel);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xSetNodeSetPreviewMode(True);
    return True;
#--------------------------------------------------------
def CreateResultMask(sVals):
    '''
    Creates nodeset from the selected result
    Parameters:
        sVals:
            sVals[1] - Nodeset name
            sVals[2] - Result name
            sVals[3] - Number of adjacent layer to mask (optional)
            sVals[4] - Minimum range value to get the nodes with in the result (optional)
            sVals[5] - Maximum range value to get the nodes with in the result (optional)
            
    Returns:
         sMaskName: If the nodeset is successfully created, it returns the nodeset name
         None: If the selected result in not valid
    '''
    nVals = len(sVals);
    if nVals < 3: return None;
    sMaskName = sVals[1]; 
    sMaskResName = sVals[2]; # result name
    sResult=SelectResult(sModel,sMaskResName);
    if sResult == None:
        PrintErrorMessage(sMaskResName,"Not Found Result=");
        return None;
    nAdjElms = 1;
    if nVals > 3:
        nAdjElms = int(sVals[3]); #
    bUserMin=False;fUserMin=-1.0;
    if nVals > 4:
        if IsFloat(sVals[4]):
            bUserMin=True;fUserMin= float(sVals[4]); #
    bUserMax=False;fUserMax = -1.0;
    if nVals > 5:
        if IsFloat(sVals[5]):
            bUserMax=True;fUserMax= float(sVals[5]);
    #---------------------- Input done ---
    _VCollabAPI.xSetNodeSetPreviewMode(True);
    sNodeSetName = sMaskName;
    if hasattr(_VCollabAPI,'xSelectNodeSetsFromResult'):
        flag=_VCollabAPI.xSelectNodeSetsFromResult(sModel,"","","",bUserMin,fUserMin,bUserMax,fUserMax);
    else:
        _VCollabAPI.xLockRefresh(True);
        GetGlobalHotSpots();
        _VCollabAPI.xCreateNodeSetFromProbedLabels(sModel,sNodeSetName);
        _VCollabAPI.xLockRefresh(False);
        _VCollabAPI.xDeleteAllLabels();
    #-----------------------
    flag=_VCollabAPI.xCreateNodeSetsFromSelectedNodes(sModel,sNodeSetName);
    if flag == True :
        for i in range(nAdjElms):
            _VCollabAPI.xNodeSetsAddAdjacency(sModel,sNodeSetName);
        _VCollabAPI.xSetNodesetVisiblity(sModel,sNodeSetName,False);
    else:
        sMaskName = None;
    _VCollabAPI.xClearNodeSetSelection(sModel);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xSetNodeSetPreviewMode(True);
    return sMaskName;
#=====================================
#--------------------------------------------------
# Create Nodesset from Selected Nodes
#NODE_MASK,NodeMask,15.0,11234,3456
def CreateNodeMask(sVals):
    '''
    Create nodeset from the selected nodes
    Parameters:
        sVals:
            sVals[1] - Nodeset name
            sVals[2] (float) - The nodes within this range are added to the nodeset
            sVals[3:] - Nodes ids for masking
    Returns:
         True: If the nodeset is successfully created
         None: If the the selected nodes are invalid
    '''
    nVals = len(sVals);
    if nVals < 4: return None;
    sMaskName = sVals[1]; 
    fRadious = 5.0;
    if IsFloat(sVals[2]):
        fRadious = float(sVals[2]);
    NodeList = [];
    for sNode in sVals[3:]:
        if IsFloat(sNode):
            #iNode = int(sNode);
            NodeList.append(int(sNode));
    #
    if len(NodeList) < 1: return None;
    visibleparts = _VCollabAPI.pxGetVisiblePartsList(sModel);
    if len(visibleparts) < 1: return None;
    _VCollabAPI.xAddNodeIDsToNodeSet(sModel,visibleparts,sMaskName,NodeList);
    _VCollabAPI.xNodeSetsAddProximity(sModel,sMaskName,fRadious,False,False);
    _VCollabAPI.xCreateNodeSetsFromSelectedNodes(sModel,sMaskName);
    _VCollabAPI.xSetNodesetVisiblity(sModel, sMaskName ,False );
    _VCollabAPI.xLockRefresh(False);
    _VCollabAPI.xClearNodeSetSelection(sModel);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xSetNodeSetPreviewMode(True);
    return True;
#==============================================================================
#--MultiModel Functions
#--    0- Active Model, 1- Multi Palette
#--    2- Combined Palette, 3- Multiple: Combined Palette
def SetPaletteMode(iMode):
    _VCollabAPI.xSetCAEMultiPalette(False)
    _VCollabAPI.xSetCAECombinedPalette(False)
    _VCollabAPI.xSetCAELegendRange(u"",False,1.0,False,0.0,False)
    _VCollabAPI.xSetCAEPaletteMode(iMode)
    _VCollabAPI.xRefreshDialogs()
    _VCollabAPI.xRefreshViewer()
    return
#===============================================================
#--- Hotspot Related Functions ----
#---------------------------------------------------------
# Estimate ZoneRadius for hotspot from spherical radius
def GetZoneRadius(sModel=u"",fZoneBoundPercent=0.08,sPartNode=u"",iType = 0):
    '''
    Gets the bound zone radius for a part or assembly
    Parameters:
        sModel: Cax model name (optional)
        fZoneBoundPercent: Bound zone percent (optional)
        sPartNode:  Part name or sub-assembly name (optional)
        iType:  0 for sub-assembly, 1 for part (optional)
    Returns:
         fZoneRadius: Bound zone radius
         If bound zone radius is less than 0 returns 0.0001
    '''
    #iType = 1 for part, 0 for model
    fBoundsVec = _VCollabAPI.pxGetBoundSphere(sModel,sPartNode,iType);
    if len(fBoundsVec) <= 0 :return 0.0001;
    fZoneRadius = fBoundsVec[3]*fZoneBoundPercent;
    return fZoneRadius;
#---------------------------------------------------------------------------
def SetHotSpotParamsCmd(sLimits):
    '''
    Sets hotspot parameters
    Parameters:
        sLimits:
            sLimits[0] - Sets minimum range value
            sLimits[1] - Sets maximum range value
            sLimits[2] - Number of top hotspots
            sLimits[3] - Number of bottom hotspots
            sLimits[4] - Zone radius for the hotspot
    Returns:
         None
    '''
    global fg_HSMinLimit;
    if sLimits == None or len(sLimits) < 5 :
        sLimits=['NA','NA','5','0','20.0'];
    bMinLimit = False;fMinLimit = 0.0;
    if IsFloat(sLimits[0]):
        fg_HSMinLimit = float(sLimits[0]);
        bMinLimit = True;
        fMinLimit = fg_HSMinLimit;
    bMaxLimit = False;fMaxLimit = 0.0;
    if IsFloat(sLimits[1]):
        bMaxLimit = True;
        fMaxLimit = float(sLimits[1]);
    iTopCount=20;fZoneRadius=20.0;iBottomCount=0;
    if IsFloat(sLimits[2]):
        iTopCount = int(sLimits[2]);
    if IsFloat(sLimits[3]):
        iBottomCount = int(sLimits[3]);
    if IsFloat(sLimits[4]):
        fZoneRadius = float(sLimits[4]);
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode); # Compact Mode
    bLocalExtrema=True;
    _VCollabAPI.xSetCAEHotspotMode(sModel, bLocalExtrema);
    _VCollabAPI.xSetCAEHotSpotsMinMax(sModel,bMinLimit,fMinLimit,bMaxLimit,fMaxLimit);
    bEnableBottom = True; bEnableTop = True;
    if iBottomCount < 1 : bEnableBottom = False;
    if iTopCount < 1 : bEnableTop = False;
    _VCollabAPI.xSetCAEHotSpotsCount(sModel,bEnableTop,iTopCount,bEnableBottom,iBottomCount);
    bAllBottom = False; bAllTop = False;
    if iBottomCount < 0 : bAllBottom = True;
    if iTopCount < 0 : bAllTop = False;
    _VCollabAPI.xSetCAEHotspotAllTopBottom(sModel, bAllTop, bAllBottom);
    bEnableZoneRadius=True;
    if fZoneRadius == None :
        fZoneRadius = GetZoneRadius(sModel,0.05);
    if fZoneRadius < -1E10 : bEnableZoneRadius=False;
    _VCollabAPI.xSetCAEHotSpotsZoneRadius(sModel,bEnableZoneRadius,fZoneRadius);
    #--
    _VCollabAPI.xSetCAEHotSpotsVisibleSurface(sModel, False);
    #_VCollabAPI.xSetCAEProbeType(sModel,3) #1 => Derived
    # bShowID = False; bShowPartHeader= False;
    # bShowRowHeader=False; bShowColHeader=False;
    # _VCollabAPI.xSetCAEProbeLabelFields(sModel,bShowID, bShowRowHeader, bShowColHeader, bShowPartHeader);
    _VCollabAPI.xSetCAEHotSpotsMarkMinMax(sModel,False);
    _VCollabAPI.xRefreshDialogs();
    return;
#===============================================================
def GetGlobalHotSpots(iTopCount=1,iBottomCount=0,fZoneRadius=-1.0):
    '''
    Finds hotspots
    Parameters:
        iTopCount: Number of top hotspots (optional)
        iBottomCount: Number of bottom hotspots (optional)
        fZoneRadius: Zone radius (optional)
    Returns:
         None    
    '''
    _VCollabAPI.xSetCAEHotspotMode(sModel, False);
    _VCollabAPI.xSetCAEHotSpotsMinMax(sModel,False,0.0,False,1.0);
    _VCollabAPI.xSetLabelAutoArrangeMode(0); # Compact Mode
    bEnableBottom = True;
    if iBottomCount < 1 : bEnableBottom = False;
    bEnableTop = True;
    if iTopCount < 1 : bEnableTop = False; 
    _VCollabAPI.xSetCAEHotSpotsCount(sModel,bEnableTop,iTopCount,bEnableBottom,0);
    _VCollabAPI.xSetCAEHotspotAllTopBottom(sModel, False, False);
    if fZoneRadius > 0.0:
        _VCollabAPI.xSetCAEHotSpotsZoneRadius(sModel,True,fZoneRadius);
    else:
        _VCollabAPI.xSetCAEHotSpotsZoneRadius(sModel,False,0.0);
    _VCollabAPI.xSetCAEHotSpotsVisibleSurface(sModel, False);
    _VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    bShowID = True; bShowPartHeader= False; bShowRowHeader=False; bShowColHeader=False;
    _VCollabAPI.xSetCAEProbeLabelFields(sModel,bShowID, bShowRowHeader, bShowColHeader, bShowPartHeader);
    _VCollabAPI.xRefreshDialogs();
    bRtnFlag=_VCollabAPI.xCAEFindHotspots(False,u"");
    if bRtnFlag == False: PrintMessage(_VCollabAPI.xGetLastError());
    return;
#=============================================================
# Set Hotspot dialog parameters , compute hotspots and create viewpoint
def ComputeFewHotspots(iTopCount=2,iBottomCount=0,fZoneRadius=-1.0):
    '''
    Finds hotspots
    Parameters:
        iTopCount: Number of top hotspots (optional)
        iBottomCount: Number of bottom hotspots (optional)
        fZoneRadius: Zone radius (optional)
    Returns:
         None    
    '''
    sModel = _VCollabAPI.xGetCurCAEModelName();
    bLocalExtrema=True;
    _VCollabAPI.xSetCAEHotspotMode(sModel, bLocalExtrema);
    _VCollabAPI.xSetCAEHotSpotsMinMax(sModel,False,0.0,False,1.0);
    bEnableBottom = True;
    if iBottomCount < 1 : bEnableBottom = False;
    bEnableTop = True;
    if iTopCount < 1 : bEnableTop = False;
    _VCollabAPI.xSetCAEHotSpotsCount(sModel,bEnableTop,iTopCount,bEnableBottom,iBottomCount);
    _VCollabAPI.xSetCAEHotspotAllTopBottom(sModel, False, False);
    bEnableZoneRadious=False;
    if fZoneRadius > 0.0 : bEnableZoneRadious=True;
    _VCollabAPI.xSetCAEHotSpotsZoneRadius(sModel,bEnableZoneRadious,fZoneRadius)
    _VCollabAPI.xSetCAEHotSpotsVisibleSurface(sModel, False);
    #_VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    #bShowID = False; bShowPartHeader= False;
    #bShowRowHeader=False; bShowColHeader=False;
    #_VCollabAPI.xSetCAEProbeLabelFields(sModel,bShowID, bShowRowHeader, bShowColHeader, bShowPartHeader);
    bRtnFlag=_VCollabAPI.xCAEFindHotspots(False,u"");
    if bRtnFlag == False: _VCollabAPI.xMessageBox(_VCollabAPI.xGetLastError(),bGUIMode);
    _VCollabAPI.xFitLabels();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshNormals();
    return;
#=========================================================
#LOADCASE_HSVIEW,VPathName
def CreateHotspotsForEachinstance(VpName=None):
    '''
    Find hotspots and create viewpoint for each instance
    Parameters:
        VpName: Viewpath name (optional)
    Returns:
         None
    '''
    VPathName = CurVPathName;
    if VpName != None:
        VPathName = VpName;
    _VCollabAPI.xShowCAEFrameMinMaxLabels(sModel,True);
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];sDerived = sCurResInfo[2];
    #sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    nInst = 0;
    for sInst in sInstanceList:
        nInst = nInst+1;
        if ig_FirstInstance!= None:
            if ig_FirstInstance > nInst: continue;
        if ig_LastInstance!= None:
            if ig_LastInstance < nInst: break;
        _VCollabAPI.xSetCAEResult(sModel,sResult,sInst,sDerived);
        sKey = u"Label"; 
        sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
        sViewName = sResult;
        if len(sValue) > 0: sViewName = sViewName+'-'+sValue;
        sViewName = sViewName + '-'+sInst;
        #--------------------------
        if len(lg_HSViewList) > 0:
            for vp in lg_HSViewList:
                SetCameraView(vp[0],vp[1],vp[2],vp[3],vp[4],vp[5]);
                _VCollabAPI.xDeleteAllLabels();
                _VCollabAPI.xCAEFindHotspots(False,u"");
                _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);
                AddVP_HF(sViewName+' '+str(vp[6]),VPathName,-1);
            #--------------------------
        else:
            _VCollabAPI.xDeleteAllLabels();
            _VCollabAPI.xCAEFindHotspots(False,u"");
            _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);
            AddVP_HF(sViewName,VPathName,-1);
            #--------------------------
    return;
#-------------------------------------------------
fg_HeaderX=0.05;fg_HeaderY=0.7;
sg_ResultDspList="";
def SetSelectedResults(sProbeResList):
    '''
    Sets the selected result list for CAE probing (Multi result probing)
    Parameters:
        sProbeResList (List): Result name list
    Returns:
         None
    '''
    global sg_ResultDspList;sg_ResultDspList="";
    sSelectedResultList = u"";nResults = 0;
    for aRes in sProbeResList:
        aRes = aRes.strip();
        if len(aRes) < 1: continue;
        sResult=SelectResult(sModel,aRes,False);
        if sResult != None:
            sSelectedResultList=sSelectedResultList+sResult+';';nResults=nResults+1;
            if sResult.find("Von")>=0: 
                _VCollabAPI.xSetCAEResultDisplayName(sModel,sResult,"Mises");
                sg_ResultDspList = sg_ResultDspList + 'vM,';
            elif sResult.find("Principal")>=0 and sResult.find("Max")>=0: 
                _VCollabAPI.xSetCAEResultDisplayName(sModel,sResult,"MaxP");
                sg_ResultDspList = sg_ResultDspList + 'MaxP,';
            elif sResult.find("Principal")>=0 and sResult.find("Min")>=0: 
                _VCollabAPI.xSetCAEResultDisplayName(sModel,sResult,"MinP");
                sg_ResultDspList = sg_ResultDspList + 'MinP,';
            # else:
                # #_VCollabAPI.xSetCAEResultDisplayName(sModel,sResult,sResult[:5]);
                # sg_ResultDspList = sg_ResultDspList + sResult[:5]+',';
    if nResults > 1:
        _VCollabAPI.xSetCAEProbeSelectedResults(sModel,sSelectedResultList);
        _VCollabAPI.xSetCAEProbeType(sModel,3) #3 => All Selected Result
    else:
        _VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    #_VCollabAPI.xShowCAEHeaderLegend(sModel,True,True);
    _VCollabAPI.xSetCAEHeaderLegendPosition(sModel,True,fg_HeaderX,fg_HeaderY);
    return;
def GetSelRes_DispNames():
    '''
    Get the short display name for a result used in probe label.
    Parameters:
        None
    Returns:
         sDispNameList (List):
    '''
    sDispNameList = [];
    iProbeType = _VCollabAPI.xGetCAEProbeTypeEx(sModel);
    if iProbeType != 3: # All result Table
        sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
        sResult = sCurResInfo[0];
        aDspName = _VCollabAPI.xGetCAEResultDisplayName(sModel,sResult);
        sDispNameList.append(aDspName);
        return sDispNameList;
    sSelResultsString = _VCollabAPI.xGetCAEProbeSelectedResults(sModel);
    sSelResultsString = sSelResultsString[:-1]; #remove last ';'
    sSelResults=sSelResultsString.split(';');
    for aRes in sSelResults:
        aDspName = _VCollabAPI.xGetCAEResultDisplayName(sModel,aRes);
        sDispNameList.append(aDspName);
    return sDispNameList;
#=============================================================
def CreateHSView(sVPName,hsLimits):
    '''
    Creates a viewpoint after finding the hotspots with the given settings
    Parameters:
        sVPName: Viewpoint name
        hsLimits (List): Hotspot parameters
            hsLimits[0] - Sets minimum range value
            hsLimits[1] - Sets maximum range value
            hsLimits[2] - Number of top hotspots
            hsLimits[3] - Number of bottom hotspots
            hsLimits[4] - Zone radius for the hotspot
            None: If the user does not want to change the hotspot settings
    Returns:
         True: Successfully created the viewpoint
         None: Failed to create the viewpoint
    '''
    if hsLimits!=None and len(hsLimits)> 4: 
        SetHotSpotParamsCmd(hsLimits);
    #_VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    fMinMaxList = _VCollabAPI.pxGetCAEVisiblePartsMinMax(u"");
    if len(fMinMaxList) < 2:
        PrintErrorMessage(u"pxGetCAEVisiblePartsMinMax Failed ");
        return;
    fMax = fMinMaxList[1];fMin = fMinMaxList[0];
    #PrintMessage(u"Max Min = "+str(fMax)+ u" , "+str(fMin));
    if abs(fMax) < 1.0E-20 : return;
    if abs(fMax) > 1.0E20 : return;
    SetLegendPrecisionMaxMin(sModel,fMax,fMin);
    #------------      
    _VCollabAPI.xCAEFindHotspots(False,u"");
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);
    if len(sVPName) > 1: AddVP_HF(sVPName,CurVPathName,-1);
    return True;
#===========================================
#-- General Related Functions ---
#-----------------------------------------------
#======================= Math functions =================
def NormVec(fDirX):
    '''
    Returns the normalized vector
    Parameters:
        fDirX (List): List of vector values to normalize
    Returns:
         fDirX (List): Normalized vector values
    '''
    fDirXLen = math.sqrt(fDirX[0]*fDirX[0]+fDirX[1]*fDirX[1]+fDirX[2]*fDirX[2]);
    if fDirXLen < 1.0E-20: fDirXLen = 1.0E-20;
    fDirX = [fDirX[0]/fDirXLen,fDirX[1]/fDirXLen,fDirX[2]/fDirXLen];
    return fDirX;
def CrossVec(a,b):
    '''
    Returns the cross product of two vectors
    Parameters:
        a (List): List of vector values
        b (List): List of vector values
    Returns:
         fCross (List): Cross vector of the two vectors
    '''
    fCross = [a[1]*b[2] - a[2]*b[1],
         a[2]*b[0] - a[0]*b[2],
         a[0]*b[1] - a[1]*b[0]];
    return fCross;
    
def DotVec(a,b):
    return a[0]*b[0] + a[1]*b[1] + a[2]*b[2];
    
def LengthVec(fDirX):
    fDirXLen = math.sqrt(fDirX[0]*fDirX[0]+fDirX[1]*fDirX[1]+fDirX[2]*fDirX[2]);
    if fDirXLen < 1.0E-20: fDirXLen = 1.0E-20;
    return fDirXLen;
#===================== New ====================
# Calculates Rotation Matrix given euler angles.
def ToRadians(Td):
    return(Td*math.pi/180.0);
def ToDegree(Tr):
    return (Tr*180.0/math.pi);
#=============================================
class Vector3D():
    def __init__(self,fx=0.0,fy=0.0,fz=0.0):
        self.x, self.y, self.z = fx, fy, fz;  
    @classmethod
    def fromlist(cls,flist):
        return cls(flist[0],flist[1],flist[2]);
    @classmethod
    def from2Pt(cls,P1,P2):
        return cls(P2[0]-P1[0],P2[1]-P1[1],P2[2]-P1[2]);
    #----------------------
    def norm(self): # ---- Returns the norm (length, magnitude) of the vector ---
        return math.sqrt(self.x*self.x+self.y*self.y+self.z*self.z);
    def normalise(self):
        flen = self.x*self.x+self.y*self.y+self.z*self.z;
        if flen < 1.0E-10 : return False;
        flen = math.sqrt(flen);
        self.x = self.x / flen;
        self.y = self.y / flen;
        self.z = self.z / flen;
        return True;
    
    def makecopy(self):
        return Vector3D(self.x, self.y, self.z);
        
    def tolist(self):
        return [self.x, self.y, self.z];
    
    def getnormalised(self):
        flen = self.x*self.x+self.y*self.y+self.z*self.z;
        if flen < 1.0E-10 :
            return Vector3D(self.x, self.y, self.z);
        flen = math.sqrt(flen);
        fx = self.x / flen;
        fy = self.y / flen;
        fz = self.z / flen;
        return Vector3D(fx,fy,fz);
    
    def dot(self, bVec):
        fval = self.x*bVec.x + self.y*bVec.y + self.z*bVec.z ;
        return fval;
    #
    def cross(self,bVec):
        fx = (self.y*bVec.z - bVec.y*self.z);
        fy = (self.z*bVec.x - bVec.z*self.x);
        fz = (self.x*bVec.y - bVec.x*self.y);
        return Vector3D(fx,fy,fz);
    
    def angleR(self,bVec):
        flena = self.x*self.x+self.y*self.y+self.z*self.z;
        flenb = bVec.x*bVec.x+bVec.y*bVec.y+bVec.z*bVec.z;
        flen = flena*flenb;
        if flen < 1.0E-10 : return 0.0;
        flen = math.sqrt(flen);
        fcos = (self.x*bVec.x + self.y*bVec.y + self.z*bVec.z)/flen;
        return math.acos(fcos);
    
    def angleD(self,bVec):
        fang = self.angleR(bVec);
        return fang*180.0/math.pi;
#===================================================================
#---------------------------------------------------------
class Mat3D():
    def __init__(self,xVec=[1,0,0],yVec=[0,1,0],zVec=[0,0,1]):
        self.R1, self.R2, self.R3 = list(xVec),list(yVec),list(zVec); 
    @classmethod
    def fromAxis(cls,Cord):
        return cls(Cord.xAxis, Cord.yAxis, Cord.zAxis);
    @classmethod
    def fromCordSys(cls,Cord):
        return cls(Cord[3:6],Cord[6:9],Cord[9:12]);
    @classmethod
    def fromTensor(cls,Tens):
        R1 = [Tens[0],Tens[3],Tens[4]]
        R2 = [Tens[3],Tens[1],Tens[5]]
        R3 = [Tens[4],Tens[5],Tens[2]]
        return cls(R1,R2,R3);
    def Copy(self):
        return Mat3D(list(self.R1),list(self.R2),list(self.R3));
    #-----------------
    def VecMult_Post(self,fVec):
        fXval = self.R1[0]*fVec[0]+self.R1[1]*fVec[1]+self.R1[2]*fVec[2];
        fYval = self.R2[0]*fVec[0]+self.R2[1]*fVec[1]+self.R2[2]*fVec[2];
        fZval = self.R3[0]*fVec[0]+self.R3[1]*fVec[1]+self.R3[2]*fVec[2];
        return [fXval,fYval,fZval];
    def VecMult_Pre(self,fVec):
        fXval = self.R1[0]*fVec[0]+self.R2[0]*fVec[1]+self.R3[0]*fVec[2];
        fYval = self.R1[1]*fVec[0]+self.R2[1]*fVec[1]+self.R3[1]*fVec[2];
        fZval = self.R1[2]*fVec[0]+self.R2[2]*fVec[1]+self.R3[2]*fVec[2];
        return [fXval,fYval,fZval];
        
    def MatMult(self,fMat):
        fOut = Mat3D();
        #PopMessage(fOut.ToSTR(),fMat.ToSTR());
        fOut.R1[0] = self.R1[0]*fMat.R1[0]+self.R1[1]*fMat.R2[0]+self.R1[2]*fMat.R3[0];
        fOut.R2[0] = self.R2[0]*fMat.R1[0]+self.R2[1]*fMat.R2[0]+self.R2[2]*fMat.R3[0];
        fOut.R3[0] = self.R3[0]*fMat.R1[0]+self.R3[1]*fMat.R2[0]+self.R3[2]*fMat.R3[0];
        
        fOut.R1[1] = self.R1[0]*fMat.R1[1]+self.R1[1]*fMat.R2[1]+self.R1[2]*fMat.R3[1];
        fOut.R2[1] = self.R2[0]*fMat.R1[1]+self.R2[1]*fMat.R2[1]+self.R2[2]*fMat.R3[1];
        fOut.R3[1] = self.R3[0]*fMat.R1[1]+self.R3[1]*fMat.R2[1]+self.R3[2]*fMat.R3[1];
        
        fOut.R1[2] = self.R1[0]*fMat.R1[2]+self.R1[1]*fMat.R2[2]+self.R1[2]*fMat.R3[2];
        fOut.R2[2] = self.R2[0]*fMat.R1[2]+self.R2[1]*fMat.R2[2]+self.R2[2]*fMat.R3[2];
        fOut.R3[2] = self.R3[0]*fMat.R1[2]+self.R3[1]*fMat.R2[2]+self.R3[2]*fMat.R3[2];
        return fOut;
        
    def Mat2Tensor(self):
        fTens=[0]*6;
        fTens[0] = self.R1[0];fTens[1] = self.R2[1];fTens[2] = self.R3[2];
        fTens[3] = self.R1[1];fTens[4] = self.R1[2];fTens[5] = self.R2[2];
        return fTens;
        
    def Transpose(self):
        fMat = self.Copy();
        fMat.R1[1] = self.R2[0];fMat.R2[0] = self.R1[1];
        fMat.R1[2] = self.R3[0];fMat.R3[0] = self.R1[2];
        fMat.R2[2] = self.R3[1];fMat.R3[1] = self.R2[2];
        return fMat;
        
    def ToSTR(self):
        return f"{self.R1}'\n'{self.R2}'\n'{self.R3}";
        
    def StressTransform(self,fTens):
        fTMat = Mat3D.fromTensor(fTens);
        PopMessage(fTens,fTMat.ToSTR())
        fMat = self.MatMult(fTMat);
        fOut = fMat.MatMult(self.Transpose());
        # LogPrint(fOut.ToSTR());
        return fOut.Mat2Tensor();
        
    @classmethod
    def RotMatX(cls,teta):
        Ct = math.cos(teta); St = math.sin(teta)
        Xvec = [1,0,0];
        Yvec = [0,Ct,-St];
        Zvec = [0,St,Ct];
        return cls(Xvec,Yvec,Zvec);
        
    @classmethod
    def RotMatY(cls,teta):
        Ct = math.cos(teta); St = math.sin(teta)
        Xvec = [Ct,0,St];
        Yvec = [0,1,0];
        Zvec = [-St,0,Ct];
        return cls(Xvec,Yvec,Zvec);
        
    @classmethod
    def RotMatZ(cls,teta):
        Ct = math.cos(teta); St = math.sin(teta)
        Xvec = [Ct,-St,0];
        Yvec = [St,Ct,0];
        Zvec = [0,0,1];
        return cls(Xvec,Yvec,Zvec);
        
    @classmethod
    def RotMatAxis(cls,Ax,teta):
        Ct = math.cos(teta); St = math.sin(teta); Ct_1 = 1.0-Ct;
        Xvec = [ Ct+Ct_1*Ax[0]*Ax[0], Ax[0]*Ax[1]*Ct_1-Ax[2]*St, Ax[0]*Ax[2]*Ct_1+Ax[1]*St ];
        Yvec = [ Ax[0]*Ax[1]*Ct_1+Ax[2]*St, Ct+Ct_1*Ax[1]*Ax[1], Ax[1]*Ax[2]*Ct_1-Ax[0]*St ];
        Zvec = [ Ax[0]*Ax[2]*Ct_1-Ax[1]*St, Ax[1]*Ax[2]*Ct_1+Ax[0]*St, Ct+Ct_1*Ax[2]*Ax[2] ];
        return cls(Xvec,Yvec,Zvec);
#-------------------------------------------------------------------------
def Trasform4x4(R1Mat,M1Vec,R2Mat,M2Vec):
    R12Mat = R1Mat.MatMult(R2Mat);
    R12VecX = R1Mat.VecMult_Post(M2Vec);
    R12Vec = [R12VecX[0]+M1Vec[0] , R12VecX[1]+M1Vec[1] , R12VecX[2]+M1Vec[2]];
    return R12Mat,R12Vec;
#-------------------------------------------------------------------------
class LocalAxis():
    def __init__(self,origin=[0,0,0],xVec=[1,0,0],yVec=[0,1,0],zVec=[0,0,1]):
        self.Org, self.xAxis, self.yAxis, self.zAxis = list(origin),list(xVec),list(yVec),list(zVec);            
    #-------------------------------
    @classmethod
    def from3Point(cls,P1,P2,P3):
        origin = P1;
        xVec = Vector3D.from2Pt(P1,P2);
        yVec_t = Vector3D.from2Pt(P1,P3);
        zVec = xVec.cross(yVec_t);
        yVec = zVec.cross(xVec);
        xVec.normalise();yVec.normalise();zVec.normalise();
        return cls(origin,xVec.tolist(),yVec.tolist(),zVec.tolist());
    @classmethod
    def from3PointCircle(cls,P1,P2,P3):
        origin = CircleCenter3Pt(P1,P2,P3);
        xVec = Vector3D.from2Pt(origin,P1);
        yVec_t = Vector3D.from2Pt(origin,P2);
        zVec = xVec.cross(yVec_t);
        yVec = zVec.cross(xVec);
        xVec.normalise();yVec.normalise();zVec.normalise();
        return cls(origin,xVec.tolist(),yVec.tolist(),zVec.tolist());
        
    def Reset(self,origin=[0,0,0],xVec=[1,0,0],yVec=[0,1,0],zVec=[0,0,1]):
        xV3d = Vector3D.fromlist(xVec);PopMessage(xV3d.norm(),"X",xVec);
        yV3d = Vector3D.fromlist(yVec);PopMessage(yV3d.norm(),"Y",yVec);
        zV3d = Vector3D.fromlist(zVec);PopMessage(zV3d.norm(),"Z",zVec);
        self.Org, self.xAxis, self.yAxis, self.zAxis = origin,xVec,yVec,zVec;            
    #-------------------------------
    def TransVecGL(self,fVec): # GlobaltoLocal
        fXval = self.xAxis[0]*fVec[0]+self.xAxis[1]*fVec[1]+self.xAxis[2]*fVec[2];
        fYval = self.yAxis[0]*fVec[0]+self.yAxis[1]*fVec[1]+self.yAxis[2]*fVec[2];
        fZval = self.zAxis[0]*fVec[0]+self.zAxis[1]*fVec[1]+self.zAxis[2]*fVec[2];
        return [fXval,fYval,fZval];
    def TransVecLG(self,fVec):
        fXval = self.xAxis[0]*fVec[0]+self.yAxis[0]*fVec[1]+self.zAxis[0]*fVec[2];
        fYval = self.xAxis[1]*fVec[0]+self.yAxis[1]*fVec[1]+self.zAxis[1]*fVec[2];
        fZval = self.xAxis[2]*fVec[0]+self.yAxis[2]*fVec[1]+self.zAxis[2]*fVec[2];
        return [fXval,fYval,fZval];
    def TransPosGL(self,fPos):
        fVec = [fPos[0]-self.Org[0],fPos[1]-self.Org[1],fPos[2]-self.Org[2]];
        fXval = self.xAxis[0]*fVec[0]+self.xAxis[1]*fVec[1]+self.xAxis[2]*fVec[2];
        fYval = self.yAxis[0]*fVec[0]+self.yAxis[1]*fVec[1]+self.yAxis[2]*fVec[2];
        fZval = self.zAxis[0]*fVec[0]+self.zAxis[1]*fVec[1]+self.zAxis[2]*fVec[2];
        return [fXval,fYval,fZval];
    def TransPosLG(self,fPos):
        fXval = self.xAxis[0]*fPos[0]+self.yAxis[0]*fPos[1]+self.zAxis[0]*fPos[2];
        fYval = self.xAxis[1]*fPos[0]+self.yAxis[1]*fPos[1]+self.zAxis[1]*fPos[2];
        fZval = self.xAxis[2]*fPos[0]+self.yAxis[2]*fPos[1]+self.zAxis[2]*fPos[2];
        return [fXval+self.Org[0],fYval+self.Org[1],fZval+self.Org[2]]; 
    def PrintMe(self):
        PopMessage([self.Org,self.xAxis,self.yAxis,self.zAxis]);
#===================================================================

#=================================================
def CircleCenter3Pt(P1,P2,P3):
    V1 = Vector3D.from2Pt(P1,P2); # v1=p2-p1
    V2 = Vector3D.from2Pt(P1,P3); # v2=p3-p1
    #-- dot products v11,v12,v22
    v11 = V1.dot(V1);
    v12 = V1.dot(V2);
    v22 = V2.dot(V2);
    #-- Compute Sclars 
    b = 2*(v11*v22-v12*v12);
    k1 = v22*(v11-v12)/b;
    k2 = v11*(v22-v12)/b;
    #--- center P0 P0 = p1+k1.v1+k2.V2
    P0x = P1[0]+k1*V1.x+k2*V2.x;
    P0y = P1[1]+k1*V1.y+k2*V2.y;
    P0z = P1[2]+k1*V1.z+k2*V2.z;
    return [P0x,P0y,P0z];
#---------------------------------------------------
def GetCameraAxis():
    fCamInfo = _VCollabAPI.pxGetCamera();
    # Order : 0-XPos,1-YPos,2-ZPos,3-XDir,4-YDir, 5-ZDir, 6-XUp,7-YUp,8-ZUp,9-FOVy,10-AspectRatio,11-NearClip,12-FarClip
    zVec = [-fCamInfo[3], -fCamInfo[4], -fCamInfo[5]];
    yVec = [fCamInfo[6], fCamInfo[7], fCamInfo[8]];
    xVec = CrossVec(yVec,zVec); yVec = CrossVec(zVec,xVec);
    return NormVec(xVec), NormVec(yVec), NormVec(zVec);
#---------------------------------------------
def GetCAEInfo(sResult,sInst,sKey):
    '''
    Gets attribute value associated with the specified key of a particular result and instance of a CAE model.
    Parameters:
        sResult: Result name
        sInst: Instance name
        sKey: Attribute key name
    Returns:
        sValue: Attribute value if it is available, NA if its not available
    '''
    sValue =_VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInst,sKey);
    if len(sValue) < 1 : return 'NA';
    return sValue;
#====================================================
def EvalInstantce(nInst,expr):
    '''
    Evaluates a expression
    Parameters:
        nInst: Number of instance
        expr: Expression
    Returns:
        iInst: The value from the evaluated expression
        None: If the expression is invalid
    '''
    if expr.find('N') < 0: return None;
    N=nInst;
    try:
        iInst = int(eval(expr));
        if iInst < 1 or iInst > nInst: return None;
        return iInst;
    except (ValueError,TypeError):
        return None
    except:
        return None
    return None
#===================================================
class KeyValueObject(object):
    '''Gets the key and value dict from object'''
    def __init__(self, Key,Value):
        '''
        Parameters:
            Key: Key for dict
            Value: Value for dict             
        '''
        self.Key = Key
        self.Value = Value
 
    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__,
                                  self.Key,
                                  self.Value)
    def __lt__(self, other):
        if hasattr(other, 'Key'):
            return self.Key < other.Key;
#=========================================
def GetCSVString(sLine):
    '''
    Returns the combined list elements as string
    Parameters:
        sLine(List): List of elements to combined
    Returns:
         sLine: Combined list elements as string
    '''
    if type(sLine) is list:
        return ','.join(str(x) for x in sLine)
    return sLine;
def GetCSVStringList(sLine,sFirst="",iStart=0,iEnd=0):
    '''
    Returns the list elements as comma separated string
    Parameters:
        sLine (List): List of comma separated strings
        sFirst: First string to append(optional)
        iStart: Start index of list (optional)
        iEnd: End index of list (optional)
    Returns:
         sRow: Comma separated first elements of the list of strings        
    '''
    sRow = "";
    if len(sFirst) > 0:  sRow = sFirst+',';
    if iEnd <= iStart: iEnd = len(sLine);
    for icol in range(iStart,iEnd):
        sCol = sLine[icol];
        sColList = sCol.split(',');
        sColF=sColList[0];
        sRow = sRow + str(sColF)+',';
    return sRow;
#----------------------------------------
def KeepFewHotSpots(sIdList,MaxHS,bDelete=False):
    '''
    Shows only the top selected hotspots and hides the remaining hotspots
    Parameters:
        sIdList (List): List of probe table ids 
        MaxHS (Integer): Maxmimum number of top hotspots
    Returns:
         MaxHS (Integer): Maxmimum number of top hotspots if successful
                else returns length of the probe table ids list
    '''
    if len(sIdList) < MaxHS : return len(sIdList);
    hTabList = [];
    for id in sIdList:
        # Node  or Elm ID
        #sNodeId = _VCollabAPI.xGetProbeTableNodeID(id);
        #sElmId = sNodeId;
        #if bIsElemental: sElmId = _VCollabAPI.xGetProbeTableElementID(id);
        # Node Position
        #pos3d = _VCollabAPI.pxGetNodeLocation(sModel,u"",sNodeId);
        # Result Values
        sTabResVals = _VCollabAPI.pxGetProbeTableResultValues(sModel,id);
        hTabList.append(KeyValueObject(float(sTabResVals[0]),id));
    hTabList_Sorted = sorted(hTabList,reverse=True);
    count=0;
    for hTab in hTabList_Sorted:
        count=count+1;
        if count < MaxHS : continue;
        id = hTab.Value;
        _VCollabAPI.xShowProbeTable(id,False);
    return MaxHS;
#====================================================
#-- Create Top envelop View point with hotspots
def Create_EnvelopView(sResultStr,hsLimits=None,DelInst='Time'):
    '''
    Creates a Viewpoint with hotspots for envelope result 
    Parameters:
        sResultStr: Result name for the envelope result
        hsLimits (List): Hotspot parameters (optional)
            hsLimits[0] - Sets minimum range value
            hsLimits[1] - Sets maximum range value
            hsLimits[2] - Number of top hotspots
            hsLimits[3] - Number of bottom hotspots
            hsLimits[4] - Zone radius for the hotspot
            None: If the user does not want to change the hotspot settings
        DelInst: Instance name that to be deleted (optional)
    Returns:
         None: If the selected result is not available
         sResult: Envelope result name
    '''
    _VCollabAPI.xDeleteAllLabels();
    #-- Use existing envelop result--
    sEnvResult = SelectResult(sModel,'*Envelop*'+sResultStr,True);
    if sEnvResult!= None:
        PrintMessage(sEnvResult,"Envelop Result Present ");
        CreateHSView(sEnvResult,hsLimits);
        return sEnvResult;
    #-- Create envelop result
    sResult = SelectResult(sModel,sResultStr,True);
    if sResult == None:
        PrintErrorMessage(sResultStr,"Not Found Result=");
        return None;
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];sDerived = sCurResInfo[2];
    _VCollabAPI.xCreateCAEEnvelopeResult(sModel,sResult,sDerived,True,False);
    sResult = SelectResult(sModel,'*Envelop*'+sResultStr, True);
    _VCollabAPI.xRefreshDialogs();
    if sResult == None:
        PrintErrorMessage('Envelop '+sResultStr,"Not Found Result=");
    if len(DelInst) > 0:
        _VCollabAPI.xCAEDeleteInstance(sModel,sResult,DelInst);
    CreateHSView(sResult,hsLimits);
    return sResult;
#==========================================================
fgDefZoneRadius = 1.0;
def SetHotSpotParams(iTopCount=igMaxHostSpots,iBottomCount=0,fZoneRadius=-1):
    '''
    Sets required hotspots count and zone radius
    Parameters:
        iTopCount (Integer): Sets required top hotspots count(optional)
        iBottomCount (Integer): Sets required bottom hotspots count(optional)
        fZoneRadius (Float): Zone radius for hotspots (max/min hotspot in the zone is picked and other hotspots within this radius are ignored) (optional)
    Returns:
         None
    '''
    #Set CAE Display Settings
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode); # Compact Mode
    bLocalExtrema=True;
    _VCollabAPI.xSetCAEHotspotMode(sModel, bLocalExtrema);
    _VCollabAPI.xSetCAEHotSpotsMinMax(sModel,False,0.0,False,1.0);
    bEnableBottom = True;
    if iBottomCount < 1 : bEnableBottom = False;
    bEnableTop = True;
    if iTopCount < 1 : bEnableTop = False;
    _VCollabAPI.xSetCAEHotSpotsCount(sModel,bEnableTop,iTopCount,bEnableBottom,iBottomCount);
    _VCollabAPI.xSetCAEHotspotAllTopBottom(sModel, False, False);
    bEnableZoneRadious=False;
    if fZoneRadius > 0.0 : bEnableZoneRadious=True;
    _VCollabAPI.xSetCAEHotSpotsZoneRadius(sModel,bEnableZoneRadious,fZoneRadius)
    _VCollabAPI.xSetCAEHotSpotsVisibleSurface(sModel, False);
    _VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    bShowID = False; bShowPartHeader= False;
    bShowRowHeader=False; bShowColHeader=False;
    _VCollabAPI.xSetCAEProbeLabelFields(sModel,bShowID, bShowRowHeader, bShowColHeader, bShowPartHeader);
    _VCollabAPI.xRefreshDialogs();
    return;
#===============================================================
def CreateHotspotView(sResult,sCurInst,sDerived,bIsMinRes=False):
    '''
    Creates hotspots for the selected result 
    Parameters:
        sResult: Result name
        sCurInst: Instance name
        sDerived: Derived type name. Can be an empty string for the scalar result
    Returns:
         Boolean : True if hotspots creation is successful
                   False if hotspots creation is not successful
    '''
    _VCollabAPI.xSetCAEResult(sModel,sResult,sCurInst,sDerived);
    _VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xShowCAELegend(sModel,True);
    _VCollabAPI.xSetCAEDiscreteLegend(sModel,True);
    if (igMaxHostSpots < 1):
        return True;
    if bIsMinRes:
        SetHotSpotParams(0,igMaxHostSpots,fgDefZoneRadius);
        _VCollabAPI.xSetCAEReverseLegend(sModel,True);
    else:
        SetHotSpotParams(igMaxHostSpots,0,fgDefZoneRadius);
        _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    #Set CAE Display Settings
    fMinMaxList = _VCollabAPI.pxGetCAEVisiblePartsMinMax(u"");
    if len(fMinMaxList) < 2:
        PrintErrorMessage(sResult+" "+sCurInst, u"pxGetCAEVisiblePartsMinMax Failed ");
        return False;
    fMax = fMinMaxList[1];fMin = fMinMaxList[0];
    #PopMessage(u"Max Min = "+str(fMax)+ u" , "+str(fMin));
    if abs(fMax) < 1.0E-30 and abs(fMax-fMin) < 1.0E-30 : return False; # All Zero
    if abs(fMax) > 1.0E30 : return False;
    SetResultPrecisionMaxMin(sModel,fMax,fMin);
    #-----
    bShowID = False; bShowPartHeader= False;
    bShowRowHeader=False; bShowColHeader=False;
    _VCollabAPI.xSetCAEProbeLabelFields(u"",bShowID, bShowRowHeader, bShowColHeader, bShowPartHeader);
    _VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xCAEFindHotspots(False,u"");
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode); # Compact Mode
    _VCollabAPI.xFitLabels();
    _VCollabAPI.xFitView();
    _VCollabAPI.xZoomScreenRect(-0.05,-0.05,1.1,1.1);
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xRefreshDialogs();
    return True;
#=============================================
def Displacement4View(iOption=2,instOption = 1):
    '''
    Creates the viewpoint for Displacement result
    Parameters:
        iOption: 2 - For all the components (optional)
                 1 - For only Magnitude
        instOption: For future use (optional)
    Returns:
         Boolean: True if the viewpoint creation was successful
                  False if the selected result is not available
    '''
    sSelected = SearchResults(sModel,"*Displacement*",False);
    if len(sSelected) < 1:
        #PrintErrorMessage("Displacement Result Not Found");
        return False;
    sResult = sSelected[0];
    sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
    sCurInst = SelectInstance(sModel,sResult,sDerived,igInstanceFlag);
    SetHotSpotParams(igMaxHostSpots,0,fgDefZoneRadius);
    bRetFlag = CreateHotspotView(sResult,sCurInst,sDerived);
    if bRetFlag == False : return False;
    AddVP_HF(sResult+'-'+sDerived,CurVPathName,-1);
    if iOption < 2:
        return True;
    sDefDerived = sDerived;
    sDerivedList = _VCollabAPI.pxGetCAEDerivedResults(sModel,sResult);
    #sDerivedList = [sDerived,u"Translational X",u"Translational Y",u"Translational Z"];
    for sDerived in sDerivedList:
        if sDerived.upper().find('ROT') >= 0: continue;
        if sDerived == sDefDerived : continue;
        bRetFlag = CreateHotspotView(sResult,sCurInst,sDerived);
        if bRetFlag :AddVP_HF(sResult+'-'+sDerived,CurVPathName,-1);
    return True;
#-----------------------------------------------------
def SelectFirstResult():
    '''
    Sets the first result in the CAE result
    Parameters:
        None
    Returns:
         Boolean: True if setting the result was successful
                  False if no result is available
    '''
    sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
    if len(sResultList) < 1: return False;
    sResult = sResultList[0];
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    sInst = sInstanceList[-1]; # Last Instance
    sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
    bRtnFlag = _VCollabAPI.xSetCAEResult(sModel,sResult,sInst,sDerived);
    return bRtnFlag;
#-----------------------------------------------
def GenerateCurResultView():
    '''
    Creates a viewpoint with hotspots for the current result
    Parameters:
        None
    Returns:
         Boolean: True if the viewpoint creation was successful
                  False if the current result is not available   
    '''
    sResList = _VCollabAPI.pxGetCAECurrentResult(sModel);
    if len(sResList) < 3 or len(sResList[0]) < 1: 
        if SelectFirstResult() == False:
            PrintErrorMessage("Not current Result?");
            return False;
        sResList = _VCollabAPI.pxGetCAECurrentResult(sModel);
        if len(sResList) < 3 or len(sResList[0]) < 1: 
            PrintErrorMessage("Not current Result?");
            return False;
    sResult = sResList[0];sDerived = sResList[2];
    PopMessage(sResList,'CurrentResult');
    sCurInst = SelectInstance(sModel,sResult,sDerived,igInstanceFlag);
    bRetFlag = CreateHotspotView(sResult,sCurInst,sDerived);
    if bRetFlag : AddVP_HF(sResult+'-'+sDerived,CurVPathName,-1);
    return bRetFlag;
#==================================------------
def GetResultType(sType):
    '''
    Gets the result type index for the selected result type
    Parameters:
        sType:
    Returns:
         List: Result type index
               Empty list for unknown result type
         None: For "ALL" result type
    '''
    if sType.upper()=='SCALAR': return [0,4];
    if sType.upper()=='TENSOR': return [3,7];
    if sType.upper()=='VECTOR': return [1,2,5,6];
    if sType.upper()=='NODAL_SCALAR': return [0];
    if sType.upper()=='NODAL_TENSOR': return [3];
    if sType.upper()=='ELEMENTAL_SCALAR': return [4];
    if sType.upper()=='ELEMENTAL_TENSOR': return [7];
    if sType.upper()=='ALL': return None;
    PrintErrorMessage(sType,"Unknown Type Result? ");
    return [];
#==============================================================
#from pathlib import Path;
def GetValidOutFileName(OutFileName,bTrimExt=False):
    '''
    Gets the absolute file path for the given model name
    Parameters:
        OutFileName: Cax model name
        bTrimExt: If True trims file extension (optional)
    Returns:
         Absolute file path 
    '''
    if OutFileName == None or len(OutFileName) < 1:
        sOutputFileName = GetOutputFilePathName(sModel)+'_Report';
        return os.path.abspath(sOutputFileName);
    sFileName = OutFileName;
    if bTrimExt:
        sFileName = (os.path.splitext(OutFileName))[0];
    if os.path.isabs(sFileName) == False:
        sOutputFileName = GetOutputFilePathName(sModel)+'_Report';
        sFolder = os.path.dirname(sOutputFileName);
        sFileName = os.path.join(sFolder,os.path.basename(sFileName));
    return os.path.abspath(sFileName);
#==================================================================
#--ALL COMMAND FUNCTIONS -------------
#===============================================
#-- CMD Related functions
#================================================
#Parts_SHOW,ALL/NONE/INVERT/ONLY,Part name list
def ShowPartsCMD(sVals):
    '''
    Sets the part visibility ON based on the given input 
    Parameters:
        sVals (List): sVals[0] - ALL/NONE/INVERT/ONLY
                      sVals[1:] - Part name list
    Returns:
         Boolean: True if setting of the part visibility was successful
                  False if the given input is not valid
    '''
    if sVals[0].upper() == 'ALL': #Display All Parts 
        _VCollabAPI.xShowAll(sModel);
        return True;
    if sVals[0].upper() == 'NONE':
        _VCollabAPI.xShowAll(sModel);
        _VCollabAPI.xInvertShow(sModel);
        #Hide All Parts 
        return True;
    if sVals[0].upper() == 'INVERT':
        _VCollabAPI.xInvertShow(sModel);
        return True;
    if sVals[0].upper() == 'ONLY':
        if len(sVals) < 2: return False;
        _VCollabAPI.xShowAll(sModel);
        sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
        _VCollabAPI.xInvertShow(sModel);
        sInpParts = sVals[1:];
    else : # Append
        sInpParts = sVals;
        _VCollabAPI.xInvertShow(sModel);
        sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
        _VCollabAPI.xInvertShow(sModel);
    #----------------------------------------------------------
    for aPart in  sPartList:
        for sPart in sInpParts:
            if IsSubString(aPart,sPart,True):
                _VCollabAPI.xShowPart(sModel,aPart,True);
    #-- end for
    _VCollabAPI.xDeselectAll(sModel);
    return True;
#------------------------------------------------
#PARTS_HIDE,ALL,INVERT,ONLY
def HidePartsCMD(sVals):
    '''
    Sets the part visibility OFF based on the given input 
    Parameters:
        sVals (List): sVals[0] - ALL/INVERT/ONLY
                      sVals[1:] - Part name list
    Returns:
         Boolean: True if setting of the part visibility was successful
                  False if the given input is not valid
    '''
    if sVals[0].upper() == 'ALL': #Hide All Parts 
        _VCollabAPI.xShowAll(sModel);
        _VCollabAPI.xInvertShow(sModel);
        return True;
    if sVals[0].upper() == 'INVERT':
        _VCollabAPI.xInvertShow(sModel);
        return True;
    if sVals[0].upper() == 'ONLY':
        if len(sVals) < 2: return False;
        _VCollabAPI.xShowAll(sModel);
        sInpParts = sVals[1:];
    else:
        sInpParts = sVals;
    sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
    #----------------------------------------------------------
    for aPart in  sPartList:
        for sPart in sInpParts:
            if IsSubString(aPart,sPart,True):
                _VCollabAPI.xShowPart(sModel,aPart,False);
    #-- end for
    _VCollabAPI.xDeselectAll(sModel);
    return True;
def ShowAssemblyCMD(sVals): #ASM_SHOW,N,Entity Sets
    '''
    Sets the assembly visibility based on the given input 
    Parameters:
        sVals (List): sVals[0] - (Y/N) Flag to show/ hide the assembly. Set Y to show
                      sVals[1:] - Entity Sets
    Returns:
         None
    '''
    bShow = False;
    if sVals[0].upper() == 'Y': bShow = True;
    #**  get assembly List 
    sPartAsmString = _VCollabAPI.xGetAssemblyList(sModel,NULLSTR,0);
    sPartAsmString = sPartAsmString[:-1]; #remove last ';'
    sModelAsmList=sPartAsmString.split(';');
    #PopMessage(sModelAsmList);
    #** 
    AsmListInp = sVals[1:];
    for sAsm in sModelAsmList:
        for sAsmInp in AsmListInp:
            if IsSubString(sAsm,sAsmInp):
                _VCollabAPI.xShowAssembly(sModel,sAsm,bShow);
    #-- for each asm
    return
#--------------------------------------------------------
def ComputeHotSpotsCMD(nVals,sVals):
    '''
    Compute hotspot with nodeset masking
    Parameters:
        nVals (Integer): Length of the sVals list
        sVals (List): sVals[1] - Viewpoint name. Set N not to add viewpoint (Optional)
                      sVals[2:] - Node Sets name for masking (Optional)
    Returns:
         None
    '''
    if nVals > 2:
        sMaskList = sVals[2:];
        _VCollabAPI.xSetCAEMaskedNodeSetList(sModel,sMaskList);
    _VCollabAPI.xCAEFindHotspots(False,u"");
    _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);
    if nVals > 1:
        sVPName = sVals[1];
        if sVPName != 'N' :
            AddVP_HF(sVPName,CurVPathName,-1);
    return;
#====================================================
def CreateImageVPCMD(sVals):
    '''
    Sets the given image as background
    Parameters:
        sVals (List): sVals[0] - Viewpoint name
                      sVals[1] - Image file path
                      sVals[2] - 2D Note string
                      sVals[3] - Screen X position
                      sVals[4] - Screen Y position
    Returns:
         None: If the image path is not valid
         True: Setting the given image as background was successful
    '''
    vpName = sVals[0];
    sImgName = SearchValidFile(sVals[1]);
    if sImgName == None: 
        sgNotify("Error",f"Image file {sVals[1]} Not found",2);
        return;
    if len(vpName) < 1 or vpName.upper() == 'N':
        SetImageView(sImgName);
        return;
    # Create dummy VPList
    AddVP_HF("__DummyView",CurVPathName,-1,0);
    SetBlankView();
    if len(sVals) > 4:
        fSx = 0.4; fSy = 0.9;
        sNoteString = sVals[2];
        if IsFloat(sVals[3]):
            fSx = float(sVals[3]);
        if IsFloat(sVals[4]):
            fSy = float(sVals[4]);
        _VCollabAPI.xAdd2DNotes(sNoteString,fSx,fSy,True);
    SetImageView(sImgName,1,vpName);
    #Restore Last View
    _VCollabAPI.xApplyViewPoint("__DummyView",CurVPathName,True,True,True);
    _VCollabAPI.xDeleteViewpoint(CurVPathName,"__DummyView");
    _VCollabAPI.xRefreshDialogs();
    return True;
#=====================================================
#** SET_Font,Type,size,name,iR,iG,iB,ibR,ibG,ibB,iborder #Type=NOTE,PROBE_VALUE,PROBE_TEXT,OTHERS
def SetFontCMD(sVals):
    '''
    Sets the font settings for Note, Probe labels and for other fields
    Parameters:
        sVals (List): sVals[0] - Tpye of field (NOTE/PROBE_VALUE/PROBE_TEXT/OTHERS)
                      sVals[1] - Font size
                      sVals[2] - Font name
                      sVals[3], sVals[4], sVals[5] - Red,Green and Blue component values of the text color in range of 0-255
                      sVals[6], sVals[7], sVals[8] - Red,Green and Blue component values of the background color in range of 0-255
                      sVals[9] - Sets border. For no border its 0 and 1 to show border
    Returns:
         None:
    '''
    iR= 0; iG = 0; iB = 0; iSize = 19; sFont = u"Arial Narrow Bold";
    ibR= 255; ibG = 255; ibB = 255; iBorder = 0;
    nVals = len(sVals);
    if nVals > 1 and IsFloat(sVals[1]): iSize = int(sVals[1]);
    if nVals > 2 : sFont = sVals[2];
    if nVals > 3 and IsFloat(sVals[3]): iR = int(sVals[3]);
    if nVals > 4 and IsFloat(sVals[4]): iG = int(sVals[4]);
    if nVals > 5 and IsFloat(sVals[5]): iB = int(sVals[5]);
    if nVals > 6 and IsFloat(sVals[6]): ibR = int(sVals[6]);
    if nVals > 7 and IsFloat(sVals[7]): ibG = int(sVals[7]);
    if nVals > 8 and IsFloat(sVals[8]): ibB = int(sVals[8]);
    if nVals > 9 and IsFloat(sVals[9]): iBorder = int(sVals[9]);
    if sVals[0].upper() == 'NOTE':
        _VCollabAPI.xSetNotesFont(sFont,iSize,iR,iG,iB);
        if nVals > 8:
            _VCollabAPI.xSetNotesBackground(True,ibR,ibG,ibB);
        else:
            _VCollabAPI.xSetNotesBackground(False,ibR,ibG,ibB);
        if iBorder > 0:
            _VCollabAPI.xSetNotesBorder(True,0,0,0);
        else:
            _VCollabAPI.xSetNotesBorder(False,0,0,0);
        return;
    if sVals[0].upper() == 'PROBE_VALUE':
        iCellType = 1;
        _VCollabAPI.xSetCAEProbeLabelDefaultFontSize(sModel,iSize,iCellType);
        _VCollabAPI.xSetCAEProbeLabelDefaultFontName(sModel,sFont,iCellType);
        #PopMessage([sFont,iSize,iCellType]);
        if nVals > 5 :
            _VCollabAPI.xSetCAEProbeLabelDefaultTextColor(sModel,iCellType,iR,iG,iB);
        if nVals > 8 :
            _VCollabAPI.xSetCAEProbeLabelDefaultBackground(sModel,iCellType,True,ibR,ibG,ibB);
        return;
    if sVals[0].upper() == 'PROBE_TEXT':
        iCellType = 0;
        _VCollabAPI.xSetCAEProbeLabelDefaultFontName(sModel,sFont,iCellType);
        _VCollabAPI.xSetCAEProbeLabelDefaultFontSize(sModel,iSize,iCellType);
        #PopMessage([sFont,iSize,iCellType]);
        if nVals > 5 :
            _VCollabAPI.xSetCAEProbeLabelDefaultTextColor(sModel,iCellType,iR,iG,iB);
        if nVals > 8 :
            _VCollabAPI.xSetCAEProbeLabelDefaultBackground(sModel,iCellType,True,ibR,ibG,ibB);
        return;
    if sVals[0].upper() == 'OTHERS':
        _VCollabAPI.xSetCAEProbeLabelFont(sModel,sFont,iSize);
        
    return;
#====================================================
#CREATE_RESULT,Name,A,B,IF((abs(A)<abs(B)),A,B)
def CreateResultCMD(sVals):
    '''
    Creates the new result from the exsisting result
    Parameters:
        sVals (List): sVals[0] - New result name
                      sVals[1] - Result A name for the expression
                      sVals[2] - Result B name for the expression
                      sVals[3] - Arithmetic expression or formula with variables A and B
    Returns:
         None:
         Boolean: True if the creation of the new result was successful
                  False if the selected result is not available
    '''
    nVals = len(sVals);
    sNewRes = sVals[0];
    if IsResultPresent(sModel,sNewRes):
        PrintMessage(sNewRes + " Result is Present, why create new?");
        sg.SystemTray.notify('Notify', f"Result {sNewRes} Is Present")
        return;
    sRes1 = SelectResult(sModel,sVals[1],False);
    if sRes1 == None:
        PrintErrorMessage(sVals[1],'Result Not Found');
        return False;
    sRes2 = SelectResult(sModel,sVals[2],False);
    if sRes2 == None:
        PrintErrorMessage(sVals[2],'Result Not Found');
        return False;
    sExpr = sVals[3];
    for k in range(4,nVals):
        sExpr = sExpr+','+sVals[k];
    bFlag = _VCollabAPI.xCreateCAENewResult(sModel,sRes1,sRes2,sExpr,sNewRes);
    return bFlag;
#===================================================
#ADD_VP,Name,Title,Sx,Sy
def ADDViewPointCMD(sVals,bAnimFlag=False):
    '''
    Saves the current display as viewpoint
    Parameters:
        sVals (List): sVals[0] - Viewpoint name
                      sVals[1] - 2D Note string
                      sVals[2], sVals[3] - Screen X and Y position for the 2D note
        bAnimFlag: Flag to set the CAE animation in viewpoint. True to set animation in viewpoint (optional)
    Returns:
         None
    '''
    vpName = sVals[0];
    if len(sVals) > 1 and len(sVals[1]) > 0:
        fSx = 0.4; fSy = 0.05;
        sNoteString = sVals[1];
        if len(sVals) > 3:
            fSx = GetFloat(sVals[2],0.4);
            fSy = GetFloat(sVals[3],0.05);
        _VCollabAPI.xAdd2DNotes(sNoteString,fSx,fSy,True);
    #----
    AddVP_HF(vpName,CurVPathName,-1);
    if bAnimFlag:
        _VCollabAPI.xSetCAEAnimationInCurViewPoint(True);
    return;
#=====================================
def SetCurrentModelCMD(sName):
    '''
    Sets the selected cax model as current model
    Parameters:
        sName: Cax model name
    Returns:
         sModel: Selected cax model name
    '''
    sModelList = _VCollabAPI.pxGetCAEModels();
    if IsFloat(sName):
        iModelNo = int(sName);
        if iModelNo > 0 and iModelNo <= len(sModelList):
            iModelNo = iModelNo-1;
        else:
            return sModel;
        sModelName = sModelList[iModelNo];
        _VCollabAPI.xSetCurCAEModel(iModelNo);
        return sModelName;
    for sModelName in sModelList:
        if sModelName.upper() == sName.upper():
            _VCollabAPI.xSetCurCAEModelByName(sModelName);
            return sModelName;
    #----
    return sModel;
#====================================================
#--KGS modified SetLegendCMD on 21 Aug 2021
def SetDynamicLegend(fC_RangeMax,fC_RangeMin,fMax=None,fMin=None,bAllInst=True):
    #PopMessage([fC_RangeMin,fC_RangeMax,fMax,fMin,bAllInst]);
    if fC_RangeMax == None and fC_RangeMin == None:
        if fMax == None and fMin == None: return;
        bEnableRangeMax = True; bEnableRangeMin =True; bEnableFilter = False;
        if fMax == None: 
            bEnableRangeMax = False;fMax = 1;
        if fMin == None: 
            bEnableRangeMin = False;fMin = 0;
        _VCollabAPI.xSetCAELegendRangeEx(sModel,bAllInst,bEnableRangeMax,fMax,bEnableRangeMin,fMin,False);
        return;
    #--
    _VCollabAPI.xSetCAELegendRangeEx(sModel,False,False,1,False,0,False);
    fRangeList = _VCollabAPI.pxGetCAELegendRange(sModel);
    fMaxRes = fRangeList[1]; fMinRes = fRangeList[3];
    fSmallVal = (fMaxRes-fMinRes)*0.0000001;
    fSmallVal = min(fSmallVal,1.0E-6);
    if fMax == None: fMax = fMaxRes;
    if fMin == None: fMin = fMinRes;
    # Set Legend Range ---
    fRangeMin = fMin; fRangeMax = fMax;
    bMinFlag=True;bMaxFlag=True
    if fC_RangeMin==None or fC_RangeMin < -1E25:
        bMinFlag = False; fC_RangeMin = fMin;
    if fC_RangeMax==None or fC_RangeMax > 1E25:
        bMaxFlag = False; fC_RangeMax = fMax;
    if bMinFlag == False and  bMaxFlag == False : 
        #sgNotify("Both NA?","",0);
        _VCollabAPI.xSetCAELegendRangeEx(sModel,bAllInst,True,fMax,True,fMin,False);
        return ; # Both are NA?
    if (fC_RangeMax-fC_RangeMin) < fSmallVal:
        #sgNotify(f"Both same?",f"{fC_RangeMax} - {fC_RangeMin} < {fSmallVal}",0);
        _VCollabAPI.xSetCAELegendRangeEx(sModel,bAllInst,True,fMax,True,fMin,False);
        return;
    factor = 0.1;
    if bMinFlag:
        if abs(fC_RangeMin - fMin) < fSmallVal : # same
            fC_RangeMin = fRangeMin; bMinFlag = False;
        elif fC_RangeMin < fRangeMin:
            fRangeMin = fC_RangeMin-(fC_RangeMax-fC_RangeMin)* factor;
    if bMaxFlag:
        if abs(fC_RangeMax - fMax) < fSmallVal : # same
            fC_RangeMax = fRangeMax; bMaxFlag = False;
        elif fC_RangeMax > fRangeMax:
            fRangeMax = fC_RangeMax+(fC_RangeMax-fC_RangeMin)* factor;
    if bMinFlag == False and  bMaxFlag == False : 
        #sgNotify("Both Same?",f"{[fC_RangeMin,fRangeMin,fC_RangeMax,fRangeMax]}",0);
        _VCollabAPI.xSetCAELegendRangeEx(sModel,bAllInst,True,fMax,True,fMin,False);
        return ; # Both are NA?
    if fRangeMax - fRangeMin < fSmallVal:
        # same limits?
        return;
    bEnableRangeMax = True; bEnableRangeMin =True; bEnableFilter = False;
    if fRangeMax > 1.0E25 : 
        bEnableRangeMax = False; fRangeMax = fMax;
    if fRangeMin < -1.0E25 : 
        bEnableRangeMin = False; fRangeMin = fMin;
    #PrintMessage([fC_RangeMin,fRangeMin,fC_RangeMax,fRangeMax,fMax,fMin]);
    _VCollabAPI.xSetCAELegendRangeEx(sModel,bAllInst,bEnableRangeMax,fRangeMax,bEnableRangeMin,fRangeMin,bEnableFilter);
    #
    if fRangeMin > fC_RangeMin: fC_RangeMin = fRangeMin;
    if fRangeMax < fC_RangeMax: fC_RangeMax = fRangeMax;
    if bEnableRangeMax and bEnableRangeMin:
        if fC_RangeMax > fC_RangeMin:
            _VCollabAPI.xSetCAELegendDynamicRangeEx(sModel,fC_RangeMin, fC_RangeMax);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return;
#===================================================
#--------------------------------------------------------------------------
def Hex2RGBF(sHex):
    sHex = sHex.lstrip('#')
    RGBF = list(min(int(sHex[i:i+2], 16),255)/255.0 for i in (0, 2, 4));
    # sg.popup(sHex,RGBF);
    return RGBF;
def Hex2RGBI(sHex):
    if len(sHex) < 6: sHex=sHex+'000000'
    sHex = sHex.upper().lstrip('#')
    RGBI = list(min(int(sHex[i:i+2], 16),255) for i in (0, 2, 4));
    # sg.popup(sHex,RGBI);
    return RGBI;
#--LEGEND_HEXCOLORS,ff000,ffdd00,00ff00,00ddff,0000ff
def SetLegendCustHexColorsCMD(sVals):
    nColors=len(sVals);
    if nColors < 3 : return False;
    if nColors > 15: nColors = 15;
    fLegColorsList = [];
    for sHex in sVals[0:nColors]:
        if len(sHex) != 6: 
            PrintMessage(f"{sHex} is not valid Hex?");
            return;
        fLegColorsList = fLegColorsList + Hex2RGBF(sHex);
    #
    #nColorsRef = int(len(fLegColorsList)/3);
    bRevLeg = _VCollabAPI.xGetCAEReverseLegend(sModel);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    _VCollabAPI.xSetCAELegendColors(sModel,fLegColorsList);
    _VCollabAPI.xSetCAEReverseLegend(sModel,bRevLeg);
    return;
#---------------------------------------------------------------
#---------------------------------------------------------------
#SET_LEGEND_DYNRANGE,10,5,2,0   # No or vals and colors to match, depends on discrete on/off
def SetCustomLegendRangeCMD(sVals):
    if len(sVals) < 3: return;
    fRangeNew=[];
    refV = None;
    for sv in sVals:
        fv = GetFloat(sv,None);
        if fv == None: 
            sgNotify("Error",f"{sVals} is not valid Dynamic Range",0);
            return;
        if refV != None and refV <= fv:
            sgNotify("Error",f"{sVals} is not decresing order Dynamic Range",0);
            return;
        fRangeNew.append(fv);
     #------
    #sg.Popup(fRangeNew);
    bRevLeg = _VCollabAPI.xGetCAEReverseLegend(sModel);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    _VCollabAPI.xSetCAELegendDynamicRange(sModel,fRangeNew);
    _VCollabAPI.xSetCAEReverseLegend(sModel,bRevLeg);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return;
#===================================================
#SET_LEGEND,MAX,MIN,AMax,AMin,Precision,Discrete(Y/N),Reverse(Y/N),NColor,bAllInst(Y/N)
def SetLegendCMD(sVals):
    '''
    Sets the legend
    Parameters:
        sVals(List): sVals[0] - Legend custom premax value
                     sVals[1] - Legend custom premin value
                     sVals[2] - Legend Max value
                     sVals[3] - Legend Min value
                     sVals[4] - Precision value for legend
                     sVals[5] - Discrete legend (Y/N). Y to set discrete legend
                     sVals[6] - Reverse legend (Y/N). Y to set reverse legend
    Returns:
         None:
    '''
    nVals = len(sVals);
    if nVals < 2: return;
    if nVals > 7: #-- New set NColor option
        fLegColorsList = _VCollabAPI.pxGetCAELegendColors(sModel);
        nColorsRef = int(len(fLegColorsList)/3);
        nColors = GetInt(sVals[7],-1);
        if nColors >= 0 and nColorsRef != nColors:
            if nColors < 3: nColors = 0;
            if nColors > 32: nColors = 9;
            bRevLeg = _VCollabAPI.xGetCAEReverseLegend(sModel);
            _VCollabAPI.xSetCAEReverseLegend(sModel,False);
            _VCollabAPI.xSetCAELegendDefaultColors(sModel,0);
            _VCollabAPI.xSetCAELegendDefaultColors(sModel,nColors);
            _VCollabAPI.xSetCAEReverseLegend(sModel,bRevLeg);
    #-----------------------------------
    if nVals > 4:
        iP=0;
        if IsFloat(sVals[4]):
            iP = int(sVals[4]);
            bScientific = False;
            if iP < 0: bScientific = True; iP = -iP;
            if iP < 10:
                _VCollabAPI.xSetCAELegendAutoFormatMode(sModel, False)
                _VCollabAPI.xSetCAELegendNumeric(sModel,bScientific,abs(iP));
                if hasattr(_VCollabAPI,'xSetCAEProbeLabelDefaultNumericalFormat'):                
                    _VCollabAPI.xSetCAEProbeLabelDefaultNumericalFormat(sModel,iP,bScientific);
                _VCollabAPI.xSetTableValueNumeric(sModel,-2,-2,bScientific,iP); #Column Precision
    if nVals > 5:
        bFlag = False;
        if sVals[5].upper() == 'Y': bFlag = True;
        _VCollabAPI.xSetCAEDiscreteLegend(sModel,bFlag);
    if nVals > 6:
        bFlag = False;
        if sVals[6].upper() == 'Y': bFlag = True;
        #PopMessage(sVals,bFlag);
        _VCollabAPI.xSetCAEReverseLegend(sModel,bFlag);
    _VCollabAPI.xRefreshDialogs();
    #--------------------Need to set Dynamic legend after other settings--------------------------------
    
    # _VCollabAPI.xShowCAELegend(sModel,True);
    fCusMax = GetFloat(sVals[0],None);
    fCusMin = GetFloat(sVals[1],None);
    fUserMin = None; fUserMax = None;
    if nVals > 3:
        fUserMax = GetFloat(sVals[2],None);
        fUserMin = GetFloat(sVals[3],None);
    bAllInst = False;
    fLegInfo = _VCollabAPI.pxGetCAELegendRange(sModel);
    if fLegInfo[5] > 0: bAllInst = True;
    if nVals > 8 :
        bAllInst = False;
        if sVals[8].upper() == 'Y': bAllInst = True;
    SetDynamicLegend(fCusMax,fCusMin,fUserMax,fUserMin,bAllInst);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return;
#=====================================================
#** SEL_RESULT,*STRESS*Von*,L7*,NA
def SelectResultCMD(sVals):
    '''
    Sets the selected result as current result
    Parameters:
        sVals(List): sVals[0] - Result name
                     sVals[1] - Instance name or index
                     sVals[2] - Derived result name
    Returns:
         sResult: Selected result name
         None: If the selected result is invalid
    '''
    sResRef = sVals[0];nVals = len(sVals);
    if sResRef[0] != '*' : sResRef = '*'+sResRef;
    if sResRef[-1] != '*' : sResRef = sResRef+'*';
    sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
    for sResult in sResultList:
        if IsSubString(sResult,sResRef,True):
            sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
            sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
            sCurInst = sInstanceList[-1];nInst = len(sInstanceList);
            iInst = None;
            if nInst > 1 and nVals > 1:
                if IsFloat(sVals[1]):
                    iInst = int(sVals[1])-1;
                else: 
                    #PopMessage(sInstanceList,['Name',sVals[1]]);
                    for k in range(nInst):
                        if IsSubString(sInstanceList[k],'*'+sVals[1]+'*',True):
                            iInst = k; 
                            #PopMessage(iInst,['Name',sVals[1]]);
                            break;
                    if iInst == None:
                        aInst = EvalInstantce(nInst,sVals[1]);
                        if aInst != None :
                            iInst = aInst-1;
                            #PopMessage(iInst,['Eval',sVals[1]]);
                #-------------
                if iInst != None and iInst >= 0 and iInst < nInst:
                    sCurInst = sInstanceList[iInst];
                else:
                    PrintMessage(f"In sel_result: Instance {sVals[1]} Not found");
            #----
            if nVals > 2 and   sVals[2].upper()  != 'NA':
                sDerived = sVals[2];
                if IsWildString(sDerived):
                    sName = sDerived; sDerived = None;
                    sDerivedList = _VCollabAPI.pxGetCAEDerivedResults(sModel,sResult);
                    for sDRName in sDerivedList:
                        if IsSubString(sDRName,sName,True):
                            sDerived = sDRName; break;
                    #---- else error
                    if sDerived == None:
                        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
                        PrintMessage(f"Select Result Error: Derived Result {sVals[2]} is not found, {sDerived} is used");
            #--------
            #PopMessage([sModel,sResult,sCurInst,sDerived],'Sel');
            retflag = _VCollabAPI.xSetCAEResult(sModel,sResult,sCurInst,sDerived);
            if retflag == False: return None;
            return sResult;
            break;
    #--- End for
    PrintMessage(f"In sel_result: {sResRef} not found");
    return None;
#====================================================
#Type,nFrames,bStaticFringe (True/False),Scale,Speed
#iType => linear=0,transient=1,harmonic=3
def AnimationSettingsCMD(nVals,sVals):
    '''
    Sets animation type and settings
    Parameters:        
        sVals(List): sVals[0] - Animation type (linear=0,transient=1,harmonic=3)
                     sVals[1] - Sets number of frames (instances)
                     sVals[2] - Sets static fringe (Y/N). Y for static fringe
                     sVals[3] - Sets scale factor based on bounding box. Deformation percentage w.r.t. geometry size 
                     sVals[4] - Set a delay value to slow animation in milliseconds. Valid range 0 to 1000. 0 sets max speed
        nVals: Length of the sVals list
    Returns:
        None
    '''
    if nVals < 2: return;
    iType = 0; #linear=0,transient=1,result=2,harmonic=3
    if IsFloat(sVals[0]): iType = int(sVals[0]);
    if iType < 0 or iType > 3 or iType == 2: # Wrong type?
        iType = 0;
    iNoOfFrames=16;fScale=1.0;
    if IsFloat(sVals[1]): iNoOfFrames = int(sVals[1]);
    #----------
    bStaticFringe = False;
    if iType == 1 : bStaticFringe = True;
    if nVals > 2:
        if sVals[2].upper() == 'Y' :
            bStaticFringe = True;
        else:
            bStaticFringe = False;
    #-----------------
    if nVals > 3:
        if IsFloat(sVals[3]):
            fScale = float(sVals[3]);
            if iType == 3:
                _VCollabAPI.xSetCAEDeformBoundPercentage(fScale);
            else:
                bUniform = True;
                _VCollabAPI.xSetCAEDeformScaleFactor(bUniform,fScale,fScale,fScale);
    #---------------------
    if nVals > 4:
        if IsFloat(sVals[4]):
            iSpeed = int(sVals[4]);
            if iSpeed < 2 or iSpeed > 100: iSpeed = 40;
            _VCollabAPI.xSetCAEAnimationSpeed(sModel,iSpeed);
    #-------------------------
    sSelectedFrames = u"";
    if iType == 3:
        sSelectedFrames = u"Displacement";
    bReserved1 = False; bReserved2 = False;
    bHarmonic = False; bSwing = False;
    #PopMessage(bStaticFringe,"bStaticFringe");
    _VCollabAPI.xSetCAEAnimationSettings(sModel,iType,iNoOfFrames,bHarmonic,bSwing,bStaticFringe,
                                         sSelectedFrames,bReserved1,bReserved2);
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xRefreshDialogs();
    return;
##===================================================
#--ADD_PROBE_RESULT,START/END/ADD,Stress*VON*,St_Von,NA,140.0
def SetProbeResultCMD(sSelectedResultList,nVals,sVals):
    sMode = sVals[0].upper();
    if len(sMode) < 1: sMode = 'N';
    if sMode[0] == 'S' or sSelectedResultList==None: #START
        sSelectedResultList = [];
    aRes = sVals[1];
    sResult=SelectResult(sModel,aRes,False);
    if sResult == None: 
        sgNotify("Error",f"{sMode} {aRes} not valid",2);
        return sSelectedResultList;
    if sMode[0] != 'N': 
        if not sResult in sSelectedResultList: sSelectedResultList.append(sResult);
    if nVals > 2: 
        sdName = sVals[2];
        _VCollabAPI.xSetCAEResultDisplayName(sModel,sResult,sdName);
        
    if nVals > 4: 
        bMin = False;bMax = False; MaxVal = 100.0; MinVal = 1.0;
        if IsFloat(sVals[3]):
            MinVal = float(sVals[3]);bMin = True;
            if MinVal <= -1E10 or MinVal >= 1E10 : bMin = False;
        if IsFloat(sVals[4]):
            MaxVal = float(sVals[4]);bMax = True;
            if MinVal >= MaxVal: bMin = False;
            if MaxVal <= -1E10 or MaxVal >= 1E10 : bMax = False;
        _VCollabAPI.xSetCAEProbeHiLightResultRange(sModel,sResult,bMin,MinVal,bMax,MaxVal);
   
    if len(sSelectedResultList) < 1 : return sSelectedResultList;
   
    if sMode[0] == 'E':
        _VCollabAPI.xSetCAEProbeSelectedResults(sModel,';'.join(sSelectedResultList));
        _VCollabAPI.xSetCAEProbeType(sModel,3) #3 => All Selected Result
        sSelectedResultList = [];
    return sSelectedResultList;
#---------------------------------------------------------------------------
# Stress*VON*,St_Von,NA,140.0
# Stress*ABS*,PriStAbs,-140,140
def SetProbeResInfoList(ProbeResInfoList):
    '''
    Sets a result's highlight range value
    Parameters:
        ProbeResInfoList(List): ProbeResInfoList[0] - Result name
                                ProbeResInfoList[1] - Result display name
                                ProbeResInfoList[2] - Sets selected result's minimum range value. If a probe table value is less than this, then the probe table will be highlighted
                                ProbeResInfoList[3] - Sets selected result's maximum range value. If a probe table value is greater than this, then the probe table will be highlighted
    Returns:
        None
    '''
    #global sg_ResultDspList;sg_ResultDspList="";
    sSelectedResultList = u"";nResults = 0;
    for sVals in ProbeResInfoList:
        nVals = len(sVals);
        if nVals < 1: continue;
        aRes = sVals[0];
        sResult=SelectResult(sModel,aRes,False);
        #PopMessage(sVals,sResult);
        if sResult == None: continue;
        sSelectedResultList=sSelectedResultList+sResult+';';nResults=nResults+1;
        if nVals > 1: 
            sdName = sVals[1];
            _VCollabAPI.xSetCAEResultDisplayName(sModel,sResult,sdName);
        if nVals > 3: 
            bMin = False;bMax = False; MaxVal = 100.0; MinVal = 1.0;
            if IsFloat(sVals[2]):
                MinVal = float(sVals[2]);bMin = True;
                if MinVal <= -0.99E10 or MinVal >= 0.99E10 : bMin = False;
            if IsFloat(sVals[3]):
                MaxVal = float(sVals[3]);bMax = True;
                if MinVal >= MaxVal: bMin = False;
                if MaxVal >= 0.99E10: bMax = False;
            _VCollabAPI.xSetCAEProbeHiLightResultRange(sModel,sResult,bMin,MinVal,bMax,MaxVal);
    #--- end for 
    if nResults > 1:
        _VCollabAPI.xSetCAEProbeSelectedResults(sModel,sSelectedResultList);
        _VCollabAPI.xSetCAEProbeType(sModel,3) #3 => All Selected Result
    else:
        _VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    return;
#================================================
#SHOW_LABEL,ID=True,ROW=True,COL=False,Rank=True,PART=False,HEADER=False,ABR=True,PROBE=0,DISP=Y/N,ARRANGE=0-5
def SetShowLabelCMD(nVals,sVals):
    '''
    Sets probe label settings
    Parameters:
        sVals(List): ID= Show node/element id (Y/N). Y to show id (optional)
                     ROW= Show row header (Y/N). Y to show row header (optional)
                     COL= Show Column header (Y/N). Y to show Column header (optional)
                     Rank= Show Rank (Y/N). Y to show Rank (optional)
                     PART= Show Part name (Y/N). Y to show Part name (optional)
                     HEADER= Show Header Legend(Y/N). Y to show Header Legend (optional)
                     ABR= Display Abbreviations legend. Y to show Abbreviation Legend (optional)
                     PROBE= Sets current probe type. The valid range is 1 to 5 (optional)
                            1 for CurrentResult-Derived
                            2 for CurrentResult-Full
                            3 for All Results-Table
                            4 for All Instances-Table
                            5 for All Instances-XYPlot
                     DISP= Show labels (Y/N). Y to show labels
                     ARRANGE= Sets label arrangement mode. The valid range is 0 to 5 (optional)
                                0 – Actual.
                                1 – Top-Bottom.
                                2 – Compact
                                3 – Circular
                                4 – Silhouette
                                5 – Rectangular
        nVals: Length of the sVals list
    Returns:
        None
    '''
    bID=False;bRow=False;bCol=False;bPart=False;
    bRank = False; bHeader=False; bAscending = False;
    for k in range(nVals):
        sCMD = sVals[k].upper().split('=');
        if len(sCMD) < 2: continue;
        if sCMD[0] == 'ID' and sCMD[1] == 'Y' :
            bID = True; continue;
        if sCMD[0] == 'ROW' and sCMD[1] == 'Y' :
            bRow = True; continue;
        if sCMD[0] == 'COL' and sCMD[1] == 'Y' :
            bCol = True;continue;
        if sCMD[0] == 'PART' and sCMD[1] == 'Y' :
            bPart = True;continue;
        if sCMD[0] == 'DISP':
            if sCMD[1] == 'Y' :
                _VCollabAPI.xShowAllLabels();
            else:
                _VCollabAPI.xHideAllLabels();
            continue;
            
        if sCMD[0] == 'RANK':
            if IsFloat(sCMD[1]):
                iRank = int(sCMD[1]); 
                bAscending = False; bRank = True;
                if iRank == 0 :
                    bRank = False;
                elif iRank < 0 :
                    bAscending = True;
            #PopMessage([bRank,bAscending],sCMD);
            continue;
        if sCMD[0] == 'PROBE':
            iType = 1;
            if IsFloat(sCMD[1]):
                iType = int(sCMD[1]); 
                if iType > 5 or iType < 1: iType = 1;
            _VCollabAPI.xSetCAEProbeType(sModel,iType);
            continue;
        if sCMD[0] == 'ARRANGE':
            global iLabelArrangeMode;
            iType = iLabelArrangeMode;
            if IsFloat(sCMD[1]):
                iType = int(sCMD[1]); 
                if iType > 5 or iType < 1: iType = iLabelArrangeMode;
                iLabelArrangeMode = iType;
            _VCollabAPI.xSetLabelAutoArrangeMode(iLabelArrangeMode);
            continue;
            
        if sCMD[0] == 'HEADER' and sCMD[1] == 'Y' :
            bHeader = True;continue;
        if sCMD[0] == 'ABR':
            if sCMD[1] == 'Y' :
                _VCollabAPI.xSetCAEProbeTemplateAbbreviation(sModel,True);
            else:
                _VCollabAPI.xSetCAEProbeTemplateAbbreviation(sModel,False);
            continue;
    #-- end for
    _VCollabAPI.xSetCAEProbeLabelFields(sModel,bID,bRow,bCol,bPart);
    _VCollabAPI.xSetCAEProbeRankHeader(bRank,bAscending);
    _VCollabAPI.xShowCAEHeaderLegend(sModel,bHeader,True);
    
        
    return;
#====================================================
#SET_DISPLAY,COLOR=Y,LEGEND=Y,DEFORM=Y,UDMESH=1,DMODE=1,SECTION=N,AXIS=Y,BG=1
def SetDisplayCMD(nVals,sVals):
    '''
    Sets display mode settings
    Parameters:
        sVals(List): COLOR= Sets CAE color plot (Y/N). Y to apply color plot
                     LEGEND= Show legend (Y/N). Y to show legend
                     DEFORM= Sets Deform mesh (Y/N). Y to set Deform mesh 
                     UDMESH= Sets visibility for the undeformed mesh (0-3)
                     DMODE= Sets display mode of the scene. Valid range 0 to 5 
                            0 – Shaded,
                            1 – Shaded Mesh.
                            2 – WireFrame.
                            3 – HiddenLine Removal.
                            4 – Point.
                            5 – Transparent
                     SECTION= Show Section (Y/N). Y to Show Section
                     AXIS= Show Axis (Y/N). Y to Show Axis
                     BG= Valid Range 0 to 2
                         0-Plain 
                         1-Gradient
                         2-Texture
        nVals: Length of the sVals list
    Returns:
        None
    '''
    for k in range(nVals):
        sCMD = sVals[k].upper().split('=');
        if len(sCMD) < 2: continue;
        if sCMD[0] == 'COLOR':
            bFlag = False;
            if sCMD[1] == 'Y' : bFlag = True;
            _VCollabAPI.xSetCAEColorPlot(sModel,bFlag);
            continue;
        if sCMD[0] == 'LEGEND':
            bFlag = False;
            if sCMD[1] == 'Y' : bFlag = True;
            _VCollabAPI.xShowCAELegend(sModel,bFlag);
            continue;
        if sCMD[0] == 'AXIS':
            bFlag = False;
            if sCMD[1] == 'Y' : bFlag = True;
            _VCollabAPI.xShowAxis(bFlag);
            continue;
        if sCMD[0] == 'SECTION':
            bFlag = False;
            if sCMD[1] == 'Y' : bFlag = True;
            _VCollabAPI.xShowSection(bFlag);
            continue;  
        if sCMD[0] == 'DEFORM':
            bFlag = False;
            if sCMD[1] == 'Y' : bFlag = True;
            _VCollabAPI.xSetCAEDeformMesh(sModel,bFlag);
            continue;  
        if sCMD[0] == 'UDMESH':
            if IsFloat(sCMD[1]):
                iMode = int(sCMD[1]);
                if iMode < 0 or iMode > 3:
                    _VCollabAPI.xShowCAEUnDeformedMesh(sModel,False);
                    continue;
                _VCollabAPI.xShowCAEUnDeformedMesh(sModel,True);
                _VCollabAPI.xSetCAEUndeformedMeshDisplayMode(sModel,iMode);
                continue;
            elif sCMD[1] == 'Y' : 
                _VCollabAPI.xShowCAEUnDeformedMesh(sModel,True);
            else:
                _VCollabAPI.xShowCAEUnDeformedMesh(sModel,False);
            continue;  
        if sCMD[0] == 'BG':
            iMode = 1;
            if IsFloat(sCMD[1]):
                iMode = int(sCMD[1]);
                if iMode < 0 or iMode > 2: iMode = 1;
            _VCollabAPI.xSetBackgroundMode(iMode);
            continue;
        if sCMD[0] == 'DMODE':
            if IsFloat(sCMD[1]):
                iMode = int(sCMD[1]);
                if iMode >=0 and iMode <= 5:
                    _VCollabAPI.xSetDisplayMode(iMode);
                    _VCollabAPI.xSetShadedMeshColorMode(1);
                    continue;
                if iMode == 6:
                    _VCollabAPI.xSetFeatureEdges(True,False,20,20,50,1);
                elif iMode == 7:
                    _VCollabAPI.xSetFeatureEdges(False,False,20,20,50,1);
                elif iMode == 10:
                    _VCollabAPI.xSetShadedMeshColorMode(0);
                continue;
            else:
                _VCollabAPI.xSetDisplayMode(0);
            continue;
        if sCMD[0] == 'HEADER':
            bFlag = False;
            if sCMD[1] == 'Y' : bFlag = True;
            _VCollabAPI.xShowCAEHeaderLegend(sModel,bFlag,True);
    _VCollabAPI.xRefreshDialogs();
    return;
#=====================================================
# PART_OPTIONS,DMODE=1,*Bracket*,*Lever*
# PART_OPTIONS,COLOR=Y,*Bracket*,*Lever*
def SetPartDisplayOptionsCMD(sVals):
    '''
    Sets Display mode or Color plot for specific parts
    Parameters:
        sVals(List): sVals[0] - Set Display mode or Color plot (DMODE/COLOR)
                                DMODE - 0 for Shaded; 1 for Shaded Mesh; 2 for WireFrame; 3 for Hidden Line Removal; 4 for Point; 5 for Transparent
                                COLOR - Y to display Color plot 
                     sVals[1:] - Part name list
    Returns:
        None
    '''
    sCMD = sVals[0].upper().split('=');
    if sCMD[0] == 'COLOR':
        bFlag = True;
        if len(sCMD) > 1:
            if sCMD[1] != 'Y' : bFlag = False;
        sPartList=_VCollabAPI.pxGetPartsList(sModel,"",0);
        sInpParts = sVals[1:];
        for aPart in  sPartList:
            for sPart in sInpParts:
                if IsSubString(aPart,sPart,True):
                    _VCollabAPI.xSetColorPlotEx(sModel,aPart,1,bFlag);
        return;
    if sCMD[0] == 'DMODE':
        iMode=0;
        if len(sCMD) > 1:
            if IsFloat(sCMD[1]):
                iMode = int(sCMD[1]);
                if iMode < 0 or iMode > 5: iMode = 0;
        sPartList=_VCollabAPI.pxGetPartsList(sModel,"",0);
        sInpParts = sVals[1:];
        for aPart in  sPartList:
            for sPart in sInpParts:
                if IsSubString(aPart,sPart,True):
                    _VCollabAPI.xSetPartDisplayMode(sModel,aPart,iMode);
        #-- end for
        _VCollabAPI.xDeselectAll(sModel);
    return;
#=====================================================
#DEL_ENTITY,PROBE,XY,LABEL,SYMBOL
def DeleteEntityCMD(nVals,sVals):
    '''
    Deletes the probe label, XY plot, labels and symbol plot entities
    Parameters:
        sVals(List): Deletes the entities (PROBE,XY,LABEL,SYMBOL)
        nVals: Length of the sVals list
    Returns:
        None
    '''
    sAll=u"";
    if nVals == 1:
        # _VCollabAPI.xShowAll(sAll);
        # _VCollabAPI.xInvertShow(sAll);
        #_VCollabAPI.xShowCAELegend(sAll,False);
        _VCollabAPI.xDeleteAllLabels();
        _VCollabAPI.xDeleteXYPlot(sAll);
        _VCollabAPI.xDeleteSymbolPlot(sAll,sAll);
        _VCollabAPI.xShowCAEHeaderLegend(sModel,False,True);
        _VCollabAPI.xShowSection(False);
        #_VCollabAPI.xShowAxis(False);
        return;
    for k in range(1,nVals):
        sCMD = sVals[k].upper();
        if sCMD == 'LABEL':
            _VCollabAPI.xDeleteAllLabels();
            _VCollabAPI.xShowCAEHeaderLegend(sModel,False,True);
            continue;
        if sCMD == 'XY':
            _VCollabAPI.xDeleteXYPlot(sAll);continue;
        if sCMD == 'SYMBOL':    
            _VCollabAPI.xDeleteSymbolPlot(sAll,sAll);continue;
        if sCMD == 'PROBE':
            _VCollabAPI.xDeleteAllProbeLabels(sModel); continue;
    #--- End for
    return;
#=====================================================
#CREATE_RESULT_CYL,Displacement,Disp Radial,53.66,73.05,42.747,0,0,1,1,0,0,U,CylCoord,
#CREATE_RESULT_CYL,RefResult,NewResult,Origin(X,Y,Z),XDir(x,Y,Z),YDir(x,y,z),U/All
def CreateCylResultCMD(sVals):
    '''
    Creates cylindrical co-ordinate result for the selected result
    Parameters:
        sVals(List): sVals[0] - Result name
                     sVals[1] - New result name 
                     sVals[2:5] - Origin of the new coordinate system
                     sVals[5:8] - X axis vector
                     sVals[8:11] - Y axis vector
                     sVals[11] - Component name can be empty or any one of the following or All for all the components
                                 For Vector Result - "U","V","W"
                                 For Tensor Result - "S11","S22","S33","S12","S23","S13"
                     sVals[12] - New Coordinate System Name
    Returns:
        None
    '''
    nVals = len(sVals);
    if nVals < 11: return;
    sRefRes = sVals[0];
    sNewRes = sVals[1];
    iCSYType = 1;
    vec=[0,0,0,0,0,0,0,0,0];
    for i in range(2,11):
        if IsFloat(sVals[i]):
            vec[i-2] = float(sVals[i]);
    #--
    sComponent = 'U';
    if nVals > 11:
        sComponent = sVals[11];
        if len(sComponent) < 1: sComponent = 'U';
        if sComponent == 'ALL' : sComponent = u"";
    sCSYName = u"VC_TempCys";bDelFlag = True;
    if nVals > 12:
        sCSYName = sVals[12];
        bDelFlag = False;
    _VCollabAPI.xCreateUserCoordinateSystemEx(sCSYName,iCSYType,vec[0],vec[1],vec[2],
            vec[3],vec[4],vec[5],vec[6],vec[7],vec[8],False);
    _VCollabAPI.xCreateCAENewUCSResult(sCSYName, sNewRes,sRefRes, sComponent,sModel);
    if bDelFlag:
        _VCollabAPI.xDeleteUserCoordinateSystem(sCSYName);
    return;
#--------------------------------------------------
#-- MODAL_VPS,10,Y
def CreateModalViewsCMD(nVals,sVals):
    '''
    Creates modal view with mode case table
    Parameters:
        sVals(List): sVals[1] - Number of mode case 
                     sVals[2] - Creates a Mode case table (Y/N). Y for mode case table
        nVals: Length of the sVals list
    Returns:
        None
    '''
    sViewPathName = CurVPathName;
    nCount = 10;
    if nVals > 1:
        nCount = GetInt(sVals[1],5);
    #Set CAE Display Settings
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xShowCAELegend(sModel,True);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    _VCollabAPI.xSetCAEDiscreteLegend(sModel,False);
    _VCollabAPI.xSetLabelAutoArrangeMode(4);
    sResName = sModalResultName;
    sModeList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResName);
    sDefDerivedResult = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResName);
    #
    #_VCollabAPI.xShowAll(sModel);
    _VCollabAPI.xRefreshDialogs();
    fRefValue = 0.0;
    count = 1;
    for sModeName in sModeList:
        sMode = u"Mode" + str(count);
        bRtnFlag = _VCollabAPI.xSetCAEResult(sModel,sResName,sModeName,sDefDerivedResult);
        if bRtnFlag == False: 
            PrintMessage(_VCollabAPI.xGetLastError(),"xSetCAEResult Failed");
            continue;
        if igEigenMode == 1:
            fValue = GetCAEModalFrequency(sResName,sModeName);
        else:
            fValue = GetCAEModalEigenValue(sResName,sModeName);
        if abs(fValue - fRefValue) < 0.1: continue;
        fRefValue = fValue;
        _VCollabAPI.xDeleteAllLabels();
        if igEigenMode == 1:
            DisplayFrequencyLabel("Mode shape:",fRefValue);
        else:
            DisplayEigenLabel("Mode shape:",fRefValue);
        # Create Viewpoint
        sViewPointName = u"VP - " + sMode.replace(':','-');
        SetModalAnimation(3,True);
        AddVP_HF(sViewPointName,sViewPathName,-1);
        _VCollabAPI.xSetCAEAnimationInCurViewPoint(True);
        count = count + 1;
        if nCount > 0 and count > nCount : break; 
    #================================================================
    if nVals < 3: return;
    bTableView = False;
    if sVals[2].upper() != 'Y':
        return;
    bTableView = True;
    fRefValue = 0.0;
    count = 1;
    dx=0.30;dy=0.08;
    _VCollabAPI.xDeleteAllLabels();
    #_VCollabAPI.xHideAllParts(sModel);
    SetBlankView();
    _VCollabAPI.xShowCAELegend(sModel,False);
    _VCollabAPI.xAdd2DNotes("Mode Shapes Table" ,dx,dy,True);
    dy = dy + 0.1;
    nPage = 1;nModesPerPage = 20;nLines = 0;
    for sModeName in sModeList:
        sMode = u"Mode" + str(count);
        bRtnFlag = _VCollabAPI.xSetCAEResult(sModel,sResName,sModeName,sDefDerivedResult)
        if bRtnFlag == False: 
            PrintMessage(_VCollabAPI.xGetLastError(),"Error from xSetCAEResult");
            continue
        if igEigenMode == 1:
            fValue = GetCAEModalFrequency(sResName,sModeName);
        else:
            fValue = GetCAEModalEigenValue(sResName,sModeName);
        if abs(fValue - fRefValue) < 0.1: continue;
        fRefValue = fValue;
        if igEigenMode == 1:
            DisplayFrequencyLabel(sMode+" ",fRefValue,dx,dy);
        else:
            DisplayEigenLabel(sMode+" ",fRefValue,dx,dy);
        nLines = nLines+1;
        # fEigen = 0.0;
        # DisplayFrequencyLabels(sMode+" ",fRefValue,fEigen,dx,dy);
        dy = dy + 0.04;
        count = count + 1;
        if nLines == nModesPerPage :
            # Create Viewpoint
            sViewPointName = u"VP - " + "Table"+str(nPage);
            AddVP_HF(sViewPointName,sViewPathName,-1);
            nPage = nPage + 1;nLines=0;
            _VCollabAPI.xDeleteAllLabels();
            dx=0.30;dy=0.08;
            _VCollabAPI.xAdd2DNotes("Mode Shapes Table"+str(nPage) ,dx,dy,True);
            dy = dy + 0.1;
        if nCount > 0 and count > nCount : break;  
    # Create Viewpoint
    if nLines != 0:
        sViewPointName = u"VP - " + "Table"+str(nPage);
        AddVP_HF(sViewPointName,sViewPathName,-1);
    return;
#===========================End of Modal Report ==========================
#=======================================================
#ALL_RESULT_VPS,5
def CreateHotspotsForEachResultCMD(nVals,sVals):
    '''
    Computes Hotspots and creates a viewpoint for each result 
    Parameters:
        sVals(List): sVals[1] - Number of Hotspots
        nVals: Length of the sVals list 
    Returns:
        None
    '''
    sViewPathName = CurVPathName;
    igMaxHostSpots = 3;
    if nVals > 1:
        igMaxHostSpots = GetInt(sVals[1],3);
        if igMaxHostSpots < 1: igMaxHostSpots = 1;
    #-----------------------------------------------
    sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
    #Set CAE Display Settings
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xShowCAELegend(sModel,True);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    _VCollabAPI.xSetCAEDiscreteLegend(sModel,True);
    _VCollabAPI.xSetLabelAutoArrangeMode(4); # Compact Mode
    _VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    #Estimate Zone Radious
    sModelList = _VCollabAPI.pxGetModels();nModels=len(sModelList);
    fZoneRadius = GetZoneRadius(sModel,0.05);
    for sResult in sResultList:
        # Not for these results
        if sResult.upper().find(u"MATERIAL") >= 0 : continue;
        if sResult.upper().find(u"CONSTRAINT") >= 0 : continue;
        if sResult.upper().find(u"THICKNESS") >= 0 : continue;
        if sResult.upper().find(u"BOTTOM") >= 0 : continue;
        if sResult.upper().find(u"FORCE") >= 0 : continue;
        if sResult.upper().find(u"VOLUME") >= 0 : continue;
        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sResult);
        IsTop = True;
        if sResult.upper().find(u"LIFE") >= 0 : IsTop = False;
        if sResult.upper().find(u"FRF") >= 0 : IsTop = False;
        # sMaxInst, sMinInst = GetMaxMinInstanceForResult(sModel,sResult,sDerived);
        #--- InstFlag= 0 => Last Instance, 1 => Max Instance, 2 => Min Instance, 
        #---           3 => First Instance, else current Instance
        InstFlag = 1;
        if IsTop == False: InstFlag = 2;
        # Multi-Model support..
        sCurModel = sModel;
        if nModels > 1:
            for aModel in sModelList:
                if aModel == sCurModel: continue;
                #---------------
                _VCollabAPI.xSetCurCAEModelByName(aModel);
                sCurInst = SelectInstance(aModel,sResult,sDerived,InstFlag);
                _VCollabAPI.xSetCAEResult(aModel,sResult,sCurInst,sDerived);
                fMinMaxList = _VCollabAPI.pxGetCAEVisiblePartsMinMax(u"");
                if len(fMinMaxList) < 2:
                    PrintErrorMessage(sResult+" "+sCurInst, u"pxGetCAEVisiblePartsMinMax Failed ");
                    continue;
                fMax = fMinMaxList[1];fMin = fMinMaxList[0];
                #PrintMessage(u"Max Min = "+str(fMax)+ u" , "+str(fMin));
                if abs(fMax) < 1.0E-20 : continue;
                if abs(fMax) > 1.0E20 : continue;
                SetLegendPrecisionMaxMin(aModel,fMax,fMin);
                #------------
            _VCollabAPI.xSetCurCAEModelByName(sCurModel);
        #---------------
        sCurInst = SelectInstance(sModel,sResult,sDerived,InstFlag);
        _VCollabAPI.xSetCAEResult(sModel,sResult,sCurInst,sDerived);
        fMinMaxList = _VCollabAPI.pxGetCAEVisiblePartsMinMax(u"");
        if len(fMinMaxList) < 2:
            PrintErrorMessage(sResult+" "+sCurInst, u"pxGetCAEVisiblePartsMinMax Failed ");
            continue;
        fMax = fMinMaxList[1];fMin = fMinMaxList[0];
        #PrintMessage(u"Max Min = "+str(fMax)+ u" , "+str(fMin));
        if abs(fMax) < 1.0E-20 : continue;
        if abs(fMax) > 1.0E20 : continue;
        SetLegendPrecisionMaxMin(sModel,fMax,fMin);
        #------------      
        
        _VCollabAPI.xFitView();
        _VCollabAPI.xRefreshNormals();
        _VCollabAPI.xCAERefresh(u"");
        fPosX=0.25;fPosY=0.08;
        _VCollabAPI.xDeleteAllLabels();
        if IsTop :
            sRefRes = Float2String(fMax);
            sNoteString = u"Maximum "+sResult+u" = "+sRefRes;
            _VCollabAPI.xAdd2DNotes(sNoteString,fPosX,fPosY,True);
            _VCollabAPI.xSetCAEReverseLegend(sModel,False);
            ComputeFewHotspots(igMaxHostSpots,0,fZoneRadius);
            AddVP_HF(sResult+'-View',sViewPathName,-1);
        else :
            sRefRes = Float2String(fMin);
            sNoteString = u"Minimum "+sResult+u" = "+sRefRes;
            _VCollabAPI.xAdd2DNotes(sNoteString,fPosX,fPosY,True);
            _VCollabAPI.xSetCAEReverseLegend(sModel,True);
            ComputeFewHotspots(0,igMaxHostSpots,fZoneRadius);
            AddVP_HF(sResult+'-View',sViewPathName,-1);
        #------------------------------
    return;
#===================================================
def IsTensorResult(sModel,sResult):
    '''
    Checks if the selected result is tensor
    Parameters:
        sModel: Cax model name
        sResult: Result name
    Returns:
        Boolean: True if the selected result is tensor
                 False if the selected result is not tensor
    '''
    iType = _VCollabAPI.xGetCAEResultType(sModel,sResult);
    if iType == 3 or iType == 7 :
        return True;
    return False;
#-------------------------------------
def IsComplexResult(sModel,sResult):
    '''
    Checks if the selected result is complex
    Parameters:
        sModel: Cax model name
        sResult: Result name
    Returns:
        Boolean: True if the selected result is complex
                 False if the selected result is not complex
    '''
    if _VCollabAPI.xGetCAEAnalysisType(sModel,sResult) == 3 : 
        return True;
    return False;
def IsVectorResult(sModel,sResult):
    '''
    Checks if the selected result is vector
    Parameters:
        sModel: Cax model name
        sResult: Result name
    Returns:
        Boolean: True if the selected result is vector
                 False if the selected result is not vector
    '''
    iType = _VCollabAPI.xGetCAEResultType(sModel,sResult);
    if iType in [1,2,5,6]:
        return True;
    return False;
#-------------------------------------------
def CAEFilterParts(sModel=u"",fRangeMin=None,fRangeMax=None,bFitView=False):
    '''
    Hide parts for which the result is not within the legend range
    Parameters:
        sModel: Cax model name (optional)
        fRangeMin: Sets minimum legend range value (optional)
        fRangeMax: Sets maximum legend range value(optional)
        bFitView(Boolean): Fit view (optional)
    Returns:
             
    '''
    if fRangeMin != None or fRangeMax != None:
        bEnableRangeMin=True;
        if fRangeMin == None : 
            bEnableRangeMin=False;
            fRangeMin = 0.0;
        bEnableRangeMax=True;
        if fRangeMax == None : 
            bEnableRangeMax=False;
            fRangeMax = fRangeMin + 1.0;
        #
        _VCollabAPI.xSetCAELegendRange(sModel,bEnableRangeMax,fRangeMax,bEnableRangeMin,fRangeMin,False);
    _VCollabAPI.xFilterCAEParts(sModel);
    if bFitView: _VCollabAPI.xFitView();
    return;
#------------------------------------------------------------
fg_XYPlotWindowSize = [0.1,0.1,0.75,0.35];
fg_XYBg_R=0.9;fg_XYBg_G=0.9;fg_XYBg_B=0.9 # XY Plot Background Colors RGB (0 to 1)
#SETXYPLOT_WIN,<bgColor(rgb), <winsize (xmin,ymin,xmax,ymax)>
def SetXYPlotWindow_CMD(nVals,sVals):
    '''
    Sets the XY plot background and windows size
    Parameters:
        sVals(List): sVals[0:3] - XY Plot Background Colors RGB (0 to 1)
                     sVals[3:7] - XY plot windows size (xmin,ymin,xmax,ymax)
        nVals: Length of sVals list
    Returns:
        None
    '''
    if nVals < 3: return;
    R = GetFloat(sVals[0],-1);
    if R >= 0.0 :
        G = GetFloat(sVals[1],-1);
        if G >= 0.0:
            B = GetFloat(sVals[2],-1);
            if R>1.0 : R = min(R/256,1.0);
            if G>1.0 : G = min(G/256,1.0);
            if B>1.0 : B = min(B/256,1.0);
            global fg_XYBg_R; global fg_XYBg_G; global fg_XYBg_B;
            fg_XYBg_R = R; fg_XYBg_G = G; fg_XYBg_B = B;
    #---------------------
    if nVals < 7: return;
    xmin = GetFloat(sVals[3],-1); 
    if xmin < 0.0 or xmin > 0.9 : return;
    ymin = GetFloat(sVals[4],-1);
    if ymin < 0.0 or ymin > 0.9 : return;
    xmax = GetFloat(sVals[5],-1); 
    if xmax < 0.2 or xmax > 1.0 : return;
    ymax = GetFloat(sVals[6],-1);
    if ymax < 0.2 or ymax > 1.0 : return;
    if (xmax-xmin) < 0.2 or (ymax-ymin) < 0.1 :
        sgNotify("Error","Too small window",5);
        return;
    global fg_XYPlotWindowSize;
    fg_XYPlotWindowSize = [xmin,ymin,xmax-xmin,ymax-ymin];
    #sgNotify("Msg",f"Win size={fg_XYPlotWindowSize}",0);
    return;
#-----------------------------------------
def CreateTransientXYPlot(sPlotName,lNodeList,sResult,sDerivedResult,xResult="Frequency"):
    '''
    Creates Transient XY plot for the selected result
    Parameters:
        sPlotName: XY plot name
        lNodeList: List of IDs as a string delimited by ‘;’
        sResult: Result name
        sDerivedResult: Derived result name
        xResult: X axis parameter (time / instance number / frequency)(optional)
    Returns:
        None
    '''
    if len(lNodeList) < 1:
        PrintErrorMessage(u"XYPlot No input Nodes");
        return;
    # sPlotName = u"Test1";
    _VCollabAPI.xCreateXYPlot(sPlotName);
    fSizeList = _VCollabAPI.pxGetWindowSize();
    fXmin = fg_XYPlotWindowSize[0]*fSizeList[0];fYmin = fg_XYPlotWindowSize[1]*fSizeList[1];
    fXmax = fg_XYPlotWindowSize[2]*fSizeList[0];fYmax = fg_XYPlotWindowSize[3]*fSizeList[1];
    _VCollabAPI.xSetXYPlotPlacement(sPlotName,fXmin,fYmin,fXmax,fYmax);
    #_VCollabAPI.xSetXYPlotPlacement(sPlotName,0.1,0.1,0.8,0.6);
    sAxisX=xResult; # Use default X axis parameter (time/instance number or frequency
    sDerivedAxisX=""
    sAxisY=sResult; # Use default Y axis parameter (Current Result)
    sDerivedAxisY= sDerivedResult;
    sInstanceList= u""
    sPath1=u"Path1";
    _VCollabAPI.xSetXYPlotComplexComponents("Magnitude","Magnitude");
    _VCollabAPI.xSetXYPlotComplexEigenAngle(0.0);
    _VCollabAPI.xAddXYPlotPath(sPlotName, sPath1, lNodeList);
    _VCollabAPI.xSetXYPlotData(sPlotName, 1, sModel, sAxisX,sDerivedAxisX, sAxisY, sDerivedAxisY, sInstanceList, sPath1);
    #_VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xSetXYPlotPlacement(sPlotName,fXmin,fYmin,fXmax,fYmax);
    #sgNotify("Windows",f"{[fXmin,fYmin,fXmax,fYmax]}");
    bBackground = True; # Set XY Plot Background Color
    _VCollabAPI.xSetXYPlotBackground(sPlotName, bBackground, fg_XYBg_R,fg_XYBg_G,fg_XYBg_B);
    _VCollabAPI.xSetXYPlotGrid(sPlotName,10,5);
    #_VCollabAPI.xSetXYPlotCurves(sPlotName,False,False,True,False,False);
    _VCollabAPI.xSetXYPlotTitle(sPlotName,f"{sResult}-{sPlotName}",xResult,sResult);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return;
#-------------------------------------------
#Create Min-Max Plot
def CreateMinMaxXYPlot(sPlotName="Plot1",DelIndex=0):
    '''
    Creates Min Max XY plot
    Parameters:
        sPlotName: XY plot name(optional)
        DelIndex: Index of the curve to be deleted(optional)
    Returns:
        Boolean: True if creation of XY plot is successful
                 False if creation of XY plot is not successful
    '''
    if len(sPlotName) < 1: sPlotName = "Plot1";
    _VCollabAPI.xCreateXYPlot(sPlotName);
    fSizeList = _VCollabAPI.pxGetWindowSize();
    fXmin = fg_XYPlotWindowSize[0]*fSizeList[0];fYmin = fg_XYPlotWindowSize[1]*fSizeList[1];
    fXmax = fg_XYPlotWindowSize[2]*fSizeList[0];fYmax = fg_XYPlotWindowSize[3]*fSizeList[1];
    _VCollabAPI.xSetXYPlotPlacement(sPlotName,fXmin,fYmin,fXmax,fYmax);
    
    sAxisX=u""; # Use default X axis parameter (time/instance number or frequency
    sDerivedAxisX=u"";
    sAxisY=u""; # Use default X axis parameter (Current Result)
    sDerivedAxisY=u"";
    sInstanceList= u""
    sPath1=u"";
    _VCollabAPI.xSetXYPlotComplexComponents("","Magnitude");
    _VCollabAPI.xSetXYPlotComplexEigenAngle(0.0);
    bRtnFlag = _VCollabAPI.xSetXYPlotData(sPlotName, 2, sModel, sAxisX,sDerivedAxisX, sAxisY, sDerivedAxisY, sInstanceList, sPath1);
    if bRtnFlag == False:
        _VCollabAPI.xDeleteXYPlot(sPlotName);
        return False;
    bBackground = True; fR=1.0;fG=1.0;fB=0.8;
    _VCollabAPI.xSetXYPlotBackground(sPlotName, bBackground, fR,fG,fB);
    _VCollabAPI.xSetXYPlotGrid(sPlotName,10,10);
    if DelIndex >=0 and DelIndex <=1: # 0 = Min, 1 Max;
        _VCollabAPI.xDeleteXYPlotCurve(sPlotName,DelIndex); # Delete Max Curve
    _VCollabAPI.xRefreshDialogs();
    return True;
#==========================================================
#MINMAX_PLOT,<PlotName>,<iMinmax=>0=Max,1=Min,2=Both>
def CreateMinMaxPlot_CMD(nVals,sVals):
    '''
    Creates Min Max plot
    Parameters:
        sVals(List): sVals[0] - Min Max plot name
                     sVals[1] - Index of the curve to be deleted (0=Max,1=Min,2=Both) 
        nVals: Length of the sVals list
    Returns:
        None
    '''
    PlotName = 'MinMax Plot'
    if nVals > 0: PlotName = sVals[0];
    iMinmax = 0;
    if nVals > 1: iMinmax = GetInt(sVals[1],0);
    CreateMinMaxXYPlot(PlotName,iMinmax);
    return;
#-----------------------------------
#HS_XYPLOT,<PlotName>,<maxhs>
def CreateHS_XYPlot_CMD(nVals,sVals):
    '''
    Compute hotspots and create Transient XY plot
    Parameters:
        sVals(List): sVals[0] - XY plot name
                     sVals[1] - Number of top hotspots 
        nVals: Length of the sVals list
    Returns:
        None
    '''
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];sDerived = sCurResInfo[2];
    PlotName = sResult + 'Transient Plot';
    if nVals > 0: PlotName = sVals[0];
    maxhs = 1;
    if nVals > 1: maxhs = GetInt(sVals[1],1);
    if maxhs == 0: maxhs = 1;
    
    sIDList = _VCollabAPI.pxGetHotspotIDs(sModel, True);
    if len(sIDList) < 1:
        #-- Compute Hotspots
        fZoneRadius = GetZoneRadius(sModel,0.05);  
        if maxhs > 0:
            ComputeFewHotspots(maxhs,0,fZoneRadius);
        else:
            maxhs = -maxhs;
            ComputeFewHotspots(0,maxhs,fZoneRadius);
        sIDList = _VCollabAPI.pxGetHotspotIDs(sModel, True);
        if len(sIDList) < 1:
            sgNotify("Error","No hotspts for XY Plot",5);
            return;
    #----FRF Plot
    sIDString = u"";
    for nhs, id in enumerate(sIDList):
        if nhs > maxhs : break;
        sIDString = sIDString + str(id)+ ";"
    CreateTransientXYPlot(PlotName,sIDString,sResult,sDerived,"")
    return;
#-----------------------------------   
##FRFVIEW_VPS,<nhotspots>
def CreateComplexFRFView_CMD(nVals,sVals):
    '''
    Compute hotspots and create Transient XY plot (FRF plot)
    Parameters:
        sVals(List): sVals[1] - Number of top hotspots
        nVals: Length of the sVals list
    Returns:
        None
    '''
    sViewPathName = CurVPathName;
    igMaxHostSpots = 2;
    if nVals > 1:
        igMaxHostSpots = GetInt(sVals[1],3);
        if igMaxHostSpots < 1: igMaxHostSpots = 1;
    #-----------------------------------------------
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];sDerived = sCurResInfo[2];
    if IsComplexResult(sModel,sResult) == False:
        sgNotify("Error",f"{sResult} is not complex",5);
        return;
    InstFlag = 1; # Max Instance
    sInst = SelectInstance(sModel,sResult,sDerived,InstFlag);
    _VCollabAPI.xSetCAEResult(sModel,sResult,sInst,sDerived);
    _VCollabAPI.xSetCAEResultComplexType(sModel,2,0); # Complex Magnitude
    _VCollabAPI.xRefreshDialogs();
    #-- Set CAE Display Settings
    CAEFilterParts();
    _VCollabAPI.xSetCAEDeformMesh(sModel,True);
    _VCollabAPI.xSetCAEColorPlot(sModel,True);
    _VCollabAPI.xShowCAELegend(sModel,True);
    _VCollabAPI.xSetCAEReverseLegend(sModel,False);
    _VCollabAPI.xSetCAEDiscreteLegend(sModel,True);
    _VCollabAPI.xSetLabelAutoArrangeMode(4); # Compact Mode
    _VCollabAPI.xSetCAEProbeType(sModel,1) #1 => Derived
    #-- Compute Hotspots
    fZoneRadius = GetZoneRadius(sModel,0.05);     
    ComputeFewHotspots(igMaxHostSpots,0,fZoneRadius);
    #----FRF Plot
    sIDList = _VCollabAPI.pxGetHotspotIDs(sModel, True);
    sIDString = u"";
    for id in sIDList:
        sIDString = sIDString + str(id)+ ";"
    CreateTransientXYPlot("FRF-Plot",sIDString,sResult,sDerived)
    #CreateMinMaxXYPlot("FRF-Plot");
    AddVP_HF(sResult+'-FRFView',sViewPathName,-1);
    return;
#==================================
#iCompareMode,fMaxDistance
def CompareGeomCMD(nVals,sVals):
    '''
    Finds the difference between the two model's geometry (Merged models) and creates the viewpoints
    Parameters:
        sVals(List): sVals[1] - Sets compare mode. 0 – Same Parts, 1- Visible Parts, 2- All Parts; (Valid range 0 to 2) 
                     sVals[2] - Two models points are compared within this value. Geometry deviation out of this value is ignored
        nVals: Length of the sVals list
    Returns:
        None
    '''
    sModelList = _VCollabAPI.pxGetModels();
    if len(sModelList) < 2 :
        sgNotify("Error",u"Need Two Parts to Compare",5);
        return;
    sViewPathName = CurVPathName;
    
    iCompareMode = 1; #0=> same part, 1=> Visible pats, 2=> All parts
    if nVals > 1:
        if IsFloat(sVals[1]):
            iCompareMode = int(sVals[1]);
    fMaxDistance = GetZoneRadius(sModel,0.1);
    if nVals > 2:
        if IsFloat(sVals[2]):
            fMaxDistance = float(sVals[2]);
    #--------------------------------------
    bSetPartMax = False;bSaveViewpoint=True;
    _VCollabAPI.xCompareMesh(sModelList[0],sModelList[1],fMaxDistance,iCompareMode, bSaveViewpoint, bSetPartMax);
    #PrintMessage(u"Compare MOdel1 with MOdel2");
    _VCollabAPI.xCompareMesh(sModelList[1],sModelList[0],fMaxDistance,iCompareMode, bSaveViewpoint, bSetPartMax);
    #_VCollabAPI.xShowAssembly(u"",sModelList[0],True); #Show Both Model
    #PrintMessage(u"Compare MOdel2 with MOdel1");
    #-------Both
    _VCollabAPI.xSetCAEMultiPalette(True);_VCollabAPI.xSetCAECombinedPalette(False);
    SetModelDisplayMode(sModelList[0],0);SetModelDisplayMode(sModelList[1],1);
    _VCollabAPI.xSetCurCAEModelByName(sModelList[0]);_VCollabAPI.xShowCAELegend(sModelList[0],True);
    _VCollabAPI.xSetCurCAEModelByName(sModelList[1]);_VCollabAPI.xShowCAELegend(sModelList[1],True);
    _VCollabAPI.xSetCAEPaletteMode(3);_VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xAdd2DNotes("Compare A and B",0.5,0.1,True);
    _VCollabAPI.xRefreshDialogs();_VCollabAPI.xRefreshViewer();
    AddVP_HF(u"Compare A and B",sViewPathName,-1);
    #---
    _VCollabAPI.xSetCAEPaletteMode(0);_VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xSetCurCAEModelByName(sModelList[0])
    SetModelDisplayMode(sModelList[0],0);SetModelDisplayMode(sModelList[1],3);
    #SetModelColorPlot(sModelList[0],True);#SetModelColorPlot(sModelList[1],False);
    _VCollabAPI.xAdd2DNotes("Compare A with B",0.5,0.1,True);
    AddVP_HF(u"Compare A with B",sViewPathName,-1);
    #-----
    _VCollabAPI.xSetCAEPaletteMode(0);_VCollabAPI.xDeleteAllLabels();
    _VCollabAPI.xSetCurCAEModelByName(sModelList[1])
    SetModelDisplayMode(sModelList[0],3);SetModelDisplayMode(sModelList[1],0);
    #SetModelColorPlot(sModelList[0],True);#SetModelColorPlot(sModelList[1],False);
    _VCollabAPI.xAdd2DNotes("Compare B with A",0.5,0.1,True);
    AddVP_HF(u"Compare B with A",sViewPathName,-1);
    #-----
    return;
#=================================================================
#---SET_COMPARE_RES,ON=Y/N,BY=0-2,MODE=0-2,WITH=0-2,RADIUS=5.0,SHOWALL=Y,B2A=N
def SetCompareResCMD(nVals,sVals):
    '''
    Sets the Hotspots compare settings
    Parameters:
        sVals(List)(keyword args): ON=Y/N. Y to set hotspots compare option ON
                                   BY=0-2. Sets Comparison of Results mode. Valid Range 0-2
                                            0 – Same Result Name
                                            1 - Selected Results Order
                                            2 - Result’s Display Name
                                   MODE=0-7. Sets comparison mode. Valid range 0 to 7
                                                0 for Position: Nearest
                                                1 for Position: Min/Max
                                                2 for ID
                                                3 for ID: Distance
                                                4 for Hotspot: Min/Max
                                                5 for Hotspot: Nearest
                                                6 for Hotspot: Min/Max User range
                                                7 for Hotspot: Nearest User range                                 
                                   WITH=0-2. Sets comparison with Valid range 0 to 2
                                             0 for Same Part 
                                             1 for Current Visible Parts
                                             2 for All parts
                                   RADIUS(float)= Sets a radius to compare hotspots within a sphere.
                                   SHOWALL=Y/N. If set to Y, Sets additional label lines to compared node/element of other models.
                                                If set to N, Sets label line only to the model that generated the hotspot.
                                   B2A=Y/N. If set to Y, finds hotspots in all models and compares across all models.
                                            If set to N, find Hotspots only in the current model and those Hotspots are used to compare across all models.
        nVals: Length of the sVals list
    Returns:
        None
    '''
    #Defaults:
    bEnableCompare=True;bHotspotInAllModels=False;bShowAllConnections=True;
    iResBy=0;iCompareMode=1;iCompareWith=1;
    fDist=GetZoneRadius(sModel,0.05);
    #--
    for k in range(1,nVals):
        sCMD = sVals[k].upper().split('=');
        if len(sCMD) < 2: continue;
        if sCMD[0] == 'ON':
            if sCMD[1] == 'Y': bEnableCompare=True;
            continue;
        if sCMD[0] == 'SHOWALL':
            if sCMD[1] == 'Y': bShowAllConnections=True;
            continue;
        if sCMD[0] == 'BY':
            iVal = GetInt(sCMD[1],-1);
            if  iVal >=0 and iVal < 3: iResBy=iVal;
            continue;
        if sCMD[0] == 'MODE':
            iVal = GetInt(sCMD[1],-1);
            if  iVal >=0 and iVal < 3: iCompareMode=iVal;
            continue;
        if sCMD[0] == 'WITH':
            iVal = GetInt(sCMD[1],-1);
            if  iVal >=0 and iVal < 3: iCompareWith=iVal;
            continue;
        if sCMD[0] == 'RADIUS':
            fVal = GetFloat(sCMD[1],-1.0);
            if  fVal > 0.0 and fVal < 1E10: fDist = fVal;
            continue;
        if sCMD[0] == 'B2A':
            if sCMD[1] == 'Y': bHotspotInAllModels=True;
            continue;
            
    _VCollabAPI.xSetCAEHotSpotsCompareResultsMode(iResBy);
    _VCollabAPI.xSetCAEHotspotsCompareOptions(bEnableCompare,bHotspotInAllModels,iCompareMode,
        iCompareWith,fDist,bShowAllConnections);
    _VCollabAPI.xRefreshDialogs();
    return;
#-----------------------------------------
#--Arange Model Related Functions
#===============================================
#--------- Set Good Camera orientation based on bounding box
def SetBestViewCMD():
    '''
    Sets Good Camera orientation based on bounding box
    Parameters:
        None
    Returns:
        None
    '''
    sModel=u"";sPart=u""
    #Get Bounding Box for current displayed parts
    lfRect = _VCollabAPI.pxGetPartBounds(sModel,sPart);
    delX = lfRect[1]-lfRect[0];
    delY = lfRect[3]-lfRect[2];
    delZ = lfRect[5]-lfRect[4];
    ViewDir = [1,0,0];
    ViewUp = [0,1,0];
    #if width along X is smalest, set camera along X-direction
    if (delX <= delY and delX <= delZ) :
        ViewDir = [1,0,0];
        if (delY < delZ) : 
            ViewUp = [0,1,0]; # if width along Y is small set camera up along Y
            if (delY < 0.5*delZ):
                ViewDir = [1,0.5,0.5];
        else :
            ViewUp = [0,0,1]; # elseif width along Z is small set camera up along Z
            if (delZ < 0.5*delY):
                ViewDir = [1,0.5,0.5];
    #if width along Y is smalest, set camera along Y-direction
    elif (delY <= delX and delY <= delZ) :
        ViewDir = [0,1,0];
        if (delX < delZ) : 
            ViewUp = [1,0,0]; # if width along X is small set camera up along X
            if (delX < 0.5*delZ):
                ViewDir = [0.5,1,0.5];
        else :
            ViewUp = [0,0,1];
            if (delZ < 0.5*delX):
                ViewDir = [0.5,1,0.5];
    #if width along Z is smalest, set camera along Z-direction
    elif (delZ <= delX and delZ <= delY) :
        ViewDir = [0,0,1];
        if (delX < delY) : 
            ViewUp = [1,0,0]; # if width along X is small set camera up along X
            if (delX < 0.5*delY):
                ViewDir = [0.5,0.5,1];
        else :
            ViewUp = [0,1,0];
            if (delY < 0.5*delX):
                ViewDir = [0.5,0.5,1];
    #print("Best View: ",ViewDir,"\n",ViewUp)
    SetCameraView(ViewDir[0],ViewDir[1],ViewDir[2],ViewUp[0],ViewUp[1],ViewUp[2]);
    return;
#------------------------------------------------------------------
def ResetArrange():
    '''
    Resets the arranged models to the default position
    Parameters:
        None
    Returns:
        None
    '''
    fCameraList = _VCollabAPI.pxGetCamera();
    _VCollabAPI.xResetView();
    sModelList = _VCollabAPI.pxGetModels();
    for aModel in sModelList:
        assmlist = _VCollabAPI.xGetAssemblyList(aModel,u"",0);
        assmlist = assmlist.split(";");
        _VCollabAPI.xSetTransformationEx(aModel,assmlist[0],0.0,0.0,0.0,
              1.0,0.0,0.0,0.0,1.0,1.0,1.0,0);
    #--
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xResetView();
    _VCollabAPI.xSetCamera(fCameraList[0],fCameraList[1],fCameraList[2],
            fCameraList[3],fCameraList[4],fCameraList[5],
            fCameraList[6],fCameraList[7],fCameraList[8],
            fCameraList[9],fCameraList[10],fCameraList[11],fCameraList[12]);
    _VCollabAPI.xFitView();
    return;
#========================================================
def TransCamera(iRow=0):
    '''
    Arange models (merged models)
    Parameters:
        iRow: Number of rows to arrange models (optional)
    Returns:
        None     
    '''
    fCamVec = _VCollabAPI.pxGetCamera();
    fDirX = [fCamVec[6], fCamVec[7], fCamVec[8]]; fDirX = NormVec(fDirX);
    fDirZ = [fCamVec[3], fCamVec[4], fCamVec[5]]; fDirZ = NormVec(fDirZ);
    fDirY = CrossVec(fDirZ,fDirX); fDirY = NormVec(fDirY);
    #-----------
    #PopMessage([fDirX,fDirY]);
    sModelList = _VCollabAPI.pxGetModels();
    nModel = len(sModelList);
    if nModel < 2: return;
    nRow = int(math.sqrt(nModel));
    if nRow*nRow < nModel : nRow = nRow + 1;
    if iRow > 0:
        nRow=iRow;
    MaxR = 0.0;MaxSize=[0.0,0.0,0.0];
    fBoundList = [];
    for aModel in sModelList:
        fBoundVec = _VCollabAPI.pxGetSpericalBounds(aModel,u"");
        fBoundList.append(fBoundVec);
        if MaxR < fBoundVec[3] : MaxR = fBoundVec[3];
        fViewBound = _VCollabAPI.pxGetViewBoundBox();
        for i in range(0,3):
            if MaxSize[i] < fViewBound[i+3] : MaxSize[i] = fViewBound[i+3];
        
    #----------
    PopMessage(MaxSize);
    fBoundVec = fBoundList[0];
    Pos1 = [fBoundVec[0],fBoundVec[1],fBoundVec[2]];
    i=0;j=0;
    Pos = [0.0,0.0,0.0];
    for aModel in sModelList:
        fBoundVec = _VCollabAPI.pxGetSpericalBounds(aModel,u"");
        # Pos[0] = Pos1[0] + MaxR * i * 2 * fDirX[0] + MaxR * j * 2 * fDirY[0];
        # Pos[1] = Pos1[1] + MaxR * i * 2 * fDirX[1] + MaxR * j * 2 * fDirY[1];
        # Pos[2] = Pos1[2] + MaxR * i * 2 * fDirX[2] + MaxR * j * 2 * fDirY[2];
        Pos[0] = Pos1[0] + MaxSize[1] * i * 1.2 * fDirX[0] + MaxSize[0] * j * 1.2 * fDirY[0];
        Pos[1] = Pos1[1] + MaxSize[1] * i * 1.2 * fDirX[1] + MaxSize[0] * j * 1.2 * fDirY[1];
        Pos[2] = Pos1[2] + MaxSize[1] * i * 1.2 * fDirX[2] + MaxSize[0] * j * 1.2 * fDirY[2];
        j=j+1;
        if j == nRow :
            j=0; i=i+1;
        #PopMessage(fBoundVec,"Bounds=");
        assmlist = _VCollabAPI.xGetAssemblyList(aModel,u"",0);
        assmlist = assmlist.split(";");
        fTrans=[Pos[0]-fBoundVec[0],Pos[1]-fBoundVec[1],Pos[2]-fBoundVec[2]];
        #PopMessage(assmlist[0],"List",fTrans);
        _VCollabAPI.xSetTransformationEx(aModel,assmlist[0],fTrans[0],fTrans[1],fTrans[2],
              1.0,0.0,0.0,0.0,1.0,1.0,1.0,0);
    #--
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return;
#============================================
#ARRANGE_MODEL,<Nrow> ---------------------------------------------
def ArrangeModelsCMD(nVals,sVals):
    '''
    
    Parameters:
        sVals(List): sVals[1] -  Number of rows to arrange models
        nVals: Length of the sVals list
    Returns:
        None
    '''
    sModelList = _VCollabAPI.pxGetModels();
    nModel = len(sModelList);
    if nModel < 2:
        PrintMessage("ArrangeModelsCMD: Need at least two Models");
        return;
    ResetArrange();
    nRow = int(math.sqrt(nModel));
    if nRow*nRow < nModel : nRow = nRow + 1;
    if nVals > 1:
        iVal = GetInt(sVals[1],0);
        if iVal >= 0:
            nRow = iVal;
    if nRow <= 0: return;
    #------------------------------------------
    fCamVec = _VCollabAPI.pxGetCamera();
    fDirX = [fCamVec[6], fCamVec[7], fCamVec[8]]; fDirX = NormVec(fDirX);
    fDirZ = [fCamVec[3], fCamVec[4], fCamVec[5]]; fDirZ = NormVec(fDirZ);
    fDirY = CrossVec(fDirZ,fDirX); fDirY = NormVec(fDirY);
    #-----------
    #PopMessage([fDirX,fDirY]);
    MaxR = 0.0;MaxSize=[0.0,0.0,0.0];
    fBoundList = [];
    for aModel in sModelList:
        fBoundVec = _VCollabAPI.pxGetSpericalBounds(aModel,u"");
        fBoundList.append(fBoundVec);
        if MaxR < fBoundVec[3] : MaxR = fBoundVec[3];
        if hasattr(_VCollabAPI,'pxGetViewBoundBox'):
            fViewBound = _VCollabAPI.pxGetViewBoundBox();
        else:
            deltaR = fBoundVec[3]*1.8;
            fViewBound = [deltaR,deltaR,deltaR];
        for i in range(0,3):
            if MaxSize[i] < fViewBound[i+3] : MaxSize[i] = fViewBound[i+3];
    #-------------------
    fBoundVec = fBoundList[0];
    Pos1 = [fBoundVec[0],fBoundVec[1],fBoundVec[2]];
    i=0;j=0;
    Pos = [0.0,0.0,0.0];
    for aModel in sModelList:
        fBoundVec = _VCollabAPI.pxGetSpericalBounds(aModel,u"");
        Pos[0] = Pos1[0] + MaxSize[1] * i * 1.2 * fDirX[0] + MaxSize[0] * j * 1.2 * fDirY[0];
        Pos[1] = Pos1[1] + MaxSize[1] * i * 1.2 * fDirX[1] + MaxSize[0] * j * 1.2 * fDirY[1];
        Pos[2] = Pos1[2] + MaxSize[1] * i * 1.2 * fDirX[2] + MaxSize[0] * j * 1.2 * fDirY[2];
        j=j+1;
        if j == nRow :
            j=0; i=i+1;
        assmlist = _VCollabAPI.xGetAssemblyList(aModel,u"",0);
        assmlist = assmlist.split(";");
        fTrans=[Pos[0]-fBoundVec[0],Pos[1]-fBoundVec[1],Pos[2]-fBoundVec[2]];
        #PopMessage(assmlist[0],"List",fTrans);
        _VCollabAPI.xSetTransformationEx(aModel,assmlist[0],fTrans[0],fTrans[1],fTrans[2],
              1.0,0.0,0.0,0.0,1.0,1.0,1.0,0);
    #--
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xFitView();
    #_VCollabAPI.xRefreshViewer();
    return;
#-----------------------------------------------------
#=====================================================
TBL_MaxRows = 25;
TBL_MaxColumns = 15;
gTable_Font = u"Arial Narrow Bold";
gTable_FontSize = 14;
gTable_TextCol = [50,10,0];
gTable_HeaderCol = [200,200,210]
def Table_InsertRow(pTableId,row,sRowList,iMaxCol):
    '''
    Appends texts to table 
    Parameters:
        pTableId: ID of the table
        row: Row index
        sRowList(List): Text value to be set for the table field
        iMaxCol: Maximum number of columns
    Returns:
        None
    '''
    nCol = len(sRowList);
    if nCol < 1 : return;
    #PrintMessage(str(nCol)+str(sRowList));
    if nCol < iMaxCol :
        for col in range(0,nCol):
            _VCollabAPI.xSet2DTableText(pTableId,row,col,"  "+str(sRowList[col])+"  ");
            _VCollabAPI.xSet2DTableFont(pTableId,row,col,gTable_Font);
            _VCollabAPI.xSet2DTableFontSize(pTableId,row,col,gTable_FontSize);
            _VCollabAPI.xSet2DTableTextColor(pTableId,row,col,gTable_TextCol[0],gTable_TextCol[1],gTable_TextCol[2]);
        return;
        
    #Too many col
    col = 0;
    _VCollabAPI.xSet2DTableText(pTableId,row,col,str(sRowList));
    _VCollabAPI.xSet2DTableFont(pTableId,row,col,gTable_Font);
    _VCollabAPI.xSet2DTableFontSize(pTableId,row,col,gTable_FontSize);
    _VCollabAPI.xSet2DTableTextColor(pTableId,row,col,gTable_TextCol[0],gTable_TextCol[1],gTable_TextCol[2]);
    return;
#==================================================================================
def DisplayHotspotSummaryTable(xPos,yPos,sHeaderRow=""):
    '''
    Creates a hotspots summary table
    Parameters:
        xPos, yPos: X, Y position in screen space of the table
        sHeaderRow: Header text for the table field (optional)
    Returns:
        Boolean: True if creation of summary table was successful
                 False if no hotspots are found
    '''
    bIsElemental = False;
    #PopMessage([gTable_Font,gTable_FontSize,gTable_TextCol],'CutFont');
    iMaxCol = TBL_MaxColumns-2;
    p2DTable = _VCollabAPI.xAdd2DTable(0.1,0.3,True);
    _VCollabAPI.xSet2DTablePosition(p2DTable,xPos,yPos,True);
    sIDList = _VCollabAPI.pxGetAllProbeTableIDs(sModel);
    if len(sIDList) < 1:
        PrintMessage("Hotspots not found");
        return False;
    #PopMessage(sIDList);
    sPLInfoList = "";
    sGap =" , ";
    hTabList = [];
    #sTimeResult = u"";
    row = 0;
    sTabResVals = _VCollabAPI.pxGetProbeTableResultValues(sModel,sIDList[0]);
    NCol = len(sTabResVals);
    bIsPos = False;
    if (iMaxCol-NCol) < 1 or bIsElemental : bIsPos = False; iMaxCol = iMaxCol+1;
    bRankID = _VCollabAPI.xGetCAEProbeRankHeader();
    idName = 'NodeId'; 
    if bIsElemental: idName = 'ElmId'; 
    if bRankID : idName = 'Rank';
    for id in sIDList:
        sTabResVals = _VCollabAPI.pxGetProbeTableResultValues(sModel,id);
        if len(sTabResVals) != NCol : continue;
        row=row+1;
        sRowList = [];
        # Node  or Elm ID
        sNodeId = _VCollabAPI.xGetProbeTableNodeID(id);
        sElmId = sNodeId;
        if bIsElemental: sElmId = _VCollabAPI.xGetProbeTableElementID(id);
        iRank = _VCollabAPI.xGetProbeTableRank(id);
        #sRowList.append(str(row));
        if bRankID:
            sRowList.append(str(iRank));
        else:
            sRowList.append(str(sElmId));
        # Node Position
        pos3d = _VCollabAPI.pxGetNodeLocation(sModel,u"",sNodeId);
        sPos3dStr=Float2String(pos3d[0])+sGap+Float2String(pos3d[1])+sGap+Float2String(pos3d[2]);
        sPLInfoList = sPLInfoList + str(sNodeId) +" ("+ sPos3dStr +")";
        if bIsPos == True:
            sRowList.append(sPos3dStr);
        # Result Values
        sTabResVals = _VCollabAPI.pxGetProbeTableResultValues(sModel,id);
        resValStr = "(";
        ncol = 0;
        for resval in sTabResVals:
            ncol = ncol+1;
            resValStr = resValStr+ " " + Float2String(resval);
            if len(sTabResVals) == NCol :
                if ncol < iMaxCol : sRowList.append(Float2String(resval));
        resValStr = resValStr+ ")"
        sPLInfoList = sPLInfoList + " " + resValStr;
        #sRowList.append(Float2String(sTabResVals[0])); # First Result
        #sRowList.append(resValStr);
        sTabResults = _VCollabAPI.pxGetProbeTableResults(id);
        sPLInfoList = sPLInfoList + " " + str(sTabResults) +"\n";
        hTabList.append(KeyValueObject(float(sTabResVals[0]),sRowList));
    PrintMessage(sPLInfoList);
    #bAscending = _VCollabAPI.xGetCAEProbeTemplateRankOrder();
    bRevFlag = _VCollabAPI.xGetCAEReverseLegend(sModel);
    hTabList_Sorted = sorted(hTabList,reverse=not bRevFlag);
    sRowList = sHeaderRow; bRes = True;
    if len(sRowList) < 1:
        sRowList = [idName];
        if bRes == False:
            sRowList.append("    Value    ");
        else:
            for j in range(0,NCol):
                sName = sTabResults[j].split(':')[0];
                sName = _VCollabAPI.xGetCAEResultDisplayName(sModel,sName);
                sRowList.append(sName);
    # PopMessage(sRowList);
    # sRowList = _VCollabAPI.pxGetProbeTableResults(id);
    # sRowList = [" ID  ", "Pos (X,Y,Z)","    Value    "];
    # if bIsPos == False :
        # sRowList = [" Rank  ", " F_FKM "];
    row = 0;
    Table_InsertRow(p2DTable,row,sRowList,TBL_MaxColumns);
    _VCollabAPI.xSet2DTableBackground(p2DTable,row,-1,gTable_HeaderCol[0],gTable_HeaderCol[1],gTable_HeaderCol[2]);
    row = 1;
    NCol = NCol + 1;
    if bIsElemental == False : NCol = NCol + 1;
    for hTab in hTabList_Sorted:
        sRowList = hTab.Value;
        #if len(sRowList) == NCol:
        PrintMessage(sRowList);
        Table_InsertRow(p2DTable,row,sRowList,TBL_MaxColumns);
        row = row+1;
        if row > TBL_MaxRows : break;
    Table_InsertRow(p2DTable,row,sRowList,TBL_MaxColumns);
    _VCollabAPI.xDelete2DTableRow(p2DTable,row);
    return True;
#=====================================================
def DisplayHS2DTableCMD(nVals=0,sVals=[]):
    '''
    Creates a hotspots summary table
    Parameters:
        sVals(List): sVals[0:2] - X, Y position in screen space of the table
                     sVals[2:] - Header text for the table field 
        nVals: Length of the sVals list
    Returns:
        None
    '''
    xPos=0.1;yPos=0.85;
    if nVals > 1: 
        xPos = GetFloat(sVals[0],0.1);
        yPos = GetFloat(sVals[1],0.85);
    sHeader = "";
    if nVals > 2: sHeader = sVals[2:];
    DisplayHotspotSummaryTable(xPos,yPos,sHeader);
    return;
#=========================================
def MySplit(sLine):
    '''
    Splits a string for comma, round and square brackets 
    Parameters:
        sLine: String for splitting
    Returns:
        sList(List): Split string    
    '''
    #PopMessage(sLine,'SLine');
    sList = [];sbuf="";bSkip=False;iCount=0;
    for ch in sLine:
        if bSkip == False and ch == ',':
            sList.append(sbuf);
            sbuf="";continue;
        elif ch == '[' or ch == '(':
            bSkip = True;iCount = iCount+1;
        elif ch == ']' or ch == ')':
            iCount = iCount - 1;
            if iCount == 0:
                bSkip = False; 
        sbuf = sbuf+ch;
    if len(sbuf) > 0: sList.append(sbuf);
    #PopMessage(sList);
    return sList;  
#---------------------------------
def SetGlobalVariableCMD(nVals,sVals):
    '''
    Set global variables
    Parameters:
        sVals(List): String for global variables
        nVals: Length of the sVals list
    Returns:
        None
    '''
    if nVals > 1:
        sLine =sVals[0];
        for i in range(1,nVals):
            sLine = sLine+','+sVals[i];
        sVals = MySplit(sLine);
    for aVal in sVals:
        try:
            sCMD = aVal.split('=');
            if len(sCMD) < 2: continue;
            if sCMD[0] in globals():
                exec(u"global "+sCMD[0]+';'+aVal);
                #PopMessage(eval(sCMD[0]),aVal);
            else:
                PopMessage(aVal,"Variable not found");
            continue;
        #except ValueError:
        except SyntaxError as err:
            # PopMessage('Syntax error', 
                    # [err.filename, err.lineno, err.offset, err.text]);
            PopMessage(f'Syntax error{err.text}',aVal);
            continue;
    return;
#======================================
#Function to export image, 
#Note: Window is resized to image size
#-- Note: Window is resized to image size
def ExportImageCMD(sImageFileName,iwidth=None,iheight=None):
    '''
    Takes screenshot of the current view and saves it as an image file
    Parameters:
        sImageFileName: The local file path of image file to be saved
        iwidth, iheight: Width and height of the new window (optional)
    Returns:
    Boolean: True if Image Generation was successful
             False if Image Generation Failed
    '''
    if iwidth == None or iheight == None: # No Resize
        bRtnFlag = _VCollabAPI.xGenerateImage(sImageFileName);
        if bRtnFlag == False :
            sgNotify("Error",u"Image Generation Failed ",5);
        else: 
            sgNotify("File Saved",u"Image File: {sImageFileName} ");
        return bRtnFlag;
    iWinSize = _VCollabAPI.pxGetWindowSize(); # Cuurent window size
    _VCollabAPI.xSetWindowSize(iwidth,iheight); # set window to image size
    bRtnFlag = _VCollabAPI.xGenerateImage(sImageFileName);
    if bRtnFlag == False :
        sgNotify("Error",u"Image Generation Failed ");
    else:
        sgNotify("File Saved",u"Image File: {sImageFileName} ");
    _VCollabAPI.xSetWindowSize(iWinSize[0],iWinSize[1]); # Reset window size
    return bRtnFlag;
#=====================================================================
"""
bool xCreatePivotDeformationResult(sModel, sNewResult, iNode1, iNode2,  iNode3,iInputType,iCoordSystem);
input type:
0 - origin, x axis and xyplane
2 - 3 point circular
iCoordSystem:
0-cartesian
1-Circular
2-spherical
"""
#PIVOT_RESULT,NewResultName,N1,N2,N3,iOrigin=2,iCoord=0
def PivotResultCMD(sVals):
    '''
    Create pivot result
    Parameters:
        sVals(List): sVals[1] - New result name
                     sVals[2:5] - Three Node ids for selecting a plane
                     sVals[5] - Input type 0 – Origin, x-axis, xy-plane
                                           2 – Three Points on Circle 

                     sVals[6] - Co ordinate system
                                0 – Cartesian Coordinate System
                                1 – Cylindrical Coordinate System
                                2 – Spherical Coordinate System
    Returns:
        Boolean: True if creation of the pivot result was successful
                 False if creation of the pivot result was not successful
    '''
    if len(sVals) < 5: return False;
    CurrResult = _VCollabAPI.pxGetCAECurrentResult(sModel); 
    #-- New result Name
    if len(sVals[1]) > 0: NewRes = sVals[1];
    else: NewRes = CurrResult[0]+" Pivot Result";
    
    #-- Get 3 node numbers
    if IsInt(sVals[2])==False or IsInt(sVals[3])==False or IsInt(sVals[4])==False: 
        PrintMessage(f" PivotResult ID Error: {sVals}"); return False;
    N1 = int(sVals[2]);N2 = int(sVals[3]);N3 = int(sVals[4]);
    
    iOrigin=2;iCoord=0;
    if len(sVals) > 5: iOrigin = GetInt(sVals[5],2);
    if len(sVals) > 6: iCoord = GetInt(sVals[6],0);
    if iOrigin != 0 or iOrigin != 2 : iOrigin=2;
    if iCoord < 0 or iCoord > 2 : iCoord=0;
    #--- Create pivote result 
    pFlag = _VCollabAPI.xCreatePivotDeformationResult(sModel,NewRes,N1,N2,N3,iOrigin,iCoord);
    if pFlag and iCoord ==0 : _VCollabAPI.xSetAsCAEDeformationResult(sModel,NewRes);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    return pFlag;
#=====================================================
def Set_sModel():
    '''
    Gets the current model name
    Parameters:
        None
    Returns:
         Cax model name of the current model
         Empty string if no model is available
    '''
    global sModel; sModel = "";
    sModel = _VCollabAPI.xGetCurCAEModelName();
    if len(sModel) < 1:
        sModelList = _VCollabAPI.pxGetModels();
        if len(sModelList) < 1:
            return ""; #Check Added on 13 Nov 2020
        sModel = sModelList[0];
    return sModel;
#-----------------------------------------------
# 0 => No Models
# 1 => Single CAD Model
# 11 => Two CAD Models
# 2 => Single CAE Generic Model
# 12 => Multiple CAE Generic Models
# 3 => Single CAE Modal Model
# 13 => Multiple CAE Modal Models
# 22 => Multiple CAD and CAE Model
#-----------------------------------
def GetModelType():
    '''
    Return the Cax model type
    Parameters:
        None
    Returns:
         0 - If no cax model was found
         11 - If cax was created from multiple CAD models
         1 - If cax was created from single CAD model
         3 - If cax was created from single CAE modal model
         2 - If cax was created from single generic CAE model
         22 - If cax was created from CAE and CAD models
         13 - If cax was created from multiple modal CAE models
         12 - If cax was created from multiple CAE models
    '''
    global sModel; sModel = "";
    sModelList = _VCollabAPI.pxGetModels();
    nModels = len(sModelList);
    if nModels < 1: # No cax models found
        sgNotify("Model Type: No cax models found");
        return 0;
    if _VCollabAPI.xHasCAEResult() == False :
        sModel = sModelList[0];
        if nModels > 1:
            sgNotify(f"Model Type 11:  {nModels} CAD models");
            return 11;
        else:
            sgNotify("Model Type 1:  Single CAD model");
            return 1;
    #-- Has CAE Models --
    if nModels == 1:
        sModel = _VCollabAPI.xGetCurCAEModelName();
        if IsModalResult():
            sgNotify("Model Type 3:  Single CAE Modal model");
            return 3;
        sgNotify("Model Type 2:  Single Generic CAE model");
        return 2;
    #------- Has multiple Models -------------------
    sCAEModelList = _VCollabAPI.pxGetCAEModels();
    nCAEModels = len(sCAEModelList);
    sModel = _VCollabAPI.xGetCurCAEModelName();
    if nCAEModels != nModels:
        sgNotify("Model Type 22:  Both CAD and CAE models");
        return 22;
    #-- Multiple CAE Models
    if IsModalResult():
        sgNotify("Model Type 13:  Multiple CAE Modal models");
        return 13;
    sgNotify("Model Type:  Multiple CAE models");
    return 12;
#-----------------------------------------------
def ReadCommandFile(sCommandFile,IsList=True):
    '''
    Extract the VCutil command from a command file
    Parameters:
        sCommandFile: Command file path
    Returns:
        VPList(List): Extracted command line     
    '''
    VPList = [];
    with open(sCommandFile,encoding='utf-8',errors='ignore') as fp:
        for aLine in fp:
            cpos=aLine.find('#');
            if cpos > 1: aLine = aLine[:cpos];
            sLine = aLine.strip()
            if len(sLine) > 0 and sLine[0] != '#':
                if IsList: 
                    VPList.append([sLine]);
                else:
                    VPList.append(sLine);
    #-- file end
    return VPList;
#--------------------------------------------------
def SetCurFolderCMD(sVal):
    '''
    Gets the folder path for Cax file, Python file and Temp 
    Parameters:
        sVals: CAX/PY/TEMP (CAX for Cax model folder path; PY for python folder path; TEMP for temp folder path)
    Returns:
        sDefFolder: Folder path
    '''
    global sDefFolder;
    #--CAX
    if sVal.upper() == 'CAX':
        if len(sModel) > 0:
            sCaxPath = _VCollabAPI.xGetFileName(sModel);
            sDefFolder = os.path.dirname(sCaxPath);
            return sDefFolder;
    #--PY
    if sVal.upper() == 'PY':
        sDefFolder = sPyFolder;
        return sDefFolder;
    #-- TEMP
    if sVal.upper() == 'TEMP':
        sDefFolder = sTmpFilePath;
        return sDefFolder;
    #-- full path 
    if IsFileExists(sVal):
        sDefFolder = sVal;
    return sDefFolder;
#-------------------------------------------------------    
# LEGEND_POS,X position,Y position,bRelative,iOrientation (0-2/N)
def MoveLegendCMD(nVals,sVals):
    '''
    Sets CAE legend position
    Parameters:
        sVals(List): sVals[1] - Normalized X position of Legend position (Left)
                     sVals[2] - Normalized Y position of Legend position (Bottom)
                     sVals[3] - Y/N. Y to set the legend position based on current legend location
                     sVals[4] - Orientation of Legend.0 - Left, 1 - Right, 2 - Top, 3 - Bottom
        nVals: Length of the sVals list
    Returns:
        None
    '''
    if nVals < 3: #Reset
        _VCollabAPI.xSetCAELegendPosition(sModel,-100,-100,0);
        return;
    lgPos = _VCollabAPI.pxGetCAELegendPosition(sModel);
    if len(lgPos) < 3: 
        return;
    xpos = GetFloat(sVals[1],lgPos[0]);
    ypos = GetFloat(sVals[2],lgPos[1]);
    iLgOri = int(lgPos[2]);
    bRelative = False;
    if nVals > 3: 
        if sVals[3].upper() == 'Y': bRelative=True;
    io = -1
    if nVals > 4: io = GetInt(sVals[4],-1);
    if io >=0 and io < 4 and iLgOri != io: # Change in Orientation?
        iLgOri = io;
        _VCollabAPI.xSetCAELegendPosition(sModel,-100,-100,iLgOri);
            
    if bRelative :
        xp = lgPos[0] + xpos; yp = lgPos[1]+ypos;
        _VCollabAPI.xSetCAELegendPosition(sModel,xp,yp,iLgOri);
        return;
    if hasattr(_VCollabAPI,'xIsSectionON') == False:
        if ypos < 0.2: ypos = ypos + 0.3;
    _VCollabAPI.xSetCAELegendPosition(sModel,xpos,ypos,iLgOri);
    return;
#==============================================================
#============================================================
class ProgressBar:
    '''Shows the progress bar for creating the viewpoint'''
    def __init__(self,MaxVal=100,xPos=600,yPos=400,Message="Progress bar"):
        '''        
        Parameters:
            MaxVal: Maximum value (optional)
            xPos: X position in the screen (optional)
            yPos: Y position in the screen (optional)
            Message: Title (optional)
        Returns:
            None                 
        '''
        layout = [[sg.ProgressBar(max_value=MaxVal, orientation='h',
            size=(20, 20), key='progress')],[sg.Cancel()]]
        self.window = sg.Window('Completion', layout, location=(xPos,yPos),keep_on_top=True,finalize=True)
        self.progress_bar = self.window['progress'];
        #self.window.Hide();
    def Close(self):
        '''
        Closes the progress bar
        Parameters:
            None
        Returns:
             None
        '''
        if self.window == None: return;
        self.window.close();del self.window;
        self.window = None;
    def Hide(self):
        '''
        Hides the progress bar
        Parameters:
            None
        Returns:
             None
        '''
        if self.window == None: return;
        self.window.Hide();
    def Show(self):
        '''
        Shows the progress bar
        Parameters:
            None
        Returns:
            None
        '''
        if self.window == None: return;
        self.window.UnHide();
        self.window.BringToFront()
    def Update(self,count,max_count=None):
        '''
        Updates the progress bar
        Parameters:
            count(int): sets the current value
            max_count(int): changes the max value(optional)
        Returns:
            None
        '''
        if self.window == None: return; 
        self.window.BringToFront()
        self.progress_bar.update_bar(count,max_count);
        event, values = self.window.read(timeout=1)
        if event in (None,'Quit','Cancel'):
            self.Close();
    def __del__(self):
        '''
        Deletes the progress bar
        Parameters:
            None
        Returns:
            None      
        '''
        self.Close();
#====================================================================================
#RUN_SCRIPT,ScriptFile,bReUse(Y/N),FunctionName,Arguments..
def RunScriptCMD(sVals):
    '''
    Run python script
    Parameters:
        sVals(List): sVals[0] - Script file path
                     sVals[1] - Y/N. Set Y to reuse module
                     sVals[2] - Funtion name to execute
                     sVals[3:] - Arguments for the function 
    Returns:
        Boolean: True if the execution of the script was successful. False if the execution was not successful
        None: If the file or file path is not valid
    '''
    # if len(sVals) < 3:
    try:
        sFileName = SearchValidFile(sVals[0]);
        if sFileName == None: 
            sgNotify("Error",f"{sVals[0]} Not found, RUN_SCRIPT Failed",10);
            return;
        sFolder = os.path.dirname(sFileName);
        #-------------
        sName, ext = os.path.splitext(os.path.basename(sFileName))
        if(ext != '.py' and ext != '.pyc'): 
            sgNotify("Error",f"{sVals[0]} Not a python script?, RUN_SCRIPT Failed",10);
            return;
        #---
        bReUse = False;
        if len(sVals) > 1 and sVals[1].upper() == 'Y':
            bReUse = True;
        PrintMessage(f"-- RUN_SCRIPT {sFileName} ---");
        sys.path.insert(0, sFolder);
        if sName in sys.modules: # Reload module
            if bReUse:
                ModuleA = sys.modules[sName];
                PrintMessage(f"Module {sName} reused");
            else:
                importlib.invalidate_caches()
                ModuleA = importlib.reload(sys.modules[sName]);
                PrintMessage(f"Module {sName} reloaded");
        else:
            ModuleA = importlib.import_module(sName);
            PrintMessage(f"Module {sName} loaded");
        importlib.invalidate_caches()
        
        sys.path.remove(sFolder);
        #---------------------------------
        if len(sVals) > 2:
            fName = sVals[2];
            if len(sVals) > 3: 
                #fArgs=','.join(sVals[3:]);
                exec(f"ModuleA.{fName}({sVals[3:]})");
            else:
                exec(f"ModuleA.{fName}()");
        return True;
    except:
        sTB = traceback.format_exc();
        PopMessage(u"Error Trace!!! " + sTB)
    #-
    return False;
#==============================================================
#--Search Step name
def SearchInstInAttr(sStep,sResult,sInstanceList = None,AttrList=['Label','Label1']):
    '''
    Returns the instance name for a given setp name
    Parameters:
        sStep: Step name of the instance
        sResult: Result name
        sInstanceList(List): Instances name list (optional)
        AttrList(List): Search attribute keys (optional)
    Returns:
        aInst: Instance name if the search was successful
        None: If the instance is not found        
    '''
    if sInstanceList == None:
        sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    #
    for aInst in sInstanceList:                           
        caeatt = _VCollabAPI.pxGetCAEAttributeKeyList(sModel,sResult,aInst);
        for key in AttrList:
            if key in caeatt:
                sValue = _VCollabAPI.xGetCAEAttributeValue(sModel,sResult,aInst,key);
                if IsSubString(sValue,'*'+sStep+'*',True): return aInst;
        #--
    #--
    return None;
#----------------------------------------------
def SearchInstance(sInst,sResult,sInstanceList = None,bNum = True):
    '''
    Searches the instance name or index in the instances list
    Parameters:
        sInst: Instance index or name to search
        sResult: Result name
        sInstanceList(List): Instance list(optional)
        bNum(Boolean): Set to True if instance index is give (optional)
    Returns:
        None: If the instance name not found
        Instance name: Name of the instance 
    '''
    if sInstanceList == None:
        sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    nInst = len(sInstanceList);
    if nInst < 1:
        PrintMessage(f"SearchInstance Error, No Instances for {sResult}");
        return None;
    iInst = None;
    if bNum :
        if type(sInst) == 'int': 
            iInst = sInst-1;
        elif IsFloat(sInst):
            iInst = int(sInst)-1;
        else:
            aInst = EvalInstantce(nInst,sInst);
            if aInst != None : iInst = aInst - 1;
        #------
        if iInst != None:
            if iInst >= 0 and iInst < nInst : 
                return sInstanceList[iInst];
            else:
                return(sInstanceList[-1]);
    #----
    sLastInst = None;
    for aInst in sInstanceList:
        if sInst == aInst: return sInst;
        if IsSubString(aInst,'*'+sInst+'*',True):
            sLastInst = aInst; 
    #--
    if sLastInst != None : return sLastInst;
    #-- Search for Step Name
    sCurInst =  SearchInstInAttr(sInst,sResult,sInstanceList);
    if sCurInst == None:
        PrintMessage(f"{sInst} not found in {sResult}");
    return sCurInst;
#---------------------------------
def Selectinstancename(gIns,sResult,sInstanceList):
    '''
    Searches a instance name or index
    Parameters:
        gIns: Instance name or index 
        sResult: Result name
        sInstanceList(List): Instance list(optional)
        bNum(Boolean): Set to True if instance index is give (optional)
    Returns:
        Instance name
    '''
    nInst = len(sInstanceList);
    if nInst < 1:
        sCurInst = "";
    else:
        sCurInst = sInstanceList[-1];
    iInst = None;
    if IsFloat(gIns):
        iInst = int(gIns)-1;
        
    else: 
        
        for k in range(nInst):
            if IsSubString(sInstanceList[k],'*'+gIns+'*',True):
                iInst = k; 
                
                break;
            else:                           
                caeatt = _VCollabAPI.pxGetCAEAttributeKeyList(sModel, sResult, sInstanceList[k]);
                if "Label" in caeatt:
                    sValue = _VCollabAPI.xGetCAEAttributeValue(sModel,sResult,sInstanceList[k],"Label");
                    if IsSubString(sValue,'*'+gIns+'*',True):
                        iInst = k;
                        break;
    #-------------
    if iInst != None and iInst >= 0 and iInst < nInst:
        sCurInst = sInstanceList[iInst];
    return sCurInst;
#===========================================================
#NEW_INSTANCE,result,inst1,inst2,expression,sNewInst
def CreateInstanceCMD(sVals):
    '''
    Creates a new instance
    Parameters:
        sVals(List): sVals[0] - Result name
                     sVals[1] - Instance1 name or index
                     sVals[2] - Instance1 name or index
                     sVals[3] - Expression for creating the new instance
                     sVals[4] - New instance name
    Returns:
        None
    '''
    _VCollabAPI.xLockRefresh(False);
    sResult = '';
    sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
    if len(sResultList) < 1: PrintMessage("No results found to create instance"); return;
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    if len(sVals[0]) > 1:
        sRefName = sVals[0]
        sResult = SelectResult(sModel,sRefName,False);
        if sResult == None:
            sResult = sCurResInfo[0];
    else: sResult = sCurResInfo[0];
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    if len(sVals) > 1:
        if len(sVals[1]) > 1:
            inst1 = SearchInstance(sVals[1],sResult,sInstanceList)
            
        else: inst1 = sCurResInfo[1];
        if len(sVals) > 2 and len(sVals[2]) > 1:
            inst2 = SearchInstance(sVals[2],sResult,sInstanceList)
            
        else: inst2 = sCurResInfo[1];
    else: inst1 = sCurResInfo[1]; inst2 = sCurResInfo[1];
    
    if len(sVals) > 3 and len(sVals[3]) > 1:
        expression = sVals[3];
    else: expression = "a";
    
    if len(sVals) > 4 and len(sVals[4]) > 1:
        sNewInst = sVals[4];
    else: sNewInst = f"L{len(sInstanceList)}M1"; #'CreatedInst'
    if sNewInst in sInstanceList:
        PrintMessage(f"{sNewInst} Already Present for {sResult}");
        return;
    _VCollabAPI.xCreateResultInstance(sModel, sResult, inst1, inst2, expression, sNewInst,-1);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xRefreshViewer();
    _VCollabAPI.xCAERefresh(sModel);
    return;
#===================================================================
def DeleteInstanceCMD(sVals):
    '''
    Deletes the selected instance
    Parameters:
        sVals(List): Instances name or index 
    Returns:
        None
    '''
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
    sResult = sCurResInfo[0];
    sInstanceList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult);
    for val in sVals:
        inst = SearchInstance(val,sResult,sInstanceList)
        _VCollabAPI.xCAEDeleteInstance(sModel,sResult,inst);
    return;
#------------------------------------------------------------
def CreateComplexDerivedeResult(sModel,sResult,sNewHRMises="Stress_HRMises",bHarmonic=False,sDerived='Von Mises Stress',bDelFlag=True):
    '''
    Creates new complex derived result
    Parameters:
        sModel: Cax model name
        sResult: Result name
        sNewHRMises: New result name(optional)
        bHarmonic(Boolean): Set to True for harmonic result(optional)
        sDerived: Derived result name(optional)
        bDelFlag(Boolean): Set to True to delete the selected result(optional)
    Returns:
         True
    '''
    if bHarmonic : # Max harmonic VonMises Result
        #-- Create harmonic Tensor Result for Max VonMises
        _VCollabAPI.xCreateStressHarmonicResult(sModel,sResult)
        if bDelFlag:  _VCollabAPI.xCAEDeleteResult(sModel,sResult);
        _VCollabAPI.xRefreshDialogs()
        sResultList = _VCollabAPI.pxGetCAEResultsList(sModel)
        sCurHRMises = sResultList[-1];
        #-- Create VonMises Derived Result
        sDerived = _VCollabAPI.xCAEGetDefaultDerivedResult(sModel,sCurHRMises)
        SetCurResult(sModel,sCurHRMises,sDerived);
        _VCollabAPI.xCreateResultDerived(sModel,sCurHRMises,sDerived,u"",sNewHRMises,0,0);
        _VCollabAPI.xCAEDeleteResult(sModel,sCurHRMises);
        _VCollabAPI.xRefreshDialogs()
        return True;
    #-- Create Complex Derived Result
    SetCurResult(sModel,sResult,sDerived);
    _VCollabAPI.xSetCAEResultComplexType(sModel,2,0); # Complex Magnitude
    _VCollabAPI.xCreateResultDerived(sModel,sResult,sDerived,u"",sNewHRMises,2,0);
    if bDelFlag : _VCollabAPI.xCAEDeleteResult(sModel,sResult);
    _VCollabAPI.xRefreshDialogs()
    return True;
#---------------------------------
def CreateComplexStressResult(CurModel,sNewResName,bHarmonic=False,sDerived='Von Mises Stress',bDeleteOriginal=True):
    '''
    Creates complex stress result
    Parameters:
        CurModel: Cax model name
        sNewResName: New result name
        bHarmonic(Boolean): Set to True for harmonic result(optional)
        sDerived: Derived result name (optional)
        bDeleteOriginal: Delete the selected result(optional)
    Returns:
        Boolean: True if the new result creation was successful
                 False for invalid result
    '''
    global sModel;
    sModel = CurModel;
    #----Get all Stress Results #
    sResult = "";
    sResultList = _VCollabAPI.pxGetCAEResultsList(sModel);
    sRefTopResult = None;sRefBotResult = None;sRefSolidResult = None;nStressRes = 0;
    for sResult in sResultList:
        iType = _VCollabAPI.xGetCAEResultType(sModel,sResult);
        if iType != 3 and iType != 7 : continue; #--Not a tensor Result
        if _VCollabAPI.xGetCAEAnalysisType(sModel,sResult) != 3 : continue; # Not a complex result?
        if IsSubString(sResult,'stress*top*)',True): 
            sRefTopResult = sResult; nStressRes = nStressRes+1;
        if IsSubString(sResult,'stress*bot*)',True): 
            sRefBotResult = sResult;nStressRes = nStressRes+1;
        if sResult.upper() == "STRESS": 
            sRefSolidResult = sResult; nStressRes = 10; break;
    if nStressRes == 0: 
        PrintErrorMessage("Complex Stress results not found"); return False;
    
    if sRefSolidResult != None:
        return CreateComplexDerivedeResult(sModel,sRefSolidResult,sNewResName,bHarmonic,sDerived,bDeleteOriginal);
        
    if sRefTopResult == None and sRefBotResult == None:
        PrintErrorMessage("Top&Bot Complex Stress results not found"); return False;
        
    #--Compute Top & Bottom Stress
    bFlag = CreateComplexDerivedeResult(sModel,sRefTopResult,sNewResName+'_Top',bHarmonic,sDerived,bDeleteOriginal);
    if bFlag == False:
        PrintErrorMessage(f"CreateComplexStressResult faild for {sRefTopResult} "); return False;
    bFlag = CreateComplexDerivedeResult(sModel,sRefBotResult,sNewResName+'_Bot',bHarmonic,sDerived,bDeleteOriginal);
    if bFlag == False:
        PrintErrorMessage(f"CreateComplexStressResult faild for {sRefBotResult} "); return False;
    #--Compute Max of Top and Bottom Stress
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xCreateCAENewResult(sModel,sNewResName+'_Top',sNewResName+'_Bot',"Max(A,B)",sNewResName);
    _VCollabAPI.xCAEDeleteResult(sModel,sNewResName+'_Top');
    _VCollabAPI.xCAEDeleteResult(sModel,sNewResName+'_Bot');
    _VCollabAPI.xRefreshDialogs()
    return True;
#=================================================================================
def ExportCurrentResult2CSV(sModel,csvFile,bAllInst=False):
    '''
    Exports the current result to csv file
    Parameters:
        sModel: Cax model name
        csvFile: CSV file path
        bAllInst(Boolean): Set to True to export all instance(optional)
    Returns:
         Boolean: True if the result export to csv file was successful
                  False if the result export was not successful
    '''
    sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel)
    sResult = sCurResInfo[0]; sInstance = sCurResInfo[1]
    sInstListSting = f"{sInstance};"
    if bAllInst:
        sInstListSting=""
        sInstList = _VCollabAPI.pxGetCAEInstanceList(sModel,sResult)
        for sInst in sInstList:
            sInstListSting += f"{sInst};"
    #
    sResultList = f"{sResult};"
    #
    iPrecision = 8 ; bScientific = True; bPrintCoords = False
    status = _VCollabAPI.xExportCAEResult(csvFile,sResultList,sInstListSting,iPrecision,bScientific,bPrintCoords)
    if status:
        PrintMessage(f"File {csvFile} is saved");
        return True
    PrintErrorMessage("Export to CSV failed");
    return False
#------------------------------------------------------------
def GetValidOutputPathName(sFile,sFolder,sExt=""):
    '''
    Returns the absolute file path
    Parameters:
        sFile: File name
        sFolder: Folder path
        sExt: File extension(optional)
    Returns:
        sFile: Absolute file path
        None: If the file path is invalid
    '''
    if sFile == None:
        sOutFile = GetOutputFilePathName(sModel)+'_vp'+sExt;
        return sOutFile;
    if os.path.isabs(sFile) == False:
        if CheckFileWriteAccess(sFolder) == False:
            sgNotify("File Access Error",sFolder);
            return None;
        sFile = os.path.join(sFolder,sFile);
    else:
        sFolder = os.path.dirname(sFile);
        if CheckFileWriteAccess(sFolder) == False:
            sgNotify("File Access Error N",sFolder);
            return None;
    #------------------------------
    sFile = os.path.splitext(sFile)[0]+sExt;
    # sExtN = os.path.splitext(sFile)[1];
    # if len(sExtN) < 3 :
        # sFile = sFile + sExt;
        # return sFile;
    return sFile;
#-----------------------------------------------------------
def SaveVarsCMD(var_dict):
    '''
    Writes the commands variables to a file
    Parameters:
        var_dict:
    Returns:
        svarFile: File path of the variables file
        None: If the file path is not valid
    '''
    if len(var_dict) < 1 : return None;
    svarFile = GetOutputFilePathName(sModel,"SERVAR_Globals.py");
    if svarFile == None: return None;
    # Write into local MNF_Globals file
    with open(svarFile, 'w',encoding='utf-8',errors='ignore') as gfp:
        for va in var_dict:
            gfp.write(str(va[1:])+'=r"'+str(var_dict[va])+'"\n');
    PrintMessage(f"SetVAR file {svarFile} nVars = {len(var_dict)} saved");
    return svarFile;
#=============================================================
def ProbeIDS(ids=[]):
    '''
    Probes node/element for the given ID list
    Parameters:
        ids(List): Node/Element IDs List(optional)
    Returns:
        None
    '''
    if len(ids)<1: 
        
        return;
    
    sIDList = ";".join(ids);
    
    _VCollabAPI.xSetCAEProbeLabelFields(sModel,False, False, False, False);
    _VCollabAPI.xCAEProbeIDs(sModel,sIDList);
    
    return;
#------------------------------------------------------------
sgFileExts = {'CAX':'.cax','IMAGE':'.png','WCAX':'.wcax','HTML':'.html','PDF':'.pdf','JT':'.jt','FBX':'.fbx'};
lg_HSViewList=[];

def ResetGlobalsCMD(aModel="",sFolder=None):
    _VCollabAPI.xSetNotesFont(u"Arial Narrow Bold",20,20,20,200);
    global sModel; sModel = "";
    global sCaxPath; sCaxPath = "";
    global sDefFolder;
    sModel = aModel;
    if sModel == None: sModel = "";
    if len(sModel) < 1: sModel = Set_sModel();
    if len(sModel) > 1:
        sCaxPath = _VCollabAPI.xGetFileName(sModel);
    if sFolder != None:
        sDefFolder = sFolder;
    elif len(sCaxPath) > 0:
        sDefFolder = os.path.dirname(sCaxPath);
    else: sDefFolder = sTmpFilePath;
        
    global lg_HSViewList; lg_HSViewList = []; # may not be required?
    global CurVPathName; CurVPathName='ReportViewPath';
    global lg_HSLimits; lg_HSLimits=['NA','NA','1','0','5.0'];
    global ig_FirstInstance; ig_FirstInstance=None;
    global ig_LastInstance; ig_LastInstance = None;
    global fg_HeaderX; fg_HeaderX = 0.05;
    global fg_HeaderY; fg_HeaderY = 0.7;
    #---
    global igMaxHostSpots; igMaxHostSpots=1;
    global igInstanceFlag; igInstanceFlag = 0; # 0=> Last Instance; 1=> Max Instance; 2=> Min Instance; 3=> AllInstances
    global sgDerivedType; sgDerivedType = "";
    global iLabelArrangeMode; iLabelArrangeMode = 2; #1=>Top-Bot, 2=>Compact, 3=>Circular 4=> Silhouette, 5=>Rectangular
    global igNoOfVPs; igNoOfVPs = 0;
    global sg_OutFileName; sg_OutFileName = u"";
    global var_dict; var_dict = {};
    global sg_DefFType; sg_DefFType=".html";
    global lg_ProbeResultList; lg_ProbeResultList =[];
    #===============================================
    return;
ResetGlobalsCMD();
#===================================================================
def ProcessSaveCommand(nVals,sVals):
    global sg_OutFileName; global igNoOfVPs;global sg_DefFType;
    CurOutFileName = sg_OutFileName;
    #-- Set Type
    if nVals < 2: 
        sType = sg_DefFType[1:].upper();
    else:
        sType = sVals[1].upper();
    #------Set File
    if len(sType) < 1: 
        sgNotify("Msg","File type not specified, set to html",1);
        sType = 'HTML';
    if nVals > 2:
        sFilePath = sVals[2];
        CurOutFileName = GetValidOutputPathName(sFilePath,sDefFolder,"");
        sgNotify(f"Output file is set to {sg_OutFileName}");
        #-------------------------
    #Note sOutputFileName will not have extention
    sOutputFileName = GetValidOutFileName(CurOutFileName,True);
    sgNotify(f"Output file is set to {sOutputFileName}.{sType.lower()}");
    if IsValidOutputPath(sOutputFileName) == False:
        sgNotify("Outfilename not Valid",f"{sOutputFileName}");
        return;
    if sType == 'CAX':
        _VCollabAPI.xFileSave(sOutputFileName+'.cax');
        return;
    if sType == 'PDF':
        _VCollabAPI.xFileSave(sOutputFileName+'.pdf');
        return;
    if sType == 'JT':
        _VCollabAPI.xFileSave(sOutputFileName+'.jt');
        return;
    if sType == 'FBX':
        _VCollabAPI.xFileSave(sOutputFileName+'.fbx');
        return;
    if sType == 'IMAGE':
        if nVals <= 2:
            CurOutFileName = sOutputFileName+'.png';
        if CurOutFileName.lower().endswith(('.png', '.jpg', '.tif', '.bmp')) == False:
            sgNotify("Save Image Type Error",f"{CurOutFileName},\n {sVals}",2);
            return False;
        #--- Set Image size
        iWidth = None;iHeight = None;
        if nVals > 4 :
            iWidth = GetInt(sVals[3],0);
            iHeight = GetInt(sVals[4],0);
            if iWidth < 100 or iHeight < 100: iWidth = None;iHeight = None;
        ExportImageCMD(CurOutFileName,iWidth,iHeight);
        return;
    if sType == 'HTML' or sType == 'WCAX':
        sFileExt = f".{sType.lower()}"
        if igNoOfVPs < 1:
            vplist = _VCollabAPI.pxGetViewPointList("",-1);
            if len(vplist) < 1:
                if GenerateCurResultView() == False:
                    SetCameraView(-1.0,-1.0,-0.5,0.5,0.0,1.0);
                    SaveAsHTMLorWCAX(sOutputFileName,sFileExt,3); #Current View
                    return;
        SaveAsHTMLorWCAX(sOutputFileName,sFileExt); # Current ViewPath
        return;
    PrintErrorMessage(sVals[1] + " File type Not Supported");
    return;
#================================================
bShowCMDS = False;
def RunCMD(sLine):
    global sModel;global bShowCMDS;
    sLine = sLine.strip()
    if len(sLine) < 1 or sLine[0] == '#' : return;
    cpos=sLine.find('#');
    if cpos > 1: sLine = sLine[:cpos];
    sLine = sLine.strip()
    sVals = [x.strip() for x in sLine.split(',')]
    nVals = len(sVals);
    if nVals < 1 : return;
    sKey = sVals[0];
    if sKey == 'EXIT': return;
    if  sKey == 'SHOWCMDS':
        bShowCMDS = False
        if nVals > 1:
            if sVals[1].upper() == 'TRUE' or sVals[1].upper() == 'Y':
                bShowCMDS = True;
        return;
    if sKey == "START":
        OpenLogFiles(bCheck = True);
        ResetGlobalsCMD();
        bShowCMDS = False
        return;
    if bShowCMDS : sgNotify("CMD Line",sVals,2); return;
    ProcessOneCommand(sKey,nVals,sVals);
    return;
#--------------------------------------------------------------
def ProcessOneCommand(sKey,nVals,sVals):
    global sModel; global sCaxPath; global sDefFolder; global CurVPathName;
    global lg_HSViewList; global lg_HSLimits;
    global ig_FirstInstance; global ig_LastInstance; 
    global fg_HeaderX; global fg_HeaderY; 
    global igMaxHostSpots;global igInstanceFlag; global sgDerivedType;
    global iLabelArrangeMode; global igNoOfVPs; global sg_OutFileName;
    global var_dict;
    global lg_ProbeResultList;
    #----------------------------------------
    #CUR_FOLDER,CAX/PY/TEMP/<string>
    if sKey == 'CUR_FOLDER':
        if nVals < 2 : return;
        sFolder = sVals[1];
        SetCurFolderCMD(sFolder);
        return;
    if sKey == 'FIT_VIEW':
        if nVals < 2 : 
            _VCollabAPI.xFitView();
            return;
        FitViewCMD(GetFloat(sVals[1],-0.1));
        return;
    if sKey == 'EXPLODE_VIEW':
        if nVals < 2 : 
            _VCollabAPI.xExplode(False,0,False,1);
            return;
        ExplodeViewCMD(nVals-1,sVals[1:]);
        return;
    #--- LOADCAX,D:\Tempi\base*Min.cax
    if  sKey == 'LOADCAX':
        if nVals < 2 or len(sVals[1]) < 1:
            sgNotify("Msg","LOADCAX: Cax File not specified",3);
            return False
        sCAXFile = sVals[1];
        #-- Validate and Load cax file
        sCAXFileName = GetFileFullPath(sDefFolder,sCAXFile);
        if sCAXFileName != None:
            _VCollabAPI.xFileOpen(sCAXFileName);
            sModel = _VCollabAPI.xGetCurCAEModelName();
            return;
        PopMessage(f"Cax file {sCAXFile} Not found in {sDefFolder}");
        return False;
    #--- MERGECAX,D:\Tempi\base*Min.cax
    if  sKey == 'MERGECAX':
        if nVals < 2 or len(sVals[1]) < 1:
            sgNotify("Msg","MERGECAX: Cax File not specified",3);
            return False
        sCAXFile = sVals[1];
        #-- Validate and Load cax file
        sCAXFile = GetFileFullPath(sDefFolder,sCAXFile);
        if sCAXFile != None:
            _VCollabAPI.xFileMerge(sCAXFile);
        return;
    #--- Set current Model=> SET_MODEL 
    if  sKey == 'SET_MODEL':
        if nVals > 1:
            sModel = SetCurrentModelCMD(sVals[1]);
        return;
    #*-- SET_Font,Type,size,name,iR,iG,iB,ibR,ibG,ibB,iborder
    #*-- Type=NOTE,PROBE_VALUE,PROBE_TEXT,OTHERS
    if sKey == 'SET_FONT':
        if nVals > 2:
            SetFontCMD(sVals[1:]);
            _VCollabAPI.xRefreshDialogs();
            _VCollabAPI.xRefreshViewer();
            _VCollabAPI.xRefreshProbeTables(sModel);
        return;
    # PART_OPTIONS,DMODE=1,*Bracket*,*Lever*
    # PART_OPTIONS,COLOR=Y,*Bracket*,*Lever*
    if sKey == 'PART_OPTIONS':
        if nVals < 3: return;
        SetPartDisplayOptionsCMD(sVals[1:]);
        return;
    #DEL_ENTITY,PROBE,XY,LABEL,SYMBOL
    if sKey == 'DEL_ENTITY':
        DeleteEntityCMD(nVals,sVals);
        return;
    #SET_DISPLAY,COLOR=Y,LEGEND=Y,DEFORM=Y,UDMESH=1,DMODE=1,AXIS=Y,SECTION=N,BG=1
    if sKey == 'SET_DISPLAY':
        if nVals < 2: return;
        SetDisplayCMD(nVals-1,sVals[1:]);
        return;
    #SHOW_LABEL,ID=True,ROW=True,COL=False,Rank=True,PART=False,HEADER=False,ABR=True
    if sKey == 'SHOW_LABEL':
        SetShowLabelCMD(nVals-1,sVals[1:]);
        return; 
    #LABEL_PRECISION,iPrecision,bScientific(Y/N)
    if sKey == 'LABEL_PRECISION':
        if nVals > 2:
            curVals = _VCollabAPI.pxGetCAEProbeLabelDefaultNumericalFormat(sModel)
            iPrecision = GetInt(sVals[1],curVals[0])
            bScientific = False
            if sVals[2].upper() == 'TRUE' or sVals[2].upper() == 'Y': bScientific = True
            SetLabelPrecision(sModel,iPrecision,bScientific)
        return;
    #SET_LEGEND,MAX,MIN,AMax,AMin,Precision,Discrete(Y/N),Reverse(Y/N),NColor
    if sKey == 'SET_LEGEND':
        if nVals > 2:
            SetLegendCMD(sVals[1:]);
            _VCollabAPI.xRefreshDialogs();
            _VCollabAPI.xRefreshViewer();
        return; 
    if sKey == 'LEGEND_HEXCOLORS':
        if nVals > 3: 
            SetLegendCustHexColorsCMD(sVals[1:]);
        return;
    if sKey == 'SET_LEGEND_DYNRANGE':
        if nVals > 3: 
            SetCustomLegendRangeCMD(sVals[1:]);
        return;
    #* Set_ANIM,Type,nFrames,bStaticFringe (True/False),Scale,Speed
    #iType => linear=0,transient=1,harmonic=3 
    if sKey == 'SET_ANIM':
        AnimationSettingsCMD(nVals-1,sVals[1:]);
        return;
    #-- Header Legend Position ---used in SetSelectedResults
    if sKey == 'HEADER_POS':
        fg_HeaderX=0.05;fg_HeaderY=0.7;
        if nVals > 2:
            fg_HeaderX=float(sVals[1]);fg_HeaderY=float(sVals[2]);
            _VCollabAPI.xSetCAEHeaderLegendPosition(sModel,True,fg_HeaderX,fg_HeaderY);
        return;
    #--- Set Camera View Direction and Upvector
    if sKey == 'CAMERA_VIEW' or sKey == 'CAMERA':
        if nVals > 6:
            fVals = [float(x) for x in sVals[1:7]];
            SetCameraView(fVals[0],fVals[1],fVals[2],fVals[3],fVals[4],fVals[5]);
        else:
            SetBestViewCMD();
        return;
    #--- Set Camera X-dir and Y Dir
    if sKey == 'CAMERA_XYAXIS':
        if nVals > 6:
            fVals = [GetFloat(x,0.1) for x in sVals[1:7]];
            SetCameraXYCMD([fVals[0],fVals[1],fVals[2]],[fVals[3],fVals[4],fVals[5]]);
        else:
            SetCameraXYCMD();
        return;
    if sKey == 'ORTHO_VIEW':
        if nVals > 1:
            if sVals[1].upper() == 'N': 
                _VCollabAPI.xSetPerspectiveCamera(True);
                return;
        _VCollabAPI.xSetPerspectiveCamera(False);
        return;
    if sKey == 'VIEWPATH':
        if nVals > 1:
            CurVPathName = sVals[1];
            if nVals > 2 and sVals[2] == 'Y':
                _VCollabAPI.xDeleteViewPath(CurVPathName);
        return;   
    #---------------------
    if sKey == 'SET_MODEL_COLOR': 
        SetModelRandomColor(sModel);
        _VCollabAPI.xRefreshDialogs();
        _VCollabAPI.xRefreshViewer();
        return;
    #Parts_SHOW,ALL/NONE/INVERT/ONLY,Part name list
    if sKey == 'PARTS_SHOW':
        if nVals > 1:
            ShowPartsCMD(sVals[1:]);
            _VCollabAPI.xRefreshDialogs();
            _VCollabAPI.xFitView();
            _VCollabAPI.xRefreshViewer();
        return;
    ##PARTS_HIDE,ALL/INVERT/ONLY,Part name list
    if sKey == 'PARTS_HIDE':
        if nVals > 1:
            HidePartsCMD(sVals[1:]);
            _VCollabAPI.xRefreshDialogs();
            _VCollabAPI.xFitView();
            _VCollabAPI.xRefreshViewer();
        return;
    #FILTER_PARTS,fMin,fMax,bFitView
    if sKey == 'FILTER_PARTS':
        CAEFilterPartsCMD(sVals[1:]);
        return;
    #ASM_SHOW,N,Entity Sets
    if sKey == 'ASM_SHOW':
        if nVals > 2:
            ShowAssemblyCMD(sVals[1:]);
            _VCollabAPI.xRefreshDialogs();
            _VCollabAPI.xFitView();
            _VCollabAPI.xRefreshViewer();
        return;
    #-----------
    #--ADD_PROBE_RESULT,START/END/ADD,Stress*VON*,St_Von,NA,140.0
    if sKey == 'ADD_PROBE_RESULT': 
        if nVals < 3:
            lg_ProbeResultList = [];return;
        lg_ProbeResultList = SetProbeResultCMD(lg_ProbeResultList,nVals-1,sVals[1:]);
        return;
    if sKey == 'SEL_RESULT': #SEL_RESULT,*STRESS*Von*,L7*,NA
        if nVals > 1 and len(sVals[1])>0:
            sResult = SelectResultCMD(sVals[1:]);
            if sResult == None:
                PrintMessage(f"{sVals[1:]} Result Not found");
        return;
    #SEL_INSTANCE,InstFlag
    #--- InstFlag= 0 => Last Instance, 1 => Max Instance, 2 => Min Instance, 
    #---           3 => First Instance, else current Instance
    if sKey == 'SEL_INSTANCE': #
        if nVals > 1:
            igInstFlag = GetInt(sVals[1]);
            sCurResInfo = _VCollabAPI.pxGetCAECurrentResult(sModel);
            sResult = sCurResInfo[0];sDerived = sCurResInfo[2];
            sInst = SelectInstance(sModel,sResult,sDerived,igInstFlag);
            _VCollabAPI.xSetCAEResult(sModel,sResult,sInst,sDerived);
            _VCollabAPI.xRefreshDialogs();
        return;
    #CREATE_RESULT,MaxVonMises,Stress*Top*Von*,Stress*Bot*Von*,if((A>B),A,B)
    if sKey == 'CREATE_RESULT':
        if nVals < 5: return;
        CreateResultCMD(sVals[1:]);
        return;
    #CREATE_RESULT_CYL,Displacement,Disp Radial,53.66,73.05,42.747,0,0,1,1,0,0,U,CylCoord,
    if sKey == 'CREATE_RESULT_CYL':
        if nVals < 11: return;
        CreateCylResultCMD(sVals[1:]);
        return;
    if sKey == 'CREATE_ENVELOP': #CREATE_ENVELOP,sResult,sDerived,bIsMax
        if nVals < 2 or len(sVals[1]) < 1 : return;
        sResult = sVals[1];
        sDerived = NULLSTR;
        if nVals > 2: sDerived = sVals[2];
        bMax = True;
        if nVals > 3:
            sMax = sVals[3];
            if sMax == 'N' or sMax.upper() == 'MIN': 
                bMax = False;
        sEnvResult = CreateEnvelopResult(sResult,sDerived,bMax);
        return;
    if sKey == 'PROBE_RES':
        if nVals > 1:
            sProbeResList = sVals[1:];
            SetSelectedResults(sProbeResList);
        return;
    if sKey == 'RES_MASK': #RES_MASK,CPMask,Contact Pressure,1,NA,NA
        CreateResultMask(sVals);
        return;
    if sKey == 'PART_MASK': #PART_MASK,ParkMask,*FLEX*EXCLUDE,NA,1
        CreatePartMask(sVals);
        return;
    if sKey == 'NODE_MASK': #NODE_MASK,NodeMask,15.0,11234,3456
        CreateNodeMask(sVals);
        return;
    if sKey == 'SET_MASK' or sKey == 'SET_MASK_IN' : #SET_MASK, CPMASK,BoltMask
        if nVals < 2 :
            _VCollabAPI.xSetCAEMaskedNodeSetList(sModel,u"");
            _VCollabAPI.xSetNodeSetHotspotMask(sModel,0);
            return;
        sMaskList = sVals[1:];
        _VCollabAPI.xSetCAEMaskedNodeSetList(sModel,sMaskList);
        _VCollabAPI.xSetNodeSetHotspotMask(sModel,1);
        # for aMask in sMaskList:
            # _VCollabAPI.xSetNodeSetMask(sModel,aMask,1);
        return;
    if sKey == 'SET_MASK_MODE': #SET_MASK_MODE,MODE,CPMASK,BoltMask
        if nVals < 2 :
            _VCollabAPI.xSetNodeSetHotspotMask(sModel,0);
            return;
        _VCollabAPI.xSetNodeSetHotspotMask(sModel,1);
        iMode = 0;
        if IsFloat(sVals[1]):
            iMode = int(sVals[1]);
            if iMode < 0 :
                lMaskList=_VCollabAPI.pxGetCAENodeSetList(sModel);
                iMode = -iMode;
            if iMode > 2: iMode = 1;
        if nVals < 3 :
            lMaskList=_VCollabAPI.pxGetCAENodeSetList(sModel);
        else:
            lMaskList = sVals[2:];
        for aMask in lMaskList:
            _VCollabAPI.xSetNodeSetMask(sModel,aMask,iMode);
        _VCollabAPI.xRefreshDialogs();
        return;
    #HS_LIMITS,NA,NA,5,0,20.0
    if sKey == 'HS_LIMITS':
        lg_HSLimits = None;
        if nVals > 5:
            lg_HSLimits = sVals[1:];
            SetHotSpotParamsCmd(lg_HSLimits);
        return; 
        
    #---SET_COMPARE_RES,ON=Y/N,BY=0-2,MODE=0-2,WITH=0-2,RADIUS=5.0,SHOWALL=Y,
    if sKey == 'SET_COMPARE_RES':
        SetCompareResCMD(nVals,sVals);
        return;
    #-- SET_PALETTE_MODE,0/1/2/3=>0- Active,1- Multi,2- Combined, 3- Multi-Common
    if sKey == 'SET_PALETTE_MODE':
        if nVals < 2: return;
        imode = GetInt(sVals[1],3);
        _VCollabAPI.xSetCAEPaletteMode(imode);
        return;
    
    if sKey == 'ADD_2DNOTE': #ADD_2DNOTE,Title Page,0.4,0.3:
        if nVals < 2: return;
        sNoteString = sVals[1];
        fSx = 0.4; fSy = 0.9;
        if nVals > 3:
            if IsFloat(sVals[2]):
                fSx = float(sVals[2]);
            if IsFloat(sVals[3]):
                fSy = float(sVals[3]);
        _VCollabAPI.xAdd2DNotes(sNoteString,fSx,fSy,True);
        return;
    
    if sKey == 'COMP_HOTSPOTS': #COMP_HOTSPOTS,sVPName,Masklist
        ComputeHotSpotsCMD(nVals,sVals);
        return;
    #IMAGE_VP,VPNAME,imagename,Title,Sx,Sy
    #IMAGE_VP,Title,Title.png,Title Slide,0.4,0.8
    if sKey == 'IMAGE_VP':
        if nVals > 2:
            CreateImageVPCMD(sVals[1:]);
        return;
    if sKey == 'ADD_VP': #ADD_VP,Name,Title,Sx,Sy
        if nVals > 1:
            ADDViewPointCMD(sVals[1:],False);
        return;
    #* ADD_VP_ANIM,Name,Title,Sx,Sy
    if sKey == 'ADD_VP_ANIM':
        if nVals > 1:
            ADDViewPointCMD(sVals[1:],True);
        return;
    #---zxxx
    if sKey == 'ADD_HSVIEW':
        if nVals > 7:
            fVals = [float(x) for x in sVals[1:7]];
            fVals.append(sVals[7]);
            lg_HSViewList.append(fVals);
            SetCameraView(fVals[0],fVals[1],fVals[2],fVals[3],fVals[4],fVals[5]);
        else:
            lg_HSViewList = [];
            #lg_HSViewList.append([1,0,0,0,1,0,'Front']);
            #lg_HSViewList.append([-1,0,0,0,1,0,'Back']);
        return;
    #------
    if sKey == 'LOADCASE':
        ig_FirstInstance = None;ig_LastInstance=None;
        if nVals > 2:
            if IsFloat(sVals[1]):
                ig_FirstInstance= int(sVals[1]);
            if IsFloat(sVals[2]):
                ig_LastInstance= int(sVals[2]);
        return;
    #----HOTSPOT_VIEW,sVPName,HSParameters
    if sKey == 'HOTSPOT_VIEW': 
        if nVals < 2: return;
        HSInfo = None;
        if nVals > 6:
            HSInfo = sVals[2:];
        CreateHSView(sVals[1],HSInfo);
        return;
    #----LOADCASE_HSVIEW,<vewpathname> 
    if sKey == 'LOADCASE_HSVIEW': 
        sVPathName = None;
        if nVals > 1:
            sVPathName = sVals[1];
        ig_FirstInstance = None;ig_LastInstance=None;
        if nVals > 3:
            if IsFloat(sVals[2]):
                ig_FirstInstance= int(sVals[2]);
            if IsFloat(sVals[3]):
                ig_LastInstance= int(sVals[3]);
        CreateHotspotsForEachinstance(sVPathName);
        return;
    #---Specific Commands
    #ENVELOP_VIEW <sResultStr>,<hotspot parameters>
    if sKey == 'ENVELOP_VIEW':
        HSInfo = None;
        if nVals < 2 or len(sVals[1]) < 1:
            sgNotify("Msg","ENVELOP_VIEW: Result not specified",3);
            #PrintErrorMessage(sVals,"Command Error");
            return;
        sResultStr = sVals[1];
        if nVals > 2:
            HSInfo = sVals[2:];
        Create_EnvelopView(sResultStr,HSInfo);
        return;
    #----------------------Specific Commands
    if sKey == 'MODAL_VPS': #-- MODAL_VPS,10,Y
        _VCollabAPI.xLockRefresh(True);
        if IsModalResult(): 
            CreateModalViewsCMD(nVals,sVals);
        else:
            PrintMessage("Not a Modal Result?");
            CreateHotspotsForEachResultCMD(1,sVals);
        _VCollabAPI.xLockRefresh(False);
        return;
    if sKey == 'ALL_RESULT_VPS': #ALL_RESULT_VPS,<nhotspots>
        if IsModalResult(): 
            _VCollabAPI.xLockRefresh(True);
            CreateModalViewsCMD(1,sVals);
            _VCollabAPI.xLockRefresh(False);
        else:
            CreateHotspotsForEachResultCMD(nVals,sVals);
        return;
    if sKey == 'FRFVIEW_VPS': #FRFVIEW_VPS,<nhotspots>
        CreateComplexFRFView_CMD(nVals,sVals);
        return;
    #SETXYPLOT_WIN,<bgColor(rgb), <winsize (xmin,ymin,xmax,ymax)>
    if sKey == 'SETXYPLOT_WIN': 
        SetXYPlotWindow_CMD(nVals-1,sVals[1:]);
        return;
    #MINMAX_PLOT,<PlotName>,<iMinmax=0=Max,1=Min,2=Both>
    if sKey == 'MINMAX_PLOT': 
        CreateMinMaxPlot_CMD(nVals-1,sVals[1:]);
        return;
    #HS_XYPLOT,<PlotName>,<maxhs>
    if sKey == 'HS_XYPLOT': 
        CreateHS_XYPlot_CMD(nVals-1,sVals[1:]);
        return;
    if sKey == 'COMPARE_GEOM_VPS':#iCompareMode,fMaxDistance
        CompareGeomCMD(nVals,sVals);
        return;
    if sKey == 'ARRANGE_MODEL': #ARRANGE_MODEL,<Nrow>
        ArrangeModelsCMD(nVals,sVals);
        return;
    if sKey == 'HS_TABLE2D': # HS_TABLE2D,0.1,0.6, Rank, VonMises,Stress MaxP
        #PopMessage(nVals,sVals);
        if nVals > 2:
            DisplayHS2DTableCMD(nVals-1,sVals[1:]);
        else:
            DisplayHS2DTableCMD();
        return;
    #------------------------------------------------------------------------------
    if sKey == 'IMPORT_XYCSV':
        if nVals > 1:
            csfile = sVals[1];
            if os.path.exists(csfile):
                _VCollabAPI.xImportXYPlots(csfile);
                Plotlist = _VCollabAPI.xGetXYPlotList().split(";");
                if len(Plotlist) > 0:
                    sPartList = _VCollabAPI.pxGetVisiblePartsList(sModel);
                    if len(sPartList) < 1:
                        _VCollabAPI.xSetXYPlotPlacement(Plotlist[0], 0.1, 0.08, 0.8, 0.7);
        return;
    #----- to fit the model into window ------
    if sKey == 'FIT_WINDOW':  
        #sgNotify("Msg",f"FitWin: [sVals]",0);
        if len(sVals) > 4:
            xpos1 = GetFloat(sVals[1],0.1);
            ypos1 = GetFloat(sVals[2],0.1);
            xpos2 = GetFloat(sVals[3],0.8);
            ypos2 = GetFloat(sVals[4],0.7);
            if ypos2 < ypos1:
                _VCollabAPI.xFitWindowView(xpos1,ypos1,xpos2,ypos2);
            else:
                _VCollabAPI.xFitWindowView(xpos1,ypos2,xpos2,ypos1);
            return;
        _VCollabAPI.xFitView();
        return;
    #----------------------------------
    #--RUN_SCRIPT,
    if sKey == 'RUN_SCRIPT':
        if nVals > 1:
            RunScriptCMD(sVals[1:]);
        return;
    #==============================================
    if sKey == 'NEW_INSTANCE':
        if nVals > 1:
            CreateInstanceCMD(sVals[1:]);
        return;
    #==============================================
    if sKey == 'DEL_INSTANCE':
        if nVals > 1:
            DeleteInstanceCMD(sVals[1:]);
        return;
    #=========================================
    #PIVOT_RESULT,NewResultName,N1,N2,N3,iOrigin=2,iCoord=0
    if sKey == 'PIVOT_RESULT':
        if len(sVals) > 1: PivotResultCMD(sVals);
        return;
    #-----------------------------
    if sKey == 'SETGVAR': #SETGVAR,gTable_Font="Arial",gTable_FontSize=16
        if nVals > 1: 
            SetGlobalVariableCMD(nVals-1,sVals[1:]);
        return;
    # Set legend no.of colors and grey end 
    # LEGEND_COL,no.of colors,grey end(Y=Grey,N=Blue),Grey reverse(Y=Reverse)
    if sKey == 'LEGEND_COL':
        if nVals < 2: return;
        nCol = GetInt(sVals[1],0);
        bGrey = False; bRev = False;
        if nVals > 2 and sVals[2].upper() == 'Y': bGrey = True;
        if nVals > 3 and sVals[3].upper() == 'Y': bRev = True;
        SetCustomLegend(bGrey,nCol,bRev);
        return;
    # Set Legend position
    # LEGEND_POS,X position,Y position,bRelative,iOrientation (0-2/N)
    if sKey == 'LEGEND_POS':
        MoveLegendCMD(nVals,sVals);
        return;
    # Set Legend Font Size
    if sKey == 'LEGENDFONT_SIZE':       #LEGENDFONT_SIZE,iSize,fontName
        size = 12;
        if nVals > 1:
            size = GetInt(sVals[1],12);
        _VCollabAPI.xSetCAELegendFontSize(size);
        if nVals > 2:
            if len(sVals[2]) < 3: return;
            if _VCollabAPI.xIsFontAvailable(sVals[2]):
                _VCollabAPI.xSetCAELegendFontName(sVals[2]);
                if _VCollabAPI.xGetCAELegendBGColorVisibility():
                    _VCollabAPI.xSetCAELegendBGColorVisibility(False);
                    _VCollabAPI.xRefreshDialogs();
                    _VCollabAPI.xSetCAELegendBGColorVisibility(True);
                else:
                    _VCollabAPI.xSetCAELegendBGColorVisibility(True);
                    _VCollabAPI.xRefreshDialogs();
                    _VCollabAPI.xSetCAELegendBGColorVisibility(False);
                _VCollabAPI.xRefreshDialogs();
            else:
                sgNotify("Error",f"{sVals[2]} is not valid Font name",0);
        return;
    # Set Axis Position
    if sKey == 'AXIS_POS':      # AXIS_POS,X position,Y position
        if nVals < 3: return;
        xpos = GetFloat(sVals[1],0.96);
        ypos = GetFloat(sVals[2],0.06);
        if xpos < 0.02 : xpos = 0.02;
        if xpos > 0.96 : xpos = 0.96;
        if ypos < 0.04 : ypos = 0.04;
        if ypos > 0.95 : ypos = 0.95;
        _VCollabAPI.xSetAxisPosition(xpos,ypos);
        return;
    #-------------- Save options -----
    if sKey == 'OUTFILE_NAME':
        if nVals < 2: return;
        sFilePath = sVals[1];
        sg_OutFileName = GetValidOutputPathName(sFilePath,sDefFolder,"");
        sgNotify(f"Output file is set to {sg_OutFileName}");
        return;
    if sKey == 'SAVE':
        ProcessSaveCommand(nVals,sVals);
        return;
    if sKey == 'PYRUN':
        retflag = ExecutePythonLineCMD(sVals[1:]);
        return;
    #===============================================
    sgNotify("Error",f"{sKey} Command Not found",2);
    return;
#=============================================================================
def ProcessCommandList(VPList,bReset=True,sFolder=None,aModel=""):
    '''
    Processes the command list
    Parameters:
        VPList(List): Command list
        bReset: Resets general settings (Label fonts,hotspot setting, nodeset for masking and legend precision)(optional)
        sFolder: Folder path (optional)
        aModel: Cax model name (optional)
    Returns:
         None/False
    '''
    if len(VPList) < 1:
        sgNotify("Error","No Commands?",5);
        return;
    global sModel; global sCaxPath; global sDefFolder; global CurVPathName;
    global lg_HSViewList; global lg_HSLimits;
    global ig_FirstInstance; global ig_LastInstance; 
    global fg_HeaderX; global fg_HeaderY; 
    global igMaxHostSpots;global igInstanceFlag; global sgDerivedType;
    global iLabelArrangeMode; global igNoOfVPs; global sg_OutFileName;
    global var_dict;
    global bShowCMDS;
    global lg_ProbeResultList;
    #----
    if bReset:
        _VCollabAPI.xSetNotesFont(u"Arial Narrow Bold",20,20,20,200);
        sDefFolder = sPyFolder;
        lg_HSViewList = [];
        CurVPathName='ReportViewPath';
        lg_HSLimits=['200','NA','20','0','20.0'];
        ig_FirstInstance=None;ig_LastInstance = None;
        fg_HeaderX = 0.05;fg_HeaderY = 0.7;
        
        sgDerivedType = "";
        igNoOfVPs = 0;
        _VCollabAPI.xSetCAELegendAutoFormatMode(sModel,False);
        var_dict = {};
        bShowCMDS = False;
        lg_ProbeResultList = [];
    #==========================================
    if aModel == None or len(aModel) < 1:
        sModel = Set_sModel();
        if sModel == None or len(sModel) < 1:
            PrintErrorMessage("No Models Loaded?");
            return;
    else:
        sModel = aModel;
    if len(sModel) > 0:
        sCaxPath = _VCollabAPI.xGetFileName(sModel);
    if sFolder != None:
        sDefFolder = sFolder;
    elif len(sCaxPath) > 0 and bReset:
        sDefFolder = os.path.dirname(sCaxPath);
    #===============================================
    iLine = 0; nVPLines = len(VPList);
    sVarsFile = None;
    cmd_StartTime = time.time();
    while iLine < nVPLines:
        sLine = VPList[iLine];iLine = iLine+1;
        sVals = [x.strip() for x in sLine[0].split(',')]
        nVals = len(sVals);
        if nVals < 1 : continue;
        sKey = sVals[0].upper();
        #if bShowCMDS : sgNotify("CMD Line",sVals,2);
        if sKey[0] == '#': #comment line
            continue;
        if sKey == '\"\"\"':
            #PopMessage('Comment Start');
            while iLine < nVPLines:
                sLine = VPList[iLine];iLine = iLine+1;
                if sLine[0].find('\"\"\"') >= 0 : break;
            continue;
            #PopMessage('Comment ENDs');
        #------------------ Set Params --------------
        # Set variables from commands
        if sKey == 'SET_VAR':
            if nVals > 1:
                NewVals = [];
                curstr=None;
                for val in sVals[1:]:
                    if val.find('=') < 0:
                        if curstr != None: curstr = curstr + ',' + val;
                    else:
                        if curstr != None:
                            NewVals.append(curstr); 
                        curstr = val;
                if curstr != None:
                        NewVals.append(curstr);
                for val in NewVals:
                    var = val.split("=");
                    if len(var) < 2: continue;
                    var = [i.strip() for i in var if i];
                    var_dict["%"+var[0]] = "=".join(var[1:]);
                    #vcNotify("var",f"{var[0]} = {var_dict['%'+var[0]]}",2);
            continue;
        if sKey == "SAVE_VAR":
            sVarsFile = SaveVarsCMD(var_dict);
            continue;
        # Assiging all mentioned variables
        if nVals > 1:
            if len(var_dict) > 0:
                for count,val in enumerate(sVals):
                    if len(val) > 0:
                        if val[0] == "%":
                            if val in var_dict:
                                sVals[count] = var_dict[val];
        if bShowCMDS : sgNotify("CMD Line",sVals,2);
        if  sKey == 'SHOWCMDS':
            bShowCMDS = False
            if nVals > 1:
                if sVals[1].upper() == 'TRUE' or sVals[1].upper() == 'Y':
                    bShowCMDS = True;
            continue;
        # cmdTime = time.time();
        # sTimeString = GetTimeString(cmd_StartTime,cmdTime);cmd_StartTime=cmdTime;
        # _VCollabAPI.xSetStatusMsg(f"{iLine} : {sVals[:2]}... {sTimeString}");
        if sKey == 'EXIT':
            break;
        if sKey == 'PYRUN':
            retflag = ExecutePythonLineCMD(sVals[1:]);
            if retflag > 0: break;
            continue
        if sKey == 'PROBERES_START':
            sProbeResInfoList = [];
            while iLine < nVPLines:
                sLine = VPList[iLine];iLine = iLine+1;
                sVals = [x.strip() for x in sLine[0].split(',')]
                nVals = len(sVals);
                if nVals < 1 : continue;
                sKey = sVals[0].upper();
                if sKey == 'PROBERES_END':
                    SetProbeResInfoList(sProbeResInfoList);
                    break;
                sProbeResInfoList.append(sVals);
            continue;
        #---
        ProcessOneCommand(sKey,nVals,sVals);
        #--End for each line----------------------------------------------------
    #
    _VCollabAPI.xLockRefresh(False);
    _VCollabAPI.xRefreshDialogs();
    _VCollabAPI.xCAERefresh(sModel);
    _VCollabAPI.xRefreshViewer();
    return;
#=================================================================
def ProcessCommandFile(sCommandFile):
    '''
    Gets the list of commands from the command file
    Parameters:
        sCommandFile: File path of command file 
    Returns:
        Boolean: True if execution of the command list was successful
                 False if command file is empty
    '''
    VPList = ReadCommandFile(sCommandFile);
    if len(VPList) < 1:
        sgNotify("Error:",f"Empty Command Template File {sCommandFile}",5);
        return False;
    ProcessCommandList(VPList);
    return True;
#==================================================
def py_exec(cmd):
    retflag = 0;
    try:
        exec(cmd)
        return 0
    except SyntaxError as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        line_number = err.lineno
        retflag = 1;
    except Exception as err:
        error_class = err.__class__.__name__
        detail = err.args[0]
        cl, exc, tb = sys.exc_info()
        line_number = traceback.extract_tb(tb)[-1][1]
        retflag = 2;
    else:
        retflag = 3;
        pass
        return retflag
    sg.Popup(f"{error_class}: {cmd}\n{detail}",keep_on_top=True);
    return retflag;
#----------------------------------------------------------
def ExecutePythonLineCMD(sVals):
    pycmd = ','.join(sVals);
    if pycmd[0:2] == '.x' or pycmd[:3] == '.px':
        pycmd = '_VCollabAPI'+pycmd;
    PrintMessage(f"PYRUN: {pycmd}");
    retFlag = py_exec(pycmd);
    return retFlag;
    
#================================= END ============================================
