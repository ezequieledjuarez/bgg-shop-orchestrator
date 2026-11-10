# Feature Specification: Buyer-Facing Store Chatbot

**Feature Branch**: `013-add-chatbot`
**Created**: 2026-11-06
**Status**: Runtime implementation complete; local acceptance is owner-reported
as passed on 2026-11-10. The new run's commands/results are not recorded:
SC-001 and SC-007 remain unexecuted in the repository evidence, and live
OpenRouter authentication remains untested. See [tasks.md](tasks.md) and
[quickstart.md](quickstart.md) for the recorded evidence and limitations.
**Input**: Approved CU-C07 decisions for an in-application buyer FAQ and product-help chatbot.

## Clarifications

### Session 2026-11-06

- Q: How should the chatbot handle a message mixing public store help with personal, account, order, or transactional content? → A: Do not process or persist any part of the mixed message; ask the buyer to submit the shop-related question separately.
- Q: What should the chatbot do when the topic guard cannot determine whether a message is about the shop? → A: Ask for a shop-related clarification without persisting or sending the unclassified message to Core or calling retrieval, a model, or a tool; politely refuse if the clarification remains out of scope or unclear.
- Q: How long should the anonymous `chat_session` cookie last? → A: Use a non-persistent browser-session cookie; conversation retention remains independent and expires after 30 days of inactivity.
- Q: What sample size and pass threshold apply to the buyer usability validation? → A: Test with 10 representative buyers; at least 9 must complete the task and identify the answer's sourced, uncertain, or unavailable status without assistance.
- Q: What minimum evaluation set should measure FAQ grounding and fallback behavior? → A: Use 20 fixed cases—10 answerable from approved sources and 10 without sufficient evidence—with at least 19 correct grounded-answer or fallback outcomes and zero unsupported factual claims.

### Session 2026-11-07

- Q: Which chatbot paths should support English and Spanish, and what language should assistant replies use? → A: Support both languages across FAQ, guardrail, and catalog-recommendation paths, and return user-facing assistant text in the language of the submitted question. Preserve all existing scope, privacy, ownership, grounding, and no-fabrication safeguards; add no other language choices.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Get grounded store help (Priority: P1)

A visitor or registered buyer opens the chatbot in the store and asks about store FAQs, policies, or other approved public store information. The buyer receives a concise answer supported by approved sources, or a clear fallback when the information is unavailable. Requests outside the store-help scope are politely refused without invoking retrieval, a model, or a tool.

**Why this priority**: Answering trustworthy store questions is the core purpose of CU-C07, and the scope boundary must be applied consistently to every chatbot request.

**Independent Test**: From the store UI, submit an in-scope question whose answer exists in approved knowledge, one with no supporting content, and an out-of-scope question. Verify grounded response, explicit fallback, and refusal respectively; verify the refusal occurs before retrieval/model/tool calls.

**Acceptance Scenarios**:

1. **Given** a buyer opens the chatbot before sending a message, **When** the interface is displayed, **Then** it presents an understandable empty state and accessible message controls that can be used by keyboard and assistive technology.
2. **Given** an in-scope question supported by approved store knowledge, **When** the buyer submits it, **Then** the chatbot returns an answer grounded only in that knowledge and includes a source link or title when available.
3. **Given** no approved content sufficiently supports an answer, **When** the buyer asks the question, **Then** the chatbot says it cannot answer with confidence and offers an appropriate next step instead of guessing.
4. **Given** an out-of-scope question, **When** it is submitted, **Then** the BFF politely refuses it before any retrieval, model, or tool invocation.
5. **Given** a request for personal, account, order, or transactional help, **When** the buyer submits it, **Then** the BFF does not forward or persist that sensitive content, does not retrieve or reveal protected information, and directs the buyer to the existing authenticated flow when applicable.
6. **Given** a response is being generated or a required service is unavailable, **When** the buyer views the conversation, **Then** the interface communicates loading or an accessible error state, preserves an understandable recovery path, and does not display a fabricated answer.

