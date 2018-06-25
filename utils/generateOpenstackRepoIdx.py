#!/usr/bin/env python

import json
import yaml
import csv
import copy
from jinja2 import Environment, FileSystemLoader

def unicode_representer(dumper, uni):
    node = yaml.ScalarNode(tag=u'tag:yaml.org,2002:str', value=uni)
    return node

def readopenstackrepolistyaml():
    official = {}
    with open('../openstackrepolist.yaml', 'rb') as yamlfile:
        official = yaml.safe_load(yamlfile)
    return official

def rendertemmplate(fulldict, newfile):
    context={ 'thedict': fulldict, 'title': title }
    theenv = Environment(autoescape=False,
                         loader=FileSystemLoader('./'),
                         trim_blocks=False)
    thetemplate = theenv.get_template("template.j2")

    try:
        fh = open(newfile, "wt")
        fh.write(template.render(context))
        fh.close()
    except Exception as e:
        print e

def dumpyaml(fulldict, filename):
    yaml.add_representer(unicode, unicode_representer)

    with open(filename, 'w') as outfile:
        yaml.dump(fulldict, outfile, default_flow_style=False)

def dumpdoc(fulldict):
    print "\n".join(printhelp.print_help_msg(mainentrypoint.cli, ['aiclcm']))

def sortby(fulldict, newkey):
    res={}
    for key, value in fulldict.items():
        newidxvalue = value[newkey]
        if newidxvalue not in res:
            res[newidxvalue] = []
        res[newidxvalue].append(value)
    return res        
    
def main(args):
    repolist = readopenstackrepolistyaml()

    res = sortby(repolist, 'matched_classification')
    dumpyaml(res, '../classification.yaml')

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Git Repo Classification')
    args = parser.parse_args()
    main(args)