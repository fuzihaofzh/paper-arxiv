#!/usr/bin/env python
# encoding=utf-8
from __future__ import print_function
import argparse
import sys
import collections
import re
import os
import json
import io
import time
reload(sys)
sys.setdefaultencoding('utf-8')

class ReadChar():
    def __enter__(self):
        import tty, sys, termios
        self.fd = sys.stdin.fileno()
        self.old_settings = termios.tcgetattr(self.fd)
        tty.setraw(sys.stdin.fileno())
        return sys.stdin.read(1)
    def __exit__(self, type, value, traceback):
        import tty, sys, termios
        termios.tcsetattr(self.fd, termios.TCSADRAIN, self.old_settings)

def getchar(info = None):
    if info is not None:
        print(info)
    with ReadChar() as rc:
        return rc

class TempPath:
    def __init__(self):
        self.temPath = os.path.join(PaperManager.getLibPath(), '.tmp')

    def __enter__(self):
        if os.path.exists(self.temPath):
            import shutil
            shutil.rmtree(self.temPath)  
        os.mkdir(self.temPath)
        return self.temPath

    def __exit__(self, type, value, traceback):
        import shutil
        shutil.rmtree(self.temPath)

class PaperDBCursor():
    def __init__(self):
        self.dbpath = os.path.join(PaperManager.getLibPath(), "pa.db")
        self.tableName  = "docInfoTable"
    def __enter__(self):
        import sqlite3
        self.conn = sqlite3.connect(self.dbpath)
        self.cursor = self.conn.cursor()
        self.cursor.execute("create table if not exists %s (name text NOT NULL PRIMARY KEY, title text, authors text, year text, journal text, tags text, comment text, path text, link text, addTime datetime, updateTime datetime, srcType text, content text)"%(self.tableName))
        return (self.cursor, self.tableName)

    def __exit__(self, type, value, traceback):
        self.cursor.close()
        self.conn.commit()
        self.conn.close()

