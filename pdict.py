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

SHIFT = 5
BMAP = (1 << SHIFT) - 1
BRANCH = 2 ** SHIFT

def relevant(hsh, shift):
    """ Return the relevant part of the hsh on the level shift. """
    return hsh >> shift & BMAP


def bit_count(integer):
    """ Count set bits in integer. """
    count = 0
    while integer:
        integer &= integer - 1
        count += 1
    return count


class NullNode(object):
    """ Dummy node being the leaf of branches that have no entries. """
    def assoc(self, hsh, shift, node):
        """ Because there currently no node, the new node
        is the node to be added. """
        return node
    
    _iassoc = assoc
    
    def get(self, hsh, shift, key):
        """ There is no entry with the searched key because the hash leads
        to a branch ending in a NullNode. """
        raise KeyError(key)
    
    def without(self, hsh, shift, key):
        """ There is no entry with the key to be removed because the hash leads
        to a branch ending in a NullNode. """
        raise KeyError(key)
    
    def __iter__(self):
        """ There are no keys contained in a NullNode. """
        return iter([])
    
    # Likewise, there are no values and items in a NullNode.
    iteritems = itervalues = __iter__

#: We only need one instance of a NullNode because it does not contain
#  any data.
NULLNODE = NullNode()


class LeafNode(object):
    """ A LeafNode contains the actual key-value mapping. """
    __slots__ = ['key', 'value', 'hsh']
    def __init__(self, key, value):
        self.key = key
        self.value = value
        self.hsh = hash(key)
    
    def get(self, hsh, shift, key):
        """ If the key does not match the key of the LeafNode,
        raise a KeyError, otherwise return the value. """
        if key != self.key:
            raise KeyError(key)
        return self.value
    
    def assoc(self, hsh, shift, node):
        """ If there is a hash-collision, return a HashCollisionNode,
        otherwise return a DispatchNode dispatching depending on the
        current level (if the two hashes only differ at a higher-level,
        DispatchNode.make will return a DispatchNode that contains a
        DispatchNode etc. up until the necessary depth. """
        if node.key == self.key:
            return node
        
        if hsh == self.hsh:
            return HashCollisionNode(
                [self, node]
            )
        return DispatchNode.make(shift, [self, node])
    
    def _iassoc(self, hsh, shift, node):
        """ Like assoc but modify the current Node. Use with care. """
        if node.key == self.key:
            self.key = node.key
            self.value = node.value
            return self
        
        if hsh == self.hsh:
            return HashCollisionNode(
                [self, node]
            )
        return DispatchNode.make(shift, [self, node])        
    
    def without(self, hsh, shift, key):
        """ If the key matches the key of this LeafNode, returning NULLNODE
        will remove the Node from the map. Otherwise raise a KeyError. """
        if key != self.key:
            raise KeyError(key)
        return NULLNODE
    
    def __iter__(self):
        yield self.key
    
    def iteritems(self):
        yield self.key, self.value
    
    def itervalues(self):
        yield self.value


class HashCollisionNode(object):
    """ If hashes of two keys collide, store them in a list and when a key
    is searched, iterate over that list and find the appropriate key. """
    __slots__ = ['nodes']
    def __init__(self, nodes):
        self.children = nodes
        self.hsh = hash(nodes[0].hsh)
    
    def get(self, hsh, shift, key):
        for node in self.children:
            if key == node.key:
                return node.value
        raise KeyError(key)
    
    def assoc(self, hsh, shift, node):
        if hsh == self.hsh:
            return HashCollisionNode(self.children + [node])
        return DispatchNode.make(shift, [self, node])
    
    def _iassoc(self, hsh, shift, node):
        if hsh == self.hsh:
            self.children.append(node)
            return self
        return DispatchNode.make(shift, [self, node])        
    
    def without(self, hsh, shift, key):
        return HashCollisionNode(
            [node for node in self.children if node.key != key]
        )
    
    def __iter__(self):
        for node in self.children:
            for elem in node:
                yield elem

    def iteritems(self):
        for child in self.children:
            for elem in child.iteritems():
                yield elem
    
    def itervalues(self):
        for child in self.children:
            for elem in child.itervalues():
                yield elem


class ListDispatch(object):
    __slots__ = ['items']
    def __init__(self, items=None):
        if items is None:
            items = []
        self.items = items
    
    def replace(self, key, item):
        return ListDispatch(
            self.items[:key] +
            [item] +
            self.items[key + 1:]
        )
    
    def _ireplace(self, key, item):
        self.items[key] = item
    
    def __getitem__(self, key):
        return self.items[key]
    
    def get(self, key, default):
        return self[key]
    
    def __iter__(self):
        return iter(self.items)


