"""Machine-readable copy of Quality's coverage map (Quality acceptance 1).

Every minted ID → the test functions that cover it ("tests.<module>.<Class>.<method>")
or an "n/a — <why>" disposition. Rows for IDs whose completing slice is not yet Built
may be empty lists; the meta-test skips them and lists them.
"""

from __future__ import annotations

INV = "tests.unit.test_invariants.WriteGatedInvariants"
MS = "tests.unit.test_model_schema"
EL = "tests.unit.test_emitter_loader"
VR = "tests.unit.test_validator_rules"
ER = "tests.unit.test_errors_render"
GOLD = "tests.golden.test_canonical.Canonical"
CEL = "tests.contract.test_elements"
CERR = "tests.contract.test_errors_security"
FS = "tests.fitness.test_structure"
FG = "tests.fitness.test_governance_ops"
FD = "tests.fitness.test_delivery"
E2E = "tests.e2e.test_journeys.Journeys"

MAP: dict[str, list[str] | str] = {
    # personas — definitions
    "PERSONA-AGENT": "n/a — a persona definition; exercised by every E2E journey",
    "PERSONA-HUMAN": "n/a — a persona definition; exercised by the --human renderings",
    "PERSONA-CONVERTER": "n/a — a persona definition; exercised by the schema tests",
    # capabilities — slice 1
    "CAP-INIT": [f"{E2E}.test_cap_init"],
    "CAP-VALIDATE": [f"{E2E}.test_cap_validate_and_pathcheck"],
    "CAP-PATHCHECK": [f"{E2E}.test_cap_validate_and_pathcheck", f"{CEL}.Validate.test_check_paths"],
    "CAP-SCHEMA": [f"{E2E}.test_cap_schema"],
    "CAP-HELP": [f"{E2E}.test_cap_help"],
    # capabilities — later slices
    "CAP-QUERY": [],
    "CAP-SET": [],
    "CAP-ADD": [],
    "CAP-REMOVE": [],
    "CAP-COVERAGE": [],
    "CAP-COMMENT": [],
    "CAP-FORMAT": [],
    # success criteria
    "SUCCESS-ROUNDTRIP": [
        f"{GOLD}.test_canonical_validates_clean_and_round_trips",
        f"{GOLD}.test_emit_is_a_fixpoint_for_every_loadable_fixture",
    ],
    "SUCCESS-COMPLETE-OPS": [],
    "SUCCESS-BOUNDED-OUTPUT": [],
    "SUCCESS-CROSS-MODEL": "n/a — not automated: an operator observation recorded per trial "
    "session",
    "SUCCESS-SCHEMA-MATCH": [
        f"{FG}.SchemaFile.test_shipped_file_equals_embedded_schema_and_readme_checksum"
    ],
    # entities
    "ENTITY-MAP": [
        f"{MS}.FromPlain.test_full_binding_converts_and_projects_back",
        f"{GOLD}.test_canonical_validates_clean_and_round_trips",
    ],
    "ENTITY-CONTRACT-ID": [f"{MS}.ContractIdGrammar.test_table"],
    "ENTITY-BINDING": [f"{MS}.FromPlain.test_full_binding_converts_and_projects_back"],
    "ENTITY-LOCATOR": [f"{MS}.FromPlain.test_full_binding_converts_and_projects_back"],
    "ENTITY-FIELD-LOCATOR": [f"{MS}.FromPlain.test_full_binding_converts_and_projects_back"],
    "ENTITY-WIRE": [f"{MS}.Dataclasses.test_anchor_projection_and_wire_emptiness"],
    "ENTITY-ASSERTION": [f"{MS}.FromPlain.test_full_binding_converts_and_projects_back"],
    "ENTITY-PATH": [f"{MS}.PathForm.test_table"],
    "ENTITY-COVERAGE": [f"{MS}.Dataclasses.test_anchor_projection_and_wire_emptiness"],
    "ENTITY-COMMENT": [f"{EL}.LoaderEdges.test_carriers_round_trip_and_transparent_markers"],
    "ENTITY-FINDING": [f"{INV}.test_findings_are_in_document_order_then_code_and_deduplicated"],
    # invariants — write-gated (unit half completes in slice 1)
    "INV-ID-GRAMMAR": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{MS}.ContractIdGrammar.test_table",
    ],
    "INV-ID-UNIQUE": [f"{EL}.LoaderEdges.test_parse_errors"],
    "INV-SCHEMA-VERSION": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{INV}.test_missing_schema_version_fires_both_codes",
    ],
    "INV-CLOSED-KEYS": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{MS}.FromPlain.test_type_and_required_key_violations_report_closed_keys",
    ],
    "INV-NO-LINE-NUMBERS": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{INV}.test_lines_key_fires_both_closed_keys_and_no_line_numbers",
    ],
    "INV-PATH-FORM": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "INV-PATH-EXISTS": [f"{INV}.test_path_exists_only_with_the_flag"],
    "INV-SYMBOL-NONEMPTY": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{VR}.ScalarAndSymbolRules.test_control_character_in_symbol",
        f"{MS}.ControlCharacters.test_table",
    ],
    "INV-ROLE-VALUES": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "INV-WIRE-SUBSET": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "INV-ASSERTION-SHAPE": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{VR}.AssertionRules.test_bound_assertion_missing_keys",
        f"{VR}.AssertionRules.test_mixed_shape",
        f"{VR}.AssertionRules.test_present_but_empty",
    ],
    "INV-FIELD-NAME": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{VR}.FieldRules.test_empty_and_control_character_names",
    ],
    "INV-COVERAGE-WELLFORMED": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{VR}.CoverageRules.test_neither_key",
        f"{VR}.CoverageRules.test_fully_bound_arms",
        f"{VR}.CoverageRules.test_curated_arms",
    ],
    "INV-LOCATOR-UNIQUE": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "INV-ASSERTION-UNIQUE": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "INV-COMMENT-ANCHORED": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{EL}.LoaderEdges.test_parse_errors",
    ],
    "INV-COMMENT-TEXT": [
        f"{INV}.test_each_write_gated_invariant_fires_exactly_once",
        f"{VR}.CommentRules.test_edge_empty_line_and_control_character",
        f"{EL}.LoaderEdges.test_leader_stripping_and_trailing_whitespace_in_comments",
    ],
    # invariants — advisory
    "INV-BYTES": [
        f"{INV}.test_advisory_invariants_are_warnings",
        f"{EL}.LoaderEdges.test_byte_layer",
    ],
    "INV-ROLE-REQUIRES-WIRE": [f"{INV}.test_advisory_invariants_are_warnings"],
    "INV-OWNED-TWICE": [
        f"{INV}.test_advisory_invariants_are_warnings",
        f"{INV}.test_owned_twice_names_the_other_binding",
    ],
    # invariants — tool properties
    "INV-CANONICAL-FIXPOINT": [f"{GOLD}.test_emit_is_a_fixpoint_for_every_loadable_fixture"],
    "INV-ORDER-PRESERVED": [],
    "INV-ATOMIC-WRITE": [f"{EL}.AtomicWrite.test_failed_rename_leaves_target_and_no_temp_file"],
    # components
    "COMPONENT-CLI": [f"{FS}.Orchestration.test_flow_components_are_isolated_and_cli_orchestrates"],
    "COMPONENT-LOADER": [
        f"{FS}.Imports.test_ruamel_only_in_loader_and_no_other_third_party",
        f"{EL}.LoaderEdges.test_carriers_round_trip_and_transparent_markers",
    ],
    "COMPONENT-MODEL": [f"{MS}.FromPlain.test_full_binding_converts_and_projects_back"],
    "COMPONENT-VALIDATOR": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "COMPONENT-COMMANDS": [
        f"{FS}.Orchestration.test_flow_components_are_isolated_and_cli_orchestrates"
    ],
    "COMPONENT-EMITTER": [
        f"{FS}.SoleWriter.test_only_emitter_writes",
        f"{EL}.Layout.test_every_construct_and_comment_carrier",
    ],
    "COMPONENT-RENDERER": [f"{CEL}.Envelope.test_compact_single_document_with_fixed_key_order"],
    "COMPONENT-SCHEMA": [f"{MS}.JsonSchema.test_every_rule_table_entry_appears_in_the_schema"],
    # patterns
    "PATTERN-ERROR-ENVELOPE": [
        f"{CERR}.ErrorCatalog.test_err_internal_from_an_unexpected_exception",
        f"{CEL}.Envelope.test_debug_adds_a_traceback_only_on_stderr",
    ],
    "PATTERN-VALIDATE-AROUND-WRITE": [],
    "PATTERN-ATOMIC-REPLACE": [
        f"{EL}.AtomicWrite.test_failed_rename_leaves_target_and_no_temp_file"
    ],
    "PATTERN-EXIT-CODES": [f"{CERR}.ErrorCatalog.test_exit_code_partition"],
    "PATTERN-OUTPUT-MODE": [
        f"{CEL}.Envelope.test_compact_single_document_with_fixed_key_order",
        f"{CEL}.Envelope.test_human_rendering_minimums",
    ],
    # ADRs
    "ADR-SINGLE-FILE": [f"{CEL}.Init.test_file_option_before_or_after_the_command"],
    "ADR-STRUCTURAL-ONLY": [f"{CERR}.SecurityForcings.test_sec_file_footprint"],
    "ADR-NO-LINE-NUMBERS": [f"{INV}.test_each_write_gated_invariant_fires_exactly_once"],
    "ADR-LOAD-RUAMEL-EMIT-OWN": [
        f"{FS}.Imports.test_ruamel_only_in_loader_and_no_other_third_party",
        f"{FS}.SoleWriter.test_only_emitter_writes",
    ],
    "ADR-ARGPARSE": [f"{FS}.Imports.test_argparse_only_in_cli"],
    "ADR-SCHEMA-SINGLE-SOURCE": [
        f"{FG}.SchemaFile.test_shipped_file_equals_embedded_schema_and_readme_checksum"
    ],
    "ADR-OWN-SHAPE-VALIDATOR": [
        f"{FS}.Imports.test_ruamel_only_in_loader_and_no_other_third_party",
        f"{MS}.JsonSchema.test_every_rule_table_entry_appears_in_the_schema",
    ],
    "ADR-FORMAT-ONLY-REORDERS": [],
    "ADR-INIT-REQUIRED": [
        f"{CERR}.ErrorCatalog.test_err_file_missing",
        f"{CEL}.Init.test_refuses_an_existing_target",
    ],
    "ADR-NO-SILENT-DEFAULTS": [f"{CERR}.ErrorCatalog.test_err_parse_fixtures_and_generated_bytes"],
    "ADR-MAJOR-PER-TEMPLATE": [
        f"{FG}.PinsAndWorkflow.test_pyproject_pins",
        f"{CEL}.Validate.test_schema_version_mismatch_is_a_finding_not_an_error",
    ],
    "ADR-NUMERIC-IDS-REJECTED": [f"{MS}.ContractIdGrammar.test_table"],
    "ADR-NO-LOGGING": [f"{FS}.Imports.test_forbidden_modules_and_calls"],
    # CLI elements — slice 1
    "CLI-INIT": [
        f"{CEL}.Init.test_creates_the_canonical_empty_map",
        f"{CEL}.Init.test_refuses_an_existing_target",
    ],
    "CLI-VALIDATE": [
        f"{CEL}.Validate.test_clean_file",
        f"{CEL}.Validate.test_error_findings_exit_1_with_ok_true",
        f"{CEL}.Validate.test_check_paths",
    ],
    "CLI-SCHEMA": [f"{CEL}.Schema.test_raw_schema_and_checksum"],
    "CLI-HELP": [
        f"{CEL}.HelpAndVersion.test_help_at_every_level_is_plain_text",
        f"{CEL}.HelpAndVersion.test_help_on_unknown_command_is_usage_error",
    ],
    "CLI-VERSION": [f"{CEL}.HelpAndVersion.test_version"],
    # CLI elements — later slices
    "CLI-FORMAT": [],
    "CLI-GET": [],
    "CLI-LIST": [],
    "CLI-SET": [],
    "CLI-ADD-LOCATOR": [],
    "CLI-ADD-FIELD": [],
    "CLI-ADD-ASSERTION": [],
    "CLI-REMOVE": [],
    "CLI-COVERAGE-GET": [],
    "CLI-COVERAGE-FULLY-BOUND": [],
    "CLI-COVERAGE-CURATED": [],
    "CLI-COMMENT-GET": [],
    "CLI-COMMENT-SET": [],
    "CLI-COMMENT-UNSET": [],
    # output documents — slice 1
    "OUT-ENVELOPE": [f"{CEL}.Envelope.test_compact_single_document_with_fixed_key_order"],
    "OUT-ERROR": [
        f"{CERR}.ErrorCatalog.test_err_usage_conditions",
        f"{ER}.RendererProjections.test_findings_and_anchor_details",
        f"{CEL}.Init.test_refuses_an_existing_target",
    ],
    "OUT-FINDING": [f"{CEL}.Validate.test_error_findings_exit_1_with_ok_true"],
    "OUT-ANCHOR": [f"{CEL}.Validate.test_error_findings_exit_1_with_ok_true"],
    "OUT-VALIDATE-RESULT": [f"{CEL}.Validate.test_clean_file"],
    "OUT-INIT-RESULT": [f"{CEL}.Init.test_creates_the_canonical_empty_map"],
    "OUT-SCHEMA": [f"{CEL}.Schema.test_raw_schema_and_checksum"],
    # output documents — later slices
    "OUT-BINDING": [],
    "OUT-LOCATOR": [],
    "OUT-FIELD-LOCATOR": [],
    "OUT-ASSERTION": [],
    "OUT-BINDING-SUMMARY": [],
    "OUT-COVERAGE": [],
    "OUT-COMMENT": [],
    "OUT-FORMAT-RESULT": [],
    "OUT-WRITE-RESULT": [],
    # errors — slice 1
    "ERR-USAGE": [f"{CERR}.ErrorCatalog.test_err_usage_conditions"],
    "ERR-FILE-MISSING": [f"{CERR}.ErrorCatalog.test_err_file_missing"],
    "ERR-FILE-EXISTS": [f"{CEL}.Init.test_refuses_an_existing_target"],
    "ERR-IO": [
        f"{CERR}.ErrorCatalog.test_err_io_directory_target",
        f"{CEL}.Init.test_unwritable_location_is_io_error",
    ],
    "ERR-PARSE": [f"{CERR}.ErrorCatalog.test_err_parse_fixtures_and_generated_bytes"],
    "ERR-FILE-TOO-LARGE": [f"{CEL}.Validate.test_size_cap_and_lift"],
    "ERR-INTERNAL": [f"{CERR}.ErrorCatalog.test_err_internal_from_an_unexpected_exception"],
    # errors — later slices
    "ERR-SCHEMA-VERSION": [],
    "ERR-FILE-INVALID": [],
    "ERR-NOT-FOUND": [],
    "ERR-DUPLICATE": [],
    "ERR-INPUT-INVALID": [],
    # security assertions
    "SEC-ZERO-NETWORK": [
        f"{FS}.Imports.test_forbidden_modules_and_calls",
        f"{CERR}.SecurityForcings.test_sec_zero_network",
    ],
    "SEC-ZERO-EXEC": [
        f"{FS}.Imports.test_forbidden_modules_and_calls",
        f"{CERR}.SecurityForcings.test_sec_zero_exec",
    ],
    "SEC-FILE-FOOTPRINT": [f"{CERR}.SecurityForcings.test_sec_file_footprint"],
    "SEC-NO-AMBIENT-CONFIG": [
        f"{FS}.Imports.test_forbidden_modules_and_calls",
        f"{CERR}.SecurityForcings.test_sec_no_ambient_config_determinism",
    ],
    "SEC-FAIL-CLOSED": [
        f"{CERR}.SecurityForcings.test_sec_fail_closed_no_traceback",
        f"{CEL}.Validate.test_size_cap_and_lift",
    ],
    "SEC-SYMLINK-FINAL-TARGET": [f"{CERR}.SecurityForcings.test_sec_symlink_final_target"],
    "SEC-NO-SECRETS": [
        f"{CERR}.SecurityForcings.test_sec_no_secrets_surface",
        f"{FG}.SchemaFile.test_shipped_file_equals_embedded_schema_and_readme_checksum",
    ],
    "SEC-TRUST-BOUNDARY": [
        f"{FS}.Imports.test_forbidden_modules_and_calls",
        f"{CERR}.SecurityForcings.test_sec_trust_boundary_mode_bits",
    ],
    # policies
    "POLICY-OUTBOUND-MIT": [
        f"{FG}.Naming.test_clause_4_license_file",
        f"{FG}.LicenceAndContributionSentences.test_readme_names_mit_and_contribution_terms_and_attribution",
    ],
    "POLICY-INBOUND-MIT-ONLY": [
        f"{FG}.LicenceGate.test_matching_rule",
        f"{FG}.LicenceGate.test_gate_passes_in_this_environment",
    ],
    "POLICY-CONTRIBUTIONS-MIT": [
        f"{FG}.LicenceAndContributionSentences.test_readme_names_mit_and_contribution_terms_and_attribution"
    ],
    "POLICY-SOURCE-MARKER": [f"{FS}.PragmasAndMarkers.test_source_markers_are_well_formed_and_mit"],
    "POLICY-PROVENANCE-PASS": "n/a — not automated: the release slice's review, recorded in "
    "docs/IMPLEMENTATION.md",
    "POLICY-NAMING-ENFORCEMENT": [
        f"{FG}.Naming.test_clause_1_independence_sentence_verbatim",
        f"{FG}.Naming.test_clause_2_versioned_conformance_phrase_and_no_forbidden_claims",
        f"{FG}.Naming.test_clause_3_no_normative_text_reproduced_in_product_artifacts",
    ],
    # dependencies, environments, tools
    "DEP-RUAMEL-YAML": [f"{FG}.PinsAndWorkflow.test_pyproject_pins"],
    "ENV-LOCAL": [f"{FG}.PinsAndWorkflow.test_pyproject_pins"],
    "ENV-CI": [f"{FG}.PinsAndWorkflow.test_workflow"],
    "TOOL-RUFF": [f"{FG}.PinsAndWorkflow.test_pyproject_pins"],
    "TOOL-PYREFLY": [f"{FG}.PinsAndWorkflow.test_pyproject_pins"],
    "TOOL-SETUPTOOLS": [f"{FG}.PinsAndWorkflow.test_pyproject_pins"],
    "TOOL-ACTIONS-CHECKOUT": [f"{FG}.PinsAndWorkflow.test_workflow"],
    "TOOL-ACTIONS-SETUP-PYTHON": [f"{FG}.PinsAndWorkflow.test_workflow"],
    # legal
    "LEGAL-DICTUM-NAMING": [
        f"{FG}.Naming.test_clause_1_independence_sentence_verbatim",
        f"{FG}.Naming.test_clause_4_license_file",
    ],
    # the one named contract without a register line
    "E2E-STANDARD": [
        f"{E2E}.test_cap_init",
        "tests.e2e.test_journeys.MetaInvocations.test_every_built_element_was_driven",
    ],
}
