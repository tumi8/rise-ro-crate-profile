# NOTE: This validator is a work in progress. The main validation logic (schema and semantic checks)
# is functional, but not every edge case may be covered yet. Use with that in mind.

import argparse
import json
import os
import sys

DEFAULT_SCHEMA = "generated_profile/rise-ro-crate-profile-schema.json"

try:
    import jsonschema  # noqa: F401
    from jsonschema import validators
    from jsonschema.exceptions import ValidationError  # noqa: F401
except ImportError:
    print("jsonschema library is not installed. Please install it using: pip install jsonschema")
    sys.exit(1)


def load_json(path):
    if not os.path.exists(path):
        print(f"Error: File not found: {path}")
        sys.exit(1)
    with open(path, 'r') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse JSON in {path}: {e}")
            sys.exit(1)


def diagnose_error(error, instance, schema, validator_cls):
    """
    Provide helpful diagnostics for common RO-Crate validation errors.
    """
    try:
        # 1. Handle 'anyOf' errors within @graph
        if len(error.path) >= 2 and error.path[0] == '@graph' and isinstance(error.path[1], int):
            index = error.path[1]
            entity = instance['@graph'][index]
            target_id = entity.get('@id', '<unknown>')

            # Heuristic to find the intended schema definition
            target_def_ref = None

            if target_id == 'ro-crate-metadata.json':
                target_def_ref = '#/definitions/MetadataFileDescriptor'
            elif target_id == './':
                target_def_ref = '#/definitions/RootDataEntity'
            else:
                e_type = entity.get('@type')
                if e_type:
                    def_name = e_type if isinstance(e_type, str) else e_type[0]
                    if def_name in schema.get('definitions', {}):
                        target_def_ref = f'#/definitions/{def_name}'

            if target_def_ref:
                definition_name = target_def_ref.split('/')[-1]
                target_schema = schema.get('definitions', {}).get(definition_name)

                if target_schema:
                    meta_schema = schema.get("$schema", "http://json-schema.org/draft-07/schema#")
                    wrapper_schema = {
                        "$schema": meta_schema,
                        "definitions": schema.get("definitions", {}),
                        "$ref": target_def_ref
                    }

                    sub_validator = validator_cls(wrapper_schema)
                    sub_errors = list(sub_validator.iter_errors(entity))

                    if not sub_errors:
                        return None

                    # Group errors by path relative to the entity
                    errors_by_path = {}
                    for sub_err in sub_errors:
                        if sub_err.path:
                            rel_path_str = " -> ".join(str(p) for p in sub_err.path)
                        else:
                            rel_path_str = ""

                        if rel_path_str not in errors_by_path:
                            errors_by_path[rel_path_str] = []

                        errors_by_path[rel_path_str].append(sub_err.message)

                    messages = []
                    for path, err_msgs in errors_by_path.items():
                        if path:
                            messages.append(f"  Path: {path}")
                            for msg in err_msgs:
                                messages.append(f"    - {msg}")
                        else:
                            for msg in err_msgs:
                                messages.append(f"  - {msg}")

                    e_type = entity.get('@type')
                    return f"Entity '{target_id}' (Type: {e_type}) is invalid:\n" + "\n".join(messages)

        # 2. Handle 'contains' errors (from allOf/contains)
        if (
            (not error.path or (len(error.path) > 0 and error.path[0] == '@graph'))
            and error.validator == 'contains'
        ):
            graph = instance.get('@graph', [])
            meta_schema = schema.get("$schema")
            defs = schema.get("definitions", {})

            # Identify which contains constraint failed via schema_path (e.g. allOf -> 0 -> contains)
            spath = list(error.schema_path)
            contains_schema = error.schema
            target_ref = contains_schema.get('$ref')

            if target_ref:
                def_name = target_ref.split('/')[-1]
            elif 'allOf' in spath and len(spath) >= 3:
                # Resolve from allOf index
                idx = spath[spath.index('allOf') + 1]
                graph_schema = schema['properties']['@graph']
                entry = graph_schema['allOf'][idx]
                c = entry.get('contains', {})
                target_ref = c.get('$ref')
                def_name = target_ref.split('/')[-1] if target_ref else None
            else:
                def_name = None

            if def_name and def_name in defs:
                # Extract expected @id from definition
                definition = defs[def_name]
                id_schema = definition.get('properties', {}).get('@id', {})
                expected_id = id_schema.get('const')

                # Find matching entity in @graph
                entity = None
                if expected_id:
                    entity = next((item for item in graph if item.get('@id') == expected_id), None)
                    label = f"{def_name} ('{expected_id}')"
                else:
                    label = def_name

                if not entity:
                    return f"{label} is missing from @graph."

                # Validate the entity against its def
                wrapper = {
                    "$schema": meta_schema,
                    "definitions": defs,
                    "$ref": f"#/definitions/{def_name}"
                }
                sub_v = validator_cls(wrapper)
                sub_errors = list(sub_v.iter_errors(entity))
                if sub_errors:
                    msgs = [e.message for e in sub_errors]
                    msg_list = "\n".join([f"  - {m}" for m in msgs])
                    return f"{label} Invalid:\n" + msg_list

            return "Global validation failed: a required entity is missing or invalid in @graph."
    # A failed heuristic must not hide the original validation error.
    except Exception as e:  # noqa: BLE001
        return f"Diagnosis failed: {e}. Original Error: {error.message}"

    return None


