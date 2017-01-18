#!/usr/bin/env python
# encoding=utf-8
import argparse
import sys
import collections
import re
import tinydb
import os
import json
import io
import click
import time


class UserException(BaseException):
    pass

class DBManager(object):
    def __init__(self, path):
        if os.path.exists(path):
            self.db = tinydb.TinyDB(os.path.join(path, 'pmdb.json'))

    def insert(self, data):
        if self.db.search(tinydb.where('name') == data['name']):
            raise UserException("Dumplicate key name. The item with name = '%s' has already been stored in the database."%data['name'])
        self.db.insert(data)

    def remove(self, name):
        rent = self.db.search(tinydb.where('name') == name)
        if len(rent) == 0:
            raise UserException("There is no item with name = '%s' in the database."%name)
        self.db.remove(tinydb.where('name') == name)

    def all(self):
        if not hasattr(self, 'db'):
            raise UserException('Please use init in this folder first.')
        return self.db.all()

    def get(self, name):
        return self.db.get(tinydb.where('name') == name)

    def update(self, data, name):
        self.db.update(data, tinydb.where('name') == name)

class Utils(object):
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
    def jsonToTable(jsonstr):
        from texttable import Texttable
        table = Texttable()
        content = [['Name', 'Value']]
        for key in jsonstr:
            content.append([key, ',' .join(jsonstr[key].split('\n'))])
        table.add_rows(content)
        return table.draw()

    @staticmethod
    def jsonToTmpFile(tmppath, jsonstr):
        with io.open(tmppath, "w", encoding='utf8') as f:
            try:
                f.write(json.dumps(jsonstr, sort_keys=False, indent=2, ensure_ascii=False).replace('\\n', '\n'))
            except TypeError:
                f.write(json.dumps(jsonstr, sort_keys=False, indent=2, ensure_ascii=False).replace('\\n', '\n').decode('utf-8'))

    @staticmethod
    def tmpFileTojson(tmppath):
        return json.loads(open(tmppath, "r").read(), strict=False, object_pairs_hook=collections.OrderedDict) # strict=False to allow \n

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
        print printer