class PaperDB():
    @classmethod
    def getEmptyMeta(cls):
        dbmeta = collections.OrderedDict([
            ('name', ''),
            ('title', ''),
            ('authors', ''),
            ('year', ''),
            ('journal', ''),
            ('tags', ''),
            ('comment', ''),
            ('path', ''),
            ('link', ''),
            ('addTime', ''),
            ('updateTime', ''),
            ('srcType', ''),
            ('content', ''),
            ])
        return dbmeta
    @classmethod
    def insert(cls, records):
        if 'name' not in records:
            print('insert should have the name attribute!')
            return
        with PaperDBCursor() as (cursor, tableName):
            sqlcmd = 'insert into %s values ('%(tableName) + ','.join(map(lambda x: '?', records)) + ')'
            par = tuple(map(lambda x: records[x], records))
            cursor.execute(sqlcmd, par)

    @classmethod
    def delete(cls, name):
        with PaperDBCursor() as (cursor, tableName):
            cursor.execute('delete from %s where name = ?'%(tableName), (name,))
    
    @classmethod
    def update(cls, name, records):
        with PaperDBCursor() as (cursor, tableName):
            if len(cursor.execute('select name from %s where name = ?'%(tableName), (name,)).fetchall()) != 0:
                sqlcmd = 'update %s set '%(tableName) + ','.join(map(lambda x: x + ' = ? ', records)) + ' where name = "%s"'%(name)
                par = tuple(map(lambda x: records[x], records))
                cursor.execute(sqlcmd, par)
            else:
                cls.insert(records)

    @classmethod
    def getMeta(cls, name):
        ret = cls.getEmptyMeta()
        del ret['content']
        with PaperDBCursor() as (cursor, tableName):
            data = cursor.execute('select name, title, authors, year, journal, tags, comment, path, link, addTime, updateTime, srcType from %s where name = ?'%(tableName), (name,)).fetchone()
            if data is None:
                return None 
            for i, key in enumerate(ret):
                ret[key] = data[i]
        return ret

    @classmethod
    def getAll(cls):
        with PaperDBCursor() as (cursor, tableName):
            data = cursor.execute('select * from %s'%(tableName)).fetchall()
        return data

    @classmethod
    def getAllJson(cls):
        with PaperDBCursor() as (cursor, tableName):
            datas = cursor.execute('select * from %s'%(tableName)).fetchall()
        rets = collections.OrderedDict([])
        for data in datas:
            ret = cls.getEmptyMeta()
            for i, key in enumerate(ret):
                ret[key] = data[i]
            rets[ret['name']] = ret
        return rets

    @classmethod
    def getAllNames(cls):
        with PaperDBCursor () as (cursor, tableName):
            data = cursor.execute('select name from %s'%(tableName)).fetchall()
        return map(lambda x: x[0], data)

    @classmethod
    def getAllTags(cls):
        with PaperDBCursor() as (cursor, tableName):
            data = cursor.execute('select tags from %s'%(tableName)).fetchall()
        return filter(lambda z: len(z) > 0, list(set(map(lambda y: y.strip(), re.split(',', ','.join(map(lambda x: x[0], data)))))))

    @classmethod
    def find(cls, args):
        import re
        ret = []
        with PaperDBCursor() as (cursor, tableName):
            #cols = args.keys()
            #cols = ['name'] + cols if 'name' not in cols else cols
            #cols = ','.join(cols)
            #cond = ' or '.join([i + ' like "%' + args[i] + '%" ' for i in args])
            #data = cursor.execute('select {0} from {1} where {2} '.format(cols, tableName, cond)).fetchall()
            for col in args:
                data = cursor.execute('select name, {0} from {1} where {2} like "%{3}%" '.format(col, tableName, col, args[col])).fetchall()
                data1 = map(lambda x: [x[0], re.sub(r'(?i)(%s)'%(args[col]), r'%s\1%s'%(Utils.colors.BROWN, Utils.colors.ENDC), x[1]).replace('\n', ' ')], data)
                if col == 'content':
                    for i in range(len(data1)):
                        place = [(a.start(), a.end()) for a in list(re.finditer(args[col], data1[i][1], re.I))]
                        itp = '\n\t'.join(map(lambda x: data1[i][1][max(0, x[0] - 40) : min(len(data1[i][1]), x[1] + 40)], place))
                        data1[i][1] = itp
                for i in range(len(data1)):
                    data1[i][1] = Utils.colors.BLUE + col + '\t' + Utils.colors.ENDC  + ' : ' + data1[i][1]
                ret += data1
        ret1 = {}
        for i in range(len(ret)):
            if ret[i][0] not in ret1:
                ret1[ret[i][0]] = []
            ret1[ret[i][0]].append(ret[i][1].strip())
        return ret1

    @classmethod
    def updateContent(cls, name, content):
        with PaperDBCursor() as (cursor, tableName):
            sqlcmd = 'update %s set content = ?  where name = "%s"'%(tableName, name)
            cursor.execute(sqlcmd, (content,))

    @classmethod
    def sql(cls, sqlcmd):
        with PaperDBCursor() as (cursor, tableName):
            data = cursor.execute(sqlcmd.format(table = tableName)).fetchall()
        print(data)

class Utils():
    class colors:
        RED = '\033[31m'
        GREEN = '\033[32m'
        BROWN = '\033[33m'
        BLUE = '\033[34m'
        PURPLE = '\095[34m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    @staticmethod
    def printList(obj, cols=3, columnwise=True, gap=4):
        """
        Print the given list in evenly-spaced columns.

        Parameters
        ----------
        obj : list
            The list to be printed.
        cols : int
            The number of columns in which the list should be printed.
        columnwise : bool, default=True
            If True, the items in the list will be printed column-wise.
            If False the items in the list will be printed row-wise.
        gap : int
            The number of spaces that should separate the longest column
            item/s from the next column. This is the effective spacing
            between columns based on the maximum len() of the list items.
        """
        import math
        if len(obj) == 0: return
        sobj = [item.encode('utf-8') for item in obj]
        if cols > len(sobj): cols = len(sobj)
        max_len = max([len(item) for item in sobj])
        if columnwise: cols = int(math.ceil(float(len(sobj)) / float(cols)))
        plist = [sobj[i: i+cols] for i in range(0, len(sobj), cols)]
        if columnwise:
            if not len(plist[-1]) == cols:
                plist[-1].extend(['']*(len(sobj) - len(plist[-1])))
            plist = zip(*plist)
        printer = '\n'.join([
            ''.join([c.ljust(max_len + gap) for c in p])
            for p in plist])
        print(printer)

