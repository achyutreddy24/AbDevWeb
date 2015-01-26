import glob
import os
import re
import argparse
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("-p", "--path", help="Path to folder with reports, (change '\\' to '/') end the string with a '/' \n leave blank for root directory", default="")
parser.add_argument("-o", "--output", help="Name of output html file, leave blank for default", default="Web-Report.html")
args = parser.parse_args()


#Path to folder with the files, relative to where the python file is
#Leave blank if python file is in same place
#End the path with a '/'
FolderPATH = args.path  # #"../output_m71derived_togo/output_m71derived_togo/"
FolderPATH = "../output_ama1_togo/output_ama1_togo/"


#Name of HTML File
FinalFileName = args.output


verbose = args.verbose
def vPrint(str):
    if verbose == True:
        print(str)
    else:
        pass


#Here is how the following 5 html strings work
#1. The PTMSummaryHTML is filled out for one row, then appended to a string. This happens for each row in the table
#2. Repeat step 1 for HYDSummaryHTML
#3. Append both of these into the SectionHTML
#4. Repeat step 1 for HTMLOpening (CDR Table)
#5. Append Section html and CDRtable html into base html
#6. Save this as an html file
BaseHTML = """
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <style>
        img{{
      margin-left: auto;
      margin-right: auto;
      padding:0;
      display: block;
    }}
    </style>
    <head>
        <title>Protein Report</title>
    </head>
    <body>
        <section>
            <div align=center>
            <div style="font: 20pt Times New Roman"><A NAME="top"><b>Antibody Developability Web Report</b></div>
            <div style="font: 16pt Times New Roman"><b>{DirName}</b></div>
            <div style="font: 10pt Times New Roman"><b>Auto-Generated Web Report</b></div><br>
            
            <table width=820 cellspacing=1 cellpadding=10 border=4>
            <tr align=center><td><b>Seq</b></td><td><b>Chain 1</b></td><td><b>Chain 2</b></td><td><b>L1</b></td><td ><b>L2</b></td><td><b>L3</b></td>
                                                                                                     <td><b>H1</b></td><td><b>H2</b></td><td><b>H3</b></td><td><b>PTM Risk</b></td><td><b>Aggregate Risk</b></td><td><b>RAW Files</b></td></tr>
                                                                                       
            {OpenTable}
            </table>
        </section>
        {Sections}

    </body>
</html>
"""

SectionHTML = """
<section>
            <h1 align=center style="font: 20pt Times New Roman"><A NAME="Seq{SeqNum}"><b>Sequence {SeqNum} - {FirstChain} - {SecondChain}</b></h1></A>
            <h2 style="font: 16pt Times New Roman" align=center colspan=10><td><b>Post Translational Modifications</b></h2>
            
            <table align=center width=820 cellspacing=2 cellpadding=4 border=0>
            <tr bgcolor="#C0C0C0" align=center><td>PTMTYPE</td><td>CDRLabel</td><td>Motif</td><td>Residue</td><td>SASA</td><td>%SASA</td><td>#Neighbours</td><td>Halflife</td><td>Risk</td></tr>
            {PTMTable}
            </table>
            
            <h2 style="font: 16pt Times New Roman" align=center colspan=10><td><b>Hydrophobicity</b></h2>
            
            <table align=center width=820 cellspacing=2 cellpadding=4 border=0>
            <tr bgcolor="#C0C0C0" align=center><td>Risk</td><td>Number</td><td>Sap Area</td><td>SASA</td><td>%SASA</td><td>HYD RES SASA</td><td>HYD Residues</td></tr>
            {HYDTable}
            </table>
            <div align=center><A HREF="#top">Back to Top</a></div>
            
            
            <img height=300 align=center src="{img1}" border=0>
            
            <img height=300 align=center src="{img2}" border=0>

    <hr> 

</section>

"""


