full_summary_schema = {
    "module": "string - the unique name of the module",
    "description": "string - short summary of the module purpose",
    "frontend": {
        "pages": ["string - file path or page route"],
        "components": ["string - reusable UI components"],
        "apiHooks": ["string - React query or custom API hooks"],
        "routes": ["string - user-facing route paths"]
    },
    "backend": {
        "controllers": ["string - controller names"],
        "services": ["string - service class names"],
        "repositories": ["string - DB abstraction layer names"],
        "dtos": {
            "DtoName": {
                "fields": ["string - field names"]
            }
        },
        "api": [
            {
                "method": "string - HTTP verb",
                "route": "string - backend route",
                "input": "string - DTO name",
                "output": "string - response structure or DTO"
            }
        ],
        "database": {
            "tables": ["string - DB table names"],
            "indexes": ["string - index definitions"]
        }
    },
    "dependencies": ["string - other module names"],
    "events": {
        "emit": ["string - emitted event names"],
        "listen": ["string - listened event names"]
    },
    "test": {
        "unit": ["string - unit test file names"],
        "e2e": ["string - e2e test script names"]
    }
}