class PaperManager(object):
    confPath = os.path.join(os.path.expanduser('~'), '.pa.conf')

    @classmethod
    def loadConf(cls):
        if not os.path.exists(cls.confPath):
            cf = collections.OrderedDict([
                        ('libpath', os.path.join(os.path.abspath(os.path.expanduser('~')), 'pa')),
                        ('ConerenceMap', collections.OrderedDict([
                                        ("Journal of Machine Learning Research", "JMLR"),
                                        ("Neural Computation", "NC"),
                                        ("IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE", "TPAMI"),
                                        ("International World Wide Web Conference", "WWW"),
                                        ("Association for the Advancement of Artificial Intelligence", "AAAI"),
                                        ("Association for the Advancement of Artiﬁcial Intelligence", "AAAI"),
                                        ("American Association for Artificial Intelligence", "AAAI"),
                                        ("International Conference on Machine Learning", "ICML"),
                                        ("Empirical Methods in Natural Language Processing", "EMNLP"),
                                        ("NAACL", "NAACL"),
                                        ("Association for Computational Linguistics", "ACL"),
                                        ("International Joint Conference on Artificial Intelligence", "IJCAI"),
                                        ("Springer Nature", "Nature"),
                                        ("ICLR", "ICLR"),
                                        ("Mach Learn", "ML"),
                                        ("ECCV", "ECCV"),
                                        ("SIGKDD", "SIGKDD"),
                                        ("SIGMOD", "SIGMOD"),
                                        ("ACM", "ACM"),
                                        ("arXiv", "arXiv"),
                                        ("Computer", "Computer"),
                                        ("IEEE", "IEEE"),
                        ]))
            ])
            cls.setConf(cf)
            cls.saveConf()
        cls.setConf(json.load(open(cls.confPath), strict=False, object_pairs_hook=collections.OrderedDict))
        return

    @classmethod
    def getConf(cls):
        if cls.conf is None:
            cls.loadConf()
        return cls.conf

    @classmethod
    def setConf(cls, conf):
        cls.conf = conf
        cls.ConerenceMap = conf['ConerenceMap']

    @classmethod
    def saveConf(cls):
        json.dump(cls.conf, open(cls.confPath, 'w'), sort_keys=False, indent=2, ensure_ascii=False)

    @classmethod
    def getLibPath(cls):
        libPath = PaperManager.getConf()['libpath']
        if libPath is not None and os.path.exists(libPath):
            return libPath
        elif libPath is not None:
            os.mkdir(libPath)
        else:
            print("please set Library Dir with 'pa set --libpath /your/path/to/store/papers' ")
            exit(0)

    @classmethod
    def getIndexPath(cls):
        indexPath = os.path.join(cls.getLibPath(), '.index')
        if not os.path.exists(indexPath):
            os.mkdir(indexPath)
        return indexPath

    @classmethod
    def add(cls, filePath):
        from lxml import etree
        if os.path.isdir(filePath):
            for root, dirs, files in os.walk(filePath):
                for file in files:
                    if file[-4:] != '.pdf':continue
                    PaperManager.add(os.path.abspath(os.path.join(root, file)))
        else:
            import urllib
            fileName = os.path.basename(filePath)
            response = urllib.urlopen(filePath.encode('utf-8'))
            content = response.read()
            if filePath[-4:] != '.pdf':
                #content = content.encode('utf-8')
                with TempPath() as tmpdir:
                    tmpPath = os.path.join(tmpdir, fileName + '.xml') 
                    with open(tmpPath, 'w') as f:
                        f.write(content)
                        tree = etree.HTML(content)
                        PaperManager.addHTMLFile(tree, content, tmpdir, filePath)
            else:# for pdf
                with TempPath() as tmpdir:
                    tmpPath = os.path.join(tmpdir, fileName)
                    with open(tmpPath, 'w') as f:
                        f.write(content)
                    PaperManager.addPdfFile(tmpdir, fileName)
    @classmethod
    def addPdfFile(cls, tmpdir, fileName):
        import datetime
        from lxml import etree
        import shutil
        import html2text
        filePath = os.path.join(tmpdir, fileName)
        os.system('pdftohtml -f 1 -l 1 -q %s -xml %s.xml'%(filePath, filePath))
        content = open('%s.xml'%(filePath)).read()
        years = [int(x) for x in re.findall(r'19\d\d|20\d\d', content)]
        years = years + [datetime.datetime.now().year] if len(years) == 0 else years
        year = max(filter(lambda x: x <= datetime.datetime.now().year, years))
        parser = etree.XMLParser(recover=True)
        tree = etree.XML(content, parser)
        # extract title and authors
        title = ' '.join([etree.tostring(e, encoding='utf8', method='text') for e in tree.xpath('//text[@font=0]')])#.encode('ascii',errors='ignore')
        title = title.replace('\n', ' ')
        al = [etree.tostring(e, encoding='utf8', method='text') for e in tree.xpath('//text[@font=1 or @font=2 or @font=3 or @font=4 or @font=5]')]
        # prevent page number to be title
        if any(map(lambda x: x in title, cls.ConerenceMap.keys())) or len(title) < 5 or 'arXiv' in title or 'Vol.' in title:
            title = ' '.join([e.text if not e.getchildren() else e.getchildren()[0].text for e in tree.xpath('//text[@font=1]')])#.encode('ascii',errors='ignore')
            al = [etree.tostring(e, encoding='utf8', method='text') for e in tree.xpath('//text[@font=2 or @font=3 or @font=4 or @font=5]')]
        weblink = ' '.join([etree.tostring(e, encoding='utf8', method='text') for e in tree.xpath('//text[@myspecialdesitaggned=0]')])
        if len(weblink):
            journal = web
        authors = []
        cnt = 0
        for a in al:
            if a is not None and 'Abstract' not in a and 'abstract' not in a and 'ABSTRACT' not in a and 'Introduction' not in a and cnt < 10:
                if '@' not in a and len(a) > 5:
                    sa = filter(lambda x: len(x) > 3, re.split(',| and ', a))
                    authors += sa
                    cnt += len(sa)
            else:
                break
        if len(authors) == 0 : authors = ["Unknown"] 
        #authors = ' '.join([e.text for e in tree.xpath('//text[@font=1]')])
        pcontent = etree.tostring(tree, encoding='utf8', method='text').replace('-\n', '').replace('\n', ' ')
        journal = "note"
        for i in cls.ConerenceMap:
            if i in pcontent:
                journal = cls.ConerenceMap[i]
                break
        rename = '-'.join([str(year), journal, re.sub('[\%\/\<\>\^\|\?\&\#\*\\\:\" \n]', '', authors[0])]) + '.pdf'
        rename = re.sub('[\%\/\<\>\^\|\?\&\#\*\\\:\" ]', '+', rename)
        authors1 = '\n'.join((a.strip() for a in authors))
        addTime = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.localtime(time.time()))
        # make index
        print('Begin indexing the file %s ...'%(rename))
        os.system('pdftohtml -q "%s" -xml "%s.xml"'%(filePath, filePath))
        content = open('%s.xml'%(filePath)).read()
        h = html2text.HTML2Text()
        h.ignore_links = True
        content = h.handle(content)
                
        outdata = collections.OrderedDict([
            ("name", unicode(rename)),
            ("title", unicode(title)),
            ("authors", unicode(authors1)),
            ("year", unicode(str(year))),
            ("journal", unicode(journal)),        
            ("tags", ""),
            ("comment", ""),
            ("path", ""),
            ("link", ""),
            ("addTime", unicode(addTime)),
            ("updateTime", unicode(addTime)),
            ("srcType", u"pdf"),
            ("content", unicode(content))
        ])
        # save to db
        sf = 1
        sfname = outdata['name']
        names = set(PaperDB.getAllNames())
        while sfname in names:
            sfname = outdata['name'][:-4] + '.' + str(sf) + outdata['name'][-4:]
            sf += 1
        outdata['name'] = sfname
        shutil.move(os.path.join(tmpdir, fileName), os.path.join(PaperManager.getLibPath(), outdata['name']))
        PaperDB.insert(outdata)
        print('%s has been added into the library.'%(outdata['name']))
        # user edit
        rc = getchar("Press enter to edit %s information.[y/n]"%(outdata['name']))
        if 'n' == rc: return
        elif ord(rc) == 3:exit(0) 
        else:outdata = cls.editInfo(outdata['name'], tmpdir)

    @classmethod
    def addHTMLFile(cls, tree, content, tmpdir, filePath):
        from urlparse import urlparse
        import datetime
        import html2text
        title = tree.xpath('//title')
        titletext = title[0].text.replace('\n', ' ') if title else ""
        years = [int(x) for x in re.findall(r'19\d\d|20\d\d', content)]
        years = years + [datetime.datetime.now().year] if len(years) == 0 else years
        year = max(filter(lambda x: x <= datetime.datetime.now().year, years))
        website = urlparse(filePath).netloc
        rename = str(year) + '-' + website + '-' + os.path.basename(filePath)
        rename = re.sub('[\%\/\<\>\^\|\?\.\&\#\*\\\:\" ]', '+', rename)
        addTime = time.strftime("%a, %d %b %Y %H:%M:%S GMT+8", time.localtime(time.time()))
        # make index
        print('Begin indexing the file %s ...'%(rename))
        h = html2text.HTML2Text()
        h.ignore_links = True
        content = h.handle(content)
        outdata = collections.OrderedDict([
            ("name", unicode(rename)),
            ("title", unicode(titletext)),
            ("authors", ""),
            ("year", unicode(str(year))),
            ("journal", unicode(website)),
            ("tags", ""),
            ("comment", ""),
            ("path", ""),
            ("link", unicode(filePath)),
            ("addTime", unicode(addTime)),
            ("updateTime", unicode(addTime)),
            ("srcType", "web"),
            ("content", unicode(content))
        ])
        # save to db
        sf = 1
        sfname = outdata['name']
        names = set(PaperDB.getAllNames())
        while sfname in names:
            sfname = outdata['name'] + '.' + str(sf)
            sf += 1
        outdata['name'] = sfname
        PaperDB.insert(outdata)
        print('%s has been added into the Library.'%(outdata['name']))
        # user edit
        rc = getchar("Press enter to edit %s information.[y/n]"%(outdata['name']))
        if 'n' == rc: return
        elif ord(rc) == 3:exit(0) 
        else:outdata = cls.editInfo(outdata['name'], tmpdir)

    @classmethod
    def editInfo(cls, name, tmpdir):
        import sqlite3
        import shutil
        outdata = PaperDB.getMeta(name)
        tmpMetaPath = os.path.join(tmpdir, name + '.tmp')
        json.dump(outdata, open(tmpMetaPath, 'w'), sort_keys=False, indent=2, ensure_ascii=False)
        oriname = outdata['name']
        while True:
            try:                     
                os.system("vim %s"%(tmpMetaPath))
                userjson = json.load(open(tmpMetaPath), strict=False, object_pairs_hook=collections.OrderedDict)
                userjson['path'] = userjson['name']
                PaperDB.update(oriname, userjson)
                if oriname != userjson['name'] and 'pdf' == userjson['srcType']:
                    shutil.move(os.path.join(PaperManager.getLibPath(), oriname), os.path.join(PaperManager.getLibPath(), userjson['name']))
                print('%s has been updated.'%(userjson['name'])) 
                return userjson
            except ValueError:
                print("Format Error, please re-edit %s."%(outdata['name']))
                with ReadChar() as rc:
                    if ord(rc) == 3:exit(0)   
            except sqlite3.IntegrityError:
                print("File name Error, the name is already exists in Library, please re-edit %s."%(outdata['name']))
                with ReadChar() as rc:
                    if ord(rc) == 3:exit(0)

    @classmethod
    def rm(cls, name):
        data = PaperDB.getMeta(name)
        if data is None:
            print('%s is not found!'%(name))
            exit(0)
        filePath =  os.path.join(cls.getLibPath(), data['name'])
        if os.path.exists(filePath):
            os.remove(filePath)
        PaperDB.delete(name)

    @classmethod
    def edit(cls, name):
        outdata = PaperDB.getMeta(name)
        if outdata is None:
            print("%s is not found!"%(name))
            exit(0)
        with TempPath() as tmpdir:
            cls.editInfo(outdata['name'], tmpdir)

    @classmethod
    def show(cls, name):
        outdata = PaperDB.getMeta(name)
        if outdata is None:
            print('%s does not exist in the library.'%(name))
            return
        for i in outdata:
            print(Utils.colors.BLUE + '%10s: '%(i) + Utils.colors.ENDC + outdata[i].strip())
        print(os.path.join(cls.getLibPath(), name))

    @classmethod
    def ls(cls, lstags):
        if lstags:
            tags = PaperDB.getAllTags()
            Utils.printList(tags)
        else:
            names = PaperDB.getAllNames()
            Utils.printList(names)

    @classmethod
    def find(cls, args):
        argdict = vars(args)
        npars = collections.OrderedDict([])
        for par in argdict:
            if par == 'keywords' or par == 'func':
                continue
            if argdict[par] != None:
                npars[par] = argdict['keywords']
        if len(npars) == 0:
            npars = PaperDB.getEmptyMeta()
            del npars['addTime']
            del npars['updateTime']
            del npars['srcType']
            del npars['path']
            for i in npars:
                npars[i] = argdict['keywords']
        result = PaperDB.find(npars)

        for i in result:
            print ('-'*80)
            print (Utils.colors.BOLD + i + Utils.colors.ENDC)
            print (os.path.join(cls.getLibPath(), i))
            print ('\n'.join(result[i]))

    @classmethod
    def exportjson(cls, path):
        data = PaperDB.getAllJson()
        json.dump(data, open(path, 'w'), sort_keys=False, indent=2, ensure_ascii=False)

    @classmethod
    def importjson(cls, path):
        rcdjsons = json.load(open(path), strict=False, object_pairs_hook=collections.OrderedDict)
        names = set(PaperDB.getAllNames())
        for rcd in rcdjsons:
            if rcd in names:
                print('%s already exists in Library.'%(rcd))
                exit(0)
        for rcd in rcdjsons:
            newRecord = PaperDB.getEmptyMeta()
            for i in newRecord:
                if i in rcdjsons[rcd]:
                    newRecord[i] = rcdjsons[rcd][i]
            PaperDB.insert(newRecord)

    @classmethod
    def updateAllContent(cls):
        names = PaperDB.getAllNames()
        for i, name in enumerate(names):
            print(i, '/', len(names), name)
            cls.updateContent(name)

    @classmethod
    def updateContent(cls, name):
        import urllib
        import html2text
        meta = PaperDB.getMeta(name)
        if meta['link'] == '':
            filePath = os.path.join(cls.getLibPath(), meta['name'])
        else:
            filePath = meta['link']
        response = urllib.urlopen(filePath.encode('utf-8'))
        content = response.read()
        with TempPath() as tmpdir:
            tmpPath = os.path.join(tmpdir, name)
            with open(tmpPath, 'w') as f:
                f.write(content)
            if meta['link'] == '':
                os.system('pdftohtml -q "%s" -xml "%s.xml"'%(tmpPath, tmpPath))
                content = open('%s.xml'%(tmpPath)).read()
                h = html2text.HTML2Text()
                h.ignore_links = True
                content = h.handle(content)
            else:
                h = html2text.HTML2Text()
                h.ignore_links = True
                content = h.handle(content)
        PaperDB.updateContent(name, content)

    @classmethod
    def sql(cls, sqlcmd):
        PaperDB.sql(sqlcmd)


