import glob
import os
import re


#Path to folder with the files, relative to where the python file is
#Leave blank if python file is in same place
FolderPATH = "../output_m71derived_togo/output_m71derived_togo/"
#Name of HTML File
FinalFileName = "Web-Report.html"

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
            <tr align=center><td colspan=2><b>Seq</b></td><td colspan=4><b>Heavy Chain</b></td><td colspan=4><b>Light Chain</b></td><td colspan=4><b>L1</b></td><td colspan=4><b>L2</b></td><td colspan=4><b>L3</b></td>
                                                                                                     <td colspan=4><b>H1</b></td><td colspan=4><b>H2</b></td><td colspan=4><b>H3</b></td><td colspan=4><b>PTM Risk</b></td><td colspan=4><b>Aggregate Risk</b></td><td colspan=4><b>RAW Files</b></td></tr>
                                                                                       
            {OpenTable}
            </table>
        </section>
        {Sections}

    </body>
</html>
"""

SectionHTML = """
<section>
            <h1 align=center style="font: 20pt Times New Roman"><A NAME="Seq{SeqNum}"><b>Sequence {SeqNum} - {HC}_hc - {LC}_lc</b></h1></A>
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


</section>

"""


HTMLOpening = """<tr align=center><td colspan=2><A HREF="#Seq{SeqNum}">{DispSeqNum}</A></td><td colspan=4>{HeavyChain}</td><td colspan=4>{LightChain}</td><td colspan=4>{L1}</td><td colspan=4>{L2}</td><td colspan=4>{L3}</td>
                                                                             <td colspan=4>{H1}</td><td colspan=4>{H2}</td><td colspan=4>{H3}</td></td><td colspan=4><font color = "#FF0000">{HPTMRisk}</font><br><font color = "#EEAD0E">{MPTMRisk}</font></br></td></td><td colspan=4><font color = "#FF0000">{HighAgg}  </font><font color="#EEAD0E">{MedAgg}  </font><font color="#00FF00">{LowAgg}</font></td><td><a href="{PTMSRC}">PTM</a><br><a href="{HYDSRC}">HYDR</a></br><a href="{PDBSRC}">PDB</a></td></tr>
"""

PTMSummaryHTML = """<tr  bgcolor="{Color}" align=center><td>{PTMype}</td><td>{CDRLabel}</td><td>{Motif}</td><td>{Residue}</td><td>{SASA}</td><td>{PSASA}</td><td>{Neigh}</td><td>{HalfLife}</td><td>{Risk}</td></tr>
"""

HYDSummaryHTML = """<tr  bgcolor="{Color}" align=center><td>{Risk}</td><td>1{Num}</td><td>{SAP_AREA}</td><td>{SASA}</td><td>{PSASA}</td><td>{HYD_RES_SASA}</td><td>{HYD_RESIDUES}</td></tr>
"""

#Gets sequences and HC and LC name from all .fst files
def getSequences():
    Seq_Dict = {}
    FilePattern = re.compile("""seq_(\d+)_(.+)_hc_(.+)_lc\.fst""")
    for x in glob.glob(FolderPATH+"*lc.fst"):
        print("glob is "+x)
        matched = re.search(FilePattern, x)
        if matched:
            SeqNum = int(matched.group(1))
            HCNAME = matched.group(2)
            LCNAME = matched.group(3)
            name = dict()
            name["HC"] = HCNAME
            name["LC"] = LCNAME
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
    return CDRs
   
def getPTMSummary(fileName):
    PTMPattern = re.compile("""-*PTM\s*SUMMARY-*\nPTMTYPE\s*CDRLabel\s*MOTIF\s*RESIDUE\s*SASA\s*%SASA\s*#Neighbors\s*Half Life\s*RISK \n-*\n((.*\n)*)""")
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
    
def makeString(num):
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

def saveHTML(strToSave, strNameOfFile):
    file = open(strNameOfFile, "w")
    file.write(strToSave)
    file.close
    
