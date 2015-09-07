import inspect

import lymph
from lymph.core.decorators import RPCBase

import sphinx
from sphinx.ext.autodoc import MethodDocumenter, ClassDocumenter, setup as autodoc_setup


class RPCMethodDocumenter(MethodDocumenter):
    """Documenter for RPC methods."""

    # Priority must be higher than AttributeDocumenter since the data
    # descriptor RPC decorator should treated in documentation as a
    # method and not an attribute.
    priority = 11

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        return isinstance(member, RPCBase)

    def format_args(self):
        """Override argument extraction by getting it from RPC decorator."""
        args = inspect.formatargspec(*self.object.args)
        return args.replace('\\', '\\\\')

    def generate(self, *args, **kwargs):
        super(RPCMethodDocumenter, self).generate(*args, **kwargs)
        # If RPC decorator define exception to raise (e.g. _RPCDecorator),
        # include this laters in the documentation of the method.
        raises = getattr(self.object, 'raises', ())
        if not isinstance(raises, tuple):
            raises = (raises, )
        for ex in raises:
            self.add_line(u':raises %s: %s' % (ex.__name__, ex.__doc__), '<autodoc>')


class RPCInterfaceDocumenter(ClassDocumenter):
    """Documenter for RPC Lymph Interfaces."""

    @classmethod
    def can_document_member(cls, member, membername, isattr, parent):
        document = super(RPCInterfaceDocumenter, cls).can_document_member(member, membername, isattr, parent)
        return document and issubclass(member, lymph.Interface)

    def format_args(self):
        """Return empty since we don't want to document Interface __init__ argument
        since they are irrelevant for service usage.
        """
        return ''

    def filter_members(self, members, want_all):
        """Filter interface attribute to only document RPC methods."""
        members = super(RPCInterfaceDocumenter, self).filter_members(members, want_all)
        ret = []
        for name, obj, isattr in members:
            if isinstance(obj, RPCBase):
                ret.append((name, obj, isattr))
        return ret


def setup(app):
    autodoc_setup(app)

    app.add_autodocumenter(RPCMethodDocumenter)
    app.add_autodocumenter(RPCInterfaceDocumenter)

    return sphinx.__version__