def get_types(entity):
    """Return @type as a set (handles str or list)."""
    t = entity.get('@type', [])
    if isinstance(t, str):
        return {t}
    if isinstance(t, list):
        return set(t)
    return set()


# Command-related types for reference validation
COMMAND_TYPES = {
    "CommandFile", "CommandFileReset", "CommandFileBootstrap", "CommandFileSetup",
    "CommandFileCopy", "CommandFileLooped", "LoopRun"
}


def validate_command_references(instance):
    """
    Validate that all command entities are reachable from Experiment.executedCommands.

    This semantic validation ensures:
    1. Start from Experiment entities, follow executedCommands
    2. Follow invokedCommands to sub-commands (recursively)
    3. For CommandFileLooped, follow loopRuns -> invokedCommands
    4. Collect all visited command IDs
    5. Check all command-type entities in @graph are visited

    Returns a list of error messages (empty if no errors).
    """
    errors = []
    graph = instance.get('@graph', [])

    # Build entity lookup by @id
    entities_by_id = {e.get('@id'): e for e in graph if e.get('@id')}

    # Find all command-type entities in the entire @graph
    all_commands_in_graph = set()
    for entity in graph:
        if get_types(entity) & COMMAND_TYPES:
            all_commands_in_graph.add(entity.get('@id'))

    if not all_commands_in_graph:
        return errors

    # Find all Experiment entities
    experiments = [e for e in graph if 'Experiment' in get_types(e)]
    if not experiments:
        errors.append("Cannot validate command references: No Experiment entities found")
        return errors

    # Set to track all visited commands
    visited_commands = set()

    def get_ref_id(ref):
        """Extract @id from a reference (dict or string)."""
        if isinstance(ref, dict) and '@id' in ref:
            return ref['@id']
        elif isinstance(ref, str):
            return ref
        return None

    def visit_command(command_id, visited):
        """Recursively visit a command and its sub-commands."""
        if command_id in visited:
            return

        entity = entities_by_id.get(command_id)
        if not entity:
            return

        if not (get_types(entity) & COMMAND_TYPES):
            return

        visited.add(command_id)

        # Follow invokedCommands
        invoked_refs = entity.get('invokedCommands', [])
        if invoked_refs:
            for ref in invoked_refs:
                sub_id = get_ref_id(ref)
                if sub_id:
                    visit_command(sub_id, visited)

        etypes = get_types(entity)

        # Follow loopRuns for CommandFileLooped
        if 'CommandFileLooped' in etypes:
            loop_run_refs = entity.get('loopRuns', [])
            if loop_run_refs:
                for ref in loop_run_refs:
                    loop_run_id = get_ref_id(ref)
                    if loop_run_id:
                        visit_command(loop_run_id, visited)

        # For LoopRun, also follow invokedCommands
        if 'LoopRun' in etypes:
            invoked_refs = entity.get('invokedCommands', [])
            if invoked_refs:
                for ref in invoked_refs:
                    sub_id = get_ref_id(ref)
                    if sub_id:
                        visit_command(sub_id, visited)

        # Follow bootstrap and setup for CommandFileReset
        if 'CommandFileReset' in etypes:
            for prop in ['bootstrapCommands', 'setupCommands']:
                sub_refs = entity.get(prop, [])
                if sub_refs:
                    for ref in sub_refs:
                        sub_id = get_ref_id(ref)
                        if sub_id:
                            visit_command(sub_id, visited)

    # Start from each Experiment's executedCommands
    for experiment in experiments:
        exec_cmd_refs = experiment.get('executedCommands', [])
        for ref in exec_cmd_refs:
            cmd_id = get_ref_id(ref)
            if cmd_id:
                visit_command(cmd_id, visited_commands)

    # Check if all command-type entities are reachable
    unreachable = all_commands_in_graph - visited_commands

    if unreachable:
        lines = []
        for cmd_id in sorted(unreachable):
            cmd_type = entities_by_id.get(cmd_id, {}).get('@type', '?')
            lines.append(f"  - {cmd_id} (Type: {cmd_type})")
        errors.append(
            f"Command reference validation failed: The following {len(unreachable)} command(s) "
            "are in the @graph but not reachable from any Experiment.executedCommands:\n"
            + "\n".join(lines)
        )

    return errors