def config(args):
    """
    config parameters in conf file.
    """
    conf = PaperManager.getConf()
    if args.libpath:
        conf['libpath'] = os.path.abspath(os.path.expanduser(args.libpath))
        PaperManager.setConf(conf)
        PaperManager.saveConf()

def add(args):
    """
    Add documents or urls to the library.
    """
    PaperManager.add(args.filePath)

def rm(args):
    """
    Remove documents or urls in the library.
    """
    PaperManager.rm(args.name)

def edit(args):
    """
    Update documents or urls in the library.
    """
    PaperManager.edit(args.name)

def show(args):
    """
    Show document information.
    """
    PaperManager.show(args.name)

def dumpJson(args):
    """
    Dump database as json.
    """
    data = PaperDB.getAll()
    if args.path:
        with open(args.path, 'w') as f:
            f.write(data)
    else:
        print (data)

def ls(args):
    """
    List document names in the library.
    """
    PaperManager.ls(args.lstags) 

def find(args):
    """
    Find keywords in the library.
    """
    PaperManager.find(args)

def exportjson(args):
    PaperManager.exportjson(args.path)

def importjson(args):
    PaperManager.importjson(args.path)

def updateContent(args):
    PaperManager.updateContent(args.name)

def updateAllContent(args):
    PaperManager.updateAllContent()

