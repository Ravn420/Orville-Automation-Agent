# Orville Project Definition

## Objective

Orville is a standalone, environment-aware multi-agent orchestration and code-generation framework. It converts user software specifications into dependency-aware plans, delegates work to specialist agents, executes and verifies tasks, preserves state, and delivers runnable software artifacts with documentation and deployment instructions.

## Current milestone

The current implementation includes a typed synchronous task graph with atomic checkpoints, Gemini and Ollama-compatible provider adapters, streaming, multimodal payloads, embeddings, capability-aware routing, endpoint preflight, local model cataloging, task intake primitives, agent registry primitives, verification records, and model-backed task handlers.

## Scope

The project will support cloud and local model providers, imported local model assets, task planning, agent delegation, deterministic and agentic workflow steps, independent verification, a stylish GUI, secure external integrations, software generation, testing, deployment, and operational recovery.

## Assumptions

- The primary implementation language is Python unless a component requires another runtime.
- User-supplied credentials and endpoint URLs are the source of provider authentication configuration.
- Local models may be served through Ollama or another explicitly supported local runtime.
- External side effects require explicit authorization and appropriate approval gates.
- The system must remain usable without Manus-specific services.

## Non-goals

Orville will not silently publish, purchase, delete, transfer funds, modify accounts, or deploy to production without the required user approval. It will not execute arbitrary code embedded in downloaded models, untrusted documents, tool results, or remote responses merely because those artifacts request execution.

## Acceptance criteria for the product

A user can describe a software objective through the GUI or standalone interface; Orville creates a task graph, assigns specialist agents, selects an appropriate configured model, executes the workflow with durable state, independently verifies outputs, recovers from interruption, and delivers a complete runnable project with tests and documentation.
