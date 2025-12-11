(** Tests for Layer 2: Rule DSL Types *)

open Droit_core.Rule_dsl
open Droit_core.Ontology

(** Helper to read file contents *)
let read_file filename =
  let ic = open_in filename in
  let n = in_channel_length ic in
  let s = really_input_string ic n in
  close_in ic;
  s

(** Test loading MiCA Art. 36 rule from YAML *)
let test_load_mica_art36 () =
  let yaml_content = read_file "../rule_examples/mica_art36.yaml" in
  match rule_of_yaml_string yaml_content with
  | Ok rule ->
    (* Test rule_id *)
    Alcotest.(check string) "rule_id"
      "mica_art36_casp_authorization" rule.rule_id;

    (* Test title *)
    Alcotest.(check string) "title"
      "CASP Authorization Requirement" rule.title;

    (* Test source fields *)
    Alcotest.(check string) "source.document_id"
      "MiCA" rule.source.document_id;
    Alcotest.(check string) "source.article"
      "36" rule.source.article;
    Alcotest.(check (list string)) "source.paragraphs"
      ["1"; "2"; "3"] rule.source.paragraphs;
    Alcotest.(check (list int)) "source.pages"
      [58; 59] rule.source.pages;

    (* Test effective dates *)
    Alcotest.(check (option string)) "effective_from"
      (Some "2024-12-30") rule.effective_from;
    Alcotest.(check (option string)) "effective_to"
      None rule.effective_to;

    (* Test applies_if has expected conditions *)
    Alcotest.(check int) "applies_if count"
      3 (List.length rule.applies_if);

    (* Test metadata *)
    (match rule.metadata with
    | Some meta ->
      Alcotest.(check string) "metadata.version" "1.0.0" meta.version;
      Alcotest.(check (option string)) "metadata.author"
        (Some "Droit Team") meta.author;
      Alcotest.(check bool) "has MiCA tag"
        true (List.mem "MiCA" meta.tags);
      Alcotest.(check bool) "has CASP tag"
        true (List.mem "CASP" meta.tags)
    | None ->
      Alcotest.fail "Expected metadata to be present")

  | Error msg ->
    Alcotest.fail ("Failed to parse YAML: " ^ msg)

(** Test constructing rule programmatically *)
let test_rule_construction () =
  let source = make_source
    ~document_id:"TestDoc"
    ~article:"1"
    ~paragraphs:["1"; "2"]
    ~pages:[1; 2]
    ()
  in
  let decision_tree = make_branch
    ~condition:(field_equals "status" "active")
    ~if_true:(make_leaf
      ~outcome:Authorized
      ~explanation:"Entity is authorized"
      ~obligations:["Maintain compliance"]
      ())
    ~if_false:(make_leaf
      ~outcome:NotAuthorized
      ~explanation:"Entity not authorized"
      ())
  in
  let rule = make_rule
    ~rule_id:"test_rule_001"
    ~title:"Test Rule"
    ~description:"A test rule for unit testing"
    ~applies_if:[ActorTypeCheck CASP; ActivityTypeCheck Custody]
    ~decision_tree
    ~source
    ~effective_from:"2024-01-01"
    ()
  in
  Alcotest.(check string) "rule_id" "test_rule_001" rule.rule_id;
  Alcotest.(check string) "title" "Test Rule" rule.title;
  Alcotest.(check int) "applies_if count" 2 (List.length rule.applies_if);
  Alcotest.(check (option string)) "effective_from"
    (Some "2024-01-01") rule.effective_from

(** Test YAML round-trip for a rule *)
let test_rule_yaml_roundtrip () =
  let source = make_source
    ~document_id:"RoundtripDoc"
    ~article:"99"
    ()
  in
  let decision_tree = make_leaf
    ~outcome:Permitted
    ~explanation:"Always permitted"
    ()
  in
  let original = make_rule
    ~rule_id:"roundtrip_test"
    ~title:"Roundtrip Test Rule"
    ~description:"Testing YAML serialization"
    ~applies_if:[AlwaysTrue]
    ~decision_tree
    ~source
    ()
  in
  match rule_to_yaml_string original with
  | Ok yaml_str ->
    (match rule_of_yaml_string yaml_str with
    | Ok parsed ->
      Alcotest.(check string) "rule_id roundtrip"
        original.rule_id parsed.rule_id;
      Alcotest.(check string) "title roundtrip"
        original.title parsed.title;
      Alcotest.(check string) "source.document_id roundtrip"
        original.source.document_id parsed.source.document_id
    | Error msg ->
      Alcotest.fail ("Parsing roundtrip failed: " ^ msg))
  | Error msg ->
    Alcotest.fail ("Serialization failed: " ^ msg)