HTMLOpening = """<tr align=center><td rowspan=3><A HREF="#Seq{SeqNum}">{DispSeqNum}</A></td><td rowspan=3>{HeavyChain}</td><td rowspan=3>{LightChain}</td></tr>

<tr>
<td bgcolor="#9F8170">{PTML1}</td><td bgcolor="#9F8170">{PTML2}</td><td bgcolor="#9F8170">{PTML3}</td>
<td bgcolor="#9F8170">{PTMH1}</td><td bgcolor="#9F8170">{PTMH2}</td><td bgcolor="#9F8170">{PTMH3}</td></td><td rowspan=2><font color = "#FF0000">{HPTMRisk}</font><br><font color = "#EEAD0E">{MPTMRisk}</font></br></td></td>
<td rowspan=2><font color = "#FF0000">{HighAgg}  </font><font color="#EEAD0E">{MedAgg}  </font><font color="#00FF00">{LowAgg}</font></td><td rowspan=2><a href="{PTMSRC}">PTM</a><br><a href="{HYDSRC}">HYDR</a></br><a href="{PDBSRC}">PDB</a></td>
</tr>

<tr>
<td bgcolor="#4E82b4">{HYDL1}</td><td bgcolor="#4E82b4">{HYDL2}</td><td bgcolor="#4E82b4">{HYDL3}</td>
<td bgcolor="#4E82b4">{HYDH1}</td><td bgcolor="#4E82b4">{HYDH2}</td><td bgcolor="#4E82b4">{HYDH3}</td>
</tr>
"""

PTMSummaryHTML = """<tr  bgcolor="{Color}" align=center><td>{PTMype}</td><td>{CDRLabel}</td><td>{Motif}</td><td>{Residue}</td><td>{SASA}</td><td>{PSASA}</td><td>{Neigh}</td><td>{HalfLife}</td><td>{Risk}</td></tr>
"""

HYDSummaryHTML = """<tr  bgcolor="{Color}" align=center><td>{Risk}</td><td>1{Num}</td><td>{SAP_AREA}</td><td>{SASA}</td><td>{PSASA}</td><td>{HYD_RES_SASA}</td><td>{HYD_RESIDUES}</td></tr>
"""

#Gets sequences and FirstChain and SecondChain name from all .fst files
def getSequences():
    Seq_Dict = {}
    FilePattern = re.compile("""seq_(\d+).*\.fst""")
    FstPattern = re.compile(""">\s*(.*)\n([\s\S]*)\n>\s*(.*)\n([\s\S]*)""")
    for x in glob.glob(FolderPATH+"*.fst"):
        file = open(x, "r")
        data = file.read()
        reg = re.search(FstPattern, data)
        matched = re.search(FilePattern, x)
        if reg and matched:
            SeqNum = int(matched.group(1))
            FirstChainNAME = reg.group(1).lower()
            FirstChainSEQ = reg.group(2)
            SecondChainNAME = reg.group(3).lower()
            SecondChainSEQ = reg.group(4)
            name = dict()
            name["FirstChain"] = FirstChainNAME
            name["FirstChainSeq"] = FirstChainSEQ
            name["SecondChain"] = SecondChainNAME
            name["SecondChainSeq"] = SecondChainSEQ
            Seq_Dict[SeqNum] = name
        else:
            pass
    return Seq_Dict

#Gets CDRs from hydr.txt
def getCDR(fileName):
    CDRinHDR = re.compile("""-*\s*CDRs\s*-*\s*\n\s*CDR definition\s*=\s*CCG\s*\n\s*Number\s*of\s*flanking\s*residues\s*=\s*\d*\s*\n\nCDR_H1\s*(\d+\s*-\s*\d+)\s*:\s*(.+)\nCDR_H2\s*(\d+\s*-\s*\d+)\s*:\s*(.+)\nCDR_H3\s*(\d+\s*-\s*\d+)\s*:\s*(.+)\s*\nCDR_L1\s*(\d+\s*-\s*\d+)\s*:\s*(.+)\nCDR_L2\s*(\d+\s*-\s*\d+)\s*:\s*(.+)\nCDR_L3\s*(\d+\s*-\s*\d+)\s*:\s*(.+)\n\n\n-*Hydrophobic Patch Analysis-*""")
    file = open(fileName, "r")
    data = file.read()
    CDR = re.search(CDRinHDR, data)
    
    #NameOfCDR = [Range(25-99), CDRName(GGTFSSYAIS)]
    #.strip removes trailing whitespace
    H1 = [CDR.group(1).strip(),CDR.group(2).strip()]
    H2 = [CDR.group(3).strip(),CDR.group(4).strip()]
    H3 = [CDR.group(5).strip(),CDR.group(6).strip()]
    L1 = [CDR.group(7).strip(),CDR.group(8).strip()]
    L2 = [CDR.group(9).strip(),CDR.group(10).strip()]
    L3 = [CDR.group(11).strip(),CDR.group(12).strip()]
    
    CDRs = {"H1":H1, "H1":H1, "H2":H2, "H3":H3, "L1":L1, "L2":L2, "L3":L3}
    file.close
    #Returns a dictionary with all CDRs
    return CDRs
   
