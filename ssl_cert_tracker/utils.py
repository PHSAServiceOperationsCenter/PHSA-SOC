"""
.. _models:

django models for the ssl_certificates app

:module:    utils.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import logging
from dateutil import parser
import xml.dom.minidom

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)


def validate(date_text):
    """check if date_text is a valid date  """
    try:
        parser.parse(date_text)
        return True
    except TypeError:
        return False
    except IndexError:
        return False
    except ValueError:
        return False


def init_record():
    """Initialize json object"""
    record = {
        "xml_data": None,
        "addresses": None,
        "node_id": None,
        "common_name": None,
        "country_name": None,
        "organization_name": None,
        "sig_algo": None,
        "name": None,
        "bits": None,
        "md5": None,
        "sha1": None,
        "not_before": None,
        "not_after": None
    }
    return record


def check_tag(elem, record, k, tag):
    """populate json object from xml tags"""
    try:
        if elem.getAttribute("key") == tag:
            if record[k] is None:
                record[k] = elem.childNodes[0].nodeValue
    except IndexError as ex:
        record[k] = None
        logging.info("nMap Record does not have commonName tag:%s", str(ex))
    except xml.parsers.expat.ExpatError as ex:
       # logging.info("nMap Record does not have commonName tag:%s", ex.msg)
        print("nMap Record does not have commonName tag:%s" + ex.msg)


def process_xml_cert(node_id, doc):
    """process xml from dom object"""
    for host in doc.getElementsByTagName("host"):
        scripts = host.getElementsByTagName("script")
        record = init_record()
        record["xml_data"] = doc
        record["addresses"] = host.getElementsByTagName("address")
        record["node_id"] = node_id
        for script in scripts:
            for elem in script.getElementsByTagName("elem"):
                check_tag(elem, record, "common_name", "commonName")
                check_tag(elem, record, "organization_name",
                          "organizationName")
                check_tag(elem, record, "country_name", "countryName")
                check_tag(elem, record, "sig_algo", "sig_algo")
                check_tag(elem, record, "name", "name")
                check_tag(elem, record, "bits", "bits")
                check_tag(elem, record, "not_before", "notBefore")
                check_tag(elem, record, "not_after", "notAfter")
                check_tag(elem, record, "md5", "md5")
                check_tag(elem, record, "sha1", "sha1")
        return record
