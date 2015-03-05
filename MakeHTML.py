import glob
import os
import re
import math
import sys
import argparse
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument("-v", "--verbose", help="increase output verbosity", action="store_true")
parser.add_argument("--phylo", help="increase output verbosity", action="store_true", default=False)
parser.add_argument("-g", "--germ", help="increase output verbosity", action="store_true", default=False)
parser.add_argument("-p", "--path", help="Path to folder with reports, (change '\\' to '/') end the string with a '/' \n leave blank for root directory", default="")
parser.add_argument("-o", "--output", help="Name of output html file, leave blank for default", default="Web-Report.html")
args = parser.parse_args()

if args.phylo is True:
    from Bio import Phylo


#Path to folder with the files, relative to where the python file is
#Leave blank if python file is in same place
#End the path with a '/'
FolderPATH = args.path  # #"../output_m71derived_togo/output_m71derived_togo/"
#FolderPATH = "../output_ama1_togo/output_ama1_togo/"
#FolderPATH = "../output_m71_germ_derived/output_m71derived/"

print('FolderPATH = '+FolderPATH ) 

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
            
            {PhyloHeader}
            </table>
        </section>
        {Sections}

        {PhyloBody}
    </body>
</html>
"""

PhyloHeader = """<div align=center><A HREF="#FirstChainPhylo">Go To first phylo tree</a></div>
<div align=center><A HREF="#SecondChainPhylo">Go To second phylo tree</a></div>
"""

PhyloBody = """<div align=center style="font: 15pt Times New Roman"><A NAME="FirstChainPhylo"><b>FirstChain Phylogenetic Tree</b></div>
<img height=500 align=center src="{phylo1}" border=0>
<div align=center style="font: 15pt Times New Roman"><A NAME="SecondChainPhylo"><b>SecondChain Phylogenetic Tree</b></div>
<img height=500 align=center src="{phylo2}" border=0>
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
            
            {GermHTML}            
            <div align=center><A HREF="#top">Back to Top</a></div>
            
            
            <img height=300 align=center src="{img1}" border=0>
            
            <img height=300 align=center src="{img2}" border=0>

    <hr> 

</section>

