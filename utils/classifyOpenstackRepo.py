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
            repos = deliverartifact['repos'] if 'repos' in deliverartifact else []
            if reponame in repos:
                repos.remove(reponame)
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

def update_classification(repo, iproject, iclass):
    repo.update({'internal_project': iproject, 'internal_classification': iclass})

# WARNING. Order is important
STARTS_WITH=[
    ('puppet-','puppet', 'installer'),
    ('ansible-role-','tripleo', 'installer'),
    ('ansible-','ansible', 'installer'),
    ('fuel-cpp-','fuel-cpp', 'installer'),
    ('fuel-','fuel', 'installer'),
    ('openstack-ansible-','openstack-ansible', 'installer'),
    ('tripleo-','tripleo', 'installer'),
    ('cookbook-','chef', 'installer'),
    ('charm-','charm', 'installer'),
    ('snap-','snap', 'installer'),
    ('salt-formula-','salt', 'installer'),
    ('airship-','helm', 'installer'),
    ('openstack-helm','helm', 'installer'),
    ('xstatic-','xstatic', 'packaging'),
    ('deb-','deb', 'packaging'),
    ('kolla-','kolla', 'packaging'),
    ('loci','loci', 'packaging'),
    ('devstack-','devstack', 'testing'),
    ('tempest-','tempest', 'testing'),
    ('oslo','oslo', 'openstack'),
    ('python-','python', 'openstack'),
    ('stx-','starlingx', 'openstack'),
    ('stacktach-','stacktach', 'openstack')
]

ENDS_WITH=[
    ('-tempest-plugin','tempest', 'testing')
]

def readrepolist(fulldict, officialprojects, officialrepos):
    with open('review.openstack.org.json', 'r') as f:
        repolist = json.load(f)

    for repo in repolist.keys():
        substr = repo.split("/")
        maindict = substr[0]
        subdict = substr[1] if len(substr) == 2 else "all"

        officialproject = findproject(officialprojects, repo)
        officialrepoclass = findrepo(officialrepos, subdict)

        repodesc = {'url': repolist[repo]['web_links'][0]['url']}
        repodesc.update({'fullname': repo,
                         'internal_project': maindict, 
                         'internal_classification': 'unknown',
                         'official_classification': officialrepoclass,
                         'official_project': officialproject})

        rulename = None 
        for rule in STARTS_WITH:
            if not rulename and subdict.startswith(rule[0]):
                rulename = rule[0]
                update_classification(repodesc ,rule[1], rule[2])

        for rule in ENDS_WITH:
            if not rulename and subdict.endswith(rule[0]):
                rulename = rule[0]
                update_classification(repodesc ,rule[1], rule[2])

        if not rulename and maindict == "openstack":
            # print repo
            pass

        fulldict[maindict][subdict] = repodesc


def dumpyaml(fulldict):
    yaml.add_representer(unicode, unicode_representer)

    with open('review.openstack.org.yaml', 'w') as outfile:
        yaml.dump(fulldict, outfile, default_flow_style=False)

    with open('../openstackrepolist.yaml', 'w') as outfile:
        yaml.dump(fulldict['openstack'], outfile, default_flow_style=False)


def showinconsistencies(officialprojects, officialrepos):
    # Show detected issues
    if officialrepos:
        print officialrepos

    for projectname, projectdesc in officialprojects.items():
        deliverables = projectdesc['deliverables'] if 'deliverables' in projectdesc else {}
        for delivername, deliverartifact in deliverables.items():
            repos = deliverartifact['repos'] if 'repos' in deliverartifact else []
            if repos:
                print "{}.{} still contains reference to {}".format(projectname, delivername, repr(repos))

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

    showinconsistencies(officialprojects, officialrepos)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Git Repo Classification')
    args = parser.parse_args()
    main(args)