def validate_command_invokedby_chain(instance):
    """
    Reverse command reachability check: for each command-type entity in @graph, follow the 'invokedBy'
    (or 'runOfLoopedCommand' for LoopRun) property upward. The chain must eventually reach a command
    listed in some Experiment.executedCommands.

    Returns a list of error messages (empty if no errors).
    """
    errors = []
    graph = instance.get('@graph', [])

    # Build entity lookup by @id
    entities_by_id = {e.get('@id'): e for e in graph if e.get('@id')}

    # Collect all command IDs in Experiment.executedCommands
    experiments = [e for e in graph if 'Experiment' in get_types(e)]
    if not experiments:
        return errors

    top_level_commands = set()
    for experiment in experiments:
        for ref in experiment.get('executedCommands', []):
            if isinstance(ref, dict) and '@id' in ref:
                top_level_commands.add(ref['@id'])
            elif isinstance(ref, str):
                top_level_commands.add(ref)

    # Find all command-type entities in @graph
    all_commands = [e for e in graph if get_types(e) & COMMAND_TYPES]

    if not all_commands:
        return errors

    # For each command, follow invokedBy / runOfLoopedCommand upward
    unreachable = []
    for cmd in all_commands:
        cmd_id = cmd.get('@id')

        # Already a top-level command -> reachable
        if cmd_id in top_level_commands:
            continue

        # Walk up via invokedBy or runOfLoopedCommand
        current_id = cmd_id
        visited = {current_id}
        reached_top = False

        while True:
            current = entities_by_id.get(current_id)
            if not current:
                break

            # LoopRun uses runOfLoopedCommand, others use invokedBy
            etypes = get_types(current)
            if 'LoopRun' in etypes:
                parent_ref = current.get('runOfLoopedCommand')
            else:
                parent_ref = current.get('invokedBy')

            if not parent_ref:
                break

            # Can be a single ref or a list
            if isinstance(parent_ref, list):
                parent_ref = parent_ref[0] if parent_ref else None

            if not parent_ref:
                break

            if isinstance(parent_ref, dict) and '@id' in parent_ref:
                parent_id = parent_ref['@id']
            elif isinstance(parent_ref, str):
                parent_id = parent_ref
            else:
                break

            if parent_id in visited:
                break  # Cycle detection
            visited.add(parent_id)

            if parent_id in top_level_commands:
                reached_top = True
                break

            current_id = parent_id

        if not reached_top:
            unreachable.append((cmd_id, cmd.get('@type', '?')))

    if unreachable:
        lines = [f"  - {cid} (Type: {ctype})" for cid, ctype in sorted(unreachable)]
        errors.append(
            f"invokedBy/runOfLoopedCommand chain validation failed: The following {len(unreachable)} command(s) "
            "cannot reach an Experiment.executedCommands entry via their invokedBy/runOfLoopedCommand chain:\n"
            + "\n".join(lines)
        )

    return errors


