---
name: stacks-sdk-api
description: "@stacks/transactions and @stacks/network v7+ API surface — key function name changes"
type: reference
---

# @stacks SDK API Surface (v7+)

## Rules

**`@stacks/network`**: Does NOT export `StacksMainnet` class. Use `STACKS_MAINNET` constant instead.
- Wrong: `const { StacksMainnet } = require('@stacks/network'); new StacksMainnet()`
- Right: `const { STACKS_MAINNET } = require('@stacks/network');` then pass `STACKS_MAINNET` directly

**`@stacks/transactions`**: Read-only contract calls use `fetchCallReadOnlyFunction`, not `callReadOnlyFunction`.
- Function: `fetchCallReadOnlyFunction({ contractAddress, contractName, functionName, functionArgs, senderAddress, network: "mainnet" })`
- Returns a Clarity value object with `.type` (use `ClarityType.OptionalSome`, `ClarityType.OptionalNone`, etc.)
- For uint result: `result.value` is a BigInt

## Why

Wasted debugging time on `undefined is not a constructor` and `callReadOnlyFunction is not a function` errors during stx-stack-delegate skill build (2026-04-10). Both issues came from assuming the DCA skill's dynamic imports worked the same way.

## How to apply

Every time you write `@stacks/network` or `@stacks/transactions` contract call code in a skill, check: use `STACKS_MAINNET` not `new StacksMainnet()`, and `fetchCallReadOnlyFunction` not `callReadOnlyFunction`.
