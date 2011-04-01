# Copyright (c) 2011, Florian Mayer <flormayer@aim.com>
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

from copy import deepcopy

SHIFT = 5
BMAP = (1 << SHIFT) - 1
BRANCH = 2 ** SHIFT

MAXBITMAPDISPATCH = 16

def relevant(hsh, shift):
    """ Return the relevant part of the hsh on the level shift. """
    return hsh >> shift & BMAP


POPCOUNT_TBL = [0] * (2 ** 16)
for idx in xrange(2 ** 16):
    POPCOUNT_TBL[idx] = (idx & 1) + POPCOUNT_TBL[idx >> 1]

def bit_count(v):
    return (POPCOUNT_TBL[v & 0xffff] +
            POPCOUNT_TBL[(v >> 16) & 0xffff])


def doc(docstring):
    """ Decorator to set docstring of function to docstring. """
    def deco(fn):
        """ Implementation detail. """
        fn.__doc__ = docstring
        return fn
    return deco


ASSOC = "\n".join([
    "Add AssocNode node whose key's hash is hsh to the node or its children.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH. If a node with the same key already",
    "exists, override it.",
])

IASSOC = "\n".join([
    "Modify so that the AssocNode whose key's hash is hsh is added to it.",
    "USE WITH CAUTION.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH. If a node with the same key already",
    "exists, override it.",
])

GET = "\n".join([
    "Get value of the AssocNode with key whose hash is hsh in the subtree.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH.",
])

WITHOUT = "\n".join([
    "Remove AssocNode with key whose hash is hsh from the subtree.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH.",
])

IWITHOUT = "\n".join([
    "Modify so that the AssocNode whose key's hash is hsh is removed from it.",
    "USE WITH CAUTION.",
    "shift refers to the current level in the tree, which must be a multiple",
    "of the global constant BRANCH.",
])

class NullNode(object):
    """ Dummy node being the leaf of branches that have no entries. """
    __slots__ = []
    def xor(self, hsh, shift, node):
        return node    
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # Because there currently no node, the new node
        # is the node to be added.
        return node
    
    # The NullNode does not need to be modified if a new association is
    # created because it only returns the new node, hence _iassoc = assoc.
    _iassoc = assoc
    
    def get(self, hsh, shift, key):
        # There is no entry with the searched key because the hash leads
        # to a branch ending in a NullNode.
        raise KeyError(key)
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        # There is no entry with the key to be removed because the hash leads
        # to a branch ending in a NullNode.
        raise KeyError(key)
    
    _iwithout = without
    
    def __iter__(self):
        # There are no keys contained in a NullNode. Hence, an empty
        # iterator is returned.
        return iter([])
    
    # Likewise, there are no values and items in a NullNode.
    iteritems = itervalues = __iter__

# We only need one instance of a NullNode because it does not contain
# any data.
NULLNODE = NullNode()


class SetNode(object):
    """ A AssocNode contains the actual key-value mapping. """
    __slots__ = ['key', 'hsh']
    def __init__(self, key):
        self.key = key
        self.hsh = hash(key)
    
    def xor(self, hsh, shift, node):
        if node.key == self.key:
            return NULLNODE
        else:
            return self.assoc(hsh, shift, node)
    
    @doc(GET)
    def get(self, hsh, shift, key):
        # If the key does not match the key of the AssocNode, thus the hash
        # matches to the current level, but it is not the correct node,
        # raise a KeyError, otherwise return the value.
        if key != self.key:
            raise KeyError(key)
        return self
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # If there is a hash-collision, return a HashCollisionNode,
        # otherwise return a DispatchNode dispatching depending on the
        # current level (if the two hashes only differ at a higher-level,
        # DispatchNode.make will return a DispatchNode that contains a
        # DispatchNode etc. up until the necessary depth.
        if node.key == self.key:
            return node
        
        if hsh == self.hsh:
            return HashCollisionNode(
                [self, node]
            )
        return DispatchNode.make(shift, [self, node])
    
    @doc(IASSOC)
    def _iassoc(self, hsh, shift, node):
        if node.key == self.key:
            self.key = node.key
            self.value = node.value
            return self
        
        if hsh == self.hsh:
            return HashCollisionNode(
                [self, node]
            )
        return DispatchNode.make(shift, [self, node])        
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        # If the key matches the key of this AssocNode, returning NULLNODE
        # will remove the Node from the map. Otherwise raise a KeyError.
        if key != self.key:
            raise KeyError(key)
        return NULLNODE
    
    _iwithout = without
    
    def __iter__(self):
        yield self


