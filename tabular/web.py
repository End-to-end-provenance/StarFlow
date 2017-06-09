"""
Functions for creating HTML representations of tabular data.

"""



import sys
import cgi
from os import getcwd
from os.path import splitext, basename, isdir, dirname

import numpy as np

import tabular as tb
import tabular.utils as utils
import tempfile
from tabular.colors import Point2HexColor

__all__ = ['tabular2html']

def tabular2html(fname=None, X=None, fin=None, title=None, printheader=False, 
                 split=True, usecss=None, writecss=None, SERVERNAME=None, 
                 SERVER_FROM_CURDIR='../', ROWS_PER_PAGE=1000, 
                 returnstring = False, **kwargs):
    """
    Creates an html representation of tabular data, either from a tabarray or 
    an externa file (`including ``.hsv``, ``.csv``, ``.tsv``).  If no data is 
    directly provided by passing a tabarray to `X`, then a tabarray is 
    constructed using :func:`tabular.tabarray.tabarray.__new__`.

    **Parameters**

            **fname** :  string

                    Path to the "main" HTML file to be created.  This file path
                    must end in ``.html``.

                    Note that this function will create additional files (e.g. 
                    a ``.css`` file and multiple linked ``.html`` files for 
                    large datasets) linked to this HTML file, inside of the 
                    directory containing `fname`.

            **X** :  tabarray

                    If `X` is `None`, then one of `fin`, `array`, `records`,
                    `columns`, `SV`, `HSV`, or `HSVlist` must not be `None`.

            **fin** :  string

                    File path to to a source of tabular dat, which will be
                    loaded using the tabarray constructor.  The load method
                    will be inferred from the file extension and whether or not
                    there is a headerkey in the first line of the file.

            **title** :  string

                    Description to be used in the <title> tag of the created
                    html file.

            **printheader** : boolean

                    If `printheader = True`, will print out a "header" and 
                    "footer" (both in the body of the HTML documents) on every 
                    page.  The header contains information about the name of 
                    the input file and the number of rows, as well what the 
                    current page number is (if split between multiple 
                    documents) and links to any other pages.  The footer 
                    contains the same page number and links.

            **split** : boolean

                    If `split = False`, will not split to multiple HTML pages, 
                    regardless of value of `ROWS_PER_PAGE`.

            **usecss** : False or None or string

                    If usecss is False, no link to a cssfile is included in the 
                    page header, and no cssfile is written out.  If is a 
                    string, that string is assumed to be a path and is linked 
                    to as the CSS file.  If it is None, then consideration of 
                    the `writecss` variable is made.

            **writecss** : boolean

                    If `usecss` is not `None`, then if `writecss` is not 
                    `False`:  the default css sheet is generated and written to 
                    a file whose name is either generated by default (if 
                    writecss is None) else given by writecss itself, and linked 
                    to in the file header

            **SERVERNAME** :  string

                    Server name.  For example, this could be the ServerName
                    of a VirtualHost on your local machine, assuming that
                    `fname` describes a path on the server.

            **SERVER_FROM_CURDIR** :  string

                    Root path of server relative to the current directory.
                    Assumed to be '../'.

            **ROWS_PER_PAGE** :  positive integer or 'all'

                    This sets the number of records displayed per .html page
                    (if the tabular file has more than ROWS_PER_PAGE rows,
                    it will be split into multiple sections on several .html
                    pages (default = 1000).

                    If the value is 'all' then the page is not split (e.g. it 
                    is as if split = False)

            **See also:**  the kwargs arguments must be valid keyword arguments 
            for :func:`tabular.tabarray.tabarray.__new__`, the tabarray 
            constructor, see documentation for descriptions.

    """

    # Must write to an HTML file.

    assert returnstring or fname.endswith( '.html' ), 'fname must end in ".html".'
      
    if X is None:
        if fin is not None:
            if fin.lstrip('/').endswith('.hsv'):
                kwargs['HSVfile'] = fin
            elif fin.endswith('.tsv') or fin.endswith('.csv'):
                kwargs['SVfile'] = fin
            elif fin.endswith(('.npy','.npz')):
                kwargs['binary'] = fin
            else:
                assert False, ('This algorithm is being forced to determine '
                              'the proper file type for web representation '
                              'from file\'s path (e.g. by looking at '
                              'extension) since the type is not given ' 
                              'explicitly by use of a keyword argument, but '
                              'is having problems deducing the intended file ' 
                              'type from the path (e.g., because the '
                              'extension is not one of those this algorithm ' 
                              'recognizes).')
        else:
            assert any([l in list(kwargs.keys()) and kwargs[l] != None 
                        for l in ['SVfile','binary','HSVfile']]), \
                   ('Either a tabarray is given, or file path "fin" is '
                    'given, or one of "HSV", "binary", or "SV" keyword '
                    'arguments are given.')

        X = tb.tabarray(**kwargs)

    names = X.dtype.names
    try:
        RowColors = X['__color__']
    except:
        if '__color__' in names:
            cspot = names.index('__color__')
            RowColors = [r[cspot] for r in X]
        else:
            RowColors = [''] * len(X)
    try:
        coloring = X.coloring
    except:
        coloring = {}

    Num_Records = len(X)
    Num_Cols = len(names)
    ColorStyles = CSSColoring(names, coloring)
    HdrNts = HeaderNotations(names, coloring)

    # If I specify usecss and it is not false, it must be a string and I want 
    # to put that file name in the link and not write anything out.
    # If I specify writecss I want it to write out file to that name and use it 
    # in the link.
    # If usecss = false, writecss is false and nothing is put in the link.
    # If usecss is not specified, then ...

    if usecss != None:
        if isinstance(usecss, str):
            cssfile = usecss
            CSSLINK = ('<link rel="stylesheet" type="text/css" href="' + '/' + 
                       cssfile[len(SERVER_FROM_CURDIR):] + '"</link>')
        else:
            assert usecss == False
            CSSLINK = ''
    else:
        if writecss == False or returnstring:
            CSSLINK = ''
        else:
            if not isinstance(writecss,str):
                cssfile = fname[:-5] + '.css'
            else:
                cssfile = writecss
            WriteOutCSS(ColorStyles[1],cssfile)
            CSSLINK = ('<link rel="stylesheet" type="text/css" href="' + '/'  + 
                       cssfile[len(SERVER_FROM_CURDIR):] + '"</link>')

    if returnstring:
        split = False
    
    if not split or ROWS_PER_PAGE == 'all':
        ROWS_PER_PAGE = Num_Records + 1

    numSections = int(Num_Records / ROWS_PER_PAGE) + 1   
    
    # section2file(i) returns the name of the .html file corresponding to 
    # section number i.
    section2file = (lambda sectionNum: fname if sectionNum == 0 
                else splitext(fname)[0] + str(sectionNum) + splitext(fname)[1])
    
    if title is None:
        if not fin is None:
            title = fin
        else:
            title = 'Title Not Given'
    for section in range(numSections):
        sectionfname = section2file(section)
        fromRow = section * ROWS_PER_PAGE  # Start record # for this section.
        toRow = min( fromRow + ROWS_PER_PAGE, Num_Records)  # End record #.

        if printheader and not returnstring:
            prefix = '/' + DirName(fname[len(SERVER_FROM_CURDIR):]) + '/'
        else:
            prefix = ''

        # Open the output file for the section to fileobject 'f'.
        if not returnstring:
            f = open(sectionfname,'w')
        else:
            f = tempfile.TemporaryFile('w+b')
                     
        # Write out file header.
        if not returnstring:
            f.write('<html><META HTTP-EQUIV="Content-Type" '
                'CONTENT="text/html; charset=utf-8" /><head><title>' + 
                title + '</title>' + CSSLINK + '</head><body>\n' )
        if printheader:
            f.write('<p>Tabular File (page ' + str(section + 1) + ' of ' + 
                    str(numSections) + ', rows ' + str(fromRow + 1) + 
                    ' - ' + str(toRow) + '): ' + title + '</p>\n')
            f.write('<p>page ')
            if section > 0:
                f.write(' <a href="' + prefix + 
                       basename(section2file(section - 1)) + '">prev</a> ')
            if section < numSections - 1:
                f.write(' <a href="' + prefix + 
                       basename(section2file(section + 1)) + '">next</a> ')
            for page in range(numSections):
                f.write((' <a href="' + prefix + 
                      basename(section2file(page)) + '">' + str(page + 1) + 
                      '</a>') if page != section else ' ' + str(page + 1))
            f.write( '</p>' )

        # Write out table with number of cols.
        f.write('<table border="1" cellspacing="0" cellpadding="4">\n')
        f.write('<col span="' + str(Num_Cols) + '" align="center">\n')

        # Write out table header line.
        f.write('<thead>')
        if len(HdrNts) > 0:
            for h in HdrNts:
                f.write(h + '\n')
        f.write('<tr align="center">')
        for name in names:
            f.write('<th class="' + ColorStyles[0][name] + '">' + 
                    cgi.escape(name) + '</th>')
        f.write('</tr>')
        f.write('</thead>\n')

        # Write out each record in the section.
        f.write( '<tbody>\n' )
        if (len(names) > 1) or (fin != None and fin.endswith('.csv')):
            for row in range( fromRow, toRow ):
                colorst = (' style="background-color:' + RowColors[row] + 
                           '" ' if  RowColors[row] != '' else '')
                f.write('<tr align="center">')
                for (i, val) in enumerate(X[ row ]):
                    #f.write('<td>' + cgi.escape(str(val)) + '</td>')
                    f.write('<td ' + colorst + ' class="' + 
                            ColorStyles[0][names[i]] + '">' + str(val).replace('\n','<br/>') + 
                            '</td>')
                f.write('</tr>\n')
        else:
            for row in range(fromRow, toRow):
                f.write('<tr align="center">')
                #f.write('<td>' + cgi.escape(str(X[row])) + '</td>')
                f.write('<td>' + str(X[row]).replace('\n','<br/>') + '</td>')
                f.write('</tr>\n')
        f.write('</tbody>\n')

        f.write( '</table>' )

        # Write out hyperlinks to other sections.
        if printheader:
            f.write('<p>page ')
            if section > 0:
                f.write(' <a href="' + prefix + 
                       basename(section2file(section - 1)) + '">prev</a> ')
            if section < numSections - 1:
                f.write(' <a href="' + prefix + 
                       basename(section2file(section + 1)) + '">next</a> ')
            for page in range(numSections):
                f.write((' <a href="' + prefix + 
                         basename(section2file(page)) + '">' + 
                         str(page + 1) + '</a>') if page != section 
                                                 else ' ' + str(page + 1))

            f.write('</p>')

        # End file.
        if not returnstring:
            f.write('</body></html>\n')
    
        if returnstring:
            f.seek(0)
            s = f.read()
            f.close()
            return s
        else:
            f.close()