class PaperManager(object):
    def __init__(self):
        self.ConerenceMap = collections.OrderedDict([
            ("Journal of Machine Learning Research", "JMLR"),
            ("Neural Computation", "NC"),
            ("IEEE TRANSACTIONS ON PATTERN ANALYSIS AND MACHINE INTELLIGENCE", "TPAMI"),
            ("International World Wide Web Conference", "WWW"),
            ("Association for the Advancement of Artificial Intelligence", "AAAI"),
            ("Association for the Advancement of Artiﬁcial Intelligence", "AAAI"),
            ("American Association for Artificial Intelligence", "AAAI"),
            ("International Conference on Machine Learning", "ICML"),
            ("Empirical Methods in Natural Language Processing", "EMNLP"),
            ("Association for Computational Linguistics", "ACL"),
            ("International Joint Conference on Artificial Intelligence", "IJCAI"),
            ("ICLR", "ICLR"),
            ("Mach Learn", "ML"),
            ("NAACL", "NAACL"),
            ("ECCV", "ECCV"),
            ("SIGKDD", "SIGKDD"),
            ("SIGMOD", "SIGMOD"),
            ("ACM", "ACM"),
            ("arXiv", "arXiv"),
            ("Computer", "Computer"),
            ("IEEE", "IEEE"),
        ])

        self.pmdb = DBManager(".pm")

        '''parser = argparse.ArgumentParser(
            description='Pretends to be pm',
            usage="")
        parser.add_argument('command', help='Subcommand to run')
        # parse_args defaults to [1:] for args, but you need to
        # exclude the rest of the args too, or validation will fail
        args = parser.parse_args(sys.argv[1:2])
        if not hasattr(self, args.command):
            print 'Unrecognized command'
            parser.print_help()
            exit(1)
        # use dispatch pattern to invoke method with same name
        getattr(self, args.command)()'''


    '''def init(self):
        parser = argparse.ArgumentParser(
            description='init paper manager repo in this directory.')
        self.initImpl()'''

    def init(self):
        import os
        os.system('mkdir -p .pm')
        if os.path.exists('.pm'):
            print 'folder .pm already exists.'
            return

    '''def add(self):
        parser = argparse.ArgumentParser(
            description='Add pdf papers into paper library.')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('pdfName')
        args = parser.parse_args(sys.argv[2:])
        self.addImpl(args.pdfName)'''

    def add(self, pdfName):
        from lxml import etree
        if pdfName[:4] == 'http':
            import urllib2
            response = urllib2.urlopen(pdfName)
            html = response.read()
            parser = etree.XMLParser(recover=True)
            tree = etree.XML(html, parser)
            # for link
            if tree:
                title = tree.xpath('//title')
                titletext = title[0].text if title else ""
                html = "<text font=\"0\">%s</text>\n"%titletext
                html += "<text myspecialdesitaggned=\"0\">%s</text>"%pdfName
                html = html.encode('utf-8')
                with open('.tmp/temp.pdf.xml', 'w') as f:
                    f.write(html)
            else:
                with open('temp.pdf', 'w') as f:
                    f.write(html)
            pdfName = 'temp.pdf'
        if os.path.isdir(pdfName):
            for root, dirs, files in os.walk(pdfName):
                for file in files:
                    if file[-4:] == '.pdf':
                        self.addSingleFile(root, file)
                        
            return
        if not os.path.exists(pdfName):
            print 'File %s does not exists.'%(pdfName)
            return
        self.addSingleFile('', pdfName)
        
    def addSingleFile(self, rootpath, file):
        from lxml import etree
        import re
        import datetime
        import json
        pdfPath = os.path.join(rootpath, file)
        if self.pmdb.get(file) is not None:
            print 'The file %s is already in Library!'%(file)
            return
        os.system('mkdir -p .tmp')
        os.system('pdftohtml -f 1 -l 1 -q %s -xml .tmp/%s.xml'%(pdfPath, file))
        content = open('.tmp/%s.xml'%(file)).read()
        years = [int(x) for x in re.findall(r'19\d\d|20\d\d', content)]
        years = years + [datetime.datetime.now().year] if len(years) == 0 else years
        year = max(filter(lambda x: x <= datetime.datetime.now().year, years))
        parser = etree.XMLParser(recover=True)
        tree = etree.XML(content, parser)
        # extract title and authors
        title = ' '.join([etree.tostring(e, encoding='utf8', method='text') for e in tree.xpath('//text[@font=0]')])#.encode('ascii',errors='ignore')
        al = [etree.tostring(e, encoding='utf8', method='text') for e in tree.xpath('//text[@font=1 or @font=2 or @font=3 or @font=4 or @font=5]')]
        # prevent page number to be title
        if any(map(lambda x: x in title, self.ConerenceMap.keys())) or len(title) < 5 or 'arXiv' in title or 'Vol.' in title:
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
        for i in self.ConerenceMap:
            if i in pcontent:
                journal = self.ConerenceMap[i]
                break
        rename = '-'.join([str(year), journal, authors[0].split()[-1]]) + '.pdf'
        authors1 = '\n'.join((a.strip() for a in authors))
        addTime = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.localtime(time.time()))
        #datetime_object = datetime.strptime(addTime, "%a, %d %b %Y %H:%M:%S GMT")
        
        outdata = collections.OrderedDict([
            ("title", title),
            ("authors", authors1),
            ("year", str(year)),
            ("journal", journal),
            ("name", rename),
            ("tags", ""),
            ("comment", ""),
            ("path", ""),
            ("addTime", addTime),
            ("updateTime", "")
        ])
            
        
        
        #with open(".tmp/%s.tmp"%(rename), "w") as f:
        #    f.write(json.dumps(outdata, sort_keys=True, indent=2).replace('\\n', '\n'))
        try:
            input("Press enter to add %s into Library."%(file))
        except SyntaxError:
            pass
        if not len(weblink):
            os.system('open %s'%pdfPath)

        Utils.jsonToTmpFile(".tmp/%s.tmp"%(file), outdata)
        
        os.system("vim .tmp/%s.tmp"%(file))
        while True:
            try:
                userjson = Utils.tmpFileTojson(".tmp/%s.tmp"%(file))
                break
            except ValueError:
                try:
                    input("Format Error, please re-edit %s."%(file))
                except SyntaxError:
                    pass
                os.system("vim .tmp/%s.tmp"%(file))

        userjson = json.loads(open(".tmp/%s.tmp"%(file), "r").read(), strict=False, object_pairs_hook=collections.OrderedDict) # strict=False to allow \n
        userjson['path'] = os.path.join(rootpath, userjson['name'])
        os.system('mv %s %s'%(pdfPath, userjson['path']))
        self.pmdb.insert(userjson)
        os.system('rm -rf .tmp')

        self.indexOneFile(rename, userjson['path'])

    '''def rm(self):
        parser = argparse.ArgumentParser(
            description='Remove pdf papers in the library.')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('name')
        args = parser.parse_args(sys.argv[2:])
        self.rmImpl(args.name)'''

    def rm(self, name):
        self.pmdb.remove(name)
        os.system('rm .pm/index/%s.txt'%(name))

    '''def ls(self):
        parser = argparse.ArgumentParser(
            description='Show all paper names in the library.')
        self.lsImpl()'''

    def ls(self):
        al = self.pmdb.all()
        al1 = [i['name'] for i in al]
        al1.sort()
        Utils.printList(al1)

    '''def edit(self):
        parser = argparse.ArgumentParser(
            description='Update pdf info in the library.')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('name')
        args = parser.parse_args(sys.argv[2:])
        self.updateImpl(args.name)'''

    def info(self, name):
        data = self.pmdb.get(name)
        if data is None:
             print 'This file doesn\'t exists in the library!'
             return
        os.system('mkdir -p .tmp')
        Utils.jsonToTmpFile('.tmp/%s.tmp'%data['name'], data)
        os.system('vim .tmp/%s.tmp'%data['name'])
        ndata = Utils.tmpFileTojson('.tmp/%s.tmp'%data['name'])
        os.system('rm -rf .tmp')
        updateTime = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.localtime(time.time()))
        ndata['updateTime'] = updateTime
        if 'addTime' not in ndata:
            ndata['addTime'] = updateTime
        self.pmdb.remove(name)
        self.pmdb.insert(ndata)

    def show(self):
        parser = argparse.ArgumentParser(
            description='Show pdf info in the library.')
        # NOT prefixing the argument with -- means it's not optional
        parser.add_argument('name')
        args = parser.parse_args(sys.argv[2:])
        self.showImpl(args.name)

    def showImpl(self, name):
        data = self.pmdb.get(name)
        if data is None:
            raise UserException('File %s is not in Library.'%name)
        print Utils.jsonToTable(data)

    def tags(self):
        allent = self.pmdb.all()
        result = {}
        for atc in allent:
            for t in atc['tags'].split(','):
                result[t] = 1 if t not in result else result[t] + 1
        result1 = [i + ': ' + str(result[i]) for i in result]
        result1.sort()
        Utils.printList(result1)

    def status(self):
        parser = argparse.ArgumentParser(
            description='Show status in the library.')
        self.statusImpl()

    def statusImpl(self):
        addedFiles = []
        al = self.pmdb.all()
        for i in al:
            addedFiles.append(i['name'])
        addedFilesSet = set(addedFiles)
        unadded = []
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file[-4:] == '.pdf':
                    if file not in addedFilesSet:
                        unadded.append(os.path.join(root, file))
        print "Added Files:"
        Utils.printList(addedFiles)
        print "Unadded Files:"
        Utils.printList(unadded)

    def findItemsWithNoTags(self):
        allent = self.pmdb.all()
        result = []
        for atc in allent:
            if atc['tags'] == "":
                result.append(atc['name'])
        print '\n'.join(result)

    def showJsonAsTable(self, jsonmap):
        from texttable import Texttable
        table = Texttable()
        content = [['Name', 'Value']]
        for key in jsonmap:
            content.append([key, ',' .join(str(jsonmap[key]).split('\n'))])
        table.add_rows(content)
        print table.draw()

    def reindex(self):
        al = self.pmdb.all()
        os.system('rm -rf .pm/index')
        os.system('mkdir -p .pm/index')
        for i in al:
            self.indexOneFile(i['name'], i['path'])

    def indexOneFile(self, name, path):
        from lxml import etree
        os.system('mkdir -p .tmp')
        os.system('pdftohtml -q %s -xml .tmp/%s.xml'%(path, name))
        content = open('.tmp/%s.xml'%(name)).read()
        parser = etree.XMLParser(recover=True)
        tree = etree.XML(content, parser)
        pcontent = etree.tostring(tree, encoding='utf8', method='text').replace('-\n', '')
        with open('.pm/index/%s.txt'%(name), "w") as f:
            f.write(pcontent)
        os.system('rm -rf .tmp')
        print path, 'info have been made.'


    def find(self, keyword, head, tags, authors, body, comment, outhead, outtags, outauthors, outcomment):
        foundFiles = {}
        al = self.pmdb.all()
        infoMap = {}
        resultMap = {}
        for i in al:
            infoMap[i['name']] = i
            thisResult = {}
            if head and keyword in i['title']:
                thisResult['head'] = i['title'].replace(keyword, Utils.colors.BROWN + keyword + Utils.colors.ENDC)
            if tags and keyword in i['tags']:
                thisResult['tags'] = i['tags'].replace(keyword, Utils.colors.BROWN + keyword + Utils.colors.ENDC)
            if authors and keyword in i['authors']:
                thisResult['authors'] = i['authors'].replace(keyword, Utils.colors.BROWN + keyword + Utils.colors.ENDC).replace('\n', ', ')
            if body != 0:
                with open('.pm/index/' + i['name'] + '.txt', 'r') as f:
                    rs = filter(lambda x: keyword in x, map(lambda x: x.decode('utf-8'), f.readlines()))[:body]
                if len(rs) != 0:
                    thisResult['body'] = '\n\t'.join(map(lambda x:x[max(0, x.find(keyword) - 40) : min(len(x), x.find(keyword) + 40)].strip().replace(keyword, Utils.colors.BROWN + keyword + Utils.colors.ENDC), rs))
            if comment and keyword in i['comment']:
                thisResult['comment'] = i['comment'].replace(keyword, Utils.colors.BROWN + keyword + Utils.colors.ENDC).replace('\n', '\t\n')
            if thisResult != {}:
                resultMap[i['name']] = thisResult


        for i in resultMap:
            print '-'*80
            print Utils.colors.BOLD + i + Utils.colors.ENDC
            for j in resultMap[i]:
                print '\t' + resultMap[i][j]
            if outhead:
                print '\t' + infoMap[i]['title']
            if outtags:
                print '\t' + infoMap[i]['tags']
            if outauthors:
                print '\t' + infoMap[i]['authors'].replace('\n', ', ')
            if outcomment:
                print '\t' + infoMap[i]['comment']

        '''if article:
            with open('.pm/index/' + i['name'] + '.txt', 'r') as f:
                rs = filter(lambda x: keyword in x, map(lambda x: x.decode('utf-8'), f.readlines()))
                if len(rs) != 0:
                    foundFiles[i['name']] = rs if i['name'] not in foundFiles else foundFiles[i['name']] + rs
                    if title:
            if keyword in i['title']:
                rs = [i['title']]
                foundFiles[i['name']] = rs if i['name'] not in foundFiles else foundFiles[i['name']] + rs'''

        '''for root, dirs, files in os.walk('.pm/index'):
            for file in files:
                if file[-4:] == '.txt':
                    pdfPath = os.path.join(root, file)
                    with open(pdfPath, 'r') as f:
                        rs = filter(lambda x: keyword in x, map(lambda x: x.decode('utf-8'), f.readlines()))
                        if len(rs) != 0:
                            foundFiles[file] = rs
        for f in foundFiles:
            print '-'*80
            print f
            for i in foundFiles[f][:line]:
                print '\t', i[max(0, i.find(keyword) - 40) : min(len(i), i.find(keyword) + 40)].strip()
            if title:
                print 'title:', infoMap[f]['title']
            if comment:
                print 'comment:', infoMap[f]['comment']
            if tags:
                print 'tags:', infoMap[f]['tags']'''

