import sys
from pydmrs.core import Dmrs, ListDmrs
from pydmrs.mapping.mapping import dmrs_mapping
from pydmrs.graphlang.graphlang import parse_graphlang


def read_paraphrases_file(filename):
    """
    """
    paraphrases = []
    file = open(filename, 'r')
    lines = iter(file)
    for line in lines:
        try:
            # equalities etc
            paraphrases.append((parse_graphlang(line), parse_graphlang(next(lines))))
        except StopIteration:
            assert False, 'Invalid paraphrases file format.'
        try:
            assert not next(lines)
        except StopIteration:
            break
    return paraphrases


def paraphrase(dmrs, paraphrases, hierarchy=None):
    """
    """
    assert isinstance(dmrs, Dmrs), 'Object in dmrs_iter is not a Dmrs.'
    for (search_dmrs, replace_dmrs) in paraphrases:
        paraphrased_dmrs = dmrs_mapping(dmrs, search_dmrs, replace_dmrs, hierarchy=hierarchy)
        if paraphrased_dmrs is None:
            break
        else:
            dmrs = paraphrased_dmrs
    return dmrs


if __name__ == '__main__':
    assert len(sys.argv) == 2 and not sys.stdin.isatty(), 'Invalid arguments'
    paraphrases = read_paraphrases_file(sys.argv[1])
    for line in sys.stdin:
        dmrs = ListDmrs.loads_xml(line[:-1])
        sys.stdout.write(str(paraphrase(dmrs, paraphrases)) + '\n')
