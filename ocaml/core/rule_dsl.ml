(** Layer 2: Rule DSL Types

    This module defines the schema for YAML rule files. Rules are
    the executable representation of regulatory provisions, containing
    conditions (applies_if), decision trees, and source metadata.
*)

open Ontology

(** Unique identifier for a rule *)
type rule_id = string

(** Source reference linking a rule to its legal text *)
type source = {
  document_id : string;
  article : string;
  paragraphs : string list;
  pages : int list;
  url : string option;
}

let source_to_yaml s =
  `O ([
    ("document_id", `String s.document_id);
    ("article", `String s.article);
    ("paragraphs", `A (List.map (fun p -> `String p) s.paragraphs));
    ("pages", `A (List.map (fun p -> `Float (float_of_int p)) s.pages));
  ] @ match s.url with
    | Some u -> [("url", `String u)]
    | None -> [])

let source_of_yaml = function
  | `O fields ->
    let get k = List.assoc_opt k fields in
    (match get "document_id", get "article" with
    | Some (`String document_id), Some (`String article) ->
      let paragraphs = match get "paragraphs" with
        | Some (`A items) ->
          List.filter_map (function `String s -> Some s | _ -> None) items
        | _ -> []
      in
      let pages = match get "pages" with
        | Some (`A items) ->
          List.filter_map (function
            | `Float f -> Some (int_of_float f)
            | _ -> None) items
        | _ -> []
      in
      let url = match get "url" with
        | Some (`String u) -> Some u
        | _ -> None
      in
      Ok { document_id; article; paragraphs; pages; url }
    | _ -> Error "Missing required fields for source")
  | _ -> Error "Expected object for source"

(** Comparison operators for condition expressions *)
type comparison_op =
  | Eq    (** Equal *)
  | Ne    (** Not equal *)
  | Lt    (** Less than *)
  | Le    (** Less than or equal *)
  | Gt    (** Greater than *)
  | Ge    (** Greater than or equal *)
  | In    (** Member of list *)
  | NotIn (** Not member of list *)

let comparison_op_to_string = function
  | Eq -> "Eq" | Ne -> "Ne" | Lt -> "Lt" | Le -> "Le"
  | Gt -> "Gt" | Ge -> "Ge" | In -> "In" | NotIn -> "NotIn"

let comparison_op_of_string = function
  | "Eq" -> Ok Eq | "Ne" -> Ok Ne | "Lt" -> Ok Lt | "Le" -> Ok Le
  | "Gt" -> Ok Gt | "Ge" -> Ok Ge | "In" -> Ok In | "NotIn" -> Ok NotIn
  | s -> Error ("Unknown comparison operator: " ^ s)

let comparison_op_to_yaml op = `String (comparison_op_to_string op)

let comparison_op_of_yaml = function
  | `String s -> comparison_op_of_string s
  | _ -> Error "Expected string for comparison_op"

(** A value in condition expressions *)
type condition_value =
  | StringVal of string
  | IntVal of int
  | FloatVal of float
  | BoolVal of bool
  | ListVal of string list
  | FieldRef of string  (** Reference to input field *)

