# Copyright (C) 2010-2013 Claudio Guarnieri.
# Copyright (C) 2014-2016 Cuckoo Foundation.
# This file is part of Cuckoo Sandbox - http://www.cuckoosandbox.org
# See the file 'docs/LICENSE' for copying permission.

import codecs
import json
import logging
import os

from cuckoo.common.abstracts import Processing
from cuckoo.common.exceptions import CuckooProcessingError
from cuckoo.core.database import Database

log = logging.getLogger(__name__)

class Logfile(list):
    def __init__(self, filepath, is_json=False):
        list.__init__(self)
        self.filepath = filepath
        self.is_json = is_json

    def __iter__(self):
        try:
            for line in codecs.open(self.filepath, "rb", "utf-8"):
                yield json.loads(line) if self.is_json else line
        except Exception as e:
            log.info("Error decoding %s: %s", self.filepath, e)

    def __nonzero__(self):
        return bool(os.path.getsize(self.filepath))

class Errors(list):
    def __init__(self, task_id):
        list.__init__(self)
        self.task_id = task_id

    def __iter__(self):
        for error in Database().view_errors(self.task_id):
            yield error.message

    def __nonzero__(self):
        return bool(Database().view_errors(self.task_id))

class Debug(Processing):
    """Analysis debug information."""
    order = 2

    def run(self):
        """Run debug analysis.
        @return: debug information dict.
        """
        self.key = "debug"
        debug = {
            "log": [],
            "cuckoo": [],
            "errors": [],
            "action": [],
        }

        if os.path.exists(self.log_path):
            try:
                f = codecs.open(self.log_path, "rb", "utf-8")
                debug["log"] = f.readlines()
            except ValueError as e:
                raise CuckooProcessingError(
                    "Error decoding %s: %s" % (self.log_path, e)
                )
            except (IOError, OSError) as e:
                raise CuckooProcessingError(
                    "Error opening %s: %s" % (self.log_path, e)
                )

        if os.path.exists(self.cuckoolog_path):
            debug["cuckoo"] = Logfile(self.cuckoolog_path)

        if os.path.exists(self.action_path):
            debug["action"] = Logfile(self.action_path, is_json=True)

        debug["errors"] = Errors(int(self.task["id"]))

        if os.path.exists(self.mitmerr_path):
            mitmerr = open(self.mitmerr_path, "rb").read()
            if mitmerr:
                debug["errors"].append(mitmerr)

        return debug