### User Story 2 - Find products using current catalog information (Priority: P2)

A buyer asks for product recommendations in natural language and receives suggestions based on current product data returned by the existing catalog capabilities in Core through the BFF.

**Why this priority**: Product discovery is a distinct chatbot benefit, but recommendations must reflect the live catalog rather than a stale copy of catalog data in the knowledge corpus.

**Independent Test**: Ask for a recommendation matching catalog-supported criteria and verify each returned product fact against the current Core result. Ask for a criterion the catalog cannot represent and verify the chatbot requests clarification or explains the limitation rather than silently changing the request.

**Acceptance Scenarios**:

1. **Given** a shop-related recommendation request that can be represented by existing catalog capabilities, **When** the buyer submits it, **Then** the BFF obtains current results from Core and the response contains only products and attributes returned by Core.
2. **Given** Core returns current product details, **When** the chatbot summarizes a recommendation, **Then** it does not invent or infer a product, price, stock status, category, or link that Core did not return.
3. **Given** the request includes a preference that existing catalog capabilities cannot faithfully express, **When** recommendations are prepared, **Then** the chatbot asks a clarifying question or explains the supported limitation instead of claiming the preference was applied.
4. **Given** the catalog returns no matching products or is unavailable, **When** the buyer asks for recommendations, **Then** the chatbot reports no supported result or a recoverable failure without substituting fabricated or stale catalog facts.

### User Story 3 - Continue a private conversation (Priority: P3)

A buyer can continue a chatbot conversation within the same authorized user or anonymous browser-session scope. Conversation content is kept separately from store knowledge and deleted after the approved 30-day retention period.

**Why this priority**: Conversation continuity improves follow-up questions while requiring clear ownership, a bounded retention period, and separation from the curated knowledge corpus.

**Independent Test**: Create conversations for two different owners, continue one conversation under its valid scope, attempt access from the other scope, and verify isolation. Verify conversation records expire after 30 days of inactivity while approved ChromaDB knowledge remains unaffected.

**Acceptance Scenarios**:

1. **Given** a registered buyer or a visitor with a valid anonymous browser session, **When** they continue their own conversation, **Then** the chatbot uses only that conversation's permitted context.
2. **Given** a user or session requests another owner's conversation, **When** access is attempted, **Then** access is denied without returning its messages or metadata.
3. **Given** a conversation has had no activity for 30 days, **When** its retention period expires, **Then** its stored conversation data is deleted.
4. **Given** a conversation is deleted under its retention policy, **When** store knowledge is queried, **Then** the approved ChromaDB knowledge corpus remains independent and is not deleted or re-ingested as a side effect.

### Edge Cases

