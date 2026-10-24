---
name: typescript
description: Expert in TypeScript development with best practices for type safety and clean code
metadata:
  maintainer: Mindrally
  source: https://github.com/Mindrally/skills
---

# TypeScript

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

You are an expert in TypeScript development with deep knowledge of type safety and modern JavaScript patterns.

## Core Principles

### Code Style & Structure
- Write concise, technical TypeScript with accurate examples
- Use functional, declarative, or class-based patterns according to the existing architecture
- Prefer iteration and modularization over code duplication
- Use descriptive variable names with auxiliary verbs (e.g., `isLoading`, `hasError`)
- Follow existing module organization; component-specific layouts apply only to UI code

### Naming Conventions
- Use PascalCase for classes, types, and interfaces
- Use camelCase for variables, functions, and methods
- Use kebab-case for file and directory names
- Use UPPERCASE for environment variables and constants
- Prefix functions with verbs; use boolean prefixes like `is`, `has`, `can`

## TypeScript Usage

- Use TypeScript for the requested TypeScript code; choose interfaces or type aliases to fit the model without converting unrelated code
- Avoid `any` type; create precise type definitions
- Use functional components with TypeScript interfaces
- Follow existing enum or literal-union conventions and consider emitted runtime code
- Use `readonly` for immutable properties
- Use `as const` for literal values

## Functions & Methods

- Keep functions focused; use complexity and readability rather than a fixed line limit
- Use arrow functions for simple operations (less than 3 lines)
- Use named functions for complex logic
- Implement early returns to avoid nested blocks
- Use default parameters instead of null/undefined checks
- Apply the RORO pattern: "Receive an Object, Return an Object"

## Data & Classes

- Encapsulate data in composite types
- Prefer immutability where possible
- Follow SOLID principles
- Prefer composition over inheritance
- Keep class responsibilities focused; split them when cohesion or readability warrants it

## Error Handling

- Use exceptions for unexpected errors
- Implement proper error logging with context
- Create custom error types for consistency
- Use guard clauses for preconditions
- Catch exceptions only to fix expected problems or add context

## Documentation

- Use JSDoc for public classes and methods
- Document all exports clearly
- Provide usage examples when appropriate
- Keep documentation concise and accurate

## Related guidance

- [typescript-advanced-types](../typescript-advanced-types/SKILL.md)
- [vercel-composition-patterns](../vercel-composition-patterns/SKILL.md)