let condition_value_to_yaml = function
  | StringVal s -> `O [("StringVal", `String s)]
  | IntVal i -> `O [("IntVal", `Float (float_of_int i))]
  | FloatVal f -> `O [("FloatVal", `Float f)]
  | BoolVal b -> `O [("BoolVal", `Bool b)]
  | ListVal lst -> `O [("ListVal", `A (List.map (fun s -> `String s) lst))]
  | FieldRef f -> `O [("FieldRef", `String f)]

let condition_value_of_yaml = function
  | `O [("StringVal", `String s)] -> Ok (StringVal s)
  | `O [("IntVal", `Float f)] -> Ok (IntVal (int_of_float f))
  | `O [("FloatVal", `Float f)] -> Ok (FloatVal f)
  | `O [("BoolVal", `Bool b)] -> Ok (BoolVal b)
  | `O [("ListVal", `A items)] ->
    let strings = List.filter_map (function `String s -> Some s | _ -> None) items in
    Ok (ListVal strings)
  | `O [("FieldRef", `String f)] -> Ok (FieldRef f)
  | _ -> Error "Invalid condition_value"

(** Condition expressions for applies_if clauses *)
type condition_expr =
  | FieldCheck of {
      field : string;
      op : comparison_op;
      value : condition_value;
    }
  | ActorTypeCheck of actor_type
  | InstrumentTypeCheck of instrument_type
  | ActivityTypeCheck of activity_type
  | JurisdictionCheck of string
  | AllOf of condition_expr list
  | AnyOf of condition_expr list
  | NoneOf of condition_expr list
  | NotExpr of condition_expr
  | AlwaysTrue
  | AlwaysFalse

let rec condition_expr_to_yaml = function
  | FieldCheck { field; op; value } ->
    `O [("FieldCheck", `O [
      ("field", `String field);
      ("op", comparison_op_to_yaml op);
      ("value", condition_value_to_yaml value);
    ])]
  | ActorTypeCheck at -> `O [("ActorTypeCheck", actor_type_to_yaml at)]
  | InstrumentTypeCheck it -> `O [("InstrumentTypeCheck", instrument_type_to_yaml it)]
  | ActivityTypeCheck at -> `O [("ActivityTypeCheck", activity_type_to_yaml at)]
  | JurisdictionCheck j -> `O [("JurisdictionCheck", `String j)]
  | AllOf exprs -> `O [("AllOf", `A (List.map condition_expr_to_yaml exprs))]
  | AnyOf exprs -> `O [("AnyOf", `A (List.map condition_expr_to_yaml exprs))]
  | NoneOf exprs -> `O [("NoneOf", `A (List.map condition_expr_to_yaml exprs))]
  | NotExpr expr -> `O [("NotExpr", condition_expr_to_yaml expr)]
  | AlwaysTrue -> `String "AlwaysTrue"
  | AlwaysFalse -> `String "AlwaysFalse"

let rec condition_expr_of_yaml = function
  | `String "AlwaysTrue" -> Ok AlwaysTrue
  | `String "AlwaysFalse" -> Ok AlwaysFalse
  | `O [("FieldCheck", `O fields)] ->
    let get k = List.assoc_opt k fields in
    (match get "field", get "op", get "value" with
    | Some (`String field), Some op_yaml, Some value_yaml ->
      (match comparison_op_of_yaml op_yaml, condition_value_of_yaml value_yaml with
      | Ok op, Ok value -> Ok (FieldCheck { field; op; value })
      | Error e, _ | _, Error e -> Error e)
    | _ -> Error "Invalid FieldCheck")
  | `O [("ActorTypeCheck", v)] ->
    (match actor_type_of_yaml v with
    | Ok at -> Ok (ActorTypeCheck at)
    | Error e -> Error e)
  | `O [("InstrumentTypeCheck", v)] ->
    (match instrument_type_of_yaml v with
    | Ok it -> Ok (InstrumentTypeCheck it)
    | Error e -> Error e)
  | `O [("ActivityTypeCheck", v)] ->
    (match activity_type_of_yaml v with
    | Ok at -> Ok (ActivityTypeCheck at)
    | Error e -> Error e)
  | `O [("JurisdictionCheck", `String j)] -> Ok (JurisdictionCheck j)
  | `O [("AllOf", `A items)] ->
    let exprs = List.filter_map (fun item ->
      match condition_expr_of_yaml item with Ok e -> Some e | Error _ -> None
    ) items in
    Ok (AllOf exprs)
  | `O [("AnyOf", `A items)] ->
    let exprs = List.filter_map (fun item ->
      match condition_expr_of_yaml item with Ok e -> Some e | Error _ -> None
    ) items in
    Ok (AnyOf exprs)
  | `O [("NoneOf", `A items)] ->
    let exprs = List.filter_map (fun item ->
      match condition_expr_of_yaml item with Ok e -> Some e | Error _ -> None
    ) items in
    Ok (NoneOf exprs)
  | `O [("NotExpr", v)] ->
    (match condition_expr_of_yaml v with
    | Ok expr -> Ok (NotExpr expr)
    | Error e -> Error e)
  | _ -> Error "Invalid condition_expr"

(** Outcome of a decision *)
type decision_outcome =
  | Authorized
  | NotAuthorized
  | Exempt
  | RequiresReview
  | RequiresNotification
  | Prohibited
  | Permitted
  | Custom of string

let decision_outcome_to_string = function
  | Authorized -> "Authorized"
  | NotAuthorized -> "NotAuthorized"
  | Exempt -> "Exempt"
  | RequiresReview -> "RequiresReview"
  | RequiresNotification -> "RequiresNotification"
  | Prohibited -> "Prohibited"
  | Permitted -> "Permitted"
  | Custom s -> s

let decision_outcome_of_string = function
  | "Authorized" -> Authorized
  | "NotAuthorized" -> NotAuthorized
  | "Exempt" -> Exempt
  | "RequiresReview" -> RequiresReview
  | "RequiresNotification" -> RequiresNotification
  | "Prohibited" -> Prohibited
  | "Permitted" -> Permitted
  | s -> Custom s

let decision_outcome_to_yaml o = `String (decision_outcome_to_string o)

let decision_outcome_of_yaml = function
  | `String s -> Ok (decision_outcome_of_string s)
  | _ -> Error "Expected string for decision_outcome"

(** A leaf node in a decision tree *)
type decision_leaf = {
  outcome : decision_outcome;
  explanation : string;
  obligations : string list;
  references : string list;
}

let decision_leaf_to_yaml l =
  `O [
    ("outcome", decision_outcome_to_yaml l.outcome);
    ("explanation", `String l.explanation);
    ("obligations", `A (List.map (fun s -> `String s) l.obligations));
    ("references", `A (List.map (fun s -> `String s) l.references));
  ]

let decision_leaf_of_yaml = function
  | `O fields ->
    let get k = List.assoc_opt k fields in
    (match get "outcome", get "explanation" with
    | Some o, Some (`String explanation) ->
      (match decision_outcome_of_yaml o with
      | Ok outcome ->
        let obligations = match get "obligations" with
          | Some (`A items) ->
            List.filter_map (function `String s -> Some s | _ -> None) items
          | _ -> []
        in
        let references = match get "references" with
          | Some (`A items) ->
            List.filter_map (function `String s -> Some s | _ -> None) items
          | _ -> []
        in
        Ok { outcome; explanation; obligations; references }
      | Error e -> Error e)
    | _ -> Error "Missing required fields for decision_leaf")
  | _ -> Error "Expected object for decision_leaf"

(** A decision tree node - either a branch or a leaf *)
type decision_node =
  | Leaf of decision_leaf
  | Branch of {
      condition : condition_expr;
      if_true : decision_node;
      if_false : decision_node;
    }

let rec decision_node_to_yaml = function
  | Leaf l -> `O [("Leaf", decision_leaf_to_yaml l)]
  | Branch { condition; if_true; if_false } ->
    `O [("Branch", `O [
      ("condition", condition_expr_to_yaml condition);
      ("if_true", decision_node_to_yaml if_true);
      ("if_false", decision_node_to_yaml if_false);
    ])]

let rec decision_node_of_yaml = function
  | `O [("Leaf", v)] ->
    (match decision_leaf_of_yaml v with
    | Ok l -> Ok (Leaf l)
    | Error e -> Error e)
  | `O [("Branch", `O fields)] ->
    let get k = List.assoc_opt k fields in
    (match get "condition", get "if_true", get "if_false" with
    | Some cond, Some if_t, Some if_f ->
      (match condition_expr_of_yaml cond,
             decision_node_of_yaml if_t,
             decision_node_of_yaml if_f with
      | Ok condition, Ok if_true, Ok if_false ->
        Ok (Branch { condition; if_true; if_false })
      | Error e, _, _ | _, Error e, _ | _, _, Error e -> Error e)
    | _ -> Error "Missing required fields for Branch")
  | _ -> Error "Invalid decision_node"

(** Metadata about the rule *)
type rule_metadata = {
  version : string;
  author : string option;
  reviewed_by : string option;
  last_updated : string option;
  tags : string list;
}

let rule_metadata_to_yaml m =
  `O ([
    ("version", `String m.version);
    ("tags", `A (List.map (fun t -> `String t) m.tags));
  ] @ (match m.author with Some a -> [("author", `String a)] | None -> [])
  @ (match m.reviewed_by with Some r -> [("reviewed_by", `String r)] | None -> [])
  @ (match m.last_updated with Some l -> [("last_updated", `String l)] | None -> []))

let rule_metadata_of_yaml = function
  | `O fields ->
    let get k = List.assoc_opt k fields in
    (match get "version" with
    | Some (`String version) ->
      let author = match get "author" with Some (`String a) -> Some a | _ -> None in
      let reviewed_by = match get "reviewed_by" with Some (`String r) -> Some r | _ -> None in
      let last_updated = match get "last_updated" with Some (`String l) -> Some l | _ -> None in
      let tags = match get "tags" with
        | Some (`A items) ->
          List.filter_map (function `String s -> Some s | _ -> None) items
        | _ -> []
      in
      Ok { version; author; reviewed_by; last_updated; tags }
    | _ -> Error "Missing version in metadata")
  | _ -> Error "Expected object for rule_metadata"

(** A complete rule definition *)
type rule = {
  rule_id : rule_id;
  title : string;
  description : string;
  applies_if : condition_expr list;
  decision_tree : decision_node;
  source : source;
  effective_from : string option;  (** ISO 8601 date *)
  effective_to : string option;    (** ISO 8601 date *)
  metadata : rule_metadata option;
}

let rule_to_yaml r =
  `O ([
    ("rule_id", `String r.rule_id);
    ("title", `String r.title);
    ("description", `String r.description);
    ("applies_if", `A (List.map condition_expr_to_yaml r.applies_if));
    ("decision_tree", decision_node_to_yaml r.decision_tree);
    ("source", source_to_yaml r.source);
  ] @ (match r.effective_from with Some e -> [("effective_from", `String e)] | None -> [])
  @ (match r.effective_to with Some e -> [("effective_to", `String e)] | None -> [])
  @ (match r.metadata with Some m -> [("metadata", rule_metadata_to_yaml m)] | None -> []))

let rule_of_yaml = function
  | `O fields ->
    let get k = List.assoc_opt k fields in
    (match get "rule_id", get "title", get "description",
           get "applies_if", get "decision_tree", get "source" with
    | Some (`String rule_id), Some (`String title), Some (`String description),
      Some (`A applies_if_yaml), Some decision_tree_yaml, Some source_yaml ->
      let applies_if = List.filter_map (fun item ->
        match condition_expr_of_yaml item with Ok e -> Some e | Error _ -> None
      ) applies_if_yaml in
      (match decision_node_of_yaml decision_tree_yaml, source_of_yaml source_yaml with
      | Ok decision_tree, Ok source ->
        let effective_from = match get "effective_from" with
          | Some (`String e) -> Some e | _ -> None in
        let effective_to = match get "effective_to" with
          | Some (`String e) -> Some e | _ -> None in
        let metadata = match get "metadata" with
          | Some m -> (match rule_metadata_of_yaml m with Ok md -> Some md | _ -> None)
          | None -> None in
        Ok { rule_id; title; description; applies_if; decision_tree;
             source; effective_from; effective_to; metadata }
      | Error e, _ | _, Error e -> Error e)
    | _ -> Error "Missing required fields for rule")
  | _ -> Error "Expected object for rule"

(** A collection of related rules (a rule pack) *)
type rule_pack = {
  pack_id : string;
  name : string;
  description : string;
  rules : rule list;
  version : string;
}

let rule_pack_to_yaml p =
  `O [
    ("pack_id", `String p.pack_id);
    ("name", `String p.name);
    ("description", `String p.description);
    ("rules", `A (List.map rule_to_yaml p.rules));
    ("version", `String p.version);
  ]

let rule_pack_of_yaml = function
  | `O fields ->
    let get k = List.assoc_opt k fields in
    (match get "pack_id", get "name", get "description", get "rules", get "version" with
    | Some (`String pack_id), Some (`String name), Some (`String description),
      Some (`A rules_yaml), Some (`String version) ->
      let rules = List.filter_map (fun r ->
        match rule_of_yaml r with Ok rule -> Some rule | Error _ -> None
      ) rules_yaml in
      Ok { pack_id; name; description; rules; version }
    | _ -> Error "Missing required fields for rule_pack")
  | _ -> Error "Expected object for rule_pack"

