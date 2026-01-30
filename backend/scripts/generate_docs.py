#!/usr/bin/env python3
"""Generate static API documentation files from FastAPI app.

This script generates:
1. OpenAPI YAML specification
2. OpenAPI JSON specification
3. Postman collection

Usage:
    python scripts/generate_docs.py

Output:
    - docs/openapi.yaml
    - docs/openapi.json
    - docs/postman_collection.json
"""

import json
import sys
from pathlib import Path

# Add backend directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import yaml
from app.main import app


def generate_openapi_spec():
    """Generate OpenAPI specification from FastAPI app."""
    return app.openapi()


def save_yaml(spec: dict, filename: str):
    """Save specification as YAML."""
    filepath = Path(__file__).parent.parent / "docs" / filename
    with open(filepath, "w") as f:
        yaml.dump(spec, f, sort_keys=False, default_flow_style=False)
    print(f"✓ Generated {filepath}")


def save_json(spec: dict, filename: str):
    """Save specification as JSON."""
    filepath = Path(__file__).parent.parent / "docs" / filename
    with open(filepath, "w") as f:
        json.dump(spec, f, indent=2)
    print(f"✓ Generated {filepath}")


def convert_to_postman(openapi_spec: dict) -> dict:
    """Convert OpenAPI spec to Postman collection format."""
    
    collection = {
        "info": {
            "name": openapi_spec.get("info", {}).get("title", "API"),
            "description": openapi_spec.get("info", {}).get("description", ""),
            "version": openapi_spec.get("info", {}).get("version", "1.0.0"),
            "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
        },
        "item": [],
        "auth": {
            "type": "bearer",
            "bearer": [
                {
                    "key": "token",
                    "value": "{{jwt_token}}",
                    "type": "string"
                }
            ]
        },
        "event": []
    }
    
    # Group endpoints by tag
    paths = openapi_spec.get("paths", {})
    endpoints_by_tag = {}
    
    for path, methods in paths.items():
        for method, details in methods.items():
            if method in ["get", "post", "patch", "put", "delete"]:
                tags = details.get("tags", ["default"])
                tag = tags[0] if tags else "default"
                
                if tag not in endpoints_by_tag:
                    endpoints_by_tag[tag] = []
                
                endpoint = {
                    "name": details.get("summary", f"{method.upper()} {path}"),
                    "request": {
                        "method": method.upper(),
                        "header": [],
                        "url": {
                            "raw": f"{{{{base_url}}}}{path}",
                            "host": ["{{base_url}}"],
                            "path": path.strip("/").split("/"),
                            "variable": []
                        },
                        "description": details.get("description", "")
                    },
                    "response": []
                }
                
                # Add parameters
                parameters = details.get("parameters", [])
                if parameters:
                    endpoint["request"]["url"]["query"] = []
                    for param in parameters:
                        if param.get("in") == "query":
                            endpoint["request"]["url"]["query"].append({
                                "key": param["name"],
                                "value": "",
                                "description": param.get("description", ""),
                                "disabled": not param.get("required", False)
                            })
                        elif param.get("in") == "path":
                            endpoint["request"]["url"]["variable"].append({
                                "key": param["name"],
                                "value": "",
                                "description": param.get("description", "")
                            })
                
                # Add request body
                request_body = details.get("requestBody", {})
                if request_body:
                    content = request_body.get("content", {})
                    if "application/json" in content:
                        endpoint["request"]["body"] = {
                            "mode": "raw",
                            "raw": json.dumps(content["application/json"].get("example", {}), indent=2),
                            "options": {
                                "raw": {
                                    "language": "json"
                                }
                            }
                        }
                    elif "multipart/form-data" in content:
                        endpoint["request"]["body"] = {
                            "mode": "formdata",
                            "formdata": []
                        }
                
                # Add authentication header for API key endpoints
                if path == "/api/v1/api-keys/" or "/api-keys/" in path:
                    endpoint["request"]["auth"] = {
                        "type": "apikey",
                        "apikey": [
                            {
                                "key": "key",
                                "value": "X-API-Key",
                                "type": "string"
                            },
                            {
                                "key": "value",
                                "value": "{{api_key}}",
                                "type": "string"
                            },
                            {
                                "key": "in",
                                "value": "header",
                                "type": "string"
                            }
                        ]
                    }
                
                endpoints_by_tag[tag].append(endpoint)
    
    # Convert to Postman items
    for tag, endpoints in endpoints_by_tag.items():
        folder = {
            "name": tag.capitalize(),
            "item": endpoints
        }
        collection["item"].append(folder)
    
    return collection


def generate_postman_environment() -> dict:
    """Generate Postman environment file."""
    return {
        "name": "Leads Data Warehouse - Local",
        "values": [
            {
                "key": "base_url",
                "value": "http://localhost:8000",
                "enabled": True
            },
            {
                "key": "api_key",
                "value": "",
                "description": "Your API key (ldwsk-...)",
                "enabled": True
            },
            {
                "key": "jwt_token",
                "value": "",
                "description": "JWT token from /auth/token",
                "enabled": True
            }
        ],
        "_postman_variable_scope": "environment"
    }


def main():
    """Main function to generate all documentation files."""
    print("Generating API documentation...")
    
    # Generate OpenAPI spec
    spec = generate_openapi_spec()
    
    # Save YAML
    save_yaml(spec, "openapi.yaml")
    
    # Save JSON
    save_json(spec, "openapi.json")
    
    # Generate Postman collection
    postman_collection = convert_to_postman(spec)
    save_json(postman_collection, "postman_collection.json")
    
    # Generate Postman environment
    environment = generate_postman_environment()
    save_json(environment, "postman_environment.json")
    
    print("\n✅ Documentation generation complete!")
    print("\nFiles generated in docs/:")
    print("  - openapi.yaml (OpenAPI specification)")
    print("  - openapi.json (OpenAPI JSON)")
    print("  - postman_collection.json (Postman collection)")
    print("  - postman_environment.json (Postman environment)")
    print("\nNext steps:")
    print("  1. Import postman_collection.json and postman_environment.json into Postman")
    print("  2. Set your api_key or jwt_token in the Postman environment")
    print("  3. Start making requests!")


if __name__ == "__main__":
    main()
