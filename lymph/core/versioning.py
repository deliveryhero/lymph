from semantic_version import Version, Spec
import six


def parse_versioned_name(name):
    if '@' not in name:
        return name, None
    name, version = name.split('@', 1)
    return name, Version.coerce(version)


def compatible(v):
    return Spec('>=%s,<%s' % (v, v.next_major()))


def get_lymph_version():
    import lymph
    return lymph.__version__


def serialize_version(version):
    if not version:
        return None
    return six.text_type(version)
