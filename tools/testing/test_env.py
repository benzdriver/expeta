from common import print_log
import os
print_log("QDRANT_HOST =", os.getenv("QDRANT_HOST"))
print_log("QDRANT_PORT =", os.getenv("QDRANT_PORT"))
print_log("QDRANT_API_KEY =", os.getenv("QDRANT_API_KEY"))
print_log("QDRANT_COLLECTION =", os.getenv("QDRANT_COLLECTION")) 