def FixCSSName(k):
    k.replace('.','__')
    if k[0] in ['0','1','2','3','4','5','6','7','8','9']:
        k = '__' + k
    return k


def CSSColoring(names, coloring):
    Tree = NameTree(names, coloring)
    X = ColorScheme(Tree, (0, 1), Tree.weight)
    D1 = dict([(k, FixCSSName(k)) for k in list(X.keys())])
    D2 = dict([(FixCSSName(k), X[k]) for k in list(X.keys())])
    return [D1, D2]


def ColorScheme(NTree, B, Total):

    [L, R] = B
    [NS, NT, W] = [len(list(NTree.subtrees.keys())), len(NTree.topnodes), 
                   NTree.weight]

    angle = L + (R - L) * float(NS) / (NS + 1)
    lfrac = float(NT) / W
    tfrac = float(NT) / Total

    CScheme = {}
    TopColor = Point2HexColor(angle, .3 * (1 - tfrac), .85 + .15 * tfrac)
    for n in NTree.topnodes:
        CScheme[n] = TopColor

    if NS > 0:
        Delta = (R-L) * (1.0/NS)
        for (i, t) in enumerate(NTree.subtrees.values()):
            CScheme.update(ColorScheme(t, (L + Delta * i, L + Delta * (i + 1)), 
                                       Total))

    return CScheme

