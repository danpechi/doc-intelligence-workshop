// Helpers for the supported ai_query structured-output syntax.
//
// The old DDL-string responseFormat (schema_of_json of a multi-field example) is rejected on
// the current DBSQL channel (AI_FUNCTION_UNSUPPORTED_RESPONSE_FORMAT.DDL_STRING). The supported
// form is a json_schema string, which returns a JSON STRING — so we wrap ai_query in
// from_json(...) with a matching DDL to recover a typed STRUCT (keeping `extracted.field`
// access, numeric ORDER BY/AVG, and @dlt.expect constraints working unchanged).
//
// These helpers turn the example-JSON that the workshop already uses (e.g.
// '{"apr_low":0.0,"note":"string","ok":false,"n":0}') into the two derived strings.

type Example = Record<string, unknown>;

function ddlType(v: unknown): string {
  if (typeof v === "boolean") return "BOOLEAN";
  if (typeof v === "number") return Number.isInteger(v) ? "BIGINT" : "DOUBLE";
  return "STRING";
}

function jsonSchemaType(v: unknown): { type: string } {
  if (typeof v === "boolean") return { type: "boolean" };
  if (typeof v === "number") return { type: Number.isInteger(v) ? "integer" : "number" };
  return { type: "string" };
}

/** JSON-schema responseFormat string for ai_query, derived from an example-JSON string. */
export function responseFormat(exampleJson: string): string {
  const ex = JSON.parse(exampleJson) as Example;
  const properties: Record<string, { type: string }> = {};
  for (const [k, v] of Object.entries(ex)) properties[k] = jsonSchemaType(v);
  return JSON.stringify({
    type: "json_schema",
    json_schema: { name: "response", schema: { type: "object", properties } },
  });
}

/** from_json DDL string matching the same example-JSON. */
export function ddl(exampleJson: string): string {
  const ex = JSON.parse(exampleJson) as Example;
  return Object.entries(ex)
    .map(([k, v]) => `${k} ${ddlType(v)}`)
    .join(", ");
}

/**
 * Full structured-extraction snippet: from_json(ai_query(model, prompt, responseFormat => '...'), 'ddl').
 * `prompt` is a raw SQL expression (already quoted/CONCAT'd by the caller).
 */
export function structuredExtract(model: string, promptExpr: string, exampleJson: string): string {
  return `from_json(ai_query(
        '${model}',
        ${promptExpr},
        responseFormat => '${responseFormat(exampleJson)}'
    ), '${ddl(exampleJson)}')`;
}