class AssocNode(SetNode):
    """ A AssocNode contains the actual key-value mapping. """
    __slots__ = ['value']
    def __init__(self, key, value):
        SetNode.__init__(self, key)
        self.value = value
    
    def __repr__(self):
        return '<AssocNode(%r, %r)>' % (self.key, self.value)


class HashCollisionNode(object):
    """ If hashes of two keys collide, store them in a list and when a key
    is searched, iterate over that list and find the appropriate key. """
    __slots__ = ['children']
    def __init__(self, nodes):
        self.children = nodes
        self.hsh = hash(nodes[0].hsh)

    def xor(self, hsh, shift, node):
        if not any(node.key == child.key for child in self.children):
            return HashCollisionNode(self.children + [node])
        return self    
    
    @doc(GET)
    def get(self, hsh, shift, key):
        # To get the child we want we need to iterate over all possible ones.
        # The contents of children are always AssocNodes,
        # so we can safely access the key member.
        for node in self.children:
            if key == node.key:
                return node
        raise KeyError(key)
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # If we have yet another key with a colliding key, return a new node
        # with it added to the children, otherwise return a DispatchNode.
        if hsh == self.hsh:
            return HashCollisionNode(self.children + [node])
        return DispatchNode.make(shift, [self, node])
    
    @doc(IASSOC)
    def _iassoc(self, hsh, shift, node):
        # If we have yet another key with a colliding key, add it to the
        # children, otherwise return a DispatchNode.
        if hsh == self.hsh:
            self.children.append(node)
            return self
        return DispatchNode.make(shift, [self, node])        
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        # Remove the node whose key is key from the children. If it was the
        # last child, return NULLNODE. If there was no member with a
        # matching key, raise KeyError.
        newchildren = [node for node in self.children if node.key != key]
        if not newchildren:
            return NULLNODE
        
        if newchildren == self.children:
            raise KeyError(key)
        
        return HashCollisionNode(newchildren)
    
    @doc(IWITHOUT)
    def _iwithout(self, hsh, shift, key):
        newchildren = [node for node in self.children if node.key != key]
        if not newchildren:
            return NULLNODE
        
        if newchildren == self.children:
            raise KeyError(key)
        
        self.children = newchildren
        return self
    
    def __iter__(self):
        for node in self.children:
            for elem in node:
                yield elem


class ListDispatch(object):
    """ Light weight dictionary like object for a little amount of items.
    Only feasable for a little amount of items as a list of length nitems 
    is always stored.
    
    Only accepts integers as keys. """
    __slots__ = ['items']
    sentinel = object()
    
    def __init__(self, nitems=None, items=None):
        if items is None:
            items = [self.sentinel for _ in xrange(nitems)]
        self.items = items
    
    def replace(self, key, item):
        """ Return a new ListDispatch with the the keyth item replaced
        with item. """
        return ListDispatch(
            None,
            self.items[:key] +
            [item] +
            self.items[key + 1:]
        )
    
    def _ireplace(self, key, item):
        """ Replace keyth item with item.
        
        USE WITH CAUTION. """
        self.items[key] = item
        return self
    
    def __getitem__(self, key):
        value = self.items[key]
        if value is self.sentinel:
            raise KeyError(key)
        return value
    
    def get(self, key, default):
        """ Get keyth item. If it is not present, return default. """
        value = self.items[key]
        if value is not self.sentinel:
            return value
        return default
    
    def remove(self, key):
        """ Return new ListDispatch with keyth item removed.
        Will not raise KeyError if it was not present. """
        if len(self.items) <= MAXBITMAPDISPATCH:
            new = self.to_listdispatch(len(self.items))
            return new._iremove(key)
        
        return self.replace(key, self.sentinel)

    def _iremove(self, key):
        """ Remove keyth item. Will not raise KeyError if it was not present.
        
        USE WITH CAUTION. """
        if len(self.items) <= MAXBITMAPDISPATCH:
            new = self.to_listdispatch(len(self.items))
            return new._iremove(key)
        
        self._ireplace(key, self.sentinel)
        return self
    
    def to_bitmapdispatch(self):
        dispatch = BitMapDispatch()
        for key, value in enumerate(self.items):
            if value is not self.sentinel:
                dispatch._ireplace(key, value)
        return dispatch
    
    def __iter__(self):
        return (item for item in self.items if item is not self.sentinel)


