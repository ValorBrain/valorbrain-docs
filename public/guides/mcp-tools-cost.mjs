#!/usr/bin/env node
// What do an MCP server's tool definitions cost before the first question?
//   HTTP:  MCP_URL=https://host/mcp [MCP_TOKEN=...] node mcp-tools-cost.mjs
//   stdio: node mcp-tools-cost.mjs -- npx -y @modelcontextprotocol/server-memory
// Prints tool count, size of the definitions and of the server instructions.
// SHOW_INSTRUCTIONS=1 also prints the instructions text, to see what sits near the start.
// Tokens are estimated as characters / 4. Say so when you quote the number.
import { spawn } from "node:child_process";
import { createInterface } from "node:readline";

const dash = process.argv.indexOf("--");
const cmd = dash > 0 ? process.argv.slice(dash + 1) : null;
const url = process.env.MCP_URL;
const token = process.env.MCP_TOKEN;
if (!cmd && !url) {
  console.error("usage: MCP_URL=... [MCP_TOKEN=...] mcp-tools-cost.mjs   |   mcp-tools-cost.mjs -- <stdio command>");
  process.exit(2);
}

let id = 1;
let rpc;
let close = () => {};
if (cmd) {
  const child = spawn(cmd[0], cmd.slice(1), { stdio: ["pipe", "pipe", "ignore"] });
  const waiting = new Map();
  createInterface({ input: child.stdout }).on("line", (line) => {
    let msg;
    try { msg = JSON.parse(line); } catch { return; }
    const w = waiting.get(msg.id);
    if (!w) return;
    waiting.delete(msg.id);
    msg.error ? w.reject(new Error(msg.error.message)) : w.resolve(msg.result);
  });
  rpc = (method, params, notify = false) => {
    const body = { jsonrpc: "2.0", method, params, ...(notify ? {} : { id: id++ }) };
    child.stdin.write(JSON.stringify(body) + "\n");
    if (notify) return Promise.resolve(null);
    return new Promise((resolve, reject) => waiting.set(body.id, { resolve, reject }));
  };
  close = () => child.kill();
} else {
  let sid = null;
  rpc = async (method, params, notify = false) => {
    const headers = { "Content-Type": "application/json", Accept: "application/json, text/event-stream" };
    if (token) headers.Authorization = `Bearer ${token}`;
    if (sid) headers["Mcp-Session-Id"] = sid;
    const body = { jsonrpc: "2.0", method, params, ...(notify ? {} : { id: id++ }) };
    const res = await fetch(url, { method: "POST", headers, body: JSON.stringify(body) });
    sid = res.headers.get("mcp-session-id") || sid;
    if (notify) return null;
    const text = await res.text();
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${text.slice(0, 200)}`);
    const data = text.split(/\r?\n/).filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trim());
    const msg = JSON.parse(data.length ? data[data.length - 1] : text);
    if (msg.error) throw new Error(`MCP error ${msg.error.code}: ${msg.error.message}`);
    return msg.result;
  };
}

const init = await rpc("initialize", {
  protocolVersion: "2025-06-18",
  capabilities: {},
  clientInfo: { name: "mcp-tools-cost", version: "0.1" },
});
await rpc("notifications/initialized", {}, true);
let tools = [];
let cursor;
do {
  const r = await rpc("tools/list", cursor ? { cursor } : {});
  tools = tools.concat(r.tools);
  cursor = r.nextCursor;
} while (cursor);
close();

// What a client forwards to the model for each tool: name, description, input schema.
const size = (t) => JSON.stringify({ name: t.name, description: t.description, input_schema: t.inputSchema }).length;
const rows = tools.map((t) => ({ name: t.name, chars: size(t) })).sort((a, b) => b.chars - a.chars);
const total = rows.reduce((s, r) => s + r.chars, 0);
const names = tools.reduce((s, t) => s + t.name.length + 1, 0);
const instr = (init.instructions || "").length;
const tok = (n) => Math.round(n / 4);
console.log(`${init.serverInfo?.name} ${init.serverInfo?.version ?? ""}`.trim());
console.log(`tools:               ${rows.length}`);
console.log(`definitions:         ${total} chars ≈ ${tok(total)} tokens`);
console.log(`names only:          ${names} chars ≈ ${tok(names)} tokens`);
console.log(`server instructions: ${instr} chars ≈ ${tok(instr)} tokens`);
console.log(`largest five:`);
for (const r of rows.slice(0, 5)) console.log(`  ${r.name.padEnd(30)} ${String(r.chars).padStart(6)} chars ≈ ${tok(r.chars)} tokens`);
if (process.env.SHOW_INSTRUCTIONS) console.log(`\n--- server instructions ---\n${init.instructions || "(none)"}`);