def getPTMSummary(fileName):
    """Gets the PTM summary"""
    """Returns a 2d list with outer list holding all the row, and inner list holds the row data"""

    PTMPattern = re.compile("""-*PTM\s*SUMMARY-*\nPTMTYPE\s*CDRLabel\s*MOTIF\s*RESIDUE\s*SASA\s*%SASA\s*#Neighbors\s*Half Life\s*RISK \n-*\n((?:.*\n)*)""")
    file = open(fileName, "r")
    data = file.read()
    chunk = re.search(PTMPattern, data)
    block = chunk.group(1)
    lines = block.split('\n')
    LineMatch = re.compile("""(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*""")
    LIST = []
    for line in lines:
        info = re.search(LineMatch, line)
        if info and not line.startswith("-"):
            LineInfo = [info.group(1), info.group(2), info.group(3), info.group(4), info.group(5), info.group(6), info.group(7), info.group(8), info.group(9)]
            LIST.append(LineInfo)
        else:
            pass
    return LIST
    
def getHYDSummary(fileName):
    """Gets the HYD summary"""
    """Returns a 2d list with outer list holding all the row, and inner list holds the row data"""

    HYDPattern = re.compile("""-*HYDROPHOBIC PATCH SUMMARY-*\nRISK\s*NUMBER\s*SAP_AREA\s*SASA\s*%SASA\s*HYD_RES_SASA\s*HYD_RESIDUES\s*-*((.*\n)*)""")
    file = open(fileName, "r")
    data = file.read()
    chunk = re.search(HYDPattern, data)
    block = chunk.group(1)
    lines = block.split('\n')
    LineMatch = re.compile("""(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*(\S+)\s*((?:\S*\s*)*)\s*""")
    LIST = []
    for line in lines:
        info = re.search(LineMatch, line)
        if info and not line.startswith("-") and not line.startswith("Note"):
            LineInfo = [info.group(1), info.group(2), info.group(3), info.group(4), info.group(5), info.group(6), info.group(7).strip()]
            LIST.append(LineInfo)
        else:
            pass
    return LIST
    
def makeFullFastaFiles(SeqDict):
    FirstChainlst = []
    SecondChainlst = []
    for key in SeqDict.keys():
        FirstChainlst.append(">"+SeqDict[key]["FirstChain"])
        FirstChainlst.append(SeqDict[key]["FirstChainSeq"])
        
        SecondChainlst.append(">"+SeqDict[key]["SecondChain"])
        SecondChainlst.append(SeqDict[key]["SecondChainSeq"])
        
    FirstChainfst = "\n".join(FirstChainlst)
    SecondChainfst = "\n".join(SecondChainlst)
    
    with open("FirstChain.fst", "w") as f:
        f.write(FirstChainfst)
        
    with open("SecondChain.fst", "w") as f:
        f.write(SecondChainfst)
        
def makeAlignment(fstFileName):
    #subprocess.call("cd ClustalO")
    subprocess.call("ClustalO\clustalo -i {fileName}.fst --guidetree-out={fileName}.dnd".format(fileName=fstFileName))
    
def makeString(num):
    """Turns the sequence number into a string and adds zeros"""
    num = str(num)
    if len(num) == 1:
        num = "000" + num
    elif len(num) == 2:
        num = "00" + num
    elif len(num) == 3:
        num = "0" + num
    elif len(num) == 4:
        num = "" + num
    return num
    