class BitMapDispatch(object):
    """ Light weight dictionary like object for a little amount of items.
    Best used for as most as many items as an integer has bits (usually 32).
    Only accepts integers as keys.
    
    The items are stored in a list and whenever an item is added, the bitmap
    is ORed with (1 << key) so that the keyth bit is set.
    The amount of set bits before the nth bit is used to find the index of the
    item referred to by key in the items list.
    """
    __slots__ = ['bitmap', 'items']
    def __init__(self, bitmap=0, items=None):
        if items is None:
            items = []
        self.bitmap = bitmap
        self.items = items
    
    def replace(self, key, item):
        """ Return a new BitMapDispatch with the the keyth item replaced
        with item. """
        if len(self.items) > MAXBITMAPDISPATCH:
            new = self.to_listdispatch(BRANCH)
            return new._ireplace(key, item)
        
        # If the item already existed in the list, we need to replace it.
        # Otherwise, it will be added to the list at the appropriate
        # position.
        notnew = bool(self.bitmap & 1 << key)
        newmap = self.bitmap | 1 << key
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        return BitMapDispatch(
            newmap,
            # If notnew is True, the item that is replaced by the new item
            # is left out, otherwise the new item is inserted. Refer to
            # _ireplace for a more concise explanation.
            self.items[:idx] + [item] + self.items[idx+notnew:]
        )
    
    def _ireplace(self, key, item):
        """ Replace keyth item with item.
        
        USE WITH CAUTION. """
        if len(self.items) > MAXBITMAPDISPATCH:
            new = self.to_listdispatch(BRANCH)
            return new._ireplace(key, item)
        
        notnew = bool(self.bitmap & 1 << key)
        self.bitmap |= 1 << key
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        if idx == len(self.items):
            self.items.append(item)
        elif notnew:
            self.items[idx] = item
        else:
            self.items.insert(idx, item)
        
        return self
    
    def get(self, key, default=None):
        """ Get keyth item. If it is not present, return default. """
        if not self.bitmap & 1 << key:
            return default
        return self.items[bit_count(self.bitmap & ((1 << key) - 1))]
    
    def remove(self, key):
        """ Return new BitMapDispatch with keyth item removed.
        Will not raise KeyError if it was not present. """
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        return BitMapDispatch(
            # Unset the keyth bit.
            self.bitmap & ~(1 << key),
            # Leave out the idxth item.
            self.items[:idx] + self.items[idx+1:]
        )
    
    def _iremove(self, key):
        """ Remove keyth item. Will not raise KeyError if it was not present.
        
        USE WITH CAUTION. """
        idx = bit_count(self.bitmap & ((1 << key) - 1))
        self.bitmap &= ~(1 << key)
        self.items.pop(idx)
        return self
    
    def __getitem__(self, key):
        if not self.bitmap & 1 << key:
            raise KeyError(key)
        return self.items[bit_count(self.bitmap & ((1 << key) - 1))]
    
    def to_listdispatch(self, nitems):
        """ Return ListDispatch with the same key to value connections as this
        BitMapDispatch. """
        return ListDispatch(
            None, [self.get(n, ListDispatch.sentinel) for n in xrange(nitems)]
        )
    
    def __iter__(self):
        return iter(self.items)
    
    def __nonzero__(self):
        return bool(self.items)


