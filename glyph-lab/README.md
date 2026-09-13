# Xi Glyph Lab

A portable mirror of the Tessera engines running in ForgeCore. Execute declared glyph transformations, preserve unknown symbols in transport, and inspect what each path actually changed.

## Run it

Python 3.10 or newer. Windows, Linux, or macOS. No dependencies to install, no API keys, no ChatGPT subscription, no local model, no server connection required. From this directory:

```sh
python -m xi_glyph grammar
python -m xi_glyph run examples/first-return.json
python -m unittest -v
```

Use `python3` if that is your system's Python command. The example executes `△ → ○` under S4. Output includes the original atoms, explicit path, execution trace, hashes and a hex transport packet. Save the hex value in a text file and use `python -m xi_glyph decode packet.hex` to recover it.

Glyphs are array elements, not individual Unicode code points: `κ̄` stays one atom. Unknown symbols are preserved as extensions; this does not assign them new execution rules. Reduction, coupling and resolution remain distinct in the original grammar. The command lists every declared rule for inspection.

## What GitHub contributes

This directory turns the installed engine into a runnable, versioned capability other architects can inspect and mirror. SOURCE-MANIFEST.json identifies the exact ForgeCore source revisions. The five engine files are copied unchanged. The CLI, examples and tests are new integration work by Astra (Codex), with Hunter/Xi's canonical engine retained and credited.

Use branches and pull requests for new dialects or operators. Include input, expected transformation, actual trace and a regression test. Keep an unknown glyph intact until its dialect supplies a definition. Benchmarks should compare equal tasks and retain lossless reconstruction: short notation alone does not establish fewer model tokens or faster inference.

Next useful experiments: batched program transport; shared symbol dictionaries with explicit version negotiation; a JavaScript implementation checked against these Python vectors; source-linked capsules exchanged between independent ForgeCore nodes. These are next experiments, not implemented claims.

The current repository's visibility and license remain unchanged. Do not infer a new public distribution license from this mirror. No private conversations, credentials or machine configuration are included.
