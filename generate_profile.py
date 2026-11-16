import copy
import csv
import json
import os
import re

from rocratepcc import (
    Author,
    CustomResourceDescriptor,
    License,
    Profile,
    ResourceDescriptor,
    RootDataEntity,
    Specification,
    TextualResource,
    UsedType,
)

OUTPUT_DIR = "generated_profile"
METADATA_FILE = "profile_definition.json"

def load_metadata():
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

# Aliases for types: (source, name) -> alias_name
# Used to enforce specific Schema.org mappings (e.g. File -> MediaObject)
TYPE_ALIASES = {
    ("schemaOrg", "File"): "MediaObject"
}

def license_spdx_to_class_name(spdx_id):
    """Convert SPDX ID to PascalCase class name.
    E.g. 'CC-BY-SA-4.0' -> 'LicenseCcBySa40',
         'Apache-2.0' -> 'LicenseApache20',
         'MIT' -> 'LicenseMit'
    """
    parts = spdx_id.replace('.', '').replace('-', ' ').split()
    return 'License' + ''.join(p.capitalize() for p in parts)

def credit_role_to_const_name(name):
    """Convert CRediT role name to UPPER_SNAKE_CASE const name.
    E.g. 'Data curation' -> 'DATA_CURATION',
         'Writing – original draft' -> 'WRITING_ORIGINAL_DRAFT'
    """
    # Replace en-dash and special chars with space, then normalize
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.replace('–', ' ').replace('&', 'and'))
    return '_'.join(cleaned.upper().split())

def credit_role_to_class_name(name):
    """Convert CRediT role name to PascalCase class name.
    E.g. 'Data curation' -> 'CreditRoleDataCuration'
    """
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.replace('–', ' ').replace('&', 'and'))
    return 'CreditRole' + ''.join(p.capitalize() for p in cleaned.split())

def credit_role_to_def_name(name):
    """Convert CRediT role name to JSON Schema definition key.
    E.g. 'Data curation' -> 'creditRole_data-curation'
    """
    cleaned = re.sub(r'[^a-zA-Z0-9\s]', '', name.replace('–', ' ').replace('&', 'and'))
    return 'creditRole_' + '-'.join(cleaned.lower().split())

def generate_types_csv(data):
    """Generate types.csv with all entities, properties, and types not from source 'profile'."""
    print("Generating types.csv...")

    # Key = IRI, avoids duplicates
    types_map = {}

    prefixes = data["prefixes"]

    # Add aliased types
    for (source, original_name), alias_name in TYPE_ALIASES.items():
        if source in prefixes:
            iri = f"{prefixes[source]['url']}{alias_name}"
            types_map[iri] = {
                "name": alias_name,
                "term_code": original_name
            }

    def process_source(source, name, is_property=False):
        if not source:
             return

        if source == "profile":
            return

        # Skip aliased types
        if (source, name) in TYPE_ALIASES:
            return

        iri_base = prefixes[source]["url"] if source in prefixes else None
        if not iri_base:
            print(f"Warning: Source '{source}' not found in prefixes.")
            return

        iri = f"{iri_base}{name}"

        if iri not in types_map:
            types_map[iri] = {
                "name": name,
                "term_code": "" # Default empty
            }

    for entity in data.get("entities", []):
        if entity.get("inherits_from"):
            process_source(entity["inherits_from"]["source"], entity["inherits_from"]["name"])

        for prop in entity.get("properties", []):
            if prop["name"] in ["@id", "@type"]:
                continue
            process_source(prop["source"], prop["name"], is_property=True)
            for type_def in prop.get("types", []):
               process_source(type_def["source"], type_def["name"])

    # Write to CSV
    csv_path = os.path.join(OUTPUT_DIR, "types.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["iri", "name", "term_code"])
        for iri, info in types_map.items():
            writer.writerow([iri, info["name"], info["term_code"]])

def generate_vocabulary_csv(data):
    """Generate vocabulary.csv with all newly defined entities, properties, and types (source='profile')."""
    print("Generating vocabulary.csv...")

    terms = {}

    def get_term_entry(name, type_):
        if name not in terms:
            terms[name] = {
                "type": type_,
                "label": name,
                "description": "",
                "domain": set(),
                "range": set()
            }
        return terms[name]

    for entity in data.get("entities", []):
        class_name = entity["name"]

        # Exclude base profile entities from vocabulary
        if class_name in ["File", "Dataset", "RootDataEntry"]:
            continue

        entry = get_term_entry(class_name, "Class")
        entry["description"] = entity.get("description", "")

        for prop in entity.get("properties", []):
            if prop["source"] == "profile":
                prop_name = prop["name"]
                prop_entry = get_term_entry(prop_name, "Property")
                prop_entry["description"] = prop.get("description", "")
                prop_entry["domain"].add(class_name)

                for type_def in prop.get("types", []):
                    prop_entry["range"].add(type_def["name"])

    # Write to CSV
    csv_path = os.path.join(OUTPUT_DIR, "vocabulary.csv")
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["term", "type", "label", "description", "domain", "range"])

        # Sort for stability
        for name in sorted(terms.keys()):
            t = terms[name]
            domain_str = " ".join(sorted(t["domain"]))
            range_str = " ".join(sorted(t["range"]))
            writer.writerow([name, t["type"], t["label"], t["description"], domain_str, range_str])

def generate_context_jsonld(data):
    """
    Generate context.jsonld
    Create a JSON-LD context file mapping profile terms to their IRIs.
    """
    print("Generating context.jsonld...")

    # Base URI for profile terms
    # Constructed from metadata URL + version
    metadata = data["metadata"]
    base_uri = metadata["url"].rstrip("/") + "/" + metadata["version"] + "/#"

    context_map = {}

    # Add Classes (Entities)
    for entity in data.get("entities", []):
        class_name = entity["name"]

        # Exclude hardcoded terms (same as vocabulary)
        if class_name in ["File", "Dataset", "RootDataEntry"]:
            continue

        context_map[class_name] = f"{base_uri}{class_name}"

        # Add Properties
        for prop in entity.get("properties", []):
            if prop["source"] == "profile":
                prop_name = prop["name"]
                context_map[prop_name] = f"{base_uri}{prop_name}"

    # Create final structure
    context_structure = {
        "@context": context_map
    }

    # Write to JSON-LD
    json_path = os.path.join(OUTPUT_DIR, "context.jsonld")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(context_structure, f, indent=4)