def validate_result_data_example_of_work(instance):
    """
    Validate that all files/datasets referenced in Experiment.resultData have an exampleOfWork property set.

    Returns a list of error messages (empty if no errors).
    """
    errors = []
    graph = instance.get('@graph', [])

    # Build entity lookup by @id
    entities_by_id = {e.get('@id'): e for e in graph if e.get('@id')}

    # Find all entities that can have resultData (Experiment, CommandFile types, LoopRun)
    target_types = {'Experiment'} | COMMAND_TYPES
    entities_with_results = [e for e in graph if get_types(e) & target_types]
    if not entities_with_results:
        return errors

    def get_ref_id(ref):
        if isinstance(ref, dict) and '@id' in ref:
            return ref['@id']
        elif isinstance(ref, str):
            return ref
        return None

    missing = []
    for entity in entities_with_results:
        parent_id = entity.get('@id', '?')
        result_refs = entity.get('resultData', [])
        for ref in result_refs:
            file_id = get_ref_id(ref)
            if not file_id:
                continue
            entity = entities_by_id.get(file_id)
            if not entity:
                continue
            if not entity.get('exampleOfWork'):
                missing.append((file_id, entity.get('@type', '?'), parent_id))

    if missing:
        lines = [f"  - {fid} (Type: {ftype}, Referenced by: {pid})" for fid, ftype, pid in missing]
        errors.append(
            f"exampleOfWork validation failed: The following {len(missing)} file(s) in "
            "resultData are missing the 'exampleOfWork' property:\n"
            + "\n".join(lines)
        )

    return errors


def validate_upload_in_result_data(instance):
    """
    Validate that all File/Dataset entities with the keyword 'upload' are referenced in some Experiment.resultData.

    Returns a list of error messages (empty if no errors).
    """
    errors = []
    graph = instance.get('@graph', [])

    # Build entity lookup by @id
    entities_by_id = {e.get('@id'): e for e in graph if e.get('@id')}

    # Find all File/Dataset entities with keyword "upload"
    upload_entities = set()
    for entity in graph:
        etypes = get_types(entity)
        if not (etypes & {'File', 'Dataset'}):
            continue
        keywords = entity.get('keywords', [])
        # keywords can be a list or a single string
        if isinstance(keywords, str):
            keywords = [keywords]
        if any(k.lower() == 'upload' for k in keywords if isinstance(k, str)):
            upload_entities.add(entity.get('@id'))

    if not upload_entities:
        return errors

    # Collect all IDs referenced in Experiment resultData vs Command resultData
    experiments = [e for e in graph if 'Experiment' in get_types(e)]
    commands = [e for e in graph if get_types(e) & COMMAND_TYPES]

    experiment_result_data_ids = set()
    for exp in experiments:
        for ref in exp.get('resultData', []):
            if isinstance(ref, dict) and '@id' in ref:
                experiment_result_data_ids.add(ref['@id'])
            elif isinstance(ref, str):
                experiment_result_data_ids.add(ref)

    command_result_data_ids = set()
    for cmd in commands:
        for ref in cmd.get('resultData', []):
            if isinstance(ref, dict) and '@id' in ref:
                command_result_data_ids.add(ref['@id'])
            elif isinstance(ref, str):
                command_result_data_ids.add(ref)

    # Check which upload entities are missing from either set
    missing_from_experiment = upload_entities - experiment_result_data_ids
    missing_from_commands = upload_entities - command_result_data_ids

    if missing_from_experiment or missing_from_commands:
        lines = []
        # Combine missing reports
        all_missing_ids = missing_from_experiment | missing_from_commands
        for eid in sorted(all_missing_ids):
            etype = entities_by_id.get(eid, {}).get('@type', '?')
            reasons = []
            if eid in missing_from_experiment:
                reasons.append("Experiment")
            if eid in missing_from_commands:
                reasons.append("CommandFile (or subtype)")
            lines.append(f"  - {eid} (Type: {etype}) - Missing from: {' & '.join(reasons)}")

        errors.append(
            "Upload file validation failed: Every File/Dataset with keyword 'upload' must be referenced in BOTH "
            "an Experiment's resultData AND a CommandFile's (or subtype's) resultData.\n"
            "The following files are missing references:\n"
            + "\n".join(lines)
        )

    return errors