def HeaderNotations(names, sdict):
    NTree = NameTree(names, sdict)
    GroupsByLevel = GroupByLevel(NTree, sdict)
    lines = []
    for l in GroupsByLevel:
        if len(l) > 0:
            lines += [MakeLine(names, l, sdict)]
    return lines

def GroupByLevel(NTree, sdict):
    #Levels = [NTree.subtrees.keys()]
    Levels = EqualLevels(list(NTree.subtrees.keys()), sdict)
    LowerLevels = [GroupByLevel(t, sdict) for t in list(NTree.subtrees.values())]
    if len(LowerLevels) > 0:
        h = max([len(l) for l in LowerLevels])
        for i in range(h):
            New = utils.uniqify(utils.listunion([l[i] for l in LowerLevels 
                                                 if len(l) > i]))
            if len(New) > 0:
                Levels += [New]
    return Levels

def EqualLevels(L, sdict):
    EL = []
    done = []
    for i in range(len(L)):
        l1 = L[i]
        if l1 not in done:
            # need to copy dictionary contents, 
            # otherwise LevelVals points to the dict!
            LevelVals = sdict[l1][:]        
            LevelKeys = [l1]
            done += [l1]
            for j in range(i, len(L)):
                l2 = L[j]
                if len(set(LevelVals).intersection(set(sdict[l2]))) == 0:
                    LevelVals += sdict[l2][:]
                    LevelKeys += [l2]
                    done += [l2]
            EL += [LevelKeys]
    return EL

