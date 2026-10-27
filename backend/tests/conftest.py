import sys
import os

backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Import all models so metadata knows foreign key references
import src.modules.tenancy.models
import src.modules.identity.models
import src.modules.access.models
import src.modules.directory.models
import src.modules.audit.models
import src.modules.attendance.models
import src.modules.complaints.models
import src.modules.feedback.models
import src.modules.knowledge.models
import src.modules.assistant.models
import src.core.outbox