pm = PaperManager()


@click.group()
@click.pass_context
def cli(ctx):
    pass

@cli.command()
def init():
    """
    Init paper manager repo in this directory.
    """
    pm.init()

@cli.command()
@click.argument('pdfname')
def add(pdfname):
    """
    Add file or download file by url.
    """
    pm.add(pdfname)

@cli.command()
def ls():
    """
    List all added files.
    """
    pm.ls()

@cli.command()
@click.argument('pdfname')
def rm(pdfname):
    """
    Remove file from the Library.
    """
    pm.rm(pdfname)

@cli.command()
@click.argument('pdfname')
def info(pdfname):
    """
    Edit the information of each file.
    """
    pm.info(pdfname)

@cli.command()
def reindex():
    """
    Rebuild the search information for each pdf file.
    """
    pm.reindex()

@cli.command()
def tags():
    """
    Show all tags in the library.
    """
    pm.tags()

@cli.command()
@click.argument('keyword')

@click.option('--head', '-h', is_flag=True,
              help='Find by head lines.')
@click.option('--tags', '-t', is_flag=True,
              help='Find by tags.')
@click.option('--author', '-a', is_flag=True,
              help='Find by authors.')
@click.option('--body', '-b', default=0,
              help='Find by article body with in specific line number.')
#@click.option('--bodyline', '-l', default=3,
#              help='Show article body with in specific line number.')
@click.option('--comment', '-c', is_flag=True,
              help='Find by my comments.')
@click.option('--outhead', '-oh', is_flag=True,
              help='Show head lines.')
@click.option('--outtags', '-ot', is_flag=True,
              help='Show tags.')
@click.option('--outauthor', '-oa', is_flag=True,
              help='Show authors.')
@click.option('--outcomment', '-oc', is_flag=True,
              help='Show my comments.')
def find(keyword, head, tags, author, body, comment, outhead, outtags, outauthor, outcomment):
    """
    Find papers by keywords.
    """
    if head == False and tags == False and author == False and body == 0 and comment == False:
        body = 3
        head = True
        tags = True
        author = True
    pm.find(keyword, head, tags, author, body, comment, outhead, outtags, outauthor, outcomment)

def main():
    os.system('mkdir -p .tmp')
    cli()
    os.system('rm .tmp')

if __name__ == '__main__':
    main()



