import xml.etree.ElementTree as ET
from pydmrs.core import RealPred, GPred, Link, ListDmrs


def loads_xml(bytestring, encoding=None, cls=ListDmrs):
    """
    Currently processes "<dmrs>...</dmrs>"
    To be updated for "<dmrslist>...</dmrslist>"...
    Expects a bytestring; to load from a string instead, specify encoding
    Produces a ListDmrs by default; for a different type, specify cls
    """
    if encoding:
        bytestring = bytestring.encode(encoding)
    xml = ET.XML(bytestring)

    dmrs = cls()

    dmrs.cfrom = int(xml.get('cfrom'))
    dmrs.cto = int(xml.get('cto'))
    dmrs.surface = xml.get('surface')
    ident = xml.get('ident')
    index_id = xml.get('index')
    if ident:
        dmrs.ident = int(ident)
    if index_id:
        index_id = int(index_id)
    top_id = None

    for elem in xml:
        if elem.tag == 'node':
            nodeid = int(elem.get('nodeid'))
            cfrom = int(elem.get('cfrom'))
            cto = int(elem.get('cto'))
            surface = elem.get('surface')
            base = elem.get('base')
            carg = elem.get('carg')

            pred = None
            sortinfo = None
            for sub in elem:
                if sub.tag == 'realpred':
                    try:
                        pred = RealPred(sub.get('lemma'), sub.get('pos'), sub.get('sense'))
                    except AssertionError:
                        # If the whole pred name is under 'lemma', rather than split between 'lemma', 'pos', 'sense'
                        pred = RealPred.from_string(sub.get('lemma'))
                elif sub.tag == 'gpred':
                    pred = GPred.from_string(sub.text)
                elif sub.tag == 'sortinfo':
                    sortinfo = sub.items()
                else:
                    raise ValueError(sub.tag)

            dmrs.add_node(cls.Node(nodeid, pred, sortinfo, cfrom, cto, surface, base, carg))

        elif elem.tag == 'link':
            start = int(elem.get('from'))
            end = int(elem.get('to'))

            if start == 0:
                top_id = end
            else:
                rargname = None
                post = None
                for sub in elem:
                    if sub.tag == 'rargname':
                        rargname = sub.text
                    elif sub.tag == 'post':
                        post = sub.text
                    else:
                        raise ValueError(sub.tag)
                dmrs.add_link(Link(start, end, rargname, post))
        else:
            raise ValueError(elem.tag)

    if top_id:
        dmrs.top = dmrs[top_id]
    if index_id:
        dmrs.index = dmrs[index_id]

    return dmrs


def load_xml(filehandle, cls=ListDmrs):
    """
    Load a DMRS from a file
    NB: read file as bytes!
    Produces a ListDmrs by default; for a different type, specify cls
    """
    return cls.loads(filehandle.read(), cls=cls)


def dumps_xml(dmrs, encoding=None):
    """
    Currently creates "<dmrs>...</dmrs>"
    To be updated for "<dmrslist>...</dmrslist>"...
    Returns a bytestring; to return a string instead, specify encoding
    """
    xdmrs = ET.Element('dmrs')
    if dmrs.index is not None:
        xdmrs.set('index', str(dmrs.index.nodeid))
    if dmrs.cfrom is not None and dmrs.cto is not None:
        xdmrs.set('cfrom', str(dmrs.cfrom))
        xdmrs.set('cto', str(dmrs.cto))
    for node in dmrs.iter_nodes():
        xnode = ET.SubElement(xdmrs, 'node')
        xnode.set('nodeid', str(node.nodeid))
        if node.cfrom is not None and node.cto is not None:
            xnode.set('cfrom', str(node.cfrom))
            xnode.set('cto', str(node.cto))
        if node.carg is not None:
            xnode.set('carg', node.carg)
        if isinstance(node.pred, GPred):
            xpred = ET.SubElement(xnode, 'gpred')
            xpred.text = str(node.pred)
        elif isinstance(node.pred, RealPred):
            xpred = ET.SubElement(xnode, 'realpred')
            xpred.set('lemma', node.pred.lemma)
            xpred.set('pos', node.pred.pos)
            if node.pred.sense:
                xpred.set('sense', node.pred.sense)
        else:
            raise Exception("predicates must be RealPred or GPred objects")
        xsortinfo = ET.SubElement(xnode, 'sortinfo')
        if node.sortinfo:
            for attr in node.sortinfo:
                xsortinfo.set(attr, node.sortinfo[attr])
    if dmrs.top is not None:
        xlink = ET.SubElement(xdmrs, 'link')
        xlink.set('from', '0')
        xlink.set('to', str(dmrs.top.nodeid))
        xrargname = ET.SubElement(xlink, 'rargname')
        xpost = ET.SubElement(xlink, 'post')
        xpost.text = 'H'
    for link in dmrs.iter_links():
        xlink = ET.SubElement(xdmrs, 'link')
        xlink.set('from', str(link.start))
        xlink.set('to', str(link.end))
        xrargname = ET.SubElement(xlink, 'rargname')
        xrargname.text = link.rargname
        xpost = ET.SubElement(xlink, 'post')
        xpost.text = link.post
    bytestring = ET.tostring(xdmrs)
    if encoding:
        return bytestring.decode(encoding)
    return bytestring


def dump_xml(filehandle, dmrs):
    """
    Dump a DMRS to a file
    NB: write as a bytestring!
    """
    filehandle.write(dumps_xml(dmrs))


def visualise(dmrs, format):
    """
    Returns the bytestring of the chosen visualisation representation.
    Supported formats: dot
    """
    if format == 'dot':
        dot_strs = []
        dot_strs.append('digraph g {\n')
        if dmrs.top is not None:
            dot_strs.append('NodeTop [label="top",style=bold];\n')
        dot_strs.append('node[shape=box];\n')
        for nodeid in dmrs:
            node = dmrs[nodeid]
            dot_strs.append('Node{} [label=<{}<BR /><FONT POINT-SIZE="10">{}</FONT>>];\n'.format(nodeid, node.pred, node.sortinfo))
        dot_strs.append('edge[fontsize=10];\n')
        if dmrs.top is not None:
            dot_strs.append('NodeTop -> Node{} [style=dotted];\n'.format(dmrs.top.nodeid))
        for link in dmrs.links:
            dot_strs.append('Node{} -> Node{} [label="{}"];\n'.format(link.start, link.end, link.labelstring))
        dot_strs.append('}\n')
        dot_str = ''.join(dot_strs)
        return dot_str.encode()
    else:
        raise NotImplementedError