- The topic guard cannot establish that a message is about the shop; ask for a shop-related clarification without persisting or sending the unclassified message to Core or calling retrieval, a model, or a tool, and politely refuse if the clarification remains out of scope or unclear.
- A message is blank, exceeds an established input limit, or arrives at a rate above the established limit; reject it before processing and show a clear, accessible explanation.
- A user asks a mixed in-scope/out-of-scope question; do not process or persist any part of the message, and ask the user to submit the shop-related question separately.
- Approved knowledge is absent, stale, withdrawn, or conflicts with another approved source; do not make an unsupported claim and use the explicit fallback until the content is reviewed.
- Core returns incomplete, unsupported, or contradictory catalog data; present only faithfully supported details or ask for clarification.
- A model, retrieval source, or catalog capability times out or returns an error; do not treat the failure as evidence and provide a clear retry or alternative path.
- Two buyers or anonymous sessions use the chatbot concurrently; conversation history and responses remain scoped to the correct owner.
- Conversation expiration coincides with a new message or continuation attempt; do not expose expired content or report it as retained.
- A user includes personal or order details in a message; do not forward them to retrieval, a model, Core, or another tool, persist them in conversation history, or repeat them in a response.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The buyer-facing application MUST provide an accessible chatbot interaction for visitors and registered buyers, including an initial empty state, clear loading and error states, keyboard-operable controls, and status/response updates available to assistive technology.
- **FR-002**: The BFF MUST apply a shop-topic guardrail to each submitted message before any retrieval, model, or tool call. Out-of-scope requests MUST receive a polite refusal. If the guard cannot determine whether a message is about the shop, the BFF MUST request a shop-related clarification without persisting the unclassified message, sending it to Core, or calling retrieval, a model, or a tool, and MUST politely refuse if the clarification remains out of scope or unclear. This boundary MUST be enforced by application behavior and MUST NOT depend only on a prompt.
- **FR-003**: The FAQ and store-policy answer path MUST use LangChain and retrieve only from ChromaDB knowledge consisting of approved, relatively stable FAQs, policies, and allowed public store content. Responses MUST be grounded in retrieved approved content, identify a source when one is available, and use an explicit uncertainty/fallback response when evidence is insufficient.
- **FR-004**: The knowledge corpus MUST be populated and updated only from approved knowledge content. Dynamic product catalog results returned by Core MUST NOT be ingested into ChromaDB or re-ingested as a consequence of answering a catalog question.
- **FR-005**: For product recommendations, the BFF MUST use existing product/catalog capabilities in Core and MUST NOT allow direct browser-to-Core access for chatbot requests. The chatbot MUST claim only product facts returned by Core; when requested criteria cannot be faithfully represented by existing catalog capabilities, it MUST ask for clarification or explain the limitation.
- **FR-006**: Chatbot capabilities MUST be limited to the approved read-only FAQ retrieval and existing catalog lookup needed for CU-C07. The LLM MUST NOT mutate orders, accounts, or catalog data, access personal or order data, or invoke arbitrary tools. When a buyer submits personal, account, or order details or requests help requiring them, the BFF MUST keep that content out of retrieval, model, Core, other tools, and persisted conversation history; it MUST NOT echo or disclose protected data and MUST direct the buyer to existing authenticated flows where applicable. When a message mixes supported public store help with personal, account, order, or transactional content, the BFF MUST NOT process or persist any part of the message and MUST ask the buyer to submit the shop-related question separately.
- **FR-007**: Conversations MUST be persisted in PostgreSQL, separately from ChromaDB and its knowledge lifecycle. Conversation access MUST be bound to the authenticated user or the same valid anonymous browser session; an owner identifier alone MUST NOT grant access to another person's conversation. The anonymous `chat_session` cookie MUST be non-persistent and expire with the browser session; its lifetime MUST NOT extend the conversation's 30-day inactivity retention period.
- **FR-008**: Conversation content and metadata MUST be deleted after 30 days of inactivity. Conversation retention/deletion MUST NOT delete, modify, or trigger re-ingestion of the separate ChromaDB knowledge corpus.
- **FR-009**: The chatbot MUST validate message input and enforce the approved limits of 2,000 characters per message, 10 previous conversation turns, and 10 message requests per minute per user or anonymous browser session. Blank or over-limit submissions MUST be rejected before retrieval, model, or catalog calls with an accessible explanation.
- **FR-010**: Failures, unsupported filters, and insufficient evidence MUST produce deterministic, user-understandable fallback behavior. The chatbot MUST NOT fabricate products, prices, stock, categories, links, policies, or other factual claims.
- **FR-011**: Feature verification MUST be local-only and use isolated test data or local substitutes for external dependencies. Remote deployment, remote-environment validation, production/staging checks, and use of real personal or order data are outside this feature's verification scope.
- **FR-012**: The chatbot MUST accept English- and Spanish-language questions on FAQ, guardrail, and catalog-recommendation paths, and MUST present all user-facing assistant text in the language of the submitted question. This includes grounded FAQ answers, catalog recommendations, refusals, clarifications, and insufficient-evidence or unavailable fallbacks. This requirement MUST NOT introduce additional language choices or weaken any shop-scope, privacy, ownership, approved-source, grounding, catalog-fact, or no-fabrication safeguard.

### Key Entities