"""

GermHTML = """<table align=center width=820 cellspacing=2 cellpadding=4 border=0>

            <h2 style="font: 16pt Times New Roman" align=center><td><b>LC</b></h2>
            <tr bgcolor="#C0C0C0" align=center><td>Name</td><td>Sequence</td><td>Count</td></tr>
            {LCGermTable}
            
            <h2 style="font: 16pt Times New Roman" align=center colspan=10><td><b>HC</b></h2>
            <tr bgcolor="#C0C0C0" align=center><td>Name</td><td>Sequence</td><td>Count</td></tr>
            {HCGermTable}
            </table>
            """
            
GermRow = """<tr bgcolor="#d3d3d3" align=left style="font-family: Courier New"><td>{Name}</td><td align=left style="font-family: Courier New">{Sequence}</td><td align=left style="font-family: Courier New">{Count}</td></tr>"""


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




#The draw() function is modified from the Biopython source code save the picture instead of showing it
def draw(tree, label_func=str, fileName='default', do_show=True, show_confidence=True,
         # For power users
         axes=None, branch_labels=None, *args, **kwargs):
    """Plot the given tree using matplotlib (or pylab).
    The graphic is a rooted tree, drawn with roughly the same algorithm as
    draw_ascii.
    Additional keyword arguments passed into this function are used as pyplot
    options. The input format should be in the form of:
    pyplot_option_name=(tuple), pyplot_option_name=(tuple, dict), or
    pyplot_option_name=(dict).
    Example using the pyplot options 'axhspan' and 'axvline':
    >>> Phylo.draw(tree, axhspan=((0.25, 7.75), {'facecolor':'0.5'}),
    ...     axvline={'x':'0', 'ymin':'0', 'ymax':'1'})
    Visual aspects of the plot can also be modified using pyplot's own functions
    and objects (via pylab or matplotlib). In particular, the pyplot.rcParams
    object can be used to scale the font size (rcParams["font.size"]) and line
    width (rcParams["lines.linewidth"]).
    :Parameters:
        label_func : callable
            A function to extract a label from a node. By default this is str(),
            but you can use a different function to select another string
            associated with each node. If this function returns None for a node,
            no label will be shown for that node.
        do_show : bool
            Whether to show() the plot automatically.
        show_confidence : bool
            Whether to display confidence values, if present on the tree.
        axes : matplotlib/pylab axes
            If a valid matplotlib.axes.Axes instance, the phylogram is plotted
            in that Axes. By default (None), a new figure is created.
        branch_labels : dict or callable
            A mapping of each clade to the label that will be shown along the
            branch leading to it. By default this is the confidence value(s) of
            the clade, taken from the ``confidence`` attribute, and can be
            easily toggled off with this function's ``show_confidence`` option.
            But if you would like to alter the formatting of confidence values,
            or label the branches with something other than confidence, then use
            this option.
    """

    try:
        import matplotlib.pyplot as plt
    except ImportError:
        try:
            import pylab as plt
        except ImportError:
            from Bio import MissingPythonDependencyError
            raise MissingPythonDependencyError(
                "Install matplotlib or pylab if you want to use draw.")

    import matplotlib.collections as mpcollections

    # Arrays that store lines for the plot of clades
    horizontal_linecollections = []
    vertical_linecollections = []

    # Options for displaying branch labels / confidence
    def conf2str(conf):
        if int(conf) == conf:
            return str(int(conf))
        return str(conf)
    if not branch_labels:
        if show_confidence:
            def format_branch_label(clade):
                if hasattr(clade, 'confidences'):
                    # phyloXML supports multiple confidences
                    return '/'.join(conf2str(cnf.value)
                                    for cnf in clade.confidences)
                if clade.confidence:
                    return conf2str(clade.confidence)
                return None
        else:
            def format_branch_label(clade):
                return None
    elif isinstance(branch_labels, dict):
        def format_branch_label(clade):
            return branch_labels.get(clade)
    else:
        assert callable(branch_labels), \
            "branch_labels must be either a dict or a callable (function)"
        format_branch_label = branch_labels

    # Layout

    def get_x_positions(tree):
        """Create a mapping of each clade to its horizontal position.
        Dict of {clade: x-coord}
        """
        depths = tree.depths()
        # If there are no branch lengths, assume unit branch lengths
        if not max(depths.values()):
            depths = tree.depths(unit_branch_lengths=True)
        return depths

    def get_y_positions(tree):
        """Create a mapping of each clade to its vertical position.
        Dict of {clade: y-coord}.
        Coordinates are negative, and integers for tips.
        """
        maxheight = tree.count_terminals()
        # Rows are defined by the tips
        heights = dict((tip, maxheight - i)
                       for i, tip in enumerate(reversed(tree.get_terminals())))

        # Internal nodes: place at midpoint of children
        def calc_row(clade):
            for subclade in clade:
                if subclade not in heights:
                    calc_row(subclade)
            # Closure over heights
            heights[clade] = (heights[clade.clades[0]] +
                              heights[clade.clades[-1]]) / 2.0

        if tree.root.clades:
            calc_row(tree.root)
        return heights

    x_posns = get_x_positions(tree)
    y_posns = get_y_positions(tree)
    # The function draw_clade closes over the axes object
    if axes is None:
        fig = plt.figure()
        axes = fig.add_subplot(1, 1, 1)
    elif not isinstance(axes, plt.matplotlib.axes.Axes):
        raise ValueError("Invalid argument for axes: %s" % axes)

    def draw_clade_lines(use_linecollection=False, orientation='horizontal',
                         y_here=0, x_start=0, x_here=0, y_bot=0, y_top=0,
                         color='black', lw='.1'):
        """Create a line with or without a line collection object.
        Graphical formatting of the lines representing clades in the plot can be
        customized by altering this function.
        """
        if (use_linecollection is False and orientation == 'horizontal'):
            axes.hlines(y_here, x_start, x_here, color=color, lw=lw)
        elif (use_linecollection is True and orientation == 'horizontal'):
            horizontal_linecollections.append(mpcollections.LineCollection(
                [[(x_start, y_here), (x_here, y_here)]], color=color, lw=lw),)
        elif (use_linecollection is False and orientation == 'vertical'):
            axes.vlines(x_here, y_bot, y_top, color=color)
        elif (use_linecollection is True and orientation == 'vertical'):
            vertical_linecollections.append(mpcollections.LineCollection(
                [[(x_here, y_bot), (x_here, y_top)]], color=color, lw=lw),)

    def draw_clade(clade, x_start, color, lw):
        """Recursively draw a tree, down from the given clade."""
        x_here = x_posns[clade]
        y_here = y_posns[clade]
        # phyloXML-only graphics annotations
        if hasattr(clade, 'color') and clade.color is not None:
            color = clade.color.to_hex()
        if hasattr(clade, 'width') and clade.width is not None:
            lw = clade.width * plt.rcParams['lines.linewidth']
        # Draw a horizontal line from start to here
        draw_clade_lines(use_linecollection=True, orientation='horizontal',
                         y_here=y_here, x_start=x_start, x_here=x_here, color=color, lw=lw)
        # Add node/taxon labels
        label = label_func(clade)
        if label not in (None, clade.__class__.__name__):
            axes.text(x_here, y_here, ' %s' %
                      label, verticalalignment='center')
        # Add label above the branch (optional)
        conf_label = format_branch_label(clade)
        if conf_label:
            axes.text(0.5 * (x_start + x_here), y_here, conf_label,
                      fontsize='small', horizontalalignment='center')
        if clade.clades:
            # Draw a vertical line connecting all children
            y_top = y_posns[clade.clades[0]]
            y_bot = y_posns[clade.clades[-1]]
            # Only apply widths to horizontal lines, like Archaeopteryx
            draw_clade_lines(use_linecollection=True, orientation='vertical',
                             x_here=x_here, y_bot=y_bot, y_top=y_top, color=color, lw=lw)
            # Draw descendents
            for child in clade:
                draw_clade(child, x_here, color, lw)

    draw_clade(tree.root, 0, 'k', plt.rcParams['lines.linewidth'])

    # If line collections were used to create clade lines, here they are added
    # to the pyplot plot.
    for i in horizontal_linecollections:
        axes.add_collection(i)
    for i in vertical_linecollections:
        axes.add_collection(i)

    # Aesthetics

    if hasattr(tree, 'name') and tree.name:
        axes.set_title(tree.name)
    axes.set_xlabel('branch length')
    axes.set_ylabel('taxa')
    # Add margins around the tree to prevent overlapping the axes
    xmax = max(x_posns.values())
    axes.set_xlim(-0.05 * xmax, 1.25 * xmax)
    # Also invert the y-axis (origin at the top)
    # Add a small vertical margin, but avoid including 0 and N+1 on the y axis
    axes.set_ylim(max(y_posns.values()) + 0.8, 0.2)

    # Parse and process key word arguments as pyplot options
    for key, value in kwargs.items():
        try:
            # Check that the pyplot option input is iterable, as required
            [i for i in value]
        except TypeError:
            raise ValueError('Keyword argument "%s=%s" is not in the format '
                             'pyplot_option_name=(tuple), pyplot_option_name=(tuple, dict),'
                             ' or pyplot_option_name=(dict) '
                             % (key, value))
        if isinstance(value, dict):
            getattr(plt, str(key))(**dict(value))
        elif not (isinstance(value[0], tuple)):
            getattr(plt, str(key))(*value)
        elif (isinstance(value[0], tuple)):
            getattr(plt, str(key))(*value[0], **dict(value[1]))

    if do_show:
        plt.savefig(fileName)
        plt.close()
        #plt.show()


def makePhylo():
    firstTree = Phylo.read('FirstChain.dnd', 'newick')
    secondTree = Phylo.read('SecondChain.dnd', 'newick')
    
    draw(firstTree, fileName=FolderPATH+'FirstChain.png')
    draw(secondTree, fileName=FolderPATH+'SecondChain.png')


#Gets sequences and FirstChain and SecondChain name from all .fst files
def getSequences():
    Seq_Dict = {}
    FilePattern = re.compile("""seq_(\d+).*\.fst""")
    FstPattern = re.compile(""">\s*(.*)\n([\s\S]*)\n>\s*(.*)\n([\s\S]*)""")
    GermPattern = re.compile(""".*germ[hc|lc].*""")
    vPrint('in getSequences .. ') 
    for x in glob.glob(FolderPATH+"*.fst"):
        vPrint (x) 
        file = open(x, "r")
        data = file.read()
        reg = re.search(FstPattern, data)
        matched = re.search(FilePattern, x)
        germ = re.search(GermPattern, x)

        if reg and matched and not germ:
            SeqNum = int(matched.group(1))
            FirstChainNAME = reg.group(1).replace(" ","").lower().strip() 
            FirstChainSEQ = reg.group(2)
            SecondChainNAME = reg.group(3).replace(" ","").lower().strip() 
            SecondChainSEQ = reg.group(4)
            vPrint( "FirstChainName="+FirstChainNAME+"<end>" ) 
            vPrint( "SecondChainNAME="+SecondChainNAME+"<end>" ) 
            name = dict()
            name["FirstChain"] = FirstChainNAME
            name["FirstChainSeq"] = FirstChainSEQ
            name["SecondChain"] = SecondChainNAME
            name["SecondChainSeq"] = SecondChainSEQ
            Seq_Dict[SeqNum] = name
        else:
            pass
    vPrint('getSequences done.') 
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
    
def getGermData(fileName):
    file = open(fileName, "r")
    data = file.read()
    single_match = """>\s*(.*)\n(.*)"""
    
    all_list = data.split("\n")
    seq_dict = dict()

    for n in range(0,len(all_list),2):
        try:
            seq_dict[all_list[n][1:].strip().lower()] = all_list[n+1]
        except Exception as e:
            vPrint("Error getting germline data")
    seq_dict["Seq"] = all_list[0][1:].strip().lower()
    return seq_dict
    
def findDiff(germ_dict):
    seq_name = germ_dict["Seq"]
    seq = germ_dict[seq_name]
    indexes = []
    affected_keys_and_indexes = dict()
    for char_pos in range(len(seq)-1):
        for key in germ_dict:
            if key == seq_name or key == "Seq":
                continue
            vPrint("+CharPos "+str(char_pos))
            try:
                if germ_dict[key][char_pos] is not seq[char_pos]:
                    if char_pos not in indexes:
                        indexes.append(char_pos)
                    if key not in affected_keys_and_indexes:
                        affected_keys_and_indexes[key] = [char_pos]
                    else:
                        affected_keys_and_indexes[key].append(char_pos)
            except Exception as e:
                vPrint("Index out of bounds in germ line sequences")
    return [indexes, affected_keys_and_indexes]

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
    try:
        subprocess.call("ClustalO\clustalo -i {fileName}.fst --guidetree-out={fileName}.dnd --distmat-out={fileName}distmattest.txt --force --full".format(fileName=fstFileName))
    except:
        print("Error make sure ClustalO is installed in the ClustalO subfolder")
    
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
    
def highlightLetter(str, indexDict, highlight=False):
    htmSecondChainColor = '<font color="{Color}">{Letter}</font>'
    htmBackgroundColor = '<span style="background-color: {Color}">{Letter}</span>'
    newStrlst = []
    for x in range(len(str)):
        if x in indexDict:
            if highlight is True:
                newHTML = htmBackgroundColor.format(Color = indexDict[x], Letter = str[x])
            if highlight is False:
                newHTML = htmSecondChainColor.format(Color = indexDict[x], Letter = str[x])
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

    
    if args.phylo is True:
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
        print("CDR is ",Sequences[SeqNum]["SecondChain"])
        
        try:
            CDRs = getCDR(CDRName)
        except Exception as e:
            vPrint("Error reading CDRs, continuing")
            vPrint(e)
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
        
        #Get germ data
        Germ_html = ""
        if args.germ:
            germ_lc_path = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_germlc.fst".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
            germ_hc_path = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_germhc.fst".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
            
            germ_lc = getGermData(germ_lc_path)
            germ_hc = getGermData(germ_hc_path)
            
            diff_lc = findDiff(germ_lc)
            diff_hc = findDiff(germ_hc)
            
            germ_lc_indexDict = {}
            germ_hc_indexDict = {}
            
                        
            for index in diff_lc[0]:
                germ_lc_indexDict[index] = "#FF0000"
            for index in diff_hc[0]:
                germ_hc_indexDict[index] = "#FF0000"
                
            LC_GERM_TABLE = []
            germ_lc[germ_lc["Seq"]] = highlightLetter(germ_lc[germ_lc["Seq"]], germ_lc_indexDict)
            LC_GERM_TABLE.append(GermRow.format(Name=germ_lc["Seq"], Sequence=germ_lc[germ_lc["Seq"]], Count=germ_lc[germ_lc["Seq"]].count('<span style="background-color: #ff0000">')))
            if germ_lc["Seq"] in germ_lc: del germ_lc[germ_lc["Seq"]]
            if "Seq" in germ_lc: del germ_lc["Seq"]
            custom_indexDict = germ_lc_indexDict
            for key in germ_lc:
                if key is not "Seq":
                    highlight=False
                    if key in diff_lc[1]:
                        indexes = diff_lc[1][key]
                        for k in custom_indexDict:
                            highlight=False
                            if k in indexes:
                                custom_indexDict[k] = "#ff0000"
                                highlight=True
                            else:
                                highlight=False
                    germ_lc[key] = highlightLetter(germ_lc[key], custom_indexDict, highlight)
                else:
                    continue
                print("Key is: "+key)
                try:
                    LC_GERM_TABLE.append(GermRow.format(Name=key.split("|")[1], Sequence=germ_lc[key], Count=germ_lc[key].count('<span style="background-color: #ff0000">')))
                except Exception as e:
                    vPrint("Key Error, Key is ("+key+"), it might be blank")
            HC_GERM_TABLE = []
            germ_hc[germ_hc["Seq"]] = highlightLetter(germ_hc[germ_hc["Seq"]], germ_hc_indexDict)
            HC_GERM_TABLE.append(GermRow.format(Name=germ_hc["Seq"], Sequence=germ_hc[germ_hc["Seq"]], Count=germ_hc[germ_hc["Seq"]].count('<span style="background-color: #ff0000">')))
            if germ_hc["Seq"] in germ_hc: del germ_hc[germ_hc["Seq"]]
            if "Seq" in germ_hc: del germ_hc["Seq"]
            custom_indexDict = germ_hc_indexDict
            for key in germ_hc:
                if key is not "Seq":
                    high=False
                    if key in diff_hc[1]:
                        indexes = diff_hc[1][key]
                        for k in custom_indexDict:
                            high=False
                            if k in indexes:
                                custom_indexDict[k] = "#ff0000"
                                high=True
                            else:
                                high=False
                    germ_hc[key] = highlightLetter(germ_hc[key], custom_indexDict, high)
                else:
                    continue
                try:
                    HC_GERM_TABLE.append(GermRow.format(Name=key.split("|")[1], Sequence=germ_hc[key], Count=germ_hc[key].count('<span style="background-color: #ff0000">')))
                except Exception as e:
                    vPrint("Key Error, Key is ("+key+"), it might be blank")
            GERM_LC = "\n".join(LC_GERM_TABLE)
            GERM_HC = "\n".join(HC_GERM_TABLE)
            
            Germ_html = GermHTML.format(LCGermTable=GERM_LC, HCGermTable=GERM_HC)

        
        #Creates path for images
        i1 = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_ptm.png".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        i2 = FolderPATH+"seq_{Num}_{FirstChain}_{SecondChain}_sap.png".format(Num=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], SecondChain=Sequences[SeqNum]["SecondChain"])
        
        #Formats section html with data
        Section = SectionHTML
        Section = Section.format(SeqNum=StringSeqNum, FirstChain=Sequences[SeqNum]["FirstChain"], 
                                 SecondChain=Sequences[SeqNum]["SecondChain"], PTMTable=PTMHTML, 
                                 HYDTable=HYDHTML, img1=i1, img2=i2, GermHTML=Germ_html)
        
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
if args.phylo:
    PH = PhyloHeader
    PB = PhyloBody.format(phylo1=FolderPATH+"FirstChain.png", phylo2=FolderPATH+"SecondChain.png")
else:
    PH = ''
    PB = ''
Base = Base.format(DirName=dirname, OpenTable=TablesFinal[0], Sections=TablesFinal[1],
                   PhyloHeader=PH, PhyloBody=PB)
saveHTML(Base, FinalFileName)

