#!/usr/bin/env python

import json
import yaml
import csv
import copy

def unicode_representer(dumper, uni):
    node = yaml.ScalarNode(tag=u'tag:yaml.org,2002:str', value=uni)
    return node


def readofficialservicecsv():
    official = {}
    with open('openstack.projects.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar="'")
        for row in csvreader:
            official[row[0].lower()] = {
                "service_name": row[0],
                'description': row[1],
                'service_group': row[2]
            }
    return official


def match_official_service(officialservices, reponame):
   # For some reasons out of the 10 installers only 3 are listed
    servicenames = set(copy.deepcopy(officialservices.keys()))
    servicenames.remove('tripleo')
    servicenames.remove('kolla')
    servicenames.remove('openstack-ansible')
    for servicename in servicenames:
        if servicename in reponame:
            return servicename
    return "Unknown"


def readofficialprojectyaml():
    official = {}
    with open('projects.yaml', 'rb') as yamlfile:
        official = yaml.safe_load(yamlfile)
    return official


def find_official_project(officialprojects, reponame):
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
    with open('openstack.repos.csv', 'rb') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',', quotechar="'")
        for row in csvreader:
            official[row[0]] = row[1]
    return official


def find_official_repo(officialrepos, subrepo):
    if subrepo in officialrepos:
        officialrepoclass = officialrepos[subrepo]
        officialrepos.pop(subrepo)
    else:
        officialrepoclass = 'Unknown'
    return officialrepoclass


def update_classification(repo, iproject, iclass):
    repo.update({'matched_project': iproject, 'matched_classification': iclass})

# WARNING. Order is important
STARTS_WITH = [
    ('puppet-', 'puppet', 'installer'),
    ('ansible-role-', 'tripleo', 'installer'),
    ('ansible-', 'ansible', 'installer'),
    ('fuel-cpp-', 'fuel-cpp', 'installer'),
    ('fuel-', 'fuel', 'installer'),
    ('openstack-ansible-', 'openstack-ansible', 'installer'),
    ('tripleo-', 'tripleo', 'installer'),
    ('cookbook-', 'chef', 'installer'),
    ('charm-', 'charm', 'installer'),
    ('snap-', 'snap', 'installer'),
    ('salt-formula-', 'salt', 'installer'),
    ('airship-', 'helm', 'installer'),
    ('openstack-helm', 'helm', 'installer'),
    ('xstatic-', 'xstatic', 'packaging'),
    ('deb-', 'deb', 'packaging'),
    ('kolla-', 'kolla', 'packaging'),
    ('loci', 'loci', 'packaging'),
    ('rpm-packaging', 'rpm-packaging', 'packaging'),
    ('devstack-', 'devstack', 'testing'),
    ('tempest-', 'tempest', 'testing'),
    ('oslo', 'oslo', 'library'),
    ('networking-', 'neutron', 'service'),
    ('python-', 'python', 'openstack'),
    ('stx-', 'starlingx', 'openstack'),
    ('stacktach-', 'stacktach', 'openstack')
]

ENDS_WITH = [
    ('-tempest-plugin', 'tempest', 'testing'),
    ('-specs', 'openstack', 'documentation')
]


def readrepolist(fulldict, officialservices, officialprojects, officialrepos):
    with open('review.openstack.org.json', 'r') as f:
        repolist = json.load(f)

    for repo in repolist.keys():
        reposubstr = repo.split("/")
        mainrepo = reposubstr[0]
        subrepo = reposubstr[1] if len(reposubstr) == 2 else "all"

        matched_service = match_official_service(officialservices, subrepo)
        matched_project = mainrepo if mainrepo != 'openstack' else 'unknown'
        matched_classification = 'unknown'

        official_project = find_official_project(officialprojects, repo)
        official_repoclass = find_official_repo(officialrepos, subrepo)

        repodesc = {'url': repolist[repo]['web_links'][0]['url']}
        repodesc.update({'fullname': repo,
                         'matched_service': matched_service,
                         'matched_project': matched_project,
                         'matched_classification': matched_classification,
                         'official_classification': official_repoclass,
                         'official_project': official_project})

        rulename = None
        for rule in STARTS_WITH:
            if not rulename and subrepo.startswith(rule[0]):
                rulename = rule[0]
                update_classification(repodesc, rule[1], rule[2])

        for rule in ENDS_WITH:
            if not rulename and subrepo.endswith(rule[0]):
                rulename = rule[0]
                update_classification(repodesc, rule[1], rule[2])

        if (not rulename) and (mainrepo == "openstack") and official_project != 'Unknown':
           update_classification(repodesc, official_project, 'service') 

        fulldict[mainrepo][subrepo] = repodesc


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

    officialservices = readofficialservicecsv()
    officialprojects = readofficialprojectyaml()
    officialrepos = readofficialrepo()
    readrepolist(fulldict, officialservices, officialprojects, officialrepos)
    dumpyaml(fulldict)

    showinconsistencies(officialprojects, officialrepos)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Git Repo Classification')
    args = parser.parse_args()
    main(args)