(** Load a rule from YAML string *)
let rule_of_yaml_string (yaml_str : string) : (rule, string) result =
  match Yaml.of_string yaml_str with
  | Ok yaml -> rule_of_yaml yaml
  | Error (`Msg msg) -> Error msg

(** Serialize a rule to YAML string *)
let rule_to_yaml_string (r : rule) : (string, string) result =
  let yaml = rule_to_yaml r in
  match Yaml.to_string yaml with
  | Ok s -> Ok s
  | Error (`Msg msg) -> Error msg

(** Load a rule pack from YAML string *)
let rule_pack_of_yaml_string (yaml_str : string) : (rule_pack, string) result =
  match Yaml.of_string yaml_str with
  | Ok yaml -> rule_pack_of_yaml yaml
  | Error (`Msg msg) -> Error msg

(** Helper to create a simple field check condition *)
let field_equals field value =
  FieldCheck { field; op = Eq; value = StringVal value }

let field_in field values =
  FieldCheck { field; op = In; value = ListVal values }

let field_greater_than field value =
  FieldCheck { field; op = Gt; value = FloatVal value }

(** Helper to create decision leaves *)
let make_leaf ~outcome ~explanation ?(obligations=[]) ?(references=[]) () =
  Leaf { outcome; explanation; obligations; references }

(** Helper to create branch nodes *)
let make_branch ~condition ~if_true ~if_false =
  Branch { condition; if_true; if_false }

(** Helper to create a source reference *)
let make_source ~document_id ~article ?(paragraphs=[]) ?(pages=[]) ?url () =
  { document_id; article; paragraphs; pages; url }

(** Helper to create a complete rule *)
let make_rule ~rule_id ~title ~description ~applies_if ~decision_tree
    ~source ?effective_from ?effective_to ?metadata () =
  { rule_id; title; description; applies_if; decision_tree;
    source; effective_from; effective_to; metadata }