def sql(args):
    PaperManager.sql(args.sql)

def main():
    PaperManager.loadConf()
    parser = argparse.ArgumentParser(prog='pa')
    subparsers = parser.add_subparsers(title='subcommands')
    # config
    parser_config = subparsers.add_parser('config', help='Config user configs')
    parser_config.add_argument('--libpath', metavar='PATH', required = True,
                               help='set Library Dir that store all ducuments.')
    parser_config.set_defaults(func=config)
    # add
    parser_add = subparsers.add_parser('add', help='Add documents or urls to the library.')
    parser_add.add_argument('filePath', metavar='PATH',
                               help='Path of the file(s) that you want to store.')
    parser_add.set_defaults(func=add)
    # rm
    parser_rm = subparsers.add_parser('rm', help='Remove documents or urls in the library.')
    parser_rm.add_argument('name', metavar='NAME',
                               help='Name of the file(s) that you want to remove.')
    parser_rm.set_defaults(func=rm)
    # edit
    parser_edit = subparsers.add_parser('edit', help='Edit documents meta in the library.')
    parser_edit.add_argument('name', metavar='NAME',
                               help='Name of the file(s) that you want to edit.')
    parser_edit.set_defaults(func=edit)
    # ls
    parser_ls = subparsers.add_parser('ls', help='List document names in the library.')
    parser_ls.add_argument('--tags', dest='lstags', action='store_true',
                               help='List tags used in this lib.')
    parser_ls.set_defaults(func=ls)
    # show
    parser_show = subparsers.add_parser('show', help='show document information.')
    parser_show.add_argument('name', metavar='NAME',
                               help='Name of the file(s) that you want to show.')
    parser_show.set_defaults(func=show)
    # dump
    parser_dump = subparsers.add_parser('dump', help='Dump the database of the library.')
    parser_dump.add_argument('--path', metavar='JSONPATH', default = None,
                               help='Name of the file(s) that you want to remove.')
    parser_dump.set_defaults(func=dumpJson)
    # find
    parser_find = subparsers.add_parser('find', help='Find the database of the library.')
    parser_find.add_argument('keywords', metavar='KEYWORDS', default = None,
                               help='Keywords that you want to find in the library.')
    parser_find.add_argument('--name', default = None, action='store_true',
                               help='Search keywords in file name.')
    parser_find.add_argument('--title', default = None, action='store_true',
                               help='Search keywords in title.')
    parser_find.add_argument('--authors', default = None, action='store_true',
                               help='Search keywords in authors.')
    parser_find.add_argument('--year', default = None, action='store_true',
                               help='Search keywords in year.')
    parser_find.add_argument('--journal', default = None, action='store_true',
                               help='Search keywords in journal.')
    parser_find.add_argument('--tags', default = None, action='store_true',
                               help='Search keywords in tags.')
    parser_find.add_argument('--comment', default = None, action='store_true',
                               help='Search keywords in comment.')
    parser_find.add_argument('--content', default = None, action='store_true',
                               help='Search keywords in content.')
    parser_find.set_defaults(func=find)
    # export
    parser_export = subparsers.add_parser('export', help='Export library to json.')
    parser_export.add_argument('path', metavar='JSONPATH',
                               help='Path of the file(s) that you want to save.')
    parser_export.set_defaults(func=exportjson)
    # import
    parser_import = subparsers.add_parser('import', help='Import json file into library.')
    parser_import.add_argument('path', metavar='JSONPATH',
                               help='Path of the file(s) that you want to import.')
    parser_import.set_defaults(func=importjson)
    # updateContent
    parser_updateContent = subparsers.add_parser('updateContent', help='Update file\'s content in the library.')
    parser_updateContent.add_argument('name', metavar='RECORD',
                               help='Name of the record that you want to update.')
    parser_updateContent.set_defaults(func=updateContent)
    # updateAllContent
    parser_updateAllContent = subparsers.add_parser('updateAllContent', help='Update all records\' content in the library.')
    parser_updateAllContent.set_defaults(func=updateAllContent)
    # sql
    parser_sql = subparsers.add_parser('sql', help='excute sql cmd.')
    parser_sql.add_argument('sql', metavar='SQL',
                               help='sql command, use \{table\} as table name.')
    parser_sql.set_defaults(func=sql)


    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()

    