def generate_json_schema(data):
    """
    Generate JSON Schema (rise-ro-crate-profile-schema.json)
    Using Draft 07 (flattened schema).
    """
    print("Generating rise-ro-crate-profile-schema.json...")

    # Load base schema
    base_schema_path = os.path.join("resources", "base_profile_schema.json")
    with open(base_schema_path, "r") as f:
        schema = json.load(f)

    metadata = data["metadata"]
    entities = data["entities"]
    static_defs = data.get("static_definitions", {})
    licenses = static_defs.get("licenses", [])

    # Add license definitions
    for lic in licenses:
        spdx_id = lic["spdx_id"]
        def_name = f"license_{spdx_id}"
        # Add $ref to @graph.items.anyOf
        lic_ref = {"$ref": f"#/definitions/{def_name}"}
        items_def = schema["properties"]["@graph"]["items"]
        if "anyOf" not in items_def:
            items_def["anyOf"] = []
        if lic_ref not in items_def["anyOf"]:
            items_def["anyOf"].append(lic_ref)
        # Add definition
        schema["definitions"][def_name] = {
            "type": "object",
            "properties": {
                "@id": {"const": lic["url"]},
                "@type": {"const": "CreativeWork"},
                "name": {"const": lic["name"]},
                "alternateName": {"const": spdx_id},
                "url": {"const": lic["url"]}
            },
            "required": ["@id", "@type", "name", "alternateName", "url"],
            "additionalProperties": False
        }

    # Add CRediT role definitions
    credit_roles = static_defs.get("credit_roles", [])
    for role in credit_roles:
        def_name = credit_role_to_def_name(role["name"])
        role_ref = {"$ref": f"#/definitions/{def_name}"}
        items_def = schema["properties"]["@graph"]["items"]
        if role_ref not in items_def["anyOf"]:
            items_def["anyOf"].append(role_ref)
        schema["definitions"][def_name] = {
            "type": "object",
            "properties": {
                "@id": {"const": role["url"]},
                "@type": {"const": "Role"},
                "roleName": {"const": role["name"]},
                "description": {"const": role["description"]},
                "url": {"const": role["url"]}
            },
            "required": ["@id", "@type", "roleName", "description", "url"],
            "additionalProperties": False
        }

    # Add custom definitions
    custom_entries = static_defs.get("custom", [])
    for entry in custom_entries:
        def_name = entry["identifier"]
        entry_ref = {"$ref": f"#/definitions/{def_name}"}
        items_def = schema["properties"]["@graph"]["items"]
        if entry_ref not in items_def["anyOf"]:
            items_def["anyOf"].append(entry_ref)
        props = {}
        required = []
        for key, value in entry["properties"].items():
            props[key] = {"const": value}
            required.append(key)
        schema["definitions"][def_name] = {
            "type": "object",
            "properties": props,
            "required": required,
            "additionalProperties": False
        }

    # Generate ProfileDefinition
    profile_url = metadata["url"].rstrip("/") + "/" + metadata["version"] + "/"
    profile_name = metadata["name"]
    profile_name_short = metadata["name_short"]
    profile_version = metadata["version"]

    schema["title"] = f"RO-Crate Schema for {profile_name} ({profile_name_short})"

    # Add ProfileDefinition to schema definitions
    schema["definitions"]["ProfileDefinition"] = {
        "type": "object",
        "properties": {
            "@id": {"const": profile_url},
            "@type": {"const": ["CreativeWork", "Profile"]},
            "name": {"const": profile_name},
            "alternateName": {"const": profile_name_short},
            "version": {"const": profile_version}
        },
        "required": ["@id", "@type", "name", "version"],
        "additionalProperties": False
    }

    # Add ProfileDefinition to @graph.items.anyOf
    profile_ref = {"$ref": "#/definitions/ProfileDefinition"}
    items_def = schema["properties"]["@graph"]["items"]
    if "anyOf" not in items_def:
        items_def["anyOf"] = []
    if profile_ref not in items_def["anyOf"]:
        items_def["anyOf"].append(profile_ref)

    # Require ProfileDefinition in @graph (via allOf/contains)
    graph_def = schema["properties"]["@graph"]
    if "allOf" not in graph_def:
        graph_def["allOf"] = []
    profile_contains = {"contains": profile_ref}
    if profile_contains not in graph_def["allOf"]:
        graph_def["allOf"].append(profile_contains)

    # Create concrete class definitions (Flattened)

    # Helper to build property definition
    def build_property_schema(prop):
        p_name = prop["name"]

        # Skip @id/@type as they are handled in the class definition wrapper
        if p_name in ["@id", "@type"]:
            return None

        # Prepare Type Lookup Table (Reverse mapping) - supports multiple mappings
        type_lookup = {}
        for schema_type, type_names in data["type_mapping"].items():
            for t_name in type_names:
                if t_name not in type_lookup:
                    type_lookup[t_name] = []
                type_lookup[t_name].append(schema_type)

        allowed_schemas = []

        for t in prop.get("types", []):
            t_name = t["name"]

            if t_name not in type_lookup:
                 # It might be a profile type, check if it is in entities
                 if any(e["name"] == t_name for e in entities):
                     # It's an object type defined in this profile
                     d_types = ["object"]
                 else:
                     raise ValueError(f"Type '{t_name}' (used in {p_name}) is not defined.")
            else:
                d_types = type_lookup[t_name]

            for d_type in d_types:
                if d_type == "object":
                     allowed_schemas.append({
                        "type": "object",
                        "properties": {"@id": {"type": "string"}},
                        "required": ["@id"]
                     })
                else:
                    allowed_schemas.append({"type": d_type})

        # Deduplicate schemas
        unique_schemas = []
        for s in allowed_schemas:
            if s not in unique_schemas:
                unique_schemas.append(s)

        if not unique_schemas:
            prop_schema = {}
        elif len(unique_schemas) == 1:
            prop_schema = unique_schemas[0]
        else:
            prop_schema = {"anyOf": unique_schemas}

        # Handling Arrays
        if prop.get("multiple", False):
            return {
                "type": "array",
                "items": prop_schema
            }
        else:
            return prop_schema

    # Properties to exclude from inheritance for specific entities
    # Key: entity name, Value: list of property names to exclude from parent inheritance
    EXCLUDE_INHERITED_PROPERTIES = {
        "RootDataEntry": ["exampleOfWork"],  # exampleOfWork is for File/Dataset, not for root
    }

    # Collect all properties per entity (flattening inheritance)
    for entity in entities:
        class_name = entity["name"]

        if class_name == "RootDataEntry":
            def_name = "RootDataEntity"
        else:
            def_name = class_name

        ref = {"$ref": f"#/definitions/{def_name}"}

        # Add to @graph anyOf
        if "items" in schema["properties"]["@graph"]:
            items_def = schema["properties"]["@graph"]["items"]
            if "anyOf" not in items_def:
                items_def["anyOf"] = []
            if ref not in items_def["anyOf"]:
                 items_def["anyOf"].append(ref)



        # Collect properties walking up the inheritance chain
        collected_properties = {}
        collected_requirements = set()

        # Current entity properties
        for prop in entity.get("properties", []):
             if prop["name"] not in ["@id", "@type"]:
                collected_properties[prop["name"]] = build_property_schema(prop)

             if prop.get("requirement", "optional") == "required":
                 collected_requirements.add(prop["name"])

        # Walk up parents
        current = entity
        visited = {class_name}

        while current.get("inherits_from"):
            parent_ref = current["inherits_from"]
            parent_name = parent_ref["name"]

            if parent_name in visited:
                break
            visited.add(parent_name)

            # Find parent entity
            parent_entity = next((e for e in entities if e["name"] == parent_name), None)

            if parent_entity:
                current = parent_entity
                # Get list of properties to exclude from inheritance for this entity
                excluded_props = EXCLUDE_INHERITED_PROPERTIES.get(class_name, [])

                for prop in current.get("properties", []):
                    # Child overrides parent property definition if exists
                    # Also skip properties that are explicitly excluded from inheritance
                    if (
                        prop["name"] not in collected_properties
                        and prop["name"] not in ["@id", "@type"]
                        and prop["name"] not in excluded_props
                    ):
                        collected_properties[prop["name"]] = build_property_schema(prop)

                    # Inheritance of required status (also check exclusion list):
                    if prop.get("requirement", "optional") == "required" and prop["name"] not in excluded_props:
                        collected_requirements.add(prop["name"])
            else:
                # Parent not in profile (e.g. schema.org direct), stop here.
                break

        # Construct the Definition

        # Standard @id and @type
        definition_props = {
            "@id": {"type": "string"},
            "@type": {"const": def_name if def_name != "RootDataEntity" else "Dataset"}
        }

        definition_props.update(collected_properties)

        # Filter None values
        definition_props = {k: v for k, v in definition_props.items() if v is not None}

        # Unique required list
        final_reqs = set(collected_requirements)
        final_reqs.add("@id")
        final_reqs.add("@type")


        # Special Case: RootDataEntity mutual exclusivity for mainEntity and mentions
        one_of_constraints = []
        if def_name == "RootDataEntity":
            final_reqs.discard("mainEntity")
            final_reqs.discard("mentions")

            one_of_constraints = [
                {"required": ["mainEntity"]},
                {"required": ["mentions"]}
            ]

        required_list = sorted(final_reqs)

        def_schema = {
            "type": "object",
            "properties": definition_props,
            "required": required_list,
            "additionalProperties": False
        }

        if one_of_constraints:
            def_schema["oneOf"] = one_of_constraints

        schema["definitions"][def_name] = def_schema

    # Add conformsTo for RootDataEntity
    # (must be done after entity loop which rebuilds RootDataEntity)
    root_def = schema["definitions"]["RootDataEntity"]
    root_def["properties"]["conformsTo"] = {
        "type": "object",
        "properties": {
            "@id": {"const": profile_url}
        },
        "required": ["@id"]
    }
    if "conformsTo" not in root_def["required"]:
        root_def["required"].append("conformsTo")

    # Write Schema
    with open(os.path.join(OUTPUT_DIR, "rise-ro-crate-profile-schema.json"), "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=4)

# Helper classes
class DefinedTerm:
    def __init__(self, id, termCode, term_type, name, description, domain=(), range=()):
        self.dict_obj = {}
        self.dict_obj["@id"] = id
        self.dict_obj["@type"] = ["DefinedTerm"]
        if term_type == "Class":
            self.dict_obj["@type"].append("rdfs:Class")
        elif term_type == "Property":
            self.dict_obj["@type"].append("rdf:Property")

        self.dict_obj["termCode"] = termCode
        self.dict_obj["name"] = name
        self.dict_obj["description"] = description
        if domain:
            self.dict_obj["domainIncludes"] = [{"@id": d} for d in domain]
        if range:
            self.dict_obj["rangeIncludes"] = [{"@id": r} for r in range]

class DefinedTermSet:
    def __init__(self, id, name):
        self.defined_term_set = {}
        self.defined_term_set["@id"] = id
        self.defined_term_set["@type"] = "DefinedTermSet"
        self.defined_term_set["name"] = name
        self.defined_term_set["hasDefinedTerm"] = []
        self.defined_terms = []

    def load_defined_terms(self, csv_path, base_url, external_types_map=None):
        term_file = csv_path

        external_types_map = external_types_map or {}

        with open(term_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Construct identifier using the base URL
                identifier = f"{base_url}#{row['term']}"

                # Resolve domain names to IRIs
                domain_iris = []
                if row["domain"]:
                    for d in row["domain"].split(" "):
                        if d in external_types_map:
                            domain_iris.append(external_types_map[d])
                        else:
                            domain_iris.append(f"{base_url}#{d}")

                # Resolve range names to IRIs
                range_iris = []
                if row["range"]:
                    for r in row["range"].split(" "):
                        if r in external_types_map:
                            range_iris.append(external_types_map[r])
                        else:
                            range_iris.append(f"{base_url}#{r}")

                defined_term = DefinedTerm(
                    identifier,
                    row["term"],
                    row["type"],
                    row["label"],
                    row["description"],
                    domain_iris,
                    range_iris
                )
                self.defined_terms.append(defined_term.dict_obj)

                reference = {}
                reference["@id"] = identifier
                self.defined_term_set["hasDefinedTerm"].append(reference)

    def __iter__(self):
        yield from [self.defined_term_set, *self.defined_terms]

def generate_profile_crate(data):
    """
    Generate RO-Crate Metadata (ro-crate-metadata.json)
    """
    print("Generating ro-crate-metadata.json...")

    meta = data["metadata"]

    # Authors
    authors = []
    for auth in meta.get("authors", []):
        authors.append(Author(orcid=auth["orcid"], name=auth["name"]))

    # Used Types (from types.csv)
    types = []
    external_types_map = {}

    types_csv_path = os.path.join(OUTPUT_DIR, "types.csv")
    with open(types_csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            kwargs = {
                "iri": row["iri"],
                "name": row["name"]
            }
            if row.get("term_code"):
                kwargs["term_code"] = row["term_code"]
            types.append(UsedType(**kwargs))

            external_types_map[row["name"]] = row["iri"]
            if row.get("term_code"):
                 external_types_map[row["term_code"]] = row["iri"]

    # License
    lic = License(iri=meta["license"]["url"], name=meta["license"]["name"])

    # Specifications
    spec_id = meta["url"].rstrip("/") + "/" + meta["version"] + "/"
    profile_name = meta["name"]
    profile_name_short = meta["name_short"]
    profile_name_full = f"{profile_name} ({profile_name_short})"
    specifications = [
        TextualResource(
            name = f"{profile_name_full} description",
            file_path = "rise-ro-crate-profile.md",
            encoding_format = "text/markdown",
            root_data_entity_id = spec_id
        )
    ]

    vocab_filename = "vocabulary.csv"
    vocabulary_ref = []
    Vocabulary = CustomResourceDescriptor(role="http://www.w3.org/ns/dx/prof/role/vocabulary", id="#hasVocabulary")

    resourceDescriptors = [
        Specification(specifications),
        ResourceDescriptor(vocabulary_ref, Vocabulary)
    ]

    rootEntity = RootDataEntity(
        id = spec_id,
        name = profile_name_full,
        description = meta["description"],
        license = lic,
        used_types = types,
        resource_descriptors = resourceDescriptors,
        authors = authors
    )

    profile = Profile(
        rootEntity,
        license = lic
    )

    string = profile.ToROCrateJsonString(spaces = 4)
    base_profile = json.loads(string)

    # Add Vocabulary Terms
    # Manually set hasArtifact for vocabulary (not supported by the library)
    for entry in base_profile["@graph"]:
        if entry["@id"] == "#hasVocabulary":
            entry["hasArtifact"] = {"@id":"crate-vocabulary.csv"}
            break
    vocab_csv_path = os.path.join(OUTPUT_DIR, vocab_filename)
    DefinedTerms = DefinedTermSet(vocab_filename, f"Namespace for {profile_name_short}")

    DefinedTerms.load_defined_terms(vocab_csv_path, spec_id, external_types_map)

    base_profile["@graph"].extend(DefinedTerms)

    output_path = os.path.join(OUTPUT_DIR, "ro-crate-metadata.json")

    # Only update datePublished if content actually changed
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            existing = json.load(f)

        def find_root(obj):
            return next((e for e in obj["@graph"] if e.get("@id") == spec_id), None)

        old_root = find_root(existing)
        if old_root is not None:
            old_date = old_root.get("datePublished")

            # Compare without datePublished
            old_stripped = copy.deepcopy(existing)
            new_stripped = copy.deepcopy(base_profile)
            find_root(old_stripped).pop("datePublished", None)
            find_root(new_stripped).pop("datePublished", None)

            if old_stripped == new_stripped:
                find_root(base_profile)["datePublished"] = old_date

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(base_profile, f, indent=4)

def generate_markdown(data):
    """
    Generate rise-ro-crate-profile.md
    """
    print("Generating rise-ro-crate-profile.md...")

    lines = []
    lines.append("# Profile Information")
    lines.append("")
    profile_name_full = f"{data['metadata']['name']} ({data['metadata']['name_short']})"
    lines.append(f"**Name**: {profile_name_full}")
    lines.append("")
    lines.append(f"**Version**: {data['metadata']['version']}")
    lines.append("")


    authors = data['metadata'].get('authors', [])
    if authors:
        lines.append("**Authors**:")
        for auth in authors:
            name = auth.get("name")
            orcid = auth.get("orcid")
            if orcid:
                lines.append(f"- [{name}](https://orcid.org/{orcid})")
            else:
                 lines.append(f"- {name}")

    lines.append("")

    # Add Overview section
    description = data["metadata"].get("description", "")
    lines.append("## Overview")
    lines.append("")
    lines.append(description)
    lines.append("")

    # Copy structure.svg if it exists and add to Overview
    structure_svg_src = os.path.join("resources", "rise-ro-crate-profile-structure.svg")
    structure_svg_dst = os.path.join(OUTPUT_DIR, "rise-ro-crate-profile-structure.svg")
    if os.path.exists(structure_svg_src):
        with open(structure_svg_src, "rb") as fsrc, open(structure_svg_dst, "wb") as fdst:
            fdst.write(fsrc.read())
        lines.append('<img src="rise-ro-crate-profile-structure.svg" style="width: 100%; height: auto;" alt="RISE RO-Crate Profile Structure">')
        lines.append("")

    lines.append("## Resources")
    lines.append("")
    lines.append("The following resources are part of this profile.")
    lines.append("")
    lines.append("### Profile Definition")
    lines.append("")
    lines.append("The following resources form the core definition of this profile:")
    lines.append("")
    lines.append("- Profile Crate — [ro-crate-metadata.json]"
                 "(ro-crate-metadata.json)")
    lines.append("- External type mappings — [types.csv](types.csv)")
    lines.append("- Profile vocabulary — [vocabulary.csv]"
                 "(vocabulary.csv)")
    lines.append("- JSON-LD context — [context.jsonld](context.jsonld)")
    lines.append("")
    lines.append("### Developer Resources")
    lines.append("")
    lines.append("The following resources help developers implement or verify crates against this profile:")
    lines.append("")
    lines.append("- JSON Schema — [rise-ro-crate-profile-schema.json]"
                 "(rise-ro-crate-profile-schema.json)")
    lines.append("- TypeScript interfaces — [rise-ro-crate-profile.ts]"
                 "(rise-ro-crate-profile.ts)")
    lines.append("- Pydantic models — [rise_ro_crate_profile_pydantic.py]"
                 "(rise_ro_crate_profile_pydantic.py)")
    lines.append("")

    prefixes = data["prefixes"]
    metadata = data["metadata"]
    name_short = metadata["name_short"]
    profile_url = metadata["url"].rstrip("/") + "/" + metadata["version"] + "/"

    def get_source_label(source):
        if not source:
            return ""
        if source == "profile":
            return name_short
        prefix = prefixes.get(source)
        if prefix and prefix.get("name"):
            return prefix["name"]
        return source

    # Collect all unique sources used across entities
    used_sources = set()
    for entity in data.get("entities", []):
        inherits = entity.get("inherits_from")
        if inherits and inherits.get("source"):
            used_sources.add(inherits["source"])
        for prop in entity.get("properties", []):
            if prop.get("source"):
                used_sources.add(prop["source"])
            for t in prop.get("types", []):
                if t.get("source"):
                    used_sources.add(t["source"])

    lines.append("## Related Specifications")
    lines.append("")
    lines.append("This profile builds upon the following specifications:")
    lines.append("")
    for source in sorted(used_sources):
        if source == "profile":
            continue
        label = get_source_label(source)
        prefix = prefixes.get(source)
        if prefix and prefix.get("url"):
            lines.append(f"- [{label}]({prefix['url']})")
        else:
            lines.append(f"- {label}")
    lines.append("")

    def resolve_type_link(type_def):
        name = type_def["name"]
        source = type_def["source"]

        label = get_source_label(source)

        if source == "profile":
            # Link to full profile URL
            return (f"[{name}]({profile_url}#{name.lower()})", label)
        else:
            # Try to resolve other prefixes
            iri_base = None
            if source:
                iri_base = prefixes[source]["url"] if source in prefixes else None

            if iri_base:
                # SPECIAL CASE: File or Dataset from schema.org should link to internal table but keep schema.org label
                if (name == "File" or name == "Dataset") and source == "schemaOrg":
                    return (f"[{name}](#{name.lower()})", label)

                return (f"[{name}]({iri_base}{name})", label)

            return (name, label)

    lines.append("## Vocabulary")
    lines.append("")

    for entity in data.get("entities", []):
        name = entity["name"]
        lines.append(f"### {name}")

        inherits = entity.get("inherits_from")
        if inherits:
            # Try to link inheritance too
            source = inherits["source"]
            parent_name = inherits["name"]

            link = parent_name

            if source == "profile":
                link = f"[{parent_name}]({profile_url}#{parent_name.lower()})"
            elif source:
                iri_base = prefixes[source]["url"] if source in prefixes else None
                if iri_base:
                    # Check for alias override for inheritance link
                    if (source, parent_name) in TYPE_ALIASES:
                        alias = TYPE_ALIASES[(source, parent_name)]
                        link = f"[{parent_name}]({iri_base}{alias})"
                    else:
                        link = f"[{parent_name}]({iri_base}{parent_name})"

            lines.append(f"**Inherits from:** {link} ({get_source_label(source)})")
        else:
             lines.append("**Inherits from:** (None specified)")

        entity_description = entity.get("description")
        if entity_description:
            # Two trailing spaces = markdown hard line break (less space than paragraph break)
            lines[-1] = lines[-1] + "  "
            lines.append(f"**Description:** {entity_description}")

        lines.append("")

        # Table Header
        lines.append("| Property | Property Source | Type | Type Source | Required? | Description |")
        lines.append("| :--- | :--- | :--- | :--- | :--- | :--- |")

        for prop in entity.get("properties", []):
            p_name = prop["name"]
            source = prop["source"]

            # Format name with backticks
            display_name = f"`{p_name}`"

            # Check if external and linkable
            if source != "profile":
                iri_base = None
                if source:
                    iri_base = prefixes[source]["url"] if source in prefixes else None

                if iri_base:
                    # Create link: [`name`](url)
                    p_name = f"[{display_name}]({iri_base}{p_name})"
                else:
                    p_name = display_name
            else:
                p_name = display_name

            req_val = prop.get("requirement", "optional")
            if req_val == "required":
                required = "Required"
            elif req_val == "conditional":
                required = "Conditionally Required"
            else:
                required = "Optional"
            msg_source = get_source_label(prop["source"])

            desc = prop["description"]

            # Types
            type_links = []
            type_sources = []
            for t in prop.get("types", []):
                link, t_source = resolve_type_link(t)
                type_links.append(link)
                type_sources.append(t_source)

            type_str = " or ".join(type_links)
            type_source_str = ", ".join(dict.fromkeys(type_sources))

            if prop["multiple"]:
                type_str = f"List of ({type_str})"

            lines.append(f"| {p_name} | {msg_source} | {type_str} | {type_source_str} | {required} | {desc} |")

        lines.append("")

    with open(os.path.join(OUTPUT_DIR, "rise-ro-crate-profile.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def generate_typescript(data):
    """
    Generate TypeScript interfaces (rise-ro-crate-profile.ts)
    from the entity definitions in profile_definition.json.
    """
    print("Generating rise-ro-crate-profile.ts...")

    entities = data["entities"]
    type_mapping = data["type_mapping"]

    # Build set of entity names defined in this profile
    entity_names = {e["name"] for e in entities}

    # Build TS primitive mapping from type_mapping
    # JSON Schema type -> TypeScript type
    SCHEMA_TO_TS = {
        "string": "string",
        "boolean": "boolean",
        "integer": "number",
        "number": "number",
    }

    # Invert type_mapping: type_name -> TS type
    # (skip "object" — those are handled as EntityRef)
    ts_primitives = {}
    for schema_type, type_names in type_mapping.items():
        if schema_type == "object":
            continue
        ts_type = SCHEMA_TO_TS.get(schema_type)
        if ts_type:
            for t_name in type_names:
                ts_primitives[t_name] = ts_type

    def resolve_ts_type(type_def):
        """Resolve a single type entry to a TypeScript type string."""
        t_name = type_def["name"]

        types = set()
        if t_name in ts_primitives:
            types.add(ts_primitives[t_name])

        # Object types map to EntityRef
        if t_name in entity_names or t_name in type_mapping.get("object", []):
            types.add("EntityRef")

        if not types:
            return "string"

        return " | ".join(sorted(types))

    def build_property_line(prop, indent="  "):
        """Build a TypeScript property line from a property definition."""
        p_name = prop["name"]

        # Skip @id and @type, handled separately
        if p_name in ("@id", "@type"):
            return None

        # Resolve types
        ts_types = []
        for t in prop.get("types", []):
            ts_t = resolve_ts_type(t)
            ts_types.append(ts_t)

        final_types = set()
        for t_str in ts_types:
             for p in t_str.split(" | "):
                 final_types.add(p.strip())

        sorted_types = sorted(final_types)

        if not sorted_types:
            type_str = "unknown"
        elif len(sorted_types) == 1:
            type_str = sorted_types[0]
        else:
            type_str = " | ".join(sorted_types)

        # Wrap in array if multiple
        if prop.get("multiple", False):
            if "|" in type_str:
                type_str = f"({type_str})[]"
            else:
                type_str = f"{type_str}[]"

        # Optional marker
        optional = "" if prop.get("requirement", "optional") == "required" else "?"

        # Quote property names with special chars
        if p_name.startswith("@") or "-" in p_name:
            quoted_name = f'"{p_name}"'
        else:
            quoted_name = p_name

        lines = []

        # JSDoc comment
        desc = prop.get("description", "")
        if desc:
            lines.append(f"{indent}/** {desc} */")

        lines.append(
            f"{indent}{quoted_name}{optional}: {type_str};"
        )
        return "\n".join(lines)

    # Build output
    output_lines = []
    output_lines.append(
        "// Auto-generated from profile_definition.json"
    )
    output_lines.append(
        f"// Version: {data['metadata']['version']}\n"
    )

    # EntityRef helper type
    output_lines.append("/** Reference to another entity by @id */")
    output_lines.append("export interface EntityRef {")
    output_lines.append('  "@id": string;')
    output_lines.append("}\n")

    # Prepend base TypeScript definitions
    with open("resources/base_profile_typescript.ts", "r") as f:
        # Skip first two lines (// @ts-nocheck + blank line, only needed for IDE)
        base_ts = "".join(f.readlines()[2:])
    output_lines.append(base_ts)

    static_defs = data.get("static_definitions", {})

    # Generate license consts
    license_const_names = []
    for lic in static_defs.get("licenses", []):
        # SPDX ID to UPPER_SNAKE: 'CC-BY-SA-4.0' -> 'CC_BY_SA_4_0'
        const_name = lic["spdx_id"].replace("-", "_").replace(".", "_").upper()
        license_const_names.append(const_name)
        output_lines.append(f'/** {lic["name"]} */')
        output_lines.append(f'export const {const_name}: License = {{')
        output_lines.append(f'    "@id": "{lic["url"]}",')
        output_lines.append('    "@type": "CreativeWork",')
        output_lines.append(f'    name: "{lic["name"]}",')
        output_lines.append(f'    alternateName: "{lic["spdx_id"]}",')
        output_lines.append(f'    url: "{lic["url"]}",')
        output_lines.append('};\n')

    # Generate AvailableLicenses array
    if license_const_names:
        output_lines.append("/** Array of all available license instances defined in this profile. */")
        joined = ", ".join(license_const_names)
        output_lines.append(f"export const AvailableLicenses: License[] = [{joined}];\n")

    # Generate CRediT role consts
    role_const_names = []
    for role in static_defs.get("credit_roles", []):
        const_name = credit_role_to_const_name(role["name"])
        role_const_names.append(const_name)
        output_lines.append(f'/** {role["name"]}: {role["description"]} */')
        output_lines.append(f'export const {const_name}: Omit<Role, \'contributor\'> = {{')
        output_lines.append(f'    "@id": "{role["url"]}",')
        output_lines.append('    "@type": "Role",')
        output_lines.append(f'    roleName: "{role["name"]}",')
        output_lines.append(f'    description: "{role["description"]}",')
        output_lines.append(f'    url: "{role["url"]}",')
        output_lines.append('};\n')

    # Generate AvailableCreditRoles array
    if role_const_names:
        output_lines.append("/** Array of all CRediT contributor role instances defined in this profile. */")
        joined_roles = ", ".join(role_const_names)
        output_lines.append(f"export const AvailableCreditRoles: Omit<Role, 'contributor'>[] = [{joined_roles}];\n")

    # Generate custom consts
    custom_lists = {}  # add_to_list name -> {const_names: [], base_type: str|None}
    for entry in static_defs.get("custom", []):
        const_name = entry["identifier"]
        base_type = entry.get("base_type")
        desc = entry.get("description", entry["identifier"])
        output_lines.append(f'/** {desc} */')
        if base_type:
            output_lines.append(f'export const {const_name}: {base_type} = {{')
        else:
            output_lines.append(f'export const {const_name} = {{')
        for key, value in entry["properties"].items():
            js_key = f'"{key}"' if key.startswith('@') else key
            js_val = json.dumps(value)
            output_lines.append(f'    {js_key}: {js_val},')
        if base_type:
            output_lines.append('};\n')
        else:
            output_lines.append('} as const;\n')
        # Track for add_to_list grouping
        list_name = entry.get("add_to_list")
        if list_name:
            if list_name not in custom_lists:
                custom_lists[list_name] = {"const_names": [], "base_type": base_type}
            custom_lists[list_name]["const_names"].append(const_name)

    # Generate add_to_list arrays for custom entries
    for list_name, info in custom_lists.items():
        output_lines.append(f'/** Array of all {list_name} instances defined in this profile. */')
        joined = ', '.join(info["const_names"])
        if info["base_type"]:
            output_lines.append(f'export const {list_name}: {info["base_type"]}[] = [{joined}];\n')
        else:
            output_lines.append(f'export const {list_name} = [{joined}] as const;\n')

    # Generate ProfileDefinition interface
    output_lines.append("/** Entity describing the profile this crate conforms to. */")
    output_lines.append("export interface ProfileDefinition {")
    output_lines.append('  "@id": string;')
    output_lines.append('  "@type": ["CreativeWork", "Profile"];')
    output_lines.append('  name: string;')
    output_lines.append('  alternateName?: string;')
    output_lines.append('  version: string;')
    output_lines.append("}\n")

    # Generate prefilled profile definition instance
    metadata = data["metadata"]
    profile_url = metadata["url"].rstrip("/") + "/" + metadata["version"] + "/"
    profile_name = metadata["name"]
    profile_name_short = metadata["name_short"]
    profile_version = metadata["version"]
    # Convert name_short to UPPER_SNAKE for const name
    const_name = profile_name_short.replace(" ", "_").replace("-", "_").upper()
    output_lines.append(f'/** Prefilled profile definition for {profile_name} v{profile_version} */')
    output_lines.append(f'export const {const_name}: ProfileDefinition = {{')
    output_lines.append(f'    "@id": "{profile_url}",')
    output_lines.append('    "@type": ["CreativeWork", "Profile"],')
    output_lines.append(f'    name: "{profile_name}",')
    output_lines.append(f'    alternateName: "{profile_name_short}",')
    output_lines.append(f'    version: "{profile_version}",')
    output_lines.append('};\n')

    # Generate interfaces
    for entity in entities:
        e_name = entity["name"]
        desc = entity.get("description", "")
        inherits = entity.get("inherits_from")

        extends_clause = ""
        if inherits:
            parent_name = inherits.get("internal_link") or inherits.get("name")
            if parent_name in entity_names and parent_name != e_name:
                extends_clause = f' extends Omit<{parent_name}, "@type">'

        # JSDoc
        if desc:
            output_lines.append(f"/** {desc} */")

        output_lines.append(
            f"export interface {e_name}{extends_clause} {{"
        )

        output_lines.append('  "@id": string;')

        output_lines.append(f'  "@type": "{e_name}";')

        # Properties
        for prop in entity.get("properties", []):
            prop_line = build_property_line(prop)
            if prop_line:
                output_lines.append(prop_line)

        # Add conformsTo for RootDataEntry
        if e_name == "RootDataEntry":
            output_lines.append('  /** Profile this crate conforms to */')
            output_lines.append('  conformsTo: EntityRef;')

        output_lines.append("}\n")

    # Write output
    out_path = os.path.join(OUTPUT_DIR, "rise-ro-crate-profile.ts")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(output_lines))


def generate_pydantic_models(data, less_strict_object_reference=True):
    """
    Generate Pydantic models (rise_ro_crate_profile_pydantic.py)
    """
    print("Generating rise_ro_crate_profile_pydantic.py...")

    lines = []
    lines.append('"""')
    profile_name_full = f'{data["metadata"]["name"]} ({data["metadata"]["name_short"]})'
    lines.append(f'Auto-generated Pydantic models for {profile_name_full}')
    lines.append(f'Version: {data["metadata"]["version"]}')
    lines.append('"""')
    lines.append('')

    # Prepend base Pydantic definitions
    with open("resources/base_profile_pydantic.py", "r") as f:
        base_py = f.read()

    lines.append(base_py)
    lines.append('')

    static_defs = data.get("static_definitions", {})

    # Generate license classes
    for lic in static_defs.get("licenses", []):
        cls_name = license_spdx_to_class_name(lic["spdx_id"])
        lines.append(f'class {cls_name}(License):')
        lines.append(f'    """{lic["name"]}"""')
        lines.append(f"    id: Literal['{lic['url']}'] = Field(default='{lic['url']}', alias='@id')")
        lines.append("    type: Literal['CreativeWork'] = Field(default='CreativeWork', alias='@type')")
        lines.append(f"    name: Literal['{lic['name']}'] = Field(default='{lic['name']}')  # License full name")
        lines.append(f"    alternateName: Literal['{lic['spdx_id']}'] = Field(default='{lic['spdx_id']}')  # SPDX short identifier")
        lines.append(f"    url: Literal['{lic['url']}'] = Field(default='{lic['url']}')  # License URL")
        lines.append('')
        lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
        lines.append('')
        lines.append('')
    # Generate AvailableLicenses union type
    if static_defs.get("licenses"):
        license_names = [license_spdx_to_class_name(lic["spdx_id"]) for lic in static_defs["licenses"]]
        lines.append(f'AvailableLicenses = Union[{", ".join(license_names)}]')
        lines.append('"""Union of all available license types defined in this profile."""')
        lines.append('')
        lines.append('')

    # Generate CRediT role classes
    for role in static_defs.get("credit_roles", []):
        cls_name = credit_role_to_class_name(role["name"])
        lines.append(f'class {cls_name}(CreditRoleDefinition):')
        lines.append(f'    """{role["name"]}: {role["description"]}"""')
        lines.append(f"    id: Literal['{role['url']}'] = Field(default='{role['url']}', alias='@id')")
        lines.append("    type: Literal['Role'] = Field(default='Role', alias='@type')")
        lines.append(f"    roleName: Literal['{role['name']}'] = Field(default='{role['name']}')  # Role name")
        lines.append(f"    description: Literal['{role['description']}'] = Field(default='{role['description']}')  # Role description")
        lines.append(f"    url: Literal['{role['url']}'] = Field(default='{role['url']}')  # Role URL")
        lines.append('')
        lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
        lines.append('')
        lines.append('')

    # Generate AvailableCreditRoles union type
    if static_defs.get("credit_roles"):
        role_names = [credit_role_to_class_name(role["name"]) for role in static_defs["credit_roles"]]
        lines.append(f'AvailableCreditRoles = Union[{", ".join(role_names)}]')
        lines.append('"""Union of all CRediT contributor role types defined in this profile."""')
        lines.append('')
        lines.append('')

    # Generate custom classes
    custom_lists = {}  # add_to_list name -> list of class names
    for entry in static_defs.get("custom", []):
        cls_name = f'Custom{entry["identifier"]}'
        base_type = entry.get("base_type", "BaseModel")
        desc = entry.get("description", entry["identifier"])
        lines.append(f'class {cls_name}({base_type}):')
        lines.append(f'    """{desc}"""')
        for key, value in entry["properties"].items():
            if key.startswith('@'):
                field_name = key[1:]  # @id -> id, @type -> type
                alias_part = f", alias='{key}'"
            else:
                field_name = key
                alias_part = ""
            # Build Literal type and default
            if isinstance(value, list):
                literal_args = ', '.join(f"'{v}'" for v in value)
                default_val = repr(value)
                lines.append(f"    {field_name}: List[Literal[{literal_args}]] = Field(default={default_val}{alias_part})")
            else:
                literal_args = f"'{value}'"
                default_val = f"'{value}'"
                lines.append(f"    {field_name}: Literal[{literal_args}] = Field(default={default_val}{alias_part})")
        lines.append('')
        lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
        lines.append('')
        lines.append('')
        # Track for add_to_list grouping
        list_name = entry.get("add_to_list")
        if list_name:
            custom_lists.setdefault(list_name, []).append(cls_name)

    # Generate add_to_list union types for custom entries
    for list_name, class_names in custom_lists.items():
        lines.append(f'{list_name} = Union[{", ".join(class_names)}]')
        lines.append(f'"""Union of all {list_name} types defined in this profile."""')
        lines.append('')
        lines.append('')

    # Prepare Type Mapping
    type_map_raw = data["type_mapping"]

    # Primitives mapping
    PRIMITIVE_MAP = {
        "string": "str",
        "boolean": "bool",
        "integer": "int",
        "number": "float",
        # Objects are handled dynamically based on whether they are defined in entities
        "object": "EntityReference"
    }

    # Build lookup: TypeName -> PythonType (str)
    # e.g. "Text" -> "str", "Person" -> "EntityReference", "Experiment" -> '"Experiment"'
    # Build lookup: TypeName -> Set of PythonTypes
    # e.g. "Text" -> {"str"}, "URL" -> {"str", "EntityReference"}
    type_lookup_sets = {}

    # defined entities
    defined_entities = {e["name"] for e in data["entities"]}

    for kind, type_names in type_map_raw.items():
        py_type = PRIMITIVE_MAP.get(kind, "str") # default to str if unknown
        for t_name in type_names:
            if t_name not in type_lookup_sets:
                type_lookup_sets[t_name] = set()

            if kind == "object":
                # Check if it is a defined entity in this profile
                if t_name in defined_entities:
                     # Use quoted forward reference
                    type_lookup_sets[t_name].add(f'"{t_name}"')
                else:
                    # External object (e.g. Person, Organization) -> EntityReference
                    type_lookup_sets[t_name].add("EntityReference")
            else:
                type_lookup_sets[t_name].add(py_type)

    # Flatten lookup to strings
    type_lookup = {}
    for t_name, types in type_lookup_sets.items():
        sorted_types = sorted(types)
        if len(sorted_types) == 1:
            type_lookup[t_name] = sorted_types[0]
        else:
            type_lookup[t_name] = f"Union[{', '.join(sorted_types)}]"

    def get_py_type(type_def):
        t_name = type_def["name"]
        return type_lookup.get(t_name, "str")

    # Generate Classes
    entities = data["entities"]

    # Minimal Topological Sort
    sorted_entities = []
    visited = set()

    def visit(name):
        if name in visited:
            return
        entity = next((e for e in entities if e["name"] == name), None)
        if not entity:
            return

        inherits = entity.get("inherits_from")

        if name in ["File", "Dataset"]:
            pass
        elif inherits and inherits["name"] in defined_entities:
            visit(inherits["name"])

        visited.add(name)
        sorted_entities.append(entity)

    for entity in entities:
        visit(entity["name"])

    for entity in sorted_entities:
        class_name = entity["name"]
        description = entity.get("description", f"{class_name} entity")

        # Inheritance
        parent = "BaseModel"
        inherits = entity.get("inherits_from")

        if class_name in ["File", "Dataset"]:
             parent = "BaseModel"
        elif inherits:
            p_name = inherits["name"]
            # Inherit if parent is defined in this profile
            if p_name in defined_entities:
                parent = p_name

        lines.append(f'class {class_name}({parent}):')
        lines.append(f'    """{description}"""')
        lines.append('')

        has_own_fields = False

        if parent == "BaseModel":
             pass


        lines.append("    id: str = Field(..., alias='@id')")
        lines.append(f"    type: Literal['{class_name}'] = Field(default='{class_name}', alias='@type')")
        has_own_fields = True

        # Add conformsTo for RootDataEntry
        if class_name == "RootDataEntry":
            lines.append("    conformsTo: EntityReference  # Profile this crate conforms to")

        for prop in entity.get("properties", []):
            p_name = prop["name"]

            if p_name in ["@id", "@type"]:
                continue

            desc = prop.get("description", "")

            # Resolve Type
            p_types = prop.get("types", [])

            py_types = []
            for t in p_types:
                res_type = get_py_type(t)
                # Flatten nested Union types: "Union[A, B]" -> ["A", "B"]
                if res_type.startswith("Union["):
                    inner = res_type[6:-1].split(", ")
                    py_types.extend(inner)
                else:
                    py_types.append(res_type)

            py_types = sorted(set(py_types))

            if less_strict_object_reference:
                has_entity_ref = any(t.startswith('"') for t in py_types)
                if has_entity_ref and "EntityReference" not in py_types:
                    py_types.append("EntityReference")

            if not py_types:
                type_str = "Any"
            elif len(py_types) == 1:
                type_str = py_types[0]
            else:
                type_str = f'Union[{", ".join(py_types)}]'

            if prop["multiple"]:
                type_str = f'List[{type_str}]'

            is_required = prop.get("requirement", "optional") == "required"

            if is_required:
                field_line = f"    {p_name}: {type_str}"
            else:
                field_line = f"    {p_name}: Optional[{type_str}] = None"

            if desc:
                field_line += f"  # {desc}"

            lines.append(field_line)
            has_own_fields = True

        if not has_own_fields:
            lines.append("    pass")

        lines.append("")
        lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
        lines.append("")
        lines.append("")

    # Generate ProfileDefinition class
    lines.append('class ProfileDefinition(BaseModel):')
    lines.append('    """Entity describing the profile this crate conforms to."""')
    lines.append('')
    lines.append("    id: str = Field(..., alias='@id')")
    lines.append("    type: List[Literal['CreativeWork', 'Profile']] = Field(default=['CreativeWork', 'Profile'], alias='@type')")
    lines.append('    name: str')
    lines.append('    alternateName: Optional[str] = None')
    lines.append('    version: str')
    lines.append('')
    lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
    lines.append('')
    lines.append('')

    # Generate prefilled profile definition instance
    metadata = data["metadata"]
    profile_url = metadata["url"].rstrip("/") + "/" + metadata["version"] + "/"
    profile_name = metadata["name"]
    profile_name_short = metadata["name_short"]
    profile_version = metadata["version"]
    # Convert name_short to PascalCase for class name
    cls_name = profile_name_short.replace(" ", "").replace("-", "")
    lines.append(f'class {cls_name}(ProfileDefinition):')
    lines.append(f'    """Prefilled profile definition for {profile_name} v{profile_version}"""')
    lines.append(f"    id: Literal['{profile_url}'] = Field(default='{profile_url}', alias='@id')")
    lines.append("    type: List[Literal['CreativeWork', 'Profile']] = Field(default=['CreativeWork', 'Profile'], alias='@type')")
    lines.append(f"    name: Literal['{profile_name}'] = Field(default='{profile_name}')")
    lines.append(f"    alternateName: Literal['{profile_name_short}'] = Field(default='{profile_name_short}')")
    lines.append(f"    version: Literal['{profile_version}'] = Field(default='{profile_version}')")
    lines.append('')
    lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
    lines.append('')
    lines.append('')

    # Generate ROCrateGraph and ROCrateMetadata containers

    # Collect all class names for the graph Union
    all_class_names = [e["name"] for e in entities]
    base_model_names = ["Person", "Organization", "Role", "CreativeWork", "ScholarlyArticle", "WebPage"]
    # License class names
    for lic in static_defs.get("licenses", []):
        base_model_names.append(license_spdx_to_class_name(lic["spdx_id"]))
    # CRediT role class names
    for role in static_defs.get("credit_roles", []):
        base_model_names.append(credit_role_to_class_name(role["name"]))
    # Custom class names
    for entry in static_defs.get("custom", []):
        base_model_names.append(f'Custom{entry["identifier"]}')
    all_class_names.extend(base_model_names)
    all_class_names.append("ProfileDefinition")
    all_class_names.append("EntityReference")

    union_content = ", ".join(all_class_names)

    lines.append('class ROCrateGraph(BaseModel):')
    lines.append('    """RO-Crate @graph container."""')
    lines.append('')
    lines.append(f"    graph: List[Union[{union_content}]] = Field(..., alias='@graph')")
    lines.append('')
    lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
    lines.append('')
    lines.append('')

    lines.append('class ROCrateMetadata(BaseModel):')
    lines.append('    """Complete RO-Crate metadata file."""')
    lines.append('')
    lines.append("    context: Union[str, List[Any], dict] = Field(..., alias='@context')")
    lines.append(f"    graph: List[Union[{union_content}]] = Field(..., alias='@graph')")
    lines.append('')
    lines.append("    model_config = ConfigDict(populate_by_name=True, extra='forbid')")
    lines.append('')

    # Write output
    out_path = os.path.join(OUTPUT_DIR, "rise_ro_crate_profile_pydantic.py")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    data = load_metadata()
    generate_types_csv(data)
    generate_vocabulary_csv(data)
    generate_profile_crate(data)
    generate_markdown(data)
    generate_context_jsonld(data)
    generate_json_schema(data)
    generate_typescript(data)
    generate_pydantic_models(data)

    print("Done.")

if __name__ == "__main__":
    main()