def highlightLetter(str, indexDict):
    htmSecondChainolor = '<font color="{Color}">{Letter}</font>'
    newStrlst = []
    for x in range(len(str)):
        if x in indexDict:
            newHTML = htmSecondChainolor.format(Color = indexDict[x], Letter = str[x])
            newStrlst.append(newHTML)
        else:
            newStrlst.append(str[x])
    newStr = "".join(newStrlst)
    return newStr

def saveHTML(strToSave, strNameOfFile):
    """Writes the strToSave to a file"""
    file = open(strNameOfFile, "w")
    file.write(strToSave)
    file.close
    
    
def makeHTML():
    #Gets the number and FirstChain, SecondChain data of all the sequences
    Sequences = getSequences()
    #Lists for appending html data
    Tables = []
    Sections = []
    
    makeFullFastaFiles(Sequences)
    makeAlignment("FirstChain")
    makeAlignment("SecondChain")
    
    #Iterates over all the sequences
    for SeqNum in range(len(Sequences)):
        SeqNum = SeqNum+1
        StringSeqNum = makeString(SeqNum)
        Open = HTMLOpening
        #Gets the cdrs from the hydr file
        vPrint("Sequence info"+" "+Sequences[SeqNum]["FirstChain"]+" "+Sequences[SeqNum]["SecondChain"])
        CDRName = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_hydr.txt".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        
        try:
            CDRs = getCDR(CDRName)
        except Exception as e:
            vPrint("Error reading CDRs, continuing")
            continue
        
        #These variables are for risk counters in first table
        HPTMRiskTypes = []
        MPTMRiskTypes = []
        HIHYDPatchNum = 0
        MEHYDPatchNum = 0
        LOHYDPatchNum = 0
        
        PTMSum = getPTMSummary(FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_ptm.txt".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"]))
        PTMHTMLs = []
        HighlightPTMlst = []
        for row in PTMSum:
            PTMrawHTML = PTMSummaryHTML
            #If statement sets the color depending on the risk column
            if row[8] == 'hi':
                riskColor="#FF0000"
                #Nested if appends the risktype to a list if its not already in the list
                if row[0] in HPTMRiskTypes:
                    pass
                else:
                    HPTMRiskTypes.append(row[0])
            elif row[8] == 'low':
                riskColor="#00FF00"
            else:
                riskColor="#EEAD0E"
                #Nested if appends the risktype to a list if its not already in the list
                if row[0] in MPTMRiskTypes:
                    pass
                else:
                    MPTMRiskTypes.append(row[0])
                    
            ResNum = int(re.sub('[^\d]', '', row[3]))
            HighlightPTMlst.append([ResNum, row[1], riskColor])
                    
            #Formats the PTM Table Row html with data
            PTMrawHTML = PTMrawHTML.format(Color=riskColor, PTMype=row[0], CDRLabel=row[1], Motif=row[2], Residue=row[3], SASA=row[4], PSASA=row[5], Neigh=row[6], HalfLife=row[7], Risk=row[8])
            PTMHTMLs.append(PTMrawHTML)
        #Joins all the PTM Table Rows together
        PTMHTML = "\n".join(PTMHTMLs)
        
        PTM_H1_dict = dict()
        PTM_H2_dict = dict()
        PTM_H3_dict = dict()
        PTM_L1_dict = dict()
        PTM_L2_dict = dict()
        PTM_L3_dict = dict()
        
        for t in HighlightPTMlst:
            t[1] = re.sub('CDR_', '', t[1])
            lstRange = CDRs[t[1]][0].split(" - ")
            t[0] = t[0] - int(lstRange[0])
            
            if t[1] == "H1":
                PTM_H1_dict[t[0]] = t[2]
            elif t[1] == "H2":
                PTM_H2_dict[t[0]] = t[2]
            elif t[1] == "H3":
                PTM_H3_dict[t[0]] = t[2]
            elif t[1] == "L1":
                PTM_L1_dict[t[0]] = t[2]
            elif t[1] == "L2":
                PTM_L2_dict[t[0]] = t[2]
            elif t[1] == "L3":
                PTM_L3_dict[t[0]] = t[2]
            
        
        #Highlights the correct CDRs
        PTM_H1 = highlightLetter(CDRs["H1"][1], PTM_H1_dict)
        PTM_H2 = highlightLetter(CDRs["H2"][1], PTM_H2_dict)
        PTM_H3 = highlightLetter(CDRs["H3"][1], PTM_H3_dict)
        PTM_L1 = highlightLetter(CDRs["L1"][1], PTM_L1_dict)
        PTM_L2 = highlightLetter(CDRs["L2"][1], PTM_L2_dict)
        PTM_L3 = highlightLetter(CDRs["L3"][1], PTM_L3_dict)
        
        
        #Joins the risktypes together with a \n
        HPTMRiskType = "\n".join(HPTMRiskTypes)
        MPTMRiskType = "\n".join(MPTMRiskTypes)
        
        HYDSum = getHYDSummary(FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_hydr.txt".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"]))
        HYDHTMLs = []
        HighlightHYDlst = []
        for row in HYDSum:
            HYDrawHTML = HYDSummaryHTML
            #If statement sets the color depending on the risk column
            if row[0] == 'hi':
                riskColor="#FF0000"
                #Increases the hi risk counter by 1
                HIHYDPatchNum = HIHYDPatchNum + 1
            elif row[0] == 'low':
                riskColor="#00FF00"
                #Increases the low risk counter by 1
                LOHYDPatchNum = LOHYDPatchNum + 1
            else:
                riskColor="#EEAD0E"
                #Increases the med risk counter by 1
                MEHYDPatchNum = MEHYDPatchNum + 1
                
            resdisues = row[6].split()
            
            
            H1_Range = CDRs["H1"][0].split(" - ")
            H2_Range = CDRs["H2"][0].split(" - ")
            H3_Range = CDRs["H3"][0].split(" - ")
            L1_Range = CDRs["L1"][0].split(" - ")
            L2_Range = CDRs["L2"][0].split(" - ")
            L3_Range = CDRs["L3"][0].split(" - ")
            for residue in resdisues:
                ResNum = int(re.sub('[^\d]', '', residue))
                ResType = residue.split(".")[0]
                if ResType == "h":
                    if ResNum >= int(H1_Range[0]) and ResNum <= int(H1_Range[1]):
                        ResNum = ResNum - int(H1_Range[0])
                        HighlightHYDlst.append([ResNum, "H1", riskColor])
                    elif ResNum >= int(H2_Range[0]) and ResNum <= int(H2_Range[1]):
                        ResNum = ResNum - int(H2_Range[0])
                        HighlightHYDlst.append([ResNum, "H2", riskColor])
                    elif ResNum >= int(H3_Range[0]) and ResNum <= int(H3_Range[1]):
                        ResNum = ResNum - int(H3_Range[0])
                        HighlightHYDlst.append([ResNum, "H3", riskColor])
                    else:
                        vPrint("Non CDR Residue"+" "+ResType+" "+str(ResNum))
                elif ResType == "l":
                    if ResNum >= int(L1_Range[0]) and ResNum <= int(L1_Range[1]):
                        ResNum = ResNum - int(L1_Range[0])
                        HighlightHYDlst.append([ResNum, "L1", riskColor])
                    elif ResNum >= int(L2_Range[0]) and ResNum <= int(L2_Range[1]):
                        ResNum = ResNum - int(L2_Range[0])
                        HighlightHYDlst.append([ResNum, "L2", riskColor])
                    elif ResNum >= int(L3_Range[0]) and ResNum <= int(L3_Range[1]):
                        ResNum = ResNum - int(L3_Range[0])
                        HighlightHYDlst.append([ResNum, "L3", riskColor])
                    else:
                        vPrint("Non CDR Residue"+" "+ResType+" "+str(ResNum))
                
            #Formats the HYD Table Row html with data
            HYDrawHTML = HYDrawHTML.format(Color=riskColor, Risk=row[0], Num=row[1], SAP_AREA=row[2], SASA=row[3], PSASA=row[4], HYD_RES_SASA=row[5], HYD_RESIDUES=row[6])
            HYDHTMLs.append(HYDrawHTML)
            
        HYD_H1_dict = dict()
        HYD_H2_dict = dict()
        HYD_H3_dict = dict()
        HYD_L1_dict = dict()
        HYD_L2_dict = dict()
        HYD_L3_dict = dict()
        
        
        for t in HighlightHYDlst:           
            if t[1] == "H1":
                HYD_H1_dict[t[0]] = t[2]
            elif t[1] == "H2":
                HYD_H2_dict[t[0]] = t[2]
            elif t[1] == "H3":
                HYD_H3_dict[t[0]] = t[2]
            elif t[1] == "L1":
                HYD_L1_dict[t[0]] = t[2]
            elif t[1] == "L2":
                HYD_L2_dict[t[0]] = t[2]
            elif t[1] == "L3":
                HYD_L3_dict[t[0]] = t[2]
            
        
        #Highlights the correct CDRs
        HYD_H1 = highlightLetter(CDRs["H1"][1], HYD_H1_dict)
        HYD_H2 = highlightLetter(CDRs["H2"][1], HYD_H2_dict)
        HYD_H3 = highlightLetter(CDRs["H3"][1], HYD_H3_dict)
        HYD_L1 = highlightLetter(CDRs["L1"][1], HYD_L1_dict)
        HYD_L2 = highlightLetter(CDRs["L2"][1], HYD_L2_dict)
        HYD_L3 = highlightLetter(CDRs["L3"][1], HYD_L3_dict)
            
        #Joins all the HYD Table Rows together
        HYDHTML = "\n".join(HYDHTMLs)
        
        
        #Creates path for images
        i1 = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_ptm.png".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        i2 = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_sap.png".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        
        #Formats section html with data
        Section = SectionHTML
        Section = Section.format(SeqNum=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], 
                                 SecondChain=Sequences[SeqNum]["SecondChain"], PTMTable=PTMHTML, 
                                 HYDTable=HYDHTML, img1=i1, img2=i2)
        
        #Appends this section to a list
        Sections.append(Section)
        
        #Creates paths for raw files
        ptmSRC = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_ptm.txt".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        hydSRC = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_hydr.txt".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        pdbSRC = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}.pdb".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        
        Open = Open.format(SeqNum=StringSeqNum, DispSeqNum=StringSeqNum, 
                           HeavyChain=Sequences[SeqNum]["FirstChain"], LightChain=Sequences[SeqNum]["SecondChain"], 
                           PTMH1=PTM_H1, PTMH2=PTM_H2, PTMH3=PTM_H3, 
                           PTML1=PTM_L1, PTML2=PTM_L2, PTML3=PTM_L3,
                           HYDH1=HYD_H1, HYDH2=HYD_H2, HYDH3=HYD_H3, 
                           HYDL1=HYD_L1, HYDL2=HYD_L2, HYDL3=HYD_L3,
                           HPTMRisk=HPTMRiskType, MPTMRisk=MPTMRiskType,
                           HighAgg=HIHYDPatchNum, MedAgg=MEHYDPatchNum, LowAgg=LOHYDPatchNum, PTMSRC=ptmSRC, 
                           HYDSRC=hydSRC, PDBSRC=pdbSRC)
        Tables.append(Open)
        
            
    #Joins the list into a string with a newline character between them
    Section = "\n".join(Sections)
    Table = "\n".join(Tables)
    return [Table, Section]

    
#dirname is for subtitle name, gets the parent directory of the files
dirname = ""
if FolderPATH == "":
    dirname = os.path.abspath('')
    dirnamelst = dirname.split("\\")
    dirname = dirnamelst[-1]
else:
    dirname = FolderPATH
    dirnamelst = dirname.split("/")
    dirname = dirnamelst[-2]
    
TablesFinal = makeHTML()
Base = BaseHTML
Base = Base.format(DirName=dirname, OpenTable=TablesFinal[0], Sections=TablesFinal[1])
saveHTML(Base, FinalFileName)
