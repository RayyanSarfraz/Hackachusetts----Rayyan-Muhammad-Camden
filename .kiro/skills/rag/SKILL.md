---
name: rag
description: Implements document chunking, embedding generation, vector storage, and retrieval pipelines for Retrieval-Augmented Generation systems. Use when building RAG applications, creating document Q&A systems, or integrating AI with knowledge bases.
---

# RAG Implementation

## Using this skill

Read the [shared guide](../../AGENTS.md). Use this guidance only when its technical domain fits the task. Follow the target project's installed versions, architecture, and conventions; example tools, paths, and dependencies are options rather than required changes.

Build Retrieval-Augmented Generation systems that extend AI capabilities with external knowledge sources.

## Overview

This skill covers: document processing, embedding generation, vector storage, retrieval configuration, and RAG pipeline implementation.

## When to Use

- Building Q&A systems over proprietary documents
- Creating chatbots with factual information from knowledge bases
- Implementing semantic search with natural language queries
- Reducing hallucinations with grounded, sourced responses
- Building documentation assistants and research tools
- Enabling AI systems to access domain-specific knowledge

## Instructions

### Step 1: Choose storage

Inspect existing search/storage capabilities before adding a vector database. Compare persistence, filtering, tenant isolation, scale, operations, and cost. PostgreSQL with a suitable vector extension may fit an existing database; a separate service is optional.

### Step 2: Select embeddings

Evaluate models against the actual language, domain, quality, latency, context, cost, and privacy requirements. Record model revision, embedding dimensions, normalization, and indexing strategy. Avoid treating example model rankings as current recommendations.

### Step 3: Implement Document Processing Pipeline

1. Load documents from source (file system, database, API)
2. Clean and preprocess (remove formatting, normalize text)
3. Split documents into chunks with appropriate strategy
4. Generate embeddings for each chunk
5. Store embeddings in vector database with metadata

**Validation**: Verify embeddings were generated successfully:
```java
List<Embedding> embeddings = embeddingModel.embedAll(segments);
if (embeddings.isEmpty() || embeddings.get(0).dimension() != expectedDim) {
    throw new IllegalStateException("Embedding generation failed");
}
```

### Step 4: Configure Retrieval Strategy

Choose the appropriate strategy:

- **Dense Retrieval**: Semantic similarity via embeddings (default for most cases)
- **Hybrid Search**: Dense + sparse retrieval for better coverage
- **Metadata Filtering**: Filter by document attributes
- **Reranking**: Cross-encoder reranking for high-precision requirements

### Step 5: Build RAG Pipeline

1. Create content retriever with your embedding store
2. Configure AI service with retriever and chat memory
3. Implement prompt template with context injection
4. Add response validation and grounding checks

**Validation**: Test with known queries to verify context injection works correctly.

**Error Handling**: For batch ingestion, wrap in retry logic:
```java
for (Document doc : documents) {
    int attempts = 0;
    while (attempts < 3) {
        try {
            store.add(embeddingModel.embed(doc).content(), doc.toTextSegment());
            break;
        } catch (EmbeddingException e) {
            attempts++;
            if (attempts == 3) throw new RuntimeException("Failed after 3 retries", e);
        }
    }
}
```

### Step 6: Evaluate and Optimize

1. Measure retrieval metrics: precision@k, recall@k, MRR
2. Evaluate answer quality: faithfulness, relevance
3. Monitor performance and user feedback
4. Iterate on chunking, retrieval, and prompt parameters

## Examples

The Java examples below illustrate LangChain4j. Use equivalent APIs in the selected language/framework; adopting Java is not required.

### Example 1: Basic Document Q&A

```java
List<Document> documents = FileSystemDocumentLoader.loadDocuments("/docs");

InMemoryEmbeddingStore<TextSegment> store = new InMemoryEmbeddingStore<>();
EmbeddingStoreIngestor.ingest(documents, store);

DocumentAssistant assistant = AiServices.builder(DocumentAssistant.class)
    .chatModel(chatModel)
    .contentRetriever(EmbeddingStoreContentRetriever.from(store))
    .build();

String answer = assistant.answer("What is the company policy on remote work?");
```

### Example 2: Metadata-Filtered Retrieval

```java
EmbeddingStoreContentRetriever retriever = EmbeddingStoreContentRetriever.builder()
    .embeddingStore(store)
    .embeddingModel(embeddingModel)
    .maxResults(5)
    .minScore(0.7)
    .filter(metadataKey("category").isEqualTo("technical"))
    .build();
```

### Example 3: Multi-Source RAG Pipeline

```java
ContentRetriever webRetriever = EmbeddingStoreContentRetriever.from(webStore);
ContentRetriever docRetriever = EmbeddingStoreContentRetriever.from(docStore);

List<Content> results = new ArrayList<>();
results.addAll(webRetriever.retrieve(query));
results.addAll(docRetriever.retrieve(query));

List<Content> topResults = reranker.reorder(query, results).subList(0, 5);
```

### Example 4: RAG with Chat Memory

```java
Assistant assistant = AiServices.builder(Assistant.class)
    .chatModel(chatModel)
    .chatMemory(MessageWindowChatMemory.withMaxMessages(10))
    .contentRetriever(retriever)
    .build();

assistant.chat("Tell me about the product features");
assistant.chat("What about pricing for those features?");  // Maintains context
```

## Best Practices

### Document Preparation
- Clean documents before ingestion; remove irrelevant content and formatting
- Add relevant metadata for filtering and context

### Chunking Strategy
- Treat 500-1000 tokens as an experimental starting range, not a universal optimum
- Include 10-20% overlap to preserve context at boundaries
- Test different sizes for your specific use case

### Retrieval Optimization
- Tune candidate count and reranking against measured retrieval quality and latency
- Use metadata filtering to improve relevance
- Monitor retrieval quality and iterate based on user feedback

### Performance
- Cache embeddings for frequently accessed content
- Use batch processing for document ingestion
- Optimize vector store indexing for your scale

## Constraints and Warnings

### System Constraints
- Embedding models have maximum token limits per document
- Vector databases require proper indexing for performance
- Chunk boundaries may lose context for complex documents
- Hybrid search requires additional infrastructure

### Quality Warnings
- Retrieval quality depends heavily on chunking strategy
- Embedding models may not capture domain-specific semantics
- Metadata filtering requires proper document annotation
- Reranking adds latency to query responses

### Security Warnings
- **Never hardcode credentials**: Use environment variables for API keys and passwords
- **Validate external content**: Documents from file systems, APIs, or web sources may contain malicious content (prompt injection)
- Enforce source/tenant authorization before retrieval results reach the model; filtering alone does not prevent prompt injection
- Restrict allowed data source URLs and file paths using allowlists

## Resources

### Reference Documentation
- [Vector Database Comparison](references/vector-databases.md)
- [Embedding Models Guide](references/embedding-models.md)
- [Retrieval Strategies](references/retrieval-strategies.md)
- [Document Chunking](references/document-chunking.md)
- [LangChain4j RAG Guide](references/langchain4j-rag-guide.md)

## Related guidance

- [postgreSQL](../postgreSQL/SKILL.md)
- [transformers](../transformers/SKILL.md)
- [train-sentence-transformers](../train-sentence-transformers/SKILL.md)
