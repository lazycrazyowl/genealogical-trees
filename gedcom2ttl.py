#!/usr/bin/env python

# This script converts GEDCOM genealogy members
# to the FHKB turtle semantic web ontology individuals.
# (A header with FHKB ontology definitions is still required.)
# TODO adoptive families (>1) are not considered (TODO?)
# Author: Evgeny Blokhin
# License: MIT

import os, sys
from gedcom import Gedcom


try: workpath = sys.argv[1]
except IndexError: sys.exit("No gedcom defined!")

def term2id(el):
    return "i" + el.pointer().replace('@', '').lower()

g = Gedcom(workpath)
gedcom_dict = g.element_dict()
failed, considered = [], []

for k, v in gedcom_dict.iteritems():
    if v.is_individual():
        added_terms = ''

        if v.gender().lower() == 'm': parent_predicate, sibl_predicate = "isFatherOf", "isBrotherOf"
        else:                         parent_predicate, sibl_predicate = "isMotherOf", "isSisterOf"

        own_families = g.families(v, 'FAMS')
        children = []
        
        for fam in own_families:
            children += [term2id(i) for i in g.get_family_members(fam, "CHIL")]

        if children:
            added_terms += " ;\n    fhkb:" + parent_predicate + " " + ", ".join(["fhkb:" + i for i in children])

        parent_families = g.families(v, 'FAMC')
        if len(parent_families):
            siblings = []
            for member in g.get_family_members(parent_families[0], "CHIL"): # NB adoptive families (>1) are not considered (TODO?)
                if member.pointer() == v.pointer():
                    continue
                siblings.append(term2id(member))
            if siblings:
                added_terms += " ;\n    fhkb:" + sibl_predicate + " " + ", ".join(["fhkb:" + i for i in siblings])

        orig = v.name()[0].decode('utf8').encode('ascii', 'xmlcharrefreplace') + " " + v.name()[1].decode('utf8').encode('ascii', 'xmlcharrefreplace')
        orig = orig.replace('"', '').replace('[', '').replace(']', '').replace('(', '').replace(')', '').strip()
        print "fhkb:%s a owl:NamedIndividual, owl:Thing%s ;\n    rdfs:label \"%s\" .\n" % (term2id(v), added_terms, orig)

    elif v.is_family():
        try:
            wife = g.get_family_members(v, "WIFE")[0]
            husb = g.get_family_members(v, "HUSB")[0]
        except IndexError:
            failed.append(term2id(v))
            continue
        else:
            chk = term2id(wife) + term2id(husb)
            if chk in considered:
                failed.append(term2id(v))
                continue
            considered.append(chk)
        print "fhkb:%s a owl:NamedIndividual, owl:Thing ;\n    fhkb:hasFemalePartner fhkb:%s ;\n    fhkb:hasMalePartner fhkb:%s .\n" % (term2id(v), term2id(wife), term2id(husb))

print "[] a owl:AllDifferent ;\n    owl:distinctMembers ("
for k, v in gedcom_dict.iteritems():
    if not v.is_individual() and not v.is_family(): continue
    t = term2id(v)
    if not t in failed: print "    fhkb:" + t
print "    ) ."