class DispatchNode(object):
    """ Dispatch to children nodes depending of the hsh value at the
    current level. """
    __slots__ = ['children']
    def __init__(self, children=None):
        if children is None:
            children = BitMapDispatch()
        
        self.children = children
    
    def xor(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        newchild = self.children.get(rlv, NULLNODE).xor(hsh, shift + SHIFT, node)
        if newchild is NULLNODE:
            # This makes sure no dead nodes remain in the tree after
            # removing an item.
            newchildren = self.children.remove(rlv)
            if not newchildren:
                return NULLNODE
        else:
            newchildren = self.children.replace(
                rlv, 
                newchild
            )
        
        return DispatchNode(newchildren)
    
    @doc(ASSOC)
    def assoc(self, hsh, shift, node):
        # We need not check whether the return value of
        # self.children.get(...).assoc is NULLNODE, because assoc never
        # returns NULLNODE.
        rlv = relevant(hsh, shift)
        return DispatchNode(
            self.children.replace(
                rlv,
                self.children.get(rlv, NULLNODE).assoc(
                    hsh, shift + SHIFT, node
                )
            )
        )
    
    @doc(IASSOC)
    def _iassoc(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        self.children = self.children._ireplace(
            rlv, 
            self.children.get(rlv, NULLNODE)._iassoc(hsh, shift + SHIFT, node)
        )
        return self
    
    @classmethod
    def make(cls, shift, many):
        # Because the object we create in this function is not yet exposed
        # to any other code, we may safely call _iassoc.
        dsp = cls()
        for elem in many:
            dsp._iassoc(elem.hsh, shift, elem)
        return dsp
    
    @doc(GET)
    def get(self, hsh, shift, key):
        return self.children.get(relevant(hsh, shift), NULLNODE).get(
            hsh, shift + SHIFT, key
        )
    
    @doc(WITHOUT)
    def without(self, hsh, shift, key):
        rlv = relevant(hsh, shift)
        newchild = self.children[rlv].without(hsh, shift + SHIFT, key)
        if newchild is NULLNODE:
            # This makes sure no dead nodes remain in the tree after
            # removing an item.
            newchildren = self.children.remove(rlv)
            if not newchildren:
                return NULLNODE
        else:
            newchildren = self.children.replace(
                rlv, 
                newchild
            )
        
        return DispatchNode(newchildren)
    
    @doc(IWITHOUT)
    def _iwithout(self, hsh, shift, key):
        rlv = relevant(hsh, shift)
        newchild = self.children[rlv].without(hsh, shift + SHIFT, key)
        if newchild is NULLNODE:
            self.children = self.children._iremove(rlv)
            if not newchildren:
                return NULLNODE
        else:
            self.children = self.children._ireplace(rlv, newchild)
        
        return self
    
    def __iter__(self):
        for child in self.children:
            for elem in child:
                yield elem


class PersistentTreeMap(object):
    __slots__ = ['root']
    def __init__(self, root=NULLNODE):
        self.root = root
    
    def __getitem__(self, key):
        return self.root.get(hash(key), 0, key).value
    
    def __and__(self, other):
        new = self.root
        
        one = iter(self.root)
        other = iter(other.root)
        
        for node in one:
            while True:
                try:
                    onode = other.next()
                except StopIteration:
                    return PersistentTreeMap(new)
                
                if onode.hsh == node.hsh:
                    new = new.assoc(onode.hsh, 0, onode)
                    break
                elif onode.hsh > node.hsh:
                    new = new.without(node.hsh, 0, node.key)
                    break
        
        return PersistentTreeMap(new)
    
    def __xor__(self, other):
        new = self.root
        for node in other.root:
            new = new.xor(node.hsh, 0, node)
        return PersistentTreeMap(new)
    
    def __or__(self, other):
        new = self.root
        for node in other.root:
            new = new.replace(node.hsh, 0, node)
        return PersistentTreeMap(new)
    
    def assoc(self, key, value):
        """ Return copy of self with an association between key and value.
        May override an existing association. """
        return PersistentTreeMap(
            self.root.assoc(hash(key), 0, AssocNode(key, value))
        )
    
    def without(self, key):
        """ Return copy of self with key removed. """
        return PersistentTreeMap(
            self.root.without(hash(key), 0, key)
        )
    
    def __iter__(self):
        for node in self.root:
            yield node.key
    
    iterkeys = __iter__
    
    def iteritems(self):
        for node in self.root:
            yield node.key, node.value
    
    def itervalues(self):
        for node in self.root:
            yield node.value
    
    @staticmethod
    def from_dict(dct):
        """ Create PersistentTreeMap from existing dictionary. """
        mp = VolatileTreeMap()
        for key, value in dct.iteritems():
            mp = mp.assoc(key, value)
        return mp.persistent()
    
    def volatile(self):
        return VolatileTreeMap(deepcopy(self.root))


class VolatileTreeMap(PersistentTreeMap):
    _assoc = PersistentTreeMap.assoc
    _without = PersistentTreeMap.without
    
    def assoc(self, key, value):
        """ Update this VolatileTreeMap to contain an association between
        key and value.
        
        USE WITH CAUTION: This should only be used if no other reference
        to the PersistentTreeMap may exist. """
        self.root = self.root._iassoc(hash(key), 0, AssocNode(key, value))
        return self
    
    def without(self, key):
        """ Remove key.
        
        USE WITH CAUTION: This should only be used if no other reference
        to the PersistentTreeMap may exist. """
        self.root = self.root._iwithout(hash(key), 0, key)
        return self
    
    def persistent(self):
        self.without = self._without
        self.assoc = self._assoc
        
        return self


class PersistentTreeSet(object):
    __slots__ = ['root']
    def __init__(self, root=NULLNODE):
        self.root = root
    
    def __contains__(self, key):
        try:
            self.root.get(hash(key), 0, key)
            return  True
        except KeyError:
            return False
    
    def add(self, key):
        """ Return copy of self with an association between key and value.
        May override an existing association. """
        return PersistentTreeMap(
            self.root.assoc(hash(key), 0, SetNode(key))
        )
    
    def without(self, key):
        """ Return copy of self with key removed. """
        return PersistentTreeMap(
            self.root.without(hash(key), 0, key)
        )
    
    def __iter__(self):
        for node in self.root:
            yield node.key
    
    @staticmethod
    def from_set(set_):
        """ Create PersistentTreeSet from existing set. """
        mp = VolatileTreeSet()
        for key in set_:
            mp = mp.add(key)
        return mp.persistent()
    
    def volatile(self):
        return VolatileTreeSet(deepcopy(self.root))


class VolatileTreeSet(PersistentTreeSet):
    _add = PersistentTreeSet.add
    _without = PersistentTreeSet.without
    
    def add(self, key):
        """ Update this VolatileTreeMap to contain an association between
        key and value.
        
        USE WITH CAUTION: This should only be used if no other reference
        to the PersistentTreeMap may exist. """
        self.root = self.root.assoc(hash(key), 0, SetNode(key))
        return self
    
    def without(self, key):
        """ Remove key.
        
        USE WITH CAUTION: This should only be used if no other reference
        to the PersistentTreeMap may exist. """
        self.root = self.root._iwithout(hash(key), 0, key)
        return self
    
    def persistent(self):
        self.without = self._without
        self.add = self._add
        
        return self


def main():    
    mp = PersistentTreeMap()
    mp1 = mp.assoc('a', 'hello')
    assert mp1['a'] == 'hello'
    mp2 = mp1.assoc('b', 'world')
    assert mp2['a'] == 'hello'
    assert mp2['b'] == 'world'
    mp3 = mp2.without('a')
    assert mp3['b'] == 'world'
    try:
        assert mp3['a'] == 'hello'
    except KeyError, e:
        if e.args[0] != 'a':
            assert False
    else:
        assert False
    
    assert set(mp2.iterkeys()) == set(mp2) == set(['a', 'b'])
    assert set(mp2.itervalues()) == set(['hello', 'world'])
    assert set(mp2.iteritems()) == set([('a', 'hello'), ('b', 'world')])
    
    import os
    import time
    # Prevent expensive look-up in loop, hence the from-import.
    from copy import copy

    mp = PersistentTreeMap().volatile()
    for _ in xrange(22500):
        one, other = os.urandom(20), os.urandom(25)
        mp2 = mp.assoc(one, other)
        assert mp[one] == other
        assert mp2[one] == other
        mp = mp2
    pmp = mp.persistent()    
    
    s = time.time()
    mp = PersistentTreeMap()
    for _ in xrange(225000):
        one, other = os.urandom(20), os.urandom(25)
        mp2 = mp.assoc(one, other)
        try:
            mp[one]
        except KeyError:
            assert True
        else:
            assert False
        try:
            mp2.without(one)[one]
        except KeyError:
            assert True
        else:
            assert False
        mp = mp2
        assert mp[one] == other
    print 'PersistentHashMap:', time.time() - s
    assert mp[one] == other
    # This /may/ actually fail if we are unlucky, but it's a good start.
    assert len(list(iter(mp))) == 225000
    
    #s = time.time()
    #dct = dict()
    #for _ in xrange(225000):
        #one, other = os.urandom(20), os.urandom(25)
        #dct2 = copy(dct)
        #dct2[one] = other
        #try:
            #dct[one]
        #except KeyError:
            #assert True
        #else:
            #assert False
        #dct = dct2
        #assert dct[one] == other
    #print 'Builtin dict:', time.time() - s
    
    mp4 = mp3.volatile()
    mp5 = mp4.assoc('foo', 'bar')
    assert mp4['foo'] == 'bar'
    assert mp5['foo'] == 'bar'
    assert mp4 is mp5
    
    mp6 = mp5.persistent()
    mp7 = mp6.assoc('foo', 'spam')
    assert mp4['foo'] == 'bar'
    assert mp5['foo'] == 'bar'
    assert mp6['foo'] == 'bar'
    assert mp7['foo'] == 'spam'
    
    try:
        mp3['foo']
    except KeyError:
        assert True
    else:
        assert False


if __name__ == '__main__':
    main()
