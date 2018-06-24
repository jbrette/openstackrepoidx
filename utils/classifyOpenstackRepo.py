#!/usr/bin/env python

import json
import yaml
import csv


def unicode_representer(dumper, uni):
    node = yaml.ScalarNode(tag=u'tag:yaml.org,2002:str', value=uni)
    return node


def readofficialprojectcsv():
    official = {}
    with open('official.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar="'")
        for row in csvreader:
            official[row[0]] = row[1]
    return official


def readofficialprojectyaml():
    official = {}
    with open('projects.yaml', 'rb') as yamlfile:
        official = yaml.safe_load(yamlfile)
    return official


def findproject(officialprojects, reponame):
    for projectname, projectdesc in officialprojects.items():
        deliverables = projectdesc['deliverables'] if 'deliverables' in projectdesc else {}
        for delivername, deliverartifact in deliverables.items():
            repos = deliverartifact['repos'] if 'repos' in deliverartifact else {}
            if reponame in repos:
                return projectname
    return "Unknown"


def readofficialrepo():
    official = {}
    with open('openstackrepo.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar="'")
        for row in csvreader:
            official[row[0]] = row[1]
    return official


def findrepo(officialrepos, subdict):
    if subdict in officialrepos:
        officialrepoclass = officialrepos[subdict]
        officialrepos.pop(subdict)
    else:
        officialrepoclass = 'Unknown'
    return officialrepoclass


def readrepolist(fulldict, officialprojects, officialrepos):
    with open('openstackrepolist.json', 'r') as f:
        repolist = json.load(f)

    for repo in repolist.keys():
        substr = repo.split("/")
        maindict = substr[0]
        subdict = substr[1] if len(substr) == 2 else "all"

        officialproject = findproject(officialprojects, repo)
        officialrepoclass = findrepo(officialrepos, subdict)

        fulldict[maindict][subdict] = {'url': repolist[repo]['web_links'][0]['url']}
        fulldict[maindict][subdict].update({'fullname': repo,
                                            'internal_project': 'unknown', 'internal_classification': 'unknown',
                                            'official_classification': officialrepoclass,
                                            'official_project': officialproject})

        if subdict.startswith('puppet-'):
            fulldict[maindict][subdict].update({'internal_project': 'puppet', 'internal_classification': 'installer'})
        elif subdict.startswith('ansible-'):
            fulldict[maindict][subdict].update({'internal_project': 'ansible', 'internal_classification': 'installer'})
        elif subdict.startswith('fuel-'):
            fulldict[maindict][subdict].update({'internal_project': 'fuel', 'internal_classification': 'installer'})
        elif subdict.startswith('openstack-ansible-'):
            fulldict[maindict][subdict].update({'internal_project': 'openstack-ansible', 'internal_classification': 'installer'})
        elif subdict.startswith('tripleo-'):
            fulldict[maindict][subdict].update({'internal_project': 'tripleo', 'internal_classification': 'installer'})
        elif subdict.startswith('cookbook-'):
            fulldict[maindict][subdict].update({'internal_project': 'chef', 'internal_classification': 'installer'})
        elif subdict.startswith('charm-'):
            fulldict[maindict][subdict].update({'internal_project': 'charm', 'internal_classification': 'installer'})
        elif subdict.startswith('snap-'):
            fulldict[maindict][subdict].update({'internal_project': 'snap', 'internal_classification': 'installer'})
        elif subdict.startswith('salt-formula-'):
            fulldict[maindict][subdict].update({'internal_project': 'salt', 'internal_classification': 'installer'})
        elif subdict.startswith('airship-'):
            fulldict[maindict][subdict].update({'internal_project': 'helm', 'internal_classification': 'installer'})
        elif subdict.startswith('openstack-helm'):
            fulldict[maindict][subdict].update({'internal_project': 'helm', 'internal_classification': 'installer'})
        elif subdict.startswith('xstatic-'):
            fulldict[maindict][subdict].update({'internal_project': 'xstatic', 'internal_classification': 'packaging'})
        elif subdict.startswith('deb-'):
            fulldict[maindict][subdict].update({'internal_project': 'deb', 'internal_classification': 'packaging'})
        elif subdict.startswith('kolla-'):
            fulldict[maindict][subdict].update({'internal_project': 'kolla', 'internal_classification': 'packaging'})
        elif subdict.startswith('loci'):
            fulldict[maindict][subdict].update({'internal_project': 'loci', 'internal_classification': 'packaging'})
        elif subdict.startswith('devstack-'):
            fulldict[maindict][subdict].update({'internal_project': 'devstack', 'internal_classification': 'testing'})
        elif subdict.startswith('tempest-'):
            fulldict[maindict][subdict].update({'internal_project': 'tempest', 'internal_classification': 'testing'})
        elif subdict.startswith('oslo'):
            fulldict[maindict][subdict].update({'internal_project': 'oslo', 'internal_classification': 'openstack'})
        elif subdict.startswith('python-'):
            fulldict[maindict][subdict].update({'internal_project': 'python', 'internal_classification': 'openstack'})
        elif subdict.startswith('stx-'):
            fulldict[maindict][subdict].update({'internal_project': 'starlingx', 'internal_classification': 'openstack'})
        elif subdict.startswith('stacktach-'):
            fulldict[maindict][subdict].update({'internal_project': 'stacktach', 'internal_classification': 'openstack'})
        elif subdict.endswith('-tempest-plugin'):
            fulldict[maindict][subdict].update({'internal_project': 'tempest', 'internal_classification': 'testing'})
        else:
            if maindict == "openstack":
                # print repo
                pass


def dumpyaml(fulldict):
    yaml.add_representer(unicode, unicode_representer)
    print yaml.dump(fulldict, default_flow_style=False)

    # for key,value in fulldict.items():
    #   print "{} has {} repos".format(key,len(value.keys()))


def main(args):
    fulldict = {
        'All-Projects': {},
        'All-Users': {},
        'API-Projects': {},
        'openstack': {},
        'openstack-attic': {},
        'openstack-dev': {},
        'openstack-infra': {},
        'stackforge': {},
        'stackforge-attic': {}
    }

    officialprojectcsv = readofficialprojectcsv()
    officialprojects = readofficialprojectyaml()
    officialrepos = readofficialrepo()
    readrepolist(fulldict, officialprojects, officialrepos)
    dumpyaml(fulldict)

    if officialrepos:
        print officialrepos

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Git Repo Classification')
    args = parser.parse_args()
    main(args)