def validate_graph_in_root_has_part(instance):
    """
    Validate that all data entities in @graph are reachable from the root data entry ('./') via hasPart chains.

    Contextual entities (those whose @id is not a relative path, e.g. URLs, #fragments, or special entries like
    'ro-crate-metadata.json') are excluded from this check.

    Returns a list of error messages (empty if no errors).
    """
    errors = []
    graph = instance.get('@graph', [])

    # Build entity lookup by @id
    entities_by_id = {e.get('@id'): e for e in graph if e.get('@id')}

    # Find the root data entry
    root = entities_by_id.get('./')
    if not root:
        errors.append("hasPart validation: No root data entry ('./' @id) found in @graph.")
        return errors

    # IDs to exclude from the check
    EXCLUDED_IDS = {'ro-crate-metadata.json', './'}

    # Types to exclude from the check (contextual entities)
    EXCLUDED_TYPES = {
        'ExperimentNode', 'Person', 'Role', 'Organization', 'CreativeWork', 'SoftwareApplication', 'OSImage'
    }

    def is_data_entity(entity):
        """
        Heuristic: data entities have relative path IDs.
        Contextual entities typically have URLs, #fragments, or other non-path identifiers.
        Certain @types are also excluded.
        """
        entity_id = entity.get('@id', '')
        if entity_id in EXCLUDED_IDS:
            return False
        if entity_id.startswith(('http://', 'https://')):
            return False
        if entity_id.startswith('#'):
            return False
        return not get_types(entity) & EXCLUDED_TYPES

    def get_ref_id(ref):
        if isinstance(ref, dict) and '@id' in ref:
            return ref['@id']
        elif isinstance(ref, str):
            return ref
        return None

    # Collect all IDs reachable from root via hasPart
    reachable = set()

    def collect_has_part(entity_id):
        if entity_id in reachable:
            return
        reachable.add(entity_id)
        entity = entities_by_id.get(entity_id)
        if not entity:
            return
        for ref in entity.get('hasPart', []):
            child_id = get_ref_id(ref)
            if child_id:
                collect_has_part(child_id)

    collect_has_part('./')

    # Check all data entities in @graph
    not_linked = []
    for entity in graph:
        eid = entity.get('@id')
        if not eid or not is_data_entity(entity):
            continue
        if eid not in reachable:
            not_linked.append((eid, entity.get('@type', '?')))

    if not_linked:
        lines = [f"  - {eid} (Type: {etype})" for eid, etype in sorted(not_linked)]
        errors.append(
            f"hasPart validation failed: The following {len(not_linked)} data entit(ies) are in "
            "@graph but not reachable from the root data entry ('./') via hasPart:\n"
            + "\n".join(lines)
        )

    return errors


def validate_haspart_references_exist(instance):
    """
    Validate that all entities referenced in any 'hasPart' property actually exist in the @graph.

    Returns a list of error messages (empty if no errors).
    """
    errors = []
    graph = instance.get('@graph', [])

    # Build entity lookup by @id
    entities_by_id = {e.get('@id'): e for e in graph if e.get('@id')}

    def get_ref_id(ref):
        if isinstance(ref, dict) and '@id' in ref:
            return ref['@id']
        elif isinstance(ref, str):
            return ref
        return None

    missing = []
    for entity in graph:
        parent_id = entity.get('@id', '?')
        has_part = entity.get('hasPart', [])
        for ref in has_part:
            child_id = get_ref_id(ref)
            if child_id and child_id not in entities_by_id:
                missing.append((child_id, parent_id))

    if missing:
        lines = [f"  - {cid} (Referenced by: {pid})" for cid, pid in missing]
        errors.append(
            "hasPart reference validation failed: The following entities are referenced in a "
            "'hasPart' list but do not exist in @graph:\n"
            + "\n".join(lines)
        )

    return errors