def MakeLine(names, L, sdict):
    LN = np.array([[l for l in L if name in sdict[l]][0] 
                      if len([l for l in L if name in sdict[l]]) > 0 
                      else '' for name in names])
    Diffs = np.append(np.append([-1], (LN[1:] != LN[:-1]).nonzero()[0]), 
                         [len(LN) - 1])
    s = '<tr>'

    for i in range(len(Diffs) - 1):
        if LN[Diffs[i] + 1] != '':
            s += ('<td colspan = "' + str(Diffs[i + 1] - Diffs[i]) + '">' + 
                  LN[Diffs[i] + 1]  +  '</td>')
        else:
            s += '<th colspan = "' + str(Diffs[i + 1] - Diffs[i]) + '"></th>'

    s+= '</tr>'
    return s

class NameTree():
    def __init__(self, names, sdict):

        self.topnodes = set(names).difference(utils.listunion(list(sdict.values())))

        self.subtrees = {}
        SK = list(sdict.keys()) ; SK.sort()
        done = []
        for (i,s) in enumerate(SK):
            if not any([set(sdict[s]) < set(sdict[ss])  for ss in SK]):
                subsets = [ss for ss in list(sdict.keys()) 
                           if set(sdict[ss]) < set(sdict[s])]
                newsdict = dict([(ss, list(set(sdict[ss]).difference(done))) 
                                 for ss in subsets])
                newnames = list(set(sdict[s]))#.difference(done))
                if len(newnames) > 0:
                    self.subtrees[s] = NameTree(newnames, newsdict)
                    done += newnames

        self.weight = (sum([t.weight for t in list(self.subtrees.values())]) + 
                       len(self.topnodes))

def WriteOutCSS(ColorStyles, outpath):
    f = open(outpath,'w')
    f.write('body, td{\n')
    f.write('font-size : 10pt;\n')
    f.write('}\n')
    f.write('th{\n')
    f.write('font-weight : bold;\n')
    f.write('}\n')

    for Class in list(ColorStyles.keys()):
        f.write('td.' + Class  + ',th.' + Class + '{\n')
        f.write('background-color : ' + ColorStyles[Class] + '\n')
        f.write('}\n')

    f.close()

def DirName(path):
    '''
    Utility that gets directory name.  
    
    Sometimes this is the right thing to use intead of ``os.path.dirname``.
    '''
    if path[-1] == '/':
        path = path[:-1]
    return dirname(path)