def makeHTML():
    Sequences = getSequences()
    Tables = []
    Sections = []
    for SeqNum in range(len(Sequences)):
        SeqNum = SeqNum+1
        StringSeqNum = makeString(SeqNum)
        Open = HTMLOpening
        CDRName = FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_hydr.txt".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"])
        CDRs = getCDR(CDRName)
        
        #These variables are for risk counters in first table
        HPTMRiskTypes = []
        MPTMRiskTypes = []
        HIHYDPatchNum = 0
        MEHYDPatchNum = 0
        LOHYDPatchNum = 0
        
        
        PTMSum = getPTMSummary(FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_ptm.txt".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"]))
        PTMHTMLs = []
        for row in PTMSum:
            PTMrawHTML = PTMSummaryHTML
            if row[8] == 'hi':
                riskColor="#FF0000"
                if row[0] in HPTMRiskTypes:
                    pass
                else:
                    HPTMRiskTypes.append(row[0])
            elif row[8] == 'low':
                riskColor="#00FF00"
            else:
                riskColor="#EEAD0E"
                if row[0] in MPTMRiskTypes:
                    pass
                else:
                    MPTMRiskTypes.append(row[0])
            PTMrawHTML = PTMrawHTML.format(Color=riskColor, PTMype=row[0], CDRLabel=row[1], Motif=row[2], Residue=row[3], SASA=row[4], PSASA=row[5], Neigh=row[6], HalfLife=row[7], Risk=row[8])
            PTMHTMLs.append(PTMrawHTML)
        PTMHTML = "\n".join(PTMHTMLs)
        HPTMRiskType = "\n".join(HPTMRiskTypes)
        MPTMRiskType = "\n".join(MPTMRiskTypes)
        
        HYDSum = getHYDSummary(FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_hydr.txt".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"]))
        HYDHTMLs = []
        for row in HYDSum:
            HYDrawHTML = HYDSummaryHTML
            if row[0] == 'hi':
                riskColor="#FF0000"
                HIHYDPatchNum = HIHYDPatchNum + 1
            elif row[0] == 'low':
                riskColor="#00FF00"
                LOHYDPatchNum = LOHYDPatchNum + 1
            else:
                riskColor="#EEAD0E"
                MEHYDPatchNum = MEHYDPatchNum + 1
            HYDrawHTML = HYDrawHTML.format(Color=riskColor, Risk=row[0], Num=row[1], SAP_AREA=row[2], SASA=row[3], PSASA=row[4], HYD_RES_SASA=row[5], HYD_RESIDUES=row[6])
            HYDHTMLs.append(HYDrawHTML)
        HYDHTML = "\n".join(HYDHTMLs)
        
        
        Section = SectionHTML
        i1 = FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_ptm.png".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"])
        i2 = FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_sap.png".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"])
        Section = Section.format(SeqNum=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"], PTMTable=PTMHTML, HYDTable=HYDHTML, img1=i1, img2=i2)
        Sections.append(Section)
        
        ptmSRC = FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_ptm.txt".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"])
        hydSRC = FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_hydr.txt".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"])
        pdbSRC = FolderPATH+"seq_{Num}_{HC}_hc_{LC}_lc_.pdb".format(Num=StringSeqNum, HC=Sequences[SeqNum]["HC"], LC=Sequences[SeqNum]["LC"])
        
        Open = Open.format(SeqNum=StringSeqNum, DispSeqNum=StringSeqNum, HeavyChain=Sequences[SeqNum]["HC"], LightChain=Sequences[SeqNum]["LC"], H1=CDRs["H1"][1], H2=CDRs["H2"][1], H3=CDRs["H3"][1], L1=CDRs["L1"][1], L2=CDRs["L2"][1], L3=CDRs["L3"][1], HPTMRisk=HPTMRiskType, MPTMRisk=MPTMRiskType, HighAgg=HIHYDPatchNum, MedAgg=MEHYDPatchNum, LowAgg=LOHYDPatchNum, PTMSRC=ptmSRC, HYDSRC=hydSRC, PDBSRC=pdbSRC)
        Tables.append(Open)
        
            
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
    dirnamelst = dirname.split("\\")
    dirname = dirnamelst[-1]
    
TablesFinal = makeHTML()
Base = BaseHTML
Base = Base.format(DirName=dirname, OpenTable=TablesFinal[0], Sections=TablesFinal[1])
saveHTML(Base, FinalFileName)