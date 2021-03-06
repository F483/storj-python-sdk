# -*- coding: utf-8 -*-
"""Storj model module."""

import base64
import binascii
import hashlib
import random
import strict_rfc3339
import string

from datetime import datetime
from steenzout.object import Object


class Bucket(Object):
    """Storage bucket.

    A bucket is a logical grouping of files
    which the user can assign permissions and limits to.

    Attributes:
        id (str): unique identifier.
        name (str): name.
        status (str): bucket status (Active, ...).
        user (str): user email address.
        created (:py:class:`datetime.datetime`):
            time when the bucket was created.
        storage (int): storage limit (in GB).
        transfer (int): transfer limit (in GB).
        pubkeys ():
    """

    def __init__(
            self, id=None, name=None, status=None, user=None,
            created=None, storage=None, transfer=None, pubkeys=None):
        self.id = id
        self.name = name
        self.status = status
        self.user = user
        self.storage = storage
        self.transfer = transfer
        self.pubkeys = pubkeys

        # self.files = FileManager(bucket_id=self.id)
        # self.pubkeys = BucketKeyManager(
        #     bucket=self, authorized_public_keys=self.pubkeys)
        # self.tokens = TokenManager(bucket_id=self.id)

        if created is not None:
            self.created = datetime.fromtimestamp(
                strict_rfc3339.rfc3339_to_timestamp(created))
        else:
            self.created = None

    def delete(self):
        BucketManager.delete(bucket_id=self.id)


class File(Object):
    """
    Attributes:
        bucket (): bucket unique identifier.
        hash ():
        mimetype ():
        filename ():
        size ():
        shardManager ():
    """

    def __init__(self, bucket=None, hash=None, mimetype=None,
                 filename=None, size=None, id=None):
        self.bucket = Bucket(id=bucket)
        self.hash = hash
        self.mimetype = mimetype
        self.filename = filename
        self.size = size
        self.shardManager = ShardManager()
        self.id = id

    @property
    def content_type(self):
        return self.mimetype

    @property
    def name(self):
        return self.filename

    def download(self):
        return api_client.file_download(bucket_id=self.bucket,
                                        file_hash=self.hash)

    def delete(self):
        bucket_files = FileManager(bucket_id=self.bucket)
        bucket_files.delete(self.id)


class Frame(Object):
    """File staging frame.

    Attributes:
        id (str): unique identifier.
        created (:py:class:`datetime.datetime`):
            time when the bucket was created.
        shards (list[:py:class:`Shard`]): shards that compose this frame.
    """

    def __init__(self, id=None, created=None, shards=None):
        self.id = id

        if created is not None:
            self.created = datetime.fromtimestamp(
                strict_rfc3339.rfc3339_to_timestamp(created))
        else:
            self.created = None

        if shards is None:
            self.shards = []
        else:
            self.shards = shards


class Keyring:

    def __init__(self):
        self.password = None
        self.salt = None

    def generate(self):
        user_pass = raw_input("Enter your keyring password: ")
        password = hex(random.getrandbits(512 * 8))[2:-1]
        salt = hex(random.getrandbits(32 * 8))[2:-1]

        pbkdf2 = hashlib.pbkdf2_hmac('sha512', password, salt, 25000, 512)

        key = hashlib.new('sha256', pbkdf2).hexdigest()
        IV = salt[:16]
        self.export_keyring(password, salt, user_pass)
        self.password = password
        self.salt = salt

    def export_keyring(self, password, salt, user_pass):
        plain = pad("{\"pass\" : \"%s\", \n\"salt\" : \"%s\"\n}"
                    % (password, salt))
        IV = hex(random.getrandbits(8 * 8))[2:-1]

        aes = AES.new(pad(user_pass), AES.MODE_CBC, IV)

        with open('key.b64', 'wb') as f:
            f.write(base64.b64encode(IV + aes.encrypt(plain)))

    def import_keyring(self, filepath):
        with open(filepath, 'rb') as f:
            keyb64 = f.read()

        user_pass = raw_input('Enter your keyring password: ')

        key_enc = base64.b64decode(keyb64)
        IV = key_enc[:16]
        key = AES.new(pad(user_pass), AES.MODE_CBC, IV)

        # returns the salt and password as a dict
        creds = eval(key.decrypt(key_enc[16:])[:-4])
        self.password = creds['pass']
        self.salt = creds['salt']
        return creds


class Shard:
    """Shard.

    Attributes:
        id (str): unique identifier.
        hash (str): hash of the data.
        size (long): size of the shard in bytes.
        index (int): numberic index of the shard in the frame.
        challenges (list[str]): list of challenge numbers
        tree (list[str]): audit merkle tree
        exclude (list[str]): list of farmer nodeIDs to exclude
    """

    def __init__(self, id=None, hash=None, size=None, index=None,
                 challenges=None, tree=None, exclude=None):
        self.id = id
        # self.path = None
        self.hash = hash
        self.size = size
        self.index = index
        self.challenges = challenges
        self.tree = tree
        self.exclude = exclude

        if challenges is not None:
            self.challenges = challenges
        else:
            self.challenges = []

        if tree is not None:
            self.tree = tree
        else:
            self.tree = []

        if exclude is not None:
            self.exclude = exclude
        else:
            self.exclude = []

    def all(self):
        return_string = 'Shard{index=%s, hash=%s, ' % (
            self.index,
            self.hash)
        return_string += 'size=%s, tree={%s}, challenges={%s}' % (
            self.size,
            ', '.join(self.tree),
            ', '.join(self.challenges))
        return return_string

    def add_challenge(self, challenge):
        """Append challenge.

        Args:
            challenge (str):.
        """
        self.challenges.append(challenge)

    def add_tree(self, tree):
        """Append tree."""
        self.tree.append(tree)


class ShardManager:

    def __init__(self, filepath, shard_size):
        self.shards = []
        self.challenges = 8
        self.shard_index = 0
        self.index = 0
        self.shard_size = shard_size
        self.filepath = filepath

        file = open(filepath, "rb")

        while(True):
            chunk = file.read(shard_size)
            if not chunk:
                break
            tmpfile = open("C:/test/shard" + str(self.index) + ".shard", "wb")
            tmpfile.write(chunk)
            tmpfile.close()

            shard = Shard()
            shard.set_size(shard_size)
            shard.set_hash(hash160(chunk))
            self.addChallenges(shard, chunk)
            shard.set_index(self.index)
            self.index += 1
            self.shards.append(shard)

    def hash160(data):
        """hex encode returned str"""
        return binascii.hexlify(ripemd160(hashlib.sha256(data).digest()))

    def ripemd160(data):
        return hashlib.new('ripemd160', data).digest()

    def addChallenges(self, shard, shardData, numberOfChallenges=12):
        for i in xrange(numberOfChallenges):
            challenge = self.getRandomChallengeString()

            # concat and hex-encode data
            data2hash = binascii.hexlify('%s%s' % (challenge, shardData))

            tree = hash160(hash160(data2hash))  # double hash160 the data

            shard.add_challenge(challenge)
            shard.add_tree(tree)

            def getRandomChallengeString(self):
                return ''.join(
                    random.choice(string.ascii_letters) for _ in xrange(32))


class Token(Object):
    """

    Attributes:
        token ():
        bucket ():
        operation ():
        expires ():
    """

    def __init__(
            self, token=None, bucket=None, operation=None, expires=None):
        self.id = token
        self.bucket_id = bucket
        self.operation = operation

        if expires is not None:
            self.expires = datetime.fromtimestamp(
                strict_rfc3339.rfc3339_to_timestamp(expires))
        else:
            self.expires = None
