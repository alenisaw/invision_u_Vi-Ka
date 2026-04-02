# Frontend Style Guide

## Document Structure

- [Purpose](#purpose)
- [Typography](#typography)
- [Color System](#color-system)
- [Layout Principles](#layout-principles)
- [Interaction Patterns](#interaction-patterns)

## Purpose

This guide describes the visual system that is currently implemented in `frontend/src/app` and `frontend/src/components`. It is no longer a detached prototype reference: the live UI already follows these tokens and patterns.

## Typography

- primary font family: `Raleway`, Arial, sans-serif
- display weight: `800`
- interface weight: `600-800`
- body weight: `500`
- numbers use tabular lining numerals
- section labels use uppercase tracking via the shared `.eyebrow` token
- large headings keep slightly compressed letter spacing

## Color System

Core tokens come from `frontend/src/app/globals.css`.

Primary brand colors:

- `brand-ink`: primary text and dark surfaces
- `brand-paper`: light surface and contrast text on dark cards
- `brand-lime`: primary success / shortlist accent
- `brand-blue`: informational and reviewer-action accent
- `brand-coral`: warning / caution accent
- `brand-purple`: reserved secondary accent

Surface and UI tokens:

- `surface-soft`, `surface-strong`, `surface-hover`
- `surface-subtle`, `surface-subtle-2`
- `brand-line`
- `badge-*`
- `danger-soft-*`

The UI supports both light and dark themes through `next-themes` with mirrored token sets under `html[data-theme="dark"]`.

## Layout Principles

- the root workspace uses a reviewer-oriented shell: header + sidebar + wide main content area
- `container-app` keeps dense data views readable on wide screens and collapses padding on mobile
- cards are rounded, glassy, and slightly elevated to separate analytical blocks
- detail pages split primary evidence and secondary controls into two columns on large screens
- comparison screens prioritize scanability: radar first, then summary cards, then score tables

## Interaction Patterns

- buttons, chips, and cards use short translate / color transitions rather than heavy motion
- state is communicated through badges, helper text, and progress blocks
- reviewer actions stay in-context: override and audit history live on the candidate detail page
- dashboard and candidates pages support compare flows directly from list selection
- form and JSON submission paths share the same visual pipeline progress treatment

Projet Documentation
