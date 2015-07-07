from collections import defaultdict, OrderedDict
import inspect

import docutils
from docutils.core import publish_doctree
import xml.etree.ElementTree as etree

sphinxmapper = {'term':'name',
                'classifier':'type',
                'paragraph':'description',
                'definition':'name'}

def getFromDict(dataDict, mapList):
    return reduce(lambda d, k: d[k], mapList, dataDict)

def setInDict(dataDict, mapList, value):
    d = dataDict
    for k in mapList[:-1]:
        if not k in d.keys():
            d[k] = {}
        d = d[k]
    getFromDict(dataDict, mapList[:-1])[mapList[-1]] = value

def recursive_extract(package, d, packagename, visited):
    sub_modules = inspect.getmembers(package, inspect.ismodule)
    functions = inspect.getmembers(package, inspect.isfunction)
    classes = inspect.getmembers(package, inspect.isclass)

    for classname, classobj in classes:
        modulepath = classobj.__module__.split('.')
        modulepath.append(classobj.__name__)
        if modulepath[0] in packagename:
            if classobj.__name__.startswith('_'):
                continue
            setInDict(d, modulepath[1:], classobj)

    for funcname, funcobj in functions:
        modulepath = funcobj.__module__.split('.')
        modulepath.append(funcobj.__name__)
        if modulepath[0] in packagename:
            if funcobj.__name__.startswith('_'):
                continue
            setInDict(d, modulepath[1:], funcobj)

    for modulename, submodule in sub_modules:
        modulepath = submodule.__name__.split('.')
        if modulepath[0] in packagename and submodule not in visited:
            visited.add(submodule)
            recursive_extract(submodule, d, packagename, visited)

def recursive_documentation(d):
    for k, v in d.iteritems():
        if isinstance(v, dict):
            recursive_documentation(v)
        else:
            d[k] = generate_docs(v)

def getargorder(call):
    """
    Get the order of required args from a function.
    Does not support *args currently.
    """
    try:
        argorder = inspect.getargspec(call)[0]
    except:
        argorder = inspect.getargspec(call.__init__)[0][1:]  #ignore self
    return argorder

def generate_docs(v):
    docs = inspect.getdoc(v)
    if docs is None:
        print "{} ERROR: No documentation.".format(v.__name__)
        return None

    response_template = {'status':'success',
                'parameters':{'arguments':{},
			      'server':[]},
                'description':None,
                'doc_href':None,
                'methods':['GET', 'POST'],
                'name':v.__name__,
                'responses':{}}

    if not inspect.isclass(v):
        reqargs = inspect.getargspec(v)
        classtype = False
    elif inspect.isclass(v):
        '''
        I believe this has to be a try/except, because an if based hasattr(v, __init__)
        will fail because the object dict can have an __init__, but inspect does what
        we want it to and looks to the class that instantiates the object.  That class may
        not have an __init__ or the __init__ could be written in C.
        '''
        try:
            reqargs = inspect.getargspec(v.__init__)
            classtype = True
        except:
            print "{} ERROR: Class has no init method.  Unsupported doc parsing.".format(v.__name__)
            return
    else:
        print "{} ERROR: Unable to determine class or function".format(v.__name__)
        return

    args = reqargs.args

    if reqargs.defaults != None:
        defaults = list(reqargs.defaults)
    else:
        defaults = None

    if classtype == True:
        args.remove('self')

    argtype = OrderedDict()
    for a in args:
        argtype[a] = {'chain_name':'{}_href'.format(a),
                      'type':'Unknown', 'description':'None'}
    try:
        doctree = publish_doctree(docs).asdom()
        doctree = etree.fromstring(doctree.toxml())
    except:
        print "ERROR: Docutils error in {}".format(v.__name__)
        return None

    response_template['description'] = doctree[0].text
    sections = doctree.findall('section')

    parameters = {}
    attributes = {}
    documentation_extraction = {}
    for sub in doctree.findall('section'):
        key = sub.attrib['names']
        documentation_extraction[key] = {}
        for i in sub.findall('definition_list'):
            for j in i.findall('definition_list_item'):
                currententry = j.getchildren()[0].text
                if key == 'parameters':
                    documentation_extraction[key][currententry] = {'chain_name':'{}_href'.format(currententry)}#,
                                                                   #'name':'{}'.format(currententry)}
                else:
                    documentation_extraction[key][currententry] = {'chain_name':'{}_href'.format(currententry)}
                for var in j.getchildren()[1:]:
                    if var.tag == 'definition':
                        documentation_extraction[key][currententry]['description'] = var.getchildren()[0].text
                    else:
                        if var.text[0] == '{':
                            pythonliteral = eval(var.text)
                            selectiontype = type(iter(pythonliteral).next())
                            if selectiontype == str:
                                selectiontype = 'string'
                            documentation_extraction[key][currententry]['type'] = selectiontype
                            documentation_extraction[key][currententry]['options'] = var.text
                        else:
                            documentation_extraction[key][currententry]['type'] = var.text

    if 'attributes' in documentation_extraction.keys():
        response_template['responses'] = documentation_extraction['attributes']
    elif 'returns' in documentation_extraction.keys():
        response_template['responses'] = documentation_extraction['returns']
    else:
        response_template['responses'] = 'Neither class attributes nor return values defined'

    #Check for the parameters keyword. If it is not present, doc is likley not numpydoc compliant
    if not 'parameters' in documentation_extraction.keys():
        print "{} ERROR: parameters key not in extracted doc.  Is the doc string numpydoc compliant?".format(v.__name__)
        return None

    try:
        nargs = len(reqargs.args)
    except:
        nargs = 0

    try:
        ndef = len(reqargs.defaults)
    except:
        ndef = 0

    nrequired = nargs - ndef
    cdict = response_template['parameters']['arguments']
    for i in reqargs.args[:nrequired]:
        if i in documentation_extraction['parameters'].keys():
            cdict[i] = documentation_extraction['parameters'][i]
        else:
            print "{} ERROR: {} in parameter list, but not in doc string".format(v.__name__, i)

    cdict = response_template['parameters']['arguments']
    for c, i in enumerate(reqargs.args[nrequired:]):
        if i in documentation_extraction['parameters'].keys():
            cdict[i] = documentation_extraction['parameters'][i]
            cdict[i]['default'] = reqargs.defaults[c]
        else:
            print "{} ERROR: {} in parameter list, but not in doc string".format(v.__name__, i)
    return response_template