- **Chat conversation**: A buyer's bounded conversation record and ownership scope, stored separately from the approved store-knowledge corpus and subject to 30 days of inactivity retention.
- **Conversation message**: A buyer submission or chatbot response associated with one conversation and used only within its authorized context.
- **Approved knowledge item**: A reviewed FAQ, policy, or allowed public store-content item that may be used for grounded FAQ answers in ChromaDB.
- **Live catalog result**: Current product information returned by Core through the BFF for one recommendation request; it is transient chatbot context and is not part of the ChromaDB corpus.
- **Chat response**: A grounded answer, catalog-backed recommendation, clarification, refusal, or fallback shown to the buyer.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In a fixed set of 20 FAQ cases—10 answerable from approved sources and 10 without sufficient evidence—at least 19 receive the expected grounded answer or explicit uncertainty/fallback response, with zero unsupported factual claims.
- **SC-002**: In all tested product-recommendation responses, 100% of product names and stated catalog facts are present in the corresponding current Core results; unsupported criteria lead to clarification or an explicit limitation.
- **SC-003**: In all tested out-of-scope requests, 100% are refused before any retrieval, model, or tool invocation.
- **SC-004**: In all tested cross-user and cross-session access attempts, zero conversation content or metadata is disclosed.
- **SC-005**: All test conversations are deleted after 30 days of inactivity, and deletion of a conversation does not remove or re-ingest approved knowledge.
- **SC-006**: Buyers can complete the basic ask-and-read flow using keyboard-only navigation, and the empty, loading, error, and response states are conveyed to assistive technology.
- **SC-007**: In usability validation with 10 representative buyers, at least 9 can submit an FAQ question and identify whether the answer is sourced, uncertain, or unavailable without assistance.
- **SC-008**: In a fixed set of 10 cases—one English and one Spanish case for each of grounded FAQ answer, guardrail refusal, guardrail clarification, insufficient-evidence or unavailable fallback, and catalog recommendation—all 10 user-facing assistant responses use the language of the submitted question. The FAQ cases remain grounded in approved sources, catalog facts remain present in current Core results, and existing privacy and guardrail assertions continue to pass.

## Assumptions

- Visitors and registered buyers may use the chatbot without granting it access to an account, order, or other personal data.
- The existing BFF can mediate both chatbot requests and existing catalog capabilities in Core; no new direct browser-to-Core route is introduced.
- Content owners can identify and approve store FAQs, policies, and allowed public content before it enters the knowledge corpus.
- The 30-day retention period is measured from the most recent conversation activity; after that inactivity period, conversation content and associated metadata are deleted.
- Anonymous conversation continuity is limited to the same valid browser session; cross-device continuity is not promised for visitors.
- The anonymous `chat_session` cookie is non-persistent and expires with the browser session; database conversation retention remains independent.
- Accessibility is evaluated against WCAG 2.2 AA as a reasonable baseline, without prescribing a UI technology.
- Staff accounts receive no elevated chatbot capability: the chatbot exposes only public approved knowledge and current public catalog reads, with no administrative, account, or order access.

## Out of Scope

- Direct browser-to-Core access, arbitrary agent tools, and chatbot-triggered changes to orders, accounts, catalog, or other transactional data.
- Retrieval, disclosure, or processing of personal, account, payment, or order-specific information.
- Ingesting dynamic catalog results into ChromaDB or treating vectorized catalog data as the source of current product facts.
- Runtime behavior implementation before the BFF and Core contracts are structurally validated. The canonical contracts and provider settings are defined in the Feature 013 planning/contract gate.
- Remote deployment, remote-environment validation, production/staging checks, and validation using real personal or order data.
- Multi-agent orchestration; LangGraph is not required for this feature.

## Contract-First Gate

The canonical BFF REST and Core GraphQL conversation contracts were structurally validated before user-story source behavior was implemented. Contract structure validation does not establish runtime conformance; runtime schema conformance remains pending until implementation exists. The approved anonymous BFF-to-Core assertion mechanism and verification boundary are documented in the Feature 013 plan and are no longer an open product decision.