def validate_iso8601_duration(instance):
    """
    Validate that all 'duration' properties follow the ISO 8601 duration format (e.g., P3Y6M4DT12H30M5S).

    Returns a list of error messages (empty if no errors).
    """
    import re
    errors = []
    graph = instance.get('@graph', [])

    # ISO 8601 duration regex
    iso8601_duration_pattern = re.compile(
        r'^P'                                # Must start with P
        r'(?:(?:\d+(?:\.\d+)?Y)?'            # Years
        r'(?:\d+(?:\.\d+)?M)?'               # Months
        r'(?:\d+(?:\.\d+)?D)?)'              # Days
        r'(?:T'                              # Time part must start with T
        r'(?:\d+(?:\.\d+)?H)?'               # Hours
        r'(?:\d+(?:\.\d+)?M)?'               # Minutes
        r'(?:\d+(?:\.\d+)?S)?)?$'            # Seconds
    )

    invalid_durations = []

    for entity in graph:
        duration = entity.get('duration')
        if not duration:
            continue

        eid = entity.get('@id', '?')
        etype = entity.get('@type', '?')

        # Ensure it's a string before testing
        if not isinstance(duration, str):
            invalid_durations.append((eid, etype, str(duration), 'Not a string'))
            continue

        # Valid format must have at least one unit (can't be just 'P' or 'PT')
        if duration in ('P', 'PT') or not iso8601_duration_pattern.match(duration):
            invalid_durations.append((eid, etype, duration, 'Invalid format'))

    if invalid_durations:
        lines = [f"  - {eid} (Type: {etype}): '{val}' ({reason})" for eid, etype, val, reason in invalid_durations]
        errors.append(
            f"ISO 8601 duration validation failed: The following {len(invalid_durations)} 'duration' propert(ies) "
            "do not match the ISO 8601 format:\n"
            + "\n".join(lines)
        )

    return errors


def validate_ro_crate(schema_path, metadata_path):
    print("⚠️  Note: This validator is a work in progress. Main checks are functional, but not every edge case "
          "may be covered yet.")
    print()
    print(f"Loading Schema: {schema_path}")
    schema = load_json(schema_path)

    print(f"Loading RO-Crate: {metadata_path}")
    instance = load_json(metadata_path)

    # 1. Auto-detect validator (Draft 7, 2019-09, 2020-12)
    validator_cls = validators.validator_for(schema)
    validator = validator_cls(schema)

    # Check validator version
    if hasattr(validator_cls, 'META_SCHEMA'):
        meta_id = validator_cls.META_SCHEMA['$id']
    else:
        meta_id = 'Unknown'
    print(f"Using Validator: {meta_id}")

    print("Validating...")
    errors = list(validator.iter_errors(instance))

    if not errors:
        print("✅ Schema validation passed.")
    else:
        # Filter and Diagnose
        display_errors = []
        for error in errors:
            diagnosis = diagnose_error(error, instance, schema, validator_cls)
            if diagnosis:
                display_errors.append(diagnosis)
            elif "unevaluatedProperties" in error.message:
                display_errors.append(
                    f"Global Validation Error: {error.message}. Likely an issue with "
                    "@graph content not matching any allowed definitions."
                )
            else:
                path_str = ' -> '.join(str(p) for p in error.path) if error.path else '(root)'
                display_errors.append(f"  Message: {error.message}\n  Path: {path_str}")

        print(f"\n❌ Schema Validation FAILED: Found {len(errors)} error(s).")
        print("-" * 50)
        seen = set()
        count = 1
        for msg in display_errors:
            if msg in seen:
                continue
            seen.add(msg)
            print(f"Error {count}:")
            print(msg)
            print("-" * 50)
            count += 1

    # 2. Semantic validation
    print("\nRunning semantic validation...")
    semantic_errors = validate_command_references(instance)
    semantic_errors += validate_command_invokedby_chain(instance)
    semantic_errors += validate_result_data_example_of_work(instance)
    semantic_errors += validate_upload_in_result_data(instance)
    semantic_errors += validate_graph_in_root_has_part(instance)
    semantic_errors += validate_haspart_references_exist(instance)
    semantic_errors += validate_iso8601_duration(instance)

    if semantic_errors:
        print(f"\n⚠️  Semantic Validation: Found {len(semantic_errors)} issue(s).")
        print("-" * 50)
        for i, err in enumerate(semantic_errors, 1):
            print(f"Issue {i}:")
            print(err)
            print("-" * 50)
    else:
        print("✅ Semantic validation passed.")

    # Final summary
    if not errors and not semantic_errors:
        print("\n✅ All validations PASSED: The RO-Crate metadata file is valid.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Validate an RO-Crate metadata file against a JSON Schema (Auto-detect version).'
    )
    parser.add_argument('metadata', help='Path to the RO-Crate metadata file')
    parser.add_argument('--schema', help='Path to the RO-Crate JSON Schema', default=DEFAULT_SCHEMA)

    args = parser.parse_args()

    validate_ro_crate(args.schema, args.metadata)