class BitMapDispatch(object):
    __slots__ = ['bitmap', 'default', 'items']
    def __init__(self, bitmap=0, default=None, items=None):
        if items is None:
            items = []
        self.default = default
        self.bitmap = bitmap
        self.items = items
    
    def replace(self, key, item):
        notnew = bool(self.bitmap & 1 << key)
        idx = self.bitmap | 1 << key
        key = bit_count(idx & ((1 << key) - 1))
        return BitMapDispatch(
            idx, self.default,
            self.items[:key] + [item] + self.items[key+notnew:]
        )
    
    def _ireplace(self, key, item):
        notnew = bool(self.bitmap & 1 << key)
        self.bitmap |= 1 << key
        key = bit_count(self.bitmap & ((1 << key) - 1))
        if key == len(self.items):
            self.items.append(item)
        elif notnew:
            self.items[key] = item
        else:
            self.items.insert(key, item)
    
    def get(self, key, default=None):
        try:
            return self[key]
        except KeyError:
            return default
    
    def __getitem__(self, key):
        if not self.bitmap & 1 << key:
            raise KeyError
        return self.items[bit_count(self.bitmap & ((1 << key) - 1))]
    
    def to_listdispatch(self, nitems):
        return ListDispatch(
            [self[n] for n in xrange(nitems)]
        )
    
    def __iter__(self):
        return iter(self.items)


class DispatchNode(object):
    __slots__ = ['children']
    def __init__(self, children=None):
        if children is None:
            children = ListDispatch([NULLNODE for _ in xrange(BRANCH)])
        self.children = children
    
    def assoc(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        return DispatchNode(
            self.children.replace(
                rlv,
                self.children.get(rlv, NULLNODE).assoc(
                    hsh, shift + SHIFT, node
                )
            )
        )
    
    def _iassoc(self, hsh, shift, node):
        rlv = relevant(hsh, shift)
        self.children._ireplace(
            rlv, 
            self.children.get(rlv, NULLNODE)._iassoc(hsh, shift + SHIFT, node)
        )
        return self
    
    @classmethod
    def make(cls, shift, many):
        dsp = cls()
        for elem in many:
            dsp._iassoc(elem.hsh, shift, elem)
        return dsp
    
    def get(self, hsh, shift, key):
        return self.children[relevant(hsh, shift)].get(
            hsh, shift + SHIFT, key
        )
    
    def without(self, hsh, shift, key):
        rlv = relevant(hsh, shift)
        return DispatchNode(
            self.children.replace(
                rlv, 
                self.children[rlv].without(hsh, shift + SHIFT, key)
            )
        )
    
    def __iter__(self):
        for child in self.children:
            for elem in child:
                yield elem
    
    def iteritems(self):
        for child in self.children:
            for elem in child.iteritems():
                yield elem
    
    def itervalues(self):
        for child in self.children:
            for elem in child.itervalues():
                yield elem


class PersistentTreeMap(object):
    __slots__ = ['root']
    def __init__(self, root=NULLNODE):
        self.root = root
    
    def __getitem__(self, key):
        return self.root.get(hash(key), 0, key)
    
    def assoc(self, key, value):
        return PersistentTreeMap(
            self.root.assoc(hash(key), 0, LeafNode(key, value))
        )
    
    def _iassoc(self, key, value):
        return PersistentTreeMap(
            self.root._iassoc(hash(key), 0, LeafNode(key, value))
        )
    
    def without(self, key):
        return PersistentTreeMap(
            self.root.without(hash(key), 0, key)
        )
    
    def __iter__(self):
        return iter(self.root)
    
    iterkeys = __iter__
    
    def iteritems(self):
        return self.root.iteritems()
    
    def itervalues(self):
        return self.root.itervalues()
    
    @classmethod
    def from_dict(cls, dct):
        mp = cls()
        for key, value in dct:
            mp = mp._iassoc(key, value)
        return mp


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

    mp = PersistentTreeMap()
    for _ in xrange(22500):
        one, other = os.urandom(20), os.urandom(25)
        mp = mp._iassoc(one, other)
        assert mp[one] == other
    
    s = time.time()
    mp = PersistentTreeMap()
    for _ in xrange(22500):
        one, other = os.urandom(20), os.urandom(25)
        mp2 = mp.assoc(one, other)
        try:
            mp[one]
        except KeyError:
            assert True
        else:
            assert False
        mp = mp2
        assert mp[one] == other
    print 'PersistentHashMap:', time.time() - s
    assert mp[one] == other
    # This /may/ actually fail if we are unlucky, but it's a good start.
    assert len(list(iter(mp))) == 22500
    
    s = time.time()
    dct = dict()
    for _ in xrange(22500):
        one, other = os.urandom(20), os.urandom(25)
        dct2 = copy(dct)
        dct2[one] = other
        try:
            dct[one]
        except KeyError:
            assert True
        else:
            assert False
        dct = dct2
        assert dct[one] == other
    print 'Builtin dict:', time.time() - s


if __name__ == '__main__':
    main()