(** Test condition expression construction *)
let test_condition_expr_construction () =
  let expr = AllOf [
    ActorTypeCheck CASP;
    AnyOf [
      ActivityTypeCheck Custody;
      ActivityTypeCheck Exchange;
    ];
    JurisdictionCheck "EU";
    NotExpr (FieldCheck {
      field = "exempt";
      op = Eq;
      value = BoolVal true;
    });
  ] in
  (* Verify structure through pattern matching *)
  match expr with
  | AllOf [ActorTypeCheck CASP; AnyOf _; JurisdictionCheck "EU"; NotExpr _] ->
    Alcotest.(check pass) "condition structure" () ()
  | _ ->
    Alcotest.fail "Unexpected condition expression structure"

(** Test decision tree construction *)
let test_decision_tree_construction () =
  let tree = make_branch
    ~condition:(field_in "entity_type" ["bank"; "investment_firm"])
    ~if_true:(make_leaf
      ~outcome:Exempt
      ~explanation:"Financial institution exemption"
      ~references:["Art. 36(1)"]
      ())
    ~if_false:(make_branch
      ~condition:(field_greater_than "aum_eur" 100000000.0)
      ~if_true:(make_leaf
        ~outcome:RequiresReview
        ~explanation:"Large entity requires enhanced review"
        ())
      ~if_false:(make_leaf
        ~outcome:NotAuthorized
        ~explanation:"Standard authorization required"
        ~obligations:["Submit application"; "Pay fees"]
        ())
    )
  in
  (* Verify we can traverse the tree *)
  match tree with
  | Branch { if_true = Leaf l1; if_false = Branch { if_true = Leaf l2; _ }; _ } ->
    Alcotest.(check bool) "first outcome is Exempt"
      true (l1.outcome = Exempt);
    Alcotest.(check bool) "second outcome is RequiresReview"
      true (l2.outcome = RequiresReview)
  | _ ->
    Alcotest.fail "Unexpected decision tree structure"

(** Test comparison operators *)
let test_comparison_ops () =
  let checks = [
    FieldCheck { field = "x"; op = Eq; value = IntVal 5 };
    FieldCheck { field = "y"; op = Ne; value = StringVal "foo" };
    FieldCheck { field = "z"; op = Lt; value = FloatVal 3.14 };
    FieldCheck { field = "w"; op = Ge; value = IntVal 0 };
    FieldCheck { field = "list"; op = In; value = ListVal ["a"; "b"; "c"] };
    FieldCheck { field = "ref"; op = Eq; value = FieldRef "other_field" };
  ] in
  Alcotest.(check int) "created 6 checks" 6 (List.length checks)

(** Test all decision outcomes *)
let test_decision_outcomes () =
  let outcomes = [
    Authorized; NotAuthorized; Exempt; RequiresReview;
    RequiresNotification; Prohibited; Permitted; Custom "special_case"
  ] in
  Alcotest.(check int) "8 outcomes" 8 (List.length outcomes);
  match List.hd (List.rev outcomes) with
  | Custom s -> Alcotest.(check string) "custom outcome" "special_case" s
  | _ -> Alcotest.fail "Expected Custom outcome"

(** All rule DSL tests *)
let () =
  Alcotest.run "Rule_dsl" [
    "yaml_loading", [
      Alcotest.test_case "load mica_art36" `Quick test_load_mica_art36;
      Alcotest.test_case "yaml roundtrip" `Quick test_rule_yaml_roundtrip;
    ];
    "construction", [
      Alcotest.test_case "rule construction" `Quick test_rule_construction;
      Alcotest.test_case "condition expressions" `Quick test_condition_expr_construction;
      Alcotest.test_case "decision tree" `Quick test_decision_tree_construction;
    ];
    "types", [
      Alcotest.test_case "comparison operators" `Quick test_comparison_ops;
      Alcotest.test_case "decision outcomes" `Quick test_decision_outcomes;
    ];
  ]
