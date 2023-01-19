"""
This module provides constants describing the different stages happening during the lifecycle of project
"""

UPLOADED = "uploaded"  # files are all uploaded
COMPLETED = "completed"  # /complete hit for project
INDEXED = "indexed"  # project is fully indexed
PURGED = "purged"  # project was purged (marked as to-be-deleted) because completion didn't happened on time
EXPIRED = "expired"  # transient project has expired and was marked as "to-be-deleted"
DELETED = "deleted"  # project which was marked as "to-be-deleted" was  deleted
PERMISSIONS_CHANGED = "permissions-changed"  # permissions on the project were modified
CREATED = "created"  # project was created, now ready
VERSION_CREATED = "version-created"  # new version within an existing project added, now ready
MODIFIED = "version-modified"  # a version was modified
FAILED = "failed"  # general failure
ALL_INDEXED = "all-indexed"  # all projects are fully indexed
ALL_INDEXED_FAILED = "all-indexed-failed"  # failure during indexing process
